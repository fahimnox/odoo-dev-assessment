"""Shared fixtures and hand-calculated expectations for the Trial Balance tests.

Every fixture is a set of real, balanced journal entries in a fresh company
whose currency is the Egyptian pound (EGP), with Odoo's generic chart of
accounts and a calendar fiscal year. Entries are posted, left in draft or
cancelled through Odoo's own methods (action_post, button_cancel).

The expected numbers below are written by hand from the rules in
docs/calculation_contract.md. They are constants: no test computes them from
a report, ours or Odoo's. Each row holds nine numbers:

    (initial debit, initial credit, initial balance,
     movement debit, movement credit, movement balance,
     ending debit, ending credit, ending balance)

Initial and ending debit/credit show the net side of the balance; movement
debit/credit are gross totals; a balance is debit minus credit.
"""
import copy

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon

# ---------------------------------------------------------------------------
# TB-BASE: the Stage 07 base fixture. Report period 2026-01-01 to 2026-01-31.
#
#   2025-12-31 posted     Bank debit 1,000 / Capital credit 1,000      (Misc)
#   2026-01-10 posted     Expense debit 300 / Bank credit 300          (Misc)
#   2026-01-20 posted     Bank debit 500 / Revenue credit 500          (Bank)
#   2026-01-25 draft      Expense debit 200 / Bank credit 200          (Misc)
#   2026-01-26 cancelled  Expense debit 400 / Bank credit 400          (Misc)
#   2026-02-01 posted     Expense debit 50 / Bank credit 50            (Misc)
#
# Bank, posted only: opening 1,000; movement +500 -300 = +200; ending 1,200.
# With drafts the draft credit of 200 joins the movement: +500 -500 = 0, so
# the ending balance is 1,000. Cancelled and February items never count.
# ---------------------------------------------------------------------------
TB_BASE_POSTED = {
    "bank": (1000, 0, 1000, 500, 300, 200, 1200, 0, 1200),
    "expense": (0, 0, 0, 300, 0, 300, 300, 0, 300),
    "revenue": (0, 0, 0, 0, 500, -500, 0, 500, -500),
    "capital": (0, 1000, -1000, 0, 0, 0, 0, 1000, -1000),
    "total": (1000, 1000, 0, 800, 800, 0, 1500, 1500, 0),
}
TB_BASE_WITH_DRAFTS = {
    "bank": (1000, 0, 1000, 500, 500, 0, 1000, 0, 1000),
    "expense": (0, 0, 0, 500, 0, 500, 500, 0, 500),
    "revenue": (0, 0, 0, 0, 500, -500, 0, 500, -500),
    "capital": (0, 1000, -1000, 0, 0, 0, 0, 1000, -1000),
    "total": (1000, 1000, 0, 1000, 1000, 0, 1500, 1500, 0),
}
# The same data, one journal at a time (January, posted only). A journal
# filter restricts the opening balance too: the 1,000 opening is in Misc.
TB_BASE_BANK_JOURNAL = {
    "bank": (0, 0, 0, 500, 0, 500, 500, 0, 500),
    "revenue": (0, 0, 0, 0, 500, -500, 0, 500, -500),
    "total": (0, 0, 0, 500, 500, 0, 500, 500, 0),
}
TB_BASE_MISC_JOURNAL = {
    "bank": (1000, 0, 1000, 0, 300, -300, 700, 0, 700),
    "expense": (0, 0, 0, 300, 0, 300, 300, 0, 300),
    "capital": (0, 1000, -1000, 0, 0, 0, 0, 1000, -1000),
    "total": (1000, 1000, 0, 300, 300, 0, 1000, 1000, 0),
}

# ---------------------------------------------------------------------------
# TB-X: cross-year. TB-BASE plus a posted 2025-06-30 entry:
#   Current Assets debit 700 / Revenue credit 700.
# Income and expense accounts open at the fiscal-year start; their earlier
# result is shown on Current Year Earnings (999999). Balance-sheet accounts
# open with all earlier history.
# ---------------------------------------------------------------------------
TB_X_JANUARY = {
    "current_assets": (700, 0, 700, 0, 0, 0, 700, 0, 700),
    "bank": (1000, 0, 1000, 500, 300, 200, 1200, 0, 1200),
    "capital": (0, 1000, -1000, 0, 0, 0, 0, 1000, -1000),
    "revenue": (0, 0, 0, 0, 500, -500, 0, 500, -500),
    "expense": (0, 0, 0, 300, 0, 300, 300, 0, 300),
    "earnings": (0, 700, -700, 0, 0, 0, 0, 700, -700),
    "total": (1700, 1700, 0, 800, 800, 0, 2200, 2200, 0),
}
TB_X_FEBRUARY = {
    "current_assets": (700, 0, 700, 0, 0, 0, 700, 0, 700),
    "bank": (1200, 0, 1200, 0, 50, -50, 1150, 0, 1150),
    "capital": (0, 1000, -1000, 0, 0, 0, 0, 1000, -1000),
    "revenue": (0, 500, -500, 0, 0, 0, 0, 500, -500),
    "expense": (300, 0, 300, 50, 0, 50, 350, 0, 350),
    "earnings": (0, 700, -700, 0, 0, 0, 0, 700, -700),
    "total": (2200, 2200, 0, 50, 50, 0, 2200, 2200, 0),
}
# With drafts, the January draft (Expense 200 / Bank 200) is in the opening.
TB_X_FEBRUARY_WITH_DRAFTS = {
    "current_assets": (700, 0, 700, 0, 0, 0, 700, 0, 700),
    "bank": (1000, 0, 1000, 0, 50, -50, 950, 0, 950),
    "capital": (0, 1000, -1000, 0, 0, 0, 0, 1000, -1000),
    "revenue": (0, 500, -500, 0, 0, 0, 0, 500, -500),
    "expense": (500, 0, 500, 50, 0, 50, 550, 0, 550),
    "earnings": (0, 700, -700, 0, 0, 0, 0, 700, -700),
    "total": (2200, 2200, 0, 50, 50, 0, 2200, 2200, 0),
}

# ---------------------------------------------------------------------------
# TB-Z: zero activity. January 2026.
#   2025-12-31 Bank debit 1,000 / Capital credit 1,000
#   2026-01-05 Current Assets debit 250 / Bank credit 250
#   2026-01-15 Bank debit 250 / Current Assets credit 250
# Current Assets has no opening and no ending balance, but it moved: it stays
# visible with Skip Zero Balance. Prepaid Expenses (128000) has nothing and is
# hidden with Skip Zero Balance, listed with zeros without it.
# ---------------------------------------------------------------------------
TB_Z_JANUARY = {
    "current_assets": (0, 0, 0, 250, 250, 0, 0, 0, 0),
    "bank": (1000, 0, 1000, 250, 250, 0, 1000, 0, 1000),
    "capital": (0, 1000, -1000, 0, 0, 0, 0, 1000, -1000),
    "total": (1000, 1000, 0, 500, 500, 0, 1000, 1000, 0),
}
TB_Z_UNTOUCHED = (0, 0, 0, 0, 0, 0, 0, 0, 0)

# ---------------------------------------------------------------------------
# TB-C: currencies. Rates: 1 USD = 50 EGP, 1 EUR = 55 EGP. Account X is
# Current Assets (101000); every counterpart is on Bank, in EGP.
#   2025-12-20 X debit 1,000 (USD 20)    / Bank credit 1,000
#   2025-12-22 Bank debit 1,650          / X credit 1,650 (EUR -30)
#   2026-01-05 X debit 5,000 (USD 100)   / Bank credit 5,000
#   2026-01-12 Bank debit 2,000          / X credit 2,000 (USD -40)
#   2026-01-18 X debit 3,850 (EUR 70)    / Bank credit 3,850
#   2026-01-25 Bank debit 1,100          / X credit 1,100 (EUR -20)
# January 2026. The Amount Currency column holds the period movement only:
# USD 100 - 40 = 60 and EUR 70 - 20 = 50, never added together.
# ---------------------------------------------------------------------------
TB_C_JANUARY = {
    "current_assets": (0, 650, -650, 8850, 3100, 5750, 5100, 0, 5100),
    "bank": (650, 0, 650, 3100, 8850, -5750, 0, 5100, -5100),
    "total": (650, 650, 0, 11950, 11950, 0, 5100, 5100, 0),
}
# With Show Amount Currency: one row per (account, transaction currency).
TB_C_JANUARY_BY_CURRENCY = {
    ("current_assets", "USD"): (1000, 0, 1000, 5000, 2000, 3000, 4000, 0, 4000),
    ("current_assets", "EUR"): (0, 1650, -1650, 3850, 1100, 2750, 1100, 0, 1100),
    ("bank", "EGP"): (650, 0, 650, 3100, 8850, -5750, 0, 5100, -5100),
    "total": (1650, 1650, 0, 11950, 11950, 0, 5100, 5100, 0),
}
TB_C_JANUARY_AMOUNT_CURRENCY = {
    ("current_assets", "USD"): 60.0,
    ("current_assets", "EUR"): 50.0,
    ("bank", "EGP"): -5750.0,
}

# ---------------------------------------------------------------------------
# TB-A: analytic. March 2026. Plans: A (accounts A1, A2) and B (account B1).
#   2026-03-10 Expense debit 1,000, distribution A1 60% / A2 40%;
#              Bank credit 1,000 without distribution
#   2026-03-12 Expense debit 200, composite key "A1,B1" at 100%;
#              Bank credit 200
# Selected policy (native, whole item): an item counts once, at its full
# amount, when its distribution contains the selected account.
# ---------------------------------------------------------------------------
TB_A_MARCH = {
    None: {
        "expense": (0, 0, 0, 1200, 0, 1200, 1200, 0, 1200),
        "bank": (0, 0, 0, 0, 1200, -1200, 0, 1200, -1200),
        "total": (0, 0, 0, 1200, 1200, 0, 1200, 1200, 0),
    },
    "A1": {
        "expense": (0, 0, 0, 1200, 0, 1200, 1200, 0, 1200),
        "total": (0, 0, 0, 1200, 0, 1200, 1200, 0, 1200),
    },
    "A2": {
        "expense": (0, 0, 0, 1000, 0, 1000, 1000, 0, 1000),
        "total": (0, 0, 0, 1000, 0, 1000, 1000, 0, 1000),
    },
    "B1": {
        "expense": (0, 0, 0, 200, 0, 200, 200, 0, 200),
        "total": (0, 0, 0, 200, 0, 200, 200, 0, 200),
    },
}
# The rejected alternative (proportional allocation), for the record only:
# A1 would show 600 + 200 = 800, A2 400 and B1 200.
TB_A_PROPORTIONAL_EXPENSE = {"A1": 800, "A2": 400, "B1": 200}

# ---------------------------------------------------------------------------
# TB-M: two companies, both in EGP. January 2026.
#   Company 1: 2026-01-10 Bank debit 300 / Capital credit 300
#   Company 2: 2026-01-12 Bank debit 900 / Capital credit 900
# A report covers exactly one company.
# ---------------------------------------------------------------------------
TB_M_COMPANY_1 = {
    "bank": (0, 0, 0, 300, 0, 300, 300, 0, 300),
    "capital": (0, 0, 0, 0, 300, -300, 0, 300, -300),
    "total": (0, 0, 0, 300, 300, 0, 300, 300, 0),
}
TB_M_COMPANY_2 = {
    "bank": (0, 0, 0, 900, 0, 900, 900, 0, 900),
    "capital": (0, 0, 0, 0, 900, -900, 0, 900, -900),
    "total": (0, 0, 0, 900, 900, 0, 900, 900, 0),
}

# ---------------------------------------------------------------------------
# TB-R: restricted access. January 2026. A record rule hides the journal
# items of the "Restricted" journal (code RSTR) from normal users.
#   2026-01-10 Expense debit 300 / Bank credit 300   (Misc)
#   2026-01-15 Expense debit 70 / Bank credit 70     (Restricted)
# ---------------------------------------------------------------------------
TB_R_VISIBLE = {
    "expense": (0, 0, 0, 300, 0, 300, 300, 0, 300),
    "bank": (0, 0, 0, 0, 300, -300, 0, 300, -300),
    "total": (0, 0, 0, 300, 300, 0, 300, 300, 0),
}
TB_R_EVERYTHING = {
    "expense": (0, 0, 0, 370, 0, 370, 370, 0, 370),
    "bank": (0, 0, 0, 0, 370, -370, 0, 370, -370),
    "total": (0, 0, 0, 370, 370, 0, 370, 370, 0),
}

# ---------------------------------------------------------------------------
# TB-H: deep hierarchy. Account groups (prefix, level):
#   "1" (1) > "10" (2) > "101" (3) > "1014" (4) > "10140" (5); "4" (1).
# Bank 101401 is under "10140", Current Assets 101000 under "101", Product
# Sales 400000 and Cash Discount Loss 443000 under "4"; Capital 301000 has
# no group. January 2026:
#   2025-12-31 Bank debit 1,000 / Capital credit 1,000
#   2026-01-10 Current Assets debit 400 / Bank credit 400
#   2026-01-20 Bank debit 500 / Product Sales credit 500
#   2026-01-22 Cash Discount Loss debit 120 / Bank credit 120
# A group row sums the displayed debit and credit of its descendant accounts
# separately, so "4" shows both sides. Totals sum account rows only.
# ---------------------------------------------------------------------------
TB_H_ACCOUNTS = {
    "bank": (1000, 0, 1000, 500, 520, -20, 980, 0, 980),
    "current_assets": (0, 0, 0, 400, 0, 400, 400, 0, 400),
    "revenue": (0, 0, 0, 0, 500, -500, 0, 500, -500),
    "cash_discount_loss": (0, 0, 0, 120, 0, 120, 120, 0, 120),
    "capital": (0, 1000, -1000, 0, 0, 0, 0, 1000, -1000),
    "total": (1000, 1000, 0, 1020, 1020, 0, 1500, 1500, 0),
}
TB_H_GROUPS = {
    "1": (1000, 0, 1000, 900, 520, 380, 1380, 0, 1380),
    "10": (1000, 0, 1000, 900, 520, 380, 1380, 0, 1380),
    "101": (1000, 0, 1000, 900, 520, 380, 1380, 0, 1380),
    "1014": (1000, 0, 1000, 500, 520, -20, 980, 0, 980),
    "10140": (1000, 0, 1000, 500, 520, -20, 980, 0, 980),
    "4": (0, 0, 0, 120, 500, -380, 120, 500, -380),
    "(No Group)": (0, 1000, -1000, 0, 0, 0, 0, 1000, -1000),
}
TB_H_LEVELS = {"1": 1, "10": 2, "101": 3, "1014": 4, "10140": 5, "4": 1}
# Group rows shown by Hierarchy Only Parents with Account Level Up To N.
TB_H_ONLY_PARENTS = {
    1: ["1", "4", "(No Group)"],
    2: ["1", "10", "4", "(No Group)"],
    3: ["1", "10", "101", "4", "(No Group)"],
    4: ["1", "10", "101", "1014", "4", "(No Group)"],
    5: ["1", "10", "101", "1014", "10140", "4", "(No Group)"],
}


# ---------------------------------------------------------------------------
# TB-D: date boundaries, reversal, cancelled, draft, negative balance (Stage 08).
# Report period 2026-01-01 to 2026-01-31.
#   2025-12-31 posted     Bank debit 100 / Capital credit 100        day before
#   2026-01-01 posted     Bank debit 10 / Revenue credit 10          first day
#   2026-01-10 posted     Expense debit 30 / Bank credit 30          reversed by:
#   2026-01-12 posted     Bank debit 30 / Expense credit 30          (_reverse_moves)
#   2026-01-15 cancelled  Expense debit 70 / Bank credit 70
#   2026-01-20 posted     Expense debit 200 / Bank credit 200        overdraws Bank
#   2026-01-25 draft      Expense debit 5 / Bank credit 5
#   2026-01-31 posted     Expense debit 20 / Bank credit 20          last day
#   2026-02-01 posted     Expense debit 40 / Bank credit 40          day after
# Bank: 100 + (10 + 30) - (30 + 200 + 20) = -110, a credit balance. The
# reversal adds 30 to both sides of Bank and Expense; the net is unchanged.
# ---------------------------------------------------------------------------
TB_D_JANUARY = {
    "bank": (100, 0, 100, 40, 250, -210, 0, 110, -110),
    "capital": (0, 100, -100, 0, 0, 0, 0, 100, -100),
    "revenue": (0, 0, 0, 0, 10, -10, 0, 10, -10),
    "expense": (0, 0, 0, 250, 30, 220, 220, 0, 220),
    "total": (100, 100, 0, 290, 290, 0, 220, 220, 0),
}
TB_D_JANUARY_WITH_DRAFTS = {
    "bank": (100, 0, 100, 40, 255, -215, 0, 115, -115),
    "capital": (0, 100, -100, 0, 0, 0, 0, 100, -100),
    "revenue": (0, 0, 0, 0, 10, -10, 0, 10, -10),
    "expense": (0, 0, 0, 255, 30, 225, 225, 0, 225),
    "total": (100, 100, 0, 295, 295, 0, 225, 225, 0),
}

# The order of the nine numbers in the engine's rows and totals.
AMOUNT_KEYS = (
    "initial_debit", "initial_credit", "initial_balance",
    "debit", "credit", "balance",
    "ending_debit", "ending_credit", "ending_balance",
)


def debit_credit_pairs(row):
    """The six debit/credit numbers of a nine-number row."""
    return (row[0], row[1], row[3], row[4], row[6], row[7])


class TrialBalanceCase(AccountTestInvoicingCommon):
    """A fresh EGP company with the generic chart and a calendar fiscal year."""

    chart_template = "generic_coa"

    @classmethod
    def setup_independent_company(cls, **kwargs):
        egp = cls._enable_currency("EGP")
        return cls._create_company(name="AZK TB Company", currency_id=egp.id, **kwargs)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.misc_journal = cls.company_data["default_journal_misc"]
        cls.bank_journal = cls.company_data["default_journal_bank"]
        cls.accounts = cls._chart_accounts(cls.company)

    @classmethod
    def _chart_accounts(cls, company):
        """The generic-chart accounts the fixtures use, by short name."""
        codes = {
            "bank": "101401",
            "current_assets": "101000",
            "prepaid": "128000",
            "capital": "301000",
            "revenue": "400000",
            "cash_discount_loss": "443000",
            "expense": "600000",
            "earnings": "999999",
        }
        Account = cls.env["account.account"].with_company(company)
        domain = Account._check_company_domain(company)
        accounts = {}
        for name, code in codes.items():
            account = Account.search([("code", "=", code), *domain])
            assert len(account) == 1, f"expected one account {code} in {company.name}"
            accounts[name] = account
        return accounts

    @classmethod
    def _entry(cls, date, lines, state="posted", journal=None, ref=None, company=None):
        """Create one balanced journal entry and bring it to ``state``.

        ``lines`` holds (account, debit, credit) tuples, optionally with a
        fourth item: extra journal-item values (currency, amount currency,
        analytic distribution). A cancelled entry is posted first and then
        cancelled with Odoo's own button_cancel.
        """
        company = company or cls.company
        journal = journal or cls.misc_journal
        move = cls.env["account.move"].with_company(company).create({
            "move_type": "entry",
            "date": date,
            "journal_id": journal.id,
            "ref": ref,
            "line_ids": [
                Command.create({
                    "account_id": account.id,
                    "name": ref,
                    "debit": debit,
                    "credit": credit,
                    **(extra[0] if extra else {}),
                })
                for account, debit, credit, *extra in lines
            ],
        })
        if state in ("posted", "cancel"):
            move.action_post()
        if state == "cancel":
            move.button_cancel()
        assert move.state == state, f"{ref}: state {move.state}, expected {state}"
        return move

    @classmethod
    def _build_tb_base(cls):
        a = cls.accounts
        cls.base_moves = {
            "opening": cls._entry("2025-12-31", [(a["bank"], 1000, 0), (a["capital"], 0, 1000)],
                                  ref="TB-BASE opening capital"),
            "expense": cls._entry("2026-01-10", [(a["expense"], 300, 0), (a["bank"], 0, 300)],
                                  ref="TB-BASE expense"),
            "revenue": cls._entry("2026-01-20", [(a["bank"], 500, 0), (a["revenue"], 0, 500)],
                                  journal=cls.bank_journal, ref="TB-BASE revenue"),
            "draft": cls._entry("2026-01-25", [(a["expense"], 200, 0), (a["bank"], 0, 200)],
                                state="draft", ref="TB-BASE draft expense"),
            "cancelled": cls._entry("2026-01-26", [(a["expense"], 400, 0), (a["bank"], 0, 400)],
                                    state="cancel", ref="TB-BASE cancelled expense"),
            "february": cls._entry("2026-02-01", [(a["expense"], 50, 0), (a["bank"], 0, 50)],
                                   ref="TB-BASE February expense"),
        }

    @classmethod
    def _build_tb_d(cls):
        a = cls.accounts
        cls._entry("2025-12-31", [(a["bank"], 100, 0), (a["capital"], 0, 100)], ref="TB-D day before")
        cls._entry("2026-01-01", [(a["bank"], 10, 0), (a["revenue"], 0, 10)], ref="TB-D first day")
        reversed_move = cls._entry("2026-01-10", [(a["expense"], 30, 0), (a["bank"], 0, 30)],
                                   ref="TB-D reversed")
        # Odoo's own reversal (what the Reverse button's wizard calls): a
        # copy with every amount negated, posted on its own date.
        cls.reversal = reversed_move._reverse_moves([{"date": "2026-01-12", "ref": "TB-D reversal"}])
        cls.reversal.action_post()
        cls._entry("2026-01-15", [(a["expense"], 70, 0), (a["bank"], 0, 70)], state="cancel",
                   ref="TB-D cancelled")
        cls._entry("2026-01-20", [(a["expense"], 200, 0), (a["bank"], 0, 200)], ref="TB-D overdraft")
        cls._entry("2026-01-25", [(a["expense"], 5, 0), (a["bank"], 0, 5)], state="draft",
                   ref="TB-D draft")
        cls._entry("2026-01-31", [(a["expense"], 20, 0), (a["bank"], 0, 20)], ref="TB-D last day")
        cls._entry("2026-02-01", [(a["expense"], 40, 0), (a["bank"], 0, 40)], ref="TB-D day after")

    # ------------------------------------------------------------------
    # Our engine (models/trial_balance_engine.py)
    # ------------------------------------------------------------------
    def engine_report(self, date_from, date_to, company=None, user=None, **options):
        """Run our engine as ``user`` (default: the test user) on one active company."""
        company = company or self.company
        Engine = self.env["azk_dynamic_trial_balance.engine"]
        if user:
            Engine = Engine.with_user(user)
        Engine = Engine.with_context(allowed_company_ids=[company.id])
        return Engine.compute({
            "date_from": date_from, "date_to": date_to, "company_id": company.id, **options,
        })

    def engine_rows(self, result, accounts=None, lines=False):
        """The result's rows keyed like the expectation tables, plus "total".

        Account rows are keyed by short account name (or code), and by
        (name, currency) with Show Amount Currency; group rows by their
        prefix, or "(No Group)". Values are the nine numbers. By default
        the leaf rows are used; ``lines=True`` uses the displayed lines.
        """
        names = {account.id: name for name, account in (accounts or self.accounts).items()}
        by_currency = result["filters"]["show_amount_currency"]
        rows = {}
        for row in (result["lines"] if lines else result["leaf_rows"]):
            if row["type"] == "account":
                key = names.get(row["account_id"], row["account_code"])
                if by_currency:
                    key = (key, row["currency_name"])
            else:
                key = row["group_code"] or "(No Group)"
            self.assertNotIn(key, rows, f"row {key} appears twice")
            rows[key] = tuple(row[name] for name in AMOUNT_KEYS)
        rows["total"] = tuple(result["totals"][name] for name in AMOUNT_KEYS)
        return rows

    def assertRowsEqual(self, rows, expected):
        """Exactly the expected rows, each with exactly its nine numbers."""
        self.assertEqual(set(rows), set(expected))
        for key, values in expected.items():
            with self.subTest(row=key):
                self.assertEqual(rows[key], tuple(float(value) for value in values))

    def assertEngineMatchesNative(self, result, native, accounts=None):
        """Our account lines and totals equal the standard report's, debit and credit.

        Both reports list the same accounts (ours with Skip Zero Balance)
        and give each the same six debit and credit numbers. Balances are
        not compared: the standard report has none.
        """
        ours = self.engine_rows(result, accounts)
        theirs = {key: values for key, values in native.items()
                  if not key.startswith(("group ", "_")) and key != "(No Group)"}
        self.assertEqual(set(ours), set(theirs))
        for key, values in theirs.items():
            with self.subTest(line=key):
                self.assertEqual(debit_credit_pairs(ours[key]), values)

    # ------------------------------------------------------------------
    # Odoo's standard Trial Balance (account_reports), used as a reference
    # ------------------------------------------------------------------
    def native_trial_balance(self, date_from, date_to, company=None, draft=False,
                             hierarchy=False, journal=None, analytic=None, user=None,
                             accounts=None):
        """Run the standard Trial Balance and return its numbers by line.

        Keys: the short account names of ``accounts`` (default
        ``self.accounts``; the account code when an account has no short
        name), "group <prefix>" for account-group lines, "(No Group)" and
        "total". Values: Initial Debit/Credit, period Debit/Credit and End
        Debit/Credit, rounded to cents. Only one company is ever active, as
        in our report.
        """
        company = company or self.company
        accounts = accounts or self.accounts
        report = self.env.ref("account_reports.trial_balance_report")
        if user:
            report = report.with_user(user)
        report = report.with_context(allowed_company_ids=[company.id])
        options = report.get_options({
            "selected_variant_id": report.id,
            "date": {"date_from": date_from, "date_to": date_to, "mode": "range",
                     "filter": "custom"},
            "all_entries": draft,
            "hierarchy": hierarchy,
            "unfold_all": True,
            "analytic_accounts": analytic.ids if analytic else [],
        })
        self.assertEqual([c["id"] for c in options["companies"]], [company.id])
        self.assertEqual(options["all_entries"], draft)
        if journal:
            options = copy.deepcopy(options)
            for item in options["journals"]:
                item["selected"] = item.get("model") == "account.journal" and item["id"] == journal.id
        names = {account.id: name for name, account in accounts.items()}
        rows, depth = {}, {}
        for line in report._get_lines(options):
            model, res_id = report._get_model_info_from_id(line["id"])
            values = tuple(round(column["no_format"] or 0.0, 2) for column in line["columns"])
            self.assertEqual(len(values), 6, line["name"])
            if model == "account.account":
                key = names.get(res_id) or self.env["account.account"].browse(res_id).with_company(company).code
            elif model == "account.group" and res_id:
                key = "group " + self.env["account.group"].browse(res_id).code_prefix_start
            elif line["name"] == "(No Group)":
                key = "(No Group)"
            elif line["name"] == "Total":
                key = "total"
            else:
                self.fail(f"unexpected native line {line['name']!r} ({model})")
            self.assertNotIn(key, rows, f"line {key} appears twice")
            rows[key] = values
            depth[line["id"]] = depth.get(line.get("parent_id"), 0) + 1
            if key.startswith("group ") or key == "(No Group)":
                rows.setdefault("_depth", {})[key] = depth[line["id"]]
        return rows

    def assertNativeMatches(self, native, expected, keys=None):
        """Compare native debit/credit numbers with hand-calculated rows."""
        keys = keys or [key for key in expected]
        for key in keys:
            with self.subTest(line=key):
                self.assertIn(key, native)
                self.assertEqual(native[key], tuple(float(v) for v in debit_credit_pairs(expected[key])))

    def assertSameLines(self, native, expected):
        """The native report lists exactly the expected account lines and the total."""
        listed = {key for key in native if not key.startswith(("group ", "_"))
                  and key != "(No Group)"}
        self.assertEqual(listed, set(expected))

    def assertExpectationsConsistent(self, rows, leaf_keys=None, net_rows=True):
        """Check a hand-written expectation table against the contract's identities.

        Per row: debit - credit = balance in each column group; ending =
        opening + movement. Account rows (``net_rows``) show only the net side
        of the opening and ending balances; group rows may show both sides.
        The total row is the sum of the leaf rows. These checks catch typing
        mistakes in the hand calculation; they do not compute the numbers.
        """
        leaf_keys = leaf_keys or [key for key in rows if key != "total"]
        for key, row in rows.items():
            with self.subTest(row=key):
                for start in (0, 3, 6):
                    self.assertEqual(row[start] - row[start + 1], row[start + 2])
                self.assertEqual(row[2] + row[5], row[8])
                if net_rows and key != "total":
                    self.assertTrue(row[0] == 0 or row[1] == 0)
                    self.assertTrue(row[6] == 0 or row[7] == 0)
        if "total" in rows:
            sums = tuple(sum(rows[key][i] for key in leaf_keys) for i in range(9))
            self.assertEqual(sums, rows["total"])
