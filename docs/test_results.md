# Test results

Exact commands and results, newest stage first. Every result is PASS, FAIL, BLOCKED or NOT RUN. The commands run from `solution/` in Git Bash on the target edition `enterprise-20241208`: service `odoo-ee-20241208`, port 8071, the matched pair of [enterprise_transition.md](enterprise_transition.md). Full command logs are private, in `<kit-root>/runtime/logs/`. Earlier stages record their results in [STATE.md](STATE.md) and their handoffs.

## Stage 11 (2026-11-16): clean acceptance

The full record, with every command, count and log name, is [acceptance_results.md](acceptance_results.md). All of it ran from `git archive` exports outside the repository, in a separate Compose project with empty volumes (port 8073). The addon code is that of Stage 10 (`e54214b`); Stage 11 changed only `scripts/dev.sh`, `.env.example`, documentation and acceptance scripts.

- **FAIL, then fixed:** the first documented command in a fresh checkout. In the export of `e54214b`, `scripts/dev.sh setup` exited with 255 (AC-01).
- **PASS after the fix** (export of `3b92f98`):
  - quick start steps 1 to 3;
  - demo data at install;
  - each addon alone, then updated (TP-G-01);
  - both addons without demo data;
  - the upgrade from Stage 09 with equal fingerprints.
- **PASS:** `scripts/dev.sh test`, "0 failed, 0 error(s) of 261 tests": 147 Partner Monitor and 114 Trial Balance, as in Stage 10. No skipped test, warning or import error.
- **PASS:** `scripts/restart_check.sh`, 12 of 12.
- **PASS:** the browser checks on the fresh database: dashboard 7 of 7, Trial Balance wizard 7 of 7, preview and downloads 20 of 20, the Partner Monitor demonstration 7 of 7 (on run 3; runs 1 and 2 failed on harness timing, AC-06).
- **PASS:** `scripts/tb_engine_vs_native.py`, 6 of 6. `scripts/acceptance_access_check.py`, 24 of 24.
- **PASS:** the Partner Monitor demonstration: a bounded LIVE sample (7 requests in all), a SIMULATED outage, notes and recovery. The first notification went to the default recipient because the demo script's settings phase lacked a commit (AC-05, fixed and rerun).
- **NOT RUN:**
  - the user's manual browser check (TP-G-05);
  - a full live crawl (on purpose);
  - the Partner Monitor tests on the Community baseline (TP-G-03, optional; only its install with demo data ran).

## Stage 10 (2026-11-15): engineering review

Code: `azk_odoo_partner_monitor` 18.0.1.5.0 and `azk_dynamic_trial_balance` 18.0.1.3.0 (Python changes only), on top of Stage 09 commit `564b71b`. Findings and their verification: [review_findings.md](review_findings.md). The heavy checks ran one at a time, with free RAM sampled (about 1.9 to 2.6 GB free); C: had 40 to 41 GB free.

### Automated tests

```text
scripts/dev.sh test azk_odoo_partner_monitor
scripts/dev.sh test azk_dynamic_trial_balance
scripts/dev.sh test azk_dynamic_trial_balance /account_reports:TestTrialBalanceReport,/account_reports:TestAccountReportAnnotationsExport
```

- **Partner Monitor:**
  - run 1 (15:06 to 15:11 UTC, fresh `azk_ee24_test`): PASS, "0 failed, 0 error(s) of 145 tests", 0 warning lines, exit 0 (129 earlier and 16 new tests);
  - final run, on the final code: PASS, "0 failed, 0 error(s) of 147 tests" (16:30 to 16:32 UTC, fresh `azk_ee24_test`), 0 warning lines, exit 0 (129 earlier and 18 new tests).
- **Trial Balance:**
  - run 1 (15:32 to 15:39 UTC): FAIL, "1 failed, 0 error(s) of 113 tests": `test_a_branch_user_sees_the_branch_only` (no Current Year Earnings row for a branch-only user; RF-06);
  - run 2 (15:55 to 16:01 UTC): FAIL, "1 failed, 0 error(s) of 114 tests". The same test still failed: the first fix (a narrow `sudo()`) did not address the cause. There were also 3 warning lines from the new demo test, which recreated the demo's analytic plans;
  - run 3 (16:07 to 16:13 UTC), final code: PASS, "0 failed, 0 error(s) of 114 tests", 0 warning lines, exit 0, 114 post-tests in 178.6 s (102 earlier and 12 new tests).
- **The vendor's own tests with our addon installed:** PASS, "0 failed, 0 error(s) of 11 tests" (16:26 to 16:29 UTC, fresh `azk_ee24_test` with `azk_dynamic_trial_balance` installed, 0 warning lines): the 8 `TestTrialBalanceReport` tests, including `test_trial_balance_comparisons`, and the 3 `TestAccountReportAnnotationsExport` tests, which export the standard reports to XLSX.

### The bounded live check through the module (TP-PM-21)

```text
scripts/dev.sh shell azk_ee24_test < scripts/pm_live_check.py
```

- **Run 1 (15:14 UTC): FAIL.** robots.txt: "Remote end closed connection without response". Then seven single diagnostic requests (RF-02).
- **Run 2 (15:22 UTC): PASS for what ran.** 3 page requests; RF-03 found.
- **Run 3 (15:25 UTC): PASS.**
  - robots.txt HTTP 200, 1,627 bytes, 56 rules, both planned URLs allowed.
  - Batch 1: 3.50 s, 1 unit (the country list: 170 countries, complete), 170 remaining.
  - Batch 2: 6.43 s, 2 units: Andorra (2 of 2, complete, matched) and BDR GROUP SLU's page (17 of 17 references stored). That unit said "mismatch", which led to RF-04.
  - Requests:
    - `/partners?country_all=1`: 200, 381,670 bytes, 2.00 s;
    - `/partners/country/1`: 301, 0.12 s;
    - `/partners/country/andorra-1`: 200, 322,042 bytes, 0.47 s;
    - `/partners/bdr-group-slu-22015187`: 200, 87,050 bytes, 0.23 s.
- **Run 4 (16:32 UTC, final code): PASS.**
  - robots.txt HTTP 200, 1,627 bytes, the same 56 rules.
  - Batch 1: 2.69 s, the country list (170 countries, complete), 170 remaining.
  - Batch 2: 6.80 s, Andorra (2 of 2, complete, matched) and BDR GROUP SLU's page: "17 of 17 references, matched, 17 added" (RF-04 fixed).
  - 4 page requests, each allowed by robots.txt: the country list (200, 381,630 bytes, 2.06 s), `/partners/country/1` (301, 0.12 s), Andorra (200, 322,042 bytes, 0.52 s) and BDR GROUP SLU (200, 87,050 bytes, 0.44 s).
  - No error row. Rolled back: no unit of the run left.
- Every request: [live_site_notes.md](live_site_notes.md).

### Browser checks

**Analytic selector, as a read-only accountant, on a disposable server (RF-15)**

```text
# with TB_RO_PASSWORD set to a random value, never printed:
docker compose run --rm -T -e TB_RO_PASSWORD odoo-ee-20241208 odoo shell --database=azk_ee24_test --no-http < scripts/tb_analytic_setup.py
docker compose run -d --rm --name azk-tb-disposable-8072 -p 127.0.0.1:8072:8072 odoo-ee-20241208     odoo --http-port=8072 --database=azk_ee24_test --db-filter='^azk_ee24_test$' --max-cron-threads=0
PM_UI_URL=http://127.0.0.1:8072 PM_UI_LOGIN=tb_readonly PM_UI_PASSWORD=... python scripts/tb_analytic_smoke_check.py OUTPUT_DIR
```

- **Setup** (`azk_ee24_test`, committed; the database was recreated afterwards): Analytic Accounting on for internal users; `web.base.url` set to http://127.0.0.1:8072; user `tb_readonly` with only `account.group_account_readonly` (no accounting user rights), in the demo company only.
- **Run 1: NOT RUN.** The memory guard's path reached the host's Python in a form it could not open; no check ran. The setup and the server worked.
- **Run 2: PASS, 6 of 6:**
  - the wizard showed the Analytic Accounts field; choosing "Sales Department" and Preview opened the report with that account selected. 1 account row in March 2026 (7 without the filter), equal to the engine;
  - the preview's dropdown, "All analytic accounts": recalculated, equal to the engine;
  - the dropdown, "Sales Department" again: recalculated, equal to the engine;
  - PDF and Download Excel with the filter: the XLSX equalled the engine (2 rows with the Total), and the 1-page PDF stated "Analytic Accounts: Sales Department";
  - tampered downloads were refused: another company in our options gave "AccessError: You are not allowed to report on this company."; another company in the company list gave "AccessError: Access to unauthorized or invalid companies.";
  - no JavaScript error.
- **Server log:** 0 warning or error lines. The first `/odoo` page took 72.5 s, while the fresh server built its asset bundles. The lowest commit headroom was 3,355 MB.
- Screenshots: `screenshots/stage10_analytic_*.png` (wizard, filtered preview, unfiltered preview, PDF page).

**`azk_ee24` after the upgrade to the Stage 10 code** (`scripts/dev.sh update azk_odoo_partner_monitor,azk_dynamic_trial_balance`, 16:40 to 16:42 UTC)

- **Update: PASS.** Exit 0, 0 warning and 0 error lines; versions 18.0.1.5.0 (Partner Monitor) and 18.0.1.3.0 (Trial Balance); downloads paused (D-64).
- **One call of the worker job's entry point, with any HTTP request refused by a patch: PASS.**
  - Nothing processed and nothing sent: 1 unit remaining, waiting.
  - Run 1 now waits with "website downloads are paused (Settings > Partner Monitor > Pause Website Downloads)" and still has one note.
  - Still 0 partners from the website.
- **`scripts/ui_smoke_check.py`** (headless Chrome, admin): **PASS, 7 of 7**, the same checks as Stage 06. The dashboard shows the paused banner (`screenshots/stage10_dashboard_downloads_paused.png`).
- **`scripts/tb_preview_smoke_check.py`** (headless Chrome, admin): **PASS, 20 of 20**, the same checks as Stage 09:
  - Bank 1,200.00, then 1,000.00 with Draft Entries;
  - search and folding;
  - both downloads, and a 1-page and a 3-page PDF;
  - the empty state;
  - the route refusing tampered options and giving no file without a session;
  - all eight option sets through the route, equal to the engine.
- **Lowest commit headroom:** 3,824 MB and 3,451 MB.
- **Server log since the upgrade:** 0 warning or error lines.

### Installation without demo data, and the documented demo call

```text
scripts/dev.sh clean-install azk_odoo_partner_monitor,azk_dynamic_trial_balance --without-demo
scripts/dev.sh shell azk_ee24_clean < (a read-only state check)
docker compose run --rm -T -e PHASE=call odoo-ee-20241208 odoo shell --database=azk_ee24_clean --no-http < (the same check, then the call)
scripts/dev.sh shell azk_ee24_clean < scripts/tb_demo_data_counts.py
```

- **Install without demo data (16:35 to 16:38 UTC): PASS.** Exit 0, 0 warning and 0 error lines, 2 min 39 s.
  - Both addons and `account_reports` installed with demo off.
  - `l10n_eg` not installed; one company, "My Company".
  - No Trial Balance demo company, while the report record and its menu exist.
  - No Partner Monitor country, partner or run; its four jobs active; downloads not paused (the default).
  - No server serves this database, so no job ran.
- **The documented one-time demo call (D-59), in a real Odoo shell, committed: PASS.**
  - The first call created the company: "AZK Trial Balance Demo (EGP)", country EG, generic chart, EGP.
  - `l10n_eg` stayed uninstalled: the RF-07 fix, outside test mode.
  - A second call created nothing.
  - The counts equal the install-time demo of Stage 09: 16 entries (13 posted, 2 draft, 1 cancelled), 32 journal items, 10 account groups, 2 analytic plans, 3 analytic accounts, 2 currency rates, 7 journals.

### Benchmarks

**Trial Balance** (`scripts/tb_benchmark.py`, 16:14 to 16:18 UTC, rolled back: 0 benchmark companies left)

- **Dataset (seeded, reproducible):**
  - a new company with Odoo's generic chart plus 100 extra accounts, 146 accounts in all, with no account groups;
  - balanced two-line entries in one miscellaneous journal, dated 2025-01-01 to 2026-03-31, about 10% left in draft;
  - two sizes: 1,000 entries (2,000 journal items), then 5,000 entries (10,000 items).
- **Environment:** the Docker setup of this repository on Windows 11 (Intel Core i7-8650U, 4 cores, 15.9 GB RAM, about 2.5 GB free), PostgreSQL 16, one Odoo shell process, the admin user, report period January to March 2026.
- **Measured:** the median of 3 runs with the ORM cache cleared. The PDF timing stops before wkhtmltopdf: it covers the HTML that would be printed. Results by size, 1,000 entries then 5,000 entries:
  - **Engine `compute()`:**
    - all accounts, posted only: 0.033 s, then 0.061 s; 15 queries at both sizes;
    - drafts, hierarchy, skip zero: 0.050 s, then 0.070 s; 16 queries at both sizes.
  - **Preview lines (`_get_lines`):** 0.17 to 0.25 s, then 0.21 to 0.29 s; 18 to 19 queries.
  - **XLSX export:** 0.09 to 0.12 s, then 0.12 to 0.17 s; 40 to 41 queries; 16 to 18 KB.
  - **PDF export without wkhtmltopdf:** 0.54 to 0.66 s, then 0.58 to 0.84 s; 57 to 58 queries; about 220 KB of HTML. The very first PDF build took 11.6 s (cold templates).
  - **Rows:** 149 lines (all accounts), or 146 to 147 lines (skip zero), all balanced.
- **What it shows:**
  - The query counts do not change when the journal items grow fivefold: there is no per-account or per-item query loop.
  - The time grows slowly, because the totals are computed by PostgreSQL in three grouped queries.
- **Limits:**
  - one company and one journal;
  - no account groups, so the hierarchy only adds "(No Group)";
  - a laptop under memory pressure;
  - the wkhtmltopdf conversion itself not timed.
  - This is no capacity figure for production.

**Partner Monitor** (`scripts/pm_benchmark.py`, 16:32 to 16:33 UTC, rolled back: 0 benchmark countries left)

- **Dataset (seeded, no network):** synthetic parse results built with the module's own dataclasses, 20 cards per page as on the live site:
  - one country listing of 100 cards (5 pages), then one of 1,000 cards (50 pages);
  - one partner page with 135 references, RoayaTec's size;
  - the dashboard over every partner in the database (1,150, demo partners included).
- **Measured:** as the cron's superuser would run it (the dashboard with `sudo`, so record rules were not timed); the median of 3 runs where a step can repeat.
- **Results:**
  - **Listing, first read** (partners and history created): 100 cards 0.44 s with 704 queries; 1,000 cards 4.86 s with 7,002 queries. That is 7 queries and about 4.5 to 5 ms per card.
  - **The same pages again** (nothing new): 100 cards 0.21 s with 402 queries; 1,000 cards 1.91 s with 4,002 queries. That is 4 queries and about 2 ms per card.
  - **A partner page with 135 references:** 0.030 s with 7 queries the first time (the references are created in one batch), 0.007 s with 4 queries again.
  - **Dashboard data:** 0.061 to 0.081 s, 21 queries (34 on the first, cold call), with or without a status filter.
- **What it shows:**
  - Storing a listing costs a constant few queries per card: a per-card loop by design. Each card has its own savepoint, so one bad card cannot stop the others (RF-11).
  - The whole directory (4,517 partners on 2026-11-08) would take about 32,000 queries and some 20 seconds of database work on a first sync. That is small next to the downloads, at 3 seconds or more per request (RF-12).
  - The references and the dashboard use grouped or batched queries.
- **Limits:** synthetic cards (no parsing time), one process, and the same laptop. This is no capacity figure for production.

### Restart check (TP-PM-15), rerun

```text
scripts/restart_check.sh
```

PASS, 12 of 12 (`scripts/restart_check.sh`, 16:33 to 16:35 UTC, on `azk_ee24_test` right after the final Partner Monitor run). The worker's container was killed with SIGKILL during its second batch, at 16:34:28 UTC (exit status 137). After the restart in a new container, only the interrupted batch's units ran again (Anguilla's listing and RoayaTec's page), then DEVONEERS' page. There was no duplicate history row, reference or note, no email was queued, and no unit was left pending. The worker still uses the saved pages there (`FixtureSite`), so the check never reaches the website.

### NOT RUN

- A full live sync of the directory (about 330 listing pages and, the first time, about 4,500 partner pages): not requested, and paused on `azk_ee24` on purpose (D-64).
- The live check of an empty country through the module: the bounded check covered one country with partners. Anguilla's fallback page stays covered by the live-derived fixture.
- A browser check by the user.

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
