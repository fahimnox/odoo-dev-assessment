import logging

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from ..services.urls import is_canonical_partner_url
from .common import MAX_ATTEMPTS, STATUS_RANK, STATUS_SELECTION, VALIDATION_STATES, ensure_manager

_logger = logging.getLogger(__name__)

# Fields an observation of the website may set directly. The identity, the
# first/last-seen dates, the flags and the demo label are never taken from an
# observation, so the API cannot be used to rewrite them.
OBSERVED_FIELDS = frozenset({"name", "partner_url", "current_status", "country_id"})
# Measurements the website may not show. In an observation, None means
# "unknown": it is stored as a False *_known flag, never as a fake zero
# (Odoo reads a NULL number as 0, so the flag is what tells them apart).
METRIC_FIELDS = ("retention_rate", "total_references_count",
                 "largest_project_size", "average_project_size")


class PartnerMonitorPartner(models.Model):
    """A partner listed on the Odoo Partners website, identified by its website id."""

    _name = "azk_odoo_partner_monitor.partner"
    _description = "Monitored Odoo Partner"
    _order = "name, id"

    # --- Fields required by the assessment (PDF p. 4) ---
    name = fields.Char(required=True)
    partner_url = fields.Char(
        string="Partner Page",
        help="Canonical link to the partner's page on the Odoo website.",
    )
    current_status = fields.Selection(
        STATUS_SELECTION, string="Status", required=True,
        help="Partner level shown on the website. Ranking: Ready < Silver < Gold.",
    )
    country_id = fields.Many2one(
        "azk_odoo_partner_monitor.country", string="Country",
        required=True, ondelete="restrict", index=True,
    )
    first_seen_on = fields.Date(
        string="First Seen On", required=True, readonly=True,
        help="Date of the first scrape that listed this partner. It never changes afterwards.",
    )
    retention_rate = fields.Float()
    total_references_count = fields.Integer(
        string="References Listed",
        help="Number of references the website shows for this partner. "
             "It is the expected count used to validate the stored references.",
    )
    largest_project_size = fields.Integer()
    average_project_size = fields.Float()
    to_reprocess_references = fields.Boolean(
        string="Needs Re-scrape",
        help="Set when the active references in the database do not match the listed count, "
             "or by a manager. The reference-validation job then scrapes this partner again.",
    )
    status_history_ids = fields.One2many(
        "azk_odoo_partner_monitor.status.history", "partner_id", string="Status History")
    reference_ids = fields.One2many(
        "azk_odoo_partner_monitor.reference", "partner_id", string="References")

    # --- Supporting fields (docs/architecture.md 5.2) ---
    source_id = fields.Integer(
        string="Website ID", required=True, readonly=True,
        help="The number at the end of the partner's website link. It identifies the partner; "
             "names are never used as identities.",
    )
    active = fields.Boolean(
        default=True,
        help="Archived when a complete, validated scrape of its country no longer lists the partner.",
    )
    last_seen_on = fields.Date(string="Last Seen On", readonly=True)
    is_demo = fields.Boolean(
        string="Demo Data", readonly=True,
        help="Synthetic demonstration record, not scraped from the website.",
    )
    retention_rate_known = fields.Boolean(readonly=True)
    total_references_count_known = fields.Boolean(readonly=True)
    largest_project_size_known = fields.Boolean(readonly=True)
    average_project_size_known = fields.Boolean(readonly=True)

    # --- Validation and change detection (Stage 05, docs/resilience.md) ---
    # Expected (total_references_count), found, stored, prior and outcome are
    # kept apart.
    # The numbers default to 0, so the column is filled when it is added to an
    # existing database: SQL never matches "NULL < 5".
    previous_references_count = fields.Integer(
        string="Previously Listed References", readonly=True, default=0,
        help="The listed reference count before it last changed on the website.",
    )
    snapshot_reference_count = fields.Integer(
        string="References Found", readonly=True, default=0,
        help="References found on the partner's page at the last details read.",
    )
    active_reference_count = fields.Integer(
        string="Active References", compute="_compute_active_reference_count", store=True,
        help="Active references stored in the database.",
    )
    reference_validation_state = fields.Selection(
        VALIDATION_STATES, string="Reference Validation", required=True, readonly=True,
        default="unchecked",
        help="Matched: the last details read was a complete reference list whose size, and the "
             "active references stored, equal the listed count. Mismatch: otherwise; no "
             "reference was removed.",
    )
    details_synced_at = fields.Datetime(
        string="Details Read At", readonly=True,
        help="When the partner's own page was last read and stored.",
    )
    listing_fingerprint = fields.Char(
        readonly=True,
        help="Hash of the metrics on the partner's listing card at the last listing read. "
             "A different hash schedules a details refresh.",
    )
    reprocess_attempts = fields.Integer(
        string="Re-scrape Attempts", readonly=True, default=0,
        help="Details re-reads the reference-validation job has queued for the current "
             "mismatch. It stops after the limit; a matching read or a manager resets it.",
    )
    next_reprocess_at = fields.Datetime(string="Next Re-scrape", readonly=True)
    reprocess_exhausted = fields.Boolean(
        string="Retries Exhausted", compute="_compute_reprocess_exhausted", store=True,
        help="Every re-read allowed for the current mismatch has been queued. Unless the last "
             "one matches, the mismatch stays visible; a manager can mark the partner for "
             "re-scrape again.",
    )

    _sql_constraints = [
        ("source_id_unique", "UNIQUE(source_id)",
         "Another partner already has this website ID."),
        # Website ids are positive. Demo partners use negative ids, so they can
        # never collide with a scraped partner.
        ("source_id_namespace", "CHECK(source_id <> 0 AND (is_demo IS TRUE) = (source_id < 0))",
         "Website IDs are positive; only demo partners use negative IDs."),
        ("seen_dates_ordered", "CHECK(last_seen_on IS NULL OR last_seen_on >= first_seen_on)",
         "A partner cannot be last seen before it was first seen."),
        ("metrics_not_negative",
         "CHECK(retention_rate >= 0 AND total_references_count >= 0"
         " AND largest_project_size >= 0 AND average_project_size >= 0)",
         "Partner metrics cannot be negative."),
        # An unknown measurement carries no number, so no stale value can hide
        # behind a False *_known flag.
        ("unknown_metrics_empty",
         "CHECK((retention_rate_known IS TRUE OR COALESCE(retention_rate, 0) = 0)"
         " AND (total_references_count_known IS TRUE OR COALESCE(total_references_count, 0) = 0)"
         " AND (largest_project_size_known IS TRUE OR COALESCE(largest_project_size, 0) = 0)"
         " AND (average_project_size_known IS TRUE OR COALESCE(average_project_size, 0) = 0))",
         "An unknown metric must not carry a value."),
        ("reprocess_attempts_not_negative", "CHECK(reprocess_attempts >= 0)",
         "The re-scrape attempt count cannot be negative."),
    ]

    @api.depends("reference_ids.is_active")
    def _compute_active_reference_count(self):
        counts = dict(self.env["azk_odoo_partner_monitor.reference"]._read_group(
            [("partner_id", "in", self.ids), ("is_active", "=", True)], ["partner_id"], ["__count"]))
        for partner in self:
            partner.active_reference_count = counts.get(partner, 0)

    @api.depends("to_reprocess_references", "reprocess_attempts")
    def _compute_reprocess_exhausted(self):
        for partner in self:
            partner.reprocess_exhausted = (partner.to_reprocess_references
                                           and partner.reprocess_attempts >= MAX_ATTEMPTS)

    @api.constrains("partner_url", "source_id")
    def _check_partner_url(self):
        for partner in self:
            if partner.partner_url and not is_canonical_partner_url(partner.partner_url, partner.source_id):
                raise ValidationError(self.env._(
                    "%(url)s is not the canonical link of the partner with website ID %(id)s "
                    "(expected https://www.odoo.com/partners/<name>-%(id)s, without query string).",
                    url=partner.partner_url, id=partner.source_id))

    def write(self, vals):
        if "source_id" in vals and any(p.source_id != vals["source_id"] for p in self):
            raise ValidationError(self.env._("A partner's website ID never changes."))
        if "first_seen_on" in vals:
            new_date = fields.Date.to_date(vals["first_seen_on"])
            if any(p.first_seen_on and p.first_seen_on != new_date for p in self):
                raise ValidationError(self.env._(
                    "First Seen On is recorded once, when the partner is first scraped, "
                    "and never changes afterwards."))
        return super().write(vals)

    # ------------------------------------------------------------------
    # Ingestion API used by the sync engine (Stage 05) and the tests.
    # Private methods: they cannot be called over RPC, and they need the
    # engine's superuser rights because no user may create history rows.
    # ------------------------------------------------------------------

    @api.model
    def _record_observation(self, values, observed_on):
        """Create or update one partner from one observation of the website.

        ``values`` must hold ``source_id`` and may hold OBSERVED_FIELDS and
        METRIC_FIELDS. A None value in OBSERVED_FIELDS means "not observed";
        a None metric means "unknown". ``observed_on`` is the run date
        (assumption A-20). Returns the partner.

        Invariants (docs/architecture.md 5.3):
        - one record per website id, so a replayed observation creates nothing;
        - first_seen_on is set once, at creation;
        - one 'initial' history row at creation, then exactly one row per real
          status change, typed by rank; an unchanged status adds nothing;
        - an observation older than last_seen_on is ignored, so a late replay
          cannot record a false transition;
        - an unknown status label fails without writing anything (D-09).
        """
        values = dict(values)
        source_id = values.pop("source_id", None)
        if not source_id:
            raise ValidationError(self.env._("A partner observation needs the website ID."))
        unexpected = set(values) - OBSERVED_FIELDS - set(METRIC_FIELDS)
        if unexpected:
            raise ValueError(f"Fields not allowed in a partner observation: {sorted(unexpected)}")
        status = values.get("current_status")
        if status is not None and status not in STATUS_RANK:
            raise ValidationError(self.env._(
                "Unknown partner status %(status)r for website ID %(id)s; nothing was recorded.",
                status=status, id=source_id))
        observed_on = fields.Date.to_date(observed_on)
        vals = self._observation_vals(values)

        partner = self.with_context(active_test=False).search(
            [("source_id", "=", source_id)], limit=1).with_env(self.env)
        if not partner:
            if not status:
                raise ValidationError(self.env._(
                    "The first observation of website ID %(id)s needs a status.", id=source_id))
            partner = self.create({
                **vals,
                "source_id": source_id,
                "first_seen_on": observed_on,
                "last_seen_on": observed_on,
            })
            partner._add_status_change(False, status, observed_on)
            return partner

        if partner.last_seen_on and observed_on < partner.last_seen_on:
            _logger.info("Ignored an observation of partner %s dated %s: the partner was "
                         "already seen on %s.", source_id, observed_on, partner.last_seen_on)
            return partner

        previous_status = partner.current_status
        vals.update(last_seen_on=observed_on, active=True)
        changed = {name: value for name, value in vals.items() if partner._differs(name, value)}
        if ("total_references_count" in changed and partner.total_references_count_known
                and vals.get("total_references_count_known")):
            # A known listed count changed to another known one: keep the prior count.
            changed["previous_references_count"] = partner.total_references_count
        if changed:
            partner.write(changed)
        if status and status != previous_status:
            partner._add_status_change(previous_status, status, observed_on)
        return partner

    @api.model
    def _observation_vals(self, values):
        vals = {name: values[name] for name in OBSERVED_FIELDS if values.get(name) is not None}
        for name in METRIC_FIELDS:
            if name in values:
                known = values[name] is not None
                vals[name] = values[name] if known else 0
                vals[f"{name}_known"] = known
        return vals

    def _differs(self, name, value):
        current = self[name]
        if self._fields[name].type == "many2one":
            current = current.id
        return current != value

    def _add_status_change(self, previous_status, new_status, change_date):
        self.ensure_one()
        if not previous_status:
            change_type = "initial"
        elif STATUS_RANK[new_status] > STATUS_RANK[previous_status]:
            change_type = "promoted"
        else:
            change_type = "demoted"
        return self.env["azk_odoo_partner_monitor.status.history"].create({
            "partner_id": self.id,
            "previous_status": previous_status or False,
            "new_status": new_status,
            "change_date": change_date,
            "change_type": change_type,
        })

    def _sync_references(self, items, observed_on, complete):
        """Apply one reference snapshot of this partner (docs/architecture.md 5.4, D-10).

        ``items`` holds dicts with ``source_key`` and ``name``. Each reference
        record is one listing interval:
        - a key without an active record opens a new interval (a new active
          record with added_on); a removed reference that comes back therefore
          gets a new record, and the closed interval keeps its dates;
        - only a ``complete`` snapshot closes the active records it no longer
          lists (is_active=False, removed_on); a partial snapshot never removes.
        Returns the (added, removed) references.
        """
        self.ensure_one()
        observed_on = fields.Date.to_date(observed_on)
        Reference = self.env["azk_odoo_partner_monitor.reference"]
        # The one-active-per-key index is checked by the database at INSERT
        # time, but the ORM delays UPDATEs until a flush. Flush pending
        # closures first, so a reference closed by an earlier snapshot is
        # inactive in the database before its new interval is inserted.
        Reference.flush_model(["is_active", "removed_on"])
        active_by_key = {ref.source_key: ref for ref in self.reference_ids if ref.is_active}
        listed = {}
        for item in items:
            key = (item.get("source_key") or "").strip()
            if not key or not item.get("name"):
                raise ValidationError(self.env._("A reference needs an identifier and a name."))
            listed.setdefault(key, item)

        new_vals = []
        for key, item in listed.items():
            ref = active_by_key.get(key)
            if not ref:
                new_vals.append({"partner_id": self.id, "source_key": key,
                                 "name": item["name"], "added_on": observed_on})
            elif ref.name != item["name"]:
                ref.name = item["name"]
        added = Reference.create(new_vals)

        removed = Reference
        if complete:
            removed = Reference.union(*(ref for key, ref in active_by_key.items() if key not in listed))
            removed.write({"is_active": False, "removed_on": observed_on})
            removed.flush_recordset(["is_active", "removed_on"])
        return added, removed

    def _request_details_refresh(self, now):
        """Flag these partners for a details re-read, with a fresh retry budget.

        Partners already flagged keep their budget, so repeated requests can
        never reset a mismatch's bounded retries.
        """
        self.filtered(lambda partner: not partner.to_reprocess_references).write({
            "to_reprocess_references": True, "reprocess_attempts": 0, "next_reprocess_at": now})

    def _record_reference_validation(self, matched, found, now):
        """Store the outcome of one details read of this partner (P-20).

        A match clears the flag and the retry budget. A new mismatch sets the
        flag with a fresh budget, due at once. A mismatch that persists keeps
        the attempts already used, so re-reads stay bounded (P-21).
        """
        for partner in self:
            vals = {
                "snapshot_reference_count": found,
                "details_synced_at": now,
                "reference_validation_state": "matched" if matched else "mismatch",
            }
            if matched:
                vals.update(to_reprocess_references=False, reprocess_attempts=0, next_reprocess_at=False)
            elif not partner.to_reprocess_references:
                vals.update(to_reprocess_references=True, reprocess_attempts=0, next_reprocess_at=now)
            partner.write(vals)

    def action_mark_for_rescrape(self):
        """Manager action: flag these partners for the reference-validation job.

        It also gives them a fresh retry budget, so a partner whose retries
        were exhausted is tried again.
        """
        ensure_manager(self.env)
        self.check_access("read")
        self.sudo().write({"to_reprocess_references": True, "reprocess_attempts": 0,
                           "next_reprocess_at": fields.Datetime.now()})
        return True
