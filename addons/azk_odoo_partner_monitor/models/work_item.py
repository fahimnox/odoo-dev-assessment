import psycopg2

from odoo import api, fields, models
from odoo.tools import SQL, mute_logger
from odoo.tools.sql import index_exists

from .common import MAX_ATTEMPTS, ensure_manager, retry_delay

WORKER_CRON = "azk_odoo_partner_monitor.ir_cron_worker"

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

    The worker (models/worker.py) claims pending items one at a time with a
    row lock and processes each in its own savepoint. The scheduler's commit
    after each batch makes the finished items durable; a crashed batch is
    rolled back, so its items are simply pending again (docs/resilience.md).
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
    attempt_count = fields.Integer(string="Attempts", readonly=True, default=0)
    next_attempt_at = fields.Datetime(
        string="Next Attempt", required=True, readonly=True, default=fields.Datetime.now)
    last_error = fields.Text(readonly=True)
    finished_at = fields.Datetime(
        string="Finished", readonly=True,
        help="When the unit was done, or failed for the last time.")
    result_summary = fields.Char(
        string="Result", readonly=True, help="What the unit read and stored.")
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

    @api.model
    def _trigger_worker(self):
        """Ask the scheduler to run the worker job soon (instead of at its next interval).

        ir.cron._trigger() creates an ir.cron.trigger record with sudo() itself;
        the cron record is read with a narrow sudo() because managers may not
        read scheduled actions.
        """
        cron = self.env.ref(WORKER_CRON, raise_if_not_found=False)
        if cron:
            cron.sudo()._trigger()

    def _mark_done(self, summary, now):
        self.ensure_one()
        self.write({"state": "done", "finished_at": now, "result_summary": (summary or "")[:250]})

    def _mark_failed_attempt(self, error_text, now):
        """Count one failed try. Returns True when the retry budget is used up.

        Until then the item stays pending, due again after the backoff delay
        (common.retry_delay). After the last try it is failed and stays
        visible; a manager can retry it.
        """
        self.ensure_one()
        attempts = self.attempt_count + 1
        final = attempts >= MAX_ATTEMPTS
        self.write({
            "attempt_count": attempts,
            "state": "failed" if final else "pending",
            "next_attempt_at": now if final else now + retry_delay(attempts),
            "finished_at": now if final else False,
            "last_error": error_text,
        })
        return final

    def action_retry(self):
        """Manager action: put failed items back in the queue with a fresh retry budget.

        An item whose work is already queued again is left as it is. The
        item's run is reopened, so it is finalized again when the item ends;
        it is not notified a second time (notified_at). The worker is woken.
        """
        ensure_manager(self.env)
        self.check_access("read")
        retried = self.browse()
        for item in self.filtered(lambda i: i.state == "failed"):
            if item.sudo().search_count(
                    self._pending_domain(item.kind, item.country_id, item.partner_id), limit=1):
                continue
            item.sudo().write({
                "state": "pending",
                "attempt_count": 0,
                "next_attempt_at": fields.Datetime.now(),
                "finished_at": False,
            })
            # Write now, not at the next flush: the one-pending-per-target
            # index must see this item before anything else is queued.
            item.sudo().flush_recordset(["state"])
            retried |= item
        if retried:
            retried.sudo().run_id.filtered(lambda run: run.state != "running").write(
                {"state": "running", "finished_at": False})
            self._trigger_worker()
        return True
