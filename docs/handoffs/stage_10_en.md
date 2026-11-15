# Stage 10 handoff: engineering review

Date: 2026-11-15. Edition: `enterprise-20241208` (port 8071). Status: **DONE**, and Stage 04 is now **DONE** too.

The findings, with severity, location, evidence, fix and verification, are in [review_findings.md](../review_findings.md). That file also traces the download route step by step and answers the three Stage 09 comprehension questions. Commands and results are in [test_results.md](../test_results.md).

## What this stage delivers

- **The Partner Monitor reads the live website.**
  - `services/http_client.py` is the missing page download.
  - It is connected to the worker, with a Settings switch to pause it (D-64, D-65).
  - One bounded live check through the real worker passed on the disposable database: the country list, Andorra and one partner page.
  - Stage 04 is complete.
- **Six defects found and fixed, each with a check that fails without the fix:**
  - RF-02: the website closed every connection that offered `deflate`.
  - RF-03: work queued during a batch waited for the next scheduler interval.
  - RF-04: an empty reference card made a complete list look incomplete.
  - RF-05: connecting the download would have started an unrequested crawl on `azk_ee24`.
  - RF-06: branch-only users got an incomplete Trial Balance.
  - RF-07: the documented demo shell call would install the Egyptian localization.
- **Stale requirement rows corrected** (RF-13).
- **The Trial Balance's open coverage is closed:**
  - custom fiscal years and branches (TB-F and TB-B, against hand-calculated numbers and the standard report);
  - the analytic selector in a real browser;
  - the standard reports, shown unchanged;
  - a benchmark.

## The three most important fixes

1. **RF-02, the website closed every download.** It closed every HTTP/1.1 connection that offered `Accept-Encoding: gzip, deflate` (the `requests` default), after about 15 seconds. Every sync would have failed, though safely: nothing would have been stored or deleted. Fixed by offering gzip only. Without this, the Partner Monitor could never have synchronized.
2. **RF-06, branch-only users got an incomplete Trial Balance.** For a user who has a branch but not its root company, `account.account`'s default order dropped the shared accounts from every search. The Trial Balance lost the Current Year Earnings row (and showed a false warning), the accounts without items and every prefix match. Fixed with an explicit order, still without `sudo()`. Without this, such a user would get an incomplete report that looks right.
3. **RF-04, a complete reference list looked incomplete.** An empty card on a live partner page made a complete list of 17 references look incomplete. Fixed by skipping empty cards. Without this, the partner would be re-scraped 5 times for nothing and then shown as "Retries Exhausted".

## Short walkthrough

On http://127.0.0.1:8071 (`azk_ee24`, admin):

1. **Partner Monitor > Dashboard.** The "Sync waiting" banner now says "website downloads are paused (Settings > Partner Monitor > Pause Website Downloads)". Run 1 of 2026-11-10 keeps its queued country-list unit.
2. **Settings > Partner Monitor > Website Downloads.** "Pause Website Downloads" is ticked on this database (D-64). Unticking it lets the next worker call read the real directory: about 330 listing pages and, the first time, about 4,500 partner pages, at one request every 3 seconds or more, which takes several hours. So untick it only if you want that.
3. **The analytic selector, if you want to see it here.** It is hidden on `azk_ee24` because Odoo's Analytic Accounting setting is off (D-62); this stage tested it on a disposable copy.
   - Turn it on in Accounting > Configuration > Settings > Analytic Accounting.
   - Open Accounting > Reporting > Audit Reports > Dynamic Trial Balance, with the company "AZK Trial Balance Demo (EGP)" active.
   - Choose 1 March to 31 March 2026, Skip Zero Balance, and Analytic Accounts "Sales Department", then click Preview.
   - Expected: one row, 600000 Expenses, 1,200.00 debit, with the message that the filters are active and the report need not balance. Switching the preview's analytic dropdown to "All analytic accounts" shows the 7 accounts of March.
4. **A branch-only user (RF-06)** cannot be tried on `azk_ee24`, which has no branch. The behaviour is covered by `TestBranchFixture`.

## Checks performed

All on 2026-11-15, edition `enterprise-20241208`, one heavy check at a time. Details and earlier runs are in [test_results.md](../test_results.md).

- **Partner Monitor tests** (`scripts/dev.sh test azk_odoo_partner_monitor`):
  - run 1: PASS, 145 of 145;
  - final run: PASS, "0 failed, 0 error(s) of 147 tests", 0 warning lines (18 new tests).
- **Trial Balance tests** (`scripts/dev.sh test azk_dynamic_trial_balance`):
  - run 1: FAIL, 1 of 113 (the branch-only reader, RF-06);
  - run 2: FAIL, 1 of 114 (the first fix was wrong);
  - run 3, final code: PASS, "0 failed, 0 error(s) of 114 tests", 0 warning lines.
- **The vendor's tests with our addon installed:** PASS, 11 of 11 (`TestTrialBalanceReport` 8, `TestAccountReportAnnotationsExport` 3).
- **Live check through the worker** (`scripts/pm_live_check.py`, disposable database, rolled back):
  - run 1: FAIL (RF-02);
  - run 2: PASS for what ran (RF-03 found);
  - run 3: PASS (RF-04 found);
  - run 4, final code: PASS. 4 page requests, every one allowed by robots.txt; BDR GROUP SLU "17 of 17 references, matched"; rolled back. In all, 23 requests reached the site that day.
- **Analytic selector in a browser** (`scripts/tb_analytic_smoke_check.py`, read-only accountant, temporary server on 127.0.0.1:8072 for the disposable database): PASS, 6 of 6. That includes tampered downloads refused with AccessError.
- **Benchmarks:**
  - Trial Balance: constant query counts from 2,000 to 10,000 journal items (engine 15 to 16 queries, 0.03 to 0.07 s);
  - Partner Monitor: 7 queries per card on a first read and 4 on a repeat, at both 100 and 1,000 cards; the dashboard in 21 queries with 1,150 partners.
- **Restart check** (`scripts/restart_check.sh`): PASS, 12 of 12. The worker was killed mid-batch at 16:34:28 UTC; after the restart only the interrupted units ran again, and nothing was duplicated.
- **Install without demo data and the documented demo call** (`azk_ee24_clean`): PASS. 0 warnings, and nothing of either demo. The documented demo call then created the demo company without installing `l10n_eg`, with the same counts as the install-time demo; a second call created nothing.
- **`azk_ee24` update and browser checks:** PASS. Upgrade with 0 warnings. One worker call made no request, and run 1 now waits with "website downloads are paused". Browser reruns: dashboard 7 of 7, Trial Balance preview and downloads 20 of 20.
- **Pre-commit scan:** 41 changed text files scanned (all but the screenshots); no non-ASCII text, no local path. 4 lines were flagged and reviewed: they read the browser checks' login and password from environment variables (`PM_UI_LOGIN`, `PM_UI_PASSWORD`, `TB_RO_PASSWORD`) and hold no value. The four new screenshots were viewed: demo data only.

## Open issues and remaining gaps

- **README and publication** (G-01 to G-08, T-19, T-20): Stages 12 and 15 (RF-14).
- **No full live sync from this machine,** on purpose: downloads are paused on `azk_ee24` (D-64). The bounded check covered the country list, one country with partners and one partner page. An empty country (Anguilla's fallback) was not read live through the module; the live-derived fixture still covers it.
- **The robots.txt rules are coded** (D-25, D-65). The live check reads robots.txt and compares, but the module itself does not. A change on the site needs a code change.
- **Production configuration** (RF-12): with multi-process workers, raise `limit_time_real_cron`, or lower the worker's time budget. The largest country unit takes about 50 s at the 3-second spacing.
- **Branches** (D-16, D-66): no consolidation of a root company with its branches. A branch ignores its root's `account.fiscal.year` records (Odoo). The standard Trial Balance shows a branch-only user nothing; ours works for them.
- **The 2026-11-15 live check found three site details** that only a live run could show (RF-02, RF-03, RF-04). The site can change again; the live check script makes rerunning it cheap (at most 8 requests).
- **Still for the user:** a browser check of your own (walkthrough above), the questions Q-02 to Q-06 for the team lead, the addon license (Q-06), and the Git identity before publication.

## Changed files

**`addons/azk_odoo_partner_monitor/`** (18.0.1.5.0)

- New:
  - `services/http_client.py`: `PartnersHttpClient` (`get`, `_download`, `_attempt`, `_check_status`, `_read_body`, `_decode`, `_check_page`, `paused_reason`), `RequestPacer` (`wait`, `pause`, `paused_reason`), `retry_after_seconds`, `_charset`, and the `FetchError` classes;
  - `tests/test_http_client.py`: `TestHttpClient`, `TestWorkerWithHttpClient`.
- Changed:
  - `models/worker.py`: `_get_page_source` (returns the client, or None while paused), `_process_queue` (stops after a rate limit), `_wait_for_page_source` (takes the reason), `_cron_process_queue` (reports nothing done while waiting), `_unit_country_list` and `_unit_country_partners` (queue work due at the batch's moment), `_paused_reason`;
  - `models/work_item.py`: `_enqueue(now=...)`;
  - `models/sync_run.py`: `_set_waiting` (the note's wording);
  - `models/res_config_settings.py` and `views/res_config_settings_views.xml`: Pause Website Downloads;
  - `services/parsers.py`: `parse_partner_page` skips empty cards;
  - `services/reader.py` and `services/__init__.py`: comments;
  - `tests/test_worker.py`, `tests/test_parsers.py`, `tests/__init__.py`, and `__manifest__.py`.

**`addons/azk_dynamic_trial_balance/`** (18.0.1.3.0, Python only)

- `models/trial_balance_engine.py`: `_chart_accounts` (new), `_accounts_in_scope`, `_add_carry_forward`.
- `models/demo_data.py`: `_create_demo_data` (the company is created with `chart_template_load`).
- Tests:
  - new: `tests/test_fiscal_years_and_branches.py` (`TestFiscalYearFixture`, `TestBranchFixture`) and `tests/test_native_reports.py` (`TestNativeReportsUnchanged`);
  - changed: `tests/test_demo_data.py`, `tests/common.py` (`_entry` sets the company; `native_trial_balance(active_companies=...)`) and `tests/__init__.py`.

**Scripts**

- New: `scripts/pm_live_check.py`, `scripts/pm_benchmark.py`, `scripts/tb_benchmark.py`, `scripts/tb_analytic_setup.py`, `scripts/tb_analytic_smoke_check.py`.
- Changed: `scripts/dev.sh` (`clean-install ... --without-demo`) and `scripts/restart_check.py` (a comment).

**Documentation**

- New: [review_findings.md](../review_findings.md) and this handoff.
- Updated: [STATE.md](../STATE.md), [requirements_matrix.md](../requirements_matrix.md), [assumptions.md](../assumptions.md) (D-59, D-60 and D-62 updated; D-64 to D-66 new), [architecture.md](../architecture.md) (4.12, 5.11, 5.14), [resilience.md](../resilience.md) (1, 11, 13, 15), [live_site_notes.md](../live_site_notes.md), [test_plan.md](../test_plan.md) (3.5, 4.6, 6), [test_results.md](../test_results.md), [ai/stage_10.md](../ai/stage_10.md), [ai/README.md](../ai/README.md), and [screenshots/](../screenshots/) (`stage10_*.png`).

**Outside Git**

- `runtime/logs/stage10/`: command logs, the saved BDR GROUP SLU page, and the browser check output.
- `beautifulsoup4` in `runtime/tools/venv`.
- `azk_ee24`: the pause parameter, and the upgrade to this code.

## Comprehension questions

1. The page download raises an exception for a login page or HTTP 429 instead of returning the page it got. What exactly would go wrong, in our ingestion, if it returned that page as text and let the parser decide?
2. Why does the worker report "nothing done" to the scheduler after a rate limit, although one unit was tried? What would the scheduler do otherwise?
3. For a user who has a branch but not its root company, `search_count` found 49 accounts and `search` found none, even under `sudo()`. What in Odoo's default ordering of accounts explains it, and why did `sudo()` not help?

## Next stage

Stage 11 (clean acceptance), when you ask for it.
