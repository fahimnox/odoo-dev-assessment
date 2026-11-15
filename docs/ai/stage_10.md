# Stage 10 - Engineering review

- **Date:** 2026-11-15
- **Tool / model:** Claude Code, Opus 5.5 (`claude-opus-5-5`), in the same CLI session as Stages 01B to 09
- **Working directory:** the assessment kit root (`<kit-root>`) and `<kit-root>/solution`
- **Commit:** this log is part of the Stage 10 commit

**Transcription method:** see [README.md](README.md). The user prompt and the referenced instruction file are verbatim. The assistant messages are the visible text blocks recorded in the CLI's local session transcript, verbatim and in order, extracted by a script. Tool calls, tool outputs, reasoning blocks and system notices are not reproduced.

**Redactions:** absolute local paths are replaced with `<kit-root>`, `<home>` or `<scratchpad>`. The CLI's paste markers around the user's pasted text are omitted. No credential or subscription value appeared in the recorded text; the local web login reached the browser check through environment variables, in tool calls that are not reproduced.

## Referenced instruction file: `prompts/10_engineering_review.txt` (verbatim)

```text
STAGE 10  -  Review correctness, access control, resilience, and maintainability

LANGUAGE: English only for all newly authored terminal prose, explanations, questions, and reports. Use simple ASCII formatting and short paragraphs/bullets instead of wide or box-drawn tables. Preserve source data and original historical logs. Arabic coaching happens outside this terminal.

Follow the project contract. Review both addons as a skeptical maintainer. Start with actual code and runtime evidence; do not produce a generic checklist and declare success. Fix findings, rerun affected tests, and avoid unrelated refactors or new features.

Inspect:
1. Requirements coverage: each PDF requirement has a real implementation and evidence. Identify assumptions, unsupported cases, and untested claims. Exercise 3 must remain explicitly unselected.
2. Module quality: manifests, dependencies, imports, XML IDs/load order, security files, version-correct APIs, clean install/update, and absence of vendor/core edits, explicit and minimal Enterprise dependencies, and actual Enterprise runtime evidence rather than Community-only passes.
3. Access: reader versus manager actions, public/portal denial, report ACLs/record rules, company scope, wizard ownership and export authorization. Hidden buttons alone are not access control. Review every sudo(), raw SQL statement, public method, and custom controller.
4. Scraping: timeout/retry bounds, partial snapshots, missing values, URL scope validation, pagination completeness, stable identities, overlapping jobs, stale claims, retries after crash, false deletions, and notification deduplication. Ensure source failures cannot make live data look successfully synchronized.
5. Accounting: verify the agreed opening convention, sign/rounding behavior, cancelled/draft selection, analytics, currency separation, literal prefixes, hierarchy totals, and filter consistency in all outputs. Do not assert that an intentionally filtered ledger must always have equal debit/credit totals.
6. UI: global dashboard filter propagation, deterministic Top/Bottom 5 rankings, correct size buckets, empty states, preview search/filter behavior, actual PDF readability, and actual XLSX structure.
7. Data and secrets: test/demo records clearly separated from live observations; no database dumps, local passwords, tokens, machine-specific absolute paths, confidential source PDF, or personal study notes in staged Git content. Redact public transcripts without inventing replacement outputs.
8. Performance: use a modest reproducible synthetic dataset and record its size, environment, query/runtime observations, and limits. Check for obvious per-record query loops and unbounded HTTP/transaction work. Do not claim a production capacity number from this benchmark.

Write docs/review_findings.md with severity, actual location, reproduction/evidence, fix, and verification result. No finding should be marked resolved solely because code changed. Keep unresolved findings visible. Explain the three most important fixes in English, including what failure each prevents. Stop with the standard stage report.
```

## Conversation (recorded text, verbatim, in order)

### User prompt 1 (verbatim; the whole message was pasted text)

```text
Read prompts/10_engineering_review.txt and execute Stage 10 only,
following solution/AGENTS.md.

Review both addons against the assessment PDF and actual code.
Fix verified findings and rerun affected checks. Use the validated
Enterprise environment on port 8071.

Prioritize these outstanding items:

1. Stage 04 completion:
   Complete the missing public-page HTTP fetcher using the existing
   fetch(url) -> (final_url, html) contract and connect it to the worker.
   Use bounded timeouts, retries, response sizes and request rates.
   Respect the existing URL-scope and robots rules. Treat HTTP errors,
   login pages and rate limiting as failures, never empty datasets.
   Add mocked-response tests and run one bounded live check covering
   a small country and a partner on a disposable database.
   Mark Stage 04 complete only with actual integration evidence.
   If tooling blocks a step, record the exact blocker and continue
   independent review work.

2. Accounting:
   Test a configured July-to-June fiscal year across its boundary,
   with independent expected numbers and a matched native comparison.
   Investigate branch-company scope and isolation. Document the exact
   supported behavior and any remaining limitation.

3. Analytics:
   Enable Analytic Accounting in a disposable test environment.
   Verify the selector, recalculation and exports through the browser.

4. Access and integration:
   Test a read-only accountant, an unauthorized user, another user's
   wizard, and tampered download options.
   Trace the actual PDF/XLSX download route to every validation step,
   naming the real files and functions.
   Check that our report extensions do not change native reports.

5. Demo data and performance:
   Review demo hooks and no-demo installation behavior.
   Run the modest benchmark required by the Stage 10 prompt and
   document its dataset, measurements and limits.

Run heavy checks sequentially because memory is limited.
Reuse the existing browser scripts and retain actual PDF rendering
checks outside the unit suite.

Write docs/review_findings.md with evidence, fixes and verification.
Keep unresolved requirements visible. Recover the complete Stage 09
comprehension questions from its handoff and include their answers.

Use English ASCII only. Stop after Stage 10.
```

Assistant message 1:

> I'm still reading. I'm checking how the Enterprise service starts (cron threads, reload mode), so that connecting the live fetcher can't set off an unrequested crawl from `azk_ee24`.

Assistant message 2:

> Now connecting it to the worker. Changes: the pause setting, a stop when the site rate-limits, and no scheduler re-loop while paused.

Assistant message 3:

> The heredoc failed in this shell, the same apostrophe problem noted in Stage 09. I'll make the worker changes with the Edit tool instead.

Assistant message 4:

> Starting the Partner Monitor suite in the background on a fresh `azk_ee24_test`. While it runs I'll write the bounded live-check script (no heavy work in parallel).

Assistant message 5:

> The header change is Python-only, so the live check can rerun on the same `azk_ee24_test`. The final test suite will run again later on all changes.

Assistant message 6:

> I'll write a focused browser script for the analytic selector instead of growing the Stage 09 one. First, the filter component's markup.

Assistant message 7:

> Before the Trial Balance run I'm reviewing the wizard and the demo hook, so any fix goes into the same run.

Assistant message 8:

> While the Trial Balance suite runs, I'm writing the analytic browser check. It reuses the Stage 09 helpers and compares the visible rows with the engine after each selector change.

Assistant message 9:

> Next, a `--without-demo` option on `dev.sh clean-install` for the no-demo install check.

Assistant message 10:

> The run is installing modules (42 of 90). I'm writing the review document now, with marked placeholders for the results still to come, filled in afterwards from the logs.

Assistant message 11:

> While run 3 goes, I'm correcting what the documents already say about RF-06: the cause is the default ordering join, not the record rule, and the fix needs no `sudo()`.

Assistant message 12:

> Both worker phases of the restart check patch in the fixture source, so it can never reach the live site.

Assistant message 13:

> The run started only two minutes ago. Meanwhile I'm adding the Stage 10 live check to `live_site_notes.md`, with runs 1 to 3 and a placeholder for the final run.

Assistant message 14:

> I've drafted the Stage 10 handoff with placeholders for the remaining results. Trial Balance run 3 should finish any moment, and its notice will start the benchmark.

Assistant message 15:

> While the benchmark runs I'm updating the requirements matrix rows that this stage's evidence settles, starting with those that mention Stage 10, the analytic browser check, fiscal years or branches.

Assistant message 16:

> The analytic browser check is running as the read-only accountant on the temporary server; the browser has just started. It takes a few minutes; results arrive by notification.

Assistant message 17:

> Zero warning or error lines on the temporary server; it stopped at 16:25:42, and the lowest commit headroom was 3.3 GB. Looking at the screenshots and the rendered PDF page myself.

Assistant message 18:

> While the vendor tests run, I'm copying the four analytic screenshots into `docs/screenshots/` after checking the wizard image for anything private.

Assistant message 19:

> The vendor tests are still running. Meanwhile I'm preparing the script that assembles this stage's prompt and output log, `docs/ai/stage_10.md`.

Assistant message 20:

> The final Partner Monitor suite is installing its 34 modules. Meanwhile I corrected the third Stage 09 answer: it now cites only documented reasons and the real test name.

Assistant message 21:

> Final Partner Monitor run: PASS, "0 failed, 0 error(s) of 147 tests" (129 earlier and 18 new), 0 warning lines, exit 0. Live check run 4 on the final code is running now.

Assistant message 22:

> The restart check (TP-PM-15) is still running. I've prepared the next step: a clean install of both addons without demo data, a state check, the documented one-time demo call, and the record counts.

Assistant message 23:

> The restart check has done its kill-and-restart: the worker was SIGKILLed mid-batch (exit 137), and three units were claimable afterwards. It is now in its verification phase.

Assistant message 24:

> Verified against the session transcript: the Stage 09 final response was displayed exactly as logged in `docs/ai/stage_09.md` (5,585 characters).

Assistant message 25:

> The install of both addons without demo data passed: exit 0, 0 warning and 0 error lines, in 2 minutes 39 seconds. The state check and the documented demo call are running now.

Assistant message 26:

> `azk_ee24` is being upgraded to the Stage 10 code. When the server is back, one paused worker call runs, then the dashboard and preview browser checks. All changed text files passed the ASCII scan.

Assistant message 27:

> The dashboard browser check is running on the upgraded `azk_ee24`; the Trial Balance preview check follows. Meanwhile I've drafted the final report, with only those two results still open.

Assistant message 28:

> The dashboard check is in its last step, opening the partner list from the Top 5 table. The preview check starts next.

Assistant message 29:

> Every check is done. The server log has 0 warning or error lines since the upgrade. Filling the last results into the documents.

## Notes on accuracy

- This log was assembled from the transcript just before its own commit. Progress messages written after that point, while committing, are not included. The final response below is included as prepared, before it was displayed.
- The Stage 09 final response was checked against the session transcript before this log was written: it was displayed exactly as logged in [stage_09.md](stage_09.md).
- The CLI compacted the conversation's context just before this stage (after Stage 09). The transcript keeps every visible message, so the log is complete; the CLI's compaction summary is not a user prompt and is not reproduced.
- System notifications (background command completions and monitor events) are not user prompts; they are summarized under tool activity.
- Facts in the messages that were later corrected stay as written here; corrections are listed in [README.md](README.md) (mistakes table) and in [review_findings.md](../review_findings.md).

## Summary of tool activity (summary, not verbatim)

1. **Started:** read the Stage 10 prompt file, `solution/AGENTS.md`, STATE, the Stage 04 handoff, the live site notes and the Stage 05 page-source contract. Checked Git (clean at `564b71b`), disk (41 GB free) and memory (2.5 GB free).
2. **Read the pinned 18.0 sources by name:**
   - the scheduler loop and progress API;
   - Odoo's blocking of outgoing requests in tests;
   - the `account_reports` download route, `dispatch_report_action`, `export_to_pdf` and `export_to_xlsx`, and the multi-company options;
   - `compute_fiscalyear_dates` in account and account_accountant, and the `account.fiscal.year` constraints;
   - branch fields delegated to the root company, and how Odoo's own tests create branches;
   - the company record rule, the many2many `parent_of` search, and the `account.account` ordering;
   - the localization auto-install on company creation, and the shell's transaction handling.
3. **Safety step before any code:** set the download pause parameter on `azk_ee24` from an Odoo shell, because its queue held a country-list unit and its worker job runs every 10 minutes.
4. **Code:**
   - Partner Monitor 18.0.1.5.0:
     - `services/http_client.py`;
     - worker and work-item changes;
     - the pause setting and view;
     - the parser fix;
     - 18 tests.
   - Trial Balance:
     - the engine's account lookup (two versions; the first, with `sudo()`, was replaced);
     - the demo company flag;
     - 12 tests, and helpers in `tests/common.py`.
   - Scripts: the live check, two benchmarks, the analytic setup and browser check, and `dev.sh clean-install --without-demo`.
5. **Test runs,** each on a fresh `azk_ee24_test`, one at a time:
   - Partner Monitor: 145 of 145, then 147 of 147 on the final code.
   - Trial Balance: 112 of 113, then 113 of 114, then 114 of 114 on the final code.
   - The vendor's `TestTrialBalanceReport` and annotation-export tests with our addon installed: 11 of 11.
6. **Live site:** 23 requests to www.odoo.com in all.
   - Four live check runs through the worker, on the disposable database, rolled back.
   - Seven single diagnostic requests to robots.txt (host curl, container curl, Python `requests`).
   - One request that saved a partner page privately.
   - That page was parsed offline after adding `beautifulsoup4` 4.12.3 to the private tools venv.
7. **Probes** in Odoo shells on `azk_ee24_test`, rolled back except as noted:
   - a branch-only reader's account searches (five probes);
   - one probe created a company with Egypt, which installed `l10n_eg` and committed (the database was recreated by the next run);
   - `l10n_eg` was confirmed absent on `azk_ee24`.
8. **Benchmarks:** `scripts/tb_benchmark.py` and `scripts/pm_benchmark.py`, both rolled back.
9. **Browser:**
   - The analytic browser check on a temporary server for `azk_ee24_test`: 127.0.0.1:8072, no cron threads, a read-only accountant with a random password that was never printed.
   - Run 1 did not start (a path form); run 2 passed 6 of 6. The screenshots and the rendered PDF page were viewed.
10. **Restart check:** `scripts/restart_check.sh` after the final Partner Monitor run: 12 of 12.
11. **Install without demo data** into the disposable `azk_ee24_clean`, a state check, and the documented demo call: see the test results.
12. **`azk_ee24`:**
    - upgraded to the Stage 10 code;
    - one worker call with HTTP refused by a patch;
    - the dashboard and preview browser checks rerun: see the test results.
13. **Documentation:**
    - `review_findings.md`, the handoff and this log;
    - STATE, the requirements matrix, assumptions (D-64 to D-66), architecture, resilience, the live site notes, the test plan and the test results.
    - The kit-root CLAUDE.md got a Stage 10 note (outside the repository).
14. **Before the commit:**
    - the ASCII and pre-commit scan;
    - only the intended files were staged.

## Assistant final response (verbatim)

Everything between the two rules below is the final visible response.

---

Stage 10 is done, and Stage 04 is now complete. The review is in `docs/review_findings.md`: 15 findings, each with severity, location, evidence, fix and verification. It also traces the download route step by step and answers the three Stage 09 questions. Everything is committed locally as "Stage 10: engineering review, page download and live check".

**Completed work**

- **Partner Monitor reads the live site.**
  - `services/http_client.py` is the page download, connected to the worker. It has bounded timeouts, size, request spacing and retries. Redirects are checked against the URL and robots rules before they are followed. HTTP errors, login pages and rate limits raise, so a failure never becomes an empty result.
  - A rate limit pauses the process and stops the batch.
  - Settings > Partner Monitor > Pause Website Downloads can stop all downloads. It is on for `azk_ee24`, so that a restart never starts an unrequested full crawl.
- **The bounded live check you asked for** ran through the real worker on the disposable `azk_ee24_test`: the country list, Andorra (2 of 2 partners) and one partner page, at most 8 requests, rolled back. It found three problems that mocks could not show, all fixed (below).
- **Trial Balance:**
  - a July-to-June fiscal year, set up two ways and tested across the boundary against hand-calculated numbers and the standard report;
  - branch scope and isolation, tested and documented;
  - the analytic selector, recalculation and exports, in a real browser as a read-only accountant;
  - the standard reports, shown unchanged;
  - a benchmark.
- **Access:**
  - The rerun suites cover a read-only accountant, users without accounting rights, another user's wizard, and tampered options on the preview and both exports.
  - The browser check added a read-only accountant and two tampered downloads, both refused.
  - `docs/review_findings.md` traces `/account_reports` through every validation step, with the real files and functions.
- **The three most important fixes, and what each prevents:**
  1. **gzip only (RF-02).** The site closed every HTTP/1.1 connection that offered `deflate`, which is the `requests` default. Without this fix every sync would have failed, safely but forever.
  2. **Branch-only users (RF-06).** For a user who has a branch but not its root company, `account.account`'s default order dropped the shared accounts from every search. That user's report lost the Current Year Earnings row, every zero-activity account and every prefix match, while the numbers it showed looked right. The fix is an explicit order, still without `sudo()`.
  3. **Empty reference cards (RF-04).** One empty card made a complete list of 17 references look incomplete. That causes 5 needless re-scrapes and a false "Retries Exhausted".
- **Also fixed:**
  - RF-03: work queued during a batch was not due in that batch, so the scheduler waited up to 10 minutes per step;
  - RF-07: the documented demo shell call would have installed the Egyptian localization with a commit midway;
  - RF-13: stale matrix rows.

**Commands and results**

All on 2026-11-15, edition `enterprise-20241208` (port 8071), one heavy check at a time, with about 2 to 3 GB of RAM free.

- **`scripts/dev.sh test azk_odoo_partner_monitor`:** PASS on the final code, "0 failed, 0 error(s) of 147 tests", 0 warning lines. Run 1, before the live-check fixes, also passed (145 of 145).
- **`scripts/dev.sh test azk_dynamic_trial_balance`:** PASS on the final code, "0 failed, 0 error(s) of 114 tests", 0 warning lines.
  - Runs 1 and 2 each FAILED one test, the branch-only reader.
  - My first fix used a narrow `sudo()` and was wrong; the real cause was the ordering join.
- **The vendor's `TestTrialBalanceReport` (8) and annotation-export tests (3) with our addon installed:** PASS, 11 of 11.
- **`scripts/pm_live_check.py` on `azk_ee24_test`:**
  - run 1 FAILED (RF-02, diagnosed with seven single requests);
  - runs 2 and 3 found RF-03 and RF-04;
  - run 4, on the final code, PASSED: 4 page requests, all allowed by robots.txt, BDR GROUP SLU "17 of 17 references, matched", rolled back.
  - In all, 23 requests reached www.odoo.com.
- **`scripts/tb_analytic_smoke_check.py`** (my headless Chrome, as a read-only accountant, on a temporary server at 127.0.0.1:8072 for the disposable database, Analytic Accounting on): PASS, 6 of 6.
  - The wizard's field and the preview's dropdown each recalculate the report to match the engine.
  - The PDF and XLSX carry the filter.
  - Tampered downloads are refused with AccessError.
- **`scripts/restart_check.sh`:** PASS, 12 of 12. The worker was killed mid-batch; only the interrupted units ran again.
- **`scripts/dev.sh clean-install ... --without-demo`:** PASS, 0 warnings, no demo data at all. The documented demo call then created the demo company without installing `l10n_eg`; a second call created nothing.
- **Benchmarks** (rolled back):
  - Trial Balance: the same 15 to 16 engine queries at 2,000 and 10,000 journal items (0.03 to 0.07 s);
  - Partner Monitor: 7 queries per card on a first read and 4 on a repeat, at 100 and 1,000 cards.
- **`scripts/dev.sh update` of both addons on `azk_ee24`:** PASS, 0 warnings. The worker now waits with "website downloads are paused", and no request was sent. Browser reruns: dashboard 7 of 7, Trial Balance preview and downloads 20 of 20.

**Open issues and assumptions**

- **Kept for later stages:** the README and publication (Stages 12 and 15).
- **No full live sync was run, on purpose:** downloads are paused on `azk_ee24` (D-64). Untick the setting only if you want hours of real crawling.
- **Production setting** (RF-12): with multi-process workers, raise `limit_time_real_cron`. The largest country takes about 50 s.
- **Branches** (D-16, D-66): no consolidation of a root with its branches. A branch ignores its root's custom fiscal-year records (Odoo). The standard Trial Balance shows branch-only users nothing; ours works for them.
- **The robots.txt rules are coded:** the live check compares them with the live file, but the module itself does not.
- **Your own browser check is recommended.** The walkthrough is in the handoff.

**Changed files and functions**

- **New:**
  - `services/http_client.py` (`PartnersHttpClient.get`, `_attempt`, `_check_status`, `_read_body`, `_check_page`; `RequestPacer`);
  - `tests/test_http_client.py`;
  - in the Trial Balance: `tests/test_fiscal_years_and_branches.py` and `tests/test_native_reports.py`;
  - scripts: `pm_live_check.py`, `pm_benchmark.py`, `tb_benchmark.py`, `tb_analytic_setup.py`, `tb_analytic_smoke_check.py`;
  - `docs/review_findings.md` and `docs/handoffs/stage_10_en.md`.
- **Changed:**
  - `models/worker.py` (`_get_page_source`, `_process_queue`, `_cron_process_queue`, `_wait_for_page_source`) and `models/work_item.py` (`_enqueue(now=...)`);
  - the settings field and view, and `services/parsers.py` (`parse_partner_page`);
  - `models/trial_balance_engine.py` (`_chart_accounts`) and `models/demo_data.py` (`_create_demo_data`);
  - the tests, `scripts/dev.sh`, and the documentation.

**Comprehension questions**

1. The page download raises an exception for a login page or HTTP 429 instead of returning the page it got. What exactly would go wrong, in our ingestion, if it returned that page as text and let the parser decide?
2. Why does the worker report "nothing done" to the scheduler after a rate limit, although one unit was tried? What would the scheduler do otherwise?
3. For a user who has a branch but not its root company, `search_count` found 49 accounts and `search` found none, even under `sudo()`. What in Odoo's default ordering of accounts explains it, and why did `sudo()` not help?

**Next stage:** 11 (clean acceptance), when you ask for it.

---
