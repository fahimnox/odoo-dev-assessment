# Stage 08 - Trial Balance calculation engine

- **Date:** 2026-11-15
- **Tool / model:** Claude Code, Opus 5.5 (`claude-opus-5-5`), in the same CLI session as Stages 01B to 07
- **Working directory:** the assessment kit root (`<kit-root>`) and `<kit-root>/solution`
- **Commit:** this log is part of the Stage 08 commit

**Transcription method:** see [README.md](README.md). The user prompt and the referenced instruction file are verbatim. The assistant messages are the visible text blocks recorded in the CLI's local session transcript, verbatim and in order, extracted by a script. Tool calls, tool outputs, reasoning blocks and system notices are not reproduced.

**Redactions:** absolute local paths are replaced with `<kit-root>`, `<home>` or `<scratchpad>`. The CLI's paste markers around the user's pasted text are omitted. No credential or subscription value appeared.

## Referenced instruction file: `prompts/08_trial_balance_engine.txt` (verbatim)

```text
STAGE 08  -  Build and test the Trial Balance calculation engine

LANGUAGE: English only for all newly authored terminal prose, explanations, questions, and reports. Use simple ASCII formatting and short paragraphs/bullets instead of wide or box-drawn tables. Preserve source data and original historical logs. Arabic coaching happens outside this terminal.

Follow the project contract and the documented Stage 07 calculation contract. Implement one reusable server-side report service/adapter, extending the inspected Enterprise report framework where suitable, that returns normalized filters, leaf rows, hierarchy rows, per-currency summaries, base-currency totals, and warnings/metadata. Keep standard behavior in supported native extension points; implement only the necessary custom gaps and declare dependencies. Keep rendering out of the arithmetic.

Required correctness and security:
- Validate the selected company and all filter records against the caller's real access. Respect record rules and allowed-company scope on preview and every export. Never use blanket sudo() to make an accounting report work.
- Prefer appropriate ORM/grouped operations. If SQL is genuinely required, parameterize values, derive authorized scope using verified Odoo APIs, and explicitly preserve access rules. Filtering only by company is not a substitute for all applicable record rules. Add tests proving restricted records stay inaccessible.
- Use the same filters for opening and movement. Posted is always included; drafts are optional; cancelled never included. Use inclusive period boundaries. Handle currency rounding, negative balances and reversals correctly.
- Apply the documented native-compatible opening/ending debit-credit, movement and fiscal-year contract established in Stage 07, including any explicitly justified assessment-specific differences. Never double-count opening entries or subtotal rows.
- Implement literal multi-prefix matching, empty selections, account groups, levels 1-5, parents-only, subtotals, ungrouped accounts, and no-data results. Preserve all selected leaf amounts exactly once in totals.
- Implement the selected analytic allocation contract using verified source behavior. Test a 60%/40% allocation and compare the selected policy with native report behavior: a 1,000 debit yields 600 if our documented contract uses proportional allocation; full-item selection has different expected results and must be described explicitly. Do not change the expected value just to match a bug. Also test composite keys/multiple plans, missing distribution, and no-filter full-value behavior. Do not multiply an item by the number of analytic plans.
- Group by transaction currency when requested. Keep stored company-currency amounts separate from amount_currency; do not recalculate historical balances using today's exchange rate. Example separate fixture: USD 100 - 40 = USD 60 and EUR 70 - 20 = EUR 50 must remain separate, never become an undifferentiated 110. Use internally consistent base-currency amounts and balanced counterpart entries in fixtures.
- Keep zero-net activity visible; hiding zero accounts is not simply balance == 0. Ensure currency rounding is used for comparisons.
- Compute efficiently for the declared assessment dataset. Avoid one database query per account or per output cell. Do not claim large-scale performance without measuring it.

Run meaningful Odoo tests against manually fixed expectations:
1. Stage 07 base fixture, posted-only and with drafts.
2. Start/end date boundary records, excluded future and cancelled records, negative balances and an empty period.
3. Prefix/journal filters and consistent opening scope.
4. Zero-net activity preserved; truly inactive zero accounts hidden.
5. Currency groups, separate foreign totals, reconciliation of signed base balances/gross movements across grouped and ungrouped modes.
6. The chosen native-compatible analytic policy, composite keys and no duplication without a filter.
7. Hierarchy depths 1-5, group subtotals, parents-only and ungrouped leaves; no double-counting in grand totals.
8. Unauthorized company, forbidden account/journal, another user's report/wizard, and tampered export parameters.
9. Matched-option comparisons with the standard Enterprise Trial Balance, plus a cross-fiscal-year fixture; retain hand-calculated tests so this is not merely comparing a function to itself.

Save exact commands and results in docs/test_results.md. If accounting assumptions need review, show a concrete input/output example rather than hiding the difference. Explain the path from one journal item through filtering, aggregation, hierarchy, and final totals, with real file/function references. Stop with the standard report.
```

## Conversation (recorded text, verbatim, in order)

### User prompt 1 (verbatim; the whole message was pasted text)

```text
Read prompts/08_trial_balance_engine.txt and execute Stage 08 only,
following solution/AGENTS.md and docs/calculation_contract.md.

Continue from Stage 07 commit cabfb75 on the validated Enterprise
environment on port 8071. Use disposable databases for tests.

Implement the shared calculation engine using the Stage 07 fixtures
and their independently calculated expected results.

Follow the complete Stage 08 test requirements. Pay particular
attention to:
- Bank ending at 1,200 posted-only and 1,000 with drafts.
- Fiscal-year opening balances, including January versus February.
- The verified whole-item analytic filtering policy.
- Separate transaction currencies and correct base-currency totals.
- Preserving accounts with zero-net activity.
- Hierarchy totals without double-counting or losing ungrouped accounts.
- Company access and record rules enforced inside the engine.

Compare supported cases with the native Enterprise Trial Balance
using matching options. Report the exact scope of those comparisons.

In the handoff, trace one Bank journal item through filtering,
calculation and final totals, with the real file and function names.
Explain January versus February using the actual cross-year fixture.

Keep Preview, PDF and XLSX tracked for Stage 09, and Stage 04 as PARTIAL.
Record actual commands and results. Use English ASCII only.
Stop after Stage 08.
```

Assistant message 1:

> I'll start by checking the repository state, since four docs files show as changed on disk since the Stage 07 commit, and the free disk space.

Assistant message 2:

> Now I'll register the engine and give the wizard a method that asks it for the result. The three buttons stay entry points until Stage 09.

Assistant message 3:

> Next, the engine tests for the cross-year fixture: January at the fiscal-year start, February, February with drafts, and how the carry-forward behaves with prefixes.

Assistant message 4:

> Now the advanced fixtures. I'll read the current file once, because it was changed by script in Stage 07, then add the engine tests class by class.

Assistant message 5:

> Now the access and efficiency tests: who may run the engine, tampered options, the wizard path, and a query count that must not grow with the number of accounts.

Assistant message 6:

> Syntax check, then Stage 08 run 1, with free space sampled again. I'll update the runner script to name its logs per stage.

Assistant message 7:

> While run 1 executes, I'll write the documentation that doesn't depend on the results. First, a contract section describing the engine as built and its result structure:

Assistant message 8:

> Now the Stage 08 decisions in `assumptions.md`, after D-49:

Assistant message 9:

> The edits applied, and run 1 is still installing. Next, the architecture section for Stage 08:

Assistant message 10:

> Run 1 is still installing modules. I'll wait for the result before writing the documents that depend on it.

Assistant message 11:

> I'll check how Odoo 18's `float_round` builds its result. It decides whether comparing a rounded total with the literal 290.6 is exact or off by one unit in the last place.

Assistant message 12:

> The admin has `account.group_account_readonly`, implied through `account.group_account_user`. Now the small wording fix in the script's output line:

Assistant message 13:

> I'll wait for run 2.

Assistant message 14:

> `azk_ee24` is on 18.0.1.2.0 (exit code 0, 78 s, 0 warnings). Now the read-only comparison on the demo company's own entries:

Assistant message 15:

> I'll wait for the final run.

Assistant message 16:

> The browser check passes **8 of 8** on the final code and shows the new message. Next the documentation, starting with the requirements matrix: the prepared script, then K-02 and G-10 by hand.

Assistant message 17:

> Next, `docs/test_results.md`, the file the stage asks for, with the exact commands and results:

Assistant message 18:

> Next, the test plan: a short Stage 08 section pointing to the new results file.

Assistant message 19:

> Next, `STATE.md`:

Assistant message 20:

> Next, the Stage 08 handoff. It includes the two explanations you asked for: one Bank journal item traced through the real functions, and January against February on the cross-year fixture.

Assistant message 21:

> Now the AI-log index and the mistakes table:

Assistant message 22:

> The order is right. Next, a short Stage 08 note in the kit's guidance file, outside the repository:

Assistant message 23:

> Next, the AI log: a tool-activity summary and the final response, then assembly from the transcript.

Assistant message 24:

> Before assembling the Stage 08 log, I'll check that the Stage 07 final response I displayed matches the one logged in `docs/ai/stage_07.md` word for word, so the Stage 06 mistake isn't repeated.

## Notes on accuracy

- This log was assembled from the transcript just before its own commit. Progress messages written after that point, while committing, are not included. The final response below is included as prepared, before it was displayed.
- The Stage 07 final response was checked against the session transcript before this log was written: it was displayed exactly as logged in [stage_07.md](stage_07.md).
- The prompt asked to continue from the Stage 07 commit `cabfb75`; this stage's work starts there.
- Facts in the messages that were later corrected stay as written here; corrections are listed in [README.md](README.md) (mistakes table) and in the Stage 08 handoff.

## Summary of tool activity (summary, not verbatim)

1. Checked Git (clean at `cabfb75`; the "changed on disk" notices came from line-ending normalization at the Stage 07 commit) and the free space on C: (47 GB). Reread the Stage 08 prompt and the calculation contract.
2. Read the pinned 18.0 sources by name:
   - `_read_group` and `_search` (access check and record rules);
   - `include_initial_balance` and its search method;
   - the account-group record rule;
   - `account.move._reverse_moves`;
   - the test query counter (`sql_log_count`);
   - `float_round`.
3. **Code:**
   - `models/trial_balance_engine.py` (new);
   - `_compute_report` and the updated entry-point message in the wizard;
   - the manifest version, 18.0.1.2.0;
   - test helpers and the TB-D fixture in `tests/common.py`;
   - engine tests in the Stage 07 fixture classes, `tests/test_engine_boundaries.py`, `tests/test_engine_access.py`;
   - `scripts/tb_engine_vs_native.py`.

   A self-review of the draft engine before any run removed per-account queries, a negative zero and a `fetch()` on a computed field.
4. **Test runs** of `scripts/dev.sh test azk_dynamic_trial_balance`, each on a fresh `azk_ee24_test`, with free space sampled every 30 s:
   - run 1: 84 of 84;
   - run 2: 85 of 85, with a rounding test and logged query counts;
   - run 3, on the final code: 85 of 85, 0 warning lines.
5. **`azk_ee24`:** a read-only query of the admin's accounting groups; two upgrades, the second after the version bump, each with 0 warnings; and the read-only comparison script in the Odoo shell, with 6 of 6 cases matching.
6. **Browser:**
   - The wizard check failed at the login page.
   - Docker inspection showed both containers stopped at 06:20:26 UTC, and the engine now reports version 29.9.2.
   - `scripts/dev.sh start`, then the check passed 8 of 8.
7. **Docs:** `test_results.md` (new), the contract's section 15, architecture 4.10, assumptions D-50 to D-53, test plan 4.4, the requirements matrix, STATE, the handoff, this log and the index. Outside the repository, a Stage 08 note in the kit's guidance file. The changes were scanned for non-ASCII text, local paths and secrets, and only the intended files were staged.

## Assistant final response (verbatim)

Everything between the two rules below is the final visible response.

---

Stage 08 is done and committed. Stage 04 stays **PARTIAL**, and the Preview, PDF and XLSX buttons are still entry points for Stage 09.

**What was built**
- **The engine,** `azk_dynamic_trial_balance.engine` in `models/trial_balance_engine.py`. Its `compute(options)` returns one result that all three outputs will render: filters, display lines, account rows, group rows, totals, per-currency totals, warnings and metadata.
- **Access checks inside the engine.** It requires the accounting read-only group and validates every option again. It then runs three grouped queries as the calling user, so record rules and the company scope apply. There is no `sudo()` and no SQL.
- **The wizard's `_compute_report()`,** which returns that result for the wizard's options.

**The results you asked about** (each checked against hand-written numbers)
- **Bank:** ends at **1,200** with posted entries only, and at **1,000** with drafts.
- **January versus February** (the cross-year fixture):
  - In January, Revenue opens at 0. The 2025 revenue of 700 appears on Current Year Earnings.
  - In February, January's 500 revenue and 300 expense are in the opening. Current Year Earnings still shows only 2025's 700.
- **Analytic filter:** it takes whole journal items, as Odoo's standard report does. A1 gives 1,200 (the 1,000 item in full, plus 200 from the combined A1 and B1 key), not 800 as a 60/40 split would.
- **Currencies:** USD 60 and EUR 50 stay separate, never added into 110. Their balances add up to the account rows.
- **Skip Zero Balance:** an account whose debits and credits cancel out stays visible; an account with no activity at all is hidden.
- **Hierarchy:** five levels of groups, "(No Group)" for accounts without a group, and Hierarchy Only Parents at levels 1 to 5. The totals never include group rows.
- **Access:** these are refused: another company, a company not switched on, tampered options, and users without accounting read access. A record rule hides journal items from the engine too.

**Comparison with Odoo's standard Trial Balance**
- **Settings:** the same company as the only active one, the same dates, matching draft options, the same single journal or analytic account, and no hierarchy (except for the hierarchy fixture).
- **What was compared:** each account's opening, period and closing debit and credit, and the totals.
- **PASS for every case:**
  - the base fixture: posted, with drafts, and each journal alone;
  - the cross-year fixture: January, February, and February with drafts;
  - the date-boundary fixture: January posted and with drafts, plus two single days;
  - zero activity, currencies (in company currency), the analytic filter (none, A1, A2, B1), two companies, a record rule, and the hierarchy with its groups and depths.
- **On `azk_ee24`'s own demo data:** 6 of 6 cases match. But that data has no drafts in those periods, so it doesn't test drafts.
- **Not compared,** because the standard report has no such option: currency rows, Skip Zero Balance, Hierarchy Only Parents and its level, and account prefixes.
- **Not covered by any test:** custom fiscal years and branches.

**Checks performed**
- `scripts/dev.sh test azk_dynamic_trial_balance`:
  - Run 1: PASS, 84 of 84.
  - Run 2: PASS, 85 of 85.
  - Run 3, on the final code: **PASS**, "0 failed, 0 error(s) of 85 tests", 0 warning lines, 326 seconds.
- **Query count:** 15 to 16 queries per report after warm-up, whether 4 or 24 accounts have amounts. I didn't measure timing on large data.
- `scripts/dev.sh update azk_dynamic_trial_balance` on `azk_ee24`: PASS, 0 warnings. Version 18.0.1.2.0 is installed.
- **Wizard browser check:** the first attempt **FAILED** at login, because the web server was not running. After `scripts/dev.sh start`, it **PASSED 8 of 8**.
- **Disk:** free space on C: stayed between 47 and 48 GB.

**Docker restart:** both containers stopped at 06:20 UTC, before this stage started. Docker's engine now reports version 29.9.2, so Docker Desktop was most likely updated. Nothing was lost, and `scripts/dev.sh start` brought the web server back.

**Open issues**
- Stage 09: the Preview, PDF and XLSX outputs, through Odoo's report framework (`account_reports`).
- The Trial Balance demo data required by the PDF is still missing.
- Questions Q-03 (the analytic policy) and Q-06 (the license) are still open, and the wizard mockup (M-02) is still missing.

**Changed files**
- **New:**
  - `models/trial_balance_engine.py`;
  - `tests/test_engine_boundaries.py` and `tests/test_engine_access.py`;
  - `scripts/tb_engine_vs_native.py`;
  - `docs/test_results.md`, `docs/handoffs/stage_08_en.md` and `docs/ai/stage_08.md`.
- **Updated:**
  - the manifest (18.0.1.2.0), `models/__init__.py`, and the wizard (`_compute_report`);
  - `tests/common.py` and the three Stage 07 test files, which now hold the engine tests;
  - the calculation contract (section 15), architecture (4.10), assumptions (D-50 to D-53) and the test plan (4.4);
  - the requirements matrix, STATE and `docs/ai/README.md`.
- **Commit:** "Stage 08: Trial Balance calculation engine".

The handoff follows the Bank journal item of 2026-01-20 through each engine function to the totals, and explains January versus February on the cross-year fixture.

**Comprehension questions**
1. Why does the engine check the accounting read-only group itself, when every query already applies the record rules?
2. In the cross-year fixture's February report, which query puts January's revenue into the opening, and which one puts the 2025 revenue on Current Year Earnings?
3. Why must the totals never include group rows, and how does the engine make sure they don't?

**Next stage:** 09, the Preview, PDF and XLSX outputs. I'm stopping here.

---
