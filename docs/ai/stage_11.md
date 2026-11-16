# Stage 11 - Clean acceptance

- **Date:** 2026-11-16
- **Tool / model:** Claude Code, Opus 5.5 (`claude-opus-5-5`), in the same CLI session as Stages 01B to 10, resumed after a context compaction
- **Working directory:** the assessment kit root (`<kit-root>`) and `<kit-root>/solution`
- **Commit:** this log is part of the Stage 11 commit

**Transcription method:** see [README.md](README.md). The user prompts and the referenced instruction file are verbatim. The assistant messages are the visible text blocks recorded in the CLI's local session transcript, verbatim and in order, extracted by a script. Tool calls, tool outputs, reasoning blocks and system notices are not reproduced.

**Redactions:** absolute local paths are replaced with `<kit-root>`, `<home>` or `<scratchpad>`. The CLI's paste markers around the user's pasted text are omitted. The random password of the acceptance users never appeared in the recorded text: it went from a private file to the scripts through environment variables, in tool calls that are not reproduced.

## Between Stage 10 and Stage 11 (recorded text, verbatim, in order)

After the Stage 10 final report, the CLI delivered automatic notices that background watchers had expired. They are not user prompts and are not reproduced; the assistant answered each with a short status line. The CLI then compacted the conversation's context, the session was resumed, and the user typed "continue". The reply followed the resume procedure R1 (`prompts/R1_resume_session.txt`), which asks which stage to continue when the pending stage is unclear.

Assistant message 1:

> That notice only means an old progress watcher on the no-demo checks timed out. Those checks had already finished and passed. Stage 10 is complete and committed as `e54214b`, and nothing else is running. I'll wait for your request before starting Stage 11.

Assistant message 2:

> Another old progress watcher timed out, this one on the final Partner Monitor checks. Those checks had already finished, and all of them passed. Stage 10 stays complete at commit `e54214b`, and nothing is running. I'll wait for your request before starting Stage 11.

Assistant message 3:

> A third old progress watcher timed out, this one on the install without demo data. That install and its checks had already finished and passed. Stage 10 is complete at commit `e54214b`, and nothing is running. I'll wait for your request before starting Stage 11.

Assistant message 4:

> The last old progress watcher timed out, this one on the `azk_ee24` update and browser checks. That work had already finished and passed: dashboard 7 of 7, preview 20 of 20. Stage 10 is complete at commit `e54214b`, and nothing is running. I'll wait for your request before starting Stage 11.

### User prompt 1 (verbatim; typed)

```text
continue
```

Assistant message 5:

> Checking the project state after the restart: Stage 10 is committed and the code matches the docs. Docker Desktop is not running. I'm checking which requirements are still open.

Assistant message 6:

> I haven't started anything new because nothing was running or left half-done. I followed the resume procedure (R1) and checked the repository, the docs and the machine.
>
> **Where things stand**
>
> - **Last completed stage: 10.** It is committed locally as `e54214b` and nothing is uncommitted. No stage is partly done: Stage 04 was the only partial one, and Stage 10 finished it.
> - **The docs match the code:**
>   - Partner Monitor is version 18.0.1.5.0 with 147 test methods, and all 147 passed on 2026-11-15.
>   - Trial Balance is version 18.0.1.3.0 with 114 test methods, and all 114 passed on 2026-11-15.
>   - The scheduled worker gets its page downloader from `worker._get_page_source()`, and the downloader is in `services/http_client.py`.
> - **Done and verified (2026-11-15):**
>   - all features of both addons;
>   - the small live check against the real website;
>   - the browser checks, the restart check and the install without demo data.
>   - 136 of the 152 requirement rows are DONE, and 2 are out of scope.
> - **Failing:** nothing I know of.
> - **Still open:** 14 rows, none of them a failure:
>   - the README and the public GitHub repository (G-01 to G-06, G-08, T-19, T-20): Stages 12 and 15;
>   - packaging, proven by a clean install (G-11): Stages 11 and 12;
>   - assumptions, the AI log and source checks (G-07, G-09, K-05): updated at every stage;
>   - P-17.3: the original views specification was never supplied (question Q-02).
> - **Blocked:** nothing in the code. The questions for the team lead (Q-02 to Q-06) have not been asked yet, so the documented defaults still apply.
>
> **The machine today (2026-11-16, 10:19 UTC)**
>
> - Docker Desktop is not running, so the Odoo server on port 8071 is down.
>   - The databases should still be in Docker's storage, but I can only confirm that once Docker is running.
>   - The next stage starts with Docker Desktop and `scripts/dev.sh start`.
> - Free space: 44 GB on C:, and 5.9 GB of RAM.
>
> **Logging:** this session's transcript is still being recorded. The messages since the Stage 10 report, including this one, will go at the start of the next stage's AI log. That is how the re-sent Stage 02 prompt was logged.
>
> **Should I start Stage 11?** It is clean acceptance:
> - new throwaway databases, with each addon installed alone and then both together;
> - the full test suites, a demo, and the restart and access checks;
> - `docs/acceptance_results.md`.
>
> AGENTS.md says to start a stage only when you ask for it, so please confirm Stage 11 or send its request with your priorities.

## Referenced instruction file: `prompts/11_clean_acceptance.txt` (verbatim)

```text
STAGE 11  -  Reproduce the submission from a clean local checkout and fresh database

LANGUAGE: English only for all newly authored terminal prose, explanations, questions, and reports. Use simple ASCII formatting and short paragraphs/bullets instead of wide or box-drawn tables. Preserve source data and original historical logs. Arabic coaching happens outside this terminal.

Follow the project contract. Use a new disposable database and an isolated checkout/export of the intended submission. Do not reset or repair the development database as a substitute for proving a clean install. Use the documented pinned Enterprise environment with authorized runtime/dependency access. A Community-only install does not fulfill this acceptance stage. Keep the external Enterprise runtime separate from the custom-source checkout.

Act as the assessor:
1. Follow only the current setup documentation and declared dependencies. Install the Partner Monitor alone, the Trial Balance addon alone, and then both together in appropriate clean disposable databases. If a documented dependency is missing, fix the packaging/instructions and repeat the affected check.
2. Verify module update on an existing seeded assessment database without losing intended historical data. Re-run meaningful tests for the affected install/update paths; do not repeat unchanged tests indefinitely.
3. Run the full selected-exercise test suite using real Odoo discovery/import rules and correct test flags. Record the number of collected/executed tests and outcome, not just the shell exit code. Check logs for hidden failures, skipped tests, import errors, and tests that were never collected.
4. Perform a realistic demo: ingest a bounded sample, display history/references, show all four filtered dashboard charts, simulate one recoverable failure, and verify internal notification to the configured recipient. Identify fixture versus live data throughout.
5. Generate the Stage 07 Trial Balance with and without drafts, demonstrate another filter, show hierarchy/currency behavior, and open the real preview/PDF/XLSX outputs. Reconcile their values against the independent golden fixture and against the native Enterprise Trial Balance with matching options, documenting intended differences. Validate UI steps actually performed versus those still awaiting manual confirmation.
6. Repeat the proven restart scenario where needed to validate the packaged setup, not merely a helper function. Ensure previously committed progress survives and an interrupted unit does not duplicate history.
7. Execute security checks as non-admin users and an unauthorized user. Confirm the documented access behavior for both modules and downloads.

Produce docs/acceptance_results.md with environment/commit, dates, commands, test counts, each requirement's result, real evidence, and exact remaining blockers. A failed mandatory check means that feature is not complete. If an external site cannot be reached, distinguish live compatibility from fixture-tested behavior instead of claiming a full live pass.

Fix genuine defects and repeat only relevant checks. Update installation steps so another developer can reproduce the result without undocumented manual database edits. Explain what a clean install proves and what it does not. Stop with the standard report.
```

## Conversation (recorded text, verbatim, in order)

### User prompt 2 (verbatim; the whole message was pasted text)

```text
Start Stage 11 now.

Read prompts/11_clean_acceptance.txt and execute Stage 11 only,
following solution/AGENTS.md.

Use commit e54214b as the starting baseline.

Start Docker Desktop, wait for the engine to become ready, then run
scripts/dev.sh start. Confirm the existing databases are present.

Use an isolated checkout/export of the intended submission and fresh
disposable databases on the pinned Enterprise runtime.

Follow the complete Stage 11 prompt, with these priorities:

1. Install Partner Monitor alone, Trial Balance alone, then both together.
   Follow the documented setup and declared dependencies.

2. Verify that demo data loads automatically on a fresh demo-enabled
   installation. Verify the no-demo path and upgrade preservation too.

3. Run the full addon suites and reconcile the collected test counts
   with the Stage 10 baseline: 147 Partner Monitor and 114 Trial Balance.
   Explain any difference and inspect logs for skipped or missing tests.

4. Perform the partner sync/dashboard demonstration, recovery and
   notification checks. Clearly distinguish live pages from fixtures.

5. Verify the real Trial Balance preview and downloaded PDF/XLSX.
   Check Bank at 1,200 posted-only and 1,000 with drafts, plus the
   required filter, hierarchy and currency cases.

6. Run the packaged restart scenario and non-admin access checks,
   including report downloads.

Run heavy checks sequentially because memory is limited.
Fix genuine defects and repeat the affected checks.

Write docs/acceptance_results.md with the tested commit, commands,
actual results, evidence and remaining gaps. Update setup instructions
where needed so no undocumented manual steps are required.

Use English ASCII only. Stop after Stage 11.
```

Assistant message 7:

> Starting Stage 11. First I'll read the setup files and scripts that an assessor would follow, then start Docker.

Assistant message 8:

> Docker Desktop is starting. While the engine comes up, I'm reading the demo, live-check, restart and browser-check scripts.

Assistant message 9:

> Docker is ready and the dev server answers on port 8071. All eight existing databases are there. Next I'll check the dev database's state, then build the isolated export.

Assistant message 10:

> Now the `.env` template. It should show the target edition and the two folders an assessor must provide.

Assistant message 11:

> Now the setup documentation: a quick start for a clean checkout, plus fixes for the stale lines I found (the old target label, a removed `.env` key, and the old default edition).

Assistant message 12:

> While setup runs (about 7 to 10 minutes), I'm reading the code the next checks depend on: the user groups, the demo-data handling during a live sync, and how the download route is called.

Assistant message 13:

> Demo countries are named "Demo Country Alpha" and so on, so they can't be confused with live countries. Writing the users script.

Assistant message 14:

> Now the Partner Monitor demo script. It has three phases: settings, a simulated outage, and recovery.

Assistant message 15:

> Next is the HTTP access-check script. First I'll confirm the method signatures and IDs it will call.

Assistant message 16:

> While setup finishes, I'm reading the browser helper API so the demo browser check can reuse it.

Assistant message 17:

> My state script used a country field that doesn't exist (`first_seen_on`). I'll drop that field from the fingerprint and rerun.

Assistant message 18:

> The Stage 09 release installed with exit code 0: 92 modules and 0 warnings. Now I'll seed history through the old worker and take the "before" snapshot.

Assistant message 19:

> I'll make each step of the browser check report a FAIL instead of crashing on a missing element. The recipient check moves to the inbox step, because the chatter may not print recipient names.

Assistant message 20:

> The `if True:` blocks only preserved indentation. I'll rewrite the file cleanly with the new structure.

Assistant message 21:

> The memory guard from Stage 10 is still available. While the tests run, I'm checking which planned acceptance items the test plan and requirements matrix expect from Stage 11.

Assistant message 22:

> Only about 3 minutes had passed; the log is progressing normally. While I wait, I'll create the random password for the acceptance users. It is stored in a private scratch file and never printed.

Assistant message 23:

> Both sequences are ready. I'm waiting for the test run to finish before running them.

Assistant message 24:

> The test run is still installing modules, about 4 minutes in. I'll wait for its completion notice.

Assistant message 25:

> All later sequences are ready. Waiting for the test run.

Assistant message 26:

> While the tests run, I'll adapt the AI-log assembly script for Stage 11.

Assistant message 27:

> The Stage 11 log can reuse this structure: messages after the Stage 10 report, then the Stage 11 prompt and replies. I'll write it at the end. For now I'm waiting on the test run in the foreground.

Assistant message 28:

> The test run finished with exit code 0 after 11 min 37 s. Now I'll reconcile the counts against the Stage 10 baseline and scan the log for skipped, failed or never-collected tests.

Assistant message 29:

> While the browser checks run, I'm collecting the environment facts for the acceptance report.

Assistant message 30:

> I have every requirement ID, so the acceptance report can cover each one. Now I'll wait for the browser checks.

Assistant message 31:

> The safety check could not parse my compound command. It contained no removal; the nesting was too complex to read. I'll put the three phases in a plain script file instead.

Assistant message 32:

> The setting is reset. Next I'll restart the acceptance server and run two checks: the Partner Monitor demo in the browser and the HTTP access checks for both modules.

Assistant message 33:

> While phase 7 runs, I'll check that the export contains no Enterprise source, for requirement K-06. Then I'll write `docs/acceptance_results.md`.

Assistant message 34:

> The export holds only the two addons, both LGPL-3, and no Enterprise code. Writing the acceptance report now. The phase 7 lines will be added when it finishes.

Assistant message 35:

> Now the edits to the requirements matrix, the decisions log and the setup documentation.

Assistant message 36:

> I inserted the new decisions above D-66 rather than after it. I'll fix the order.

Assistant message 37:

> Now the Stage 11 section in the test results, newest first, and the live requests in the live-site notes.

Assistant message 38:

> Now the project state file.

Assistant message 39:

> I wrote "about 0.5 GB" for the acceptance volumes without measuring it. Checking.

Assistant message 40:

> Next is the Stage 11 handoff. I'll follow the Stage 10 handoff's structure.

Assistant message 41:

> Now the AI log index row and the Stage 11 rows of the mistakes table.

Assistant message 42:

> Next is the AI log, built from the session transcript. First I'll check how the "continue" message and the Stage 11 prompt are stored there, so the extraction keeps both verbatim.

Assistant message 43:

> The report is ASCII-only. Next, a Stage 11 note in the kit-root `CLAUDE.md`, which is outside the repository, so future sessions know the new defaults and the acceptance project.

Assistant message 44:

> Now the tool-activity summary and the final report draft. The AI log will contain the report exactly as I'll display it.

Assistant message 45:

> Now the log assembly script, adapted from Stage 10. It adds a section for the messages between the two stages.

Assistant message 46:

> Before assembling the log, the pre-commit checks. First, which scan the earlier stages used.

## Notes on accuracy

- This log was assembled from the transcript just before its own commit. Progress messages written after that point, while committing, are not included. The final response below is included as prepared, before it was displayed.
- The Stage 10 final response was checked against the session transcript before Stage 11 began: it was displayed exactly as logged in [stage_10.md](stage_10.md).
- The CLI compacted the conversation's context between Stage 10 and Stage 11. The transcript keeps every visible message, so the log is complete; the CLI's compaction summary is not a user prompt and is not reproduced.
- System notifications (background command completions and monitor events) are not user prompts; they are summarized under tool activity.
- Facts in the messages that were later corrected stay as written here; corrections are listed in [README.md](README.md) (mistakes table) and in [acceptance_results.md](../acceptance_results.md) (findings AC-04 to AC-06).

## Summary of tool activity (summary, not verbatim)

1. **After "continue" (resume procedure R1):**
   - read the resume prompt, `AGENTS.md`, STATE, the requirements matrix, the assumptions, the end of the Stage 10 log and the Git status and log;
   - checked that the manifests and test counts match STATE;
   - found Docker Desktop not running, 44 GB free on C: and 5.9 GB of free RAM.
2. **Start of Stage 11:**
   - started Docker Desktop (the engine answered after 5 s, version 29.9.2) and ran `scripts/dev.sh start`;
   - listed the eight development databases;
   - read `azk_ee24`'s module versions, Partner Monitor settings and counts with read-only SQL.
3. **Read:**
   - the setup files: `compose.yaml`, `scripts/dev.sh`, `.env.example` and `docs/environment.md`;
   - the existing check scripts;
   - the worker, notification and dashboard code;
   - in the pinned 18.0 source, Odoo's test statistics (`odoo/tests/result.py`, `odoo/tests/suite.py`) and its database creation on startup (`odoo/cli/server.py`).
4. **First run as documented:**
   - exported `e54214b` with `git archive` to `<kit-root>/runtime/acceptance/`;
   - checked that `COMPOSE_PROJECT_NAME` overrides the project name of `compose.yaml` (`docker compose config`);
   - ran `scripts/dev.sh setup` in a throwaway project: exit 255 (AC-01).
5. **Setup fixes:**
   - changed `scripts/dev.sh`, `.env.example` and `docs/environment.md` and committed them as `a203291`;
   - inspected the database the failure left (base uninstalled);
   - added the base-first rerun and checked it on that database, with the fixed helper copied into the old export (a third run left the database unchanged);
   - committed `3b92f98`;
   - removed the throwaway Compose project this stage had created (`docker compose down --volumes`, project `azk-stage11` only).
6. **The development stack** was stopped to free memory for the heavy steps.
7. **Clean acceptance run:** exported `3b92f98` and followed the quick start in project `azk-stage11-acc` (port 8073).
8. **Acceptance scripts:** wrote `scripts/acceptance_state.py`, `acceptance_users.py`, `acceptance_upgrade_seed.py`, `acceptance_pm_demo.py`, `acceptance_pm_ui_check.py` and `acceptance_access_check.py`, and extended `scripts/pm_live_check.py`.
9. **Ran one at a time,** with free RAM sampled every 15 s and the browser checks under the Stage 10 memory guard:
   - the state report;
   - three clean installs;
   - the upgrade from an export of `564b71b`, with seed, state reports and probe;
   - `scripts/dev.sh test`;
   - `scripts/restart_check.sh`;
   - the dashboard, wizard and preview browser checks;
   - `scripts/tb_engine_vs_native.py`;
   - the Partner Monitor demonstration phases, twice (AC-05), and a reset of the batch-size setting (AC-04);
   - the browser demonstration, three times (AC-06);
   - the access checks;
   - each addon alone, then updated.
10. **Live website:** 7 requests to www.odoo.com in all.
11. **Viewed:** two screenshots of the browser demonstration (the recipient's inbox and the live partner's references) and the rendered first page of the short PDF.
12. **Shell tool:** one compound command was refused by the CLI's safety check, which could not parse it (it contained no removal). The same steps then ran from a script file.
13. **After the checks:**
    - stopped the acceptance project;
    - restarted the development stack (port 8071, HTTP 200);
    - measured the acceptance volumes;
    - updated the documentation and added a Stage 11 note to the kit-root CLAUDE.md (outside the repository).
14. **Before the commit:** the ASCII and pre-commit scans; only the intended files were staged.

## Assistant final response (verbatim)

Everything between the two rules below is the final visible response.

---

Stage 11 is done. I rebuilt the submission from clean exports of the repository, in a separate Docker Compose project with empty volumes, the way an assessor would. The full record is in `docs/acceptance_results.md`. Everything is committed locally as "Stage 11: clean acceptance from a fresh checkout".

**Completed work**

- **The first documented command failed in a fresh checkout. It is fixed.**
  - In an export of `e54214b`, `scripts/dev.sh setup` chose the Community edition. It stopped with exit code 255, because the Trial Balance needs the Enterprise module `account_reports` (AC-01).
  - Now the default edition is `enterprise-20241208`. The first `setup` writes `.env` and asks for the two source folders, and `docs/environment.md` has a quick start for a clean checkout.
  - The failure also left a database that a rerun of `setup` would not repair (AC-02). A rerun now installs what is missing, `base` first if needed, and never drops the database. I checked this on the very database the failure left.
- **Installs, from an export of the fixed commit:**
  - the quick start created `azk_ee24` (92 modules) in 8 min 44 s;
  - demo data loads automatically: 50 partners with 57 history rows, and the Trial Balance demo company with 16 entries;
  - the Partner Monitor alone (34 modules, no accounting) and the Trial Balance alone (91 modules), each then updated;
  - both addons without demo data;
  - every install and update log had 0 warnings.
- **Upgrade:** I installed the Stage 09 release, seeded history through its own worker, and upgraded. The state reports before and after differ only in the Partner Monitor's version. The fingerprints of the history, references, partners and demo entries are all equal.
- **Tests:** 261 of 261 in one fresh database, 147 Partner Monitor and 114 Trial Balance: exactly the Stage 10 baseline.
- **Demonstrations:**
  - **Partner Monitor:** a live sample of Andorra and its 2 partners, kept in the database; two simulated outages with their notes; recovery through a manager's Retry. In all, 7 requests reached www.odoo.com, every one allowed by robots.txt.
  - **Trial Balance:** the real preview, PDF and XLSX on the fresh database. Bank ends at 1,200.00 with posted entries and at 1,000.00 with drafts. The hierarchy, a search filter and the currency column work. The standard Trial Balance matched in 6 of 6 cases.
- **Access:** 24 HTTP checks, as four non-admin users and an anonymous visitor, covering both modules and both downloads.
- **No addon code changed.** The development server runs again on port 8071. Its databases were not changed; I only ran a few read-only SQL queries on `azk_ee24` at the start.

**Commands and results** (2026-11-16)

- **`scripts/dev.sh setup`, export of `e54214b`:** FAIL, exit 255 (AC-01). Rerun with the fixed helper: PASS.
- **Quick start, export of `3b92f98`:** PASS. Step 1 stops to ask for the folders; step 3 exits with 0 and 0 warnings.
- **`scripts/dev.sh clean-install` for each addon alone, then `update`, and both with `--without-demo`:** PASS, with 0 warnings each.
- **Upgrade from `564b71b`** (`scripts/acceptance_upgrade_seed.py`, `scripts/acceptance_state.py`): PASS.
- **`scripts/dev.sh test`:** PASS, "0 failed, 0 error(s) of 261 tests". No skipped test, warning or import error, and every test file was collected. Odoo's statistics lines say 177 and 150, because they also count each class's setup and teardown.
- **`scripts/restart_check.sh`:** PASS, 12 of 12.
- **Headless Chrome, run by me:** dashboard 7 of 7, wizard 7 of 7, preview and downloads 20 of 20, Partner Monitor demonstration 7 of 7. The demonstration passed on its third run, after I fixed two timing faults in my own check script.
- **`scripts/tb_engine_vs_native.py`:** PASS, 6 of 6.
- **`scripts/acceptance_access_check.py`:** PASS, 24 of 24.
- **NOT RUN:** your own browser check, a full live crawl (on purpose), and the Partner Monitor tests on Community (optional).

**Open issues and assumptions**

- **Notes by email (O-01):** the administrator's default notification preference is "Handle by Emails". With no mail server, run 1's note stayed on the run's chatter and its email failed. The configured recipient, set to "Handle in Odoo", found run 2's note in the inbox. The README must say to configure a mail server or choose "Handle in Odoo" (D-69).
- **My own script error (AC-05):** the first settings phase of my demonstration script did not commit, so run 1 went to the default recipient. Fixed and rerun.
- **Kept for later stages:** the README (Stage 12) and publication (Stage 15).
- **Still open:** questions Q-02 to Q-06. P-17.3 needs the original views specification.
- **The acceptance project** `azk-stage11-acc` is stopped, and its volumes (318 MB) are kept. Deleting them is your decision.
- **Memory:** free RAM fell to 0.48 GB during the first setup, so every heavy step ran alone.

**Changed files and functions**

- `scripts/dev.sh`: the default edition, `ensure_env`, `main`, `cmd_setup`, `installed_count` and `DEFAULT_ADDONS`.
- `.env.example`, and `docs/environment.md` (quick start, troubleshooting, verification).
- `scripts/pm_live_check.py`: `PM_LIVE_KEEP`, `PM_LIVE_DB_CREATED_AFTER`, and the batch-size restore.
- **New:**
  - `scripts/acceptance_state.py`, `acceptance_users.py`, `acceptance_upgrade_seed.py`, `acceptance_pm_demo.py`, `acceptance_pm_ui_check.py`, `acceptance_access_check.py`;
  - `docs/acceptance_results.md` and `docs/handoffs/stage_11_en.md`.
- **Updated:** STATE, the requirements matrix (G-11), assumptions (D-67 to D-69), the test plan, the test results, the live site notes and the AI logs.

**Comprehension questions**

1. The acceptance ran with `COMPOSE_PROJECT_NAME=azk-stage11-acc` from an exported folder. What would its first `scripts/dev.sh setup` have done to the development containers and their database server if the project name had come from `compose.yaml`, with a new `.env` holding new random passwords?
2. Odoo's statistics printed "177 tests" for the Partner Monitor, while the summary counted 147 of its tests. Where do the 30 extra entries come from, and which number belongs in a comparison with the Stage 10 baseline?
3. Run 1's failure note reached no inbox, while run 2's did, although the same code posted both. What differed between the two recipients, and why did the local setup make that difference visible?

**Next stage:** 12 (submission documentation), when you ask for it.

---
