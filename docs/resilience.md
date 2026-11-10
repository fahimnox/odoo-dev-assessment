# Resilience of the Partner Monitor sync

_Written 2026-11-10 in Stage 05. Code: `models/worker.py` (the engine), `models/work_item.py`, `models/sync_run.py`, `models/ingest.py`, `models/country.py`, `models/partner.py` and `data/ir_cron.xml`, all in `addons/azk_odoo_partner_monitor/`. Tests: `tests/test_worker.py` and `tests/test_worker_concurrency.py`. Restart check: `scripts/restart_check.sh` with `scripts/restart_check.py`._

## 1. Status

- The scheduled jobs, the worker and the failure handling are built and tested with the saved live-derived pages.
- No live sync has run. The page-download module is still deferred (Stage 04 PARTIAL). Until it exists, `worker._get_page_source()` returns nothing, and the worker keeps every queued unit and marks the run as waiting (section 11).
- Observed results are in section 12; the open live check is in section 13.

## 2. The jobs

Four scheduled actions (`data/ir_cron.xml`, `noupdate`), all running as the superuser like every Odoo cron, all calling `azk_odoo_partner_monitor.worker`:

- **Daily Discovery** (every day, first run at 02:00 UTC): `_cron_daily_discovery` creates a run with one `country_list` unit and wakes the worker. It never reads a page. If a country list is already queued it creates nothing.
- **Sync Worker** (every 10 minutes, and woken on demand by `ir.cron._trigger()`): `_cron_process_queue` processes one bounded batch per call. It is the only job that reads pages.
- **Country Validation** (every 6 hours): `_cron_validate_countries` queues one listing unit per flagged country whose retry is due (P-19).
- **Reference Validation** (every 6 hours): `_cron_validate_references` queues one partner-page unit per flagged partner whose retry is due (P-21), plus the pages read more than 7 days ago (at most 200 per call).

Django analogy: the producers are like Celery beat tasks that only enqueue, and the worker is the only consumer. The queue is a normal table (`work.item`), and the broker is Odoo's own scheduler. No Celery or Redis is needed: the scheduler already gives bounded calls, a commit after each call and one running copy of each job.

## 3. The unit of work

One work item is one unit. Its kind decides what it reads:

- `country_list`: the all-countries page. It records the countries and their counts. A complete list (the counts add up to the "All Countries" total) deactivates the countries it no longer shows and archives their partners (P-23). Then it queues one `country_partners` unit per active country.
- `country_partners`: every listing page of one country, following the pager. It records the cards, then validates the snapshot (D-28). Partners whose own page was never read get a `partner_details` unit in the same run. When the page shows the no-partners notice, the unit also reads the country list, to confirm the empty country (D-27).
- `partner_details`: one partner's page: its values and its reference list (P-20).

Units are queued with `work_item._enqueue`. A partial unique index allows one pending unit per (kind, target), so work queued twice exists once.

## 4. Transactions, savepoints and the commit boundary

What the pinned 18.0 scheduler does (`odoo/addons/base/models/ir_cron.py`, read again in Stage 05):

- `_acquire_one_job` locks the job's `ir_cron` row with `FOR NO KEY UPDATE SKIP LOCKED`, so one job runs once at a time per database.
- `_run_job` calls the job up to 10 times (`MAX_BATCH_PER_CRON_JOB`). Before each call it inserts an `ir.cron.progress` row and commits. After each call it commits again. If the call raises, `_callback` rolls back and re-raises.
- With work left and progress reported (`_notify_progress(done, remaining)`), the next call starts at once; after 10 calls the job stays ready and runs again soon. A call that reports nothing done counts as finished, and the job waits for its next interval or trigger.

What our code does:

```text
scheduler (ir.cron._run_job)        worker._cron_process_queue (one call = one batch)
  INSERT progress row; COMMIT
  call 1 -------------------------> claim unit A (row lock)  SAVEPOINT  work  RELEASE
                                    claim unit B (row lock)  SAVEPOINT  error
                                                             ROLLBACK TO SAVEPOINT
                                    record B's failure: error row, try count, log line
                                    finalize runs with no pending unit (note if needed)
                                    _notify_progress(done=2, remaining=n)
  COMMIT   <- the durability point: A done, B's failure, notes; row locks released
  INSERT progress row; COMMIT
  call 2 -------------------------> ...
```

- **Our code never commits.** The scheduler's commit after `_cron_process_queue` returns is the only point that makes work durable. A batch is at most `max_units` units (system parameter `azk_odoo_partner_monitor.worker_batch_size`, default 20) and starts no new unit after `time_budget` seconds (`azk_odoo_partner_monitor.worker_time_budget`, default 60).
- **One savepoint per unit** (`worker._run_unit`): any exception rolls back that unit's writes only. Odoo's flushing savepoint also clears the ORM cache, so no stale value survives. The cursor stays usable, and the batch goes on with the next unit (P-05). A test makes a real SQL error inside a unit and runs a query afterwards.
- **A savepoint does not make anything durable.** It only limits what a rollback undoes.
- **Failures are recorded after the rollback** (`worker._record_unit_failure`), in the same transaction: a `sync.error` row with the run, unit, country or partner, URL, error type, message and a short trace; one counted try on the unit; and a WARNING line in the server log. These rows are committed with the rest of the batch. Errors are never swallowed: each one is stored, counted and logged.
- **If the process dies before the commit**, the whole batch is rolled back, including its error rows. The log lines already written remain in the server log. The batch's units are pending again and run again later (section 6).
- **No explicit commit in model methods.** Only the restart check's setup phase (a test harness, `scripts/restart_check.py`) commits, to prepare its data.

## 5. Claims, overlap and abandoned work

- **The claim** (`worker._claim_next`) is one SQL statement: the next due pending unit, in the order country list, countries, partners, `FOR NO KEY UPDATE SKIP LOCKED`, one at a time. A unit locked by another worker's open transaction is skipped, so two workers never process the same unit. Odoo 18 has no ORM helper for this lock; the SQL is built with `odoo.tools.SQL` and parameters.
- **The lock lasts until the transaction ends**: the scheduler's commit, or the rollback of a crashed process, when PostgreSQL drops the dead connection's locks. A claim never outlives its transaction, so no lease or stale-claim cleanup is needed. The abandoned unit is simply pending again.
- **Snapshot isolation.** Odoo runs transactions in REPEATABLE READ. If another worker committed the next unit after this transaction began, PostgreSQL refuses to lock it ("could not serialize access"). The claim runs in its own savepoint, catches that error, and ends the batch; the next batch sees the committed state.
- **Duplicate scheduling.** The daily job and "Sync Now" create nothing while a country list is queued (`sync_run._queue_full_sync`); two transactions racing are settled by the unique index, and the loser's run and unit are rolled back together in a savepoint. The validation jobs skip a target whose unit is already pending, without using a retry.
- **Residual risk.** Two workers on different units that write the same partner (its listing and its own page) wait for each other's row locks. A deadlock or serialization error then fails one unit, which is retried.

## 6. Idempotency and replay

- Every write is keyed on the website's own ids, with database uniqueness (Stage 03): a replayed observation updates the same partner.
- Status history gets a row only when the status changes (D-09), and an observation older than the last one is ignored (D-21).
- References follow D-10: a new active row only for a key without an active row; only a complete list closes rows.
- So repeating a unit creates nothing new. After a crash, only the interrupted batch runs again; committed batches are never repeated, because their units are done (TP-PM-15 below).

## 7. Retries and backoff (models/common.py)

- **Failed units**: at most 5 tries. After try n the unit waits `retry_delay(n)`: 15, 30, 60 and 120 minutes, doubling and never more than 24 hours. After the 5th try the unit is `failed` and stays visible. A manager's "Retry" gives it a fresh budget, reopens its run and wakes the worker; the run is not notified a second time.
- **Validation re-scrapes**: a new mismatch sets the flag with a fresh budget, due at once. Each re-scrape the validation job queues uses one try and pushes the next one back by the same delays. A match clears the flag and the count. A mismatch that persists stops after 5 re-scrapes; it stays flagged and is shown as "Retries Exhausted". "Mark for Re-scrape" starts a new budget.
- **No tight loop**: the validation jobs run every 6 hours and only queue due targets; a worker call without progress reports nothing done, and the scheduler waits for the next interval.

## 8. Validation bookkeeping

- **Countries:** expected count `total_partner_count` (read on the country's own listing), found `snapshot_partner_count`, prior `previous_partner_count`, outcome `validation_state` (matched or mismatch) and `validated_at`, plus the retry fields.
- **Partners:** expected `total_references_count`, found on the page `snapshot_reference_count`, stored `active_reference_count`, prior `previous_references_count`, outcome `reference_validation_state` and `details_synced_at`, plus the retry fields.
- **A genuine change is not a false mismatch.** The expected count is read on the same pages as the partners, so a real change of the count arrives with the matching snapshot. A test drops one partner and the count from 2 to 1: matched, previous count 2.
- **A matching count proves little.** Snapshots compare identities: a test keeps the count at 2 while one partner leaves, another arrives and a third is promoted. Partner pages are also re-read at least every 7 days.

## 9. Change-aware pulling (P-08.3)

- The live site sends no `ETag` or `Last-Modified` header (Stage 04 live sample), so there are no conditional requests and no 304 handling. A 304 would only be acceptable with a known-good stored snapshot; that case cannot arise with this site.
- Listing pages are read daily: they are the discovery source, and a country count alone cannot reveal status, metric or reference changes.
- A partner's own page is read only when:
  - the partner is new (same run);
  - its card changed: the hash of retention rate, average and largest project size and reference count (`PartnerCard.metrics_fingerprint`) differs from the last listing read. That sets `to_reprocess_references`, and the reference-validation job queues the page;
  - it is flagged after a mismatch;
  - it was read more than 7 days ago.
- **No self-triggering loop:** the hash compares a card with the previous card. Reading the partner page never changes it, so a page whose values differ from its card does not trigger another read.

## 10. Failure notification (P-07)

- When a run ends `partial` (some units failed) or `failed` (no unit succeeded), `sync_run._finalize` posts one internal note on the run's chatter for the configured user (D-08). It holds the counts, the failed scopes with their last error, the retry policy and the recovery actions. `notified_at` prevents a second note, also after a manager's retry.
- A run that waits for a page source gets one "waiting" note (section 11).
- Tests use Odoo's mail mocks and an Inbox user, so no email leaves the test.

## 11. When the page source is missing

- `worker._get_page_source()` is the integration point of the deferred page-download module. It returns None today.
- The worker then attempts nothing: units stay pending with no try counted, no error row and no lost work. The open runs get `waiting_reason` ("no page source is available ..."), shown as a banner on the run and filterable as "Waiting". The configured user gets one note per run. Each worker call logs a WARNING, and reports no progress, so the scheduler waits for the next interval.
- The daily job adds nothing while the country list is still queued, so waiting runs do not pile up.

## 12. Observed results (2026-11-10, edition `enterprise-20241208`)

### Automated tests

- `scripts/dev.sh test azk_odoo_partner_monitor` on the final code, in a fresh `azk_ee24_test`: **PASS**, "0 failed, 0 error(s) of 113 tests", 0 warning or error lines in the log, 1 min 58 s. That is 91 earlier tests plus 22 new ones (20 in `TestWorker`, 2 in `TestWorkerConcurrency`). Test names per requirement: [test_plan.md](test_plan.md) 3.3.
- Earlier runs on earlier code: 112 of 112 (first version), then 113 of 113 (after the two fixes in section 14). The final run followed two small clean-ups (one validation run per job call, an unused import).

### Restart check (TP-PM-15)

How to run it: `scripts/dev.sh test azk_odoo_partner_monitor` (creates the disposable database), then `scripts/restart_check.sh`. The script refuses any database whose name does not end in `_test`. Final run, 10:08 to 10:10 UTC, output kept privately in `<kit-root>/runtime/logs/stage05_restart_check_run3.log`.

**Setup (committed).** Batch size 2; failure notes go to an Inbox user, so no email can be queued. The pages are the saved fixtures, with BDR GROUP SLU shown as Silver on Andorra's listing (a variant made in code).

- Run 49: unit 259, Egypt's listing, with 4 tries already used. Its pages 2 to 10 are not saved, so it fails again.
- Run 50: units 260 (Andorra listing), 261 (Anguilla listing), 262 (RoayaTec's page) and 263 (DEVONEERS' page).

**Batch 1, committed:**

- unit 259 failed its 5th and last try; run 49 ended `failed` and posted one note;
- unit 260 finished: BDR GROUP SLU was promoted from Ready to Silver.

**Batch 2, interrupted:**

- unit 261 finished inside the open transaction: Anguilla confirmed empty, an earlier Anguilla partner archived;
- then the read of RoayaTec's page blocked.

While it was blocked:

- the database showed batch 1's results only;
- the earlier Anguilla partner was still active;
- two worker sessions were "idle in transaction";
- a `FOR NO KEY UPDATE SKIP LOCKED` probe from another session could claim only unit 263 (261 and 262 were locked).

**Kill.** `docker kill` at 10:09:38 UTC; the container exited with 137 (SIGKILL).

- Right after, no session of the worker was left in the database.
- The probe could claim units 261, 262 and 263: PostgreSQL had rolled back the batch and dropped its locks.
- The committed state was unchanged: 259 failed with 5 tries, 260 done, 261 to 263 pending with 0 tries.

**Restart.** A new container ran the same job.

- The scheduler's own bookkeeping counted the killed call as one time-out (`timed_out_counter` 1) and ran the job.
- Batch 1 replayed units 261 and 262. Batch 2 ran unit 263. Run 50 ended `done`, without a note.
- The pages read after the restart were only those of Anguilla (its listing and the country list that confirms it), RoayaTec and DEVONEERS. Egypt's and Andorra's pages were not read again.

**Checks after the restart, 12 of 12 PASS:**

- unit 259 still failed with 5 tries and 1 error row (not run again);
- BDR GROUP SLU's history is exactly "initial, promoted";
- the 2 Andorra partners exist once;
- units 261 and 262 are done with 0 tries: the killed attempt left no trace;
- the earlier Anguilla partner is archived, without a history row;
- RoayaTec has 3 references, not 6;
- 13 partners have 14 history rows (13 initial, 1 promotion);
- run 49 has exactly one note and one Inbox notification;
- run 50 has no note;
- no unit is pending;
- no email was queued.

### Development database

`scripts/dev.sh update azk_odoo_partner_monitor` on `azk_ee24`: PASS, exit 0, 0 warning or error lines (1 min 20 s). A read-only check afterwards:

- version 18.0.1.3.0;
- the four jobs are active, and the first daily discovery is due on 2026-11-11 at 02:00 UTC;
- 0 runs and 0 units;
- no NULL retry count: Odoo filled the new columns with their default;
- the login page answers HTTP 200 on port 8071.

## 13. Limits and open checks

- **No live sync yet.** The worker has only run on saved pages. A bounded live run needs the page-download module (Stage 04).
- **Unit duration.** The time budget is checked between units. One country unit reads up to 60 listing pages (`reader.MAX_LISTING_PAGES`), each bounded by the future module's timeouts. In multi-process mode the scheduler kills a call that exceeds `limit_time_real_cron` (or `limit_time_real`, 120 s by default). A unit that always runs longer would be replayed until the scheduler counts 3 time-outs and marks the job failed. Page-level checkpoints are the next step if live timings show it is needed.
- **Error rows of a crashed batch** are rolled back with it; the server log keeps the lines written before the crash.
- **Parallel workers** on the same partner can deadlock; the unit fails and is retried (section 5).
- **Delivery** of the note follows the recipient's preference (D-08): with "Handle by Emails", Odoo queues an email.

## 14. Problems found during the stage

- **NULL retry counts.** The first restart check showed empty try counts: integer fields without a default are NULL in the database. The validation jobs selected `reprocess_attempts < 5`, which never matches NULL, so a row flagged before an upgrade would never have been re-scraped. Fixed with defaults of 0 and a "not exhausted" filter. Regression test: `test_flag_without_a_retry_count_is_still_validated`.
- **An ERROR line in the restart check.** Importing the tests' helpers inside `odoo shell` made Odoo log "Importing test framework ... when not running in test mode". The script now declares test mode around that one import.
