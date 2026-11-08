# Project state

_Last updated: 2026-11-08, end of Stage 03._

## Current position

- **Stage 03: DONE (2026-11-08).** `azk_odoo_partner_monitor` 18.0.1.1.0 has its data model, access rules, basic UI and demo data; no scraping yet.
  - Models: the four PDF models with their exact fields, plus `sync.run` (with chatter), `work.item` and `sync.error`. The observation API (`country._record_observation`, `partner._record_observation`, `partner._sync_references`) enforces the Stage 03 invariants; the Stage 05 worker will call it.
  - Access: Reader and Manager groups with read-only ACLs; four manager actions with an explicit group check and a narrow `sudo()` (D-18); no record rules, because the data is shared across companies (A-21); Settings for system administrators.
  - UI: list, form and search views for every model, Settings (failure recipient) and menus. Menu path to a partner: Partner Monitor > Partners, then click the partner.
  - Demo: 4 countries, 6 partners, 10 status events and 6 references, all labeled demo (D-20).
  - Design changes are in [architecture.md](architecture.md) 5.10 and decisions D-18 to D-22 in [assumptions.md](assumptions.md).
- **Stage 03 checks** (edition `enterprise-20241208`, port 8071):
  - `scripts/dev.sh test azk_odoo_partner_monitor`: PASS, 0 failed, 0 errors of 53 tests, in a fresh `azk_ee24_test` with demo data; the whole log had 0 warnings (6 min 26 s). The first run found two bugs, fixed before this result (see [ai/README.md](ai/README.md)).
  - `scripts/dev.sh update azk_odoo_partner_monitor` on `azk_ee24`, twice: PASS, 0 warnings or errors each time (3 min 16 s, then 2 min 45 s); no duplicated demo records.
  - Read-only shell check of `azk_ee24`: version 18.0.1.1.0, the demo counts above, the 3 partial unique indexes and 14 check and unique constraints present, the failure recipient set to the admin (whose notification preference is email).
  - HTTP check on 8071 as admin: login, partner search, list/form/search views and the 11 Partner Monitor menus: PASS.
  - NOT RUN: browser check (no browser available to the agent).
- **Stage 02: DONE (2026-11-05).** Requirements, assumptions, architecture and the test plan are agreed on paper; no feature code was written.
  - [requirements_matrix.md](requirements_matrix.md): every selected requirement (fields, options, help texts and charts) with its interpretation, planned location, planned test and status (mostly DESIGNED).
  - [architecture.md](architecture.md): components, security boundary, the Partner Monitor sync design, the Trial Balance calculation contract, and the native Trial Balance probe.
  - [assumptions.md](assumptions.md): D-01 to D-07 resolved, new decisions D-08 to D-17, version notes V-01 to V-07, open questions Q-02 to Q-06.
  - [test_plan.md](test_plan.md): test IDs TP-PM-01 to 21, TP-TB-01 to 17 and TP-G-01 to 05, with hand-calculated Trial Balance expectations.
- **Stage 02 checks** (read-only, on the matched pair):
  - the version-sensitive APIs were read in the pinned core and Enterprise sources;
  - the disposable database `azk_ee24_clean` was created with `accountant` (90 modules, 0 warnings, 0 errors, 5 min 20 s);
  - a native Trial Balance probe ran there with eight option sets and was rolled back (PASS: the conventions were observed and recorded).
  - No addon tests ran, because no addon code changed.
- **Stage 01B: DONE (2026-11-05).** The compatibility blocker is resolved by the matched pair.
  - Matched pair: official `odoo/odoo` `4e5027c159a9d9a8dd006618486c8e54cb1eb453` (fetched from GitHub; 21,846 files verified identical) with the 620 Enterprise-repository modules of build 18.0+e.20241208.
  - It runs as edition `enterprise-20241208` (service `odoo-ee-20241208`, databases `azk_ee24*`, port 8071), which is the default in `.env`.
  - Results on fresh databases:
    - all eight `TestTrialBalanceReport` tests passed, including `test_trial_balance_comparisons`;
    - the custom addon tests passed 4 of 4;
    - the login, Trial Balance, PDF and XLSX smoke checks passed.
  - Details in [enterprise_transition.md](enterprise_transition.md#follow-up-continuation-2026-11-05).
- **Next stage:** 04 - Partner scraping (fetch and parse layers), on edition `enterprise-20241208`.
- **Browser checks:** the user reported a browser smoke check of the Stage 01B environment (port 8070) in the 2026-11-04 message, without detailed results. No browser check of the matched-pair environment (port 8071) has been done yet; the agent has no browser here. It is recommended (steps in [enterprise_transition.md](enterprise_transition.md)).
- **Business features implemented:** the Partner Monitor data model, access rules, basic views and demo data (Stage 03). No scraping, sync jobs or dashboard yet. The Trial Balance addon is still an installable skeleton with smoke tests.
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
| 02 | Requirements, assumptions, architecture | DONE (2026-11-05): design agreed; native Trial Balance probed on the matched pair |
| 03 | Partner Monitor models, permissions, basic UI | DONE (2026-11-08): 53 tests pass; installs and upgrades without warnings |
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
- Databases: `azk_ee24` (Enterprise development on the matched pair, demo data), `azk_ee24_test` and `azk_ee24_clean` (disposable; since Stage 02 `azk_ee24_clean` holds `accountant` with demo data, used for the native probe); `azk_ent` (Stage 01B pair, preserved, blocked), `azk_ent_test` and `azk_ent_clean`; `azk_dev` (Community development), `azk_test` and `azk_clean` (disposable). See [environment.md](environment.md) and A-04 to A-07.
- **Stage 02 design** ([architecture.md](architecture.md)):
  - **Trial Balance:**
    - our own engine inside our own `account.report` record and custom handler;
    - native preview, PDF and XLSX consume one normalized result (A-13);
    - native opening, carry-forward and netting conventions (A-14) and native whole-item analytic filtering (A-15);
    - Many2one journal and analytic account (D-02); one authorized company and Date From/To (D-03);
    - the Amount Currency column shows the period movement per transaction currency (D-11).
  - **Partner Monitor:**
    - stable source keys with database uniqueness;
    - removals only after complete, validated snapshots;
    - durable work items processed by one worker cron in bounded batches, using the 18.0 progress API and scheduler commits (A-18);
    - row-lock claims;
    - a failure note on the run's chatter to the configured user (D-08);
    - the dashboard as a small OWL client action embedding four XML graph views with shared filters (A-17).
  - The manifest dependency change to `account_reports` happens in Stage 07, not in Stage 02.
- **Stage 03 decisions** ([assumptions.md](assumptions.md)):
  - D-18: nobody edits scraped data, history or checkpoints through access rules; managers use four checked actions;
  - D-19: the default failure recipient is the administrator, because install hooks run as the superuser;
  - D-20: demo records are labeled and use reserved website ids;
  - D-21: an observation older than the last one is ignored;
  - D-22: `total_references_count` also has a known flag, and unknown measurements carry no number.

## Corrections applied

- **R0, 2026-11-01:** switched the project from Egyptian Arabic explanations to English-only output. AGENTS.md rules 7 and 9 now match the revised kit, the Stage 00 English handoff is in [handoffs/stage_00_en.md](handoffs/stage_00_en.md), and [ai/README.md](ai/README.md) records the change. The kit-root CLAUDE.md (outside this repository) was aligned as well. No scope, requirement or completion status changed, and the historical Stage 00 transcript is unchanged.
- **Stage 01B, 2026-11-03:** Enterprise replaced the Community assumption. AGENTS.md has a dated clarification, and the kit-root CLAUDE.md was aligned. The Stage 00 and 01 transcripts are unchanged; Stage 01 results remain baseline evidence.

## Missing inputs

The original views specification (M-01), the Trial Balance mockup (M-02) and the `azk_zkteco_machine_proxy` documentation example (M-03) were not supplied and have not been read. The company-supplied archive contains only a byte-identical copy of the assessment PDF, nothing more. Details in [assumptions.md](assumptions.md).

## Open items

- **Disk space:** resolved by the user before the 2026-11-05 continuation. C: had 17 to 19 GB free during that work, and 13 GB during Stage 02. The drop happened between the two sessions and was not investigated. On 2026-11-08, C: had 14 GB free before Stage 03's two test runs and 9.7 GB after them. Docker's virtual disk (`docker_data.vhdx`, shared with another project) was 14.6 GB on 2026-11-03 and 15.4 GB after the runs, so it explains at most 0.8 GB of the drop; the rest is not attributed. Keep several GB free before long test runs (see [environment.md](environment.md)).
- **After a machine restart:** the Compose services use `restart: "no"`, so `scripts/dev.sh start` is needed once Docker Desktop is up (found on 2026-11-08, after the restart of 2026-11-06).
- **Browser check of the Partner Monitor UI (user, recommended):** log in at http://127.0.0.1:8071 (admin), open Partner Monitor > Partners and a demo partner, and Settings > Partner Monitor. Not run by the agent (no browser).
- **Compatibility blocker:** resolved on 2026-11-05 for the matched pair (all eight `TestTrialBalanceReport` tests pass). The Stage 01B pair still fails `test_trial_balance_comparisons` and stays blocked; it is kept only for `azk_ent`.
- **Browser check (user, recommended):** the user reported a browser check of the Stage 01B environment (no detailed results given). The matched-pair environment on port 8071 has not been checked in a browser yet; steps are in [enterprise_transition.md](enterprise_transition.md).
- **Enterprise source verification:** the Enterprise files cannot be checked against an official baseline without access to the private repository. Only the tarball's file list and timestamps support them.
- **Matched Enterprise build for the 2026 core:** question Q-05 for the team lead. It would be an alternative to the 2024 pair.
- **Extracted archive:** no runtime needs `<kit-root>/odoo/odoo18`: the matched pair uses the official Community source and the 620-module Enterprise copy. Deleting it (1.76 GB) is the user's decision, and only sensible if the original archive file is kept elsewhere.
- **Decision for the user:** the supplied archive contains an earlier implementation of this assessment's modules (`projects/assessment/`, not opened or used). Whether to mention it to the team lead is the user's decision.
- **Subscription:** `azk_ee24` and `azk_ent` are unregistered trials; registering needs the employer's subscription code.
- Clarifications Q-02 to Q-06 for the team lead are drafted in [assumptions.md](assumptions.md) and not yet asked. None blocks Stage 04.
- Ambiguities D-01 to D-07 were resolved in Stage 02, and D-08 to D-17 were added and decided ([assumptions.md](assumptions.md)).
- **Verification still ahead:**
  - The live partners site is modeled on the 18.0 `website_crm_partner_assign` module (A-19) until Stage 04 checks a small live sample.
  - The `account_reports` display and export hooks are known by name; their exact mechanics (column groups, the PDF header template, the preview filter component) are verified in Stages 08-09, with the fallback documented in [architecture.md](architecture.md) 4.7.
- Manifest author `fahimnox` and license LGPL-3 are unconfirmed defaults (A-06). The license of `azk_dynamic_trial_balance`, which will depend on the OEEL-1 module `account_reports`, is question Q-06.
- Commits use the global Git identity `fahimnox <mohamed.fahim@noxholding.com>`, which becomes public in Stage 15 unless the user decides otherwise.
- Not exercised: `scripts/dev.sh source` itself (an equivalent command made the source copy).

## Host facts

Inspected in Stage 01 and rechecked in Stage 01B; details in [environment.md](environment.md).

- Windows 11 Pro 10.0.26200, Intel Core i7-8650U (4 cores, 8 threads), 15.9 GB RAM. Drive C: had 18.0 GB free before Stage 01, 10.2 GB after it, 7.9 GB at the start of Stage 01B (after the archive had been extracted) and 2.0 GB at its end. The files and databases created in Stage 01B account for about 0.65 GB. The rest is not attributed: Docker's virtual disk (shared with the other running project, size at the start of the stage unknown) grew during the install and test runs, and other Windows activity may also contribute.
- The agent works through Git Bash (installed per user under `%LOCALAPPDATA%\Programs\Git`) and PowerShell. In PowerShell, `bash` starts WSL, not Git Bash.
- Docker Desktop 29.4.0 with Compose v5.1.1 (WSL2 backend). Another project (ots-local) uses 127.0.0.1 ports 5433, 8000 and 9000; ports 8069 and 8070 were free. On this host Docker Desktop creates missing bind-mount folders even with `create_host_path: false`.
- A host PostgreSQL 18 service listens on port 5432; this project does not use it.
- Host `python` 3.12.0, `git` 2.53.0.windows.2 and `pdftotext` are available. wkhtmltopdf is not installed on the host; the Odoo image provides it.
