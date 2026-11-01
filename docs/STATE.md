# Project state

_Last updated: 2026-11-01, end of Stage 00._

## Current position

- **Last completed stage:** 00 — operating contract, workspace and state files.
- **Next stage:** 01 — build and verify the local development environment.
- **Business features implemented:** none.
- **Tests run:** none (Stage 00 has no code to test).

## Stage status

| Stage | Title | Status |
|---|---|---|
| 00 | Operating contract | DONE |
| 01 | Environment | NOT STARTED |
| 02 | Requirements, assumptions, architecture | NOT STARTED |
| 03 | Partner Monitor models, permissions, basic UI | NOT STARTED |
| 04 | Partner scraping | NOT STARTED |
| 05 | Partner resilience | NOT STARTED |
| 06 | Partner dashboard | NOT STARTED |
| 07 | Trial Balance wizard and calculation contract | NOT STARTED |
| 08 | Trial Balance calculation engine | NOT STARTED |
| 09 | Trial Balance outputs (Preview, PDF, XLSX) | NOT STARTED |
| 10 | Engineering review | NOT STARTED |
| 11 | Clean acceptance | NOT STARTED |
| 12 | Submission documentation | NOT STARTED |
| 13 | Code walkthrough | NOT STARTED |
| 14 | Mock interview | NOT STARTED |
| 15 | Publish | NOT STARTED |

## Decisions in force

- Exercises 1 (`azk_odoo_partner_monitor`) and 2 (`azk_dynamic_trial_balance`); Exercise 3 out of scope. See [assumptions.md](assumptions.md) A-01, A-03.
- Odoo 18 Community, unconfirmed by the assessor (A-02).
- This repository holds the solution only. The assessment PDF and prompt kit live in the parent kit directory and are never committed.

## Missing inputs

The original views specification (M-01), the Trial Balance mockup (M-02) and the `azk_zkteco_machine_proxy` documentation example (M-03) were not supplied and have not been read. Details in [assumptions.md](assumptions.md).

## Open items

- Clarifications Q-01 to Q-03 for the team lead are drafted in [assumptions.md](assumptions.md) and not yet asked.
- Ambiguities D-01 to D-07 are to be resolved in Stage 02.

## Host facts observed so far

Observed during Stage 00 and the earlier `/init` session; Stage 01 performs the full inspection.

- Windows 11 Pro 10.0.26200; the agent runs through Git Bash and PowerShell.
- `git` 2.53.0.windows.2; host `python` 3.12.0; `pdftotext` available in Git Bash.
- Not yet checked: Docker/WSL, PostgreSQL, wkhtmltopdf, RAM/disk.
