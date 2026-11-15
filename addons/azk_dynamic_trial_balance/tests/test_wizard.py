import json

from odoo import Command, fields
from odoo.addons.azk_dynamic_trial_balance.models.report_options import normalize_options
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import Form, new_test_user, tagged
from odoo.tools import date_utils

from .common import TrialBalanceCase

WIZARD = "azk_dynamic_trial_balance.wizard"
PREFIX = "azk_dynamic_trial_balance.account.prefix"

# The assessment's help texts (Exercise 2, part 1.1), typed here from the PDF
# so that the test does not read them from the code it checks.
PDF_HELP = {
    "account_prefix_ids": "Specify the account prefix to view only matching accounts. "
                          "If no prefix is entered, all accounts will be displayed.",
    "journal_id": "Select specific journals to include in the report, or leave the "
                  "field empty to include all journals.",
    "analytic_account_id": "Select specific analytic accounts to include in the report, "
                           "or leave the field empty to include all.",
    "skip_zero_balance": "Select this option to hide accounts that have neither an "
                         "initial balance nor any transactions in this report.",
    "show_amount_currency": "Enable this option to group the report by Account, followed "
                            "by Amount Currency. This will show the sum of the Amount "
                            "Currency for each account in its respective currency. "
                            "Essentially, this option provides a breakdown of account "
                            "balances by the transaction currency used.",
}


@tagged("post_install", "-at_install")
class TestTrialBalanceWizard(TrialBalanceCase):
    """TP-TB-01: the wizard's fields, validation, privacy and entry points."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        egp = cls.company.currency_id
        data_2 = cls.setup_other_company(name="AZK TB Second Company", currency_id=egp.id)
        cls.company_2 = data_2["company"]
        cls.journal_2 = data_2["default_journal_misc"]
        su_env = cls.env(su=True)
        readers = "base.group_user,account.group_account_readonly"
        cls.reader = new_test_user(
            su_env, login="tb_wizard_reader", groups=readers,
            company_id=cls.company.id, company_ids=[Command.set(cls.company.ids)])
        cls.other_reader = new_test_user(
            su_env, login="tb_wizard_other_reader", groups=readers,
            company_id=cls.company.id, company_ids=[Command.set(cls.company.ids)])
        cls.two_company_reader = new_test_user(
            su_env, login="tb_wizard_two_companies", groups=readers,
            company_id=cls.company.id,
            company_ids=[Command.set((cls.company + cls.company_2).ids)])
        cls.employee = new_test_user(
            su_env, login="tb_wizard_employee", groups="base.group_user",
            company_id=cls.company.id, company_ids=[Command.set(cls.company.ids)])
        plan = su_env["account.analytic.plan"].create({"name": "TB Wizard Plan"})
        Analytic = su_env["account.analytic.account"]
        cls.analytic_shared = Analytic.create({"name": "TB Shared", "plan_id": plan.id})
        cls.analytic_company_2 = Analytic.create(
            {"name": "TB Company 2 only", "plan_id": plan.id, "company_id": cls.company_2.id})

    def _wizard(self, user=None, companies=None, **values):
        Wizard = self.env[WIZARD].with_user(user or self.reader)
        Wizard = Wizard.with_context(allowed_company_ids=(companies or self.company).ids)
        return Wizard.create({"date_from": "2026-01-01", "date_to": "2026-01-31", **values})

    def _raw(self, **values):
        raw = {"date_from": "2026-01-01", "date_to": "2026-01-31",
               "company_id": self.company.id}
        raw.update(values)
        return raw

    def _normalize(self, raw, user=None, companies=None):
        env = self.env(user=user or self.reader)
        env = env(context=dict(env.context, allowed_company_ids=(companies or self.company).ids))
        return normalize_options(env, raw)

    # ------------------------------------------------------------------
    # Fields and defaults
    # ------------------------------------------------------------------
    def test_defaults_cover_the_current_month(self):
        wizard = self.env[WIZARD].with_user(self.reader).create({})
        today = fields.Date.context_today(wizard)
        self.assertEqual(wizard.date_from, date_utils.start_of(today, "month"))
        self.assertEqual(wizard.date_to, date_utils.end_of(today, "month"))
        self.assertEqual(wizard.company_id, self.company)
        self.assertTrue(wizard.posted_entries)
        for name in ("include_unposted", "hierarchy_subtotals", "hierarchy_only_parents",
                     "account_level", "skip_zero_balance", "show_amount_currency"):
            self.assertFalse(wizard[name], name)
        self.assertFalse(wizard.account_prefix_ids or wizard.journal_id or wizard.analytic_account_id)
        # Posted entries cannot be switched off, even through an RPC write.
        with self.assertRaises(ValidationError):
            wizard.write({"posted_entries": False})

    def test_options_are_plain_validated_values(self):
        wizard = self._wizard(
            include_unposted=True, hierarchy_subtotals=True, hierarchy_only_parents=True,
            account_level="3", skip_zero_balance=True, journal_id=self.misc_journal.id,
            analytic_account_id=self.analytic_shared.id,
            account_prefix_ids=[Command.create({"name": " 10 "}), Command.create({"name": "4"}),
                                Command.create({"name": "10"})],
        )
        options = wizard.with_user(self.reader).with_context(
            allowed_company_ids=self.company.ids)._get_report_options()
        self.assertEqual(options, {
            "date_from": "2026-01-01",
            "date_to": "2026-01-31",
            "company_id": self.company.id,
            "include_unposted": True,
            "hierarchy_subtotals": True,
            "hierarchy_only_parents": True,
            "account_level": 3,
            "account_prefixes": ["10", "4"],
            "journal_id": self.misc_journal.id,
            "analytic_account_id": self.analytic_shared.id,
            "skip_zero_balance": True,
            "show_amount_currency": False,
        })
        self.assertNotIn("posted_entries", options)

    def test_journal_and_analytic_account_are_single_choices(self):
        Wizard = self.env[WIZARD]
        self.assertEqual(Wizard._fields["journal_id"].type, "many2one")
        self.assertEqual(Wizard._fields["journal_id"].comodel_name, "account.journal")
        self.assertEqual(Wizard._fields["analytic_account_id"].type, "many2one")
        self.assertEqual(Wizard._fields["analytic_account_id"].comodel_name,
                         "account.analytic.account")
        options = self._normalize(self._raw())
        self.assertIsNone(options["journal_id"])
        self.assertIsNone(options["analytic_account_id"])
        self.assertEqual(options["account_prefixes"], [])

    def test_help_texts_follow_the_assessment(self):
        Wizard = self.env[WIZARD]
        for name, text in PDF_HELP.items():
            with self.subTest(field=name):
                if name == "show_amount_currency":
                    # The PDF text, then one sentence on the column's dates (D-11).
                    self.assertTrue(Wizard._fields[name].help.startswith(text))
                    self.assertIn("from Date From to Date To", Wizard._fields[name].help)
                else:
                    self.assertEqual(Wizard._fields[name].help, text)
        for name in ("date_from", "date_to", "company_id", "posted_entries", "include_unposted",
                     "hierarchy_subtotals", "hierarchy_only_parents", "account_level"):
            self.assertTrue(Wizard._fields[name].help, name)
        self.assertIn("Cancelled entries are never included",
                      Wizard._fields["include_unposted"].help)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    def test_dates_must_be_in_order(self):
        self._wizard(date_from="2026-01-31", date_to="2026-01-31")
        with self.assertRaises(ValidationError):
            self._wizard(date_from="2026-02-01", date_to="2026-01-31")
        wizard = self._wizard()
        with self.assertRaises(ValidationError):
            wizard.with_user(self.reader).date_to = "2025-12-31"
        for raw in (self._raw(date_from=False), self._raw(date_to="2026-13-01"),
                    self._raw(date_from="2026-02-01")):
            with self.subTest(raw=raw), self.assertRaises(ValidationError):
                self._normalize(raw)

    def test_company_must_be_authorized_and_active(self):
        # A company the user may not access at all.
        with self.assertRaises(AccessError):
            self._wizard(company_id=self.company_2.id)
        with self.assertRaises(AccessError):
            self._normalize(self._raw(company_id=self.company_2.id))
        # A company the user may access, but which is not active.
        with self.assertRaises(ValidationError):
            self._wizard(user=self.two_company_reader, company_id=self.company_2.id)
        both = self.company + self.company_2
        wizard = self._wizard(user=self.two_company_reader, companies=both,
                              company_id=self.company_2.id)
        options = wizard.with_user(self.two_company_reader).with_context(
            allowed_company_ids=both.ids)._get_report_options()
        self.assertEqual(options["company_id"], self.company_2.id)
        # The same wizard is refused once the company is switched off.
        with self.assertRaises(ValidationError):
            wizard.with_user(self.two_company_reader).with_context(
                allowed_company_ids=self.company.ids)._get_report_options()
        for value in ("1", None, True):
            with self.subTest(company=value), self.assertRaises(ValidationError):
                self._normalize(self._raw(company_id=value))

    def test_journal_and_analytic_account_must_suit_the_company(self):
        with self.assertRaises(UserError):
            self._wizard(journal_id=self.journal_2.id)
        with self.assertRaises(UserError):
            self._wizard(analytic_account_id=self.analytic_company_2.id)
        both = self.company + self.company_2
        for raw in (self._raw(journal_id=self.journal_2.id),
                    self._raw(analytic_account_id=self.analytic_company_2.id),
                    self._raw(journal_id="1"), self._raw(journal_id=10 ** 9)):
            with self.subTest(raw=raw), self.assertRaises(ValidationError):
                self._normalize(raw, user=self.two_company_reader, companies=both)
        options = self._normalize(self._raw(analytic_account_id=self.analytic_shared.id))
        self.assertEqual(options["analytic_account_id"], self.analytic_shared.id)

    def test_option_combinations(self):
        valid = [
            {},
            {"include_unposted": True, "hierarchy_subtotals": True},
            {"hierarchy_subtotals": True, "show_amount_currency": True},
            {"hierarchy_subtotals": True, "hierarchy_only_parents": True, "account_level": "1",
             "skip_zero_balance": True, "include_unposted": True},
            {"hierarchy_subtotals": True, "hierarchy_only_parents": True, "account_level": "5"},
        ]
        for values in valid:
            with self.subTest(valid=values):
                self._wizard(**values)
        invalid = [
            {"hierarchy_only_parents": True, "account_level": "2"},
            {"hierarchy_subtotals": True, "hierarchy_only_parents": True},
            {"hierarchy_subtotals": True, "account_level": "2"},
            {"account_level": "2"},
            {"hierarchy_subtotals": True, "hierarchy_only_parents": True, "account_level": "2",
             "show_amount_currency": True},
        ]
        for values in invalid:
            with self.subTest(invalid=values), self.assertRaises(ValidationError):
                self._wizard(**values)
        only_parents = {"hierarchy_subtotals": True, "hierarchy_only_parents": True}
        for level in (0, 6, True, "x", 2.5):
            with self.subTest(level=level), self.assertRaises(ValidationError):
                self._normalize(self._raw(account_level=level, **only_parents))
        for key in ("include_unposted", "skip_zero_balance"):
            with self.subTest(key=key), self.assertRaises(ValidationError):
                self._normalize(self._raw(**{key: "false"}))
        with self.assertRaises(ValidationError):
            self._normalize(self._raw(posted_entries=False))

    def test_onchanges_keep_the_combination_valid(self):
        form = Form(self.env[WIZARD].with_user(self.reader))
        # Regression (Stage 07 browser check): the new form must already show
        # Posted Entries ticked, before anything is saved.
        self.assertTrue(form.posted_entries)
        form.hierarchy_subtotals = True
        form.hierarchy_only_parents = True
        form.account_level = "2"
        form.show_amount_currency = True
        self.assertFalse(form.hierarchy_only_parents)
        self.assertFalse(form.account_level)
        form.hierarchy_only_parents = True
        self.assertFalse(form.show_amount_currency)
        form.account_level = "4"
        form.hierarchy_subtotals = False
        self.assertFalse(form.hierarchy_only_parents)
        self.assertFalse(form.account_level)
        form.save()

    def test_prefixes_are_literal_code_prefixes(self):
        Prefix = self.env[PREFIX].with_user(self.reader)
        self.assertEqual(Prefix.create({"name": " 4 "}).name, "4")
        self.assertEqual(Prefix.browse(Prefix.name_create(" 10.1 ")[0]).name, "10.1")
        refused = ["", "   ", "1_", "1%", "10%", "1\\", "10 20", "4*", "x" * 65]
        for value in refused:
            with self.subTest(prefix=value), self.assertRaises(ValidationError):
                Prefix.create({"name": value})
        self.assertEqual(len(Prefix.create({"name": "1" * 64}).name), 64)
        options = self._normalize(self._raw(account_prefixes=["10", " 4", "10", "4 "]))
        self.assertEqual(options["account_prefixes"], ["10", "4"])
        for value in (["1_"], "10", [10]):
            with self.subTest(prefixes=value), self.assertRaises(ValidationError):
                self._normalize(self._raw(account_prefixes=value))

    def test_raw_options_are_not_trusted(self):
        for raw in (None, [], self._raw(domain=[("id", ">", 0)])):
            with self.subTest(raw=raw), self.assertRaises(ValidationError):
                self._normalize(raw)

    def test_messages_are_translated_without_warnings(self):
        # Regression (Stage 07, run 1): the option helpers have no ``self``,
        # so a bare _() could not find the language and logged a warning on
        # every call. They use env._() now.
        with self.assertNoLogs("odoo.tools.translate", level="WARNING"):
            self._normalize(self._raw(account_prefixes=["10"]))
            for raw in (self._raw(date_from="2026-02-01"), self._raw(date_to=False),
                        self._raw(account_prefixes=["1_"]), self._raw(account_level=9)):
                with self.assertRaises(ValidationError):
                    self._normalize(raw)
            with self.assertRaises(ValidationError):
                self.env[PREFIX].with_user(self.reader).create({"name": "1%"})

    # ------------------------------------------------------------------
    # Privacy and access
    # ------------------------------------------------------------------
    def test_wizards_are_private_to_their_creator(self):
        wizard = self._wizard(account_prefix_ids=[Command.create({"name": "10"})])
        prefix = wizard.with_user(self.reader).account_prefix_ids
        foreign = wizard.with_user(self.other_reader)
        with self.assertRaises(AccessError):
            foreign.read(["date_from"])
        with self.assertRaises(AccessError):
            foreign.action_preview()
        with self.assertRaises(AccessError):
            foreign.write({"date_to": "2026-02-28"})
        with self.assertRaises(AccessError):
            prefix.with_user(self.other_reader).read(["name"])
        self.assertFalse(self.env[WIZARD].with_user(self.other_reader).search([("id", "=", wizard.id)]))

    def test_users_without_accounting_access_cannot_use_it(self):
        with self.assertRaises(AccessError):
            self.env[WIZARD].with_user(self.employee).create({})
        with self.assertRaises(AccessError):
            self.env[PREFIX].with_user(self.employee).create({"name": "10"})

    # ------------------------------------------------------------------
    # Entry points and menu
    # ------------------------------------------------------------------
    def test_output_buttons_open_the_report_with_the_wizard_options(self):
        # Stage 09: the buttons are connected (they validated, then said "not
        # available yet", until Stage 08).
        wizard = self._wizard(include_unposted=True, skip_zero_balance=True).with_user(
            self.reader).with_context(allowed_company_ids=self.company.ids)
        report = self.env.ref("azk_dynamic_trial_balance.dynamic_trial_balance_report")
        preview = wizard.action_preview()
        self.assertEqual((preview["type"], preview["tag"]), ("ir.actions.client", "account_report"))
        self.assertEqual(preview["context"]["report_id"], report.id)
        options = preview["params"]["options"]
        self.assertTrue(preview["params"]["ignore_session"])
        self.assertEqual(options["date"]["date_from"], "2026-01-01")
        self.assertTrue(options["all_entries"])
        self.assertEqual(options["azk_tb"]["company_id"], self.company.id)
        self.assertTrue(options["azk_tb"]["skip_zero_balance"])
        for method, generator in (("action_export_pdf", "export_to_pdf"),
                                  ("action_export_xlsx", "export_to_xlsx")):
            with self.subTest(button=method):
                action = getattr(wizard, method)()
                self.assertEqual(action["type"], "ir_actions_account_report_download")
                self.assertEqual(action["data"]["file_generator"], generator)
                sent = json.loads(action["data"]["options"])
                self.assertEqual(sent["report_id"], report.id)
                self.assertEqual(sent["azk_tb"]["company_id"], self.company.id)
        # Invalid options are refused before any action is returned.
        both = self.company + self.company_2
        wizard_2 = self._wizard(user=self.two_company_reader, companies=both,
                                company_id=self.company_2.id)
        for method in ("action_preview", "action_export_pdf", "action_export_xlsx"):
            with self.subTest(refused=method), self.assertRaises(ValidationError):
                getattr(wizard_2.with_user(self.two_company_reader).with_context(
                    allowed_company_ids=self.company.ids), method)()

    def test_menu_opens_the_wizard_next_to_the_standard_trial_balance(self):
        menu = self.env.ref("azk_dynamic_trial_balance.menu_dynamic_trial_balance")
        self.assertEqual(menu.parent_id,
                         self.env.ref("account_reports.account_reports_audit_reports_menu"))
        self.assertEqual(menu.groups_id, self.env.ref("account.group_account_readonly"))
        action = menu.action
        self.assertEqual((action.res_model, action.target, action.view_mode),
                         (WIZARD, "new", "form"))
        self.assertEqual(menu.with_user(self.reader).complete_name,
                         "Accounting/Reporting/Audit Reports/Dynamic Trial Balance")
        visible = self.env["ir.ui.menu"].with_user(self.reader)._visible_menu_ids()
        self.assertIn(menu.id, visible)
        hidden = self.env["ir.ui.menu"].with_user(self.employee)._visible_menu_ids()
        self.assertNotIn(menu.id, hidden)
