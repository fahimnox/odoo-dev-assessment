import psycopg2

from odoo import api, fields, models
from odoo.tools import SQL, mute_logger
from odoo.tools.sql import index_exists

from .common import ensure_manager

WORK_KINDS = [
    ("country_list", "Country list"),
    ("country_partners", "Country partners"),
    ("partner_details", "Partner details"),
]
WORK_STATES = [
    ("pending", "Pending"),
    ("done", "Done"),
    ("failed", "Failed"),
    ("cancelled", "Cancelled"),
]


class PartnerMonitorWorkItem(models.Model):
    """One durable unit of sync work: the checkpoint of the sync engine.

    The worker cron (Stage 05) claims pending items in small batches; the
    scheduler's commit after each batch makes the finished items durable.
    Stage 03 defines the record, its integrity rules and the manager actions.
    No access rule lets a user write it.
    """

    _name = "azk_odoo_partner_monitor.work.item"
    _description = "Partner Monitor Work Item"
    _order = "id desc"

    kind = fields.Selection(WORK_KINDS, required=True, readonly=True)
    run_id = fields.Many2one(
        "azk_odoo_partner_monitor.sync.run", string="Run",
        required=True, readonly=True, ondelete="cascade", index=True,
    )
    country_id = fields.Many2one(
        "azk_odoo_partner_monitor.country", string="Country",
        readonly=True, ondelete="cascade", index=True,
    )
    partner_id = fields.Many2one(
        "azk_odoo_partner_monitor.partner", string="Partner",
        readonly=True, ondelete="cascade", index=True,
    )
    state = fields.Selection(WORK_STATES, required=True, readonly=True, default="pending", index=True)
    attempt_count = fields.Integer(string="Attempts", readonly=True)
    next_attempt_at = fields.Datetime(
        string="Next Attempt", required=True, readonly=True, default=fields.Datetime.now)
    last_error = fields.Text(readonly=True)
    error_ids = fields.One2many("azk_odoo_partner_monitor.sync.error", "work_item_id", string="Errors")

    _sql_constraints = [
        # Each kind has exactly the target it needs, so a unit can never point
        # at the wrong kind of record.
        ("target_matches_kind",
         "CHECK((kind = 'country_list' AND country_id IS NULL AND partner_id IS NULL)"
         " OR (kind = 'country_partners' AND country_id IS NOT NULL AND partner_id IS NULL)"
         " OR (kind = 'partner_details' AND partner_id IS NOT NULL AND country_id IS NULL))",
         "The work item's target does not match its kind."),
        ("attempts_not_negative", "CHECK(attempt_count >= 0)",
         "The attempt count cannot be negative."),
        # Virtual constraint backed by the partial unique index created in init().
        ("one_pending_per_target", "", "This work is already queued."),
    ]

    def init(self):
        super().init()
        index_name = f"{self._table}_one_pending_per_target"
        if not index_exists(self.env.cr, index_name):
            self.env.cr.execute(SQL(
                "CREATE UNIQUE INDEX %s ON %s (kind, COALESCE(country_id, 0), COALESCE(partner_id, 0))"
                " WHERE state = 'pending'",
                SQL.identifier(index_name), SQL.identifier(self._table)))

    @api.depends("kind", "country_id", "partner_id")
    def _compute_display_name(self):
        labels = dict(self._fields["kind"]._description_selection(self.env))
        for item in self:
            target = item.country_id.name or item.partner_id.name
            label = labels.get(item.kind, "")
            item.display_name = f"{label}: {target}" if target else label

    @api.model
    def _pending_domain(self, kind, country=None, partner=None):
        return [
            ("state", "=", "pending"),
            ("kind", "=", kind),
            ("country_id", "=", country.id if country else False),
            ("partner_id", "=", partner.id if partner else False),
        ]

    @api.model
    def _enqueue(self, kind, run, country=None, partner=None):
        """Queue one unit unless the same work is already pending.

        Returns the pending item, or an empty recordset when another transaction
        queued it at the same moment (the partial unique index refused ours).
        """
        existing = self.search(self._pending_domain(kind, country, partner), limit=1)
        if existing:
            return existing
        try:
            with mute_logger("odoo.sql_db"), self.env.cr.savepoint():
                return self.create({
                    "kind": kind,
                    "run_id": run.id,
                    "country_id": country.id if country else False,
                    "partner_id": partner.id if partner else False,
                })
        except psycopg2.errors.UniqueViolation:
            return self.browse()

    def action_retry(self):
        """Manager action: put failed items back in the queue with a fresh retry budget.

        An item whose work is already queued again is left as it is.
        """
        ensure_manager(self.env)
        self.check_access("read")
        for item in self.filtered(lambda i: i.state == "failed"):
            if item.sudo().search_count(
                    self._pending_domain(item.kind, item.country_id, item.partner_id), limit=1):
                continue
            item.sudo().write({
                "state": "pending",
                "attempt_count": 0,
                "next_attempt_at": fields.Datetime.now(),
            })
            # Write now, not at the next flush: the one-pending-per-target
            # index must see this item before anything else is queued.
            item.sudo().flush_recordset(["state"])
        return True
