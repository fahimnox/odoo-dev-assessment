# Test results

Exact commands and results, newest stage first. Every result is PASS, FAIL, BLOCKED or NOT RUN. The commands run from `solution/` in Git Bash on the target edition `enterprise-20241208`: service `odoo-ee-20241208`, port 8071, the matched pair of [enterprise_transition.md](enterprise_transition.md). Full command logs are private, in `<kit-root>/runtime/logs/`. Earlier stages record their results in [STATE.md](STATE.md) and their handoffs.

## Stage 09 (2026-11-15): Trial Balance outputs (Preview, PDF, XLSX)

Code: `azk_dynamic_trial_balance` 18.0.1.3.0 on top of Stage 08 commit `845accb`. Memory was tight on the host during this stage (other applications used most of the 15.9 GB). Free RAM was therefore sampled with free space on C:, and the browser checks ran under a guard that would stop them below 500 MB of commit headroom (it never triggered).

### Automated tests

```text
scripts/dev.sh test azk_dynamic_trial_balance
```

| Run | Code | Result line | Warnings | Exit, time | C: free, RAM free |
|---|---|---|---|---|---|
| 1 | first Stage 09 code: an `HttpCase` class and real wkhtmltopdf in unit tests | none: stopped | 1 | none | 48 GB |
| 2 | wkhtmltopdf replaced by a capturing stub, no `HttpCase`, demo creation after loading | "0 failed, 0 error(s) of 101 tests" | 0 | 0, 419 s | 48.4 GB; 2.0 to 2.7 GB |
| 3 | plus the demo company's country | none: stopped by the agent while installing modules, superseded by run 4 | - | 130, 176 s | 48.0 GB |
| 4 | final code: plus bold group rows, the rounding unit in the PDF, a regression test | "0 failed, 0 error(s) of 102 tests" | 0 | 0, 438 s | 48.0 GB; 0.9 to 1.7 GB |

**Result: PASS** (run 4, final code; 102 post-tests in 189.30 s). The 102 tests are the 85 of Stage 08 and 17 new. The documentation and the browser scripts changed after run 4; the module did not.

- **Run 1 details** (log notes kept privately):
  - The demo data logged "Incorrect usage of try_loading without a fully loaded registry". Fixed: the creation now waits for `_register_hook`, as the `account` module does for its own first chart.
  - The `HttpCase` class made Odoo build every asset bundle before the post-install tests (about 13 minutes).
  - The first real PDF render in a unit test then made no progress (a `wkhtmltopdf` process with no CPU use for over 1 min 44 s).
  - At about 08:41 UTC the CLI stopped the background command because the machine was critically low on memory (1.0 GB of RAM free). The test container kept running, stuck; the agent stopped it with `docker stop`.
  - Up to that point the Stage 07 and 08 classes and `TestDemoData` had run without a failure, but the run has no summary, so it counts as neither PASS nor FAIL.
- **Fixes, following Odoo's own `account_reports` tests:**
  - unit tests replace `_run_wkhtmltopdf` with a stub that keeps the HTML documents, and the tests read those (they are exactly what the PDF prints);
  - the download route and real PDFs are checked on the running server instead (below).

New tests by area:

1. **The three outputs against the engine** (`test_report_outputs.py`, `TestReportOutputs`, 11 tests, on the installed demo company):
   - for eight option sets (posted only, drafts, hierarchy, parents only, amount currency, analytic, zero filtering, empty result), the preview lines equal the engine rows, the XLSX cells equal the printed lines, and every PDF row prints exactly the name and the formatted cells of one printed line (`test_outputs_follow_the_engine_for_each_option_set`);
   - Bank 1,200 posted only and 1,000 with drafts in all three outputs (`test_bank_in_all_three_outputs`);
   - per-currency rows and totals, USD 60 and EUR 50, never 110 (`test_amount_currency_rows_and_totals`);
   - the PDF's company, period, options, column titles and "[Draft]" (`test_pdf_states_company_period_options_and_columns`), its table header in `thead` with the group widths (`test_pdf_table_header_repeats_on_every_page`), and the rounding unit (`test_rounding_unit_is_printed_and_xlsx_keeps_exact_numbers`);
   - the XLSX metadata, number formats, frozen header and the absence of formulas (`test_xlsx_cells_metadata_and_frozen_header`);
   - exports follow the preview's search and folded groups;
   - the preview's columns, filter component and messages, and the wizard's options round trip.
2. **Access and tampering** (`test_report_access.py`, `TestReportAccess`, 3 tests, on TB-BASE):
   - an accounting reader previews and exports;
   - employees and billing users get AccessError;
   - tampered options are refused on the preview and both exports: another company's journal, an unknown key, a wrongly typed value, a non-code prefix, a non-dictionary, another report, and an unauthorized company, also through the company list that the download route turns into the active companies;
   - no tampered export reached the PDF converter.
3. **Demo data** (`test_demo_data.py`, `TestDemoData`, 3 tests): the demo company is Egyptian, in EGP, with the generic chart; it has 13 posted, 2 draft and 1 cancelled entries, EGP, USD and EUR items, analytic distributions and groups 1 > 10 > 101 > 1014 > 10140 above Bank; the engine gives Bank 1,200 and 1,000; a second call of the demo function creates nothing.
4. **Changed:** `test_wizard.py` (the buttons return the report and download actions with the wizard's options) and `test_engine_access.py` (another user's wizard cannot be previewed or exported).

### Demo data and upgrades

Counts from `scripts/dev.sh shell DB < scripts/tb_demo_data_counts.py` (read-only, rolled back). Every count below was the same each time: demo company id 2, EGP; 16 demo entries (13 posted, 2 draft, 1 cancelled); 32 journal items; 10 account groups; 2 analytic plans; 3 analytic accounts; 2 currency rates; 7 journals.

- **A finding first:** the first `scripts/dev.sh update azk_dynamic_trial_balance` on `azk_ee24` (exit 0, 71 s, 0 warnings) did not create the demo company. Odoo loads demo files as noupdate data, and `<function>` tags of noupdate files run only when a module is installed (pinned source: `load_data` in `odoo/modules/loading.py`, `_tag_function` in `odoo/tools/convert.py`). `azk_ee24` had the module since Stage 07. The comments that claimed otherwise were corrected.
- **Install, then upgrade** (`azk_ee24_test`, freshly installed by the final test run): counts after the install; `scripts/dev.sh update azk_dynamic_trial_balance azk_ee24_test` exit 0, 62 s, 0 warnings; the same counts. Country EG, fiscal country US. The same check on run 2's install gave the same counts too (upgrade exit 0, 68 s).
- **`azk_ee24`:**
  - the demo function was called once from an Odoo shell, as install would have done (`_create_demo_data()` returned True; 0 warnings);
  - the company's country was then set to Egypt, the value a fresh install now gives;
  - three upgrades (exit 0 in 70, 71 and 65 s, 0 warnings each) left every count unchanged.

**Result: PASS:** no upgrade duplicated a demo record.

### Browser and server checks on `azk_ee24` (headless Chrome)

```text
PM_UI_LOGIN=... PM_UI_PASSWORD=... python scripts/tb_preview_smoke_check.py OUTPUT_DIR
PM_UI_LOGIN=... PM_UI_PASSWORD=... python scripts/tb_wizard_smoke_check.py OUTPUT_DIR
```

(Run with a private virtual environment that has websocket-client, openpyxl and PyMuPDF, outside the repository.)

- **`tb_preview_smoke_check.py`:**
  - Run 1: 19 of 20. The FAIL was the check itself: it expected a refused download to answer with an error status, but the standard route answers HTTP 200 with a JSON error body. The check now reads the error.
  - Run 2: 20 of 20.
  - Run 3, on the final code: **20 of 20, PASS**:
    - Preview: Bank cells 1,000.00 / 0.00 / 1,000.00 / 500.00 / 300.00 / 200.00 / 1,200.00 / 0.00 / 1,200.00;
    - Draft Entries: Bank ends at 1,000.00;
    - search "bank": only "101401 Bank" visible;
    - hierarchy: 11 group rows, and folding 10140 hides Bank;
    - downloads: PDF and "Download Excel" (gear menu); the XLSX equals the engine (19 rows with Total), numeric, formatted, frozen at C17;
    - a 1-page PDF, and a 3-page PDF with the header printed 3 times;
    - empty state: "No journal items match these options. ...";
    - the route refused a tampered prefix with `odoo.exceptions.ValidationError` and gave only the login page without a session;
    - all eight option sets through the real route: the XLSX equals the engine and every row is in the real PDF text (for example posted only 49 leaf rows, 2 pages; hierarchy 61 XLSX rows, 3 pages; empty result 1 XLSX row);
    - no JavaScript error.
    Lowest commit headroom: 1.43 GB.
- **`tb_wizard_smoke_check.py`, updated for Stage 09** (no more "not connected yet" notice; Preview opens the report), on the final code: **7 of 7, PASS**.
- **A style probe** (scratch script, not committed) found the group rows at weight 600: our stylesheet overrode the standard bold. Fixed, then seen bold in run 3.
- **Visual inspection** of the real PDFs rendered to PNG (the 1-page, the 3-page and the amount-currency PDF):
  - landscape A4, readable, no clipping;
  - the company block with the report company (Egypt), the options block, the column groups, bold groups, muted zeros, balanced totals, "page / pages" in the footer;
  - the column header on every page;
  - two rows on pages 2 and 3 of the 3-page PDF have slightly taller gaps (no extra rows: the unit tests show one PDF row per printed line).
  - Before the country fix, the address showed "United States" (the generic chart's fiscal country).
- Samples: [samples/](samples/); screenshots and PDF renders: [screenshots/](screenshots/) (`stage09_*.png`).

### NOT RUN

- The analytic dropdown in the browser. Analytic fields need Odoo's Analytic Accounting setting, which is off on `azk_ee24`, so the dropdown is hidden there. The analytic option set passed in the unit tests and through the real route.
- A real wkhtmltopdf in unit tests: replaced by the stub by design (above).
- Custom fiscal years and branch companies: Stage 10 (D-60).
- A browser check by the user.

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
