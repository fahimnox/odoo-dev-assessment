# Engineering review findings (Stage 10)

_Review of both addons against the assessment PDF and the actual code, on 2026-11-15, edition `enterprise-20241208` (port 8071). Commands and full results: [test_results.md](test_results.md). Handoff: [handoffs/stage_10_en.md](handoffs/stage_10_en.md)._

## How to read this

- **Severity.**
  - High: a requirement cannot work, or results are wrong for everyone.
  - Medium: results are wrong, or work is lost or wasted, in a supported case.
  - Low: a narrow edge case, a documentation error, or a process problem.
  - Info: checked, nothing wrong, recorded as evidence.
- **Status.**
  - FIXED, VERIFIED: the code changed and a test or check that failed before (or could not run before) now passes.
  - DOCUMENTED: a limit kept on purpose, with its evidence.
  - OPEN: not resolved; still visible here and in [requirements_matrix.md](requirements_matrix.md).
- No finding is marked resolved only because code changed. Each FIXED finding names the check that proves it.

## Summary

15 findings. Seven defects were fixed and verified: two High, four Medium and one Low. One documentation error was fixed. Six results are documented with evidence, and one item stays open by plan.

- **RF-01 (High), FIXED, VERIFIED:** no page download, so no live sync (Stage 04 PARTIAL).
- **RF-02 (High), FIXED, VERIFIED:** `Accept-Encoding: gzip, deflate` made the website close every connection.
- **RF-03 (Medium), FIXED, VERIFIED:** work queued during a batch waited for the next scheduler interval.
- **RF-04 (Medium), FIXED, VERIFIED:** an empty reference card caused a false reference mismatch.
- **RF-05 (Medium), FIXED, VERIFIED:** connecting the download would have started an unrequested full crawl on `azk_ee24`.
- **RF-06 (Medium), FIXED, VERIFIED:** branch-only users got an incomplete Trial Balance.
- **RF-07 (Low), FIXED, VERIFIED:** the documented demo shell call would install the Egyptian localization.
- **RF-08 (Info), DOCUMENTED:** custom fiscal years.
- **RF-09 (Info), DOCUMENTED:** branch companies.
- **RF-10 (Info), DOCUMENTED:** our report extensions leave the standard reports unchanged.
- **RF-11 (Info), DOCUMENTED:** Partner Monitor storage cost grows with the number of cards.
- **RF-12 (Low), DOCUMENTED:** the longest country unit leaves little room under the prefork time limit.
- **RF-13 (Low), FIXED:** stale requirement rows (documentation).
- **RF-14 (Info), OPEN:** README and publication items, by plan (Stages 12 and 15).
- **RF-15 (Info), DOCUMENTED:** analytic accounting in the browser.

## The three most important fixes

1. **The website closed every download (RF-02).** The `requests` library offers `Accept-Encoding: gzip, deflate` by default. For that header, www.odoo.com kept an HTTP/1.1 connection open about 15 seconds and then closed it without any answer; with `gzip` alone it answers at once. Every page request of every sync would have failed, been retried and then recorded as a failed unit. The design held (a failure never became an empty page and nothing was deleted), but no sync could ever have succeeded. The mocked tests could not show this: only the live check did. The client now asks for gzip only (`services/http_client.py`, `REQUEST_HEADERS`).
2. **Branch-only users got an incomplete Trial Balance (RF-06).** Odoo 18 lets a user access a branch without its root company. The default order of `account.account` in this build ("code, placeholder_code") joins each account to its first company among the user's own companies. For such a user that join drops every account the branch shares with its root, so `search()` found none of them, although the record rules let the user count and read them. The report then:
   - lost the Current Year Earnings row and showed a false "no Current Year Earnings account" warning;
   - listed no account without items;
   - matched no account prefix.

   The amounts it did show were right, which made the gap easy to miss. The engine now searches the report company's chart as the user, ordered by id (`_chart_accounts` in `models/trial_balance_engine.py`). No `sudo()` was needed. The standard Trial Balance of this build shows such a user no line at all.
3. **A complete reference list looked incomplete (RF-04).** A live partner page carried an empty card among its references (18 cards for "References - 17"). The parser read it as a reference without a name, a problem that makes the list incomplete. The partner was then flagged for re-scraping, re-read up to 5 times, and finally shown as "Retries Exhausted", for a page that was in fact complete. Empty cards are now skipped; the count comparison still decides completeness, so a hidden reference would still show as a mismatch (`parse_partner_page` in `services/parsers.py`).

## Findings

### RF-01 (High): no page download, so no live sync (Stage 04 PARTIAL)

- **Location:** `models/worker.py`, `PartnerMonitorWorker._get_page_source()`, which returned None; `services/http_client.py` did not exist.
- **Evidence:** Stage 04 and 05 handoffs. `azk_ee24` held run 1 (manual, 2026-11-10) waiting with "no page source is available". Requirements P-02, P-03.1, P-03.2, P-04 and P-22 had no live evidence.
- **Fix:**
  - `services/http_client.py`: `PartnersHttpClient` (the `fetch(url)` of `services/reader.py`), `RequestPacer`, and the `FetchError` family: `FetchTimeout`, `FetchConnectionError`, `HttpStatusError`, `RateLimitedError`, `LoginPageError`, `UnexpectedResponseError`.
  - Bounds: 5 s to connect, 20 s between bytes, 30 s per page; at most 3 MB per page; at least 3 s between two requests of the process, redirects included; at most 3 tries of one URL, and only for timeouts, connection errors, cut-off pages and HTTP 502, 503 and 504.
  - Redirects are followed one by one, at most 5. Each target is checked against the URL scope and robots rules (`urls.fetch_allowed`) before it is requested.
  - HTTP errors, login pages (a redirect to `/web/login` or a password field) and rate limits (HTTP 429, a 503 with Retry-After, a "Too Many Requests" page) all raise: never an empty page.
  - A rate limit pauses every client of the process, for the Retry-After delay but at least 10 minutes and at most 24 hours. The worker then stops the batch and reports no progress, so the scheduler does not start another batch at once.
  - `_get_page_source()` returns a new client per batch, unless downloads are paused (RF-05).
- **Verification:**
  - `tests/test_http_client.py`: 13 client tests and 3 worker tests, with mocked responses. They cover a success, redirects, disallowed URLs and redirect targets, endless redirects, login pages, three kinds of rate limit, HTTP errors (only 502, 503 and 504 retried), timeouts, cut-off pages, slow pages, oversized, empty and non-HTML pages, the charset, spacing across clients, and whole units through the client: stored, failed with the data kept, or stopped by a rate limit with the queue kept.
  - Results: the final Partner Monitor run PASSED, "0 failed, 0 error(s) of 147 tests", 0 warning lines (run 1, before the live-check fixes: 145 of 145).
  - Live check through the worker: run 4 PASS on the final code: the country list (170 countries, complete), Andorra (2 of 2, complete, matched) and BDR GROUP SLU's page (17 of 17 references, matched), with 4 page requests, every one allowed by robots.txt. Run 3 read the same pages but called the reference list a mismatch, which led to RF-04.
- **Status:** FIXED, VERIFIED. Stage 04 is DONE.

### RF-02 (High): `Accept-Encoding: gzip, deflate` made the website close every connection

- **Location:** `services/http_client.py` (the first version relied on the `requests` default headers).
- **Evidence:** live check run 1, 15:14 UTC: the first request (robots.txt) ended with "Remote end closed connection without response". Then seven single requests to robots.txt, about 5 seconds apart, isolated the cause:
  - the host's curl, same User-Agent: HTTP 200, 1,627 bytes;
  - curl inside the Odoo container: HTTP 200;
  - Python `requests` inside the container: no answer, connection closed after 15.6 s;
  - curl over HTTP/1.1: HTTP 200;
  - curl over HTTP/1.1 with the `requests` default headers: "Empty reply from server" after 15.5 s;
  - curl over HTTP/1.1 with only `Accept-Encoding: gzip, deflate`: "Empty reply from server" after 16.8 s;
  - curl over HTTP/1.1 with only `Accept-Encoding: gzip`: HTTP 200, 590 bytes, 1.07 s.
- **Fix:** `REQUEST_HEADERS` sends `Accept-Encoding: gzip`.
- **Verification:** a regression assertion in `test_a_page_comes_back_with_its_final_url`; live check runs 2, 3 and 4 downloaded every page (below).
- **Status:** FIXED, VERIFIED.

### RF-03 (Medium): work queued during a batch waited for the next scheduler interval

- **Location:** `models/work_item.py`, `_enqueue()`; `models/worker.py`, `_unit_country_list()` and `_unit_country_partners()`.
- **Evidence:** live check run 2. A batch fixes its moment when it starts. Units queued seconds later (the 170 country units of the country list, the partner pages of a country) got the current time as their due time: they could not be claimed in that batch and were not counted as remaining. Batch 1 reported "remaining 0" with 170 units queued, so the scheduler would have ended its loop and waited up to the 10-minute interval at each step. In batch 2, Andorra's partner pages could not run.
- **Fix:** `_enqueue(..., now=now)`: work queued by a unit is due at the batch's moment.
- **Verification:**
  - Regression test `test_units_queued_by_a_unit_are_due_in_the_same_batch`; it fails without the fix, because the frozen clock is later than the batch's moment.
  - Live check run 3: batch 1 reported 170 remaining; batch 2 ran Andorra and then BDR GROUP SLU's page.
- **Status:** FIXED, VERIFIED.

### RF-04 (Medium): an empty reference card caused a false reference mismatch

- **Location:** `services/parsers.py`, `parse_partner_page()`.
- **Evidence:** live check run 3: "17 of 17 references, mismatch". The page was saved once (private, `runtime/logs/stage10/`) and parsed offline. 18 `div.card` siblings follow `h3#references`; one is completely empty, and it was reported as "a reference without a name". RoayaTec's live page of 2026-11-08 had 135 cards for 135 references.
- **Fix:** a card without a link, an image or any text is skipped. A card with content but no name is still a problem.
- **Verification:**
  - Regression test `test_an_empty_card_is_not_a_reference`.
  - The saved page now parses as 17 of 17 with no problem.
  - Live check run 4: PASS, "17 of 17 references, matched".
- **Status:** FIXED, VERIFIED.

### RF-05 (Medium): connecting the download would have started an unrequested full crawl on `azk_ee24`

- **Location:** `models/worker.py`, `_get_page_source()`; the `azk_ee24` queue.
- **Evidence:**
  - `azk_ee24` has had a pending country-list unit since 2026-11-10, and its Sync Worker job runs every 10 minutes. The server loads Python code at start, so any restart would have started reading the whole directory: about 330 listing pages and, on a first run, about 4,500 partner pages.
  - The user asked for one bounded live check on a disposable database only.
- **Fix:**
  - Settings > Partner Monitor > Pause Website Downloads (`azk_odoo_partner_monitor.downloads_paused`, D-64). Downloads run by default, as the assessment asks; while paused, the worker keeps every unit and the open runs show why they wait.
  - The parameter was set on `azk_ee24` before any code changed.
- **Verification:**
  - `test_paused_downloads_keep_the_queue_and_say_so`.
  - `azk_ee24` after the upgrade (16:42 UTC): one call of the worker job's entry point, with any HTTP request refused by a patch, processed nothing and sent nothing. Run 1 now waits with "website downloads are paused (Settings > Partner Monitor > Pause Website Downloads)" and still has one note; its queued unit is kept, and there are still 0 website partners.
- **Status:** FIXED, VERIFIED.

### RF-06 (Medium): branch-only users got an incomplete Trial Balance

- **Location:** `models/trial_balance_engine.py`, `_accounts_in_scope()` and `_add_carry_forward()`.
- **Evidence:**
  - Test run 1 of this stage: `test_a_branch_user_sees_the_branch_only` FAILED, because the Current Year Earnings row was missing.
  - A rolled-back probe on `azk_ee24_test`, January 2026, a branch with three entries. A user with the branch and its root got the right report. A user with the branch only got:
    - right amounts on Bank, Capital and Expenses;
    - no Current Year Earnings row (its 70 credit missing) and a false "no Current Year Earnings account" warning;
    - 3 rows instead of 49 without Skip Zero Balance;
    - no row at all for prefix 1014.
  - The cause, found in three probe steps and read in the pinned core:
    1. A first `sudo()` version of the fix did not help, so the cause was not access rights.
    2. `search_count` (49 accounts) and `search` (none) disagreed for the same domain, also under `sudo()`.
    3. `account.account._order` is "code, placeholder_code". Sorting by `placeholder_code` adds an INNER JOIN with each account's first company among `env.user._get_company_ids()`. That is the user's own companies, even under `sudo()`, so a user without the root company loses all of the root's accounts.
  - The standard Trial Balance showed this user only an empty Total line.
- **Fix:** `_chart_accounts()` searches the report company's chart (`_check_company_domain`) as the user, with `order="id"`; the rows are sorted by code later anyway. The engine still has no `sudo()` and no SQL, and the journal-item queries are unchanged.
- **Verification:** Trial Balance run 3 (final code, 114 of 114): `test_a_branch_user_sees_the_branch_only` PASS. It failed in runs 1 and 2. It checks the rows with and without Skip Zero Balance against a user who also has the root, a prefix, the shared journal, the refusals, and the standard report's empty answer.
- **Status:** FIXED, VERIFIED.

### RF-07 (Low): the documented demo shell call would install the Egyptian localization

- **Location:** `models/demo_data.py`, `_create_demo_data()`.
- **Evidence:**
  - Odoo 18 installs a country's localization when a company with that country is created outside tests and module loading (base `install_l10n_modules`). Installing a module commits the transaction. Then the account module queues the country's chart for the new company.
  - At install time (module loading) and in tests nothing happens, which is why Stage 09 saw no effect. But D-59 documents a one-time call from an Odoo shell for databases installed before the demo existed.
  - Found by accident: a probe in a shell on the disposable `azk_ee24_test` created a company with Egypt. Odoo installed `l10n_eg` (15:42 UTC) and committed the probe company, although the shell rolls back.
  - `azk_ee24` was checked: no `l10n_eg`. Its demo company was created without a country in Stage 09, and a company that already has a chart triggers nothing.
- **Fix:** the demo company is created with `chart_template_load` in the context, Odoo's own flag for "a chart is being loaded", which turns the automatic install off. The function loads the generic chart itself, and the flag is dropped from the company record afterwards.
- **Verification:**
  - Regression test `test_a_new_demo_company_installs_no_localization`: a spy sees the flag. Without the fix the spy would see no flag, even in test mode.
  - Real shell, `azk_ee24_clean` installed without demo data: the documented call created the demo company (Egypt, generic chart, EGP), and `l10n_eg` stayed uninstalled. A second call created nothing, and the counts equal the install-time demo (16 entries, 32 items, 10 groups).
- **Status:** FIXED, VERIFIED.

### RF-08 (Info): custom fiscal years, a coverage gap of D-60

- **Location:** `models/trial_balance_engine.py` (`compute_fiscalyear_dates` of the report company), `tests/test_fiscal_years_and_branches.py` (TB-F).
- **Evidence:** the same seven entries, hand-calculated for three periods (June 2026, July 2026, and 15 June to 15 July 2026), in two companies whose fiscal year runs from 1 July: one through the company setting, one through an `account.fiscal.year` record. Both the engine and the standard Trial Balance equal the hand-calculated numbers in every case, and each other. With a calendar year, July 2026 would differ (Expense opening 250, Earnings 680 instead of 430), so the tests discriminate.
- **Documented behaviour:**
  - A period across the boundary opens the income and expense accounts at the start of the fiscal year that contains Date From, as the standard report does. So the ending Revenue (1,000) mixes two fiscal years (600 and 400). For closing figures, choose a period inside one fiscal year.
  - After the last `account.fiscal.year` record, Odoo starts the next year the day after it and ends it with the setting's year end (2026-07-01 to 2026-12-31 here).
- **Verification:** Trial Balance run 3 (114 of 114): the three TB-F tests PASS, as they did in runs 1 and 2.
- **Status:** DOCUMENTED (no defect).

### RF-09 (Info): branch companies, a coverage gap of D-60

- **Evidence (TB-B tests):**
  - A branch shares its root's chart and journal.
  - Our report covers exactly the selected company (D-16). The standard report adds up every active company, so with the root and its branch active it adds them both, and ours does not.
  - Each company alone equals the standard report and the hand-calculated numbers.
  - A user of one company is refused the other.
  - A branch ignores its root's `account.fiscal.year` records, because Odoo keeps them on root companies only and looks them up by the exact company. The standard report does the same.
- **Verification:** Trial Balance run 3 (114 of 114): the six TB-B tests PASS.
- **Status:** DOCUMENTED. Consolidating a root with its branches is not supported; each company is reported on its own.

### RF-10 (Info): our report extensions leave the standard reports unchanged

- **Evidence:**
  - `tests/test_native_reports.py`: the standard Trial Balance and General Ledger XLSX are equal, cell by cell, to the ones written by the original Enterprise methods; the standard PDF uses none of our templates.
  - The vendor's own `TestTrialBalanceReport` (8 tests) and `TestAccountReportAnnotationsExport` (3 tests) were run with our addon installed: PASS, "0 failed, 0 error(s) of 11 tests" (16:26 to 16:29 UTC, fresh `azk_ee24_test` with `azk_dynamic_trial_balance` installed, 0 warning lines): the 8 `TestTrialBalanceReport` tests, including `test_trial_balance_comparisons`, and the 3 `TestAccountReportAnnotationsExport` tests, which export the standard reports to XLSX.
- **Status:** DOCUMENTED (no defect).

### RF-11 (Info): Partner Monitor storage cost grows with the number of cards

- **Evidence:** the benchmark below: 7 queries and about 5 ms per card on a first read, 4 queries and about 2 ms per card on a repeat, the same at 100 and at 1,000 cards; a 135-reference page in 7 queries; the dashboard in 21 queries with 1,150 partners.
- **Status:** DOCUMENTED, kept by design. Each card is stored in its own savepoint through the observation methods, so that one bad card cannot stop the others; the cost per card is constant and the daily directory (about 4,500 partners) is small.

### RF-12 (Low): the longest country unit leaves little room under the prefork time limit

- **Evidence:**
  - The country list of 2026-11-08 has 170 countries and 328 listing pages. The largest, the United States, has 269 partners on 14 pages: at least 42 s at 3 s per request, about 50 s with transfers.
  - The worker checks its 60-second budget between units, so a batch can last about 110 s. In multi-process mode, the scheduler kills a call after `limit_time_real_cron`, or after `limit_time_real` (120 s by default) when that is not set.
  - This Docker setup runs threaded, without that limit.
- **Status:** DOCUMENTED. For production: raise `limit_time_real_cron`, or lower `azk_odoo_partner_monitor.worker_time_budget`. Page-level checkpoints stay the next step if live timings require them (resilience.md section 13).

### RF-13 (Low): stale requirement rows

- **Location:** [requirements_matrix.md](requirements_matrix.md): P-28 still said DESIGNED although Stage 06 built and tested the charts; P-03.2 said `requests` was not used.
- **Fix:** both rows were updated, along with every row this stage touched.
- **Status:** FIXED (documentation).

### RF-14 (Info): README and publication items

- G-01 to G-06, G-08, T-19 and T-20 depend on the README and the public repository (Stages 12 and 15). They stay NOT STARTED or IN PROGRESS in the matrix.
- The Trial Balance mockup (M-02) and the views specification (M-01) were never supplied, so the layout choices remain assumptions (A-16, P-17.3).
- **Status:** OPEN, by plan.

### RF-15 (Info): analytic accounting in the browser

- **Evidence:** Stage 09 could not try the analytic selector in a browser, because Odoo's Analytic Accounting setting is off on `azk_ee24` (D-62). This stage turned it on in the disposable `azk_ee24_test`, served it on a temporary server at http://127.0.0.1:8072 (no cron threads), and ran `scripts/tb_analytic_smoke_check.py` there as a read-only accountant (run 2, 16:22 to 16:25 UTC): PASS, 6 of 6. The wizard's Analytic Accounts field opened the preview filtered (1 account row in March 2026 with Sales Department, 7 without), the preview's dropdown recalculated the report both ways, each time equal to the engine, the XLSX equalled the engine and the PDF stated the filter, two tampered downloads were refused with AccessError, and no JavaScript error occurred.
- **Status:** DOCUMENTED (no defect).

## Checked with no finding

- **Scope.** Exercise 3 (POS) stays explicitly unselected (X-01, A-01).
- **Manifests and dependencies.**
  - `azk_odoo_partner_monitor` depends on `mail` only and declares `requests` and `beautifulsoup4`.
  - `azk_dynamic_trial_balance` depends on `account_reports` (Enterprise, OEEL-1; its own license is question Q-06) and declares XlsxWriter.
  - Security files load first. The addons contain no Odoo license header and no vendor or core code; Enterprise interfaces are used by name only (K-06).
  - The Partner Monitor is 18.0.1.5.0 after this stage; the Trial Balance stays 18.0.1.3.0 (code changed, no data or view).
- **`sudo()`: 11 calls in 8 methods, all narrow.**
  - Four manager actions run their group check first: mark a country or a partner for re-scrape, Sync Now, and Retry.
  - Three places read `ir.config_parameter`: the failure recipient, the worker numbers, and the download pause.
  - One place triggers the worker job.
  - None of them takes a domain or values from a client.
  - The Trial Balance has none.
- **Raw SQL: 4 statements**, all built with `SQL()` from constants and parameters: three partial unique indexes in `init()`, and the worker's claim query. No user input reaches SQL.
- **Methods callable over RPC:**
  - Partner Monitor: `get_dashboard_data` (reader check; it takes filter values only), `action_mark_for_rescrape` twice, `action_sync_now` and `action_retry` (manager check).
  - Trial Balance: the engine's `compute` (accounting read-only group, plus validation), and the wizard's `action_preview`, `action_export_pdf` and `action_export_xlsx` (record rule on `create_uid`).
  - Neither addon has a controller.
- **Access rights.**
  - No ACL line for portal or public users in either addon.
  - Partner Monitor data is read-only for readers and managers; writes go through the checked actions.
  - Trial Balance wizards and prefixes are private to their creator. The engine requires `account.group_account_readonly`.
  - A hidden button is never the only check: every action and RPC method checks again on the server.
- **Accounting (Stages 07 to 09 tests, rerun in this stage):**
  - the opening convention, signs and rounding, cancelled entries never, drafts on request;
  - whole-item analytic selection, currencies never summed together, literal prefixes (`%` and `_` refused, and escaped anyway);
  - hierarchy totals, and the same numbers in Preview, PDF and XLSX.
  - A report filtered on purpose is not required to balance: the engine reports `balanced`, and the preview shows a message instead of an error.
- **Scraping:**
  - bounded timeouts and retries (RF-01);
  - partial snapshots never delete, and now a login page or a rate limit through the real client keeps the data too;
  - missing values stay unknown;
  - the country scope is checked on raw links;
  - a snapshot must have every page from 1 to the last;
  - identities are stable (website ids and reference keys);
  - overlapping workers are covered (row locks, tested on two real connections);
  - crashed batches are replayed: restart check PASS, 12 of 12 on the Stage 10 code;
  - one failure note per run.
- **UI.** Dashboard filters, Top and Bottom 5 rankings, size buckets and empty states are covered by 16 dashboard tests. Browser checks after updating `azk_ee24`: the dashboard check passed 7 of 7 and the preview check 20 of 20, both on `azk_ee24` after the upgrade, with 0 warning lines in the server log.
- **Data and secrets.**
  - Demo records are labelled (`is_demo`, reserved ids, a separate Trial Balance company).
  - The live check ran on the disposable database and rolled back.
  - Pre-commit scan: 41 changed text files scanned (all but the screenshots); no non-ASCII text, no local path. 4 lines were flagged and reviewed: they read the browser checks' login and password from environment variables (`PM_UI_LOGIN`, `PM_UI_PASSWORD`, `TB_RO_PASSWORD`) and hold no value. The four new screenshots were viewed: demo data only.

## The download route, step by step

What happens when the preview's PDF button or its gear menu's "Download Excel" is used (the wizard's PDF and XLSX buttons join at step 2). Read in the pinned sources on 2026-11-15; Enterprise code is named, not quoted. Each validation step is marked with the failure it stops.

1. **The button.** `account.report.dispatch_report_action(options, 'export_file', 'export_to_pdf')` returns the action of `export_file()`: a client download of `ir_actions_account_report_download` with the options as JSON. The wizard's `action_export_pdf()` and `action_export_xlsx()` (`models/trial_balance_wizard.py`) reach the same `export_file()` through `_export()`. Before that, the wizard reads its own record: the `create_uid` record rule (`security/trial_balance_security.xml`) gives another user's wizard an AccessError.
2. **The route.** The browser POSTs `options` and `file_generator` to `/account_reports`: `AccountReportController.get_report` in `account_reports/controllers/main.py`.
   - `auth='user'`: no session, no file. The request gets the login page (browser check, Stage 09).
   - `get_report_company_ids(options)` turns the client's `options['companies']` into `allowed_company_ids`. The ORM refuses a company the user may not access (AccessError when the environment's companies are read): a tampered company list cannot widen access (`test_tampered_options_are_refused_on_every_path`).
   - `check_method_name(file_generator)`: no private method can be called.
   - A refused download answers HTTP 200 with an HTML-escaped JSON error body; no file is produced.
3. **Dispatch.** `account.report.dispatch_report_action(options, file_generator)`:
   - `options['report_id']` must be this report (UserError otherwise);
   - `check_method_name(action)` again;
   - our handler has no `export_to_*` method, so the report's own `export_to_pdf()` or `export_to_xlsx()` runs. Reading the report needs the `account.report` read right, which only `account.group_account_readonly` and above have.
4. **The options are rebuilt.** Both exports start with `get_options(previous_options={**options, 'export_mode': 'print'})`. Nothing from the browser is used as it is:
   - our `TrialBalanceReportHandler._custom_options_initializer()` (`models/trial_balance_report_handler.py`) takes `options['azk_tb']` through `_raw_engine_options()` (a dictionary, or ValidationError), then `normalize_options()` (`models/report_options.py`): unknown keys, wrong types, dates, a company the user may not use or that is not active (AccessError or ValidationError), option combinations, literal prefixes, and a journal or analytic account that is not readable in that company;
   - `options['companies']` is set to exactly the validated report company;
   - the printed texts (`azk_tb_display`) are computed again from the validated options, so a tampered label cannot reach the PDF or the XLSX.
5. **The numbers.** `_get_lines()` calls the handler's `_dynamic_lines_generator()`, which calls `TrialBalanceEngine.compute()` (`models/trial_balance_engine.py`):
   - `compute()` requires `account.group_account_readonly` (AccessError) and validates the options a third time with `normalize_options()`;
   - three `_read_group` queries run as the user, so access rights and every record rule apply; there is no `sudo()` and no SQL.
6. **The file.**
   - PDF: `_custom_line_postprocessor()` applies the search text, `_filter_out_folded_children()` drops folded children, `_get_pdf_export_html()` renders `account_reports.pdf_export_main` with our three templates (QWeb `t-out` escapes every text), and `ir.actions.report._run_wkhtmltopdf()` converts it.
   - XLSX: the workbook is created with `strings_to_formulas` off; our `_inject_report_into_xlsx_sheet()` (`models/account_report.py`) writes codes and names with `write_string` and amounts with `write_number`, so text from the options or the data can never become a formula.

Tests of this path: `test_report_access.py` (a reader exports; employees and billing users get nothing; five tamperings and an unauthorized company refused on `get_options`, `export_to_pdf` and `export_to_xlsx`; another report refused), `test_engine_access.py` (another user's wizard), and the browser checks against the real route (Stage 09: a tampered prefix refused, no file without a session. Stage 10: the same check rerun on `azk_ee24`, and two tampered downloads refused for a read-only accountant, RF-15).

## Benchmark

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

## Notes on the review process

- **Live requests.** Every request to www.odoo.com is listed in [live_site_notes.md](live_site_notes.md) and [test_results.md](test_results.md).
  - Total on 2026-11-15: 23 requests between 15:14 and 16:33 UTC: the four live check runs (1, 4, 5 and 5 requests, robots.txt included), 7 single diagnostic requests to robots.txt (RF-02), and 1 request that saved BDR GROUP SLU's page for offline analysis.
  - The four live check runs used the module's client.
  - The diagnostic requests were single curl or `requests` calls, about 5 seconds apart.
  - One request saved BDR GROUP SLU's page for offline analysis; that page is kept privately and not committed.
- **A probe committed into the disposable database.** A probe company created with Egypt in an Odoo shell made Odoo install `l10n_eg` into `azk_ee24_test`, which committed the probe company too (RF-07). That database is disposable and was recreated by the next test run. The later probes were created without a country.
- **One wrong lead, corrected.** The first explanation of RF-06 blamed the `res.company` record rule, and the first fix used a narrow `sudo()`. Test run 2 still failed. A probe showed that `search_count` and `search` disagreed even under `sudo()`, which led to the real cause: the default order's join. The final fix has no `sudo()`. The documents were corrected before the commit.
- **Tools.** `beautifulsoup4` 4.12.3 was added to the private `runtime/tools/venv` (outside Git), to parse the saved live page offline with the module's own parser.
- **Memory.** The heavy checks ran one at a time. Free RAM was sampled (1.9 to 2.6 GB free), and the browser checks ran under the Stage 09 memory guard.

## Stage 09 comprehension questions, with answers

The three questions of [handoffs/stage_09_en.md](handoffs/stage_09_en.md), recovered as written, then answered.

1. **The PDF button of the preview and the XLSX item of its gear menu both end in the same route. Which function validates the options again there, and why must it, even though the preview already validated them?**

   On `/account_reports`, `export_to_pdf()` and `export_to_xlsx()` both call `get_options()`, which runs our `_custom_options_initializer()`; that calls `normalize_options()` on `options['azk_tb']` and resets `options['companies']` to the validated report company. The engine's `compute()` then calls `normalize_options()` once more before any query. This is needed because the route receives the options as JSON in a new POST. Anyone with a session can change them: another company, a journal of another company, a `%` in a prefix, an unknown key. A check made by the earlier preview request says nothing about this request. In Django terms, it is the reason a view validates the submitted form again instead of trusting a hidden field it rendered earlier.

2. **Why does the handler mark every group line `unfolded` or not, and send all child lines, instead of loading children when a group is unfolded? What would the PDF and XLSX lose otherwise?**

   The engine computes the whole report in one call, so every group and account line is already known. Sending them all, each group marked `unfolded` or not, means:
   - folding in the browser needs no further server request;
   - every output is built from the same `_get_lines()` result;
   - the standard `_filter_out_folded_children()` drops exactly the rows the user folded, so the PDF and XLSX show what the preview shows.

   With lines loaded only when a group is unfolded (the framework's expand functions), the exports would contain only what the server had expanded. They would lose the account rows under the groups, or they would need a second code path that expands groups for the exports. That second place to build lines could then disagree with the preview.

3. **The demo data is created by a function called from a demo XML file. Why does an upgrade never run that function, and why must the function still check the company's XML id before it creates anything?**

   Odoo loads demo files as `noupdate` data, and its XML loader skips a `<function>` element of a `noupdate` file unless the module is being installed. So `-u` (an upgrade) never calls it, as the Stage 09 upgrade runs showed. The function can still run more than once in other ways:
   - an explicit call from an Odoo shell, as was done once for `azk_ee24`, which got the module before the demo existed, and as D-59 documents for any such database;
   - the deferred call from `_register_hook`, a second path into the same function;
   - any later caller, for example a call repeated by mistake.

   Checking the XML id `azk_dynamic_trial_balance.demo_company` first makes every later call a no-op. `test_running_the_demo_function_again_creates_nothing` checks this: the second call returns False and every count is unchanged. Without the check, each such call would create another demo company with duplicate entries.
