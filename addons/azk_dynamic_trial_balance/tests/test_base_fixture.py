from datetime import date

from odoo.addons.azk_dynamic_trial_balance.models.trial_balance_engine import like_prefix_pattern
from odoo.tests import tagged

from .common import (
    TB_BASE_BANK_JOURNAL,
    TB_BASE_MISC_JOURNAL,
    TB_BASE_POSTED,
    TB_BASE_WITH_DRAFTS,
    TrialBalanceCase,
)

ZERO_ROW = (0,) * 9


@tagged("post_install", "-at_install")
class TestBaseFixture(TrialBalanceCase):
    """TB-BASE, the Stage 07 base fixture: the standard Trial Balance and our engine.

    The expected numbers are hand-calculated constants (tests/common.py).
    Stage 07 compared them with the standard Enterprise Trial Balance run
    with the same company, dates and posting option; Stage 08 compares our
    engine with the same constants, and with the standard report.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._build_tb_base()

    def test_fixture_is_built_from_real_balanced_entries(self):
        moves = self.base_moves
        expected = {
            "opening": ("posted", date(2025, 12, 31), self.misc_journal, 1000),
            "expense": ("posted", date(2026, 1, 10), self.misc_journal, 300),
            "revenue": ("posted", date(2026, 1, 20), self.bank_journal, 500),
            "draft": ("draft", date(2026, 1, 25), self.misc_journal, 200),
            "cancelled": ("cancel", date(2026, 1, 26), self.misc_journal, 400),
            "february": ("posted", date(2026, 2, 1), self.misc_journal, 50),
        }
        for name, (state, move_date, journal, amount) in expected.items():
            with self.subTest(move=name):
                move = moves[name]
                self.assertEqual(move.state, state)
                self.assertEqual(move.date, move_date)
                self.assertEqual(move.journal_id, journal)
                self.assertEqual(move.company_id, self.company)
                self.assertEqual(len(move.line_ids), 2)
                self.assertEqual(sum(move.line_ids.mapped("debit")), amount)
                self.assertEqual(sum(move.line_ids.mapped("credit")), amount)
                self.assertEqual(set(move.line_ids.mapped("parent_state")), {state})
        # The cancelled entry went through the supported transitions: it was
        # posted (so it has a sequence number), then cancelled.
        self.assertNotEqual(moves["cancelled"].name, "/")
        self.assertEqual(self.company.currency_id.name, "EGP")

    def test_company_uses_a_calendar_fiscal_year(self):
        dates = self.company.compute_fiscalyear_dates(date(2026, 1, 15))
        self.assertEqual((dates["date_from"], dates["date_to"]),
                         (date(2026, 1, 1), date(2026, 12, 31)))

    def test_hand_calculations_are_consistent(self):
        for name, table in {
            "posted": TB_BASE_POSTED,
            "with drafts": TB_BASE_WITH_DRAFTS,
            "bank journal": TB_BASE_BANK_JOURNAL,
            "misc journal": TB_BASE_MISC_JOURNAL,
        }.items():
            with self.subTest(table=name):
                self.assertExpectationsConsistent(table)
        # Bank, by hand: 1,000 + 500 - 300 = 1,200 posted; the draft credit
        # of 200 lowers it to 1,000. Debit and credit totals stay equal.
        self.assertEqual(TB_BASE_POSTED["bank"][8], 1000 + 500 - 300)
        self.assertEqual(TB_BASE_WITH_DRAFTS["bank"][8], 1000 + 500 - 300 - 200)
        for table in (TB_BASE_POSTED, TB_BASE_WITH_DRAFTS):
            self.assertEqual(table["total"][6], table["total"][7])
            self.assertEqual(table["total"][6], 1500)

    def test_native_trial_balance_posted_only(self):
        native = self.native_trial_balance("2026-01-01", "2026-01-31")
        self.assertSameLines(native, TB_BASE_POSTED)
        self.assertNativeMatches(native, TB_BASE_POSTED)

    def test_native_trial_balance_with_drafts(self):
        native = self.native_trial_balance("2026-01-01", "2026-01-31", draft=True)
        self.assertSameLines(native, TB_BASE_WITH_DRAFTS)
        self.assertNativeMatches(native, TB_BASE_WITH_DRAFTS)
        # The cancelled 400 and the February 50 never count: Expense moved
        # 300 posted + 200 draft, not 950.
        self.assertEqual(native["expense"][2], 500)

    def test_native_journal_filter_also_restricts_the_opening(self):
        bank = self.native_trial_balance("2026-01-01", "2026-01-31", journal=self.bank_journal)
        self.assertSameLines(bank, TB_BASE_BANK_JOURNAL)
        self.assertNativeMatches(bank, TB_BASE_BANK_JOURNAL)
        misc = self.native_trial_balance("2026-01-01", "2026-01-31", journal=self.misc_journal)
        self.assertSameLines(misc, TB_BASE_MISC_JOURNAL)
        self.assertNativeMatches(misc, TB_BASE_MISC_JOURNAL)

    # ------------------------------------------------------------------
    # Our engine (Stage 08)
    # ------------------------------------------------------------------
    def _bank_row(self, result):
        return next(row for row in result["leaf_rows"] if row["account_id"] == self.accounts["bank"].id)

    def test_engine_posted_only(self):
        result = self.engine_report("2026-01-01", "2026-01-31", skip_zero_balance=True)
        self.assertRowsEqual(self.engine_rows(result), TB_BASE_POSTED)
        bank = self._bank_row(result)
        # By hand: opening 1,000; debit 500; credit 300; ending 1,000 + 500 - 300.
        self.assertEqual(
            (bank["initial_balance"], bank["debit"], bank["credit"], bank["ending_balance"]),
            (1000.0, 500.0, 300.0, 1200.0))
        self.assertTrue(result["metadata"]["balanced"])
        self.assertEqual(result["warnings"], [])
        self.assertEqual(result["metadata"]["fiscal_year_start"], "2026-01-01")
        self.assertEqual(result["lines"], result["leaf_rows"])
        self.assertFalse(result["hierarchy_rows"] or result["currency_totals"])

    def test_engine_with_drafts(self):
        result = self.engine_report("2026-01-01", "2026-01-31", include_unposted=True,
                                    skip_zero_balance=True)
        self.assertRowsEqual(self.engine_rows(result), TB_BASE_WITH_DRAFTS)
        bank = self._bank_row(result)
        # The draft credit of 200 joins the movement: 1,000 + 500 - 500.
        self.assertEqual((bank["credit"], bank["ending_balance"]), (500.0, 1000.0))
        # The cancelled 400 and the February 50 never count.
        expense = next(row for row in result["leaf_rows"]
                       if row["account_id"] == self.accounts["expense"].id)
        self.assertEqual(expense["debit"], 500.0)

    def test_engine_journal_filter_also_restricts_the_opening(self):
        for journal, expected in ((self.bank_journal, TB_BASE_BANK_JOURNAL),
                                  (self.misc_journal, TB_BASE_MISC_JOURNAL)):
            with self.subTest(journal=journal.code):
                result = self.engine_report("2026-01-01", "2026-01-31", journal_id=journal.id,
                                            skip_zero_balance=True)
                self.assertRowsEqual(self.engine_rows(result), expected)
                self.assertEqual(result["filters"]["journal_name"], journal.display_name)

    def test_engine_matches_the_standard_report(self):
        # Matched options: same company (the only active one), January,
        # Draft Entries off and on, all journals or one, no hierarchy.
        cases = [(False, None), (True, None), (False, self.bank_journal), (False, self.misc_journal)]
        for draft, journal in cases:
            with self.subTest(drafts=draft, journal=journal and journal.code):
                native = self.native_trial_balance("2026-01-01", "2026-01-31", draft=draft,
                                                   journal=journal)
                ours = self.engine_report("2026-01-01", "2026-01-31", include_unposted=draft,
                                          journal_id=journal.id if journal else None,
                                          skip_zero_balance=True)
                self.assertEngineMatchesNative(ours, native)

    def test_engine_prefixes(self):
        def rows(prefixes):
            return self.engine_rows(self.engine_report(
                "2026-01-01", "2026-01-31", account_prefixes=prefixes, skip_zero_balance=True))

        # One prefix: only Bank. A filtered report need not balance.
        bank = TB_BASE_POSTED["bank"]
        self.assertRowsEqual(rows(["1"]), {"bank": bank, "total": bank})
        self.assertRowsEqual(rows(["10140"]), {"bank": bank, "total": bank})
        # Several prefixes are combined with OR; overlapping prefixes still
        # count each account once.
        self.assertRowsEqual(rows(["4", "6", "60", "600000"]), {
            "revenue": TB_BASE_POSTED["revenue"],
            "expense": TB_BASE_POSTED["expense"],
            "total": (0, 0, 0, 300, 500, -200, 300, 500, -200),
        })
        # A prefix that matches only accounts without amounts gives no row.
        self.assertRowsEqual(rows(["1015"]), {"total": ZERO_ROW})
        result = self.engine_report("2026-01-01", "2026-01-31", account_prefixes=["1"],
                                    skip_zero_balance=True)
        self.assertFalse(result["metadata"]["balanced"])

    def test_engine_prefixes_are_literal_and_case_sensitive(self):
        self.assertEqual(like_prefix_pattern("10"), "10%")
        self.assertEqual(like_prefix_pattern("1_%\\"), "1\\_\\%\\\\%")
        account = self.env["account.account"].create(
            {"name": "TB letters", "code": "TBX100", "account_type": "asset_current"})
        self._entry("2026-01-15", [(account, 10, 0), (self.accounts["bank"], 0, 10)], ref="TB letters")
        row = (0, 0, 0, 10, 0, 10, 10, 0, 10)
        upper = self.engine_report("2026-01-01", "2026-01-31", account_prefixes=["TBX"],
                                   skip_zero_balance=True)
        self.assertRowsEqual(self.engine_rows(upper), {"TBX100": row, "total": row})
        lower = self.engine_report("2026-01-01", "2026-01-31", account_prefixes=["tbx"],
                                   skip_zero_balance=True)
        self.assertRowsEqual(self.engine_rows(lower), {"total": ZERO_ROW})

    def test_engine_lists_every_account_without_skip_zero_balance(self):
        Account = self.env["account.account"].with_company(self.company)
        used = Account.create({"name": "TB deprecated, used", "code": "TBDEP1",
                               "account_type": "asset_current"})
        unused = Account.create({"name": "TB deprecated, unused", "code": "TBDEP2",
                                 "account_type": "asset_current"})
        self._entry("2026-01-15", [(used, 10, 0), (self.accounts["bank"], 0, 10)], ref="TB deprecated")
        (used | unused).deprecated = True
        result = self.engine_report("2026-01-01", "2026-01-31")
        listed = {row["account_id"] for row in result["leaf_rows"]}
        active = Account.search([*Account._check_company_domain(self.company), ("deprecated", "=", False)])
        # Every non-deprecated account, plus the deprecated one with amounts.
        self.assertEqual(listed, set(active.ids) | {used.id})
        rows = self.engine_rows(result)
        for key, values in rows.items():
            if key in ("total", "bank", "TBDEP1"):
                continue
            with self.subTest(row=key):
                self.assertEqual(values, TB_BASE_POSTED.get(key, ZERO_ROW))
        self.assertEqual(rows["TBDEP1"], (0, 0, 0, 10, 0, 10, 10, 0, 10))
