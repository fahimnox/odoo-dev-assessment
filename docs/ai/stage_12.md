# Stage 12 - Submission documentation

- **Date:** 2026-11-16
- **Tool / model:** Claude Code, Opus 5.5 (`claude-opus-5-5`), in the same CLI session as Stages 01B to 11, after a context compaction at the end of Stage 11
- **Working directory:** the assessment kit root (`<kit-root>`) and `<kit-root>/solution`
- **Commit:** this log is part of the Stage 12 commit (tagged `submission-rc1` afterwards)

**Transcription method:** see [README.md](README.md). The user prompts and the referenced instruction file are verbatim. The assistant messages are the visible text blocks recorded in the CLI's local session transcript, verbatim and in order, extracted by a script. Tool calls, tool outputs, reasoning blocks and system notices are not reproduced.

**Redactions:** absolute local paths are replaced with `<kit-root>`, `<home>` or `<scratchpad>`. The CLI's paste markers around the user's pasted text are omitted. The random passwords of the throwaway database used in this stage never appeared in the recorded text; they stayed inside a script run by a tool call, which is not reproduced. The Git identity's email address does not appear in the recorded text.

## Between Stage 11 and Stage 12 (recorded text, verbatim, in order)

The CLI compacted the conversation's context at the end of Stage 11, after its commit. The assistant then displayed the Stage 11 final report (logged in [stage_11.md](stage_11.md)), and the user pasted the Stage 12 request. Nothing else was recorded between them.

## Referenced instruction file: `prompts/12_submission_documentation.txt` (verbatim)

```text
STAGE 12  -  Prepare the final submission documentation and reviewable package

LANGUAGE: English only for all newly authored terminal prose, explanations, questions, and reports. Use simple ASCII formatting and short paragraphs/bullets instead of wide or box-drawn tables. Preserve source data and original historical logs. Arabic coaching happens outside this terminal.

Follow the project contract. Read the actual code, requirements matrix, test evidence, and unresolved findings. Rewrite documentation to describe the final implementation, not an earlier plan or an idealized solution. Do not invent outputs, explanations of absent code, or features that remain unfinished.

Prepare:
1. README.md: selected exercises and scope; confirmed Enterprise target, independently recorded major-version confirmation and pinned core/Enterprise builds; declared dependencies and authorized runtime-access prerequisites; exact install/start/configuration/update/test commands; module features; user demo steps; known assumptions/limitations; what is complete and pending; evidence links; and concise AI-use disclosure. Explain that Exercise 3 is intentionally unselected.
2. docs/architecture.md and docs/resilience.md: actual model/component relationships, daily scheduling, separate validation jobs, work units, commit boundaries, checkpoint/replay behavior, idempotency, overlap control, retry limits, incremental-fetch strategy and limitations, partial-snapshot safety, and failure notification.
3. docs/calculation_contract.md: actual opening/movement/ending convention, company/state/date filters, currency grouping, analytic allocation assumption, hierarchy, zero filtering, observed Enterprise baseline behavior, matched-option comparison evidence, cross-year semantics and documented deviations; no unsupported promise of complete standard-report parity. Include the small worked example and verified expected values.
4. docs/test_results.md and docs/acceptance_results.md: commands, environment/commit, executed test counts, passed/failed/blocked/not-run checks, screenshots/exports only where actually produced, and clean-install verification.
5. docs/ai/README.md: an index of the real prompts and visible outputs captured from the start, tool/model identity only when known, representative mistakes found and corrected with evidence, and redactions/omissions. A template or reconstructed summary is not an execution transcript; label it accurately. Include only visible user/model text, not hidden reasoning or private system prompts.
6. docs/demo_script.md: a 5-8 minute walkthrough with exact menus/actions, fixture/live labels, the expected report numbers, one failure/recovery story, and where to find the relevant code. Document a fixture-based demo fallback if live connectivity is unavailable, without concealing that limitation.
7. A concise release checklist, a final requirement matrix, and an unambiguous pending-work section. Keep personal study/coaching notes outside the public solution repository.

Ensure the repository contains installable addons, required code/assets, small tests/fixtures, configuration examples, and enough setup documentation. Exclude Odoo core and Enterprise source, private vendor snippets or source dumps in AI logs, virtual environments, caches, database/filestore dumps, actual .env files, secrets, the supplied assessment PDF, and the prompt kit itself unless the assessor explicitly requests them. Small synthetic examples and sanitized AI logs belong in the submission.

Review the exact files intended for publication and create a local release checkpoint. Do NOT push or create a public repository in this stage. Tell me in English what I can honestly demonstrate now and which specific limitations I must mention. Stop with the standard stage report.
```

## Conversation (recorded text, verbatim, in order)

### User prompt 1 (verbatim; the whole message was pasted text)

```text
Read prompts/12_submission_documentation.txt and execute Stage 12 only,
following solution/AGENTS.md.

Use the final Stage 11 code and docs/acceptance_results.md as the
verified baseline. Prepare the complete documentation and local
submission package required by the Stage 12 prompt.

Priorities:

1. Base README.md on the clean-checkout quick start actually verified
   in Stage 11. Document the default Enterprise edition, pinned runtime,
   required external source folders, setup, start, update and tests.

2. Explain isolated acceptance with COMPOSE_PROJECT_NAME and the
   consequences of reusing an existing project's volumes with a new
   environment file.

3. Document failure notifications:
   configure an outgoing mail server for email delivery, or select
   "Handle in Odoo" for the configured recipient.
   Distinguish chatter messages, inbox notifications and email delivery.

4. Report 261 executed test methods: 147 Partner Monitor and 114 Trial
   Balance. Explain the additional setup/teardown statistics separately.

5. Prepare a reproducible 5-8 minute demo covering both addons,
   Bank at 1,200 posted-only and 1,000 with drafts, and one
   failure/recovery example. Clearly label fixture versus live data.

6. Keep unanswered questions Q-02 to Q-06 and the missing views
   specification visible. Label defaults as assumptions, not approvals.
   Describe the actual bounded live checks and measured limitations.

7. Review the intended publication files and Git history for secrets,
   private vendor content and unsuitable artifacts. Keep external
   Community/Enterprise runtime source outside the submission.
   Preserve truthful AI logs with clearly marked redactions.

Check documentation links, commands, filenames and consistency.
Rerun application checks only when relevant code or configuration changes.

Create a local release checkpoint. Publication remains Stage 15.
Explain what is ready to demonstrate and what remains pending.

Use English ASCII only. Stop after Stage 12.
```

Assistant message 1:

> Reading the Stage 12 prompt, the contract and the current documentation before writing anything. The repository has no README yet, and no demo script or release checklist.

Assistant message 2:

> Still gathering facts for the docs: confirming Odoo 18's own labels for the notification preference and the outgoing mail server, so the README names them exactly.

Assistant message 3:

> Next I'm reading the resilience design and the calculation contract, which this stage must bring up to the final implementation.

Assistant message 4:

> Reading the rest of the calculation contract to find statements that the later stages made outdated.

Assistant message 5:

> Checking the setup helper's commands, so every command in the README is one it really accepts.

Assistant message 6:

> The first attempt created nothing (a path-conversion mistake in my script: Git received a POSIX path while path conversion was off). Fixing and rerunning.

Assistant message 7:

> Now a read-only look at the Stage 11 acceptance database, which the demo script will use as the prepared demo state (database container only, stopped again afterwards).

Assistant message 8:

> Writing the README next. First, two last label checks: the Partner Monitor group names, and the accounting read-only group's name.

Assistant message 9:

> Checking one more claim before I write it down: that `COMPOSE_PROJECT_NAME` takes effect whether it is exported in the shell or written in `.env` (a dry `docker compose config`, nothing is created).

Assistant message 10:

> Confirmed: an exported variable, a `COMPOSE_PROJECT_NAME` line in `.env`, and the `-p` option all override the fixed project name. Nothing was created.
>
> Now writing the README.

Assistant message 11:

> I have exact labels now: the report's options button reads "Posted Entries" and becomes "With Draft Entries" after ticking "Draft Entries". Writing the demo script.

Assistant message 12:

> Verifying two demo-script claims: whether the administrator holds the Partner Monitor Manager group (needed to see Errors and Work Items), and the dashboard's overlap message.

Assistant message 13:

> Now the calculation contract: a reviewer summary at the top, and fixing the two outdated statements about fiscal years and branches.

Assistant message 14:

> Now the two stale lines outside `docs/`: the fixtures README and a script comment (comment-only, no code change).

Assistant message 15:

> Now the requirements matrix: final statuses for the README rows, and an honest status for T-19 (the candidate's own manual check is still pending, so it stays IN PROGRESS).

Assistant message 16:

> Matrix and assumptions updated. Next is the publication review: scanning the files to be published, and every blob in the Git history, for secrets, local paths, personal data and copied vendor code.

Assistant message 17:

> All links and anchors resolve except `release_checklist.md`, which I write next. First, a check that every helper command and file path named in the README and demo script exists:

Assistant message 18:

> Every helper command and path named in the documents exists; only the release checklist is still missing. Running two harmless commands from the README as written:

Assistant message 19:

> Both commands work as documented, and `.env` is ignored by Git. Writing the release checklist with the review results and the pending work:

Assistant message 20:

> Now `STATE.md`: the Stage 12 entry, the stage table, next step and open items.

Assistant message 21:

> Now the AI log index: the Stage 12 row, the redaction note, and this stage's mistakes so far.

Assistant message 22:

> Writing the Stage 12 handoff.

Assistant message 23:

> Now the final report draft (it goes into the AI log verbatim, then is displayed):

Assistant message 24:

> Now the AI-log tooling: a tool-activity summary and the assembler, adapted from Stage 11. The assembler also checks that the Stage 11 report I displayed matches its log.

Assistant message 25:

> Only `stage_12.md` is still missing. Assembling a first version of it to verify the assembler and the Stage 11 comparison:

Assistant message 26:

> The Stage 11 report I displayed matches its log exactly. One line in the new log still says "Stage 11 commit"; fixing the assembler and checking the rest of the log:

Assistant message 27:

> The log is clean: no local paths, no personal data, 25 assistant messages, and the Stage 11 comparison is recorded. Now the final verification pass over everything: links, publication review, ASCII.

Assistant message 28:

> Two README statements need correcting after the matrix work: the top status mentions only P-17.3 (T-19 is also open), and the decision range should now end at D-70.

## Notes on accuracy

- This log was assembled from the transcript just before its own commit. Progress messages written after that point, while committing, are not included. The final response below is included as prepared, before it was displayed.
- The Stage 11 final response, as displayed at the start of this part of the session, was compared by the assembling script with the final-response section of [stage_11.md](stage_11.md): identical.
- The CLI compacted the conversation's context at the end of Stage 11. The transcript keeps every visible message, so the log is complete; the CLI's compaction summary is not a user prompt and is not reproduced.
- System notices (for example the CLI's reminders that the user had not heard from the assistant for a while) are not user prompts and are not reproduced; the short progress messages they prompted are.
- Facts in the messages that were later corrected stay as written here; corrections are listed in [README.md](README.md) (mistakes table).

## Summary of tool activity (summary, not verbatim)

1. **Read the instructions and the state:** the Stage 12 prompt file, `AGENTS.md`, STATE, the requirements matrix, the assumptions (missing inputs, working assumptions, decisions, open questions), the Stage 11 acceptance results, the environment guide, the architecture, resilience and calculation documents, the test results and test plan, the AI log index, the live-site notes and part of the review findings; the Git status and log.
2. **Read the code for exact names and labels:** both manifests, the Partner Monitor menus, settings view, sync views, security groups and dashboard template, the notification and retry methods, the Trial Balance wizard view and fields, its filter bar, its demo data, the setup helper (`main`, `cmd_setup`, the usage text), `compose.yaml`, the role script and the check scripts' headers.
3. **Read the pinned Odoo 18.0 sources by name:** the notification preference of `res.users` and where it is shown, the "Use Custom Email Servers" setting and the outgoing mail server menu, the user menu's "Preferences" item, the accounting groups and their implications, the Technical menus (Automation, Parameters), the `account_reports` "Audit Reports" menu and the report's "Draft Entries" option.
4. **Checks run in this stage:**
   - the volume-reuse check on a throwaway Compose project `azk-s12-envcheck`, database service only, with random passwords that were never printed; its first run exported nothing because of a path mistake in the check script and created no resource; the second run gave the result; the project was removed and the other projects were confirmed unchanged;
   - the project-name precedence with `docker compose config` in a scratch folder (no resource created);
   - read-only SQL on the Stage 11 acceptance database (its database container was started, queried and stopped);
   - the committed sample exports read with openpyxl from the private tools environment, and the short sample PDF's text with `pdftotext`;
   - the dashboard tests' expected numbers read from the test file;
   - `scripts/dev.sh help` and `scripts/dev.sh status`.
5. **Documents written and updated:** the README, the demo script, the release checklist, the handoff; the architecture, resilience and calculation documents; the requirements matrix (rows updated by a small script, then counted by another; see the mistakes table), the assumptions, the test results and test plan, the acceptance note, STATE and the AI index; the Partner Monitor fixtures README and one comment in `scripts/fixture_sync_demo.py`.
6. **Review scripts:**
   - a publication review over the files to publish and every blob of the Git history (secret values compared without printing them, keys, tokens, local paths, email addresses, vendor license headers, large files, deleted paths, commit messages);
   - a comparison of every published line with the lines of the four Enterprise modules the solution uses;
   - a non-ASCII scan, a link and anchor check with GitHub's heading rules, and a check of the commands and paths named in the documents.
7. **Before the commit:** this log was assembled from the session transcript; the checks were run again on the final files; only the intended files were staged. After the commit: the annotated tag `submission-rc1` (local), and a Stage 12 note in the kit-root CLAUDE.md (outside the repository).

## Assistant final response (verbatim)

Everything between the two rules below is the final visible response.

---

Stage 12 is done. The submission now has its README, a demo script, a release checklist and a final requirement matrix, and the design documents describe what was actually built. Everything is committed locally as "Stage 12: submission documentation and local release checkpoint" and tagged `submission-rc1`. Nothing was pushed.

**Completed work**

- **README.md**, written from the code and the recorded evidence:
  - the installation is the quick start that Stage 11 followed literally from a clean checkout;
  - it states the Enterprise target (confirmed by the team lead) and that 18.0 is our assumption (Q-04), with the pinned Community commit, Enterprise build and images;
  - it lists the external folders you need: the public Community source, and the proprietary Enterprise addons, which need authorized access;
  - setup, start, update and test commands, then the testing story: 261 executed test methods (147 + 114), and why Odoo's statistics lines say 177 and 150 (each test class's setup and teardown are counted too).
- **Isolated copies (README section 6):** how `COMPOSE_PROJECT_NAME` separates a second copy, and what happens when a new `.env` meets an existing project's volumes. I checked this on a throwaway project instead of assuming it:
  - the database container was recreated, but the volume and its databases were kept;
  - the new password was refused ("password authentication failed for user "odoo""), and the old one still worked;
  - the container's local socket needed no password, which is why `setup` cannot notice the mismatch.
- **Failure notes (README section 7):** the note is always on the run's chatter. It reaches the Discuss inbox only for a recipient set to "Handle in Odoo"; with "Handle by Emails" (the default), it is sent by email, which needs an outgoing mail server.
- **docs/demo_script.md:** about 7 minutes, with exact menus, the DEMO, LIVE, FIXTURE and SIMULATED labels, the expected numbers and one failure-and-recovery story. It also has an offline fallback that says what it cannot show.
  - The numbers come from the committed sample exports and the tests: Bank 1,200.00 posted only, then 1,000.00 with drafts.
- **docs/release_checklist.md:** the publication review, your decisions before Stage 15, and the pending work.
- **Updated to the final implementation:**
  - `architecture.md` gets a new section 0; its intro still said later parts were "not implemented yet";
  - `resilience.md` gets a map of topics, the three delivery channels, and partial-snapshot safety;
  - `calculation_contract.md` gets a reviewer summary, and now records the Stage 10 comparisons of fiscal years and branches;
  - `test_results.md`, `test_plan.md`, `assumptions.md` (D-70: no license file until Q-06), STATE and the AI index.
- **Final matrix:** 147 of 152 rows DONE.
  - P-17.3 stays IN PROGRESS: the original views specification was never supplied.
  - T-19 stays IN PROGRESS: your own manual check has not been done.
  - G-01 (publication) is NOT STARTED.

**Commands and results** (2026-11-16)

- **Application checks:** NOT RUN again. No addon code, configuration or setup script changed; the Stage 11 results remain the evidence. The only files changed outside `docs/` are a fixtures README and one script comment.
- **Volume reuse with a new `.env`** (throwaway project `azk-s12-envcheck`, database only, then removed): PASS, the documented behavior was observed. Its first run failed on my own script's path handling and created nothing.
- **`docker compose config`:** PASS. An exported `COMPOSE_PROJECT_NAME`, a line in `.env`, and `-p` all override the project name.
- **Read-only SQL on the Stage 11 acceptance database:** its runs, errors, notes and settings match `acceptance_results.md`; the demo script uses this state.
- **Link check:** PASS, 434 relative links and anchors in 50 Markdown files, 0 broken.
- **Commands and paths** named in the README and the demo script: PASS. `scripts/dev.sh help` and `status` ran as written.
- **ASCII:** PASS for every new or changed document.
- **Publication review** (198 files, and every blob of the 24 commits): PASS. There is no secret value, key, token, local user path, vendor license header or copied Enterprise code. The only shared lines are imports, hook signatures and standard field names.

**What you can demonstrate now**

- A clean install from the README (about 9 minutes here), then `scripts/dev.sh test`: 261 tests pass.
- **Partner Monitor:**
  - the dashboard on demo data, with Status, Year and Country filters acting on all four charts;
  - the live Andorra sample of 2026-11-16, with BDR GROUP SLU's 17 references;
  - two simulated outages, their notes, and the recovery by a manager's Retry;
  - paused downloads.
- **Trial Balance:** the wizard, the preview (Bank 1,200.00, then 1,000.00 with drafts), the hierarchy, currency rows, and the PDF and XLSX.
- The crash-and-restart check: offline, 12 of 12.

**Limitations you must mention**

- **Version:** 18.0 is unconfirmed. Only the 2024-12-08 matched pair was tested, on one Windows machine, with a trial database.
- **Live website:** only bounded live samples were read (39 requests over three days). A full crawl was never run, and multi-process mode was not tested.
- **Views:** the views and the wizard layout are our proposal, because the specification and the mockup were never supplied.
- **Trial Balance scope:** analytic filtering selects whole journal items, a report covers one company, and parity with the standard Trial Balance is claimed only for the compared cases.
- **Notifications:** without a mail server, notes reach an inbox only with "Handle in Odoo".
- **Who checked the screens:** the browser checks were scripted by the AI agent; your own manual check is pending.

**Open issues and assumptions**

- **Your decisions before Stage 15** (checklist section 4):
  - your work email is in all 24 commits and in four documents; a rewrite must happen before the first push;
  - the license file (Q-06);
  - the manual check;
  - whether to ask Q-02 to Q-06 first;
  - the tag.
- The Stage 11 acceptance project (318 MB of volumes) is kept for the demo.
- Q-02 to Q-06 are still unasked; the defaults stand and are labeled as assumptions.

**Changed files**

- **New:** `README.md`, `docs/demo_script.md`, `docs/release_checklist.md`, `docs/handoffs/stage_12_en.md`, `docs/ai/stage_12.md`.
- **Updated:**
  - `docs/architecture.md` (section 0), `docs/resilience.md` (sections 1, 10, 13, 16, 17), `docs/calculation_contract.md` (sections 0, 5, 14);
  - `docs/requirements_matrix.md`, `docs/assumptions.md`, `docs/test_results.md`, `docs/test_plan.md`, `docs/acceptance_results.md`;
  - `docs/STATE.md`, `docs/ai/README.md`;
  - `addons/azk_odoo_partner_monitor/tests/fixtures/README.md`, `scripts/fixture_sync_demo.py` (a comment only).

**Comprehension questions**

1. A second checkout runs its first `scripts/dev.sh setup` without its own project name, writing a new `.env` with new passwords. Why does `setup` then report that `azk_ee24` "already exists", and why can the web server still not connect to PostgreSQL?
2. In the demo company, Bank opens January 2026 at 1,000.00, ends at 1,200.00 with posted entries only, and ends at 1,000.00 with drafts included. Which journal entries explain each number, and which two entries never count?
3. The checklist says that rewriting the commits' author must happen before the first push. Why would hiding the email address be much harder after publication?

**Next stage:** 13 (code walkthrough), when you ask for it.

---
