# Test results

Exact commands and results, newest stage first. Every result is PASS, FAIL, BLOCKED or NOT RUN. The commands run from `solution/` in Git Bash on the target edition `enterprise-20241208`: service `odoo-ee-20241208`, port 8071, the matched pair of [enterprise_transition.md](enterprise_transition.md). Full command logs are private, in `<kit-root>/runtime/logs/`. Earlier stages record their results in [STATE.md](STATE.md) and their handoffs.

## Stage 08 (2026-11-15): Trial Balance calculation engine

Code: `azk_dynamic_trial_balance` 18.0.1.2.0 on top of Stage 07 commit `cabfb75`.

### Automated tests

```text
scripts/dev.sh test azk_dynamic_trial_balance
```

Each run drops and recreates `azk_ee24_test`, installs the addon with its dependencies and demo data (about 90 modules), and runs the addon's tests. Free space on C: was sampled every 30 s.

| Run | Code | Result line | Warnings | Exit, time | Free space on C: |
|---|---|---|---|---|---|
| 1 | first engine code | "0 failed, 0 error(s) of 84 tests" | 0 | 0, 462 s | 48.3 GB, stable |
| 2 | plus a rounding test and logged query counts | "0 failed, 0 error(s) of 85 tests" | 0 | 0, 331 s | 48.4 to 47.9 GB |
| 3 | final code (only the manifest version differs from run 2) | "0 failed, 0 error(s) of 85 tests" | 0 | 0, 326 s | 48.2 to 48.4 GB |

**Result: PASS.** The 85 tests are 48 from Stage 07 and 37 new. By the areas the Stage 08 prompt lists:

1. **Base fixture, posted and with drafts** (`TestBaseFixture`):
   - `test_engine_posted_only`: Bank 1,000 + 500 - 300 = 1,200;
   - `test_engine_with_drafts`: Bank 1,000;
   - `test_engine_journal_filter_also_restricts_the_opening`.
2. **Boundaries** (`TestEngineBoundaries`, fixture TB-D):
   - `test_both_dates_count_and_neighbours_do_not`: the first and last days count, the day before is in the opening and the day after is excluded; the overdrawn Bank ends at 110 credit;
   - `test_drafts_join_but_cancelled_never_does`, `test_single_day_periods`, `test_empty_period`, `test_reversal_is_a_posted_mirror_entry`;
   - `test_amounts_are_rounded_to_the_company_currency`: 0.10 + 0.20 shows as 0.30.
3. **Prefixes and journals** (`TestBaseFixture`):
   - `test_engine_prefixes`: OR semantics, and overlapping prefixes count an account once;
   - `test_engine_prefixes_are_literal_and_case_sensitive`;
   - `test_engine_lists_every_account_without_skip_zero_balance`: every non-deprecated account, plus a deprecated one with amounts;
   - the journal test above.
4. **Zero activity** (`TestZeroActivityFixture`): `test_engine_skip_zero_balance_keeps_zero_net_activity` and `test_engine_without_skip_zero_balance_lists_untouched_accounts`.
5. **Currencies** (`TestCurrencyFixture`):
   - `test_engine_rows_per_transaction_currency`: USD 60 and EUR 50, never 110;
   - `test_engine_currency_rows_reconcile_with_account_rows`: signed balances and gross movements reconcile; the netted opening totals are 1,650 against 650 (D-49);
   - `test_engine_does_not_revalue_at_a_later_rate`.
6. **Analytic** (`TestAnalyticFixture`):
   - `test_engine_selects_whole_items`: A1 gives 1,200, not the proportional 800; A2 1,000; B1 200;
   - `test_engine_counts_each_item_once_without_a_filter`: 1,200, not 1,400 or 2,400.
7. **Hierarchy** (`TestHierarchyFixture`):
   - `test_engine_hierarchy_and_subtotals`: the order, levels 1 to 6, group sums and "(No Group)";
   - `test_engine_only_parents_at_each_level`: levels 1 to 5;
   - `test_engine_hierarchy_options_never_change_totals`.
8. **Access and tampering:**
   - `TestEngineAccess`: `test_users_without_accounting_read_access_are_refused` (an employee and a billing user), `test_tampered_options_are_refused` (14 tampered option sets, plus another company), `test_wizard_computes_with_its_owner_access_only`;
   - `TestMultiCompanyFixture`: `test_engine_refuses_a_company_the_user_may_not_use`, `test_engine_prefixes_never_reach_another_company`;
   - `TestRestrictedAccessFixture`: `test_engine_applies_record_rules`, `test_engine_restricted_items_stay_hidden_when_targeted`.
9. **Standard report comparisons:** the cases in the next section, with the cross-year fixture (`TestCrossYearConventions.test_engine_january_february_and_drafts`). The hand-calculated tests stay, so no test only compares two programs with each other.

**Query count** (`test_query_count_does_not_grow_with_accounts`, logged in runs 2 and 3):

| Options | 4 accounts with amounts | 24 accounts with amounts |
|---|---|---|
| Skip Zero Balance | 35 | 15 |
| Hierarchy and Subtotals, Skip Zero Balance | 16 | 16 |
| Show Amount Currency (all accounts listed) | 15 | 15 |

- The first call in the test runs with cold caches, hence its 35.
- After that, the count stays the same whatever the number of accounts.
- Wall-clock time on large data was not measured, and no large-scale performance is claimed.

### Comparisons with the standard Trial Balance

Our engine and `account_reports.trial_balance_report` were run with matching options:

- the same company, and only that company active;
- the same dates;
- Draft Entries equal to Include Unposted Entries;
- the same single journal or analytic account;
- the hierarchy off, except for TB-H.

For every account line, the Initial, period and End debit and credit, and the totals, are equal. Our report uses Skip Zero Balance in these comparisons, because the standard report lists only accounts with journal items. **All PASS** (run 3). Cases compared:

- **TB-BASE, January 2026:** posted; with drafts; the Bank journal only; the Misc journal only.
- **TB-X:** January (the fiscal-year start); February; February with drafts.
- **TB-D:** January, posted and with drafts; the single days 2026-01-01 and 2026-01-31.
- **TB-Z:** January.
- **TB-C:** January without currency rows. The standard report has no currency rows.
- **TB-A, March:** no filter; analytic A1; A2; B1.
- **TB-M, January:** company 1; company 2.
- **TB-R, January:** as the restricted reader; as the accountant.
- **TB-H, January, hierarchy on:** account lines, group lines, "(No Group)" and group depths.

**Not compared,** because the standard report has no such option:

- currency rows and the Amount Currency column;
- Skip Zero Balance, and the listing of accounts without journal items;
- Hierarchy Only Parents and the level limit;
- account prefixes.

These are tested against the hand-calculated constants only.

**Not covered by any test:** custom fiscal years, branches and period comparisons.

### The standard report on the development database's own data

This check is not hand-calculated: it compares two programs on demo data.

```text
scripts/dev.sh shell azk_ee24 < scripts/tb_engine_vs_native.py
```

- **Setup:** user admin (not the superuser); company YourCompany (USD); today 2026-11-15; read-only, rolled back at the end.
- **Result: PASS, 6 of 6 cases match** per account and in total:
  - this month, posted, and with drafts (8 account lines each);
  - fiscal year to date, posted, and with drafts (8 lines each);
  - previous fiscal year, posted (3 lines);
  - fiscal year to date with the sales journal only (3 lines).
- One all-zero standard line was set aside in four cases.
- **Limit:** the demo data has no draft items in these periods, so the "with drafts" cases equal the posted ones there.

### Development database and browser

- **`scripts/dev.sh update azk_dynamic_trial_balance` on `azk_ee24`:** PASS twice (72 s, then 78 s on the final version), 0 warnings. Version 18.0.1.2.0 is installed.
- **`python scripts/tb_wizard_smoke_check.py OUTPUT_DIR`,** with `PM_UI_LOGIN` and `PM_UI_PASSWORD` set:
  - The first attempt **failed** at the login page: the web server was not running. Docker had stopped both containers at 06:20:26 UTC, before this stage's work; Docker's engine now reports version 29.9.2. `scripts/dev.sh update` restarts the web server only if it runs.
  - After `scripts/dev.sh start`, the rerun **passed 8 of 8**, with the new message "The Preview is not available yet. Your options are valid, but the report outputs are still being built."

### NOT RUN

- The Preview, PDF and XLSX outputs: Stage 09.
- A browser check of anything but the wizard dialog.
