from odoo import api, fields, models
from odoo.exceptions import ValidationError

from .common import MAX_ATTEMPTS, VALIDATION_STATES, ensure_manager

# Fields a country-list observation may set. The identity (source_key) is
# matched, never written, and the demo label never comes from the website.
OBSERVED_FIELDS = frozenset({"name", "total_partner_count"})


class PartnerMonitorCountry(models.Model):
    """A country as listed on the Odoo Partners website.

    A standalone model, as the assessment asks, not res.country: the
    website's country list and ids are its own.
    """

    _name = "azk_odoo_partner_monitor.country"
    _description = "Partner Monitor Country"
    _order = "name, id"

    # --- Fields required by the assessment (PDF p. 3) ---
    name = fields.Char(required=True)
    active = fields.Boolean(
        default=True,
        help="Cleared when a complete, validated country list no longer contains this country.",
    )
    total_partner_count = fields.Integer(
        string="Partners Listed",
        help="Number of partners the website listed for this country during the last scrape. "
             "Used for validation.",
    )
    to_reprocess_partners = fields.Boolean(
        string="Needs Re-scrape",
        help="Set when the partners found did not match the listed count, or by a manager. "
             "The country-validation job then scrapes this country again.",
    )

    # --- Supporting fields (docs/architecture.md 5.2) ---
    source_key = fields.Char(
        string="Website ID", required=True, readonly=True,
        help="The website's identifier for this country. Names are never used as identities.",
    )
    is_demo = fields.Boolean(
        string="Demo Data", readonly=True,
        help="Synthetic demonstration record, not scraped from the website.",
    )
    partner_ids = fields.One2many(
        "azk_odoo_partner_monitor.partner", "country_id", string="Partners")
    partner_count = fields.Integer(
        string="Partners in Database", compute="_compute_partner_count",
        help="Active partners of this country stored in the database.",
    )

    # --- Validation bookkeeping (Stage 05, docs/resilience.md) ---
    # Expected (total_partner_count), found, prior and outcome are kept apart,
    # so a genuine change of the listed count is visible as such.
    # The numbers default to 0, so the column is filled when it is added to an
    # existing database: SQL never matches "NULL < 5".
    previous_partner_count = fields.Integer(
        string="Previously Listed", readonly=True, default=0,
        help="The listed partner count before it last changed on the website.",
    )
    snapshot_partner_count = fields.Integer(
        string="Partners Found", readonly=True, default=0,
        help="Distinct partners of this country found by the last listing read.",
    )
    validation_state = fields.Selection(
        VALIDATION_STATES, string="Validation", required=True, readonly=True, default="unchecked",
        help="Matched: the last listing read was a complete snapshot whose partners match the "
             "listed count. Mismatch: it was incomplete or did not match, so nothing was archived.",
    )
    validated_at = fields.Datetime(string="Last Validated", readonly=True)
    reprocess_attempts = fields.Integer(
        string="Re-scrape Attempts", readonly=True, default=0, aggregator=None,
        help="Re-scrapes the country-validation job has queued for the current mismatch. "
             "It stops after the limit; a matching snapshot or a manager resets it.",
    )
    next_reprocess_at = fields.Datetime(string="Next Re-scrape", readonly=True)
    reprocess_exhausted = fields.Boolean(
        string="Retries Exhausted", compute="_compute_reprocess_exhausted", store=True,
        help="Every re-scrape allowed for the current mismatch has been queued. Unless the last "
             "one matches, the mismatch stays visible; a manager can mark the country for "
             "re-scrape again.",
    )

    _sql_constraints = [
        ("source_key_unique", "UNIQUE(source_key)",
         "Another country already has this website ID."),
        # Demo countries use "demo-..." ids, which the website never uses, so a
        # demo record can never be mistaken for, or collide with, a real one.
        ("source_key_namespace", "CHECK((is_demo IS TRUE) = (left(source_key, 5) = 'demo-'))",
         "Only demo countries may use, and must use, website IDs starting with 'demo-'."),
        ("listed_count_not_negative", "CHECK(total_partner_count >= 0)",
         "The listed partner count cannot be negative."),
        ("reprocess_attempts_not_negative", "CHECK(reprocess_attempts >= 0)",
         "The re-scrape attempt count cannot be negative."),
    ]

    def _compute_partner_count(self):
        counts = dict(self.env["azk_odoo_partner_monitor.partner"]._read_group(
            [("country_id", "in", self.ids)], ["country_id"], ["__count"]))
        for country in self:
            country.partner_count = counts.get(country, 0)

    @api.depends("to_reprocess_partners", "reprocess_attempts")
    def _compute_reprocess_exhausted(self):
        for country in self:
            country.reprocess_exhausted = (country.to_reprocess_partners
                                           and country.reprocess_attempts >= MAX_ATTEMPTS)

    def write(self, vals):
        if "source_key" in vals and any(c.source_key != vals["source_key"] for c in self):
            raise ValidationError(self.env._("A country's website ID never changes."))
        return super().write(vals)

    @api.model
    def _record_observation(self, values):
        """Create or update one country from the website's country list.

        ``values`` holds ``source_key`` plus any of OBSERVED_FIELDS. The match is
        on source_key, never on the name. A country seen again is reactivated.
        Deactivating countries missing from a complete list is the sync engine's
        job (Stage 05). Returns the country.
        """
        values = dict(values)
        source_key = (values.pop("source_key", None) or "").strip()
        if not source_key:
            raise ValidationError(self.env._("A country observation needs the website ID."))
        unexpected = set(values) - OBSERVED_FIELDS
        if unexpected:
            raise ValueError(f"Fields not allowed in a country observation: {sorted(unexpected)}")
        country = self.with_context(active_test=False).search(
            [("source_key", "=", source_key)], limit=1).with_env(self.env)
        if not country:
            return self.create({**values, "source_key": source_key})
        changed = {name: value for name, value in {**values, "active": True}.items()
                   if country[name] != value}
        if "total_partner_count" in changed:
            changed["previous_partner_count"] = country.total_partner_count
        if changed:
            country.write(changed)
        return country

    def _set_listed_count(self, count):
        """Store a new listed (expected) count, keeping the previous one."""
        self.ensure_one()
        if count is not None and count != self.total_partner_count:
            self.write({"previous_partner_count": self.total_partner_count, "total_partner_count": count})

    def _record_validation(self, matched, found, now):
        """Store the outcome of one listing read of this country (P-18).

        A match clears the flag and the retry budget. A new mismatch sets the
        flag with a fresh budget, due at once. A mismatch that persists keeps
        the attempts already used, so re-scrapes stay bounded (P-19).
        """
        for country in self:
            vals = {
                "snapshot_partner_count": found,
                "validated_at": now,
                "validation_state": "matched" if matched else "mismatch",
            }
            if matched:
                vals.update(to_reprocess_partners=False, reprocess_attempts=0, next_reprocess_at=False)
            elif not country.to_reprocess_partners:
                vals.update(to_reprocess_partners=True, reprocess_attempts=0, next_reprocess_at=now)
            country.write(vals)

    def action_mark_for_rescrape(self):
        """Manager action: flag these countries for the country-validation job.

        It also gives them a fresh retry budget, so a country whose retries
        were exhausted is tried again.
        """
        ensure_manager(self.env)
        self.check_access("read")
        self.sudo().write({"to_reprocess_partners": True, "reprocess_attempts": 0,
                           "next_reprocess_at": fields.Datetime.now()})
        return True
