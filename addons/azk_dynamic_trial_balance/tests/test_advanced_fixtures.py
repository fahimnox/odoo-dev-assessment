"""Advanced fixtures, kept apart from TB-BASE so its numbers stay simple.

Each class builds one fixture in its own fresh company from real, balanced
entries and checks that the data is what the hand calculation assumes.
Stage 07 compared the standard Trial Balance with the hand-calculated
constants of tests/common.py wherever it has the same option. Stage 08 adds
our engine: it must give the same constants, including for the options only
our report has (currency rows, Skip Zero Balance, Hierarchy Only Parents),
and the same numbers as the standard report where both apply.
"""
from datetime import date

from odoo import Command
from odoo.exceptions import AccessError, ValidationError
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

    def test_engine_skip_zero_balance_keeps_zero_net_activity(self):
        # Skip Zero Balance hides Prepaid Expenses (nothing happened) but
        # keeps Current Assets: 250 in and 250 out is activity (D-48).
        result = self.engine_report("2026-01-01", "2026-01-31", skip_zero_balance=True)
        self.assertRowsEqual(self.engine_rows(result), TB_Z_JANUARY)
        self.assertEngineMatchesNative(result, self.native_trial_balance("2026-01-01", "2026-01-31"))

    def test_engine_without_skip_zero_balance_lists_untouched_accounts(self):
        rows = self.engine_rows(self.engine_report("2026-01-01", "2026-01-31"))
        self.assertEqual(rows["prepaid"], TB_Z_UNTOUCHED)
        for key, values in TB_Z_JANUARY.items():
            with self.subTest(row=key):
                self.assertEqual(rows[key], values)


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

    def test_engine_rows_per_transaction_currency(self):
        result = self.engine_report("2026-01-01", "2026-01-31", show_amount_currency=True,
                                    skip_zero_balance=True)
        self.assertRowsEqual(self.engine_rows(result), TB_C_JANUARY_BY_CURRENCY)
        names = {account.id: name for name, account in self.accounts.items()}
        amounts = {(names[row["account_id"]], row["currency_name"]): row["amount_currency"]
                   for row in result["leaf_rows"]}
        self.assertEqual(amounts, TB_C_JANUARY_AMOUNT_CURRENCY)
        # One total per currency: USD 100 - 40 = 60 and EUR 70 - 20 = 50,
        # never added together into 110.
        totals = {total["currency_name"]: total["amount_currency"] for total in result["currency_totals"]}
        self.assertEqual(totals, {"USD": 60.0, "EUR": 50.0, "EGP": -5750.0})
        self.assertEqual({row["currency_symbol"] for row in result["leaf_rows"]},
                         {self.usd.symbol, self.eur.symbol, self.company.currency_id.symbol})

    def test_engine_currency_rows_reconcile_with_account_rows(self):
        flat = self.engine_report("2026-01-01", "2026-01-31", skip_zero_balance=True)
        self.assertRowsEqual(self.engine_rows(flat), TB_C_JANUARY)
        self.assertEqual(flat["currency_totals"], [])
        self.assertEngineMatchesNative(flat, self.native_trial_balance("2026-01-01", "2026-01-31"))
        split = self.engine_rows(self.engine_report(
            "2026-01-01", "2026-01-31", show_amount_currency=True, skip_zero_balance=True))
        flat_rows = self.engine_rows(flat)
        # Opening, movement debit and credit, movement balance and ending
        # balance add up across the currency rows of an account.
        for index in (2, 3, 4, 5, 8):
            self.assertEqual(split[("current_assets", "USD")][index] + split[("current_assets", "EUR")][index],
                             flat_rows["current_assets"][index])
            self.assertEqual(split["total"][index], flat_rows["total"][index])
        # Netted opening totals differ with the grain of netting (D-49).
        self.assertEqual((split["total"][0], flat_rows["total"][0]), (1650.0, 650.0))

    def test_engine_does_not_revalue_at_a_later_rate(self):
        # A new USD rate dated inside the period changes nothing: company
        # amounts are used as booked.
        before = self.engine_rows(self.engine_report(
            "2026-01-01", "2026-01-31", show_amount_currency=True, skip_zero_balance=True))
        self.env["res.currency.rate"].sudo().create({
            "name": "2026-01-02", "currency_id": self.usd.id, "company_id": self.company.id,
            "rate": 1 / 60,
        })
        after = self.engine_rows(self.engine_report(
            "2026-01-01", "2026-01-31", show_amount_currency=True, skip_zero_balance=True))
        self.assertEqual(after, before)


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

    def test_engine_selects_whole_items(self):
        for name, table in TB_A_MARCH.items():
            with self.subTest(filter=name):
                analytic = self.analytic.get(name)
                result = self.engine_report("2026-03-01", "2026-03-31",
                                            analytic_account_id=analytic.id if analytic else None,
                                            skip_zero_balance=True)
                self.assertRowsEqual(self.engine_rows(result), table)
                native = self.native_trial_balance("2026-03-01", "2026-03-31", analytic=analytic)
                self.assertEngineMatchesNative(result, native)
        # The 60/40 item counts in full for A1: 1,000 + the composite key's
        # 200 = 1,200. Proportional allocation (rejected, documented) would
        # give 600 + 200 = 800.
        a1 = self.engine_report("2026-03-01", "2026-03-31",
                                analytic_account_id=self.analytic["A1"].id, skip_zero_balance=True)
        expense = self.engine_rows(a1)["expense"]
        self.assertEqual(expense[3], 1200.0)
        self.assertNotEqual(expense[3], TB_A_PROPORTIONAL_EXPENSE["A1"])
        # Bank items have no distribution, so a filtered report need not balance.
        self.assertFalse(a1["metadata"]["balanced"])

    def test_engine_counts_each_item_once_without_a_filter(self):
        # Two distribution keys on one item, and a key spanning two plans,
        # never multiply the item: 1,000 + 200, not 1,400 or 2,400.
        result = self.engine_report("2026-03-01", "2026-03-31", skip_zero_balance=True)
        rows = self.engine_rows(result)
        self.assertEqual(rows["expense"][3], 1200.0)
        self.assertEqual(rows["bank"][4], 1200.0)
        self.assertTrue(result["metadata"]["balanced"])


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
        cls.misc_journal_2 = data_2["default_journal_misc"]
        cls._entry("2026-01-12", [(a2["bank"], 900, 0), (a2["capital"], 0, 900)],
                   journal=cls.misc_journal_2, company=cls.company_2, ref="TB-M company 2")
        cls.reader_1 = new_test_user(
            cls.env(su=True), login="tb_reader_company_1",
            groups="base.group_user,account.group_account_readonly",
            company_id=cls.company.id, company_ids=[Command.set(cls.company.ids)])
        cls.reader_both = new_test_user(
            cls.env(su=True), login="tb_reader_both_companies",
            groups="base.group_user,account.group_account_readonly",
            company_id=cls.company.id,
            company_ids=[Command.set((cls.company + cls.company_2).ids)])

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

    def test_engine_reports_exactly_one_company(self):
        one = self.engine_report("2026-01-01", "2026-01-31", skip_zero_balance=True)
        self.assertRowsEqual(self.engine_rows(one), TB_M_COMPANY_1)
        self.assertEngineMatchesNative(one, self.native_trial_balance("2026-01-01", "2026-01-31"))
        two = self.engine_report("2026-01-01", "2026-01-31", company=self.company_2,
                                 skip_zero_balance=True)
        self.assertRowsEqual(self.engine_rows(two, self.accounts_2), TB_M_COMPANY_2)
        native_2 = self.native_trial_balance("2026-01-01", "2026-01-31", company=self.company_2,
                                             accounts=self.accounts_2)
        self.assertEngineMatchesNative(two, native_2, self.accounts_2)
        self.assertEqual(two["filters"]["company_name"], "AZK TB Second Company")

    def test_engine_refuses_a_company_the_user_may_not_use(self):
        # Not one of the user's companies: refused before any query.
        with self.assertRaises(AccessError):
            self.engine_report("2026-01-01", "2026-01-31", company=self.company_2, user=self.reader_1)
        # One of the user's companies, but not active in the switcher.
        Engine = self.env["azk_dynamic_trial_balance.engine"].with_user(self.reader_both)
        with self.assertRaises(ValidationError):
            Engine.with_context(allowed_company_ids=self.company.ids).compute({
                "date_from": "2026-01-01", "date_to": "2026-01-31", "company_id": self.company_2.id})
        # Active: allowed.
        result = Engine.with_context(allowed_company_ids=self.company_2.ids).compute({
            "date_from": "2026-01-01", "date_to": "2026-01-31", "company_id": self.company_2.id,
            "skip_zero_balance": True})
        self.assertRowsEqual(self.engine_rows(result, self.accounts_2), TB_M_COMPANY_2)

    def test_engine_prefixes_never_reach_another_company(self):
        account_2 = self.env["account.account"].with_company(self.company_2).create(
            {"name": "TB company 2 only", "code": "TBM900", "account_type": "asset_current"})
        self._entry("2026-01-20", [(account_2, 50, 0), (self.accounts_2["bank"], 0, 50)],
                    journal=self.misc_journal_2, company=self.company_2, ref="TB-M prefix")
        result = self.engine_report("2026-01-01", "2026-01-31", user=self.reader_1,
                                    account_prefixes=["TBM"])
        self.assertEqual(result["leaf_rows"], [])


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

    def test_engine_applies_record_rules(self):
        # The same request gives each user only the journal items they may read.
        restricted = self.engine_report("2026-01-01", "2026-01-31", user=self.reader,
                                        skip_zero_balance=True)
        self.assertRowsEqual(self.engine_rows(restricted), TB_R_VISIBLE)
        self.assertEngineMatchesNative(
            restricted, self.native_trial_balance("2026-01-01", "2026-01-31", user=self.reader))
        everything = self.engine_report("2026-01-01", "2026-01-31", skip_zero_balance=True)
        self.assertRowsEqual(self.engine_rows(everything), TB_R_EVERYTHING)
        self.assertEngineMatchesNative(everything, self.native_trial_balance("2026-01-01", "2026-01-31"))

    def test_engine_restricted_items_stay_hidden_when_targeted(self):
        # The reader may see the journal itself, so selecting it is allowed;
        # its items stay invisible to them.
        result = self.engine_report("2026-01-01", "2026-01-31", user=self.reader,
                                    journal_id=self.restricted_journal.id, skip_zero_balance=True)
        self.assertEqual(result["leaf_rows"], [])
        self.assertEqual(set(result["totals"].values()), {0.0})


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

    # ------------------------------------------------------------------
    # Our engine (Stage 08)
    # ------------------------------------------------------------------
    def _line_keys(self, result):
        names = {account.id: name for name, account in self.accounts.items()}
        return [(names[row["account_id"]] if row["type"] == "account" else row["group_code"] or "(No Group)",
                 row["level"]) for row in result["lines"]]

    def test_engine_hierarchy_and_subtotals(self):
        result = self.engine_report("2026-01-01", "2026-01-31", hierarchy_subtotals=True,
                                    skip_zero_balance=True)
        self.assertRowsEqual(self.engine_rows(result, lines=True), {**TB_H_ACCOUNTS, **TB_H_GROUPS})
        # Code order, each group before its content; "(No Group)" last.
        # Levels: groups by depth, accounts one below their group.
        self.assertEqual(self._line_keys(result), [
            ("1", 1), ("10", 2), ("101", 3), ("current_assets", 4), ("1014", 4), ("10140", 5),
            ("bank", 6), ("4", 1), ("revenue", 2), ("cash_discount_loss", 2),
            ("(No Group)", 1), ("capital", 2),
        ])
        # The total adds account rows only: 1,500 / 1,500, not the group rows too.
        self.assertEqual(result["totals"]["ending_debit"], 1500.0)
        # Same group rows, depths and account rows as the standard hierarchy.
        native = self.native_trial_balance("2026-01-01", "2026-01-31", hierarchy=True)
        self.assertEngineMatchesNative(result, native)
        for row in result["hierarchy_rows"]:
            key = f"group {row['group_code']}" if row["group_code"] else "(No Group)"
            with self.subTest(group=key):
                self.assertEqual(tuple(row[name] for name in ("initial_debit", "initial_credit", "debit",
                                                              "credit", "ending_debit", "ending_credit")),
                                 native[key])
                self.assertEqual(row["level"], native["_depth"][key])

    def test_engine_only_parents_at_each_level(self):
        for level, shown in TB_H_ONLY_PARENTS.items():
            with self.subTest(level=level):
                result = self.engine_report(
                    "2026-01-01", "2026-01-31", hierarchy_subtotals=True, hierarchy_only_parents=True,
                    account_level=level, skip_zero_balance=True)
                self.assertEqual([key for key, _level in self._line_keys(result)], shown)
                rows = self.engine_rows(result, lines=True)
                self.assertRowsEqual(rows, {**{key: TB_H_GROUPS[key] for key in shown},
                                            "total": TB_H_ACCOUNTS["total"]})
                # Deeper groups and every account are still in the amounts.
                self.assertEqual(len(result["leaf_rows"]), 5)

    def test_engine_hierarchy_options_never_change_totals(self):
        variants = [
            {}, {"hierarchy_subtotals": True},
            {"hierarchy_subtotals": True, "hierarchy_only_parents": True, "account_level": 1},
        ]
        for values in variants:
            for skip in (True, False):
                with self.subTest(options=values, skip_zero=skip):
                    result = self.engine_report("2026-01-01", "2026-01-31", skip_zero_balance=skip,
                                                **values)
                    self.assertEqual(tuple(result["totals"][name] for name in (
                        "initial_debit", "initial_credit", "debit", "credit", "ending_debit",
                        "ending_credit")), (1000.0, 1000.0, 1020.0, 1020.0, 1500.0, 1500.0))
        # Without Skip Zero Balance the ungrouped accounts without amounts
        # join "(No Group)", which keeps Capital's numbers.
        result = self.engine_report("2026-01-01", "2026-01-31", hierarchy_subtotals=True)
        no_group = next(row for row in result["hierarchy_rows"] if row["group_id"] is None)
        self.assertEqual(tuple(no_group[name] for name in ("initial_credit", "ending_credit")),
                         (1000.0, 1000.0))
        members = [row for row in result["leaf_rows"] if row["parent_id"] == no_group["id"]]
        self.assertGreater(len(members), 1)
        self.assertIn(self.accounts["capital"].id, [row["account_id"] for row in members])
