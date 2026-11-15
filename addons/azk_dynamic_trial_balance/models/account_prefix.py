from odoo import api, fields, models

from .report_options import clean_prefix


class TrialBalanceAccountPrefix(models.TransientModel):
    """One account-code prefix typed in the wizard's Accounts field.

    The wizard shows these records as tags, so the user can type several
    prefixes. Each prefix is trimmed and checked when it is created, and a
    record rule keeps them private to the user who typed them.
    """

    _name = "azk_dynamic_trial_balance.account.prefix"
    _description = "Dynamic Trial Balance Account Prefix"

    name = fields.Char(
        string="Prefix",
        required=True,
        help="The start of the account codes to include.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if "name" in vals:
                vals["name"] = clean_prefix(self.env, vals["name"])
        return super().create(vals_list)

    def write(self, vals):
        if "name" in vals:
            vals = dict(vals, name=clean_prefix(self.env, vals["name"]))
        return super().write(vals)
