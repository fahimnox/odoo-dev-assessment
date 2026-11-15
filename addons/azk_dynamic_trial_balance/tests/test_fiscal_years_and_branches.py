"""Fiscal years and branch companies (Stage 10, the coverage gaps of D-60).

The numbers below are hand-calculated from the entries, like the constants
of tests/common.py; then the standard Trial Balance is run on the same data,
and our engine must equal both.

TB-F: a fiscal year from 1 July to 30 June, set up in two ways on two fresh
companies with the same entries:
- "setting": the company's fiscal year ends on 30 June (Accounting >
  Settings, ``fiscalyear_last_day`` and ``fiscalyear_last_month``);
- "record": the company keeps the calendar year, and an ``account.fiscal.year``
  record (account_accountant, Accounting > Configuration > Fiscal Years)
  covers 2025-07-01 to 2026-06-30. For a date after it, Odoo starts the
  fiscal year the day after the record ends (and ends it with the calendar
  year), so both companies get the same fiscal-year starts here.
Entries:
  2025-03-10  Bank debit 80 / Revenue credit 80          FY 2024-25
  2025-06-30  Bank debit 1,000 / Capital credit 1,000    FY 2024-25, last day
  2025-08-15  Bank debit 600 / Revenue credit 600        FY 2025-26
  2026-06-30  Expense debit 250 / Bank credit 250        FY 2025-26, last day
  2026-07-01  Bank debit 400 / Revenue credit 400        FY 2026-27, first day
  2026-07-20  Expense debit 100 / Bank credit 100        FY 2026-27
  2026-08-05  Expense debit 30 / Bank credit 30          after every period below
Income and expense accounts open from the start of the fiscal year that
contains Date From; earlier years' results are shown on Current Year
Earnings (contract 5). With a calendar year instead, July 2026 would open
Expense at 250 and Earnings at 680 credit: these tables would fail.
"""
from datetime import date

from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import new_test_user, tagged

from .common import TrialBalanceCase

# July 2026: the first month of FY 2026-27 (fiscal-year start 2026-07-01).
# Earnings: 80 + 600 revenue - 250 expense of the earlier years = 430 credit.
TB_F_JULY = {
    "bank": (1430, 0, 1430, 400, 100, 300, 1730, 0, 1730),
    "capital": (0, 1000, -1000, 0, 0, 0, 0, 1000, -1000),
    "revenue": (0, 0, 0, 0, 400, -400, 0, 400, -400),
    "expense": (0, 0, 0, 100, 0, 100, 100, 0, 100),
    "earnings": (0, 430, -430, 0, 0, 0, 0, 430, -430),
    "total": (1430, 1430, 0, 500, 500, 0, 1830, 1830, 0),
}
# June 2026: the last month of FY 2025-26 (start 2025-07-01). Revenue opens
# with the 600 of August 2025; Earnings carries the 80 of FY 2024-25.
TB_F_JUNE = {
    "bank": (1680, 0, 1680, 0, 250, -250, 1430, 0, 1430),
    "capital": (0, 1000, -1000, 0, 0, 0, 0, 1000, -1000),
    "revenue": (0, 600, -600, 0, 0, 0, 0, 600, -600),
    "expense": (0, 0, 0, 250, 0, 250, 250, 0, 250),
    "earnings": (0, 80, -80, 0, 0, 0, 0, 80, -80),
    "total": (1680, 1680, 0, 250, 250, 0, 1680, 1680, 0),
}
# 2026-06-15 to 2026-07-15, across the boundary: the fiscal year of Date From
# (2025-07-01) gives the openings, as in the standard report, so the ending
# Revenue (1,000) mixes FY 2025-26 (600) and FY 2026-27 (400).
TB_F_ACROSS = {
    "bank": (1680, 0, 1680, 400, 250, 150, 1830, 0, 1830),
    "capital": (0, 1000, -1000, 0, 0, 0, 0, 1000, -1000),
    "revenue": (0, 600, -600, 0, 400, -400, 0, 1000, -1000),
    "expense": (0, 0, 0, 250, 0, 250, 250, 0, 250),
    "earnings": (0, 80, -80, 0, 0, 0, 0, 80, -80),
    "total": (1680, 1680, 0, 650, 650, 0, 2080, 2080, 0),
}
TB_F_PERIODS = {
    "july": ("2026-07-01", "2026-07-31", date(2026, 7, 1), TB_F_JULY),
    "june": ("2026-06-01", "2026-06-30", date(2025, 7, 1), TB_F_JUNE),
    "across": ("2026-06-15", "2026-07-15", date(2025, 7, 1), TB_F_ACROSS),
}

# ---------------------------------------------------------------------------
# TB-B: a root company and its branch (calendar year). Branches share the
# root's accounts and journals; the branch's entries carry the branch as
# their company. January 2026:
#   root    2026-01-10  Bank debit 300 / Capital credit 300
#   branch  2025-11-20  Bank debit 70 / Revenue credit 70       earlier year
#   branch  2026-01-12  Bank debit 900 / Capital credit 900
#   branch  2026-01-15  Expense debit 40 / Bank credit 40
# Our report covers exactly the selected company (D-16). The standard report
# adds up every company active in the switcher.
# ---------------------------------------------------------------------------
TB_B_ROOT = {
    "bank": (0, 0, 0, 300, 0, 300, 300, 0, 300),
    "capital": (0, 0, 0, 0, 300, -300, 0, 300, -300),
    "total": (0, 0, 0, 300, 300, 0, 300, 300, 0),
}
TB_B_BRANCH = {
    "bank": (70, 0, 70, 900, 40, 860, 930, 0, 930),
    "capital": (0, 0, 0, 0, 900, -900, 0, 900, -900),
    "expense": (0, 0, 0, 40, 0, 40, 40, 0, 40),
    "earnings": (0, 70, -70, 0, 0, 0, 0, 70, -70),
    "total": (70, 70, 0, 940, 940, 0, 970, 970, 0),
}
TB_B_ROOT_AND_BRANCH = {
    "bank": (70, 0, 70, 1200, 40, 1160, 1230, 0, 1230),
    "capital": (0, 0, 0, 0, 1200, -1200, 0, 1200, -1200),
    "expense": (0, 0, 0, 40, 0, 40, 40, 0, 40),
    "earnings": (0, 70, -70, 0, 0, 0, 0, 70, -70),
    "total": (70, 70, 0, 1240, 1240, 0, 1270, 1270, 0),
}


@tagged("post_install", "-at_install")
class TestFiscalYearFixture(TrialBalanceCase):
    """TB-F: a July-to-June fiscal year, from the company setting and from a fiscal-year record."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        egp = cls.company.currency_id
        cls.fiscal = {}
        for name in ("setting", "record"):
            data = cls.setup_other_company(name=f"AZK TB Fiscal Year ({name})", currency_id=egp.id)
            company = data["company"]
            if name == "setting":
                company.write({"fiscalyear_last_month": "6", "fiscalyear_last_day": 30})
            else:
                cls.env["account.fiscal.year"].create({
                    "name": "FY 2025-26", "company_id": company.id,
                    "date_from": "2025-07-01", "date_to": "2026-06-30",
                })
            accounts = cls._chart_accounts(company)
            journal = data["default_journal_misc"]
            a = accounts
            for day, lines in (
                ("2025-03-10", [(a["bank"], 80, 0), (a["revenue"], 0, 80)]),
                ("2025-06-30", [(a["bank"], 1000, 0), (a["capital"], 0, 1000)]),
                ("2025-08-15", [(a["bank"], 600, 0), (a["revenue"], 0, 600)]),
                ("2026-06-30", [(a["expense"], 250, 0), (a["bank"], 0, 250)]),
                ("2026-07-01", [(a["bank"], 400, 0), (a["revenue"], 0, 400)]),
                ("2026-07-20", [(a["expense"], 100, 0), (a["bank"], 0, 100)]),
                ("2026-08-05", [(a["expense"], 30, 0), (a["bank"], 0, 30)]),
            ):
                cls._entry(day, lines, journal=journal, company=company, ref=f"TB-F {name} {day}")
            cls.fiscal[name] = (company, accounts)

    def test_hand_calculations_are_consistent(self):
        for name, (_date_from, _date_to, _start, expected) in TB_F_PERIODS.items():
            with self.subTest(period=name):
                self.assertExpectationsConsistent(expected)

    def test_both_set_ups_start_the_year_on_1_july(self):
        expected = {
            ("setting", date(2026, 7, 1)): (date(2026, 7, 1), date(2027, 6, 30)),
            ("setting", date(2026, 6, 15)): (date(2025, 7, 1), date(2026, 6, 30)),
            # After the record, the year runs to the calendar setting's year end.
            ("record", date(2026, 7, 1)): (date(2026, 7, 1), date(2026, 12, 31)),
            ("record", date(2026, 6, 15)): (date(2025, 7, 1), date(2026, 6, 30)),
        }
        for (name, day), (start, end) in expected.items():
            with self.subTest(setup=name, day=day):
                dates = self.fiscal[name][0].compute_fiscalyear_dates(day)
                self.assertEqual((dates["date_from"], dates["date_to"]), (start, end))

    def test_engine_and_standard_report_across_the_boundary(self):
        for name, (company, accounts) in self.fiscal.items():
            for period, (date_from, date_to, start, expected) in TB_F_PERIODS.items():
                with self.subTest(setup=name, period=period):
                    result = self.engine_report(date_from, date_to, company=company, skip_zero_balance=True)
                    self.assertEqual(result["metadata"]["fiscal_year_start"], start.isoformat())
                    self.assertRowsEqual(self.engine_rows(result, accounts), expected)
                    native = self.native_trial_balance(date_from, date_to, company=company, accounts=accounts)
                    self.assertNativeMatches(native, expected)
                    self.assertEngineMatchesNative(result, native, accounts)


@tagged("post_install", "-at_install")
class TestBranchFixture(TrialBalanceCase):
    """TB-B: a branch shares its root's chart and journals; a report covers one company."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.root = cls.company
        cls.root.write({"child_ids": [Command.create({"name": "AZK TB Branch"})]})
        cls.cr.precommit.run()  # the branch's accounting set-up, as Odoo's own branch tests do
        cls.branch = cls.root.child_ids
        a = cls.accounts
        cls._entry("2026-01-10", [(a["bank"], 300, 0), (a["capital"], 0, 300)], ref="TB-B root")
        cls._entry("2025-11-20", [(a["bank"], 70, 0), (a["revenue"], 0, 70)], company=cls.branch,
                   ref="TB-B branch earlier year")
        cls._entry("2026-01-12", [(a["bank"], 900, 0), (a["capital"], 0, 900)], company=cls.branch,
                   ref="TB-B branch capital")
        cls._entry("2026-01-15", [(a["expense"], 40, 0), (a["bank"], 0, 40)], company=cls.branch,
                   ref="TB-B branch expense")
        groups = "base.group_user,account.group_account_readonly"
        cls.branch_reader = new_test_user(
            cls.env(su=True), login="tb_branch_reader", groups=groups,
            company_id=cls.branch.id, company_ids=[Command.set(cls.branch.ids)])
        cls.root_reader = new_test_user(
            cls.env(su=True), login="tb_root_reader", groups=groups,
            company_id=cls.root.id, company_ids=[Command.set(cls.root.ids)])

    def test_hand_calculations_are_consistent(self):
        for expected in (TB_B_ROOT, TB_B_BRANCH, TB_B_ROOT_AND_BRANCH):
            self.assertExpectationsConsistent(expected)

    def test_the_branch_shares_the_root_chart_and_journal(self):
        moves = self.env["account.move"].search([("ref", "like", "TB-B branch")])
        self.assertEqual(len(moves), 3)
        self.assertEqual(moves.company_id, self.branch)
        self.assertEqual(moves.journal_id, self.misc_journal)
        self.assertEqual(self.misc_journal.company_id, self.root)
        Account = self.env["account.account"]
        self.assertEqual(Account.search(Account._check_company_domain(self.branch)),
                         Account.search(Account._check_company_domain(self.root)))

    def test_each_report_covers_exactly_its_company(self):
        for company, expected in ((self.root, TB_B_ROOT), (self.branch, TB_B_BRANCH)):
            with self.subTest(company=company.name):
                result = self.engine_report("2026-01-01", "2026-01-31", company=company, skip_zero_balance=True)
                self.assertRowsEqual(self.engine_rows(result), expected)
                native = self.native_trial_balance("2026-01-01", "2026-01-31", company=company)
                self.assertNativeMatches(native, expected)
                self.assertEngineMatchesNative(result, native)

    def test_the_standard_report_adds_up_active_branches_ours_does_not(self):
        both = self.root | self.branch
        native = self.native_trial_balance("2026-01-01", "2026-01-31", company=self.root, active_companies=both)
        self.assertNativeMatches(native, TB_B_ROOT_AND_BRANCH)
        # Our report, with the same two companies active: the root only (D-16).
        result = self.env["azk_dynamic_trial_balance.engine"].with_context(
            allowed_company_ids=both.ids).compute({
                "date_from": "2026-01-01", "date_to": "2026-01-31", "company_id": self.root.id,
                "skip_zero_balance": True})
        self.assertRowsEqual(self.engine_rows(result), TB_B_ROOT)

    def test_a_branch_user_sees_the_branch_only(self):
        # Regression (Stage 10): Odoo 18 lets a user access a branch without
        # its root company. That user's searches on accounts cannot see the
        # root's shared chart, so the report lost the Current Year Earnings
        # row (with a wrong "no earnings account" warning), the accounts
        # without items and every prefix match. The amounts were right.
        def report(user, **options):
            return self.engine_report("2026-01-01", "2026-01-31", company=self.branch, user=user, **options)

        result = report(self.branch_reader, skip_zero_balance=True)
        self.assertRowsEqual(self.engine_rows(result), TB_B_BRANCH)
        self.assertEqual(result["warnings"], [])
        # The same rows as for a user who also has the root company.
        full = report(self.branch_reader)
        self.assertEqual(full["leaf_rows"], report(self.env.user)["leaf_rows"])
        self.assertGreater(len(full["leaf_rows"]), len(TB_B_BRANCH))
        prefixed = report(self.branch_reader, account_prefixes=["1014"])
        self.assertIn(("101401", 930.0), [(row["account_code"], row["ending_balance"]) for row in prefixed["leaf_rows"]])
        # The shared root journal is a valid filter for the branch.
        result = report(self.branch_reader, skip_zero_balance=True, journal_id=self.misc_journal.id)
        self.assertRowsEqual(self.engine_rows(result), TB_B_BRANCH)
        # The standard Trial Balance of this build shows that user no line at all.
        native = self.native_trial_balance("2026-01-01", "2026-01-31", company=self.branch, user=self.branch_reader)
        self.assertEqual(native, {"total": (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)})
        for user, company in ((self.branch_reader, self.root), (self.root_reader, self.branch)):
            with self.subTest(user=user.login), self.assertRaises(AccessError):
                self.engine_report("2026-01-01", "2026-01-31", company=company, user=user)

    def test_a_branch_ignores_the_root_custom_fiscal_year(self):
        # Odoo keeps fiscal-year records on root companies only and looks them
        # up by the exact company, so a branch falls back to the root's
        # month and day setting. The standard report does the same.
        self.env["account.fiscal.year"].create({
            "name": "Root FY 2025-26", "company_id": self.root.id,
            "date_from": "2025-07-01", "date_to": "2026-06-30",
        })
        self.assertEqual(self.root.compute_fiscalyear_dates(date(2026, 1, 1))["date_from"], date(2025, 7, 1))
        self.assertEqual(self.branch.compute_fiscalyear_dates(date(2026, 1, 1))["date_from"], date(2026, 1, 1))
        result = self.engine_report("2026-01-01", "2026-01-31", company=self.branch, skip_zero_balance=True)
        self.assertEqual(result["metadata"]["fiscal_year_start"], "2026-01-01")
        self.assertRowsEqual(self.engine_rows(result), TB_B_BRANCH)
        self.assertEngineMatchesNative(result, self.native_trial_balance("2026-01-01", "2026-01-31",
                                                                         company=self.branch))
        root = self.engine_report("2026-01-01", "2026-01-31", company=self.root, skip_zero_balance=True)
        self.assertEqual(root["metadata"]["fiscal_year_start"], "2025-07-01")
