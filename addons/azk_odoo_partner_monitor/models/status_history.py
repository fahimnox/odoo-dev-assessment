from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import SQL
from odoo.tools.sql import index_exists

from .common import STATUS_RANK, STATUS_SELECTION

CHANGE_TYPES = [("initial", "Initial"), ("promoted", "Promoted"), ("demoted", "Demoted")]


class PartnerMonitorStatusHistory(models.Model):
    """One status event of a partner: its first observation or a real change.

    Rows are written only by the ingestion API (superuser engine). No access
    rule lets a user create, edit or delete them, and the model itself refuses
    edits, so the history is an append-only audit trail.
    """

    _name = "azk_odoo_partner_monitor.status.history"
    _description = "Partner Monitor Status Change"
    _order = "change_date desc, id desc"

    # --- Fields required by the assessment (PDF p. 4) ---
    partner_id = fields.Many2one(
        "azk_odoo_partner_monitor.partner", string="Partner",
        required=True, ondelete="cascade", index=True,
    )
    previous_status = fields.Selection(
        STATUS_SELECTION, help="Empty for the initial observation.")
    new_status = fields.Selection(STATUS_SELECTION, required=True)
    change_date = fields.Date(required=True, help="Date of the scrape that observed the status.")
    change_type = fields.Selection(
        CHANGE_TYPES, required=True,
        help="Initial: first observation of the partner. Promoted or Demoted: the status "
             "moved up or down in the ranking Ready < Silver < Gold.",
    )

    _sql_constraints = [
        ("initial_no_previous", "CHECK((change_type = 'initial') = (previous_status IS NULL))",
         "Only the initial status record has no previous status."),
        ("status_changes", "CHECK(previous_status IS NULL OR previous_status <> new_status)",
         "A status change must change the status."),
        # Virtual constraint backed by the partial unique index created in init().
        ("single_initial", "", "A partner has only one initial status record."),
    ]

    def init(self):
        super().init()
        index_name = f"{self._table}_single_initial"
        if not index_exists(self.env.cr, index_name):
            self.env.cr.execute(SQL(
                "CREATE UNIQUE INDEX %s ON %s (partner_id) WHERE change_type = 'initial'",
                SQL.identifier(index_name), SQL.identifier(self._table)))

    @api.constrains("previous_status", "new_status", "change_type")
    def _check_change_type(self):
        for row in self.filtered(lambda r: r.change_type != "initial" and r.previous_status):
            moved_up = STATUS_RANK[row.new_status] > STATUS_RANK[row.previous_status]
            if row.change_type != ("promoted" if moved_up else "demoted"):
                raise ValidationError(self.env._(
                    "The change type must follow the ranking Ready < Silver < Gold."))

    @api.constrains("change_date", "change_type", "partner_id")
    def _check_change_date(self):
        for row in self:
            first_seen = row.partner_id.first_seen_on
            if row.change_type == "initial" and row.change_date != first_seen:
                raise ValidationError(self.env._(
                    "The initial status record is dated on the partner's First Seen On date."))
            if row.change_date < first_seen:
                raise ValidationError(self.env._(
                    "A status change cannot be dated before the partner was first seen."))

    @api.depends("partner_id", "previous_status", "new_status")
    def _compute_display_name(self):
        labels = dict(STATUS_SELECTION)
        for row in self:
            previous = labels.get(row.previous_status, "-")
            row.display_name = f"{row.partner_id.name}: {previous} -> {labels.get(row.new_status, '')}"

    def write(self, vals):
        raise UserError(self.env._("Status history records cannot be changed."))
