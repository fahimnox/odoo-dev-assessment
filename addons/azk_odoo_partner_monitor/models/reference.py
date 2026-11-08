from odoo import api, fields, models
from odoo.tools import SQL
from odoo.tools.sql import index_exists


class PartnerMonitorReference(models.Model):
    """One listing interval of a client reference of a partner (decision D-10).

    A reference is added with is_active=True. When a complete reference
    snapshot no longer lists it, the record is closed (is_active=False,
    removed_on). If it comes back, a new record opens a new interval, so every
    earlier added_on/removed_on pair is kept.
    """

    _name = "azk_odoo_partner_monitor.reference"
    _description = "Partner Monitor Client Reference"
    _order = "is_active desc, added_on desc, id desc"

    # --- Fields required by the assessment (PDF p. 4) ---
    partner_id = fields.Many2one(
        "azk_odoo_partner_monitor.partner", string="Partner",
        required=True, ondelete="cascade", index=True,
    )
    name = fields.Char(required=True, help="Name of the reference client.")
    is_active = fields.Boolean(string="Active", default=True)
    added_on = fields.Date(required=True, help="Date of the scrape that first listed this reference.")
    removed_on = fields.Date(help="Date of the complete scrape that no longer listed it.")

    # --- Supporting field (docs/architecture.md 5.2) ---
    source_key = fields.Char(
        string="Reference Key", required=True,
        help="Identifies the reference within its partner. Stage 04 decides its source on the "
             "live website (a link or id if shown, otherwise the normalized name).",
    )

    _sql_constraints = [
        ("active_xor_removed", "CHECK((is_active IS TRUE) = (removed_on IS NULL))",
         "An active reference has no removal date, and a removed one has one."),
        ("removal_after_addition", "CHECK(removed_on IS NULL OR removed_on >= added_on)",
         "A reference cannot be removed before it was added."),
        # Virtual constraint backed by the partial unique index created in init().
        ("one_active_per_key", "",
         "This partner already has an active reference with this key."),
    ]

    def init(self):
        super().init()
        index_name = f"{self._table}_one_active_per_key"
        if not index_exists(self.env.cr, index_name):
            self.env.cr.execute(SQL(
                "CREATE UNIQUE INDEX %s ON %s (partner_id, source_key) WHERE is_active IS TRUE",
                SQL.identifier(index_name), SQL.identifier(self._table)))

    @api.depends("partner_id", "name")
    def _compute_display_name(self):
        for ref in self:
            ref.display_name = f"{ref.partner_id.name}: {ref.name}"
