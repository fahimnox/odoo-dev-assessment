from odoo.tests import tagged

from .common import TB_D_JANUARY, TB_D_JANUARY_WITH_DRAFTS, TrialBalanceCase

# Single-day periods of TB-D, by hand (Debit / Credit / Balance for
# Initial, Movement and End).
#
# 2026-01-01 only. Opening: everything before 1 January, so Bank 100 and
# Capital 100 credit; income and expense open at zero on the first day of
# the fiscal year. Movement: the first-day entry, Bank debit 10 / Revenue
# credit 10.
TB_D_FIRST_DAY = {
    "bank": (100, 0, 100, 10, 0, 10, 110, 0, 110),
    "capital": (0, 100, -100, 0, 0, 0, 0, 100, -100),
    "revenue": (0, 0, 0, 0, 10, -10, 0, 10, -10),
    "total": (100, 100, 0, 10, 10, 0, 110, 110, 0),
}
# 2026-01-31 only. Opening: 1 to 30 January is now in the opening, also for
# income and expense (fiscal year from 1 January). Bank 100 + 10 + 30 - 30 -
# 200 = -90; Revenue 10 credit; Expense 30 - 30 + 200 = 200. The cancelled
# and draft entries do not count. Movement: the last-day entry, Expense
# debit 20 / Bank credit 20.
TB_D_LAST_DAY = {
    "bank": (0, 90, -90, 0, 20, -20, 0, 110, -110),
    "capital": (0, 100, -100, 0, 0, 0, 0, 100, -100),
    "revenue": (0, 10, -10, 0, 0, 0, 0, 10, -10),
    "expense": (200, 0, 200, 20, 0, 20, 220, 0, 220),
    "total": (200, 200, 0, 20, 20, 0, 220, 220, 0),
}


@tagged("post_install", "-at_install")
class TestEngineBoundaries(TrialBalanceCase):
    """TB-D: inclusive dates, cancelled, draft and later entries, a reversal,
    a negative balance and an empty period (Stage 08)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._build_tb_d()

    def test_reversal_is_a_posted_mirror_entry(self):
        self.assertEqual(self.reversal.state, "posted")
        self.assertEqual(self.reversal.reversed_entry_id.ref, "TB-D reversed")
        lines = {line.account_id: (line.debit, line.credit) for line in self.reversal.line_ids}
        self.assertEqual(lines, {self.accounts["bank"]: (30.0, 0.0), self.accounts["expense"]: (0.0, 30.0)})

    def test_hand_calculations_are_consistent(self):
        for name, table in {"January": TB_D_JANUARY, "January with drafts": TB_D_JANUARY_WITH_DRAFTS,
                            "first day": TB_D_FIRST_DAY, "last day": TB_D_LAST_DAY}.items():
            with self.subTest(table=name):
                self.assertExpectationsConsistent(table)

    def test_both_dates_count_and_neighbours_do_not(self):
        result = self.engine_report("2026-01-01", "2026-01-31", skip_zero_balance=True)
        self.assertRowsEqual(self.engine_rows(result), TB_D_JANUARY)
        # The overdrawn Bank ends on the credit side: 110 credit, balance -110.
        bank = self.engine_rows(result)["bank"]
        self.assertEqual(bank[6:], (0.0, 110.0, -110.0))
        self.assertTrue(result["metadata"]["balanced"])

    def test_drafts_join_but_cancelled_never_does(self):
        result = self.engine_report("2026-01-01", "2026-01-31", include_unposted=True,
                                    skip_zero_balance=True)
        self.assertRowsEqual(self.engine_rows(result), TB_D_JANUARY_WITH_DRAFTS)

    def test_single_day_periods(self):
        for day, expected in (("2026-01-01", TB_D_FIRST_DAY), ("2026-01-31", TB_D_LAST_DAY)):
            with self.subTest(day=day):
                result = self.engine_report(day, day, skip_zero_balance=True)
                self.assertRowsEqual(self.engine_rows(result), expected)

    def test_empty_period(self):
        # Nothing before or during January 2024: a valid, empty report.
        result = self.engine_report("2024-01-01", "2024-01-31", skip_zero_balance=True)
        self.assertEqual((result["lines"], result["leaf_rows"], result["warnings"]), ([], [], []))
        self.assertEqual(set(result["totals"].values()), {0.0})
        self.assertTrue(result["metadata"]["balanced"])
        # Without Skip Zero Balance, every account is listed with zeros.
        result = self.engine_report("2024-01-01", "2024-01-31")
        self.assertTrue(result["leaf_rows"])
        self.assertEqual({row[name] for row in result["leaf_rows"]
                          for name in ("initial_balance", "debit", "credit", "ending_balance")}, {0.0})

    def test_amounts_are_rounded_to_the_company_currency(self):
        # 0.10 + 0.20 is 0.30000000000000004 in binary floating point. Totals
        # and balances are rounded to the currency, so the report shows 0.30,
        # and an account whose cents cancel out ends at exactly zero.
        a = self.accounts
        self._entry("2026-01-05", [(a["prepaid"], 0.10, 0), (a["bank"], 0, 0.10)], ref="TB-D cents 1")
        self._entry("2026-01-06", [(a["current_assets"], 0.20, 0), (a["bank"], 0, 0.20)], ref="TB-D cents 2")
        self._entry("2026-01-07", [(a["bank"], 0.30, 0), (a["prepaid"], 0, 0.10),
                                   (a["current_assets"], 0, 0.20)], ref="TB-D cents back")
        result = self.engine_report("2026-01-01", "2026-01-31", skip_zero_balance=True)
        rows = self.engine_rows(result)
        self.assertEqual(rows["prepaid"], (0, 0, 0, 0.10, 0.10, 0, 0, 0, 0))
        self.assertEqual(rows["current_assets"], (0, 0, 0, 0.20, 0.20, 0, 0, 0, 0))
        totals = result["totals"]
        self.assertEqual((totals["debit"], totals["credit"]), (290.6, 290.6))
        self.assertEqual(totals["balance"], 0.0)

    def test_engine_matches_the_standard_report(self):
        # Matched options: same company, the periods below, Draft Entries
        # off and on, all journals, no hierarchy.
        cases = [("2026-01-01", "2026-01-31", False), ("2026-01-01", "2026-01-31", True),
                 ("2026-01-01", "2026-01-01", False), ("2026-01-31", "2026-01-31", False)]
        for date_from, date_to, draft in cases:
            with self.subTest(period=(date_from, date_to), drafts=draft):
                result = self.engine_report(date_from, date_to, include_unposted=draft,
                                            skip_zero_balance=True)
                native = self.native_trial_balance(date_from, date_to, draft=draft)
                self.assertEngineMatchesNative(result, native)
