# Stage 09 - Trial Balance outputs (Preview, PDF, XLSX)

- **Date:** 2026-11-15
- **Tool / model:** Claude Code, Opus 5.5 (`claude-opus-5-5`), in the same CLI session as Stages 01B to 08
- **Working directory:** the assessment kit root (`<kit-root>`) and `<kit-root>/solution`
- **Commit:** this log is part of the Stage 09 commit

**Transcription method:** see [README.md](README.md). The user prompts and the referenced instruction file are verbatim. The assistant messages are the visible text blocks recorded in the CLI's local session transcript, verbatim and in order, extracted by a script. Tool calls, tool outputs, reasoning blocks and system notices are not reproduced.

**Redactions:** absolute local paths are replaced with `<kit-root>`, `<home>` or `<scratchpad>`. The CLI's paste markers around the user's pasted text are omitted. No credential or subscription value appeared in the recorded text; the local web login reached the browser check through environment variables, in tool calls that are not reproduced.

## Referenced instruction file: `prompts/09_trial_balance_outputs.txt` (verbatim)

```text
STAGE 09  -  Complete on-screen preview, PDF, and XLSX from the same report data

LANGUAGE: English only for all newly authored terminal prose, explanations, questions, and reports. Use simple ASCII formatting and short paragraphs/bullets instead of wide or box-drawn tables. Preserve source data and original historical logs. Arabic coaching happens outside this terminal.

Follow the project contract. Use the tested calculation engine from Stage 08. Use the inspected Enterprise report preview/export extension points where suitable, with declared dependencies and any necessary adapters. Do not create three independent calculation implementations, copy vendor source, or patch core modules.

PREVIEW
Implement an Odoo-integrated dynamic preview with the selected filters, search, hierarchy/expand-collapse where relevant, subtotal/parent styles, currency identification, and a useful no-results state. Match Odoo's normal visual conventions using the actual Enterprise report UI/extension hooks first, or a thin client action only where a documented requirement needs it. Changing a filter must recalculate the report. Do not substitute a static HTML download for the requested on-screen preview.

PDF
Use the verified native Enterprise PDF export/report-template hooks where suitable, or a justified custom Odoo report action/QWeb template for remaining requirements. Keep the shared calculation contract and real supported PDF renderer. Include company, dates, selected filters, and all nine required numeric columns: Initial Debit/Credit/Balance; Movement Debit/Credit/Balance; Ending Debit/Credit/Balance. Include the requested Amount Currency column when enabled, with a clear currency and documented time scope. Choose a paper format that keeps columns readable, repeat table headers on long reports, and prevent clipping. Preserve hierarchy and meaningful totals. Render the actual PDF and inspect it; a successful function return alone is not layout verification.

XLSX
Use native Enterprise XLSX export hooks where they meet the specification, or a justified extension/custom writer for gaps. Generate a real XLSX file, not CSV renamed .xlsx. Keep numeric cells numeric, currency formats meaningful, group/subtotal structure readable, headers frozen where useful, and widths reasonable. Include company/date/filter metadata. Write account names/codes as text and avoid evaluating user-controlled strings as formulas. Keep different transaction currencies separate. Avoid subtotal double-counting if formulas are used.

CONSISTENCY AND ACCESS
All three outputs must use the same normalized filter contract and engine. Make exports reflect the current preview selection. Either reuse the same report snapshot or document live recalculation and test equivalence against an unchanged database. Enforce access when reading the wizard/result and generating/downloading the file. A public download URL must not expose accounting records. Prevent one user's result from being reused by another.

TEST AND DEMONSTRATE
- Verify all three outputs for posted-only, drafts enabled, hierarchy, parents-only, amount currency, analytics, zero filtering, and an empty result.
- Compare numeric cell values and row identities in XLSX with engine results. Check actual PDF text/values and inspect at least a short and multipage PDF visually. Verify preview data/filters with real browser interaction where available.
- Test unauthorized export attempts and invalid/tampered wizard IDs/filters.
- Do not mark browser, PDF rendering, or download tests passed if the required runtime is unavailable. Report the blocker and exact manual steps.

Explain QWeb, ir.actions.report, transient wizard state, and why sharing a calculation engine prevents output drift. Store actual sample exports and sanitized evidence in the appropriate demo/evidence locations. Stop with the standard stage report.
```

## Conversation (recorded text, verbatim, in order)

### User prompt 1 (verbatim; the whole message was pasted text)

```text
Read prompts/09_trial_balance_outputs.txt and execute Stage 09 only,
following solution/AGENTS.md and docs/calculation_contract.md.

Use the validated Enterprise environment on port 8071 and the completed
Stage 08 engine. Use disposable databases for tests.

Implement the interactive Preview, PDF and XLSX through the inspected
account_reports extension points, following the complete Stage 09 prompt.

Ensure all outputs use the shared engine and reflect the current
preview filters. Verify Bank ending at 1,200 posted-only and 1,000
with drafts across all three outputs on the same unchanged dataset.

Use the available browser to test the actual preview and downloads.
Inspect a short and a multipage PDF visually. Check XLSX numeric
cells and row identities against the engine result.

Test an accounting read-only user, unauthorized downloads, another
user's wizard, and tampered options.

Add the assessment's required installable Trial Balance demo data,
with balanced entries, drafts, foreign currencies and account groups.
Verify that an upgrade does not duplicate the demo records.

Keep custom fiscal-year and branch coverage gaps explicit for Stage 10.
Keep Stage 04 marked PARTIAL.

In the handoff, give a short browser walkthrough and explain the exact
file/function path from the wizard through the engine to each output.
Record actual commands and results. Use English ASCII only.
Stop after Stage 09.
```

Assistant message 1:

> Starting Stage 09. First the usual checks: Git state, free disk space and the services, and the full Stage 09 prompt.

Assistant message 2:

> Children that are already loaded are supported (`isLoadedLine`, then `unfoldLoadedLine`). I'll check how the UI decides that a line is a child, because that sets the rule our line ids must follow.

Assistant message 3:

> Each row gets `line_level_N`, `unfolded`, `total` and its own `class`. I'll check how the controller recognizes the total row, so ours is styled and placed like a native total.

Assistant message 4:

> Next, the XLSX side: an inherited `account.report` that changes the writer for our report only and leaves every other report on the standard code.

Assistant message 5:

> Before the frontend, a quick check that `account.report.column` has the fields I set:

Assistant message 6:

> All fields exist. Now the preview's filter controls: a small OWL extension of the standard filters component, following the aged-balance pattern.

Assistant message 7:

> Now the wizard: its three buttons now open the real outputs, so the "not connected" notice goes.

Assistant message 8:

> Now the manifest: the new data files, the demo file, the assets and the version.

Assistant message 9:

> The production code is written. Two existing tests assert the old "not available yet" behaviour, so they must change with it. I'll find them:

Assistant message 10:

> I'm adding the last Stage 09 tests now (report access, the download route and demo data), then I'll run the module's test suite in a disposable database.

Assistant message 11:

> Fixing two small issues in the demo data, then reviewing the output tests before the first run.

Assistant message 12:

> Small XLSX tidy-up (group names without the repeated code), then writing the demo-data test.

Assistant message 13:

> Syntax checks pass. Starting the full module test run in a fresh test database now (takes 5-15 minutes), with disk-space sampling.

Assistant message 14:

> While that runs, I'll prepare the browser check for the preview and downloads, reusing the existing DevTools helpers.

Assistant message 15:

> Writing the browser check next; first checking which Python packages the host already has for driving Chrome and reading the downloads.

Assistant message 16:

> No generic-chart account starts with 8, so the prefix "8" gives a reliable empty report. Writing the Stage 09 browser check now.

Assistant message 17:

> Now updating the Stage 07 wizard check, whose "not connected yet" and "not available yet" steps no longer apply.

Assistant message 18:

> While the tests run, I'm reviewing the docs that Stage 09 must update (STATE, requirements matrix, assumptions, architecture, test plan and results).

Assistant message 19:

> Tests are still running; peeking at the log once to catch any early failure.

Assistant message 20:

> The demo data loaded, but it logged a warning: `try_loading` ran before the registry was fully loaded. Checking the pinned source for the right way to do this.

Assistant message 21:

> `account` itself defers its chart install to `_register_hook`, which runs once the registry is complete. Checking the order in the pinned `loading.py` before I use the same pattern.

Assistant message 22:

> While the run continues: Odoo can return HTML instead of a PDF during tests unless forced, so I'm checking how `export_to_pdf` renders.

Assistant message 23:

> Everything that doesn't depend on the test results is prepared. Waiting for the test run to finish.

Assistant message 24:

> The run has reached the PDF tests (report assets are being built). Waiting for results.

Assistant message 25:

> While waiting, checking how the native PDF export picks its paper orientation, for the documentation.

Assistant message 26:

> The native export prints landscape when a report has more than 5 columns, so ours (9 or 10) gets landscape pages. Waiting for the test results now.

Assistant message 27:

> The log has not moved since 08:34:02. Checking whether a PDF render is stuck.

Assistant message 28:

> Only about a minute has passed since that line, and no render process is stuck, so the run is just slow. Waiting for the notification.

Assistant message 29:

> While the run continues, I'll write the Stage 09 architecture section (the design is settled; the evidence goes in elsewhere).

Assistant message 30:

> While waiting, recording the Stage 09 decisions in `assumptions.md` (D-47 superseded; D-54 to D-60).

Assistant message 31:

> Verifying two claims I just wrote: that the standard XLSX writer lacks number formats and frozen headers, and where the native code uses the switcher's company name.

Assistant message 32:

> The native writer does write numbers, just in the General format with no number format and no frozen header. Correcting my wording in D-56 and in the module docstring.

Assistant message 33:

> The test run is still going (it started at about 08:21 UTC; the Stage 08 suite took about 5.5 minutes and this one adds about 20 PDF renders). I've written the Stage 09 architecture section and decisions D-54 to D-60 while waiting. I'll pick up as soon as the run reports.

Assistant message 34:

> The test run was stopped by Claude Code because the machine ran critically low on memory, not because of a test failure. I won't restart it without your go-ahead. First, a read-only check of what is still running and how much memory is free.

Assistant message 35:

> Free RAM is 1.0 GB of 15.9 GB. The host-side test command was killed, but its Docker container is still running on its own. Checking how far it got and how much memory it uses (read-only).

Assistant message 36:

> The container uses only about 300 MB, so it is not what filled memory. Its CPU is near zero, though, which may mean it is waiting. Checking the test sequence and timings.

Assistant message 37:

> A `wkhtmltopdf` process inside the test container has been stuck for 1 min 44 s on the first PDF export of `TestReportAccess`, with no CPU use. Checking what ran just before, to understand the hang.

Assistant message 38:

> Odoo's own Enterprise tests never run a real `wkhtmltopdf` in unit tests: they patch `_run_wkhtmltopdf` or `export_to_pdf`. Checking what triggers the 13-minute asset generation.

Assistant message 39:

> Now writing the test changes: a shared stub in `tests/common.py` that captures the documents, then the output and access tests on top of it.

Assistant message 40:

> Now rewriting `tests/test_report_outputs.py` around the captured PDF document. The XLSX and preview checks stay as they were.

Assistant message 41:

> API Error: Connection lost mid-response. The response above may be incomplete.

### User prompt 2 (verbatim; typed)

```text
continue
```

Assistant message 42:

> Continuing: finishing the test rewrite first, then I'll check free memory before starting the rerun.

Assistant message 43:

> Now the access tests: removing the `HttpCase` class (its asset pre-generation alone cost 13 minutes) and using the same stub. The real route gets checked on the running server instead.

Assistant message 44:

> The stub's byte string in `tests/common.py` got a real line break instead of `\n`. Fixing that line.

Assistant message 45:

> While run 2 works, I'm recording what happened to run 1 in a private log note (facts only).

Assistant message 46:

> Now the test plan: a Stage 09 section listing the new test files, the browser check and the check statuses.

Assistant message 47:

> Run 2 is installing modules. Meanwhile, looking at the Stage 08 handoff's format before drafting the Stage 09 one.

Assistant message 48:

> Before writing the explanations, verifying the transient-model cleanup defaults in the pinned core.

Assistant message 49:

> Checking how the standard report controller loads options and triggers exports, so the handoff's call path is exact.

Assistant message 50:

> The XLSX button is labeled "Download Excel" in this build, not "XLSX". Checking how the buttons bar groups the buttons before fixing the browser script.

Assistant message 51:

> Only the first button ("PDF") is in the bar; "Download Excel" sits in the gear (cog) menu. Checking that menu's markup.

Assistant message 52:

> Checking whether the wizard's preview action sets a name, which the Stage 07 wizard check reads from the breadcrumb.

Assistant message 53:

> The action is named after the report, so the Stage 07 breadcrumb check holds. While the tests run, I'm adding a small read-only script that counts the demo records before and after an upgrade.

Assistant message 54:

> Run 2 is still installing modules (no warnings so far, about 2.4 GB RAM free). Drafting the Stage 09 handoff now, with result placeholders I'll fill in from the actual runs.

Assistant message 55:

> Tests are moving quickly, with no failures and no `wkhtmltopdf` process.

Assistant message 56:

> Run 2 passed: "0 failed, 0 error(s) of 101 tests" (85 earlier plus 16 new), exit code 0, 419 s. Checking the full log for warning lines and the disk and memory samples.

Assistant message 57:

> First upgrade: exit 0, 71 s, 0 warning lines. Counting the demo records now.

Assistant message 58:

> The first upgrade did not create the demo company, although the same code created it in the fresh test database. Checking the pinned `loading.py` for how an upgrade differs from an install.

Assistant message 59:

> Comments corrected. Now the clean install-then-upgrade proof on `azk_ee24_test`, which the test run just installed fresh, with demo data. Sequence: count, upgrade, count.

Assistant message 60:

> Created on `azk_ee24` with 0 warnings, and the counts match the fresh install exactly. Now two upgrades with a count after each.

Assistant message 61:

> Both upgrades: exit 0, 0 warning lines, and every count unchanged (16 entries, 32 items, 10 groups, and so on). Now the browser check on port 8071, after confirming the restarted web server answers.

Assistant message 62:

> Free RAM reads 826 MB, which is low. Checking Windows' "available" memory, which also counts reclaimable cache, before starting Chrome.

Assistant message 63:

> Only about 900 MB is available, with 1.8 GB of commit headroom. Checking what is using memory before deciding whether to start Chrome.

Assistant message 64:

> The first browser run took about 3.3 minutes, and commit headroom never fell below 1.38 GB. Rerunning the whole check with the corrected route test.

Assistant message 65:

> The multipage PDF repeats the column header at the top of page 3, and the footer reads "3 / 3". Page 3 shows a blank row between 500000 and 961000, so I'm checking page 2 to understand it.

Assistant message 66:

> Page 2 also repeats the header. There are two slightly taller gaps, after "141000 Prepayments" and before "961000 RD Expenses". Checking the native body template for spacing rows.

Assistant message 67:

> Adding a regression assertion for the country to `TestDemoData`, then giving `azk_ee24`'s existing demo company the value a fresh install now produces.

Assistant message 68:

> 1.85 GB RAM free and 48 GB disk. Starting test run 3 on the final module code.

Assistant message 69:

> While run 3 works, I'm inspecting the preview screenshots from browser run 2, starting with the posted-only preview.

Assistant message 70:

> Run 3 is still installing modules, and 1.2 GB RAM is free. Running the probe under the memory guard.

Assistant message 71:

> Run 3 is stopped (superseded during module installation; I'll record it as such). Applying the three fixes: bold group rows, the rounding unit in the PDF filters, and a regression test for it.

Assistant message 72:

> Syntax is clean. Starting test run 4 with the final module code.

Assistant message 73:

> Run 4 is still installing base modules. Meanwhile, collecting the current requirement-matrix rows that Stage 09 completes, so I can rewrite them exactly.

Assistant message 74:

> While run 4 continues, I'm preparing the requirements-matrix update as a script; I'll fill in the final test count once the run reports.

Assistant message 75:

> The backslashes in my edit script were turned into real line breaks again, as happened earlier. I'll copy the file and use the Edit tool instead, which matches text exactly.

Assistant message 76:

> Module 70 of 90 is loading. Waiting for the run 4 summary.

Assistant message 77:

> The fresh install on the final code gives country EG and fiscal country US, the same as `azk_ee24` now. After the upgrade (exit 0, 62 s, 0 warnings) every count is identical. Now `azk_ee24`.

Assistant message 78:

> The final browser check passed 20 of 20 on the final code. Visually checking the two things that changed: group rows should now be bold in the preview, and the PDF address should say Egypt.

Assistant message 79:

> Both confirmed: group rows are bold in the preview, and the PDF address now reads "Egypt". Collecting file sizes to choose the sample exports and screenshots to commit.

Assistant message 80:

> All samples are small (8 to 36 KB). Before copying any into the repository, checking their text and metadata for anything private: user names, local URLs or e-mail-like strings.

Assistant message 81:

> Now a short README for the samples, stating exactly how each file was produced.

Assistant message 82:

> Samples and their README are in place. Gathering the remaining numbers for `test_results.md` (memory ranges of runs 2 and 4, and the run 3 log tail).

Assistant message 83:

> Writing the Stage 09 section of `test_results.md` (newest first).

Assistant message 84:

> As noted earlier in this project, heredocs with apostrophes fail in this shell, so I'll write the section with the Write tool and splice it in with Python.

Assistant message 85:

> Running the requirements-matrix update with the final figures (102 of 102 tests, browser 20 of 20), then updating the matrix's introduction.

Assistant message 86:

> All Trial Balance rows are DONE except T-19 and T-20, which wait for the Stage 12 README. Spot-checking two rewritten rows.

Assistant message 87:

> The rows read well. Now `test_plan.md` (17 new tests, with the rounding-unit test) and the remaining decisions in `assumptions.md`.

Assistant message 88:

> I appended the status lines to the end of `test_plan.md`, but they belong at the end of section 4.5. Moving them.

Assistant message 89:

> API Error: Connection lost mid-response. The response above may be incomplete.

### User prompt 3 (verbatim; typed)

```text
continure
```

Assistant message 90:

> Continuing. Fixing the placement of the status lines in `test_plan.md` first.

Assistant message 91:

> Section 6 of the test plan lists commands. Checking whether it needs the new Stage 09 scripts.

Assistant message 92:

> Now updating architecture section 4.11: when demo data is created, the rounding unit, analytic visibility and how PDFs are tested.

Assistant message 93:

> Next, `STATE.md`. Writing the Stage 09 entry to a scratch file first, to avoid the shell quoting problem, then splicing it in.

Assistant message 94:

> Adding the private tools environment to the host facts in `STATE.md`, and an "as built" pointer to architecture 4.7.

Assistant message 95:

> Before filling in the handoff, confirming the exact function names in the changed wizard and the new handler, so the file list is accurate.

Assistant message 96:

> Filling in the handoff's result sections. The texts go into a scratch file via the Write tool and are spliced in with Python.

Assistant message 97:

> Adding an optional analytic step to the handoff walkthrough. I'll describe the whole-item rule without numbers I haven't seen in the UI.

Assistant message 98:

> Now `docs/ai/README.md`: the log index and the mistakes table. Reading its structure.

Assistant message 99:

> One wording slip in the second row ("demo function was created"); correcting it.

Assistant message 100:

> Now the kit-root `CLAUDE.md` (outside the repository): a Stage 09 bullet in the Architecture section, in the same style as Stage 08.

Assistant message 101:

> The documentation is updated. Now the repository state and the pre-commit checks: what changed, that it is ASCII only, and that nothing private is staged.

Assistant message 102:

> Line-ending warnings are Git's usual normalization. Checking every changed or new text file for non-ASCII characters.

Assistant message 103:

> All 33 changed text files are ASCII only. Next, the tool-activity summary for the AI log; checking the Stage 08 summary's style first.

Assistant message 104:

> Now the final stage report, written to a file first so that the log and the displayed text are identical.

Assistant message 105:

> The log's notes will claim that the Stage 08 final response was displayed exactly as logged, so I'm verifying that against the transcript now.

## Notes on accuracy

- This log was assembled from the transcript just before its own commit. Progress messages written after that point, while committing, are not included. The final response below is included as prepared, before it was displayed.
- The Stage 08 final response was checked against the session transcript before this log was written: it was displayed exactly as logged in [stage_08.md](stage_08.md).
- The CLI compacted the conversation's context once during this stage. The transcript keeps every visible message, so the log is complete; the CLI's compaction summary is not a user prompt and is not reproduced.
- System notifications (for example the CLI stopping background commands while the machine was low on memory) are not user prompts; they are summarized under tool activity.
- Facts in the messages that were later corrected stay as written here; corrections are listed in [README.md](README.md) (mistakes table) and in the Stage 09 handoff.

## Summary of tool activity (summary, not verbatim)

1. Read the Stage 09 prompt file, `solution/AGENTS.md`, the calculation contract and the Stage 08 handoff, and checked Git (clean at `845accb`) and the free space on C: (48 GB).
2. Read the pinned 18.0 sources by name, to use their extension points:
   - in the Enterprise `account_reports`: the custom handler hooks, the report options initializers, `export_to_pdf`, `export_to_xlsx` and its XLSX writer, the PDF templates, the download route `/account_reports`, the preview's filter, search, line and buttons components;
   - in the core: the chart loader (`try_loading`, `_load`), `_update_xmlids`, `button_cancel`, `load_data` and `_tag_function` (demo files), the module loading steps and `_register_hook`, transient-record cleanup.
3. **Code** (addon version 18.0.1.3.0):
   - the report record and its columns, the report handler, the XLSX override, three PDF templates, the preview filter component;
   - the wizard's Preview, PDF and XLSX connections;
   - the demo data model and file;
   - tests of the three outputs, of access and tampering, and of the demo data, with a stub that captures the PDF's HTML;
   - `scripts/tb_preview_smoke_check.py` and `scripts/tb_demo_data_counts.py`; `scripts/tb_wizard_smoke_check.py` updated for the connected buttons.
4. **Test runs** of `scripts/dev.sh test azk_dynamic_trial_balance`, each on a fresh `azk_ee24_test`, with free space and free RAM sampled:
   - run 1: stopped. The CLI stopped the background command because the machine was critically low on memory. The test container was stuck in a real wkhtmltopdf render and was stopped with `docker stop`. Its log showed a try_loading warning, and about 13 minutes of asset building caused by an `HttpCase` class;
   - run 2, after the stub, the removal of the `HttpCase` class and the deferred demo creation: 101 of 101;
   - run 3: stopped by the agent while modules installed, superseded;
   - run 4, final code: 102 of 102, 0 warnings.
5. **Demo data:**
   - the first upgrade of `azk_ee24` created no demo company. The pinned source showed that demo-file functions run at install only;
   - the demo function was called once from an Odoo shell on `azk_ee24`;
   - record counts before and after upgrades of `azk_ee24_test` (twice) and `azk_ee24` (four times) were unchanged;
   - the demo company's country was set to Egypt on `azk_ee24` after the code fix.
6. **Tools:** created a private virtual environment `runtime/tools/venv` (outside Git) with websocket-client, openpyxl and PyMuPDF from PyPI. Wrote a scratch memory guard that would stop a browser check below 500 MB of commit headroom.
7. **Browser checks** (headless Chrome, `azk_ee24`, under the memory guard):
   - `tb_preview_smoke_check.py`: run 1, 19 of 20 (the check misread the route's refusal); run 2, 20 of 20; run 3, final code, 20 of 20;
   - `tb_wizard_smoke_check.py`: 7 of 7;
   - a scratch probe read the computed font weight of group rows.
8. **Visual inspection:** rendered the real PDFs to PNG and viewed them, together with the screenshots. This found the "United States" address and the unbold group rows, both fixed, and confirmed the repeated header.
9. **Evidence files:** copied five sample exports and eleven screenshots into `docs/`, after scanning them for user names, URLs and paths (none found).
10. **Documentation:** STATE, requirements matrix, assumptions (D-47 superseded; D-54 to D-63), architecture 4.7 and 4.11, calculation contract 16, test plan, test results, the handoff, this log and its README, and a Stage 09 note in the kit-root CLAUDE.md (outside the repository).
11. **Checks before the commit:** ASCII-only check of the changed text files; the pre-commit scan (binary samples skipped, as they were scanned above). It flagged three lines of `scripts/tb_preview_smoke_check.py` that read the login from the environment variables `PM_UI_LOGIN` and `PM_UI_PASSWORD` and pass it to the page; reviewed, they hold no secret value. Only the intended files were staged.

## Assistant final response (verbatim)

Everything between the two rules below is the final visible response.

---

Stage 09 is done. The Dynamic Trial Balance now has a working Preview, PDF and XLSX, all built from one engine call per request, plus installable demo data. It is committed locally as "Stage 09: Trial Balance outputs, demo data and checks". Stage 04 stays PARTIAL.

**Completed work**

- **One shared path:** our report record and a custom handler connect the Stage 08 engine to the standard `account_reports` screen and exporters. No output computes an amount itself.
- **Preview:** the wizard's Preview opens the standard report view with the wizard's options.
  - A filter bar adds the Trial Balance options, account prefixes, journal and analytic account. Every change recalculates the report.
  - Search, folding and unfolding of groups, and messages for an empty or unbalanced report all work.
- **PDF:** the standard exporter, with our own:
  - company block (the report's company);
  - every option printed as "label: value";
  - grouped column headers that repeat on every page;
  - the rounding unit, when one is chosen.
- **XLSX:** our own sheet for this report:
  - the options above the table;
  - codes and names as text, and amounts as numbers with a number format;
  - a separate currency column and a frozen header.
- **Exports follow the preview:** they use its current options, search text and folded groups. Nothing is stored, so every request recalculates as the user who asks.
- **Demo data:** the company "AZK Trial Balance Demo (EGP)" has posted, draft, cancelled, USD, EUR and analytic entries, and account groups five levels deep. Its January 2026 report shows Bank ending at 1,200 with posted entries only and at 1,000 with drafts.

**Commands and results** (2026-11-15, port 8071)

- **`scripts/dev.sh test azk_dynamic_trial_balance`:** PASS on the final code. "0 failed, 0 error(s) of 102 tests", 0 warnings, exit 0, 438 s.
  - The first run was stopped by the CLI because the machine ran critically low on memory.
  - Its log showed two test choices to drop: an `HttpCase` class, which made Odoo build every asset bundle (about 13 minutes), and real wkhtmltopdf renders inside unit tests, which hung.
  - Unit tests now capture the PDF's HTML instead, as Odoo's own tests do.
- **Demo data and upgrades:** PASS. The record counts were identical:
  - before and after upgrading a fresh install (`azk_ee24_test`);
  - after three upgrades of `azk_ee24`.
  The counts: 16 entries (13 posted, 2 draft, 1 cancelled), 32 journal items, 10 groups.
- **`scripts/tb_preview_smoke_check.py`** (my headless Chrome on `azk_ee24`): PASS, 20 of 20.
  - Preview: Bank 1,200.00, then 1,000.00 after ticking Draft Entries.
  - Search and folding.
  - Both downloads, a 1-page PDF and a 3-page PDF.
  - The empty-report message.
  - The download route refuses tampered options and gives no file without a session.
  - All eight option sets through the real route equal the engine: posted only, drafts, hierarchy, parents only, amount currency, analytic, zero filtering, empty.
  The updated wizard check passed 7 of 7.
- **Visual check of the PDFs (rendered to images):** readable landscape pages, the report company and every option, the header on every page, and nothing cut off.

**Open issues and assumptions**

- **For Stage 10:** custom fiscal years and branch companies are not tested yet (D-60).
- **Analytic filter:** it shows only when Odoo's Analytic Accounting setting is on, and it is off on `azk_ee24`. So the browser check could not use it; it passed in the unit tests and through the download route.
- **Demo data on `azk_ee24`:** it came from one Odoo shell call. Odoo runs demo-file functions only at install, and the module was installed in Stage 07.
- **Memory:** it is tight on this machine. Close unused applications before long runs.
- **Your own browser check is recommended.** The walkthrough is in the handoff.

**Changed files and functions**

- **New:**
  - `models/trial_balance_report_handler.py` (`_custom_options_initializer`, `_dynamic_lines_generator`, `_report_lines`, `_custom_line_postprocessor`);
  - `models/account_report.py` (`_write_dynamic_trial_balance_sheet`);
  - `models/demo_data.py` (`_create_demo_data`, `_register_hook`);
  - `data/trial_balance_report.xml`, `data/pdf_export_templates.xml`, `demo/trial_balance_demo.xml`, `static/src/components/trial_balance/`;
  - three test files;
  - `scripts/tb_preview_smoke_check.py`, `scripts/tb_demo_data_counts.py`.
- **Changed:** `models/trial_balance_wizard.py` (`action_preview`, `_export`), `tests/common.py` (`capture_wkhtmltopdf`), the wizard view, the manifest (18.0.1.3.0), and the documentation.
- **Handoff:** `docs/handoffs/stage_09_en.md`. It has the walkthrough and the exact path from the wizard through the engine to each output. It also explains QWeb, `ir.actions.report`, the temporary wizard records and why one shared engine prevents the outputs from disagreeing.

**Comprehension questions**

1. The PDF button of the preview and the XLSX item of its gear menu both end in the same route. Which function validates the options again there, and why must it, even though the preview already validated them?
2. Why does the handler mark every group line `unfolded` or not, and send all child lines, instead of loading children when a group is unfolded? What would the PDF and XLSX lose otherwise?
3. The demo data is created by a function called from a demo XML file. Why does an upgrade never run that function, and why must the function still check the company's XML id before it creates anything?

**Next stage:** 10 (engineering review), when you ask for it.

---
