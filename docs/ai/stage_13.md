# Stage 13 - Code walkthrough (PAUSED after section 1)

- **Date:** 2026-11-17
- **Status:** PAUSED by the user after section 1 of 7, before answering its question, to publish first (Stage 15). Stage 13 resumes after publication; this log will be continued then.
- **Tool / model:** Claude Code, Opus 5.5 (`claude-opus-5-5`), in the same CLI session as Stages 01B to 12, after a context compaction at the end of Stage 12
- **Working directory:** the assessment kit root (`<kit-root>`) and `<kit-root>/solution`
- **Commit:** no commit during Stage 13; this log is part of the Stage 15 publication commit

**Transcription method:** see [README.md](README.md). The user prompt and the referenced instruction file are verbatim. The assistant messages are the visible text blocks recorded in the CLI's local session transcript, verbatim and in order, extracted by a script. Tool calls, tool outputs, reasoning blocks and system notices are not reproduced.

**Redactions:** absolute local paths are replaced with `<kit-root>`, `<home>` or `<scratchpad>`. The CLI's paste markers around the user's pasted text are omitted.

**Private material, not in this repository:** as the Stage 13 prompt requires, the code map and the record of the candidate's answers are private study notes outside the repository (`<kit-root>/private_study/`).

## Between Stage 12 and Stage 13 (recorded text, verbatim, in order)

The CLI compacted the conversation's context at the end of Stage 12, after its commit. The assistant then displayed the Stage 12 final report (logged in [stage_12.md](stage_12.md)), and the user pasted the Stage 13 request. Nothing else was recorded between them.

## Referenced instruction file: `prompts/13_code_walkthrough.txt` (verbatim)

```text
STAGE 13  -  Teach me the implemented solution using its actual code

LANGUAGE: English only for all newly authored terminal prose, explanations, questions, and reports. Use simple ASCII formatting and short paragraphs/bullets instead of wide or box-drawn tables. Preserve source data and original historical logs. Arabic coaching happens outside this terminal.

Follow the project contract. This is a learning stage. I know Python/Django but have not studied Odoo systematically. Use clear English, precise terminology, and small examples. Any Arabic explanation will happen separately with ChatGPT. Do not give me a memorized speech detached from the repository, and do not pretend an unimplemented feature exists.

Also save the code map in clear English so I can share it with ChatGPT for Arabic coaching. First inspect the final source and test results. Build a short private study map outside the public repository, e.g. ../private_study/code_map.md. Link each topic to actual files and functions and, when useful, current line numbers. If a proposed design was not implemented, explain the implementation that actually shipped.

Teach in short interactive sections, pausing after each section for my explanation in my own words:
1. A 60-second project overview: what each addon solves, inputs, stored data, outputs, selected exercises, edition/version, and limitations.
2. Odoo for a Django developer: addon/manifest/dependencies/imports; Model versus TransientModel; fields and recordsets; env/domain/context; XML views/actions/menus/XML IDs; install/update/restart; ACLs versus record rules; testing and demo data.
3. Partner data flow: raw HTML -> parser -> validated snapshot -> idempotent ORM write -> history -> chart. Trace one concrete partner and show a matching fixture/test.
4. Failure flow: one unit fails, another succeeds, the transaction ends, the worker restarts, retries are bounded, and missing records are not falsely deleted. Explain precisely which progress survives a process kill and why.
5. Report data flow: wizard -> authorized journal items -> opening/movement/ending -> optional analytic/currency grouping -> hierarchy -> normalized result -> preview/PDF/XLSX. Manually calculate the Bank row in the golden example with me.
6. Security and design choices: show one actual denied-access test, one justified tradeoff, one alternative we rejected, and a real limitation. Explain the difference between filtering a widget and enforcing access on the server.
7. Version-sensitive code: identify a few APIs/templates/fields verified against the pinned source. Show how to investigate them instead of memorizing possibly outdated names.

For every section: explain briefly; show a real excerpt from our custom code (use interface/path references rather than copied private Enterprise source); ask one comprehension question; wait for my answer; correct misconceptions; then continue. Do not dump all answers at once. Use questions requiring prediction or code location, not only definitions.

Finish only after the sections with a private one-page revision sheet, a list of areas I still need to practice, and three small exercises I can perform in the sandbox. Any first-person presentation claims must be based on what I have actually understood or verified. Start now with section 1 only and wait for my response.
```

## Conversation (recorded text, verbatim, in order)

### User prompt 1 (verbatim; the whole message was pasted text)

```text
Read prompts/13_code_walkthrough.txt and begin Stage 13 as an
interactive learning session, following solution/AGENTS.md.

I know Python and Django but am new to Odoo.

Inspect the final implementation and create the concise private
code map required by the prompt, outside the public repository.
Reference actual custom-code files, functions and relevant tests.

Teach one section at a time. Use short explanations, concrete examples
and Django comparisons where they are accurate.

Start with section 1 only:
- What each addon does.
- Where its inputs come from.
- What it stores and produces.
- How the Community core, Enterprise addons and our addons fit together.
- The main verified limitations.

Keep this first explanation under 300 words.
Then ask one comprehension question and wait for my answer.

Correct misunderstandings before continuing. Track what I actually
understand based on my answers.

Keep Stage 13 IN PROGRESS until the walkthrough is completed.
Use English ASCII only. Start section 1 now.
```

Assistant message 1:

> Almost done inspecting; now checking two test helpers, then writing the code map to `private_study/` at the kit root (outside the repository).

Assistant message 2:

> Writing the code map and a progress tracker now, both outside the repository.

Assistant message 3:

> Recording the Stage 13 status in the kit notes, then I'll present section 1.

Assistant message 4:

> Stage 13 has started. The private code map covers all seven sections, with file and line pointers. It is at `<kit-root>\private_study\code_map.md`, outside the repository. I'll record your answers in `<kit-root>\private_study\stage13_progress.md`. `docs/STATE.md` now shows Stage 13 as IN PROGRESS.
>
> **Section 1: the project in 60 seconds**
>
> We chose Exercises 1 and 2. Exercise 3 (POS) was left out on purpose.
>
> **Partner Monitor** (`azk_odoo_partner_monitor`, Exercise 1)
> - **Input:** the public HTML pages of www.odoo.com/partners. `services/http_client.py` downloads them with `requests`, and `services/parsers.py` reads them with BeautifulSoup.
> - **Stores:**
>   - the assessment's four models: country, partner, status history and reference;
>   - three models that run the sync: run, work item and error.
> - **Produces:** a dashboard with four charts and shared filters, list and form views, and a chatter note when a run fails or is only partly done. Four scheduled jobs drive it.
>
> **Dynamic Trial Balance** (`azk_dynamic_trial_balance`, Exercise 2)
> - **Input:** the wizard's choices, plus the journal items (`account.move.line`) the user is allowed to read.
> - **Stores:** no balances. The wizard is a TransientModel: Odoo deletes its rows automatically. Think of a Django form backed by a short-lived table.
> - **Produces:** one result from our engine (`compute` in `models/trial_balance_engine.py`). The Enterprise report framework shows that result as the Preview, the PDF and the XLSX.
>
> **How the layers fit**
> - **Community core:** the framework, like Django plus its contrib apps (the ORM, `mail`, `account`). Pinned to commit `4e5027c1`.
> - **Enterprise addons:** Odoo's proprietary apps, such as `account_reports`. Build 18.0+e.20241208, kept outside the repository.
> - **Our addons:** like your own Django apps. Each manifest declares what the addon needs:
>
> ```python
> # addons/azk_odoo_partner_monitor/__manifest__.py
> "depends": ["mail"],
> # addons/azk_dynamic_trial_balance/__manifest__.py
> "depends": ["account_reports"],
> ```
>
> **Verified limitations**
> - Enterprise is confirmed; version 18.0 is only our assumption. We tested one runtime pair on one Windows machine.
> - The live site was only read in small samples (39 requests). We never ran a full crawl, and never tested Odoo with several worker processes.
> - The views and the wizard layout are our own proposal, because the views specification and the wizard mockup were never supplied.
> - The Trial Balance covers one company per report. Filtering by analytic account counts whole journal items, not a percentage share.
>
> **Question:** Imagine a server with only the Community source and no Enterprise addons folder. What happens when you try to install each of our two addons? Which line in our code decides each outcome?

## Status at the pause

- Section 1 (the project overview) was taught in the last assistant message above, with one comprehension question. The user had not answered it when the next message paused Stage 13 and started Stage 15 (logged in `stage_15.md`, added after the submitted commit).
- Sections 2 to 7, the revision sheet, the practice list and the sandbox exercises have not started.
- No handoff is written for Stage 13 yet: it is written when the stage ends.

## Notes on accuracy

- The Stage 12 final response, as displayed at the start of this part of the session, was compared by the assembling script with the final-response section of [stage_12.md](stage_12.md): identical.
- The CLI compacted the conversation's context at the end of Stage 12. The transcript keeps every visible message, so the log is complete; the CLI's compaction summary is not a user prompt and is not reproduced.
- System notices (for example the CLI's reminders that the user had not heard from the assistant for a while) are not user prompts and are not reproduced; the short progress messages they prompted are.
- The assistant's own context also holds one earlier short progress message of this stage (it said that the code map was being built and which files had been read) that the CLI's transcript does not contain. It is not reproduced, because this log copies only recorded text.

## Summary of tool activity (summary, not verbatim)

1. **Read the instructions:** the Stage 13 prompt file and `AGENTS.md`; the Git status (clean at commit `32445f0`, tag `submission-rc1`).
2. **Inspected the final code read-only:** both manifests and `__init__.py` files; every model, service and test file's classes and functions with their line numbers; the main models' fields; the access-control files, groups, record rules, scheduled jobs, menus, actions and the report record; the worker's page source and job entry points; the engine's entry point and the wizard's buttons; the test helpers, the golden fixture TB-BASE and the walkthrough test; the README's scope, platform, features, limitations and status; `docs/architecture.md` section 0.3. The test methods were counted per file: 147 and 114.
3. **Checked by name in the pinned runtime:** the dependency chain of `account_reports` in the Enterprise manifests (module names only) and the location of `ir.cron._notify_progress` in the pinned Community source.
4. **Wrote private files outside the repository** (`<kit-root>/private_study/`): `code_map.md` (seven sections with file, function and line pointers at commit `32445f0`) and `stage13_progress.md` (the question asked, the expected answer, and the candidate's answers when given). An ASCII check found 0 non-ASCII bytes in both.
5. **Updated** `docs/STATE.md` (Stage 13 IN PROGRESS; uncommitted until the Stage 15 commit, which records the pause) and the kit's private guidance file `<kit-root>/CLAUDE.md` (where the private files are). No addon, setup or script file changed.
