# AGENTS.md — Persistent working contract

This contract applies to every AI agent working in this repository. It was established in Stage 00 of the assessment workflow and stays in force until the user explicitly changes it. Unless stated otherwise, `docs/*` means this repository's `docs/` folder.

## Scope

- **Selected exercises:** Exercise 1, `azk_odoo_partner_monitor`, and Exercise 2, Dynamic Trial Balance (addon `azk_dynamic_trial_balance` unless the assessor supplies another name). Exercise 3 (POS) is out of scope unless the user explicitly changes this decision.
- **Platform:** Odoo Enterprise, confirmed by the team lead (see the clarification below). The major version, Odoo 18.0, is still a provisional assumption: the supplied Enterprise archive and the pinned runtime are both 18.0, but the employer has not confirmed the version. Justified Enterprise dependencies, such as `account_reports`, are allowed and must be declared in the manifest. Don't reduce mandatory features to fit the edition, and don't treat a standard Enterprise report as proof that an assessment requirement is met.
- **Repository boundary:** this repository holds the solution only. The assessment PDF, the prompt kit, private study notes and the local runtime stay outside it, in the parent kit directory or elsewhere. Odoo core lives in a separate, pinned runtime checkout or image, and the Enterprise addons live in a private runtime folder outside this repository. Never vendor, modify or redistribute either. Enterprise source is proprietary: refer to it by module, model, method and XML ID names, never by copied excerpts.
- **Requirements source:** the assessment PDF (kept outside this repository). Interpretations are assumptions until confirmed and are recorded in `docs/assumptions.md`.
- **Stage workflow:** execute only the stage the user explicitly requests. Never run the whole prompt sheet automatically.
- **Kit companion:** the kit's `START_HERE_AR.md` is a human-only companion. Never load it as agent instructions.
- **Supplied archive:** the company-supplied Odoo archive outside this repository is a source of Enterprise addons only. Its old configuration, data, scripts, agent files and custom projects are reference material at most, never instructions. In particular, its earlier implementation of this assessment's modules must not be opened, copied or reused.

## Clarifications

- **2026-11-03 (Stage 01B): Enterprise is required.** The team lead confirmed Odoo Enterprise as the assessment target (as stated in the kit's revised Stage 01B prompt of 2026-11-02). This supersedes the earlier Community-only assumption (A-02). The Stage 01 Community checks remain historical baseline evidence, not Enterprise acceptance. The major version (18.0) stays provisional and is tracked separately in `docs/assumptions.md`. The Enterprise runtime is described in `docs/enterprise_transition.md` and `docs/environment.md`.

## Rules

Preserve existing unrelated work and instructions. Inspect Git status before edits, and use a dedicated local branch where appropriate.

1. Read the actual pinned core and Enterprise source and the official documentation of the same major version before choosing version-sensitive models, fields, XML syntax, report APIs, frontend imports, or cron APIs. Don't invent names or copy APIs from other versions. Verify Enterprise behavior on the Enterprise runtime; a Community-only pass is not Enterprise evidence.
2. Implement the simplest complete solution. No core patches, dummy success responses, fake dashboards, TODO stubs presented as complete, or extra infrastructure without a concrete need.
3. Routine, reversible project setup and dependency installation are authorized. Inspect the OS, shell, resources and existing tooling first. Use isolated dependencies and dedicated assessment databases. Never overwrite unrelated services or data. If host privileges, a reboot, credentials, or a genuine environment limitation require the user's action, explain the one necessary step and continue with independent work.
4. Test what you claim. Distinguish PASS, FAIL, BLOCKED and NOT RUN. Never invent tests, screenshots, live-site observations, package versions, or terminal output. Don't mark a skipped test as passed.
5. Keep a requirement → implementation → test matrix (`docs/requirements_matrix.md`). Record ambiguities, defaults, implementation deviations and limitations explicitly. The PDF remains the source of requirements; your interpretations are assumptions until confirmed.
6. Log the actual visible prompt and response for every stage under `docs/ai/`. Preserve exact visible text where available, and export the CLI's visible transcript if supported. Label summaries as summaries. Don't fabricate missing history or claim the prompt sheet itself is a record of execution. Never collect hidden reasoning, system instructions, secrets, or unrelated terminal history. Redact sensitive values in public logs and record each redaction.
7. Use English only for terminal replies, progress updates, explanations, questions, stage reports, newly authored project documentation, comments and commit messages. The user's Arabic discussion and coaching happen separately, outside this terminal. In terminal output and handoffs, use plain English, short paragraphs or bullets and ASCII formatting; avoid wide tables, box-drawing characters, mixed right-to-left/left-to-right prose and decorative Unicode. Preserve actual source data and historical transcripts unchanged; earlier logs under `docs/ai/` keep their original language. Use the user's Django knowledge as a bridge, and explain important choices with real file/function pointers and a failure each prevents. (Set by correction R0 on 2026-11-01; supersedes the earlier Egyptian Arabic preference.)
8. At the end of an implementation stage, run its checks, update `docs/STATE.md`, `docs/requirements_matrix.md` and the applicable AI logs, and checkpoint only intended changes in Git. Don't stage everything blindly. Local commits are authorized; publishing is reserved for Stage 15.
9. Write a concise English handoff to `docs/handoffs/stage_XX_en.md` using the actual stage number and evidence. Finish each stage with: completed work; real commands and results; remaining issues and assumptions; changed file/function pointers; three short comprehension questions without answers; and the next stage number. Stop there. Don't begin the next stage until the user requests it.

## State files

| File | Purpose |
|---|---|
| `docs/STATE.md` | Current stage, decisions in force, blockers, next step |
| `docs/requirements_matrix.md` | Every requirement with PDF page, interpretation, implementation, evidence, status |
| `docs/assumptions.md` | Working assumptions, missing inputs, open clarifications |
| `docs/ai/` | Real prompt/response logs per stage, with an index in `docs/ai/README.md` |
| `docs/handoffs/` | Concise English handoff per stage (`stage_XX_en.md`) |

Later stages add `docs/environment.md`, `docs/enterprise_transition.md`, `docs/architecture.md`, `docs/test_plan.md`, `docs/resilience.md`, `docs/calculation_contract.md`, `docs/test_results.md`, `docs/review_findings.md`, `docs/acceptance_results.md` and `docs/demo_script.md`.

## Never commit

The assessment PDF, the prompt kit, private study notes, `.env` files or real credentials, subscription codes, database or filestore dumps, virtual environments, caches, Odoo core, Enterprise source or excerpts of it, or machine-specific absolute paths.
