# Project state

_Last updated: 2026-11-01, end of Stage 01, including the follow-up checks._

## Current position

- **Last completed stage:** 01 - local development environment (Docker Compose with pinned Odoo 18 and PostgreSQL 16 images).
- **Next stage:** 02 - requirements, assumptions, architecture and acceptance plan.
- **Business features implemented:** none. Both addons exist as installable skeletons with smoke tests.
- **Tests run:** `scripts/dev.sh test` on 2026-11-01: 4 tests, 0 failed, 0 errors. A deliberately failing test made the command exit with 1, and the user's browser check of login and the Apps list passed. Details in [environment.md](environment.md).

## Stage status

| Stage | Title | Status |
|---|---|---|
| 00 | Operating contract | DONE |
| 01 | Environment | DONE |
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
- English only for terminal output, new documentation, code comments and commit messages (AGENTS.md rule 7, set by correction R0). Each stage also writes an English handoff to [handoffs/](handoffs/) (AGENTS.md rule 9).
- Development environment: Docker Compose with pinned images, run through `scripts/dev.sh`, with three databases: `azk_dev` (development, demo data), `azk_test` and `azk_clean` (both disposable). See [environment.md](environment.md) and A-04 to A-07.

## Corrections applied

- **R0, 2026-11-01:** switched the project from Egyptian Arabic explanations to English-only output. AGENTS.md rules 7 and 9 now match the revised kit, the Stage 00 English handoff is in [handoffs/stage_00_en.md](handoffs/stage_00_en.md), and [ai/README.md](ai/README.md) records the change. The kit-root CLAUDE.md (outside this repository) was aligned as well. No scope, requirement or completion status changed, and the historical Stage 00 transcript is unchanged.

## Missing inputs

The original views specification (M-01), the Trial Balance mockup (M-02) and the `azk_zkteco_machine_proxy` documentation example (M-03) were not supplied and have not been read. Details in [assumptions.md](assumptions.md).

## Open items

- Clarifications Q-01 to Q-03 for the team lead are drafted in [assumptions.md](assumptions.md) and not yet asked.
- Ambiguities D-01 to D-07 are to be resolved in Stage 02.
- Manifest author `fahimnox` and license LGPL-3 are unconfirmed defaults (A-06).
- Commits use the global Git identity `fahimnox <mohamed.fahim@noxholding.com>`, which becomes public in Stage 15 unless the user decides otherwise.
- Not exercised: `scripts/dev.sh source` itself (an equivalent command made the source copy).

## Host facts

Inspected in Stage 01; details in [environment.md](environment.md).

- Windows 11 Pro 10.0.26200, Intel Core i7-8650U (4 cores, 8 threads), 15.9 GB RAM. Drive C: had 18.0 GB free before Stage 01 and 10.2 GB after.
- The agent works through Git Bash (installed per user under `%LOCALAPPDATA%\Programs\Git`) and PowerShell. In PowerShell, `bash` starts WSL, not Git Bash.
- Docker Desktop 29.4.0 with Compose v5.1.1 (WSL2 backend) was already running. Another project (ots-local) uses 127.0.0.1 ports 5433, 8000 and 9000.
- A host PostgreSQL 18 service listens on port 5432; this project does not use it.
- Host `python` 3.12.0, `git` 2.53.0.windows.2 and `pdftotext` are available. wkhtmltopdf is not installed on the host; the Odoo image provides it.
