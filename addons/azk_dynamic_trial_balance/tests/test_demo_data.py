"""The installable demo data of the Dynamic Trial Balance (Stage 09).

The assessment asks for demo data with posted and unposted entries, other
currencies, analytic accounts and a chart deep enough for the hierarchy.
``demo/trial_balance_demo.xml`` runs ``_create_demo_data`` when the module is
installed with demo data (never on an upgrade: Odoo loads demo files as
noupdate data). The function must still create the records once only,
whoever calls it again.
"""
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged

DEMO_COMPANY = "azk_dynamic_trial_balance.demo_company"


@tagged("post_install", "-at_install")
class TestDemoData(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref(DEMO_COMPANY)
        cls.moves = cls.env["account.move"].search(
            [("company_id", "=", cls.company.id), ("ref", "=like", "TB Demo:%")])

    def counts(self):
        company = [("company_id", "=", self.company.id)]
        return {
            "companies": self.env["res.company"].search_count([("name", "=", self.company.name)]),
            "moves": self.env["account.move"].search_count([*company, ("ref", "=like", "TB Demo:%")]),
            "groups": self.env["account.group"].search_count(company),
            "analytic accounts": self.env["account.analytic.account"].search_count(company),
            "plans": self.env["account.analytic.plan"].search_count(
                [("name", "in", ("Demo Departments", "Demo Projects"))]),
            "rates": self.env["res.currency.rate"].search_count(company),
        }

    def test_the_demo_company_covers_the_assessment_cases(self):
        self.assertEqual(self.company.currency_id.name, "EGP")
        # An Egyptian company: the generic chart must not make it American.
        self.assertEqual(self.company.country_id.code, "EG")
        self.assertEqual(self.company.chart_template, "generic_coa")
        states = self.moves.mapped("state")
        self.assertEqual({state: states.count(state) for state in set(states)},
                         {"posted": 13, "draft": 2, "cancel": 1})
        egp = self.company.currency_id
        self.assertTrue(all(move.line_ids and egp.is_zero(sum(move.line_ids.mapped("balance")))
                            for move in self.moves))
        lines = self.moves.line_ids
        self.assertEqual(set(lines.currency_id.mapped("name")), {"EGP", "USD", "EUR"})
        self.assertTrue(lines.filtered("analytic_distribution"))
        # Account groups five levels deep above Bank 101401.
        Account = self.env["account.account"].with_company(self.company)
        bank = Account.search([("code", "=", "101401"), *Account._check_company_domain(self.company)])
        chain, group = [], bank.group_id
        while group:
            chain.append(group.code_prefix_start)
            group = group.parent_id
        self.assertEqual(chain, ["10140", "1014", "101", "10", "1"])

    def test_the_demo_company_reproduces_the_bank_example(self):
        admin = self.env.ref("base.user_admin")
        Engine = self.env["azk_dynamic_trial_balance.engine"].with_user(admin).with_context(
            allowed_company_ids=self.company.ids)
        Account = self.env["account.account"].with_company(self.company)
        bank = Account.search([("code", "=", "101401"), *Account._check_company_domain(self.company)])
        for drafts, expected in ((False, 1200.0), (True, 1000.0)):
            with self.subTest(drafts=drafts):
                result = Engine.compute({"date_from": "2026-01-01", "date_to": "2026-01-31",
                                         "company_id": self.company.id, "include_unposted": drafts})
                row = next(row for row in result["leaf_rows"] if row["account_id"] == bank.id)
                self.assertEqual((row["initial_balance"], row["debit"], row["ending_balance"]),
                                 (1000.0, 500.0, expected))

    def test_a_new_demo_company_installs_no_localization(self):
        # Regression (Stage 10): outside tests and module loading, as in the
        # documented one-time call from an Odoo shell, a new company with a
        # country makes Odoo install that country's localization (a commit)
        # and queue its chart. Odoo skips this while a chart is being loaded
        # (context chart_template_load), and the demo function sets that flag.
        # In tests Odoo never installs; the spy sees what the hook was asked.
        self.company.name = "AZK Trial Balance Demo (earlier)"
        self.env["ir.model.data"].search([("module", "=", "azk_dynamic_trial_balance"),
                                          ("name", "=", "demo_company")]).unlink()
        Company = type(self.env["res.company"])
        original, flags = Company.install_l10n_modules, []

        def spy(companies):
            flags.append(bool(companies.env.context.get("chart_template_load")))
            return original(companies)

        # Only the company matters here: no second set of analytic plans (their
        # fields would share labels with the first ones) and no entries.
        Demo = type(self.env["azk_dynamic_trial_balance.demo"])
        with patch.object(Company, "install_l10n_modules", spy), \
                patch.object(Demo, "_demo_analytic_accounts", lambda demo, company: {}), \
                patch.object(Demo, "_demo_entries", lambda demo, *args: None):
            self.assertTrue(self.env["azk_dynamic_trial_balance.demo"]._create_demo_data())
        new = self.env.ref(DEMO_COMPANY)
        self.assertNotEqual(new, self.company)
        self.assertTrue(flags)
        self.assertTrue(all(flags), flags)
        self.assertEqual((new.country_id.code, new.chart_template, new.currency_id.name),
                         ("EG", "generic_coa", "EGP"))
        self.assertFalse(new.env.context.get("chart_template_load"))

    def test_running_the_demo_function_again_creates_nothing(self):
        before = self.counts()
        self.assertEqual(before["companies"], 1)
        self.assertFalse(self.env["azk_dynamic_trial_balance.demo"]._create_demo_data())
        self.assertEqual(self.counts(), before)
