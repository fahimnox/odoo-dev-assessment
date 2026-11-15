from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import date_utils

from .report_options import ACCOUNT_LEVELS, check_combination, check_company, normalize_options

# Help texts given by the assessment (Exercise 2, part 1.1), word for word.
HELP_ACCOUNTS = (
    "Specify the account prefix to view only matching accounts. If no prefix is "
    "entered, all accounts will be displayed."
)
HELP_JOURNALS = (
    "Select specific journals to include in the report, or leave the field empty "
    "to include all journals."
)
HELP_ANALYTIC_ACCOUNTS = (
    "Select specific analytic accounts to include in the report, or leave the "
    "field empty to include all."
)
HELP_SKIP_ZERO_BALANCE = (
    "Select this option to hide accounts that have neither an initial balance nor "
    "any transactions in this report."
)
HELP_SHOW_AMOUNT_CURRENCY = (
    "Enable this option to group the report by Account, followed by Amount "
    "Currency. This will show the sum of the Amount Currency for each account in "
    "its respective currency. Essentially, this option provides a breakdown of "
    "account balances by the transaction currency used."
)
# Our one added sentence: the date scope of the column (decision D-11).
HELP_AMOUNT_CURRENCY_SCOPE = (
    " The Amount Currency column sums the journal items dated from Date From to "
    "Date To."
)


class TrialBalanceWizard(models.TransientModel):
    """The Dynamic Trial Balance wizard (Exercise 2, part 1.1).

    A transient record holds one user's choices for one report. Its buttons
    turn the choices into validated, plain option values
    (``_get_report_options``); the calculation and the Preview, PDF and XLSX
    outputs consume those values in later stages. A record rule keeps each
    wizard private to the user who created it.
    """

    _name = "azk_dynamic_trial_balance.wizard"
    _description = "Dynamic Trial Balance"
    _check_company_auto = True

    date_from = fields.Date(
        string="Date From",
        required=True,
        default=lambda self: date_utils.start_of(fields.Date.context_today(self), "month"),
        help="First day of the report period. Journal items dated on this day "
             "belong to the period.",
    )
    date_to = fields.Date(
        string="Date To",
        required=True,
        default=lambda self: date_utils.end_of(fields.Date.context_today(self), "month"),
        help="Last day of the report period. Journal items dated on this day "
             "belong to the period.",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        help="The report covers this company only. Choose one of the companies "
             "selected in the company switcher.",
    )
    # A plain field with a default, not a computed one: the form of a new
    # record shows defaults, and a computed field without dependencies came
    # back unticked there (seen in the Stage 07 browser check). The
    # calculation never reads it; posted items are always in scope.
    posted_entries = fields.Boolean(
        string="Posted Entries",
        default=True,
        readonly=True,
        help="Posted journal entries are always included.",
    )
    include_unposted = fields.Boolean(
        string="Include Unposted Entries",
        help="Also include draft journal entries, as the standard Trial Balance "
             "does. Cancelled entries are never included.",
    )
    hierarchy_subtotals = fields.Boolean(
        string="Hierarchy and Subtotals",
        help="Show the accounts under their account groups, with a subtotal line "
             "for each group, as the standard Trial Balance does. Accounts without "
             "a group are shown under (No Group).",
    )
    hierarchy_only_parents = fields.Boolean(
        string="Hierarchy Only Parents",
        help="Show only the account-group lines, down to the level chosen in "
             "Account Level Up To, without account lines. Each group line still "
             "includes every account below it, and accounts without a group are "
             "shown as (No Group). Needs Hierarchy and Subtotals; not available "
             "with Show Amount Currency.",
    )
    account_level = fields.Selection(
        ACCOUNT_LEVELS,
        string="Account Level Up To",
        help="Deepest account-group level to show: 1 shows only the top groups, "
             "5 shows groups down to the fifth level.",
    )
    account_prefix_ids = fields.Many2many(
        "azk_dynamic_trial_balance.account.prefix",
        relation="azk_dtb_wizard_prefix_rel",
        column1="wizard_id",
        column2="prefix_id",
        string="Accounts",
        help=HELP_ACCOUNTS,
    )
    journal_id = fields.Many2one(
        "account.journal",
        string="Journals",
        check_company=True,
        help=HELP_JOURNALS,
    )
    analytic_account_id = fields.Many2one(
        "account.analytic.account",
        string="Analytic Accounts",
        check_company=True,
        help=HELP_ANALYTIC_ACCOUNTS,
    )
    skip_zero_balance = fields.Boolean(
        string="Skip Zero Balance",
        help=HELP_SKIP_ZERO_BALANCE,
    )
    show_amount_currency = fields.Boolean(
        string="Show Amount Currency",
        help=HELP_SHOW_AMOUNT_CURRENCY + HELP_AMOUNT_CURRENCY_SCOPE,
    )

    @api.constrains("posted_entries")
    def _check_posted_entries(self):
        # The assessment fixes this option: posted entries are always included.
        if not all(self.mapped("posted_entries")):
            raise ValidationError(_("Posted entries are always included."))

    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        for wizard in self:
            if wizard.date_from and wizard.date_to and wizard.date_from > wizard.date_to:
                raise ValidationError(_("Date From must be on or before Date To."))

    @api.constrains("company_id")
    def _check_company_is_usable(self):
        for wizard in self:
            check_company(self.env, wizard.company_id.id)

    @api.constrains(
        "hierarchy_subtotals", "hierarchy_only_parents", "account_level",
        "show_amount_currency",
    )
    def _check_option_combination(self):
        for wizard in self:
            check_combination(
                self.env,
                wizard.hierarchy_subtotals,
                wizard.hierarchy_only_parents,
                int(wizard.account_level) if wizard.account_level else None,
                wizard.show_amount_currency,
            )

    @api.onchange("hierarchy_subtotals")
    def _onchange_hierarchy_subtotals(self):
        if not self.hierarchy_subtotals:
            self.hierarchy_only_parents = False
            self.account_level = False

    @api.onchange("hierarchy_only_parents")
    def _onchange_hierarchy_only_parents(self):
        if self.hierarchy_only_parents:
            self.show_amount_currency = False
        else:
            self.account_level = False

    @api.onchange("show_amount_currency")
    def _onchange_show_amount_currency(self):
        if self.show_amount_currency:
            self.hierarchy_only_parents = False
            self.account_level = False

    def _get_report_options(self):
        """Return this wizard's choices as validated, plain option values.

        Posted entries are not an option: the calculation always includes
        them. The values are checked again in ``normalize_options`` with the
        caller's current access, so a wizard that was valid when it was saved
        but no longer is (for example, its company was switched off) is
        refused.
        """
        self.ensure_one()
        return normalize_options(self.env, {
            "date_from": self.date_from,
            "date_to": self.date_to,
            "company_id": self.company_id.id,
            "include_unposted": self.include_unposted,
            "hierarchy_subtotals": self.hierarchy_subtotals,
            "hierarchy_only_parents": self.hierarchy_only_parents,
            "account_level": int(self.account_level) if self.account_level else None,
            "account_prefixes": self.account_prefix_ids.mapped("name"),
            "journal_id": self.journal_id.id or None,
            "analytic_account_id": self.analytic_account_id.id or None,
            "skip_zero_balance": self.skip_zero_balance,
            "show_amount_currency": self.show_amount_currency,
        })

    def _output_not_available(self, output):
        # Entry point only: the options are validated, but the calculation
        # (Stage 08) and the outputs (Stage 09) are not built yet. Saying so
        # is better than a button that seems to work.
        self._get_report_options()
        raise UserError(_(
            "%(output)s is not available yet. Your options are valid, but the "
            "report calculation and its outputs are still being built.",
            output=output,
        ))

    def action_preview(self):
        return self._output_not_available(_("The Preview"))

    def action_export_pdf(self):
        return self._output_not_available(_("The PDF export"))

    def action_export_xlsx(self):
        return self._output_not_available(_("The XLSX export"))
