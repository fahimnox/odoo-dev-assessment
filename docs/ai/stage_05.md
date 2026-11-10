# Stage 05 - Resumable synchronization (Partner Monitor)

- **Date:** 2026-11-10
- **Tool / model:** Claude Code, Opus 5.5 (`claude-opus-5-5`), in the same CLI session as Stages 01B to 04; the CLI summarized the earlier context once before this stage started
- **Working directory:** the assessment kit root (`<kit-root>`) and `<kit-root>/solution`
- **Commit:** this log is part of the Stage 05 commit

**Transcription method:** see [README.md](README.md). The user prompt and the referenced instruction file are verbatim. The assistant messages are the visible text blocks recorded in the CLI's local session transcript, verbatim and in order, extracted by a script. Tool calls, tool outputs, reasoning blocks and system notices are not reproduced.

**Redactions:** absolute local paths are replaced with `<kit-root>`, `<home>` or `<scratchpad>`. The CLI's paste markers around the user's pasted text are omitted. No credential or subscription value appeared.

## Referenced instruction file: `prompts/05_partner_resilience.txt` (verbatim)

```text
STAGE 05  -  Implement resumable synchronization and prove its failure behavior

LANGUAGE: English only for all newly authored terminal prose, explanations, questions, and reports. Use simple ASCII formatting and short paragraphs/bullets instead of wide or box-drawn tables. Preserve source data and original historical logs. Arabic coaching happens outside this terminal.

Follow the project contract and the agreed architecture. Inspect the running target-version Odoo cron implementation before relying on batching/progress APIs. Implement a small, durable workflow, not one giant cron transaction. Do not add Celery/Redis/external queues unless the documented requirement cannot reasonably be met inside Odoo.

Required behavior:
1. A daily cron triggers discovery/synchronization. Bounded worker invocations process pending units with explicit time/item limits. Persist progress in dedicated records so completed committed batches survive a process restart.
2. Country validation and partner-reference validation have their own separate crons, as requested. A mismatch sets the corresponding flag; enqueue targeted work with deduplication. Changes in retention_rate, largest_project_size, average_project_size, or reference counts should trigger the targeted reference refresh where appropriate; record and test the trigger policy without creating a self-triggering retry loop. Successful complete validation clears it. A permanent source mismatch remains visible with bounded retries, not an endless tight loop.
3. Track expected counts from the source, actual counts from the completed snapshot, prior counts, and validation outcome distinctly. A genuine change in the number of partners must not create a permanent false mismatch. A matching count alone does not prove identities or content are unchanged.
4. One country's or partner's failure does not prevent unrelated units from progressing. Use correctly scoped savepoints/exception handling where appropriate; do not leave the database cursor in an aborted state. Do not swallow errors.
5. Explain exact commit boundaries. A savepoint only isolates rollback; it does not make progress durable. Prefer small invocations that return to scheduler-managed transaction boundaries. If explicit cursor/commit ownership is required, justify it against this version and keep it out of generic model methods. Document how error logs survive a failed unit.
6. Prevent overlapping workers/daily/manual jobs from processing the same unit unsafely. Use a justified lock/claim mechanism and database uniqueness. If a running claim can persist across commits, implement a recoverable lease or stale-work policy. Test overlap and abandoned work.
7. Make writes idempotent. Repeating a successful or interrupted work item cannot duplicate partners, references, or status events. Work replay of the interrupted batch is acceptable; repeating all previously committed work is not.
8. Only finalize removals/inactivation after a validated complete snapshot of the relevant scope. Do not deactivate countries from an incomplete country list, partners from a truncated country fetch, or references from a partial detail fetch. Stage snapshot data if necessary.
9. Preserve first-seen dates and promotion/demotion history. Handle reference reactivation according to the documented policy.
10. Implement change-aware pulling where the actual source permits it: conditional HTTP requests, content fingerprints, or a justified equivalent. A country count alone cannot detect status/reference/metric changes. If no reliable conditional mechanism exists, periodically revalidate details and state the limitation honestly. A 304 response is reusable only when a known-good snapshot exists.
11. Log every failed unit with run/entity context. For partial/full run failure, send a useful internal chatter notification to the configured user through the verified mail model/API. Include counts, failed scope, and recovery action. Deduplicate repeated notifications; do not send real external email during tests.

Tests/evidence must include: repeated identical ingestion; one partner failure while another succeeds; reference count mismatch then recovery; country mismatch; unchanged counts with changed identities/status; partial snapshot with NO false deletion; valid empty scope; bounded retry exhaustion; duplicate scheduling; two workers racing; and an actual process stop/restart in a disposable environment across a committed boundary. Show the SQL/ORM state before and after restart. An in-process exception test alone does not prove crash recovery.

Write docs/resilience.md with the unit of work, commit/rollback story, restart steps, limits, and observed results. Explain transactions, savepoints, checkpoints, idempotency, and retry backoff with our own code. Stop with the standard stage report.
```

## Conversation (recorded text, verbatim, in order)

### User prompt 1 (verbatim; the whole message was pasted text)

```text
Read prompts/05_partner_resilience.txt and execute Stage 05 only,
following solution/AGENTS.md. Keep Stage 04 marked PARTIAL.

Build the scheduled jobs and worker around the existing reader and
ingestion code. Use the existing fixture-backed fetch function in tests.
When the live fetcher is unavailable, preserve queued work and expose
that condition clearly.

Run the Stage 05 checks on a disposable Enterprise test database.
For the restart test, commit one batch, interrupt the worker during
the next batch, then restart it. Show which items resumed and verify
that completed work, status history, and notifications were not duplicated.
Also verify that one failed partner does not stop unrelated work.

Keep the two previously interrupted files deferred. In the handoff,
document the fetch(url) contract from the actual reader: its expected
return value, exceptions, and integration point. Report the worker test
results and the outstanding live-sync check separately.

Use English only. Stop after the Stage 05 handoff.
```

Assistant message 1:

> Reading the existing Stage 03/04 code and the Stage 05 prompt before designing the worker. Continuing.

Assistant message 2:

> Checking the pinned 18.0 cron engine (commit points, progress API, locking) before writing the worker.

Assistant message 3:

> Still in the design pass: I've read the Stage 03/04 models, the reader and the 18.0 cron engine, and I'm now checking the test plan and assumptions before writing code.

Assistant message 4:

> Confirmed in the pinned source: an `ir.cron` can target an abstract model (`ir.autovacuum` does), so the worker can be a plain engine model. Writing the code now.

Assistant message 5:

> Now the worker engine itself (`models/worker.py`).

Assistant message 6:

> Now the views: validation fields on countries and partners, the waiting banner on runs, and unit results on work items.

Assistant message 7:

> The shell mangled the inline script; I'll put it in a scratch file instead.

Assistant message 8:

> Code is in place; next the tests. Checking two fixture details I need for the test variants.

Assistant message 9:

> Writing the shared test helpers (page variants built in code from the live-derived fixtures, as Stage 04 did).

Assistant message 10:

> Now the main worker test file.

Assistant message 11:

> Fixing one test I got wrong while reviewing (a retried Andorra unit queues more work, so the run would not finish); checking the scheduler's reschedule code for the last assertion.

Assistant message 12:

> Now the concurrency tests with real, separate database connections.

Assistant message 13:

> Next, the out-of-process restart check. First confirming how `odoo shell` runs a piped script in 18.0.

Assistant message 14:

> Now the harness that runs the phases, kills the worker container mid-batch, and dumps SQL state before and after.

Assistant message 15:

> Code and tests are written. Quick syntax and XML checks before the full test run.

Assistant message 16:

> Running the full Partner Monitor suite on a fresh `azk_ee24_test` (background, about 2-3 minutes).

Assistant message 17:

> While the suite runs, reading the doc sections I will update.

Assistant message 18:

> Drafting `docs/resilience.md` while the tests run (observed results are filled in after the runs).

Assistant message 19:

> Adding the Stage 05 decisions to `docs/assumptions.md` while the suite runs.

Assistant message 20:

> Waiting for the test run to finish before continuing.

Assistant message 21:

> Continuing with documentation that does not depend on the results: the architecture section for Stage 05.

Assistant message 22:

> All 112 tests passed on the first run (91 earlier plus 21 new). Checking the log for warnings and that the new classes really ran.

Assistant message 23:

> PASS: "0 failed, 0 error(s) of 112 tests", 0 warning or error lines in the log, exit code 0. Getting the timing, then running the restart check on the same fresh test database.

Assistant message 24:

> Small consistency fix in the check's setup (create runs with the same mail context as the production code), then running the restart check in the background.

Assistant message 25:

> While the restart check runs, updating the test plan with the Stage 05 tests.

Assistant message 26:

> Now the NULL-safe validation domains in the worker, and the regression test.

Assistant message 27:

> Tightening one help text I noticed while reviewing ("Retries Exhausted" turns on when the last allowed re-scrape is queued, not after it ran).

Assistant message 28:

> Re-running the full suite on a fresh database, then the restart check, in one background job.

Assistant message 29:

> While that runs, preparing the requirements-matrix updates. Reading the full rows I will change.

Assistant message 30:

> Reviewing my own diff for leftovers (unused imports, stale comments) while the run finishes.

Assistant message 31:

> Drafting the Stage 05 handoff now; result numbers will be filled in from the final run (marked with a placeholder I will grep for).

Assistant message 32:

> Preparing the STATE.md update (result placeholders to fill from the final run).

Assistant message 33:

> Second run finished. Checking its results, then applying the two small cleanups and doing the final rerun.

Assistant message 34:

> Run 2: suite "0 failed, 0 error(s) of 113 tests", 0 warning or error lines; restart check 12 of 12 PASS, and the ERROR line is gone. Applying the two cleanups now, then the final run.

Assistant message 35:

> Adding a small assertion that a flagged partner and a stale page queued by the same job call share one validation run.

Assistant message 36:

> Final run on the final code: the suite, the restart check, then the upgrade of the development database `azk_ee24` (as in Stages 03 and 04), all in one background job.

Assistant message 37:

> While the final run goes, applying the requirements-matrix update (docs only).

Assistant message 38:

> Waiting for the final run; then I fill in the observed results.

Assistant message 39:

> Drafting the final report while the last run finishes.

Assistant message 40:

> Final verification run is still in progress (suite, then restart check, then the `azk_ee24` upgrade). The report draft, handoff and docs are ready except for the numbers from this run.

Assistant message 41:

> All three finished with exit 0. Reading the final results from the logs.

Assistant message 42:

> Final run: suite "0 failed, 0 error(s) of 113 tests" with 0 warning or error lines (1 min 58 s); `azk_ee24` upgrade exit 0 with 0 warning or error lines. Now the final restart-check evidence.

Assistant message 43:

> Moving the "Problems found" section after "Limits" so the numbering reads in order.

Assistant message 44:

> Filling in the handoff's result sections.

Assistant message 45:

> The shell wrapper trips over apostrophes in inline scripts; writing the script to a scratch file instead.

Assistant message 46:

> Now the STATE evidence block.

Assistant message 47:

> Updating the kit-level guidance file (outside the repository) with a short Stage 05 note, as done for Stage 04.

Assistant message 48:

> Finalizing the report text.

Assistant message 49:

> Some progress messages I wrote seem to be missing from the extracted log. Checking the transcript before trusting the assembler.

## Notes on accuracy

- This log was assembled from the transcript just before its own commit. Progress messages written after that point, while committing, are not included. The final response below is included as prepared, and it was displayed unchanged.
- Several progress notes the agent meant as messages were written inside its reasoning, so they were never displayed and are not in the transcript's text blocks. Examples: the explanation of the two problems found by the first restart check, and the note that a lock probe had been misread. They are not reproduced here; their content is in the final response, the Stage 05 handoff and the mistakes table of [README.md](README.md).
- Facts in the messages that were later corrected stay as written here; corrections are listed in [README.md](README.md) (mistakes table) and in the Stage 05 handoff.

## Summary of tool activity (summary, not verbatim)

1. Read `prompts/05_partner_resilience.txt`, `solution/AGENTS.md`, `docs/STATE.md`, the architecture, the Stage 03 and Stage 04 models, the reader, the ingestion and the tests. Checked Git (clean, at the Stage 04 commit) and the disk (9.0 GB free).
2. Read the pinned 18.0 scheduler source (`odoo/addons/base/models/ir_cron.py`: `_process_jobs`, `_acquire_one_job`, `_process_job`, `_run_job`, `_callback`, `_trigger`, `_notify_progress`, `_reschedule_later`, `method_direct_trigger`), the core cron tests (`_process_job` in test mode), `odoo/tests/common.py` (TransactionCase cursors), `odoo/sql_db.py` (savepoints, REPEATABLE READ), `odoo/cli/shell.py` and `odoo/modules/loading.py`. Confirmed that a cron can target an abstract model (`ir.autovacuum`).
3. **Code:** wrote `models/worker.py` and `data/ir_cron.xml`; extended `models/common.py`, `models/country.py`, `models/partner.py`, `models/work_item.py`, `models/sync_run.py`, `models/ingest.py`, `services/parsers.py` (card metrics hash), the views and the manifest (18.0.1.3.0).
4. **Tests:** wrote `tests/test_worker.py` and `tests/test_worker_concurrency.py`; added fixture variants made in code and `ALL_PAGES` to `tests/common.py`. Wrote `scripts/restart_check.sh` and `scripts/restart_check.py`.
5. **First run** of `scripts/dev.sh test azk_odoo_partner_monitor` (fresh `azk_ee24_test`): 112 tests, 0 failed, 0 errors, 0 warning lines (log `<kit-root>/runtime/logs/stage05_test_run1.log`).
6. **First restart check** (`<kit-root>/runtime/logs/stage05_restart_check_run1.log`): all 12 checks PASS. Its output showed two problems, fixed before the final runs:
   - importing the tests' helpers in `odoo shell` made Odoo log an ERROR (test framework imported outside test mode); the script now declares test mode around that import only;
   - new integer fields were NULL without a default, and the validation jobs filtered with `reprocess_attempts < 5`, which never matches NULL. The fields now default to 0, the jobs test "not exhausted" instead, and a regression test was added.
7. **Second runs** after those fixes: 113 tests, 0 failed, 0 errors (`stage05_test_run2.log`); restart check 12 of 12 (`stage05_restart_check_run2.log`). A self-review then made two clean-ups: one validation run per job call (with a new assertion) and an unused import removed.
8. **Final runs** on the final code: 113 tests, 0 failed, 0 errors, 0 warning lines (`stage05_test_run3.log`); restart check 12 of 12 (`stage05_restart_check_run3.log`); `scripts/dev.sh update azk_odoo_partner_monitor` on `azk_ee24` with 0 warnings (`stage05_update_azk_ee24.log`), then a read-only check of the jobs, runs and version, and an HTTP check of the login page. All logs are in `<kit-root>/runtime/logs/`.
9. **Docs:** wrote `docs/resilience.md` and the Stage 05 handoff; updated the architecture (5.12), assumptions (A-20 superseded, D-30 to D-36), requirements matrix, test plan (3.3), STATE and the AI log index. Outside the repository, added a Stage 05 note to the kit's guidance file. Checked the changes for non-ASCII text, local paths and secrets, and committed only the intended files.

## Assistant final response (verbatim)

Everything between the two rules below is the final visible response.

---

Stage 05 is committed: the scheduled jobs and the sync worker are built and tested offline. Stage 04 stays **PARTIAL**, so no live sync has run.

**What was built**
- `models/worker.py`, the sync engine, with four jobs in `data/ir_cron.xml`:
  - daily discovery;
  - the worker, every 10 minutes;
  - country validation and reference validation, every 6 hours.
- **Claims and savepoints.** The worker claims one unit at a time with a row lock (`FOR NO KEY UPDATE SKIP LOCKED`) and runs it in its own savepoint. A failure is stored after the rollback (an error row, a counted try, a log line), and the batch goes on.
- **Durability.** Nothing in our code commits. The scheduler's commit after each batch (20 units or 60 s at most) is the only durability point.
- **Retries.** A unit gets 5 tries, 15, 30, 60 and 120 minutes apart. A validation mismatch gets 5 re-scrapes. After that the record stays visible as failed or "Retries Exhausted".
- **Validation.** Expected, found, previous and stored counts are kept apart.
- **Change detection.** A changed card (retention rate, project sizes or reference count) triggers one page re-read, never a loop. Pages read more than 7 days ago are read again.
- **Notes.** A partial or failed run posts one note for the configured user.
- **Without a page source (today):** nothing is attempted and the queue is kept. The run shows why it is waiting, posts one note, and each worker call logs a warning.
- **Docs:** `docs/resilience.md` explains the commit story, savepoints, claims, idempotency, backoff, limits and the results.

**Worker tests (automated, today, on the final code)**
- `scripts/dev.sh test azk_odoo_partner_monitor`: **PASS**, "0 failed, 0 error(s) of 113 tests" in a fresh `azk_ee24_test`, 0 warnings in the log, 1 min 58 s. That is the 91 earlier tests plus 22 new ones: 20 worker tests and 2 concurrency tests on real, separate database connections.
- **One failed partner does not stop unrelated work:** IT SYS's page download failed and was stored as an error row with its run, unit and URL. RoayaTec and DEVONEERS were stored in the same batch.
- **A real SQL error inside one unit** rolled back only that unit. The next unit was stored, and the cursor still worked.
- **Two workers** on separate connections never got the same unit, also after one of them committed.

**Restart test (process killed, then restarted, on the final code)**
- **Batch 1 committed:**
  - unit 259 (Egypt) used its 5th and last try and failed, so run 49 ended `failed` with one note;
  - unit 260 (Andorra) finished and promoted BDR GROUP SLU to Silver.
- **Batch 2:** unit 261 (Anguilla) finished inside the open transaction, then the read of unit 262 (RoayaTec) blocked.
- **The kill:** `docker kill` (SIGKILL) at 10:09:38 UTC, exit 137.
  - While batch 2 was blocked, another session could claim only unit 263.
  - After the kill, units 261, 262 and 263 were claimable, and no worker session was left.
- **Resumed after the restart:** units 261 and 262 (the interrupted batch, replayed with 0 tries recorded), then unit 263. Only their pages were read. Egypt and Andorra were not read again.
- **Not duplicated** (12 of 12 checks PASS):
  - unit 259 still has 5 tries and 1 error row;
  - BDR GROUP SLU's history is exactly "initial, promoted", and 13 partners have 14 history rows;
  - RoayaTec has 3 references, not 6;
  - run 49 has one note and one Inbox notification;
  - run 50 ended `done` without a note, and no email was queued.

**Outstanding: the live sync check, NOT RUN**
- The page-download module is still deferred, so `worker._get_page_source()` returns None and no unit can read the live site.
- The handoff gives the steps for when the module exists: connect it, add its mocked-response tests, run one small country and one partner page on the test database, and check the unit timings.

**The fetch(url) contract** (from `services/reader.py`; details in the handoff)
- `fetch(url)` returns `(final_url, html)`: the URL after redirects and the page text.
- It must raise on any failure: a timeout, a connection error, an HTTP error, a login or rate-limit page. It must never return an empty page instead.
- The reader catches nothing. The worker records the exception as a failed try for that unit.
- Integration point: `PartnerMonitorWorker._get_page_source()` in `models/worker.py`.

**Also run**
- First runs, before two fixes: 112 of 112 tests, and the restart check 12 of 12. Second run: 113 of 113 and 12 of 12. Those two fixes, found by the first restart check:
  - New counters were NULL. The validation jobs filtered with "attempts < 5", which never matches NULL. Fixed with defaults of 0, a "not exhausted" filter and a regression test.
  - The check's shell import of the test helpers made Odoo log an ERROR; fixed in the script.
- `scripts/dev.sh update azk_odoo_partner_monitor` on `azk_ee24`: PASS, 0 warnings. The four jobs are active, and the first daily discovery is due 2026-11-11 at 02:00 UTC. There are 0 runs, and the login page answers HTTP 200.

**Open issues**
- No live sync (above).
- One country listing is one unit. A very long country could exceed the scheduler's time limit; page checkpoints would be the next step.
- A crash rolls back the error rows of its batch. The server log keeps the lines written before it.
- `azk_ee24` now has the four jobs. At 02:00 UTC the daily job will queue a run that waits, with one note to the administrator, whose preference is email.

**Changed files**
- **New:** `models/worker.py`, `data/ir_cron.xml`, `tests/test_worker.py`, `tests/test_worker_concurrency.py`, `scripts/restart_check.sh`, `scripts/restart_check.py`, `docs/resilience.md`, `docs/handoffs/stage_05_en.md`, `docs/ai/stage_05.md`.
- **Updated:**
  - models: `common.py`, `country.py`, `partner.py`, `work_item.py`, `sync_run.py`, `ingest.py`, `__init__.py`;
  - `services/parsers.py` (the card hash), `tests/common.py`, `tests/__init__.py`, three view files, the manifest (18.0.1.3.0);
  - the docs: STATE, architecture (5.12), assumptions (D-30 to D-36), requirements matrix, test plan (3.3) and `ai/README.md`.
- **Commit:** "Stage 05: resumable sync worker, scheduled jobs and restart check".

**Comprehension questions**
1. Why does a worker killed in the middle of a batch never leave a unit claimed forever, even though no lease is stored?
2. A failed unit's error row is written after `ROLLBACK TO SAVEPOINT`, not inside the savepoint. What would be lost the other way round, and what is still lost when the whole process dies?
3. Why does the card hash compare a listing card with the previous listing card, and not with the values stored from the partner's own page?

**Next stage:** 06, the Partner Monitor dashboard. I'm stopping here.

---
