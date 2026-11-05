# Stage 02 - Requirements, assumptions, architecture and test plan

- **Date:** 2026-11-05
- **Tool / model:** Claude Code, Opus 5.5 (`claude-opus-5-5`), in the same CLI session as Stage 01B, after an automatic context compaction
- **Working directory:** the assessment kit root (`<kit-root>`) and `<kit-root>/solution`
- **Commit:** this log is part of the Stage 02 commit

**Transcription method:** see [README.md](README.md). The user text and the referenced instruction file are verbatim. The assistant messages are the text blocks recorded in the CLI's local session transcript, verbatim and in order, extracted by a script. The CLI's conversation summary from the context compaction is a tool artifact, not a user message, and is not reproduced.

**Redactions:** absolute local paths are replaced with `<kit-root>`, `<home>` or `<scratchpad>`. The CLI's paste markers around the user's pasted text are omitted. No credential or subscription value was printed.

## User prompt (verbatim)

The whole message was pasted text.

```text
Read prompts/02_requirements_and_design.txt and execute Stage 02 only,
following solution/AGENTS.md. Use the validated Enterprise setup on port 8071.
End with a short plain-English summary of how each module will work
and how we will test it. Stop after Stage 02.
```

## Referenced instruction file: `prompts/02_requirements_and_design.txt` (verbatim)

```text
STAGE 02  -  Freeze the requirements, assumptions, architecture, and acceptance plan

LANGUAGE: English only for all newly authored terminal prose, explanations, questions, and reports. Use simple ASCII formatting and short paragraphs/bullets instead of wide or box-drawn tables. Preserve source data and original historical logs. Arabic coaching happens outside this terminal.

Follow the project contract. Inspect the PDF, the confirmed Enterprise requirement, the pinned core/Enterprise source, and Stage 01/01B evidence. Inspect the actual supplied major version; Odoo 18 is still provisional unless confirmed. If Enterprise access is blocked, complete the requirement inventory but mark native-framework decisions provisional rather than inventing private internals. Do not implement the full features yet. Resolve choices explicitly and keep decisions small enough that I can explain them.

Create docs/requirements_matrix.md with a unique ID, PDF page, requirement, chosen interpretation, implementation location, test/evidence, and status. Include every selected exercise requirement, not just its major headings.

PARTNER MONITOR DESIGN
- Preserve the four required model names and all specified field names/types. Add only justified supporting fields/models: stable source identities, partner activity, scrape runs/work items or checkpoints, error details, retry scheduling, and completeness metadata as needed.
- Define status ordering ready < silver < gold, first observation, initial history, promotions/demotions, unknown statuses, reference removal, and reappearance. Names alone are not reliable identities. Define stable keys and database uniqueness.
- Treat a successful complete snapshot differently from a partial fetch or parse failure. Missing partners, countries, or references must not be marked removed/inactive from incomplete evidence.
- Explain daily discovery, bounded processing, separate country-validation and partner-reference-validation crons, retries, checkpoint durability, and overlap prevention. A savepoint or progress counter is not itself a durable commit. Inspect the actual version's transaction/cron behavior; do not assume an API from another Odoo release.
- Design one dashboard entry point with XML definitions/templates and all four required charts. It must run in our edition and share Status, Country, and Year First Seen filters. Investigate the actual available Enterprise and core actions/views first; use a small custom client action only if needed to meet the actual dashboard requirements. Do not replace the dashboard with four unrelated menu links.
- Record the incomplete original views specification. Propose list/form/search/history/reference views, graph/pivot views, and filters/groupings as an explicit assumption.

TRIAL BALANCE DESIGN
- Use a real TransientModel wizard with date range and company selection, plus every specified option. The PDF does not list date fields in its wizard inventory but requires a period throughout the report; record the added fields as necessary clarification.
- Preserve Many2one cardinality for Journal and Analytic Account unless the assessor explicitly changes it; their plural help text is ambiguous. Support multiple account-code prefixes with OR semantics.
- Posted entries always participate; optional drafts join them; cancelled entries never participate. Company/account/journal/analytic access must be enforced server-side.
- Document opening/closing debit-credit semantics, fiscal-year/carry-forward treatment, amount_currency date scope, analytic-distribution interpretation, hierarchy levels 1-5, parents-only behavior, and zero-activity filtering before implementing them.
- Use one authorized company per report. Inspect and compare the standard Enterprise Trial Balance on the same dataset, dates, company/localization and options before setting opening/closing debit-credit and fiscal-year/carry-forward semantics. Prefer native behavior wherever the assessment expects the standard report, and explicitly document intentional differences. The old generic ledger-based fallback is no longer the default. Keep inclusive period movement and independently calculated expected values. Do not invent opening adjustments or claim parity without matched-option evidence.
- Inspect the native Enterprise analytic-filter behavior and actual distribution representation before selecting the allocation contract. Prefer the verified native semantics unless the assessor requires otherwise. Proportional allocation remains a candidate interpretation, not an imposed default or explicit PDF requirement. No filter must not duplicate journal items across analytic plans; document and test the selected policy.
- Proposed amount-currency default: the additional column shows period movement in each transaction currency, clearly documented in its help text. Group rows by account and transaction currency; never sum different currencies into one foreign-currency total.
- Use one normalized calculation result for preview, PDF, and XLSX. Decide how exports receive exactly the selected filters and how concurrent users' reports stay isolated. Inspect account_reports and the native Trial Balance extension points; prefer an appropriate custom addon extension/adaptor over reimplementing the whole standard framework. Declare all required dependencies in the manifest, preserve the specified wizard/features, and explain any custom calculation/rendering still needed. Do not copy private Enterprise source into the submission or edit vendor code.

Create docs/architecture.md, docs/assumptions.md and docs/test_plan.md. Include a concise diagram of components, the security boundary, and the calculation contract. Record any version/edition conflict rather than changing scope silently. List only unresolved clarification points, such as the exact major version, missing mockup/views specification and intended reference report. Do not ask whether Enterprise is acceptable: it is already confirmed. Continue independent work under explicit provisional assumptions where feasible; do not present blocked Enterprise-dependent design as verified. Explain the decisions in English and stop with the standard report.
```

## Conversation during the stage (recorded text, verbatim, in order)

Assistant message 1:

> I'm reading the assessment PDF and the project state files before writing the Stage 02 design.

Assistant message 2:

> I've read the PDF and the later stage prompts. Next I'll check the version-sensitive APIs in the pinned 18.0 sources, starting with cron and transaction behavior.

Assistant message 3:

> Still checking the pinned sources. Cron batching and transient-record access are confirmed; next I'm checking the account, analytic and mail APIs.

Assistant message 4:

> Reading the native Enterprise report framework's filter and extension points (names only, nothing copied).

Assistant message 5:

> Still reading the native Trial Balance rules: opening balances, fiscal-year carry-forward and netting. Then I'll check the dashboard options.

Assistant message 6:

> Still investigating: the native PDF header supports per-report template overrides. Checking what it prints, then the dashboard options.

Assistant message 7:

> Cron and transaction behavior is verified in the pinned core. Now checking the mail and graph-view APIs the design depends on.

Assistant message 8:

> While the disposable database installs (about 6 minutes), I'll keep reading the native report's data and extension hooks.

Assistant message 9:

> The native report framework exposes the needed hooks by name. Checking the export entry points and the dashboard alternatives next.

Assistant message 10:

> While the install runs, checking two more APIs the design relies on: partial unique indexes and the superuser flag for cron users.

Assistant message 11:

> Disposable database `azk_ee24_clean` is ready: accountant installed, 90 modules, no warnings, 5 min 20 s. Running the native Trial Balance probe now; it rolls back at the end.

Assistant message 12:

> Decided: the Trial Balance engine builds its own hierarchy rows, using the same rules the native report showed in the probe. Checking `account_reports` dependencies, then writing the documents.

Assistant message 13:

> Next I'll pin the PDF page of each requirement for the matrix, then write the documents.

Assistant message 14:

> Writing `docs/architecture.md`: component diagram, security boundary, Partner Monitor sync design, and the Trial Balance contract with the probe evidence.

Assistant message 15:

> Verifying a few claims in the draft before relying on them.

Assistant message 16:

> Correction: the admin's notification preference in this build is "email", not "inbox" (checked in `azk_ee24_clean`). Fixing that paragraph.

Assistant message 17:

> Writing the expanded `docs/assumptions.md`: resolved ambiguities, new design decisions, and only the clarification points still open.

Assistant message 18:

> Writing `docs/test_plan.md` with test IDs, fixtures and hand-calculated expected values. First, a quick check that the image ships `freezegun` for date-dependent tests.

Assistant message 19:

> Tidying one unclear sentence in the test plan: checking whether an XLSX reader is available in the image.

Assistant message 20:

> Rewriting `docs/requirements_matrix.md` at the granularity the prompt asks for: every field, option, help text and chart, each with its interpretation, planned location and planned test.

Assistant message 21:

> Adding a note on split requirement IDs to the matrix, and pointing the Stage 01B "Decisions for Stage 02" list to where they are now resolved.

Assistant message 22:

> Updating `docs/STATE.md` for the end of Stage 02.

Assistant message 23:

> The design documents are written. Next: the Stage 02 handoff, the AI log, and the commit.

Assistant message 24:

> Aligning the kit's `CLAUDE.md` (outside Git) with the Stage 02 decisions, so future sessions don't follow the old provisional defaults.

Assistant message 25:

> Writing the Stage 02 AI log next. I'll check the extraction scripts from the earlier stages so I can reuse them.

Assistant message 26:

> The script matched the first "final response" heading instead of the last, and replaced too much. Restoring the file from Git and redoing it on the right section.

Assistant message 27:

> The fix now touches only the last section. Checking that the two earlier final responses in that log also match what was displayed.

Assistant message 28:

> Both earlier final-response sections in that log hold drafts, not the displayed text. The conversation sections match the transcript. Extracting the two displayed responses to correct those sections.

Assistant message 29:

> Checking that the corrected sections really differ only in wording: comparing the numbers and code names in each draft with the displayed version.

Assistant message 30:

> The differences are wording and detail (the displayed versions add commit IDs and leave out a few details); no result or status differs. Making the correction note say exactly that.

Assistant message 31:

> Checking that the newly inserted displayed texts contain no customer project names, credentials or absolute paths, which the log's redaction rules exclude.

Assistant message 32:

> Recording these corrections in `docs/ai/README.md` and adding the Stage 02 index row.

Assistant message 33:

> Writing the final Stage 02 report to the scratchpad. It goes into the AI log and is then displayed unchanged.

## Notes on accuracy

- This log was assembled from the transcript just before its own commit. The few short progress messages written after that point, while committing, are not included. The final response below is included as prepared, and it was displayed unchanged.
- Facts in the messages that were later corrected stay as written here; the corrections are listed in [README.md](README.md) (mistakes table) and reflected in the Stage 02 documents.

## Summary of tool activity (summary, not verbatim)

1. Checked the disk (13 GB free on C:) and Git (clean at `00fb80c`). Read `AGENTS.md`, `docs/STATE.md`, the requirements matrix, the assumptions, the Stage 02 prompt and the prompts of Stages 03 to 09. Read PDF pages 1 to 8 with `pdftotext`.
2. Read the version-sensitive code in the pinned Community source `<kit-root>/runtime/community/18.0-4e5027c1/`:
   - `ir.cron`: batching, the progress API, job locking, failure handling;
   - `odoo/models.py`: SQL constraints, access checks, transient vacuum;
   - the shell's rollback, the server's time limits, and `fields.py` relation rules;
   - accounts and account groups, journal item fields, the analytic mixin;
   - mail notification preferences;
   - the graph view parser and the `View` component, `board` and spreadsheet global filters;
   - the `website_crm_partner_assign` controller and templates;
   - the SQL index helpers.
3. Read the Enterprise `account_reports` code, citing it by name only: report options and filters, the Trial Balance and General Ledger handlers, the custom-handler hooks, the PDF templates, the export method and download route, the client action's option loading and the option labels. Nothing was copied into the repository.
4. Created the disposable database `azk_ee24_clean` with `scripts/dev.sh clean-install accountant`: 5 min 20 s, 0 warnings, 0 errors.
5. Ran a probe script through `scripts/dev.sh shell azk_ee24_clean`. It created a probe company with the generic chart, nine journal entries, two analytic plans and five nested account groups. It ran the native Trial Balance with eight option sets, printed the lines and rolled back. The full output is in the private log `<kit-root>/runtime/logs/stage02_native_tb_probe.log`.
6. Ran read-only checks: the users' notification type (psql, `azk_ee24_clean`), and the Python packages and browsers available in the image.
7. Wrote:
   - `docs/architecture.md` and `docs/test_plan.md` (new);
   - `docs/requirements_matrix.md` (rewritten);
   - `docs/assumptions.md` (expanded);
   - updates to `docs/STATE.md`, `docs/environment.md` and `docs/enterprise_transition.md`;
   - the Stage 02 handoff;
   - the kit-root `CLAUDE.md` architecture summary (outside Git).
8. Compared every logged final response in `docs/ai/stage_01b.md` with the session transcript and replaced the three drafts with the displayed text. The first script run replaced the wrong section; the file was restored with `git checkout` and corrected again.
9. Scanned the changes for non-ASCII text, absolute paths and secret values, and committed only the intended files.

## Assistant final response (verbatim)

Everything between the two rules below is the final visible response.

---

Stage 02 is done. The requirements, assumptions, architecture and test plan are written and committed. As the stage requires, no feature code was written.

**What I did**
- Re-read the assessment (pages 1 to 8) and the prompts for the later stages, so this design fits Stages 03 to 09.
- Checked every version-sensitive API in the pinned 18.0 sources. Enterprise code is cited by name only. The checks covered:
  - how scheduled jobs batch and commit their work;
  - database constraints and wizard access rules;
  - account codes, account groups and analytic distributions;
  - mail notification preferences;
  - chart views and the dashboard options Odoo already has;
  - the native report framework's hooks and exports;
  - the Odoo 18 module behind the public partners pages.
- Ran the native Enterprise Trial Balance on a small known dataset in a throwaway database, then rolled everything back. The dataset had posted, draft and cancelled entries, a prior-year result, a 60/40 analytic split, a combined analytic key, a bank-journal entry and five levels of account groups.

**Real commands and results**
- `df -h /c`: 13 GB free, down from 17 to 19 GB last session; I didn't investigate the drop.
- `ODOO_EDITION=enterprise-20241208 scripts/dev.sh clean-install accountant`: PASS. A fresh `azk_ee24_clean` with 90 modules, no warnings or errors, in 5 min 20 s.
- `scripts/dev.sh shell azk_ee24_clean` with the probe script: PASS. Eight report runs, all rolled back. What the native report did:
  - Bank, January, posted only: Initial 1,000, movement +500 and -300, End 1,200. With drafts, End 1,000. The cancelled entry never counted. These are the Stage 07 expected values.
  - Income and expense accounts start again at the fiscal-year start; the 2025 result appears on "999999 Undistributed Profits/Losses".
  - Filtering on analytic account A1 counted the 60/40 item at its full 1,000, not 600. A combined key counted once.
  - A journal filter also limits the opening balance. Group subtotals add up their children's netted amounts.
- Read-only checks: in this build `admin` gets notifications by email, not in the Odoo Inbox. The image has `freezegun`, `openpyxl` and `xlrd`, but no Chrome.
- NOT RUN: addon tests (no addon code changed) and browser checks (I have no browser).

**Key decisions**
- **Trial Balance:**
  - Our own calculation engine runs inside our own report record and handler in Odoo's report framework. Odoo's report screen, PDF export and XLSX export all display its single result.
  - Opening balances, the fiscal-year carry-forward, netting and the analytic filter follow the native rules the probe showed.
  - Journal and analytic account stay single-choice, as the PDF says.
  - One authorized company per report, plus Date From and Date To.
  - Amount Currency shows each currency's period movement and never adds different currencies together.
  - The module will declare `account_reports` in Stage 07.
- **Partner Monitor:**
  - Each country and partner is identified by the site's own id, with unique database constraints.
  - Nothing is removed unless a complete, checked snapshot shows it is gone.
  - Work is queued as small saved tasks that only one worker job processes, in bounded batches. Odoo's scheduler commits after each batch, and claimed tasks are locked rows.
  - A failed run posts a note, addressed to the configured user, on the run's chatter.
  - The dashboard is a small client action embedding four standard chart views, all driven by one filter bar.

**Corrections**
- My first draft said the admin gets notifications in the Odoo Inbox by default; the check above showed email. I fixed the text before the commit.
- The Stage 01B AI log held the drafts of its three final responses, not the text you actually saw. I replaced them with the displayed text from the session transcript and recorded this in `docs/ai/README.md`. My first fix script replaced the wrong section; I restored the file from Git and redid it correctly.

**Open issues and assumptions**
- Questions for the team lead; none blocks Stage 03:
  - Q-02: the missing views specification, mockup and documentation example.
  - Q-03: is the native Trial Balance the intended reference, including its carry-forward and whole-item analytic filter?
  - Q-04: the major version.
  - Q-05: a matched Enterprise build for the newer core.
  - Q-06: the license for an addon that depends on the Enterprise module `account_reports`.
- The live partners site may differ from the 18.0 module. Stage 04 checks a small sample.
- The exact mechanics of three report hooks (column groups, PDF header, preview filters) are verified in Stages 08 and 09, with a documented fallback.
- To see the failure note in the Discuss Inbox, the recipient must choose "Handle in Odoo".

**Changed files**
- New:
  - `docs/architecture.md`
  - `docs/test_plan.md`
  - `docs/handoffs/stage_02_en.md`
  - `docs/ai/stage_02.md`
- Updated:
  - `docs/requirements_matrix.md`: one row per requirement, mostly DESIGNED
  - `docs/assumptions.md`: D-01 to D-17, V-01 to V-07, Q-06
  - `docs/STATE.md`: Stage 02 DONE
  - `docs/environment.md`
  - `docs/enterprise_transition.md`
  - `docs/ai/stage_01b.md`
  - `docs/ai/README.md`
- Outside Git:
  - the kit's `CLAUDE.md` architecture summary;
  - the private logs `runtime/logs/stage02_*`;
  - the throwaway database `azk_ee24_clean`.
- Commit: "Stage 02: requirements, assumptions, architecture and test plan".

**Comprehension questions**
1. Why can a crash in the middle of a worker batch never leave a work item permanently claimed?
2. Why must the Trial Balance engine re-check the company, journal and analytic ids even though the wizard already checked them?
3. In the probe, why did the prior-year revenue appear on account 999999 instead of the revenue account?

**Next stage:** 03, Partner Monitor models, permissions and basic UI. I'm stopping here. When you're ready:

Read prompts/03_partner_models.txt and execute Stage 03 only, following solution/AGENTS.md.

**In plain English: how each module will work**
- **Partner Monitor:**
  - Every day, a scheduled job writes a to-do list: read the country list, then each country's pages, then the details of partners that are new or changed.
  - A separate worker job does a few items at a time and saves after each small batch. If Odoo stops halfway, finished items stay finished and only the last batch is redone.
  - Partners are tracked by the number in their odoo.com link, so reading a page twice never creates duplicates. Status changes become history rows marked promoted or demoted.
  - Nothing is marked removed unless all the pages for that country or partner were read and checked. Two more jobs retry countries and partners whose counts didn't match.
  - If a run has failures, the chosen user gets one note.
  - The dashboard is the module's home page: one filter bar (status, country, year first seen) drives all four charts.
- **Dynamic Trial Balance:**
  - The user fills in a wizard: dates, company and options.
  - Our engine calculates every number in one place, following the rules of Odoo's own Trial Balance, which we checked on real data: balance-sheet accounts carry their whole history, income and expense restart each fiscal year, drafts count only when asked, and cancelled entries never count.
  - Odoo's own report screen shows the result, and Odoo's own exporters turn the same result into the PDF and XLSX, so the three always agree.
  - What we add: Balance columns, account-prefix filters, hiding empty accounts, one line per currency, and a hierarchy limited to a chosen level.

**How we will test them**
- **Partner Monitor:**
  - the parsers run on saved web pages, never the live site;
  - database tests cover duplicates, history and permissions;
  - failure tests: one partner failing, mismatched counts, partial pages, and two workers at once;
  - one real stop and restart of the worker in a throwaway database;
  - dashboard tests check that the chart totals match the filtered partners.
- **Trial Balance:**
  - small datasets whose expected numbers are worked out by hand, for example Bank ending at 1,200 with posted entries only and 1,000 with drafts;
  - separate datasets for cross-year, currency, analytic and hierarchy cases;
  - access tests with two users and two companies;
  - a comparison with Odoo's native Trial Balance on the same data;
  - checks of the real PDF text and XLSX cells.

---
