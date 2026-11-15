from odoo.tests import tagged

from .common import (
    TB_X_FEBRUARY,
    TB_X_FEBRUARY_WITH_DRAFTS,
    TB_X_JANUARY,
    TrialBalanceCase,
)


@tagged("post_install", "-at_install")
class TestCrossYearConventions(TrialBalanceCase):
    """TB-X: the fiscal-year rules of the standard Trial Balance.

    TB-BASE plus prior-year revenue (2025-06-30, Current Assets 700 /
    Revenue 700). The hand-calculated tables in tests/common.py follow the
    contract: balance-sheet accounts open with all earlier history; income
    and expense accounts open at the fiscal-year start; their earlier result
    appears on Current Year Earnings, and no journal entry is invented for it.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._build_tb_base()
        a = cls.accounts
        cls.prior_year = cls._entry(
            "2025-06-30", [(a["current_assets"], 700, 0), (a["revenue"], 0, 700)],
            ref="TB-X prior-year revenue",
        )

    def test_hand_calculations_are_consistent(self):
        for name, table in {
            "January": TB_X_JANUARY,
            "February": TB_X_FEBRUARY,
            "February with drafts": TB_X_FEBRUARY_WITH_DRAFTS,
        }.items():
            with self.subTest(table=name):
                self.assertExpectationsConsistent(table)

    def test_january_opens_a_new_fiscal_year(self):
        native = self.native_trial_balance("2026-01-01", "2026-01-31")
        self.assertSameLines(native, TB_X_JANUARY)
        self.assertNativeMatches(native, TB_X_JANUARY)
        # Revenue opens at zero: the 700 of 2025 is on Current Year Earnings.
        self.assertEqual(native["revenue"][:2], (0.0, 0.0))
        self.assertEqual(native["earnings"][:2], (0.0, 700.0))

    def test_february_opens_from_the_fiscal_year_start(self):
        native = self.native_trial_balance("2026-02-01", "2026-02-28")
        self.assertSameLines(native, TB_X_FEBRUARY)
        self.assertNativeMatches(native, TB_X_FEBRUARY)

    def test_drafts_also_change_the_opening_balance(self):
        native = self.native_trial_balance("2026-02-01", "2026-02-28", draft=True)
        self.assertSameLines(native, TB_X_FEBRUARY_WITH_DRAFTS)
        self.assertNativeMatches(native, TB_X_FEBRUARY_WITH_DRAFTS)

    def test_carry_forward_is_not_a_journal_entry(self):
        # The report shows 700 on Current Year Earnings, yet no journal item
        # was ever posted there: the carry-forward is a presentation.
        native = self.native_trial_balance("2026-01-01", "2026-01-31")
        self.assertEqual(native["earnings"][1], 700.0)
        lines = self.env["account.move.line"].search([
            ("company_id", "=", self.company.id),
            ("account_id", "=", self.accounts["earnings"].id),
        ])
        self.assertFalse(lines)
