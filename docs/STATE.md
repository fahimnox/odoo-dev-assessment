# Project state

_Last updated: 2026-11-05, end of the Stage 01B compatibility follow-up._

## Current position

- **Stage 01B: DONE. The compatibility blocker is resolved by the matched pair, and Stage 02 is ready.**
  - Matched pair: official `odoo/odoo` `4e5027c159a9d9a8dd006618486c8e54cb1eb453` (fetched from GitHub; 21,846 files verified identical) with the 620 Enterprise-repository modules of build 18.0+e.20241208.
  - It runs as edition `enterprise-20241208` (service `odoo-ee-20241208`, databases `azk_ee24*`, port 8071), which is the default in `.env`.
  - On fresh databases: all eight `TestTrialBalanceReport` tests passed, including `test_trial_balance_comparisons`; the custom addon tests passed 4 of 4; and the login, Trial Balance, PDF and XLSX smoke checks passed.
  - Details in [enterprise_transition.md](enterprise_transition.md#follow-up-continuation-2026-11-05).
- **Next stage:** 02 - requirements, assumptions, architecture and acceptance plan, on edition `enterprise-20241208`.
- **Browser checks:** the user reported a browser smoke check of the Stage 01B environment (port 8070) in the 2026-11-04 message, without detailed results. No browser check of the matched-pair environment (port 8071) has been done yet; the agent has no browser here. It was not part of the agreed checks, but is recommended (steps in [enterprise_transition.md](enterprise_transition.md)).
- **Business features implemented:** none. Both addons are installable skeletons with smoke tests.
- **Target:** Odoo Enterprise (confirmed, A-08); major version 18.0 (provisional, A-09).
- **Tests run on 2026-11-03:**
  - Enterprise: `scripts/dev.sh test`, 4 tests, 0 failed, 0 errors.
  - Community baseline: `ODOO_EDITION=community scripts/dev.sh test`, 4 tests, 0 failed, 0 errors.
  - Vendor `account_reports` Trial Balance class on our runtime: 7 of 8 passed (one known incompatibility); the same class on the archive's matched 2024 build: 8 of 8. The full vendor suite was NOT RUN: it was stopped because drive C: was nearly full.
- **Checks run on 2026-11-04 (follow-up):** read-only content verification against official GitHub trees, not tests. `odoo/odoo@4e5027c1`: 36,514 of 37,496 files identical, 10 explained differences. `design-themes@3057d466`: 4,266 of 4,268 identical. No server, database or test run.
- **Checks run on 2026-11-05 (continuation, matched pair, fresh databases):**
  - source verification: 21,846 of 21,846 files identical;
  - `TestTrialBalanceReport`: 8 of 8;
  - custom addon tests: 4 of 4;
  - `azk_ee24` setup: 92 modules, 0 warnings;
  - shell, HTTP, PDF and XLSX smoke checks: PASS;
  - server log: 0 warnings.
  - Both test commands were rerun on the final configuration after removing a redundant mount.

## Stage status

| Stage | Title | Status |
|---|---|---|
| 00 | Operating contract | DONE |
| 01 | Environment (Community baseline) | DONE |
| 01B | Enterprise transition | DONE (2026-11-05): matched pair validated; the Stage 01B pair stays blocked and preserved |
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
- Odoo Enterprise is the target (A-08, clarification C-01 dated 2026-11-03). Odoo 18.0 is provisional (A-09). Justified Enterprise dependencies such as `account_reports` are allowed and must be declared; the native Trial Balance is a baseline, not proof that the assessment is met.
- **Enterprise runtime (A-12):** the matched pair as edition `enterprise-20241208`: service `odoo-ee-20241208` serving `azk_ee24` on 127.0.0.1:8071, with the official Community source `odoo/odoo@4e5027c1` mounted over the pinned image's package and the 620 Enterprise modules of build 18.0+e.20241208. See [environment.md](environment.md) and [enterprise_transition.md](enterprise_transition.md).
- The Stage 01B pair (A-10: the 2026 core with the same Enterprise addons, service `odoo-ee`, `azk_ent`, port 8070) is blocked by the vendor test failure and kept only as preserved evidence. The Community baseline (`odoo`, `azk_dev`, 8069) is kept for comparison.
- Each database belongs to one edition by prefix (`azk_ent*`, `azk_ee24*`, otherwise Community), and `scripts/dev.sh` refuses the others. So no older core ever opens `azk_ent`, which the 2026 core initialized.
- `scripts/dev.sh` selects the edition with `ODOO_EDITION` (`enterprise-20241208` in this workspace's `.env`).
- The Enterprise source stays private, outside this repository: a curated copy in `<kit-root>/runtime/enterprise/18.0-20241208/`, pinned by a tree digest. It is referenced by names only, never copied or quoted. The official Community source is in `<kit-root>/runtime/community/18.0-4e5027c1/`, also outside the repository and pinned.
- This repository holds the solution only. The assessment PDF and prompt kit live in the parent kit directory and are never committed.
- English only for terminal output, new documentation, code comments and commit messages (AGENTS.md rule 7, set by correction R0). Each stage also writes an English handoff to [handoffs/](handoffs/) (AGENTS.md rule 9).
- Databases: `azk_ee24` (Enterprise development on the matched pair, demo data), `azk_ee24_test` and `azk_ee24_clean` (disposable); `azk_ent` (Stage 01B pair, preserved, blocked), `azk_ent_test` and `azk_ent_clean`; `azk_dev` (Community development), `azk_test` and `azk_clean` (disposable). See [environment.md](environment.md) and A-04 to A-07.

## Corrections applied

- **R0, 2026-11-01:** switched the project from Egyptian Arabic explanations to English-only output. AGENTS.md rules 7 and 9 now match the revised kit, the Stage 00 English handoff is in [handoffs/stage_00_en.md](handoffs/stage_00_en.md), and [ai/README.md](ai/README.md) records the change. The kit-root CLAUDE.md (outside this repository) was aligned as well. No scope, requirement or completion status changed, and the historical Stage 00 transcript is unchanged.
- **Stage 01B, 2026-11-03:** Enterprise replaced the Community assumption. AGENTS.md has a dated clarification, and the kit-root CLAUDE.md was aligned. The Stage 00 and 01 transcripts are unchanged; Stage 01 results remain baseline evidence.

## Missing inputs

The original views specification (M-01), the Trial Balance mockup (M-02) and the `azk_zkteco_machine_proxy` documentation example (M-03) were not supplied and have not been read. The company-supplied archive contains only a byte-identical copy of the assessment PDF, nothing more. Details in [assumptions.md](assumptions.md).

## Open items

- **Disk space:** resolved by the user before the 2026-11-05 continuation. C: had 17 to 19 GB free during the work. Keep several GB free before long test runs (see [environment.md](environment.md)).
- **Compatibility blocker:** resolved on 2026-11-05 for the matched pair (all eight `TestTrialBalanceReport` tests pass). The Stage 01B pair still fails `test_trial_balance_comparisons` and stays blocked; it is kept only for `azk_ent`.
- **Browser check (user, recommended):** the user reported a browser check of the Stage 01B environment (no detailed results given). The matched-pair environment on port 8071 has not been checked in a browser yet; steps are in [enterprise_transition.md](enterprise_transition.md).
- **Enterprise source verification:** the Enterprise files cannot be checked against an official baseline without access to the private repository. Only the tarball's file list and timestamps support them.
- **Matched Enterprise build for the 2026 core:** question Q-05 for the team lead. It would be an alternative to the 2024 pair.
- **Extracted archive:** no runtime needs `<kit-root>/odoo/odoo18`: the matched pair uses the official Community source and the 620-module Enterprise copy. Deleting it (1.76 GB) is the user's decision, and only sensible if the original archive file is kept elsewhere.
- **Decision for the user:** the supplied archive contains an earlier implementation of this assessment's modules (`projects/assessment/`, not opened or used). Whether to mention it to the team lead is the user's decision.
- **Subscription:** `azk_ee24` and `azk_ent` are unregistered trials; registering needs the employer's subscription code.
- Clarifications Q-02 to Q-05 for the team lead are drafted in [assumptions.md](assumptions.md) and not yet asked.
- Ambiguities D-01 to D-07 are to be resolved in Stage 02; D-01, D-04 and D-07 now carry observations from the native Trial Balance.
- Manifest author `fahimnox` and license LGPL-3 are unconfirmed defaults (A-06).
- Commits use the global Git identity `fahimnox <mohamed.fahim@noxholding.com>`, which becomes public in Stage 15 unless the user decides otherwise.
- Not exercised: `scripts/dev.sh source` itself (an equivalent command made the source copy).

## Host facts

Inspected in Stage 01 and rechecked in Stage 01B; details in [environment.md](environment.md).

- Windows 11 Pro 10.0.26200, Intel Core i7-8650U (4 cores, 8 threads), 15.9 GB RAM. Drive C: had 18.0 GB free before Stage 01, 10.2 GB after it, 7.9 GB at the start of Stage 01B (after the archive had been extracted) and 2.0 GB at its end. The files and databases created in Stage 01B account for about 0.65 GB. The rest is not attributed: Docker's virtual disk (shared with the other running project, size at the start of the stage unknown) grew during the install and test runs, and other Windows activity may also contribute.
- The agent works through Git Bash (installed per user under `%LOCALAPPDATA%\Programs\Git`) and PowerShell. In PowerShell, `bash` starts WSL, not Git Bash.
- Docker Desktop 29.4.0 with Compose v5.1.1 (WSL2 backend). Another project (ots-local) uses 127.0.0.1 ports 5433, 8000 and 9000; ports 8069 and 8070 were free. On this host Docker Desktop creates missing bind-mount folders even with `create_host_path: false`.
- A host PostgreSQL 18 service listens on port 5432; this project does not use it.
- Host `python` 3.12.0, `git` 2.53.0.windows.2 and `pdftotext` are available. wkhtmltopdf is not installed on the host; the Odoo image provides it.
