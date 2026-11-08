import logging

from markupsafe import Markup

from odoo import api, fields, models

from .common import MANAGER_GROUP, ensure_manager

_logger = logging.getLogger(__name__)

NOTIFY_USER_PARAM = "azk_odoo_partner_monitor.notify_user_id"
MAX_FAILED_UNITS_LISTED = 20


class PartnerMonitorSyncRun(models.Model):
    """One synchronization run: a daily discovery, a manual sync or a validation pass.

    The run groups its work items and errors. Its chatter (mail.thread) is where
    a failed or partial run posts its note for the configured user
    (docs/architecture.md 5.7). Runs are created and updated only by the sync
    engine and by the manager action "Sync Now"; no access rule lets users
    write them.
    """

    _name = "azk_odoo_partner_monitor.sync.run"
    _description = "Partner Monitor Sync Run"
    _inherit = ["mail.thread"]
    _order = "started_at desc, id desc"

    trigger = fields.Selection(
        [("daily", "Daily discovery"), ("manual", "Manual"), ("validation", "Validation")],
        required=True, readonly=True, default="manual",
    )
    state = fields.Selection(
        [("running", "Running"), ("done", "Done"), ("partial", "Partial"), ("failed", "Failed")],
        required=True, readonly=True, default="running", tracking=True,
        help="Running: work is queued or in progress. Done: every unit succeeded. "
             "Partial: some units failed. Failed: the run could not do its work.",
    )
    started_at = fields.Datetime(required=True, readonly=True, default=fields.Datetime.now)
    finished_at = fields.Datetime(readonly=True)
    notified_at = fields.Datetime(
        string="Failure Note Posted", readonly=True,
        help="When the failure note was posted. A run is never notified twice.",
    )
    work_item_ids = fields.One2many(
        "azk_odoo_partner_monitor.work.item", "run_id", string="Work Items", groups=MANAGER_GROUP)
    error_ids = fields.One2many(
        "azk_odoo_partner_monitor.sync.error", "run_id", string="Errors", groups=MANAGER_GROUP)
    pending_count = fields.Integer(string="Pending Units", compute="_compute_counts", groups=MANAGER_GROUP)
    done_count = fields.Integer(string="Done Units", compute="_compute_counts", groups=MANAGER_GROUP)
    failed_count = fields.Integer(string="Failed Units", compute="_compute_counts", groups=MANAGER_GROUP)
    error_count = fields.Integer(string="Error Count", compute="_compute_counts", groups=MANAGER_GROUP)

    @api.depends("trigger")
    def _compute_display_name(self):
        labels = dict(self._fields["trigger"]._description_selection(self.env))
        for run in self:
            run.display_name = self.env._(
                "Run %(number)s (%(trigger)s)",
                number=run._origin.id or "", trigger=labels.get(run.trigger, ""))

    @api.depends("work_item_ids.state", "error_ids")
    def _compute_counts(self):
        units = self.env["azk_odoo_partner_monitor.work.item"]._read_group(
            [("run_id", "in", self.ids)], ["run_id", "state"], ["__count"])
        errors = dict(self.env["azk_odoo_partner_monitor.sync.error"]._read_group(
            [("run_id", "in", self.ids)], ["run_id"], ["__count"]))
        by_run = {}
        for run, state, count in units:
            by_run.setdefault(run, {})[state] = count
        for run in self:
            counts = by_run.get(run, {})
            run.pending_count = counts.get("pending", 0)
            run.done_count = counts.get("done", 0)
            run.failed_count = counts.get("failed", 0)
            run.error_count = errors.get(run, 0)

    def action_sync_now(self):
        """Manager action: queue a full sync.

        It only creates a run and queues its first unit (the country list).
        The worker job processes the queue in bounded batches (Stage 05); this
        button never scrapes inside the user's request.
        """
        ensure_manager(self.env)
        WorkItem = self.env["azk_odoo_partner_monitor.work.item"].sudo()
        if WorkItem.search_count([("kind", "=", "country_list"), ("state", "=", "pending")], limit=1):
            message, kind = self.env._("A sync is already queued."), "warning"
        else:
            run = self.sudo().with_context(mail_create_nolog=True, mail_create_nosubscribe=True).create(
                {"trigger": "manual"})
            WorkItem._enqueue("country_list", run)
            message, kind = self.env._("%(run)s is queued.", run=run.display_name), "info"
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "message": message,
                "type": kind,
                "next": {"type": "ir.actions.client", "tag": "soft_reload"},
            },
        }

    # ------------------------------------------------------------------
    # Failure notification (P-07, decision D-08)
    # ------------------------------------------------------------------

    @api.model
    def _get_failure_recipient(self):
        """Return the configured internal user, falling back to the administrator.

        The setting is stored as an ir.config_parameter (Settings > Partner
        Monitor). Reading it needs sudo(): the parameter table is restricted to
        system administrators, and only the user id is read.
        """
        value = self.env["ir.config_parameter"].sudo().get_param(NOTIFY_USER_PARAM) or ""
        user = self.env["res.users"]
        if value.strip().isdigit():
            user = user.browse(int(value)).exists()
        if user and user.active and not user.share:
            return user
        admin = self.env.ref("base.user_admin", raise_if_not_found=False)
        _logger.warning("Partner Monitor: the failure recipient %r is not an active internal "
                        "user; the administrator is notified instead.", value)
        if admin and admin.active and not admin.share:
            return admin
        return self.env["res.users"]

    def _notify_failure(self):
        """Post one internal note on each failed or partial run, for the configured user.

        The note is a message on the run's own chatter with the recipient's
        partner in partner_ids. Odoo then delivers it according to that user's
        notification preference: the Discuss Inbox ("Handle in Odoo") or an
        email ("Handle by Emails"). notified_at prevents a second note.
        Returns the posted messages.
        """
        messages = self.env["mail.message"]
        for run in self:
            if run.state not in ("partial", "failed") or run.notified_at:
                continue
            recipient = run._get_failure_recipient()
            messages |= run.message_post(
                body=run._failure_note_body(),
                message_type="comment",
                subtype_xmlid="mail.mt_note",
                partner_ids=recipient.partner_id.ids,
            )
            run.notified_at = fields.Datetime.now()
        return messages

    def _failure_note_body(self):
        self.ensure_one()
        state_label = dict(self._fields["state"]._description_selection(self.env))[self.state]
        summary = self.env._(
            "Partner Monitor %(run)s ended as %(state)s: %(done)s units done, %(failed)s failed, "
            "%(pending)s pending, %(errors)s errors logged.",
            run=self.display_name, state=state_label, done=self.done_count,
            failed=self.failed_count, pending=self.pending_count, errors=self.error_count)
        failed_units = self.work_item_ids.filtered(lambda item: item.state == "failed")
        lines = Markup().join(
            Markup("<li>%s: %s</li>") % (item.display_name, (item.last_error or "").splitlines()[0][:200]
                                          if item.last_error else "-")
            for item in failed_units[:MAX_FAILED_UNITS_LISTED])
        recovery = self.env._(
            "Managers can retry failed work under Partner Monitor > Sync > Work Items.")
        body = Markup("<p>%s</p>") % summary
        if lines:
            body += Markup("<p>%s</p><ul>%s</ul>") % (self.env._("Failed scopes:"), lines)
        return body + Markup("<p>%s</p>") % recovery
