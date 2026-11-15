from datetime import date

from odoo.tests import tagged

from .common import (
    TB_BASE_BANK_JOURNAL,
    TB_BASE_MISC_JOURNAL,
    TB_BASE_POSTED,
    TB_BASE_WITH_DRAFTS,
    TrialBalanceCase,
)


@tagged("post_install", "-at_install")
class TestBaseFixture(TrialBalanceCase):
    """TB-BASE, the Stage 07 base fixture, against Odoo's standard Trial Balance.

    The expected numbers are hand-calculated constants (tests/common.py).
    Here they are compared with the standard Enterprise Trial Balance run
    with the same company, dates and posting option; our own calculation is
    compared with the same constants in Stage 08.
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
