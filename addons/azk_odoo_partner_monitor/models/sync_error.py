from odoo import api, fields, models


class PartnerMonitorSyncError(models.Model):
    """One error met during a sync, with its context (P-06).

    The sync engine (Stage 05) writes a row for every failed unit, outside the
    unit's rolled-back savepoint, and also logs it with the Python logger.
    Only managers can read errors; nobody can write them.
    """

    _name = "azk_odoo_partner_monitor.sync.error"
    _description = "Partner Monitor Sync Error"
    _order = "occurred_at desc, id desc"

    run_id = fields.Many2one(
        "azk_odoo_partner_monitor.sync.run", string="Run",
        required=True, readonly=True, ondelete="cascade", index=True,
    )
    work_item_id = fields.Many2one(
        "azk_odoo_partner_monitor.work.item", string="Work Item",
        readonly=True, ondelete="set null", index=True,
    )
    kind = fields.Selection(related="work_item_id.kind")
    country_id = fields.Many2one(
        "azk_odoo_partner_monitor.country", string="Country", readonly=True, ondelete="set null")
    partner_id = fields.Many2one(
        "azk_odoo_partner_monitor.partner", string="Partner", readonly=True, ondelete="set null")
    url = fields.Char(string="URL", readonly=True)
    error_class = fields.Char(string="Error Type", required=True, readonly=True)
    message = fields.Text(required=True, readonly=True)
    trace = fields.Text(string="Trace", readonly=True, help="Shortened technical trace.")
    occurred_at = fields.Datetime(required=True, readonly=True, default=fields.Datetime.now)

    @api.depends("error_class", "message")
    def _compute_display_name(self):
        for error in self:
            first_line = (error.message or "").splitlines()[0][:80] if error.message else ""
            error.display_name = f"{error.error_class}: {first_line}"
