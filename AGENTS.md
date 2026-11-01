# AGENTS.md — Persistent working contract

This contract applies to every AI agent working in this repository. It was established in Stage 00 of the assessment workflow and stays in force until the user explicitly changes it. Unless stated otherwise, `docs/*` means this repository's `docs/` folder.

## Scope

- **Selected exercises:** Exercise 1, `azk_odoo_partner_monitor`, and Exercise 2, Dynamic Trial Balance (addon `azk_dynamic_trial_balance` unless the assessor supplies another name). Exercise 3 (POS) is out of scope unless the user explicitly changes this decision.
- **Platform:** Odoo 18 Community. This is a documented working assumption, not an employer-confirmed requirement. Check any clarification the user provides before proceeding. Implement both exercises fully within this edition. Don't silently depend on Enterprise-only modules, and don't reduce mandatory features to fit the edition.
- **Repository boundary:** this repository holds the solution only. The assessment PDF, the prompt kit, private study notes and the local runtime stay outside it, in the parent kit directory or elsewhere. Odoo core lives in a separate, pinned runtime checkout or image. Never vendor or modify it.
- **Requirements source:** the assessment PDF (kept outside this repository). Interpretations are assumptions until confirmed and are recorded in `docs/assumptions.md`.
- **Stage workflow:** execute only the stage the user explicitly requests. Never run the whole prompt sheet automatically.

## Rules

Preserve existing unrelated work and instructions. Inspect Git status before edits, and use a dedicated local branch where appropriate.

1. Read the actual pinned Odoo 18 source and the official documentation before choosing version-sensitive models, fields, XML syntax, report APIs, frontend imports, or cron APIs. Don't invent names or copy APIs from other versions.
2. Implement the simplest complete solution. No core patches, dummy success responses, fake dashboards, TODO stubs presented as complete, or extra infrastructure without a concrete need.
3. Routine, reversible project setup and dependency installation are authorized. Inspect the OS, shell, resources and existing tooling first. Use isolated dependencies and dedicated assessment databases. Never overwrite unrelated services or data. If host privileges, a reboot, credentials, or a genuine environment limitation require the user's action, explain the one necessary step and continue with independent work.
4. Test what you claim. Distinguish PASS, FAIL, BLOCKED and NOT RUN. Never invent tests, screenshots, live-site observations, package versions, or terminal output. Don't mark a skipped test as passed.
5. Keep a requirement → implementation → test matrix (`docs/requirements_matrix.md`). Record ambiguities, defaults, implementation deviations and limitations explicitly. The PDF remains the source of requirements; your interpretations are assumptions until confirmed.
6. Log the actual visible prompt and response for every stage under `docs/ai/`. Preserve exact visible text where available, and export the CLI's visible transcript if supported. Label summaries as summaries. Don't fabricate missing history or claim the prompt sheet itself is a record of execution. Never collect hidden reasoning, system instructions, secrets, or unrelated terminal history. Redact sensitive values in public logs and record each redaction.
7. Explain in Egyptian Arabic, and keep code and repository documentation in English. (Verbatim AI transcripts under `docs/ai/` keep their original language.) Use the user's Django knowledge as a bridge. Explain the reason for each important design choice with a real file/function and a failure it prevents.
8. At the end of an implementation stage, run its checks, update `docs/STATE.md`, `docs/requirements_matrix.md` and the applicable AI logs, and checkpoint only intended changes in Git. Don't stage everything blindly. Local commits are authorized; publishing is reserved for Stage 15.
9. Finish each stage with: completed work; real commands and results; remaining issues and assumptions; changed file/function pointers; three short comprehension questions without answers; and the next stage number. Stop there. Don't begin the next stage until the user requests it.

## State files

| File | Purpose |
|---|---|
| `docs/STATE.md` | Current stage, decisions in force, blockers, next step |
| `docs/requirements_matrix.md` | Every requirement with PDF page, interpretation, implementation, evidence, status |
| `docs/assumptions.md` | Working assumptions, missing inputs, open clarifications |
| `docs/ai/` | Real prompt/response logs per stage, with an index in `docs/ai/README.md` |

Later stages add `docs/environment.md`, `docs/architecture.md`, `docs/test_plan.md`, `docs/resilience.md`, `docs/calculation_contract.md`, `docs/test_results.md`, `docs/review_findings.md`, `docs/acceptance_results.md` and `docs/demo_script.md`.

## Never commit

The assessment PDF, the prompt kit, private study notes, `.env` files or real credentials, database or filestore dumps, virtual environments, caches, Odoo core, or machine-specific absolute paths.
