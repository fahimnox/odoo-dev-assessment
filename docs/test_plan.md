# Test and acceptance plan (Stage 02)

_Written 2026-11-05 as the plan. Stages 03 to 06 implemented the Partner Monitor tests (sections 3.1 to 3.4). Stage 07 (2026-11-15) implemented the Trial Balance fixtures, the wizard tests and the comparisons with the standard Trial Balance (sections 4.1 to 4.3); the engine and output tests come in Stages 08 and 09. The design they verify is in [architecture.md](architecture.md), the requirements in [requirements_matrix.md](requirements_matrix.md)._

## 1. Rules for every result

- Every check is reported as PASS, FAIL, BLOCKED or NOT RUN. A run that collects zero tests is a failure: `scripts/dev.sh test` already fails on Odoo's "of 0 tests" line.
- Tests run in a fresh disposable database of the target edition (`azk_ee24_test`, edition `enterprise-20241208`) through `scripts/dev.sh test`.
- Normal tests never touch the live website; they use saved HTML fixtures labeled live-derived or synthetic.
- Tests send no real email; they use Odoo's mail mocks.
- Dates are frozen with `freezegun` (1.2.1 in the image) where the result depends on today.
- **Trial Balance:** expected values are written by hand from the documented contract, never produced by the code under test. Comparisons with the native Trial Balance are extra evidence, not a replacement.
- **Browser:** the Odoo image has no browser, so Odoo's own browser tours do not run. Since Stage 06 the agent drives the host's Chrome headless through the DevTools protocol (`scripts/ui_smoke_check.py`). Other screens are NOT RUN unless such a check exists for them. The user's manual browser checks are recorded separately, as the user's results.
- **Where results go:**
  - `docs/test_results.md` from Stage 08;
  - `docs/resilience.md` in Stage 05;
  - `docs/acceptance_results.md` in Stage 11;
  - full command logs privately in `<kit-root>/runtime/logs/`.

## 2. Test levels

| Level | What | How | Stages |
|---|---|---|---|
| L1 | Pure functions: HTML parsers, URL rules, bucket and ranking helpers, amount netting | Odoo test classes without database writes, on saved fixtures | 04, 06, 08 |
| L2 | ORM behavior: models, constraints, ingestion, history, engine numbers, access rules | `TransactionCase` (rolled back), several users and companies | 03-09 |
| L3 | Commit boundaries and crashes: the worker cron in a real process, killed and restarted | A script against a disposable database; SQL state before and after; it cannot run inside `TransactionCase`, which forbids commits | 05 |
| L4 | HTTP and RPC: dashboard method, report RPC, download route, access denial | `HttpCase` with real sessions (no browser) | 06, 09 |
| L5 | Rendered outputs: PDF text and layout, XLSX cells | Native exporters through a running server (wkhtmltopdf needs the HTTP server for CSS). XLSX cells are read in tests with `openpyxl` (3.1.2 in the image). PDF text is checked with the host's `pdftotext` (not in the image), and the PDF is inspected visually | 09 |
| L6 | Manual and browser checks | Steps for the user; screenshots only if a browser is available | 06, 09, 11 |

## 3. Exercise 1: Partner Monitor

| ID | Stage | Check | Expected result | Requirements |
|---|---|---|---|---|
| TP-PM-01 | 03 | Install and upgrade; required models, field names and types match the PDF (field introspection) | The four models exist with exactly the PDF's fields and types; the module upgrades without warnings | P-01, P-09 to P-12 |
| TP-PM-02 | 03 | Uniqueness | A duplicate `country.source_key`, a duplicate `partner.source_id`, a second active reference with the same key, a second `initial` history row, and a second pending work item for the same target are all rejected by the database | K-03 |
| TP-PM-03 | 03 | First observation | One partner and exactly one `initial` history row (empty previous status). `first_seen_on` = the frozen run date; it is unchanged after a later ingestion | P-13, P-14 |
| TP-PM-04 | 03 | Transitions | ready -> gold is `promoted`, gold -> silver is `demoted`; an unchanged status adds no row; replaying the same unit adds no row; an unknown label fails the unit without writes | P-14, D-09 |
| TP-PM-05 | 03 | Permissions | A reader can read business data but cannot write it, create history or see work items; a manager can schedule Sync now and Retry; a user without the groups cannot read anything | K-02, A-22 |
| TP-PM-06 | 04 | Parsers on fixtures | The country list yields ids, names and counts; listing pages yield partner ids, names, statuses, reference counts and pagination; detail pages yield metrics and references; missing values are flagged unknown, never 0 | P-02, P-09, P-10 |
| TP-PM-07 | 04 | Broken input | Truncated or unexpected markup, a login page, a rate-limit page, an HTTP error and a timeout (mocked) are each a failure with a clear error, never an empty result | P-05, P-06, K-04 |
| TP-PM-08 | 04 | Country-scope rule | A link with the right `country_id` is kept, also as the second parameter; a missing or different `country_id` is ignored and logged; a page with the fallback alert is unscoped; the check happens before canonicalization | P-22 |
| TP-PM-09 | 05 | Idempotent ingestion | The same snapshot ingested twice creates no duplicate partner, reference or history row | P-08.2, K-03 |
| TP-PM-10 | 05 | Failure isolation | In one batch, partner A fails and partner B succeeds; A's error is stored with its context; the cursor stays usable; B's data is written | P-05, P-06 |
| TP-PM-11 | 05 | Country validation | A count mismatch sets `to_reprocess_partners` and blocks archiving; the validation cron re-enqueues once (de-duplicated); a matching retry clears the flag; a permanent mismatch stops after the retry limit and stays visible | P-18, P-19 |
| TP-PM-12 | 05 | Reference validation | An expected count different from the active count sets `to_reprocess_references`; a changed metric schedules one detail refresh, not a loop; a complete matching fetch clears the flag | P-20, P-21 |
| TP-PM-13 | 05 | Partial snapshots | A truncated country fetch archives no partner; a partial reference list removes no reference; an incomplete country list deactivates no country; a valid empty country is handled as empty | P-16, P-23, K-04 |
| TP-PM-14 | 05 | Overlap | Two cursors claim units concurrently and never get the same unit (`SKIP LOCKED`); duplicate scheduling creates one pending unit | P-08.1 |
| TP-PM-15 | 05 | Crash and restart (L3) | Kill the worker process mid-run, then restart: committed batches stay done, the interrupted batch is replayed once, nothing is duplicated; SQL counts before and after are recorded | P-08.1, P-08.2 |
| TP-PM-16 | 05 | Failure notification | A partial run posts exactly one note on its chatter with the configured user as recipient (a `mail.notification` row for that partner); a second finalization posts nothing; no email leaves the system | P-07 |
| TP-PM-17 | 05 | Change-aware pulling | An unchanged listing card triggers no detail fetch; a changed card or stale details do; a 304 is used only with a known-good snapshot | P-08.3 |
| TP-PM-18 | 06 | Dashboard data | Filter propagation to all four charts; ranking after filters; ties; fewer than 5 and fewer than 10 countries; empty state; bucket boundaries 4.99, 5, 10.99, 11, 24.99, 25 and unknown; chart totals equal the filtered record counts | P-24 to P-27, D-05, D-06 |
| TP-PM-19 | 06 | Dashboard access (L4) | A reader gets data; a user without the reader group is refused by the server, whatever domain the client sends | P-24, K-02 |
| TP-PM-20 | 06 | UI (L6) | Menu opens the dashboard first; four charts render; each filter changes all four; a bar opens the matching partners | P-24, P-25 |
| TP-PM-21 | 04, 06 | Bounded live smoke | One or two country pages fetched live; evidence saved and labeled live with its date; BLOCKED if there is no connectivity | P-02 |

### 3.1 Implemented in Stage 03 (2026-11-08)

The checks TP-PM-01 to TP-PM-05 are automated in `addons/azk_odoo_partner_monitor/tests/` (`TransactionCase`, tagged `post_install`). Results are in [STATE.md](STATE.md) and the Stage 03 handoff.

- **TP-PM-01** (models and fields): `test_models.py`, `TestDataModel.test_required_models_and_field_types_match_the_pdf`. Install and upgrade are checked with the commands in section 6.
- **TP-PM-02** (uniqueness, identities, relations): `TestDataModel`:
  - `test_country_identity_is_the_website_id`, `test_partner_identity_is_the_website_id`;
  - `test_demo_and_website_ids_never_collide`, `test_relations_are_enforced`;
  - `test_work_item_target_matches_its_kind`, `test_one_pending_work_item_per_target`;
  - `test_partner_url_must_be_canonical`, `test_canonical_url_rule`;
  - `test_unknown_metric_is_not_zero`, `test_observation_cannot_set_protected_fields`, `test_demo_records_are_labeled`;
  - plus `test_references.py`, `TestReferences.test_reference_rules_in_database` and `test_status_history.py`, `TestStatusHistory.test_history_rules_in_database_and_model`.
- **TP-PM-03 and TP-PM-04** (first observation, transitions): `test_status_history.py`, `TestStatusHistory`:
  - `test_first_observation_creates_partner_and_initial_row`;
  - `test_silver_gold_gold_records_initial_then_one_promotion`, the sequence Silver -> Gold -> Gold;
  - `test_ranking_types_promotions_and_demotions`, `test_replayed_observation_adds_nothing`, `test_older_observation_is_ignored`;
  - `test_unknown_status_writes_nothing`, `test_first_seen_on_cannot_be_rewritten`;
  - `test_archived_partner_reappears_with_its_history`, `test_country_move_updates_the_same_partner`;
  - `test_history_rows_cannot_be_changed`, `test_users_cannot_record_observations`, `test_demo_history_is_consistent`.
- **Reference intervals** (D-10, the model part of TP-PM-12 and TP-PM-13): `test_references.py`, `TestReferences` (7 tests).
- **TP-PM-05** (permissions): `test_security.py`, `TestSecurity` (12 tests): reader reads and is refused writes, work items, errors and manager actions; manager actions; manager refused direct edits; no access without a group; data shared across companies; Settings for system administrators only; menus and views per role.
- **Notification destination** (the Stage 03 part of TP-PM-16): `test_notification.py`, `TestFailureNotification` (7 tests). The worker's call at the end of a run, and its tests, come in Stage 05.

### 3.2 Implemented in Stage 04 (2026-11-08, PARTIAL)

38 offline tests use only the seven live-derived fixtures in `tests/fixtures/` (provenance in their README). Pages reach the parsers through `services/reader.py` with `FixtureSite`, a fixture-backed `fetch` function in `tests/common.py`. No test touches the network.

- **TP-PM-06** (parsers): `test_parsers.py`, `TestParsers` (12 tests):
  - the country list (170 countries, counts add up to 4517) and a variant with one country removed (incomplete);
  - Andorra (complete page); Egypt page 1 (page 1 of 11, the next-page link) and page 11 (last page, missing retention, known zeros);
  - partner pages (RoayaTec: 3 of 135 references, identified by link id; DEVONEERS: no references);
  - wrong page types and empty input raise ParseError.
- **TP-PM-08** (country scope):
  - `test_urls.py`, `TestUrlRules` (8 tests): `country_id` in any position; missing, empty, repeated and wrong values rejected; the check needs the raw link; canonical URLs; reference keys; robots.txt rules;
  - `TestParsers`: Anguilla's 3 global links rejected for "missing country_id"; the Andorra page read for Egypt is "unscoped".
- **Ingestion** (`test_ingest.py`, `TestIngest`, 18 tests), including the cases the user named:
  - Andorra ingested twice (and again on a later date) creates no duplicate partner or history row;
  - RoayaTec's 3-of-135 list keeps a seeded reference active and flags the partner;
  - Anguilla is empty only when a complete country list confirms it; without that, or with an incomplete list, or with the country listed with partners, everything is kept and the country is flagged;
  - Egypt: the reader follows the pager and a missing page 2 fails the read; the last page alone, or pages 1 and 11 with a gap, are incomplete and archive nothing.
  It also covers: the raw-URL-to-stored-partner walkthrough; a complete snapshot archiving an unlisted partner; a timeout failing the read with no change; an unknown status card skipped; a page of another country changing nothing; complete and incomplete country lists; a valid empty reference list; and a page of another partner refused.
- **Partly covered:**
  - TP-PM-07: page-type errors and source failures at the reader (a timeout, a missing page) are covered. A login page, a rate-limit page, HTTP errors and truncated markup are not: the synthetic fixtures for them and the page-download module were deferred.
  - TP-PM-13: incomplete snapshots are covered at the ingestion level; the worker path comes in Stage 05.
- **TP-PM-21** (live): a manual sample with curl (9 requests) and a manual parser check on the saved full pages ([live_site_notes.md](live_site_notes.md)). A live run through the module is NOT RUN: the page-download module is deferred.

### 3.3 Implemented in Stage 05 (2026-11-10)

21 tests drive the worker with `FixtureSite` (the seven live-derived fixtures, plus variants made in code from them). Design and results: [resilience.md](resilience.md).

- `test_worker.py`, `TestWorker` (19 tests, time frozen at 2026-11-10 08:00 UTC):
  - **TP-PM-09** (idempotency): `test_repeated_identical_ingestion_creates_nothing_new`.
  - **TP-PM-10** (failure isolation): `test_one_failed_partner_does_not_stop_the_others` (a missing partner page fails one unit with its error row and context; two other partners are stored in the same batch), `test_database_error_in_one_unit_leaves_the_cursor_usable` (a real SQL error after the unit's writes: they are rolled back, the next unit is stored, the cursor works).
  - **TP-PM-11** (country validation): `test_country_mismatch_then_recovery`, `test_genuine_change_in_partner_count_is_no_false_mismatch`, `test_permanent_mismatch_stops_after_the_retry_limit`.
  - **TP-PM-12** (reference validation): `test_reference_mismatch_then_recovery`, and the refresh policy in `test_details_refresh_policy`.
  - **TP-PM-13** (partial snapshots, valid empty scope): `test_failed_or_partial_reads_delete_nothing`, `test_valid_empty_country_is_confirmed_by_the_country_list`, `test_unconfirmed_empty_notice_keeps_the_data`, `test_same_count_with_changed_identities_and_status`.
  - **TP-PM-14** (scheduling): `test_duplicate_scheduling_adds_no_work`; the bounded unit retries `test_unit_retries_are_bounded_with_growing_delays`.
  - **TP-PM-16** (notification): `test_daily_run_retries_failed_units_then_notifies_once`, `test_missing_page_source_keeps_the_queue_and_says_so`, `test_manager_retry_reopens_the_run_and_wakes_the_worker`.
  - **TP-PM-17** (change-aware pulling): `test_details_refresh_policy` (new partner, unchanged card, changed card, no refresh loop, stale details).
  - **The scheduler path:** `test_worker_job_runs_bounded_batches_through_the_scheduler` runs the real `ir.cron._process_job` in test mode (each scheduler commit becomes a savepoint), with a batch size of 1; `test_sync_jobs_are_scheduled` checks the four jobs.
- `test_worker_concurrency.py`, `TestWorkerConcurrency` (2 tests, **TP-PM-14** with real concurrency): two separate database connections claim units at the same time and never get the same one, including after one of them commits; a worker whose transaction ends without a commit releases its unit at once. These tests commit their own small dataset through a separate cursor and delete it afterwards.
- **TP-PM-15** (crash and restart, L3): `scripts/restart_check.sh`, outside the test suite, on the disposable `azk_ee24_test` after the suite ran. It kills the worker's container (SIGKILL) during its second batch and restarts it. Steps and observed SQL state: [resilience.md](resilience.md) section 12.
- **Still not covered:** TP-PM-07's login, rate-limit, HTTP-error and truncated pages (synthetic fixtures and the page-download module deferred), and TP-PM-21's live run through the module.

### 3.4 Implemented in Stage 06 (2026-11-10)

- `test_dashboard.py`, `TestDashboard` (14 tests, website data built by the test: Andes 4, Baltic 4, Caspian 3, Delta 2, Euphrates 1, plus an archived partner, an inactive country and a country without partners):
  - **TP-PM-18** (dashboard data):
    - ranking without filters and the name tie-break, checked against the graph view's own group order: `test_ranking_without_filters_and_tie_order`;
    - filters applied before ranking (Gold; Gold and 2025; 2026; one country; Gold and Silver): `test_filters_apply_before_ranking`;
    - countries with no matching partner take no part: `test_zero_match_countries_take_no_part`;
    - empty result: `test_empty_result_is_labelled`;
    - fewer than 5 and fewer than 10 countries: the few and overlap flags, in the tests above;
    - chart totals: for four filter sets and both cohorts, the totals of `web_read_group` (called as each graph view calls it) equal the matching records, the summaries, the bucket counts and an independent search built from the field values: `test_chart_totals_equal_the_filtered_records`;
    - both charts of a side read the same cohort: `test_same_cohorts_feed_both_charts_of_a_side`;
    - bucket boundaries 4.99, 5, 10.99, 11, 24.99, 25, a known 0 and unknown, with the stored field following new observations: `test_project_size_buckets`;
    - website and demo data never mixed: `test_demo_and_website_data_are_never_mixed`;
    - the sync state, including waiting, last success and the queue for managers: `test_sync_state_shows_waiting_last_success_and_queue`.
  - **TP-PM-19** (access): `test_access_is_enforced_on_the_server` (no group refused; reader without queue or Sync Now; manager with them; the chart query refused without the group) and `test_filter_values_are_validated` (a domain, strings and unknown ids are dropped).
  - Entry point and views: `test_dashboard_is_the_entry_point`, `test_graph_and_pivot_views_load_for_readers`, and `test_template_escapes_website_text` (the template uses `t-esc` only).
- `TestDashboardDemoData` (2 tests): the demo data ranking (12 countries, 47 partners; Top 5 Epsilon 8, Zeta 7, Eta 6, Alpha 5, Iota 5; Bottom 5 Beta, Gamma, Nu 1, Mu 2, Kappa 3) and the handoff walkthrough (Gold and 2025: Epsilon 3 first; its partner list holds 3 records).
- **TP-PM-20** (UI, L6): `scripts/ui_smoke_check.py` drives headless Chrome through the DevTools protocol against `azk_ee24` and saves screenshots. It checks:
  - no asset error;
  - the app opens on the dashboard with four charts;
  - the charts use the dashboard graph view;
  - the demo banner;
  - Gold and 2025 applied;
  - the first country's partner list holds the count shown;
  - with `--sync`: Sync Now queues a run, and the dashboard shows it waiting for a page source;
  - no JavaScript error.
  The country selector, a bar click and the reader role are manual steps (Stage 06 handoff).
- **Fixture sync demonstration:** `scripts/fixture_sync_demo.py`, on `azk_ee24_test`, from saved fixture pages: one country sync, a status change and a reference change, printed before and after.

### 3.5 Implemented in Stage 10 (2026-11-15): the page download and the live check

New automated tests (18), all with mocked responses or saved pages, never the network (Odoo's test framework also blocks real requests):

- `test_http_client.py`, `TestHttpClient`, 13 tests (TP-PM-07 at the download layer):
  - a page with its final URL after a redirect, the request arguments and headers, and the spacing between requests, also across clients;
  - URLs and redirect targets refused by the URL rules (never requested), and endless redirects;
  - login pages (a redirect, a password field);
  - rate limits (HTTP 429, a 503 with Retry-After, a "Too Many Requests" page): the pause and its limits;
  - HTTP errors (only 502, 503 and 504 retried), timeouts, cut-off and slow pages;
  - oversized, empty, non-HTML and 204 answers;
  - the charset and Retry-After parsing.
- `test_http_client.py`, `TestWorkerWithHttpClient`, 3 tests: whole units through the client (Andorra and RoayaTec stored); a login page as a failed unit that keeps the data; a rate limit that stops the batch, keeps the queue and tells the scheduler nothing was done.
- `test_worker.py`: `test_paused_downloads_keep_the_queue_and_say_so` (replaces the "missing page source" test) and the regression `test_units_queued_by_a_unit_are_due_in_the_same_batch` (RF-03).
- `test_parsers.py`: the regression `test_an_empty_card_is_not_a_reference` (RF-04).

TP-PM-21, the bounded live check through the module: `scripts/pm_live_check.py` on the disposable test database (robots.txt read and checked first, the country list, Andorra and one partner page, at most 8 requests, rolled back). Results: [live_site_notes.md](live_site_notes.md) and [test_results.md](test_results.md).

Status after Stage 10: TP-PM-07 and TP-PM-21 PASS; every TP-PM check has automated or live evidence.

## 4. Exercise 2: Dynamic Trial Balance

### 4.1 Fixtures and hand-calculated expectations

All fixtures use a fresh company whose currency is EGP, with Odoo's generic chart of accounts and a calendar fiscal year. They are built from real, balanced journal entries, posted, left in draft or cancelled through Odoo's own methods (`action_post`, then `button_cancel` for the cancelled entry). Each advanced fixture has its own company and test class, so the base numbers stay simple.

The expected numbers are constants in `addons/azk_dynamic_trial_balance/tests/common.py`, written by hand from [calculation_contract.md](calculation_contract.md). Each row reads Debit / Credit / Balance for Initial, Movement and End.

**TB-BASE** (Stage 07's base fixture). Period 2026-01-01 to 2026-01-31. All entries are in the Misc journal, except the revenue entry, which is in the Bank journal.

- Posted 2025-12-31: Bank debit 1,000 / Equity (Capital) credit 1,000.
- Posted 2026-01-10: Expense debit 300 / Bank credit 300.
- Posted 2026-01-20 (Bank journal): Bank debit 500 / Revenue credit 500.
- Draft 2026-01-25: Expense debit 200 / Bank credit 200.
- Cancelled 2026-01-26 (posted, then cancelled): Expense debit 400 / Bank credit 400.
- Posted 2026-02-01: Expense debit 50 / Bank credit 50.

Expected, posted only:

- Bank: Initial 1,000 / 0 / 1,000; Movement 500 / 300 / 200; End 1,200 / 0 / 1,200.
- Expense: Initial 0 / 0 / 0; Movement 300 / 0 / 300; End 300 / 0 / 300.
- Revenue: Initial 0 / 0 / 0; Movement 0 / 500 / -500; End 0 / 500 / -500.
- Equity: Initial 0 / 1,000 / -1,000; Movement 0 / 0 / 0; End 0 / 1,000 / -1,000.
- Total: Initial 1,000 / 1,000 / 0; Movement 800 / 800 / 0; End 1,500 / 1,500 / 0.

Expected with Include Unposted Entries:

- Bank: Movement 500 / 500 / 0; End 1,000 / 0 / 1,000.
- Expense: Movement 500 / 0 / 500; End 500 / 0 / 500.
- Revenue and Equity: unchanged.
- Total: Movement 1,000 / 1,000 / 0; End 1,500 / 1,500 / 0.
- The cancelled and February entries never count.

Expected with one journal (posted only). The journal filter also restricts the opening:

- **Bank journal:**
  - Bank: Initial 0 / 0 / 0, Movement 500 / 0 / 500, End 500 / 0 / 500;
  - Revenue: Movement 0 / 500 / -500;
  - Total: Initial 0 / 0, Movement 500 / 500, End 500 / 500.
- **Misc journal:**
  - Bank: Initial 1,000 / 0 / 1,000, Movement 0 / 300 / -300, End 700 / 0 / 700;
  - Expense: 300 / 0 / 300;
  - Equity: 0 / 1,000 / -1,000;
  - Total: Initial 1,000 / 1,000, Movement 300 / 300, End 1,000 / 1,000.

**TB-X** (cross-year): TB-BASE plus a posted entry on 2025-06-30, Current Assets debit 700 / Revenue credit 700.

- January 2026, posted:
  - Revenue Initial 0 / 0 / 0, because income opens at the fiscal-year start.
  - Current Year Earnings (999999) Initial 0 / 700 / -700, from the 2025 result.
  - Current Assets Initial 700 / 0 / 700.
  - Total Initial 1,700 / 1,700 / 0; End 2,200 / 2,200 / 0.
- February 2026, posted:
  - Bank Initial 1,200 / 0 / 1,200; End 1,150 / 0 / 1,150.
  - Expense Initial 300 / 0 / 300 and Revenue Initial 0 / 500 / -500 (January of the current fiscal year).
  - Current Year Earnings Initial 0 / 700 / -700 (prior years only).
  - Movement: Expense 50 / 0 / 50 and Bank 0 / 50 / -50.
  - Total Initial 2,200 / 2,200 / 0; End 2,200 / 2,200 / 0.
- February 2026 with drafts: the January draft is in the opening.
  - Bank: Initial 1,000, End 950.
  - Expense: Initial 500, End 550.

**TB-Z** (zero activity). January 2026.

- Entries:
  - 2025-12-31: Bank debit 1,000 / Capital credit 1,000;
  - 2026-01-05: Current Assets debit 250 / Bank credit 250;
  - 2026-01-15: Bank debit 250 / Current Assets credit 250.
- Current Assets: Initial 0 / 0 / 0; Movement 250 / 250 / 0; End 0 / 0 / 0. It stays visible with Skip Zero Balance.
- Bank: Initial 1,000 / 0 / 1,000; Movement 250 / 250 / 0; End 1,000 / 0 / 1,000.
- Prepaid Expenses (128000) has no journal items. It is hidden with Skip Zero Balance, and listed with zeros without it.

**TB-C** (currencies). Rates: 1 USD = 50 EGP, 1 EUR = 55 EGP. Account X is Current Assets; every counterpart is on Bank, in EGP.

- 2025-12-20: X debit 1,000 (USD 20) / Bank credit 1,000.
- 2025-12-22: Bank debit 1,650 / X credit 1,650 (EUR -30).
- 2026-01-05: X debit 5,000 (USD 100) / Bank credit 5,000.
- 2026-01-12: Bank debit 2,000 / X credit 2,000 (USD -40).
- 2026-01-18: X debit 3,850 (EUR 70) / Bank credit 3,850.
- 2026-01-25: Bank debit 1,100 / X credit 1,100 (EUR -20).

January 2026, with Show Amount Currency:

- Row (X, USD): Initial 1,000 / 0 / 1,000; Movement 5,000 / 2,000 / 3,000; End 4,000 / 0 / 4,000; Amount Currency USD 60.00.
- Row (X, EUR): Initial 0 / 1,650 / -1,650; Movement 3,850 / 1,100 / 2,750; End 1,100 / 0 / 1,100; Amount Currency EUR 50.00.
- Row (Bank, EGP): Initial 650 / 0 / 650; Movement 3,100 / 8,850 / -5,750; End 0 / 5,100 / -5,100; Amount Currency EGP -5,750.00.
- Total: Initial 1,650 / 1,650; Movement 11,950 / 11,950; End 5,100 / 5,100. Group and total rows have no amount currency.
- Per-currency totals: USD 60.00, EUR 50.00 and EGP -5,750.00, never added together.

Without the option:

- X: Initial 0 / 650 / -650; Movement 8,850 / 3,100 / 5,750; End 5,100 / 0 / 5,100.
- Total: Initial 650 / 650.
- Signed balances and gross movements reconcile between the two modes. The netted Initial totals differ: 1,650 against 650 (D-49).

**TB-A** (analytic). March 2026. Plans A (accounts A1, A2) and B (account B1).

- Lines:
  - Expense debit 1,000 with distribution A1 60% / A2 40%, against Bank credit 1,000 without distribution;
  - Expense debit 200 with the composite key "A1,B1" at 100%, against Bank credit 200.
- Results under the selected policy (whole-item inclusion):
  - filter A1: Expense Movement 1,200 / 0 / 1,200; Bank absent;
  - filter A2: Expense 1,000;
  - filter B1: Expense 200;
  - no filter: Expense 1,200 and Bank credit 1,200, each item once.
- Under the rejected proportional alternative, A1 would give 800 (600 + 200), A2 400 and B1 200. Those numbers are documented, not implemented.

**TB-M** (two companies, both in EGP). January 2026.

- Company 1: 2026-01-10, Bank debit 300 / Capital credit 300.
- Company 2: 2026-01-12, Bank debit 900 / Capital credit 900.
- A report on company 1 shows only the 300, and one on company 2 only the 900.
- A reader of company 1 only is refused company 2.

**TB-R** (restricted access). January 2026. A test record rule hides the journal items of the "Restricted" journal (code RSTR) from one reader.

- 2026-01-10: Expense debit 300 / Bank credit 300 (Misc).
- 2026-01-15: Expense debit 70 / Bank credit 70 (Restricted).
- The restricted reader sees Expense 300 and Bank credit 300; the accountant sees 370.

**TB-H** (hierarchy).

- **Groups:** "1" > "10" > "101" > "1014" > "10140" (levels 1 to 5), and "4" (level 1).
- **Accounts:** Bank 101401 is under "10140", Current Assets 101000 under "101", and Product Sales 400000 and Cash Discount Loss 443000 under "4". Capital has no group.
- **Entries:**
  - 2025-12-31: Bank debit 1,000 / Capital credit 1,000;
  - 2026-01-10: Current Assets debit 400 / Bank credit 400;
  - 2026-01-20: Bank debit 500 / Product Sales credit 500;
  - 2026-01-22: Cash Discount Loss debit 120 / Bank credit 120.
- **Expected, January 2026:**
  - "10140" and "1014" (= Bank): Initial 1,000 / 0; Movement 500 / 520; End 980 / 0.
  - "101", "10" and "1": Initial 1,000 / 0; Movement 900 / 520; End 1,380 / 0.
  - "4": Initial 0 / 0; Movement 120 / 500; End 120 / 500 (both sides).
  - "(No Group)" (Capital): Initial 0 / 1,000; End 0 / 1,000.
  - Total: Initial 1,000 / 1,000; Movement 1,020 / 1,020; End 1,500 / 1,500.
- **Only Parents:** N = 1 shows "1", "4" and "(No Group)", and each level adds the next group down; N = 5 shows all six groups. Grand totals never change with the hierarchy options.

### 4.2 Checks

| ID | Stage | Check | Expected result | Requirements |
|---|---|---|---|---|
| TP-TB-01 | 07 | Wizard validation | Missing or reversed dates, an unauthorized or inactive company, a journal or analytic account of another company, Only Parents without Hierarchy, a level without Only Parents or outside 1-5, Show Amount Currency with Only Parents, blank, over-long or non-code prefixes, unknown option keys and wrongly typed values are refused server-side; the Many2one fields stay single; wizards are private; the buttons validate, then say that the output is not available yet | T-02, T-03, T-07 to T-12, K-02 |
| TP-TB-02 | 07, 08 | TB-BASE posted only | The numbers listed above, exactly. Stage 07: the standard Trial Balance gives them; Stage 08: our engine | T-04, T-14, T-15 |
| TP-TB-03 | 07, 08 | TB-BASE with drafts | The numbers listed above; cancelled and February entries excluded | T-05 |
| TP-TB-04 | 07, 08 | TB-X cross-year | The numbers listed above, for January, February and February with drafts | T-15, A-14 |
| TP-TB-05 | 08 | Date boundaries | Items on Date From and Date To count; items on the day before or after don't; an empty period gives a valid empty report; a negative balance shows on the credit side | T-15 |
| TP-TB-06 | 07, 08 | Prefixes and journal | OR semantics over several prefixes; prefixes with "_", "%" or "\" are refused by validation (D-44), and the engine escapes wildcards anyway; the journal filter also restricts the opening balance (Stage 07: standard report, TB-BASE by journal) | T-08, T-09 |
| TP-TB-07 | 07, 08 | Skip Zero Balance | Equal debit and credit movement stays visible (Stage 07: the standard report lists TB-Z's account); an account with nothing is hidden only when the option is on; with it off, every non-deprecated matching account is listed | T-11, D-12, D-48 |
| TP-TB-08 | 07, 08 | TB-C currencies | The rows, columns and per-currency totals listed above; base amounts reconcile between modes (Stage 07: fixture amounts and the company-currency report) | T-12, D-11, D-49 |
| TP-TB-09 | 07, 08 | TB-A analytic | The whole-item results listed above; composite keys count once; no filter never duplicates (Stage 07: the standard report) | T-10, D-07 |
| TP-TB-10 | 07, 08 | TB-H hierarchy | Levels 1-5, subtotals, "(No Group)", Only Parents for N = 1 to 5, no double counting in totals (Stage 07: group rows and depths of the standard hierarchy) | T-06, T-07, D-13 |
| TP-TB-11 | 07, 08, 09 | Access | User B cannot read, preview or export user A's wizard; a company outside B's companies or not active, a forbidden journal or analytic id, and tampered options are refused; restricted journal items stay invisible (Stage 07: wizard privacy, and TB-M and TB-R on the standard report) | K-02 |
| TP-TB-12 | 07, 08 | Native parity | For TB-BASE, TB-X, TB-Z, TB-C, TB-A, TB-M, TB-R and TB-H with matched options, our Initial, Movement and End debit and credit per account and the totals equal the standard Trial Balance's. Stage 07 checks the standard report against the hand-calculated constants; Stage 08 checks our engine against the same constants | A-14, A-15 |
| TP-TB-13 | 09 | Preview | Opens from the wizard with its options; changing the date or Draft Entries recalculates; the search bar filters lines; folding works; an empty result shows a clear message | T-13, T-16 |
| TP-TB-14 | 09 | PDF (L5) | A real wkhtmltopdf PDF whose text contains the company name, "From ... to ...", the selected filters and the nine column titles; a multi-page sample repeats the header; inspected visually | T-14, T-17 |
| TP-TB-15 | 09 | XLSX (L5) | A real workbook: numeric cells numeric, codes and names as text, no formulas from user text, hierarchy readable, metadata rows present, currencies separate; cell values equal the engine result | T-14, T-18 |
| TP-TB-16 | 09 | Consistency | For the same options on an unchanged database, preview lines, PDF values and XLSX cells are identical | K-01 |
| TP-TB-17 | 08+ | Demo data | Installs with the module: posted and draft entries, several currencies, analytic distributions, and an account-group chart deep enough for levels 1-5 | T-21 to T-23 |

### 4.3 Implemented in Stage 07 (2026-11-15)

Addon `azk_dynamic_trial_balance` 18.0.1.1.0, folder `tests/`. Fixtures and hand-calculated constants are in `tests/common.py`. `native_trial_balance()` runs `account_reports.trial_balance_report` with exactly one active company and the same dates and options, and returns its numbers by line.

- `test_install.py`, 2 tests (Stage 01): the addon is installed; XlsxWriter works.
- `test_wizard.py`, `TestTrialBalanceWizard`, 16 tests (TP-TB-01, part of TP-TB-11):
  - defaults and the always-true Posted Entries;
  - plain, validated option values;
  - single journal and analytic account;
  - the PDF's help texts, word for word;
  - date order;
  - an authorized and active company;
  - a journal or analytic account usable in the company;
  - option combinations, and onchanges in a form;
  - literal code prefixes;
  - untrusted raw options, and no translation warnings;
  - private wizards and prefixes;
  - no access without an accounting group;
  - the entry-point buttons;
  - the menu.
- `test_base_fixture.py`, `TestBaseFixture`, 6 tests (TP-TB-02, TP-TB-03, part of TP-TB-06):
  - TB-BASE is real and balanced, with the right states and journals, and the cancelled entry went through posting;
  - the fiscal year is the calendar year;
  - the hand tables are consistent;
  - the standard report is compared posted only, with drafts, and per journal.
- `test_native_conventions.py`, `TestCrossYearConventions`, 5 tests (TP-TB-04): TB-X in January (fiscal-year start), February and February with drafts; the carry-forward has no journal entry behind it.
- `test_advanced_fixtures.py`, 19 tests, one class per fixture:
  - `TestZeroActivityFixture` (TB-Z);
  - `TestCurrencyFixture` (TB-C: the rates, amounts per currency, reconciliation across groupings, the company-currency report);
  - `TestAnalyticFixture` (TB-A: the distributions, and the standard report for no filter, A1, A2 and B1);
  - `TestMultiCompanyFixture` (TB-M);
  - `TestRestrictedAccessFixture` (TB-R: a record rule hides items from one reader, and the standard report respects it);
  - `TestHierarchyFixture` (TB-H: the five-level chain, our level definition, group rows and Only Parents in the hand tables, and the standard hierarchy's group rows and depths).

Results of `scripts/dev.sh test azk_dynamic_trial_balance`, each on a fresh `azk_ee24_test`:

- Run 1: 1 failure and 2 errors of 47 tests. The three failures were all in the wizard tests: the company check read an inactive company's name, and a test expected a different menu path format. There were also 88 translation warnings. All fixture and standard-report comparisons passed.
- Run 2: 0 failed, 0 errors of 48 tests.
- Run 3, on the final code: 0 failed, 0 errors of 48 tests; 0 warning lines; exit code 0; 289 s.

### 4.4 Implemented in Stage 08 (2026-11-15)

The engine tests sit next to the Stage 07 tests of each fixture, so the standard report and our engine are checked against the same hand-calculated constants on the same data. New files:

- `test_engine_boundaries.py`, `TestEngineBoundaries`, 8 tests: fixture TB-D (dates, reversal, cancelled, draft, overdraft, empty period, rounding).
- `test_engine_access.py`, `TestEngineAccess`, 5 tests: who may run the engine, tampered options, the wizard path, query count.

New engine tests in the Stage 07 classes:

- `TestBaseFixture`: 7;
- `TestCrossYearConventions`: 2;
- `TestZeroActivityFixture`: 2;
- `TestCurrencyFixture`: 3;
- `TestAnalyticFixture`: 2;
- `TestMultiCompanyFixture`: 3;
- `TestRestrictedAccessFixture`: 2;
- `TestHierarchyFixture`: 3.

Total: 85 tests (48 from Stage 07). Commands, results, the scope of the standard-report comparisons and the query counts are in [test_results.md](test_results.md). Status of the checks of 4.2 after Stage 08:

- **PASS:** TP-TB-02 to TP-TB-10 and TP-TB-12.
- **PASS for the calculation, open for the exports (Stage 09):** TP-TB-11.
- **Stage 09:** TP-TB-13 to TP-TB-17.

### 4.5 Implemented in Stage 09 (2026-11-15)

New automated tests (17), all on real data, all compared with the engine result or with hand-calculated constants (102 in total):

- `test_report_outputs.py`, `TestReportOutputs`, 11 tests, on the installed demo company. For each option set (posted only, drafts, hierarchy, parents only, amount currency, analytic, zero filtering, empty result) the preview lines equal the engine rows, the XLSX cells equal the printed lines (codes, numbers, number types), and every PDF row prints exactly the name and formatted cells of one printed line. Also: Bank 1,200 and 1,000 in all three outputs; per-currency totals (USD 60, EUR 50, never 110); the PDF header, filters and columns; the rounding unit printed while the XLSX keeps exact numbers; the repeating table header; the XLSX metadata, number formats, frozen header and absence of formulas; exports following the preview's search and folded groups; the preview's columns, filter component and messages; the wizard's options round trip.
- `test_report_access.py`, `TestReportAccess`, 3 tests, on TB-BASE: an accounting reader can preview and export; employees and billing users get AccessError; tampered options (another company's journal, an unknown key, a wrongly typed value, a non-code prefix, a non-dictionary, another report, an unauthorized company, including through the company list the download route uses) are refused on the preview and on both exports.
- `test_demo_data.py`, `TestDemoData`, 3 tests: the demo company's country, states, currencies, analytic items and five-level groups; its Bank example through the engine (1,200 and 1,000); a second run of the demo function creates nothing.
- Changed: `test_wizard.py` (the buttons now return the report and download actions with the wizard's options) and `test_engine_access.py` (another user's wizard cannot be previewed or exported).

PDFs in unit tests: `tests/common.py` `capture_wkhtmltopdf` replaces `_run_wkhtmltopdf` with a stub that records the HTML documents, which are exactly what the PDF prints. Odoo's own `account_reports` tests replace it too. A real wkhtmltopdf started from a unit test made no progress in the first Stage 09 run, and an `HttpCase` makes Odoo build every asset bundle first. Real PDFs are therefore produced and read back on the running server.

Browser and server check `scripts/tb_preview_smoke_check.py` (headless Chrome, `azk_ee24`, demo company): the wizard, the Preview, Draft Entries, the search, the hierarchy with folding, the PDF and XLSX buttons, a short and a multipage PDF rendered to PNG for visual inspection, the empty state, the download route with tampered options and without a session, and the eight option sets through the real route (PDF text with PyMuPDF, XLSX cells with openpyxl, both against the engine).

Status of the checks of 4.2 after Stage 09 (results in [test_results.md](test_results.md)):

- **PASS:** TP-TB-01 to TP-TB-17, with TP-TB-11 now covering the exports and the download route.
- **NOT RUN:** the analytic dropdown in the browser (Analytic Accounting is off on `azk_ee24`); custom fiscal years and branch companies (Stage 10, D-60).

### 4.6 Implemented in Stage 10 (2026-11-15)

New automated tests (12), with hand-calculated numbers and the standard report on the same data:

- `test_fiscal_years_and_branches.py`, `TestFiscalYearFixture` (TB-F), 3 tests: a July-to-June fiscal year from the company setting and from an `account.fiscal.year` record; June 2026, July 2026 and 15 June to 15 July 2026, against the hand-calculated numbers and the standard report.
- `test_fiscal_years_and_branches.py`, `TestBranchFixture` (TB-B), 6 tests:
  - a root company and its branch sharing a chart and a journal; each report covers exactly its company and equals the standard report;
  - the standard report adds up active branches, ours does not (D-16);
  - a branch-only user gets the full branch report (the regression of RF-06), and the standard report shows that user nothing;
  - a branch ignores its root's fiscal-year records.
- `test_native_reports.py`, `TestNativeReportsUnchanged`, 2 tests: the standard Trial Balance and General Ledger XLSX equal, cell by cell, those of the original Enterprise methods; the standard PDF uses none of our templates.
- `test_demo_data.py`: the regression `test_a_new_demo_company_installs_no_localization` (RF-07).

Also run in Stage 10: the vendor's `TestTrialBalanceReport` and `TestAccountReportAnnotationsExport` with our addon installed; `scripts/tb_analytic_smoke_check.py` (the analytic selector, recalculation, exports and tampered downloads as a read-only accountant, in a browser, on a disposable server with Analytic Accounting on); `scripts/tb_benchmark.py`.

Status after Stage 10: TP-TB-01 to TP-TB-17 PASS, including the analytic dropdown in a browser, custom fiscal years and branch companies.

## 5. Acceptance (Stage 11) and general checks

| ID | Check | Expected result | Requirements |
|---|---|---|---|
| TP-G-01 | Each addon installs alone into a fresh database of edition `enterprise-20241208`, then upgrades | No errors or warnings | G-11, P-01, T-01 |
| TP-G-02 | Full custom test suite | All tests pass, with more than 0 tests collected | G-10, G-11 |
| TP-G-03 | Partner Monitor on the Community baseline (optional) | Installs and passes, proving it has no Enterprise dependency | A-17 |
| TP-G-04 | README instructions followed literally from a fresh clone | The documented commands work as written | G-02 to G-05, T-19, T-20 |
| TP-G-05 | Manual demo script (user) | Dashboard, sync status, TB preview, PDF and XLSX checked in a browser; recorded as the user's results | G-11 |

Stage 11 results (2026-11-16, [acceptance_results.md](acceptance_results.md)):

- TP-G-01: PASS, each addon alone and then updated, 0 warnings.
- TP-G-02: PASS, 261 of 261 tests (147 and 114).
- TP-G-03: partly run. The Partner Monitor installed with its demo data on the Community edition while checking AC-02; its tests were not run there.
- TP-G-04: the README does not exist yet (Stage 12). The quick start in [environment.md](environment.md), followed literally from a clean export, PASSED after fixing AC-01.
- TP-G-05: NOT RUN (the user's own check).

## 6. Commands

Run in `solution/` with Git Bash (see [environment.md](environment.md)):

```text
scripts/dev.sh test azk_odoo_partner_monitor
scripts/dev.sh test azk_dynamic_trial_balance
scripts/dev.sh test azk_dynamic_trial_balance /azk_dynamic_trial_balance:TestNativeParity
scripts/dev.sh test account_reports /account_reports:TestTrialBalanceReport   # vendor regression check
scripts/dev.sh clean-install                                                   # acceptance install
scripts/dev.sh shell azk_ee24 < scripts/tb_demo_data_counts.py                 # demo record counts (read-only)
python scripts/tb_preview_smoke_check.py OUTPUT_DIR    # Stage 09 browser and download check (PM_UI_LOGIN, PM_UI_PASSWORD)
scripts/dev.sh shell azk_ee24_test < scripts/pm_live_check.py     # Stage 10 bounded live check (disposable DB, rolled back)
scripts/dev.sh shell azk_ee24_test < scripts/pm_benchmark.py      # Stage 10 Partner Monitor benchmark (rolled back)
scripts/dev.sh shell azk_ee24_test < scripts/tb_benchmark.py      # Stage 10 Trial Balance benchmark (rolled back)
scripts/dev.sh test azk_dynamic_trial_balance /account_reports:TestTrialBalanceReport,/account_reports:TestAccountReportAnnotationsExport
scripts/dev.sh clean-install azk_odoo_partner_monitor,azk_dynamic_trial_balance --without-demo
python scripts/tb_analytic_smoke_check.py OUTPUT_DIR  # Stage 10, against a temporary server of a disposable DB (PM_UI_URL)
```

One Stage 09 class can be run alone, for example:

```text
scripts/dev.sh test azk_dynamic_trial_balance /azk_dynamic_trial_balance:TestReportOutputs
```

Test class names are provisional; Stage 03 onward records the real ones (section 3.1). One Stage 03 test can be run alone, for example:

```text
scripts/dev.sh test azk_odoo_partner_monitor /azk_odoo_partner_monitor:TestStatusHistory.test_silver_gold_gold_records_initial_then_one_promotion
```
