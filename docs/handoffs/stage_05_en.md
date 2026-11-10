# Stage 05 handoff: resumable synchronization

Date: 2026-11-10. Edition: `enterprise-20241208` (port 8071).

- **Stage 05: DONE for the worker, tested offline.** The scheduled jobs, the worker, retries, validation, overlap protection and failure notes are built, and their tests pass with the saved live-derived pages.
- **Stage 04 stays PARTIAL.** The page-download module (`services/http_client.py`) and the synthetic fixtures remain deferred, so no live sync has run. Until the module exists, the worker keeps queued work and shows that it is waiting.

The full design and evidence are in [../resilience.md](../resilience.md).

## What was built

- **`models/worker.py`** (AbstractModel `azk_odoo_partner_monitor.worker`), the sync engine:
  - `_cron_daily_discovery`: creates a run with a country-list unit; nothing if one is already queued.
  - `_cron_process_queue`: one bounded batch per scheduler call (20 units, 60 s by default, system parameters `azk_odoo_partner_monitor.worker_batch_size` and `..._worker_time_budget`), then `_notify_progress`.
  - `_claim_next`: one unit at a time, `SELECT ... FOR NO KEY UPDATE SKIP LOCKED`; a REPEATABLE READ serialization failure ends the batch.
  - `_run_unit`: one savepoint per unit; `_record_unit_failure` stores the error row, the try and a log line after the rollback.
  - `_unit_country_list`, `_unit_country_partners`, `_unit_partner_details`: read through `services/reader.py`, store through `models/ingest.py`.
  - `_cron_validate_countries`, `_cron_validate_references`: queue flagged (and stale) targets, de-duplicated, with bounded retries.
  - `_get_page_source`: the integration point of the deferred page-download module (returns None today).
- **`data/ir_cron.xml`:** four jobs: Daily Discovery (daily, first run 02:00 UTC), Sync Worker (10 minutes), Country Validation and Reference Validation (6 hours).
- **Model changes:**
  - work items: `_mark_done`, `_mark_failed_attempt` (5 tries; 15, 30, 60, 120 minutes apart), `_trigger_worker`; "Retry" reopens the run and wakes the worker.
  - runs: `_queue_full_sync`, `_finalize` (done, partial or failed; one note per run), `_set_waiting` and `waiting_reason`.
  - countries and partners: expected, found, previous and stored counts, the validation outcome, the retry count and time, "Retries Exhausted"; partners also `active_reference_count`, `details_synced_at` and `listing_fingerprint`.
  - ingestion: the validation bookkeeping, the details-refresh policy (`_observe_card`, D-31), and archiving the partners of a country missing from a complete list.
- **Views:** validation fields and filters ("Validation Mismatch", "Retries Exhausted"), the waiting banner and filter on runs, unit results on work items.
- **Decisions:** D-30 to D-36 in [../assumptions.md](../assumptions.md) (A-20 is superseded by D-30).

## The fetch(url) contract (from services/reader.py)

- **Signature:** `fetch(url) -> (final_url, html)`.
- **What it is asked for:** absolute `https://www.odoo.com` URLs that the reader has already checked against robots.txt (`urls.fetch_allowed`). A refused URL raises `reader.NotAllowedError` before `fetch` is called. The reader asks for:
  - the country list `https://www.odoo.com/partners?country_all=1`;
  - a country listing `https://www.odoo.com/partners/country/<id>` and the next pages its pager links to;
  - a partner page, at the partner's canonical URL.
- **Return value:** a tuple.
  - `final_url`: the URL after redirects. The parsers rely on it: a listing that lands on another country's page is "unscoped", and a partner page must be about the requested partner.
  - `html`: the page text, already decoded (str).
- **Exceptions:** it must RAISE on any failure: a timeout, a connection error, an HTTP error status, a login or rate-limit page, or anything unexpected. It must never return an empty or substitute page instead. The reader catches nothing. The exception reaches the worker's savepoint for that unit, which records a failed try: an error row with the URL, a try count and the backoff. Nothing is stored for that scope.
- **Integration point:** `models/worker.py`, `PartnerMonitorWorker._get_page_source()` must return the callable.
  - `_cron_process_queue` calls it once per batch.
  - `_run_unit` wraps it (`_UrlTracker`) to record the last URL for error context.
  - With None, the worker attempts nothing (D-33).
- **Still expected from the future module** (Stage 04 plan): English pages (D-26), a polite delay, short timeouts so a batch stays within the scheduler's time limit, and limited retries.
- **Test double:** `tests/common.py`, `FixtureSite`. It returns saved pages by URL, raises `LookupError` for an unsaved URL (like a failed download), and can raise a chosen exception for a URL.

## Worker test results (automated, today, on the final code)

- `scripts/dev.sh test azk_odoo_partner_monitor`, fresh `azk_ee24_test`, final code: **PASS**, "0 failed, 0 error(s) of 113 tests", 0 warning or error lines in the log, exit code 0, 1 min 58 s. That is the 91 earlier tests plus 22 new ones.
- New tests (`tests/test_worker.py`, 20; `tests/test_worker_concurrency.py`, 2), all PASS. The ones you asked about:
  - **One failed partner does not stop unrelated work** (`test_one_failed_partner_does_not_stop_the_others`). In one batch, IT SYS's page download failed: its unit stayed pending with 1 try and a 15-minute backoff, and an error row recorded the run, the unit, the partner, the URL and the error type. RoayaTec (3 references) and DEVONEERS (matched) were stored in the same batch.
  - **A real SQL error inside one unit** (`test_database_error_in_one_unit_leaves_the_cursor_usable`). The unit's writes were rolled back with its savepoint, the next unit was stored, and the cursor still answered a query.
  - **Two workers racing** (`test_two_workers_never_get_the_same_unit`, two real database connections). They never got the same unit, also after one of them committed (the REPEATABLE READ serialization case). Each page was read once.
  - **Abandoned work** (`test_a_crashed_worker_releases_its_unit`). A transaction that ends without a commit releases its unit at once.
  - **The other required cases:** repeated identical ingestion, reference mismatch then recovery, country mismatch then recovery, a genuine count change, the same count with changed identities and status, failed and partial reads deleting nothing, a valid and an unconfirmed empty country, bounded unit retries (15, 30, 60, 120 minutes, then failed with one note), a permanent mismatch stopping after 5 re-scrapes, duplicate scheduling, the details-refresh policy (no loop, 7-day re-reads), a missing page source, a manager's retry, the real scheduler loop (`_process_job` in test mode, one unit per call) and the four job definitions.
  - **Regression:** `test_flag_without_a_retry_count_is_still_validated`.
- **Earlier runs** (kept as evidence of the fixes): 112 of 112 on the first code; 113 of 113 after the fixes below. The final run came after two clean-ups (one validation run per job call, an unused import).
- `scripts/dev.sh update azk_odoo_partner_monitor` on `azk_ee24` (the development database): PASS, exit 0, 0 warning or error lines. A read-only check afterwards:
  - version 18.0.1.3.0;
  - the four jobs are active, and the first daily discovery is due on 2026-11-11 at 02:00 UTC;
  - 0 runs and 0 units;
  - no NULL retry count;
  - the login page answers HTTP 200 on port 8071.

## Restart check (TP-PM-15, run on the final code)

Command: `scripts/restart_check.sh`, after the suite, on `azk_ee24_test`, with a batch size of 2. Full numbers are in [../resilience.md](../resilience.md) section 12.

1. **Seeded and committed:**
   - run 49 with unit 259 (Egypt's listing, 4 of 5 tries used; its pages 2 to 10 are not saved);
   - run 50 with units 260 (Andorra), 261 (Anguilla), 262 (RoayaTec's page) and 263 (DEVONEERS' page).
2. **Batch 1 committed:**
   - unit 259 failed its last try; run 49 ended `failed` and posted one note;
   - unit 260 finished, and BDR GROUP SLU was promoted from Ready to Silver.
3. **Batch 2 was interrupted:**
   - unit 261 finished inside the open transaction;
   - the read of unit 262's page blocked;
   - meanwhile another session could claim only unit 263, because 261 and 262 were locked.
4. **`docker kill` (SIGKILL) at 10:09:38 UTC**, exit status 137.
   - No worker session was left in the database.
   - Units 261, 262 and 263 became claimable.
   - The committed state was unchanged: 261 to 263 pending with 0 tries, and the earlier Anguilla partner still active.
5. **Restart in a new container.**
   - The scheduler counted the killed call as one time-out.
   - **Units 261 and 262 resumed** (the interrupted batch, replayed), then **unit 263**. Run 50 ended `done`.
   - Only those units' pages were read: Anguilla's listing and the country list confirming it, RoayaTec and DEVONEERS. Egypt and Andorra were not read again.
6. **Checks, 12 of 12 PASS. Nothing was duplicated:**
   - unit 259 still failed with 5 tries and 1 error row;
   - BDR GROUP SLU's history is exactly "initial, promoted";
   - 13 partners have 14 history rows;
   - RoayaTec has 3 references, not 6;
   - run 49 has one note and one Inbox notification;
   - run 50 has no note;
   - no email was queued;
   - no unit is pending.

## Outstanding: the live sync check (NOT RUN)

- No live sync has run, through the worker or otherwise. The worker has only read the saved live-derived pages.
- **Blocker:** the page-download module is deferred (Stage 04 PARTIAL), so `_get_page_source()` returns None.
- **Steps once the module exists:**
  1. Return its `get` method from `_get_page_source()`.
  2. Add its mocked-response tests (a success, a timeout, an HTTP error, a login and a rate-limit page).
  3. On the disposable `azk_ee24_test`, queue one small country (for example Andorra) and one partner page, run one worker batch, and record the requests, the stored rows and the timings.
  4. Check the unit durations against the scheduler's time limit (resilience.md, section 13).
- Until then, TP-PM-21 (bounded live smoke) and the live parts of P-02, P-03, P-04 and P-22 stay open.

## Problems found and fixed during the stage

- **NULL retry counts** (found by the first restart check). New integer fields had no default, so the database held NULL. The validation jobs selected `reprocess_attempts < 5`, which never matches NULL, so rows flagged before an upgrade would never have been re-scraped.
  - Fix: defaults of 0 (filled on upgrade, confirmed on `azk_ee24`), and the jobs now select "not exhausted".
  - Regression test: `test_flag_without_a_retry_count_is_still_validated`.
- **An ERROR line in the restart check.** Importing the tests' fixture helpers inside `odoo shell` made Odoo log "Importing test framework ... when not running in test mode". The script now declares test mode around that one import; the final run logged no error.
- **Two drafts were corrected before any run:**
  - a test expected a retried Andorra unit to end its run, but that unit queues its partners' pages;
  - the first restart scenario would have queued pages with no saved fixture.

## Open issues and limits

- No live sync (above).
- One country listing is one unit. The time budget is checked between units, so a very long country could exceed the scheduler's time limit; page-level checkpoints are the next step if live timings require them (resilience.md, section 13).
- A crash rolls back the error rows of its batch; the server log keeps the lines written before it.
- Two workers writing the same partner can deadlock; that unit fails and is retried.
- `azk_ee24` (the development database) now has the four jobs. At 02:00 UTC the daily job will queue a run. With no page source the run waits, and the configured user (the administrator, whose preference is email) gets one note. With no mail server, the queued email cannot leave.

## Changed files

- **New:**
  - `addons/azk_odoo_partner_monitor/models/worker.py`, `data/ir_cron.xml`;
  - `tests/test_worker.py`, `tests/test_worker_concurrency.py`;
  - `scripts/restart_check.sh`, `scripts/restart_check.py`;
  - `docs/resilience.md`, this handoff, `docs/ai/stage_05.md`.
- **Updated in the addon:**
  - `models/common.py`: validation states, retry limits, `retry_delay`;
  - `models/country.py` and `models/partner.py`: validation fields, `_record_validation`, `_record_reference_validation`, `_request_details_refresh`, the previous counts, "Mark for Re-scrape" resets the budget;
  - `models/work_item.py`: `_mark_done`, `_mark_failed_attempt`, `_trigger_worker`, Retry reopens the run;
  - `models/sync_run.py`: `_queue_full_sync`, `_finalize_finished`, `_finalize`, `_set_waiting`, `_post_note`, a longer failure note;
  - `models/ingest.py`: the validation bookkeeping, `_observe_card`, archiving with the country;
  - `services/parsers.py`: `PartnerCard.metrics_fingerprint`;
  - `tests/common.py`: `ALL_PAGES` and page variants made in code;
  - `models/__init__.py`, `tests/__init__.py`, the three view files, and the manifest (18.0.1.3.0).
- **Updated docs:** STATE, architecture (5.12), assumptions (A-20, D-30 to D-36), requirements matrix, test plan (3.3), `ai/README.md`.

## Comprehension questions

1. Why does a worker killed in the middle of a batch never leave a unit claimed forever, even though no lease or owner is stored on the work item?
2. A failed unit's error row is written after `ROLLBACK TO SAVEPOINT`, not inside the savepoint. What would be lost the other way round, and what is still lost when the whole process dies?
3. Why does the card's metrics hash compare a listing card with the previous listing card, and not with the values stored from the partner's own page?

## Next stage

Stage 06, the Partner Monitor dashboard. The live sync still waits for Stage 04's page-download module.
