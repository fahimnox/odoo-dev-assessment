# Stage 07 - Trial Balance wizard and calculation contract

- **Date:** 2026-11-15
- **Tool / model:** Claude Code, Opus 5.5 (`claude-opus-5-5`), in the same CLI session as Stages 01B to 06
- **Working directory:** the assessment kit root (`<kit-root>`) and `<kit-root>/solution`
- **Commit:** this log is part of the Stage 07 commit

**Transcription method:** see [README.md](README.md). The user prompt and the referenced instruction file are verbatim. The assistant messages are the visible text blocks recorded in the CLI's local session transcript, verbatim and in order, extracted by a script. Tool calls, tool outputs, reasoning blocks and system notices are not reproduced.

**Redactions:** absolute local paths are replaced with `<kit-root>`, `<home>` or `<scratchpad>`. The CLI's paste markers around the user's pasted text are omitted. No credential or subscription value appeared.

## Referenced instruction file: `prompts/07_trial_balance_contract.txt` (verbatim)

```text
STAGE 07  -  Implement the Trial Balance wizard and an independently checked data contract

LANGUAGE: English only for all newly authored terminal prose, explanations, questions, and reports. Use simple ASCII formatting and short paragraphs/bullets instead of wide or box-drawn tables. Preserve source data and original historical logs. Arabic coaching happens outside this terminal.

Follow the project contract. Re-read Exercise 2, inspect the actual Enterprise Trial Balance/reporting engine, account models and analytic fields, and review docs/assumptions.md. Use azk_dynamic_trial_balance and declare its verified Enterprise reporting dependencies. Preserve the requested wizard while using suitable native report extension points. Do not replace the required feature set with a bare link to the unmodified standard report. Do not build attractive exports before the calculation contract and expected results are established.

Implement a TransientModel wizard with:
- Date From, Date To, and one authorized Company; validate date order and access server-side.
- Posted always included; Include Unposted Entries includes draft only, never cancelled.
- Hierarchy and Subtotals; Hierarchy Only Parents; conditional Account Level Up To, from 1 to 5. Specify valid option combinations and enforce them server-side.
- Multiple account-code prefixes with OR semantics and all accounts when empty. Treat prefixes as literal prefixes, not unintended SQL wildcard patterns.
- Journal Many2one and Analytic Account Many2one, with all authorized values when empty, matching the PDF's cardinality despite its plural help text.
- Skip Zero Balance; Show Amount Currency.
- Preview, PDF and XLSX action entry points, connected in subsequent stages. Do not present unfinished buttons as accepted features.
- Clear help text based on the PDF and our documented interpretations.

Write docs/calculation_contract.md before the calculation engine:
1. Use the actual native report/ORM interfaces and account.move.line relationships. Enforce consistent company, state, account-prefix, journal and analytic scope for opening and movement. Movement dates are inclusive. Inspect the native opening/fiscal-year domains and any supported adjustments rather than imposing the old generic ledger-before-start fallback. Document a reconciliation from opening and movement to ending and any standard adjustments.
2. Define opening, movement and ending debit/credit/balance using the observed Enterprise Trial Balance conventions where applicable. Explicitly document net-versus-gross presentation and the display grain. Match the same standard report options in comparisons, and record any assessment-driven change.
3. Verify native fiscal-year and carry-forward behavior with a cross-year fixture including prior-year income/expense and balance-sheet accounts. Reuse supported native behavior where appropriate; do not manually invent retained earnings postings or silently substitute the old Community fallback. Claim parity only for cases and options actually compared.
4. Define zero filtering using opening balance AND real period activity AND ending balance. An account with equal debit/credit movements must remain visible. Use currency-aware rounding.
5. Define grouping by account plus transaction currency when enabled, the date scope of the additional Amount Currency column, and separate per-currency totals. Signed base-currency balances and gross movements reconcile across groupings; net debit/credit display totals can differ with the grain of netting, which must be documented.
6. Define analytic selection from the verified native behavior and assessor intent; explicitly choose and document weighted allocation versus full-item selection rather than assuming either. No selection means each journal item contributes its full value exactly once. Composite distribution keys/multiple plans must not double-count items. A scoped/analytic report need not balance like a complete company ledger.
7. Define hierarchy from the actual account-group structure. Parent rows aggregate their descendant leaf amounts once, and report totals exclude parent/subtotal rows. Parents-only must not silently drop ungrouped accounts or deeper descendants.

Create a deterministic small base fixture and write expected results independently of the production calculator:
- Report dates: 2026-01-01 to 2026-01-31. Company currency: EGP.
- Posted 2025-12-31: Bank debit 1,000; Equity credit 1,000.
- Posted 2026-01-10: Expense debit 300; Bank credit 300.
- Posted 2026-01-20: Bank debit 500; Revenue credit 500.
- Draft 2026-01-25: Expense debit 200; Bank credit 200.
- Cancelled 2026-01-26: Expense debit 400; Bank credit 400, constructed using supported Odoo state transitions.
- Posted 2026-02-01: Expense debit 50; Bank credit 50.

Expected for posted-only January: Bank opening 1,000, movement debit 500/credit 300/balance 200, ending 1,200; Expense ending debit 300; Revenue ending credit 500; Equity ending credit 1,000. Total ending debit = total ending credit = 1,500.
With drafts: Bank ending 1,000 and Expense ending 500; Revenue and Equity unchanged. The cancelled and February items never contribute to this January report.

Compare the simple fixture against the standard Enterprise Trial Balance with aligned options; keep the hand-calculated numbers independent of the native engine. Keep advanced fixtures separate so these simple expectations stay understandable: zero-net activity, multiple currencies, analytic allocation, multiple companies, restricted access, and deep account hierarchy. Use real balanced moves and required accounts/journals, not isolated fake journal items. Explain debit, credit, balance, journal entry versus journal item, and wizard versus persistent model using the example. Stop with the standard stage report.
```

## Conversation (recorded text, verbatim, in order)

### User prompt 1 (verbatim; the whole message was pasted text)

```text
Check free space on C: before starting Docker tests and monitor it during
database creation. At commit 3222285, rerun the existing dashboard browser
smoke check and record the result in the Stage 06 handoff.

Read prompts/07_trial_balance_contract.txt and execute Stage 07 only,
following solution/AGENTS.md on the validated Enterprise setup on port 8071.

Build the Dynamic Trial Balance wizard and document its calculation rules.
On a disposable test database, compare the January example with Odoo's
native Trial Balance using the same company, dates, and posting options.

In the handoff, show the Bank calculation by hand: opening 1,000,
posted debit 500, posted credit 300, ending 1,200. Show why including
the draft credit of 200 changes the ending balance to 1,000.

Report the checks actually performed. Use English only. Stop after Stage 07.
```

Assistant message 1:

> The rerun passed 7 of 7 at commit 3222285. Before I record it, I'll look at one screenshot, because a screenshot once showed a problem that the checks had missed.

Assistant message 2:

> I'll commit this record on its own, before any Stage 07 change. The pre-commit scan checks for non-ASCII text, local paths and secrets.

Assistant message 3:

> Next, I'll read how the native report takes its draft, hierarchy, journal and company options, so the comparison tests set them exactly as the report expects.

Assistant message 4:

> I have the native report details I need. One more check: does Odoo's own account-code search ignore case? That decides how the prefix filter matches letters.

Assistant message 5:

> Odoo's own code search is case-sensitive (`=like` on the code), so the prefix filter will be case-sensitive too, with wildcards escaped. Last check: the journal item fields the contract names.

Assistant message 6:

> I have what I need from the sources. Before writing the test helper, I'll read how the native hierarchy names and nests its group, "(No Group)" and total lines.

Assistant message 7:

> The APIs are verified. Now I'll write the addon: the manifest, the option rules, the two transient models, security, and the view and menu.

Assistant message 8:

> I'll let the native helper take another company's account names, for the two-company fixture. Then I'll write the advanced fixtures.

Assistant message 9:

> Two fixes before the wizard tests. `new_test_user` must run with superuser rights, because the test user 'accountman' cannot create users. Then I'll write the wizard tests.

Assistant message 10:

> With `accountant` installed, Reporting moves under "Accounting", so the expected menu path holds. Now the two small fixes.

Assistant message 11:

> Now the test index, a syntax check of every file, and then the first test run.

Assistant message 12:

> The contract is written. I'll check the free-space samples so far, since the database is being created now.

Assistant message 13:

> I put the new rows before D-42 by mistake. I'll move them after it.

Assistant message 14:

> I'll check the test run and disk again.

Assistant message 15:

> A heredoc with apostrophes failed again in this shell, a known limitation. I'll write the section with the Write tool, then splice it in with a small script.

Assistant message 16:

> Now the architecture: a short "as built in Stage 07" section after the native probe evidence.

Assistant message 17:

> The install is at module 19 of 90, so the run will take a while. Meanwhile I'll look at the Stage 06 handoff's structure, so the Stage 07 handoff follows it.

Assistant message 18:

> While run 1 continues, I'll look at the format of the Stage 06 AI log, so the Stage 07 log matches it.

Assistant message 19:

> I'll adapt that script for the Stage 07 log at the end. Now the run's progress:

Assistant message 20:

> The `account` module takes a few minutes. I'll draft the handoff meanwhile and fill in the results when the run finishes.

Assistant message 21:

> I've reviewed the wizard code and the tests while waiting. One open risk: whether a read-only accountant can read a shared analytic account. The run will show it. Install progress:

Assistant message 22:

> Module 77 of 90; the tests start soon. I'll wait for the run to finish.

Assistant message 23:

> Our module installed its security and view files without errors. Now the post-install tests run; I'll wait for the result.

Assistant message 24:

> Now the callers, and the corrected menu-path expectation in the test.

Assistant message 25:

> A regression test for the warnings: it runs valid and invalid option sets and asserts that Odoo logs no translation warning. The company bug is already covered by the two tests that failed.

Assistant message 26:

> I'll confirm that `env._()` cannot log the same warning when the environment has no language set:

Assistant message 27:

> `env._()` falls back to English silently. Syntax check, then run 2 with disk sampling.

Assistant message 28:

> Run 2 is running. Meanwhile, the run 1 disk record, and Docker's virtual disk compared with before:

Assistant message 29:

> The tool summary is drafted. I'll wait for run 2 to finish.

Assistant message 30:

> The upgrade passed: exit code 0, 90 s, no warnings or errors. I'll confirm the installed version and wait for the restarted web server.

Assistant message 31:

> `azk_ee24` now has 18.0.1.1.0, and the login page answers. Next, the headless browser check of the wizard. Its output stays outside the repository until I've looked at it.

Assistant message 32:

> Now the regression checks in the tests, and the label fix in the browser script.

Assistant message 33:

> The code is final unless run 3 finds something. Run 3 starts now, on a fresh test database with disk sampling again.

Assistant message 34:

> While run 3 runs, I'll update the documents. First the architecture note about Posted Entries, which no longer matches the code.

Assistant message 35:

> I'll add the Stage 07 rows to the AI-log index and the mistakes table.

Assistant message 36:

> Now I'll wait for run 3.

Assistant message 37:

> The browser check passed 8 of 8 on the final code, including the new check that Posted Entries is ticked in a new form. I'll look at the screenshot to confirm visually.

Assistant message 38:

> 35 rows updated. One correction: the wizard test file now has 16 tests, not 15. Then the three rows the script doesn't cover (K-02, K-05) and the matrix's header note.

Assistant message 39:

> Now the status of assumptions A-14 and A-15, which this stage checked against the standard report:

Assistant message 40:

> Next, test-plan section 4.3: what Stage 07 implemented, and the three runs.

Assistant message 41:

> Now `STATE.md`: a Stage 07 block at the top, the stage table, decisions in force, and the next step.

Assistant message 42:

> Now I'll fill in the handoff's result sections.

Assistant message 43:

> The handoff is complete. Next, a short Stage 07 note in the kit's guidance file. It is outside the repository and not committed, as in earlier stages.

Assistant message 44:

> Before the commit, I'll read the whole handoff once, as the user will see it.

Assistant message 45:

> The handoff reads well. Now the Git status, to see exactly what will be staged:

Assistant message 46:

> That is exactly the intended set; the AI log comes next. First the pre-commit scan, which now stops on a finding:

Assistant message 47:

> There is exactly one displayed Stage 06 final response in the transcript, dated 2026-11-10 12:03 UTC, and it is the reworded one. Here is the end of `stage_06.md`, to place the correction exactly:

Assistant message 48:

> The Stage 06 log is corrected. Next, the two places that should mention that correction: the AI-log mistakes table and the handoff's file list.

## Notes on accuracy

- This log was assembled from the transcript just before its own commit. Progress messages written after that point, while committing, are not included. The final response below is included as prepared, before it was displayed.
- Before the prompt, the user ran the CLI's `/model` command, which kept Opus 5.5. That local command is not part of the prompt and is not reproduced.
- The prompt asked for two things before Stage 07 itself: free disk space checked and monitored, and the Stage 06 browser check rerun at commit `3222285`. The rerun was recorded in the Stage 06 handoff and committed separately (`597e0e8`).
- Facts in the messages that were later corrected stay as written here; corrections are listed in [README.md](README.md) (mistakes table) and in the Stage 07 handoff.

## Summary of tool activity (summary, not verbatim)

1. Read `prompts/07_trial_balance_contract.txt`, the Stage 08 and 09 prompts (to keep the scope to Stage 07), `AGENTS.md`, `STATE.md`, `assumptions.md`, the Trial Balance parts of the architecture, test plan and requirements matrix, and Exercise 2 of the PDF (pages 6 to 8). Checked Git (clean at `3222285`) and the free space on C: (54 GB).
2. **Stage 06 rerun (requested first):** the containers had stopped three days earlier, so `scripts/dev.sh start` started them, and the login page answered after about 35 s. `scripts/ui_smoke_check.py` was then run at commit `3222285` on `azk_ee24` without `--sync`: 7 of 7 PASS. The agent viewed one screenshot. The result was recorded in the Stage 06 handoff, STATE and the requirements matrix, and committed separately (`597e0e8`).
3. Read the pinned 18.0 sources by name:
   - the account test helpers;
   - the standard Trial Balance handler and report record;
   - the general ledger's opening-balance, carry-forward and query code;
   - the report framework's domain, draft, journal, analytic, hierarchy and company options;
   - the analytic mixin's search;
   - the account code, group and opening-balance fields;
   - `button_cancel`;
   - `compute_fiscalyear_dates` and its `account_accountant` override;
   - the accounting menus and groups;
   - `Environment.__call__` and `Environment._`.

   Also read the private log of the Stage 02 native probe.
4. **Code:** the manifest now depends on `account_reports`. New: `models/report_options.py`, `models/account_prefix.py`, `models/trial_balance_wizard.py`, the security files and `views/trial_balance_wizard_views.xml`. Tests: `tests/common.py` (fixtures, hand-calculated constants, a helper that runs the standard Trial Balance), `test_wizard.py`, `test_base_fixture.py`, `test_native_conventions.py` and `test_advanced_fixtures.py`. Also `scripts/tb_wizard_smoke_check.py`.
5. **Docs:** `calculation_contract.md` (new), assumptions D-43 to D-49 and V-08, test plan 4.1 and 4.2, architecture 4.9, requirements matrix, STATE, this handoff, this log and the index.
6. **Test runs** of `scripts/dev.sh test azk_dynamic_trial_balance`, each on a fresh `azk_ee24_test`, with free space on C: sampled every 30 s (logs in `<kit-root>/runtime/logs/`).
   - Run 1: 44 of 47. It showed a company-check bug, a wrong test expectation and 88 translation warnings.
   - Run 2: 48 of 48.
   - Run 3, on the final code: 48 of 48, 0 warning lines.
7. **Disk investigation.** Between runs, the agent measured Docker's virtual disk: its size and the space actually allocated to it, and whether it is sparse. It also checked for a WSL swap file and the page file, and sampled free space for a minute while idle. Shadow storage could not be read without administrator rights.
8. **`azk_ee24`:** two upgrades with `scripts/dev.sh update azk_dynamic_trial_balance`, each with 0 warnings, and a read-only version check.
9. **Browser:** `scripts/tb_wizard_smoke_check.py` against `azk_ee24`.
   - The first run gave 6 of 7, with one false failure in the label comparison. Its screenshot showed Posted Entries unticked in a new form.
   - Both were fixed, and the second run on the final code passed 8 of 8.
   - The agent viewed the screenshots.
10. **Log correction:** the agent found that the displayed Stage 06 final response differed from the one logged in `docs/ai/stage_06.md`. It replaced that section with the displayed text from the transcript, with a correction note.
11. **Before the commit:**
    - updated the kit's guidance file outside the repository with a Stage 07 note;
    - scanned the changes for non-ASCII text, local paths and secrets (the only remaining hits were the browser script's reads of the login and password from environment variables, reviewed as false positives);
    - staged only the intended files.

## Assistant final response (verbatim)

Everything between the two rules below is the final visible response.

---

Stage 07 is done and committed. Stage 04 stays **PARTIAL**. The calculation engine is Stage 08 and the Preview, PDF and XLSX outputs are Stage 09; the wizard's three buttons are entry points only, so those requirements are not marked done.

**Stage 06 rerun (done first)**
- At commit `3222285`, `scripts/ui_smoke_check.py` against `azk_ee24` passed **7 of 7**, with the same numbers as before: Gold and 2025 give 9 partners in 6 countries, and Epsilon shows "1-3 / 3".
- The containers had been stopped for three days, so I started them first.
- The result is in the Stage 06 handoff, STATE and the requirements matrix. I committed it separately (`597e0e8`).

**Disk space**
- Drive C: had 54 GB free before any Docker work. I sampled free space every 30 seconds during each test run.
  - Run 1: from 54.7 GB down to 50.0 GB, mostly while the database was being created.
  - Run 2: from about 49 GB to 45.7 GB.
  - Run 3: from 46.4 GB to 46.2 GB.
- I couldn't find where the space from runs 1 and 2 went.
  - Docker's virtual disk stayed at 17.63 GB, there is no WSL swap file, and free space is stable when nothing runs.
  - Windows shadow copies might explain it, but checking them needs administrator rights.
- About 46 GB are free now.

**What was built**
- **The wizard,** under Accounting > Reporting > Audit Reports > Dynamic Trial Balance.
  - It has every field from the PDF, with the PDF's help texts word for word, plus Date From, Date To and one company.
  - The server enforces the valid combinations:
    - Hierarchy Only Parents needs Hierarchy and Subtotals.
    - Account Level Up To (1 to 5) exists only with Only Parents.
    - Show Amount Currency is refused with Only Parents, because there are no account lines to split by currency.
  - The company must be one of yours and active. The journal and analytic account must be usable in that company. Prefixes must look like account codes, so "1_" is refused rather than acting as a wildcard.
  - Each wizard is private to the user who created it.
  - Preview, PDF and XLSX check the options, then say the output is not available yet.
- **The calculation contract** (`docs/calculation_contract.md`), written before any calculation code. It defines:
  - the scope of journal items;
  - the fiscal-year opening and the carry-forward of earlier profit;
  - net versus gross display;
  - zero filtering and currency rows;
  - the analytic policy: whole journal items, as Odoo does;
  - the hierarchy and the totals.
- **Fixtures:** real, balanced journal entries in fresh EGP companies, each with hand-calculated expected numbers. The base fixture is kept separate from seven advanced ones: cross-year, zero activity, currencies, analytic, two companies, restricted access and a deep hierarchy.

**Bank by hand, January 2026** (full working in the handoff)
- Opening 1,000, from the entry posted on 2025-12-31.
- Posted movement: debit 500 and credit 300, so +200. Ending: 1,000 + 500 - 300 = **1,200**.
- Including drafts adds the draft credit of 200 (2026-01-25) to the movement. Credits become 300 + 200 = 500, the movement is 500 - 500 = 0, and the ending is **1,000**.
- Expense rises from 300 to 500, so the report still balances at 1,500 debit and 1,500 credit.
- The cancelled 400 and the February 50 never count.

**Comparison with Odoo's standard Trial Balance** (on the disposable `azk_ee24_test`)
- Settings: the same company as the only active one, 2026-01-01 to 2026-01-31, Draft Entries off and then on, no hierarchy.
- Every Initial, period and End debit and credit, and the totals, equal the hand calculation: **PASS**.
- Also **PASS** with matching options:
  - one journal at a time (the journal filter also limits the opening balance);
  - the cross-year fixture in January and February;
  - zero activity, and company-currency amounts;
  - the analytic filter (A1 gives 1,200, so whole items count);
  - two companies, a record rule and a five-level hierarchy.
- I claim parity only for these cases.

**Checks performed**
- `scripts/dev.sh test azk_dynamic_trial_balance`:
  - Run 1: **FAIL**, 1 failure and 2 errors out of 47 tests, all in the wizard tests, plus 88 translation warnings. All fixed.
  - Run 2: PASS.
  - Run 3, on the final code: **PASS**, "0 failed, 0 error(s) of 48 tests", 0 warning lines, 289 seconds.
- `scripts/dev.sh update azk_dynamic_trial_balance` on `azk_ee24`: PASS, 0 warnings. Version 18.0.1.1.0 is installed.
- Headless Chrome, `scripts/tb_wizard_smoke_check.py` against `azk_ee24`, on the final code: **PASS, 8 of 8**.
  - The checks: the menu, the dialog, the notice, Posted Entries ticked, the fields, the dependent options, a prefix tag, the Preview message and no JavaScript error.
  - The first run's screenshot showed Posted Entries unticked in a new form. I fixed that bug.
- **NOT RUN:**
  - the calculation engine (Stage 08) and the outputs (Stage 09);
  - in a browser: the Company field, the Analytic Accounts field, and a read-only accountant's view. The manual steps are in the handoff.

**Also corrected:** `docs/ai/stage_06.md` said the Stage 06 final response was displayed unchanged. After a context compaction I displayed a reworded version. The log now holds the text that was actually displayed, with a correction note.

**Open issues**
- There is no calculation engine, no output and no Trial Balance demo data yet. The fixtures are test data only.
- These are not compared with the standard report: currency rows, Skip Zero Balance, Only Parents and its level, the prefix filter, custom fiscal years and branches.
- Question Q-03 (the analytic policy) and Q-06 (the license) are still open, and the wizard mockup (M-02) is still missing.

**Changed files**
- **New in the addon:**
  - `models/report_options.py`, `models/account_prefix.py`, `models/trial_balance_wizard.py`;
  - the security files and `views/trial_balance_wizard_views.xml`;
  - `tests/common.py` and four test files.
- **New elsewhere:**
  - `scripts/tb_wizard_smoke_check.py`;
  - `docs/calculation_contract.md`, `docs/handoffs/stage_07_en.md`, `docs/ai/stage_07.md`;
  - two screenshots.
- **Updated:**
  - the manifest (18.0.1.1.0, now depending on `account_reports`);
  - STATE, assumptions (D-43 to D-49, V-08), architecture (4.9), the test plan (4.1 to 4.3) and the requirements matrix;
  - `docs/ai/README.md` and `docs/ai/stage_06.md`.
- **Commit:** "Stage 07: Trial Balance wizard, calculation contract and fixtures".

**Comprehension questions**
1. Why does the wizard refuse Show Amount Currency together with Hierarchy Only Parents?
2. In January, the 700 of 2025 revenue appears on Current Year Earnings, not on Revenue. Which dates decide this, and what does February's report show for Revenue?
3. Why must the chosen company be active in the company switcher, not just one of the user's companies?

**Next stage:** 08, the Trial Balance calculation engine. I'm stopping here.

---
