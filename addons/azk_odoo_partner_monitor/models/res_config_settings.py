from odoo import fields, models

from .sync_run import NOTIFY_USER_PARAM


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # Settings are restricted to system administrators (base ACL on
    # res.config.settings and ir.config_parameter). The data file sets the
    # default to the administrator; see docs/architecture.md 5.7.
    partner_monitor_notify_user_id = fields.Many2one(
        "res.users", string="Failure Recipient",
        config_parameter=NOTIFY_USER_PARAM,
        domain=[("share", "=", False)],
        help="Internal user who receives a note when a Partner Monitor sync run fails "
             "or ends partially.",
    )
