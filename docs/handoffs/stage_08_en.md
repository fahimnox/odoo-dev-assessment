# Stage 08 handoff: Trial Balance calculation engine

_2026-11-15. Edition `enterprise-20241208` (port 8071), continuing from the Stage 07 commit `cabfb75`. Stage 04 stays PARTIAL. The Preview, PDF and XLSX buttons stay entry points until Stage 09._

## What this stage delivers

- **The engine** `azk_dynamic_trial_balance.engine` (`models/trial_balance_engine.py`), with one entry point, `compute(options)`. It returns one normalized result:
  - the filters, the display lines, the leaf (account) rows and the hierarchy (group) rows;
  - base-currency totals and per-currency totals;
  - warnings and metadata.
  Every output in Stage 09 will render this result and compute nothing itself. The result's keys are listed in [calculation_contract.md](../calculation_contract.md) 15.
- **Access inside the engine:**
  - It requires the accounting read-only group (D-50) and validates every option again, for the wizard and for any client-sent options.
  - It runs three grouped `_read_group` queries as the calling user, so access rights and every record rule apply. There is no `sudo()` and no SQL.
- **The wizard's** `_compute_report()` returns the result for the wizard's options, with the caller's access.
- **Tests:** 85 in total, 37 of them new. They compare the engine with the hand-calculated constants of every fixture, and with the standard Trial Balance where it has the same option.
- **[test_results.md](../test_results.md)** holds the exact commands and results.

## One Bank journal item, from the database to the totals

Take the base fixture TB-BASE and the Bank line of the entry posted on 2026-01-20 in the Bank journal: Bank debit 500 / Revenue credit 500. The report runs for January 2026, posted only.

1. **The request.**
   - `TrialBalanceWizard._compute_report()` (`models/trial_balance_wizard.py`) calls `_get_report_options()`, which builds the plain options with `normalize_options()` (`models/report_options.py`).
   - It passes them to `TrialBalanceEngine.compute()` (`models/trial_balance_engine.py`). `compute` checks `account.group_account_readonly`, validates the options again, and switches to the report company with `with_company`, because account codes are company-dependent.
2. **The period.** `_compute` takes the fiscal-year start S from `company.compute_fiscalyear_dates(date_from)`. Here S = 2026-01-01, the same day as Date From.
3. **The accounts.** `_accounts_in_scope` finds all the company's accounts (no prefix was given), so no account filter is added to the item queries.
4. **The scope.** `_scope_domain` keeps the items of this company that are not section or note lines and whose entry is posted. Our item passes.
   - The 2026-01-25 draft credit of 200 fails the state test, and so does the 2026-01-26 cancelled credit of 400.
5. **The movement.** `_add_movement` runs one `_read_group` over the scope dated 2026-01-01 to 2026-01-31, grouped by account. For Bank 101401 it returns:
   - debit 500: our item;
   - credit 300: the 2026-01-10 expense payment.
   The 2026-02-01 credit of 50 is after Date To.
6. **The opening.** `_add_opening` runs one `_read_group` over the scope dated before 2026-01-01 for balance-sheet accounts (`include_initial_balance`), and from S for income and expense.
   - Bank is a balance-sheet account, so its opening is the 2025-12-31 debit of 1,000.
   - Our item is not in it: it is dated in the period.
7. **The carry-forward.** `_add_carry_forward` sums income and expense before S: nothing in TB-BASE, so 0.
8. **The row.** `_leaf_rows` calls `_amounts(opening=1000, debit=500, credit=300)`:
   - movement balance 500 - 300 = 200;
   - ending 1,000 + 200 = 1,200;
   - the opening and ending show their net side (1,000 debit, then 1,200 debit); the movement shows both sides;
   - each number is rounded to the company currency.
9. **Skip Zero Balance** (if ticked). `_is_zero_row` keeps the row: it has activity and balances.
10. **Hierarchy** (if ticked). `_hierarchy` looks up `account.group_id`.
    - TB-BASE's company has no account groups, so Bank goes under "(No Group)" and the result warns `no_account_groups`.
    - In TB-H, the same kind of line is added exactly once to each of the five groups above Bank: 10140, 1014, 101, 10 and 1.
11. **The totals.** `_sum_amounts` adds the account rows only, never group rows.
    - Movement debit: 500 (our item, on Bank) + 300 (Expense) = 800.
    - Ending debit: 1,200 + 300 = 1,500. Ending credit: 500 (Revenue) + 1,000 (Capital) = 1,500. The report balances.
12. **With Include Unposted Entries.** The scope becomes "not cancelled". The draft credit of 200 joins Bank's movement: credit 500, balance 0, ending **1,000**. Expense ends at 500 and the totals stay 1,500 / 1,500.

`test_engine_posted_only` and `test_engine_with_drafts` check these numbers against the hand-written constants.

## January versus February, on the cross-year fixture

TB-X is TB-BASE plus one 2025 entry: on 2025-06-30, Current Assets debit 700 / Revenue credit 700. That is income of the 2025 fiscal year. The fiscal year is the calendar year, so S = 2026-01-01 for both months.

**January 2026** (Date From = 2026-01-01 = S):

- `_add_opening`, balance-sheet accounts: everything before 1 January. Bank 1,000 debit, Current Assets 700 debit, Capital 1,000 credit.
- `_add_opening`, income and expense: only from S to the day before Date From. That is an empty range, so Revenue opens at 0, not at 700 credit.
- `_add_carry_forward`: income and expense before S, the 2025 revenue of 700. It appears as the opening of Current Year Earnings (999999): 700 credit. `metadata.carry_forward` is -700.
- Totals: Initial 1,700 / 1,700; Movement 800 / 800; End 2,200 / 2,200.

**February 2026** (Date From = 2026-02-01, S still 2026-01-01):

- Balance-sheet accounts: everything before 1 February. Bank 1,000 + 500 - 300 = 1,200 debit.
- Income and expense: from S, so January is now in the opening. Revenue opens at 500 credit and Expense at 300 debit.
- Carry-forward: still only before S, so Current Year Earnings keeps 700 credit. The January result is not carried forward; it is still part of this fiscal year.
- Movement: the 2026-02-01 entry, Expense 50 debit and Bank 50 credit.
- Ending: Bank 1,150, Expense 350, Revenue 500 credit, Current Year Earnings 700 credit. Totals 2,200 / 2,200.
- With drafts, the January draft is in February's opening: Bank opens at 1,000 and Expense at 500.

In both months the 2025 revenue never shows on Revenue: it belongs to a closed fiscal year, and the report presents it on Current Year Earnings without any journal entry. The engine and the standard Trial Balance give the same numbers for all three cases (`test_engine_january_february_and_drafts`).

## Comparison with the standard Trial Balance: exact scope

**Matched options:**

- the same company, and only that company active;
- the same dates;
- Draft Entries equal to Include Unposted Entries;
- the same single journal or analytic account;
- hierarchy off, except for TB-H.

**Compared:** every account line's Initial, period and End debit and credit, and the totals. Our side uses Skip Zero Balance, because the standard report lists only accounts that have journal items. All PASS.

- **TB-BASE:** January posted; with drafts; the Bank journal only; the Misc journal only.
- **TB-X:** January; February; February with drafts.
- **TB-D:** January posted and with drafts; the single days 2026-01-01 and 2026-01-31.
- **TB-Z:** January.
- **TB-C:** January, without currency rows.
- **TB-A:** March, with no filter, A1, A2 and B1.
- **TB-M:** company 1 and company 2.
- **TB-R:** as the restricted reader and as the accountant.
- **TB-H:** with the hierarchy, including group lines, "(No Group)" and group depths.
- **`azk_ee24`'s own demo data** (`scripts/tb_engine_vs_native.py`, admin, rolled back): 6 of 6 cases.
  - Covered: this month, fiscal year to date and the previous fiscal year, posted and with drafts, plus the sales journal alone.
  - Limit: there are no draft items in those periods, so "with drafts" equals "posted" there.

**Not compared,** because the standard report has no equivalent option:

- currency rows;
- Skip Zero Balance and the listing of accounts without items;
- Hierarchy Only Parents and its level;
- account prefixes.

These are tested against the hand-calculated constants only. Custom fiscal years, branches and period comparisons are not covered by any test.

## The analytic policy, with a concrete example

The fixture has an Expense item of 1,000 with distribution A1 60% / A2 40%, and an item of 200 with the composite key "A1,B1".

- **Our engine** (whole items, the same as the standard report): A1 gives 1,000 + 200 = **1,200**, A2 gives 1,000, B1 gives 200, and no filter gives 1,200.
- **Proportional allocation** would give A1 600 + 200 = 800, A2 400 and B1 200.

The test asserts 1,200, not 800. This is a documented choice (A-15, D-07), and question Q-03 for the team lead is still open. A filtered report need not balance: the Bank items carry no distribution.

## Checks performed

All run by the agent on 2026-11-15; logs are in `<kit-root>/runtime/logs/`.

1. **Free space on C: before Docker work:** 47 GB. It stayed at 47 to 48 GB, sampled every 30 s during the three test runs.
2. **`scripts/dev.sh test azk_dynamic_trial_balance`:**
   - run 1: PASS, 84 of 84;
   - run 2: PASS, 85 of 85, with an added rounding test and logged query counts;
   - **run 3, on the final code: PASS.** "0 failed, 0 error(s) of 85 tests", 0 warning lines, exit code 0, 326 s.
3. **Query count:** 15 to 16 queries per report after warm-up, whether 4 or 24 accounts have amounts. No large-scale timing was measured.
4. **`scripts/dev.sh update azk_dynamic_trial_balance` on `azk_ee24`:** PASS twice, 0 warnings; 18.0.1.2.0 installed.
5. **`scripts/dev.sh shell azk_ee24 < scripts/tb_engine_vs_native.py`:** PASS, 6 of 6 cases match.
6. **Headless Chrome check of the wizard** (`scripts/tb_wizard_smoke_check.py`):
   - The first attempt failed at the login page, because the web server was stopped (next section).
   - After `scripts/dev.sh start`: PASS, 8 of 8, with the new message "The Preview is not available yet. Your options are valid, but the report outputs are still being built."

**NOT RUN:** the Preview, PDF and XLSX outputs, which are Stage 09.

## Docker restart before this stage

Both containers stopped at the same second, 06:20:26 UTC. That was after the Stage 07 commit and before this stage's work. The web server exited with code 255 and the database with 0.

Docker's engine now reports version 29.9.2; Stage 01 recorded 29.4.0. So Docker Desktop was most likely updated and restarted. That is an inference: the engine kept no events from before its restart.

The services do not restart by themselves (`restart: "no"`), and `scripts/dev.sh update` restarts the web server only if it is running. `scripts/dev.sh start` brought it back. No data was affected: the tests and upgrades ran in their own short-lived containers.

## Problems found and fixed

- **Found in self-review of the draft engine, before any run:**
  - Accounts were browsed one at a time, so the company-dependent `code` and `group_id` would have run one query per account. The fix uses one shared recordset (`_accounts_by_id`).
  - `max()` could return -0.0, which an output could print as "-0.00"; the net side is now written out.
  - `fetch()` was called on a computed field.
- **The manifest version was not bumped before the first upgrade of `azk_ee24`.** It was set to 18.0.1.2.0, `azk_ee24` was upgraded again, and the final test run used exactly the committed code.
- **The first pass needed more evidence:** after run 1 passed, a rounding test (0.10 + 0.20 shows as 0.30) and logged query counts were added (run 2).

## Open issues and remaining gaps

- **Preview, PDF and XLSX (Stage 09):** the `account_reports` handler and report record that render the result (D-53). The buttons stay entry points (D-47).
- **Trial Balance demo data** (T-21 to T-23) is still to be added. The fixtures are test data.
- **Not compared with the standard report:** currency rows, Skip Zero Balance, Only Parents and its level, prefixes. **Not covered by any test:** custom fiscal years, branches, period comparisons.
- **Open questions:** Q-03 (the analytic policy) and Q-06 (the license). The wizard mockup (M-02) is still missing.
- **After a Docker Desktop restart,** `scripts/dev.sh start` is needed before the web UI answers.

## Changed files

All paths are relative to the repository; the addon is `addons/azk_dynamic_trial_balance/`.

**New:**

- `models/trial_balance_engine.py`:
  - the entry point `compute`;
  - the steps `_compute`, `_accounts_in_scope`, `_scope_domain`, `_add_movement`, `_add_opening`, `_add_carry_forward` and `_add_accounts_without_items`;
  - the rows: `_leaf_rows`, `_amounts`, `_is_zero_row` and `_hierarchy`;
  - the totals and filters: `_sum_amounts`, `_currency_totals` and `_filters`;
  - the helper `like_prefix_pattern`.
- `tests/test_engine_boundaries.py` (fixture TB-D) and `tests/test_engine_access.py`.
- `scripts/tb_engine_vs_native.py`.
- `docs/test_results.md`, `docs/handoffs/stage_08_en.md`, `docs/ai/stage_08.md`.

**Updated:**

- The addon's `__manifest__.py` (18.0.1.2.0) and `models/__init__.py`.
- `models/trial_balance_wizard.py`: `_compute_report`, and the entry-point message.
- `tests/common.py`: the TB-D constants and builder, and the engine helpers `engine_report`, `engine_rows`, `assertRowsEqual` and `assertEngineMatchesNative`.
- The engine tests in `tests/test_base_fixture.py`, `tests/test_native_conventions.py` and `tests/test_advanced_fixtures.py`, and `tests/__init__.py`.
- `docs/calculation_contract.md` (section 15), `docs/architecture.md` (4.10), `docs/assumptions.md` (D-50 to D-53), `docs/test_plan.md` (4.4), `docs/requirements_matrix.md`, `docs/STATE.md` and `docs/ai/README.md`.

## Comprehension questions

1. Why does the engine check the accounting read-only group itself, when every query already applies the record rules?
2. In TB-X's February report, which query puts January's revenue into the opening, and which one puts the 2025 revenue on Current Year Earnings?
3. Why must the totals never include group rows, and how does the engine make sure they don't?

## Next stage

Stage 09: the Preview, PDF and XLSX outputs, rendered from this engine's result.
