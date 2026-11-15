"""Advanced fixtures, kept apart from TB-BASE so its numbers stay simple.

Each class builds one fixture in its own fresh company from real, balanced
entries, checks that the data is what the hand calculation assumes, and,
where the standard Trial Balance has the same option, compares it with the
hand-calculated constants of tests/common.py. Our own calculation is
compared with the same constants in Stage 08; options that only our report
has (currency rows, Skip Zero Balance, Hierarchy Only Parents) wait for it.
"""
from datetime import date

from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import new_test_user, tagged

from .common import (
    TB_A_MARCH,
    TB_A_PROPORTIONAL_EXPENSE,
    TB_C_JANUARY,
    TB_C_JANUARY_AMOUNT_CURRENCY,
    TB_C_JANUARY_BY_CURRENCY,
    TB_H_ACCOUNTS,
    TB_H_GROUPS,
    TB_H_LEVELS,
    TB_H_ONLY_PARENTS,
    TB_M_COMPANY_1,
    TB_M_COMPANY_2,
    TB_R_EVERYTHING,
    TB_R_VISIBLE,
    TB_Z_JANUARY,
    TB_Z_UNTOUCHED,
    TrialBalanceCase,
)


@tagged("post_install", "-at_install")
class TestZeroActivityFixture(TrialBalanceCase):
    """TB-Z: an account whose debit and credit movements cancel out."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        a = cls.accounts
        cls._entry("2025-12-31", [(a["bank"], 1000, 0), (a["capital"], 0, 1000)], ref="TB-Z opening")
        cls._entry("2026-01-05", [(a["current_assets"], 250, 0), (a["bank"], 0, 250)], ref="TB-Z out")
        cls._entry("2026-01-15", [(a["bank"], 250, 0), (a["current_assets"], 0, 250)], ref="TB-Z back")

    def test_hand_calculations_are_consistent(self):
        self.assertExpectationsConsistent(TB_Z_JANUARY)
        # Opening, ending and net movement are all zero, but the account moved.
        row = TB_Z_JANUARY["current_assets"]
        self.assertEqual((row[2], row[5], row[8]), (0, 0, 0))
        self.assertEqual((row[3], row[4]), (250, 250))
        self.assertEqual(TB_Z_UNTOUCHED, (0,) * 9)

    def test_untouched_account_has_no_journal_items(self):
        count = self.env["account.move.line"].search_count(
            [("account_id", "=", self.accounts["prepaid"].id)])
        self.assertEqual(count, 0)

    def test_native_report_keeps_the_zero_net_account(self):
        native = self.native_trial_balance("2026-01-01", "2026-01-31")
        self.assertSameLines(native, TB_Z_JANUARY)
        self.assertNativeMatches(native, TB_Z_JANUARY)


@tagged("post_install", "-at_install")
class TestCurrencyFixture(TrialBalanceCase):
    """TB-C: journal items in USD and EUR on one account, in an EGP company."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Rates for this company only (a rate is units of currency per EGP).
        # Other companies' rates are left alone.
        cls.usd = cls._enable_currency("USD")
        cls.eur = cls._enable_currency("EUR")
        cls.env["res.currency.rate"].sudo().create([
            {"name": "2025-01-01", "currency_id": cls.usd.id, "company_id": cls.company.id,
             "rate": 1 / 50},
            {"name": "2025-01-01", "currency_id": cls.eur.id, "company_id": cls.company.id,
             "rate": 1 / 55},
        ])
        x, bank = cls.accounts["current_assets"], cls.accounts["bank"]
        usd, eur = cls.usd.id, cls.eur.id

        def foreign(currency, amount):
            return {"currency_id": currency, "amount_currency": amount}

        cls._entry("2025-12-20", [(x, 1000, 0, foreign(usd, 20)), (bank, 0, 1000)], ref="TB-C C1")
        cls._entry("2025-12-22", [(bank, 1650, 0), (x, 0, 1650, foreign(eur, -30))], ref="TB-C C2")
        cls._entry("2026-01-05", [(x, 5000, 0, foreign(usd, 100)), (bank, 0, 5000)], ref="TB-C C3")
        cls._entry("2026-01-12", [(bank, 2000, 0), (x, 0, 2000, foreign(usd, -40))], ref="TB-C C4")
        cls._entry("2026-01-18", [(x, 3850, 0, foreign(eur, 70)), (bank, 0, 3850)], ref="TB-C C5")
        cls._entry("2026-01-25", [(bank, 1100, 0), (x, 0, 1100, foreign(eur, -20))], ref="TB-C C6")

    def test_company_amounts_follow_the_exchange_rates(self):
        egp = self.company.currency_id
        for currency, amount, expected in ((self.usd, 100, 5000), (self.usd, 20, 1000),
                                           (self.eur, 70, 3850), (self.eur, 30, 1650)):
            with self.subTest(currency=currency.name, amount=amount):
                self.assertEqual(
                    currency._convert(amount, egp, self.company, date(2026, 1, 5)), expected)

    def test_fixture_keeps_each_currency_separate(self):
        groups = self.env["account.move.line"]._read_group(
            [("company_id", "=", self.company.id), ("parent_state", "=", "posted"),
             ("date", ">=", "2026-01-01"), ("date", "<=", "2026-01-31")],
            ["account_id", "currency_id"],
            ["amount_currency:sum", "debit:sum", "credit:sum"],
        )
        names = {account: name for name, account in self.accounts.items()}
        found = {(names[account], currency.name): (amount, debit, credit)
                 for account, currency, amount, debit, credit in groups}
        self.assertEqual(found, {
            ("current_assets", "USD"): (60.0, 5000.0, 2000.0),
            ("current_assets", "EUR"): (50.0, 3850.0, 1100.0),
            ("bank", "EGP"): (-5750.0, 3100.0, 8850.0),
        })
        self.assertEqual(
            {key: value[0] for key, value in found.items()}, TB_C_JANUARY_AMOUNT_CURRENCY)

    def test_hand_calculations_are_consistent(self):
        self.assertExpectationsConsistent(TB_C_JANUARY)
        self.assertExpectationsConsistent(TB_C_JANUARY_BY_CURRENCY)
        # Signed balances and gross movements reconcile across the two
        # groupings: the USD and EUR rows add up to the account row.
        usd = TB_C_JANUARY_BY_CURRENCY[("current_assets", "USD")]
        eur = TB_C_JANUARY_BY_CURRENCY[("current_assets", "EUR")]
        for index in (2, 3, 4, 5, 8):
            self.assertEqual(usd[index] + eur[index], TB_C_JANUARY["current_assets"][index])
        # Net display totals depend on the grain of netting: the opening is
        # 1,000 debit (USD row) and 1,650 credit (EUR row), but 650 credit
        # for the account as a whole.
        self.assertEqual(TB_C_JANUARY_BY_CURRENCY["total"][:2], (1650, 1650))
        self.assertEqual(TB_C_JANUARY["total"][:2], (650, 650))

    def test_native_report_in_company_currency(self):
        native = self.native_trial_balance("2026-01-01", "2026-01-31")
        self.assertSameLines(native, TB_C_JANUARY)
        self.assertNativeMatches(native, TB_C_JANUARY)


@tagged("post_install", "-at_install")
class TestAnalyticFixture(TrialBalanceCase):
    """TB-A: a 60/40 distribution and a composite key across two plans."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.sudo().groups_id = [
            Command.link(cls.env.ref("analytic.group_analytic_accounting").id)]
        Plan = cls.env["account.analytic.plan"].sudo()
        plan_a = Plan.create({"name": "TB Plan A"})
        plan_b = Plan.create({"name": "TB Plan B"})
        Analytic = cls.env["account.analytic.account"].sudo()
        cls.analytic = {
            "A1": Analytic.create({"name": "TB A1", "plan_id": plan_a.id}),
            "A2": Analytic.create({"name": "TB A2", "plan_id": plan_a.id}),
            "B1": Analytic.create({"name": "TB B1", "plan_id": plan_b.id}),
        }
        a, an = cls.accounts, cls.analytic
        cls.split = {str(an["A1"].id): 60.0, str(an["A2"].id): 40.0}
        cls.composite = {f"{an['A1'].id},{an['B1'].id}": 100.0}
        cls._entry("2026-03-10", [(a["expense"], 1000, 0, {"analytic_distribution": cls.split}),
                                  (a["bank"], 0, 1000)], ref="TB-A 60/40")
        cls._entry("2026-03-12", [(a["expense"], 200, 0, {"analytic_distribution": cls.composite}),
                                  (a["bank"], 0, 200)], ref="TB-A composite key")

    def test_fixture_distributions(self):
        lines = self.env["account.move.line"].search(
            [("company_id", "=", self.company.id), ("account_id", "=", self.accounts["expense"].id)],
            order="date")
        self.assertEqual([line.analytic_distribution for line in lines],
                         [self.split, self.composite])
        self.assertFalse(any(self.env["account.move.line"].search(
            [("company_id", "=", self.company.id),
             ("account_id", "=", self.accounts["bank"].id)]).mapped("analytic_distribution")))

    def test_hand_calculations_are_consistent(self):
        for name, table in TB_A_MARCH.items():
            with self.subTest(filter=name):
                self.assertExpectationsConsistent(table)
        # Whole-item selection versus the rejected proportional allocation.
        self.assertEqual(TB_A_MARCH["A1"]["expense"][3], 1000 + 200)
        self.assertEqual(TB_A_PROPORTIONAL_EXPENSE["A1"], 1000 * 60 // 100 + 200)

    def test_native_analytic_filter_selects_whole_items(self):
        for name, table in TB_A_MARCH.items():
            with self.subTest(filter=name):
                native = self.native_trial_balance(
                    "2026-03-01", "2026-03-31", analytic=self.analytic.get(name))
                self.assertSameLines(native, table)
                self.assertNativeMatches(native, table)


@tagged("post_install", "-at_install")
class TestMultiCompanyFixture(TrialBalanceCase):
    """TB-M: two companies; a report covers exactly one of them."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        data_2 = cls.setup_other_company(
            name="AZK TB Second Company", currency_id=cls.company.currency_id.id)
        cls.company_2 = data_2["company"]
        cls.accounts_2 = cls._chart_accounts(cls.company_2)
        a, a2 = cls.accounts, cls.accounts_2
        cls._entry("2026-01-10", [(a["bank"], 300, 0), (a["capital"], 0, 300)], ref="TB-M company 1")
        cls._entry("2026-01-12", [(a2["bank"], 900, 0), (a2["capital"], 0, 900)],
                   journal=data_2["default_journal_misc"], company=cls.company_2,
                   ref="TB-M company 2")
        cls.reader_1 = new_test_user(
            cls.env(su=True), login="tb_reader_company_1",
            groups="base.group_user,account.group_account_readonly",
            company_id=cls.company.id, company_ids=[Command.set(cls.company.ids)])

    def test_hand_calculations_are_consistent(self):
        self.assertExpectationsConsistent(TB_M_COMPANY_1)
        self.assertExpectationsConsistent(TB_M_COMPANY_2)

    def test_native_report_covers_one_company(self):
        native_1 = self.native_trial_balance("2026-01-01", "2026-01-31")
        self.assertSameLines(native_1, TB_M_COMPANY_1)
        self.assertNativeMatches(native_1, TB_M_COMPANY_1)
        native_2 = self.native_trial_balance(
            "2026-01-01", "2026-01-31", company=self.company_2, accounts=self.accounts_2)
        self.assertSameLines(native_2, TB_M_COMPANY_2)
        self.assertNativeMatches(native_2, TB_M_COMPANY_2)

    def test_a_user_cannot_report_on_another_company(self):
        with self.assertRaises(AccessError):
            self.native_trial_balance(
                "2026-01-01", "2026-01-31", company=self.company_2,
                accounts=self.accounts_2, user=self.reader_1)


@tagged("post_install", "-at_install")
class TestRestrictedAccessFixture(TrialBalanceCase):
    """TB-R: a record rule hides some journal items from one reader."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.restricted_journal = cls.env["account.journal"].create({
            "name": "Restricted", "code": "RSTR", "type": "general",
            "company_id": cls.company.id,
        })
        a = cls.accounts
        cls._entry("2026-01-10", [(a["expense"], 300, 0), (a["bank"], 0, 300)], ref="TB-R visible")
        cls._entry("2026-01-15", [(a["expense"], 70, 0), (a["bank"], 0, 70)],
                   journal=cls.restricted_journal, ref="TB-R restricted")
        cls.reader = new_test_user(
            cls.env(su=True), login="tb_restricted_reader",
            groups="base.group_user,account.group_account_readonly",
            company_id=cls.company.id, company_ids=[Command.set(cls.company.ids)])
        # A global rule (global rules always restrict; group rules would be
        # widened by the accounting groups' own rules) that applies to this
        # reader only.
        cls.env["ir.rule"].sudo().create({
            "name": "TB-R test rule: hide the Restricted journal from one reader",
            "model_id": cls.env["ir.model"]._get_id("account.move.line"),
            "domain_force": "[('journal_id.code', '!=', 'RSTR')] if user.id == %d else []"
                            % cls.reader.id,
        })

    def test_hand_calculations_are_consistent(self):
        self.assertExpectationsConsistent(TB_R_VISIBLE)
        self.assertExpectationsConsistent(TB_R_EVERYTHING)

    def test_the_rule_hides_the_items_from_the_reader(self):
        Line = self.env["account.move.line"]
        domain = [("company_id", "=", self.company.id), ("journal_id", "=", self.restricted_journal.id)]
        self.assertEqual(Line.search_count(domain), 2)
        self.assertEqual(Line.with_user(self.reader).search_count(domain), 0)

    def test_native_report_applies_record_rules(self):
        restricted = self.native_trial_balance("2026-01-01", "2026-01-31", user=self.reader)
        self.assertSameLines(restricted, TB_R_VISIBLE)
        self.assertNativeMatches(restricted, TB_R_VISIBLE)
        everything = self.native_trial_balance("2026-01-01", "2026-01-31")
        self.assertSameLines(everything, TB_R_EVERYTHING)
        self.assertNativeMatches(everything, TB_R_EVERYTHING)


@tagged("post_install", "-at_install")
class TestHierarchyFixture(TrialBalanceCase):
    """TB-H: account groups five levels deep, plus ungrouped accounts."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Group = cls.env["account.group"]
        cls.groups = {}
        for prefix, name in (("1", "Assets"), ("10", "Current Assets"),
                             ("101", "Cash and Receivables"), ("1014", "Bank and Cash"),
                             ("10140", "Bank Accounts"), ("4", "Income and Discounts")):
            cls.groups[prefix] = Group.create(
                {"name": name, "code_prefix_start": prefix, "company_id": cls.company.id})
        a = cls.accounts
        cls._entry("2025-12-31", [(a["bank"], 1000, 0), (a["capital"], 0, 1000)], ref="TB-H opening")
        cls._entry("2026-01-10", [(a["current_assets"], 400, 0), (a["bank"], 0, 400)], ref="TB-H H2")
        cls._entry("2026-01-20", [(a["bank"], 500, 0), (a["revenue"], 0, 500)], ref="TB-H H3")
        cls._entry("2026-01-22", [(a["cash_discount_loss"], 120, 0), (a["bank"], 0, 120)],
                   ref="TB-H H4")

    def _level(self, group):
        # Our definition (contract, hierarchy): number of ancestors + 1.
        level = 1
        while group.parent_id:
            group, level = group.parent_id, level + 1
        return level

    def test_groups_form_a_five_level_chain(self):
        g = self.groups
        self.assertEqual(g["10140"].parent_id, g["1014"])
        self.assertEqual(g["1014"].parent_id, g["101"])
        self.assertEqual(g["101"].parent_id, g["10"])
        self.assertEqual(g["10"].parent_id, g["1"])
        self.assertFalse(g["1"].parent_id)
        self.assertFalse(g["4"].parent_id)
        self.assertEqual({prefix: self._level(group) for prefix, group in g.items()}, TB_H_LEVELS)
        accounts = {name: account.with_company(self.company) for name, account in self.accounts.items()}
        self.assertEqual(accounts["bank"].group_id, g["10140"])
        self.assertEqual(accounts["current_assets"].group_id, g["101"])
        self.assertEqual(accounts["revenue"].group_id, g["4"])
        self.assertEqual(accounts["cash_discount_loss"].group_id, g["4"])
        self.assertFalse(accounts["capital"].group_id)

    def test_hand_calculations_are_consistent(self):
        self.assertExpectationsConsistent(TB_H_ACCOUNTS)
        self.assertExpectationsConsistent(TB_H_GROUPS, net_rows=False)
        members = {
            "1": ["bank", "current_assets"], "10": ["bank", "current_assets"],
            "101": ["bank", "current_assets"], "1014": ["bank"], "10140": ["bank"],
            "4": ["revenue", "cash_discount_loss"], "(No Group)": ["capital"],
        }
        for group, names in members.items():
            with self.subTest(group=group):
                sums = tuple(sum(TB_H_ACCOUNTS[name][i] for name in names) for i in range(9))
                self.assertEqual(sums, TB_H_GROUPS[group])
        # Only Parents: each level keeps every amount exactly once. The
        # top-level rows (level 1 groups and "(No Group)") add up to the
        # total, whatever level is chosen.
        for level, shown in TB_H_ONLY_PARENTS.items():
            with self.subTest(level=level):
                self.assertEqual(
                    shown, [p for p in TB_H_GROUPS if p == "(No Group)" or TB_H_LEVELS[p] <= level])
        top = ("1", "4", "(No Group)")
        sums = tuple(sum(TB_H_GROUPS[p][i] for p in top) for i in range(9))
        self.assertEqual(sums, TB_H_ACCOUNTS["total"])

    def test_native_hierarchy_matches(self):
        native = self.native_trial_balance("2026-01-01", "2026-01-31", hierarchy=True)
        self.assertNativeMatches(native, TB_H_ACCOUNTS)
        groups = {f"group {p}" if p != "(No Group)" else p: row for p, row in TB_H_GROUPS.items()}
        self.assertNativeMatches(native, groups)
        depths = {f"group {p}": level for p, level in TB_H_LEVELS.items()}
        depths["(No Group)"] = 1
        self.assertEqual(native["_depth"], depths)
