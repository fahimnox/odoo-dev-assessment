# Stage 01 - Build and verify the local development environment

- **Date:** 2026-11-01
- **Tool / model:** Claude Code, Opus 5.5 (`claude-opus-5-5`)
- **Working directory:** the assessment kit root (`<kit-root>`) and `<kit-root>/solution`
- **Commit:** this log is part of the Stage 01 commit

**Transcription method:** see [README.md](README.md). User text, the referenced instruction file and the assistant's visible messages are verbatim. Tool activity is a labeled summary. Values from `.env` were never printed; only key names and lengths were checked.

## User prompt (verbatim)

```text
Read prompts/01_environment.txt and execute Stage 01 only, following solution/AGENTS.md.
```

## Referenced instruction file: `prompts/01_environment.txt` (verbatim)

```text
STAGE 01  -  Build and verify the local development environment

LANGUAGE: English only for all newly authored terminal prose, explanations, questions, and reports. Use simple ASCII formatting and short paragraphs/bullets instead of wide or box-drawn tables. Preserve source data and original historical logs. Arabic coaching happens outside this terminal.

Follow solution/AGENTS.md and the Stage 00 contract. Read docs/STATE.md and the actual assessment. Work only on this stage.

1. Inspect the host OS/shell, available RAM/disk, Python, PostgreSQL, Docker/Compose, and any existing Odoo setup. Choose one maintainable development route: an available Docker/Compose setup with source access, or a source checkout with an isolated Python environment and dedicated PostgreSQL instance/database. On Windows, account for Docker/WSL availability; do not assume either is installed or running. Do not install two competing stacks unnecessarily.
2. Verify Odoo 18 prerequisites against its official installation documentation and the pinned source requirements. Pin an exact Odoo source commit or image digest, record PostgreSQL and Python versions, and keep custom addons separate. Avoid a floating latest image and arbitrary global package upgrades. If using an image, obtain the matching source for API inspection and record how it matches the running build.
3. Configure local-only access, dedicated database credentials, an example configuration without secrets, and ignored actual local secrets. Detect port conflicts. Keep the runtime, PostgreSQL data, filestore, virtual environment, and caches out of Git. Do not use the postgres superuser as Odoo's application role.
4. Verify real PDF generation prerequisites early, including the supported wkhtmltopdf setup described by Odoo 18. Include any chosen XLSX library in reproducible dependencies. A missing PDF engine is a blocker to PDF acceptance, not a reason to call HTML output a PDF.
5. Add repeatable setup, start, stop, module-install/update, shell, and test commands appropriate for this detected environment. Separate demo, test, and clean-install databases. Document exactly which disposable database each reset command affects; never reset another database.
6. Initialize an empty custom addons repository and the minimal addon manifests needed for our two exercises. Use the exact required name azk_odoo_partner_monitor; use azk_dynamic_trial_balance for the second addon unless the assessor supplies another name. Install only justified dependencies and verify them in this edition. Keep the addons independently installable where their dependencies allow.
7. Boot Odoo, confirm the version, connect to PostgreSQL, install the minimal addons, and run a real shell query and a minimal Odoo test. If browser automation is available, verify login and Apps/module visibility. Otherwise identify the exact manual UI check I must perform; do not invent its result.

Deliver docs/environment.md with versions, architecture, verified commands, host-specific instructions, URLs, and a troubleshooting section. Explain how addons_path, __manifest__.py, __init__.py, module installation, module update, and server restart differ. Update the persistent state and stop with the standard stage report.
```

## Conversation during the stage (verbatim, in order)

Assistant message 1:

> Docker Desktop is already running (another project's containers hold ports 5433, 8000 and 9000), and the network is reachable. Next I'll resolve pinned image digests for Odoo 18 and PostgreSQL 16 without touching existing local tags.

Assistant message 2:

> The Odoo 18 source is now copied out of the pinned image into `runtime/odoo18` (all 34,383 non-translation files; a few font symlinks can't be created on Windows, which doesn't affect code inspection). Next I'm checking version-specific details in that source before writing the setup files.

User message (it appeared right after the agent loaded the WebFetch tool):

```text
Tool loaded.
```

Assistant message 3:

> Verified the version requirements in the pinned source and in part of the official install page (Python 3.10+, PostgreSQL 12+, no `postgres` superuser). Next I'll read the rest of that page for the wkhtmltopdf requirement, then write the Docker setup and the two addon skeletons.

Assistant message 4:

> Source checks are done: the pinned code confirms the test exit codes, how the shell reads piped input, and the test summary format. Now I'm writing the compose file, helper script, config and the two addon skeletons in `solution/`.

Assistant message 5:

> The setup command is running in the background. It has created the database container and is now building `azk_dev` with both addons, which pulls in `mail` and `account` with demo data, so it takes a few minutes. Meanwhile I'll check the database roles and the port bindings, which doesn't interfere with the install.

Assistant message 6 (end of a turn):

> Waiting for the `azk_dev` install to finish before running the remaining checks.

An automated notification (not user input) reported that the setup command had finished, and the agent continued.

Assistant message 7:

> Login over JSON-RPC works (`admin` is uid 2 on `azk_dev`), and both addons show as installed. One result needs a closer look: `/web/database/manager` answered 200 even though the database manager is disabled. I'm checking what that page actually allows.

Assistant message 8:

> The page only shows "The database manager has been disabled by the administrator", and both `list` and `drop` (even with the default master password) are refused with AccessDenied, so database management is blocked. Next: a real query through the Odoo shell.

Assistant message 9:

> PDF generation works end to end. Odoo reports wkhtmltopdf as `ok`, and a real 1-page PDF rendered through QWeb, with the page header and "1/1" numbering. Next I'll check where Odoo logs the test summary, so the test command can refuse a run in which no tests ran.

Assistant message 10:

> The test and clean-install runs are still going in the background: all tests, one single test, a run that should match no test, and each addon installed alone into a clean database, about 3 minutes each. Meanwhile I've drafted `docs/environment.md` and am updating the assumptions; the results section gets filled from the real logs.

Assistant message 11 (end of a turn):

> Still waiting for the background test and clean-install runs. I'll continue as soon as they finish.

An automated notification (not user input) reported that the test runs had finished, and the agent continued.

Assistant message 12:

> All four runs gave the expected results:
> - All tests: 4 tests, 0 failed, 0 errors.
> - Single test: exactly 1 test ran.
> - No-match run: Odoo itself exited 0 here, but the script caught the "0 tests" summary and failed as intended.
> - Each addon installed alone in a fresh `azk_clean`.
>
> Next I'll exercise the remaining helper commands: `update` and `install` on existing databases, the reset refusal, `psql`, and a stop/start cycle.

User message (it appeared right after the agent loaded the TaskStop tool):

```text
Tool loaded.
```

Assistant message 13:

> All the remaining helper commands passed: `update`, `install` on an existing database, the reset refusal, `psql`, and a stop/start cycle. The other project's containers are still running untouched. Before I write it into the docs, I'm confirming one claim in the pinned source: a plain restart doesn't add columns for new fields.

Assistant message 14:

> All results are now recorded in `docs/environment.md`, the state files and the Stage 01 handoff. The last steps are this stage's AI log and one local commit.

Corrections to the messages above:

- Message 8 overstates the page. Its visible notice says the manager is disabled, but its HTML also contains the create-database form. What the page displays was not checked in a browser. The accurate statement is in `docs/environment.md`: every management call is refused.
- Message 12 says "four runs". There were five: the two clean installs share one bullet.

## Summary of tool activity (summary, not verbatim)

1. Read the Stage 01 prompt and confirmed a clean Git state (commits up to `f0c79c5`).
2. Inspected the host: OS, CPU, RAM and disk, services, listening ports, tools on PATH and their versions, WSL distributions, Docker daemon and resources, and network reachability (Docker Hub, GitHub, odoo.com/partners, nightly.odoo.com).
3. Resolved image digests with `docker buildx imagetools inspect` and pulled `odoo:18.0` and `postgres:16` by digest.
4. Inspected the Odoo image: OS, Python, Odoo package version, wkhtmltopdf, Python libraries, default config and entrypoint.
5. Copied the Odoo source, without translations, from the image to the kit's `runtime/odoo18`. Then checked version-sensitive code there: Python bounds, config options, database auto-creation, the `postgres` user check, the database-management guard, the external-dependency check, the wkhtmltopdf state, the test exit code and summary, shell stdin handling, the addons path, the JSON-RPC routes and schema updates on load.
6. Read the official Odoo 18 source-installation page with WebFetch, in two parts.
7. Wrote `compose.yaml`, `config/odoo.conf`, `docker/db/init/10-create-odoo-role.sh`, `.env.example`, `scripts/dev.sh` and both addon skeletons with smoke tests; updated `.gitignore`.
8. Ran setup, start, HTTP and JSON-RPC checks, database-manager checks, a shell query, a PDF render, tests (all, single, no-match), clean installs of each addon, install and update on existing databases, the reset refusal, psql, a stop/start cycle and a PowerShell launch. Logs were kept in the kit's `runtime/logs` folder.
9. Wrote `docs/environment.md` and `docs/handoffs/stage_01_en.md`; updated `docs/STATE.md`, `docs/requirements_matrix.md`, `docs/assumptions.md` and `docs/ai/README.md`, plus the Commands section of the kit-root `CLAUDE.md` (outside this repository).
10. Wrote this log, inserted the instruction file text with a short Python script, staged the intended files by name and committed them.

## Assistant final response (verbatim)

Everything between the two rules below is the final visible response.

---

Stage 01 is done. The local Odoo 18 Community environment runs on Docker Compose with pinned images, both addons install together and separately, and the smoke tests pass. One manual check is left for you: the browser login and the Apps list.

Completed work:
- Inspected the host: Windows 11, 15.9 GB RAM, and Docker Desktop 29.4.0 already running. A host PostgreSQL 18 service holds port 5432, and another project's containers hold 127.0.0.1 ports 5433, 8000 and 9000. None of them was touched.
- Chose Docker Compose with `odoo:18.0` and `postgres:16`, both pinned by digest. The Odoo image is the 18.0-20261015 nightly build, with Python 3.12.3, wkhtmltopdf 0.12.6.1 (patched Qt), XlsxWriter 3.1.9, beautifulsoup4 4.12.3 and requests 2.31.0. That meets the official requirements (Python 3.10+, PostgreSQL 12+, wkhtmltopdf 0.12.6), which I also checked in the pinned source.
- Copied the exact Odoo source from that image to `runtime/odoo18` (outside the repo, without translations) and checked version-specific behavior there before writing any config.
- Security:
  - Odoo is published only on 127.0.0.1:8069, and PostgreSQL is not published at all.
  - Odoo connects as a non-superuser `odoo` role.
  - Passwords live only in the ignored `.env`.
  - The database manager is disabled.
- Databases: `azk_dev` (development, with demo data), plus `azk_test` and `azk_clean`, the only two the script may drop.
- Created both addon skeletons under `solution/addons/`, each with two smoke tests.

Verified (PASS unless noted):
- `scripts/dev.sh setup`: `azk_dev` was built with both addons (48 modules) in 3m06s.
- `GET /web/login` returned 200. A JSON-RPC login as admin returned uid 2, and both addons read back as installed. Calls without a session were refused.
- Database manager: its page shows the "disabled" notice, and the `list` and `drop` calls are refused even with the default master password.
- Odoo shell query: role `odoo`, PostgreSQL 16.15, both addons installed with demo data.
- Real PDF: wkhtmltopdf state `ok`, and a 1-page QWeb PDF with the header and the "1/1" page counter.
- `scripts/dev.sh test`: 0 failed, 0 error(s) of 4 tests. A single test can also run alone (1 test). A run that matched no test was rejected by the script, even though Odoo itself exited 0.
- Each addon installs alone in a fresh `azk_clean`. `install` and `update` work on existing databases, resetting `azk_dev` is refused, and a stop/start cycle works.
- NOT RUN: the browser check (no browser automation here); a deliberately failing test; `scripts/dev.sh source` itself (the same copy was made by hand); `logs`.

Please check in a browser (the server is still running; `scripts/dev.sh stop` stops it):
1. Open http://127.0.0.1:8069/web/login.
2. Log in as admin / admin.
3. Open Apps, remove the default "Apps" filter, and search for "azk".
4. Both "Odoo Partner Monitor" and "Dynamic Trial Balance" should show as installed. Tell me what you see.

How the Odoo pieces differ (the full version is in `docs/environment.md`):
- `addons_path` lists the folders Odoo scans for modules. Here that is `/mnt/extra-addons`, which is our `addons/` folder; Odoo adds its core folder automatically.
- `__manifest__.py` declares the module: its dependencies, the data files to load, and the external Python packages it needs. `__init__.py` imports the module's Python code; anything it doesn't import never runs.
- Install creates tables and loads data. Update reloads data and applies field changes. A restart reloads Python code only. So a Python-only change needs a restart, and an XML, CSV, manifest or field change needs an update.

Open items:
- The manifest author is `fahimnox` (your git name) and the license is LGPL-3. Both are defaults (A-06); tell me if you want them changed.
- Drive C: went from 18.0 GB to 10.2 GB free. Part of that is the Docker images (about 3.6 GB more) and the Odoo source copy; I did not trace the rest.
- The admin/admin login and the default master password are acceptable only because everything listens on 127.0.0.1.
- Odoo 18 Community (A-02) and questions Q-01 to Q-03 are still unconfirmed.

Files:
- New in `solution/`:
  - `compose.yaml`, `config/odoo.conf`, `.env.example` and `docker/db/init/10-create-odoo-role.sh`.
  - `scripts/dev.sh`, mainly `cmd_setup`, `cmd_test`, `reset_db` and `odoo_run`.
  - Both addons under `addons/`, each with a manifest and `tests/test_install.py`.
  - `docs/environment.md`, `docs/handoffs/stage_01_en.md` and `docs/ai/stage_01.md`.
- Updated: `.gitignore`, `docs/STATE.md`, `docs/requirements_matrix.md` (P-01 DONE; G-11, P-03 and T-01 in progress), `docs/assumptions.md` (A-04 to A-07) and `docs/ai/README.md`. Outside the repo, the Commands section of the kit-root `CLAUDE.md`.
- Everything is in one local commit on `main`; nothing was pushed.

Comprehension questions:
1. You add a new field to an existing model and only restart the server. What happens when Odoo reads that field, and which command fixes it?
2. Why does `scripts/dev.sh test` treat "of 0 tests" as a failure, even though Odoo exits with code 0?
3. The image entrypoint passes the database password as a command-line argument. Where is that visible, and why is it acceptable here but not on a shared server?

Next stage: 02

```text
Read prompts/02_requirements_and_design.txt and execute Stage 02 only, following solution/AGENTS.md.
```

---

## Follow-up after the stage report

User message (verbatim):

```text
okay i logged in and searched, found the apps skeleton azk 
don't start the next step before i tell you 
is there anything else to check or make now
```

### Summary of tool activity (summary, not verbatim)

1. Created a temporary addon `azk_failcheck` with one deliberately failing test, plus a matching `odoo.conf` and a compose override. All of it lived in the kit's `runtime/failcheck` folder, outside this repository.
2. With `COMPOSE_FILE` naming both compose files, confirmed the merged mounts, then ran `scripts/dev.sh test azk_failcheck`. It reported "1 failed, 0 error(s) of 1 tests"; Odoo exited with 1, and so did the script.
3. Dropped `azk_test` with `scripts/dev.sh reset-db azk_test` and deleted the temporary folder.
4. Ran `scripts/dev.sh logs` under `timeout 8`; it printed the server log.
5. Recorded the user's browser check and the two new results in `docs/environment.md`, `docs/STATE.md`, the Stage 01 handoff and this log, then committed.

### Assistant final response (verbatim)

Everything between the two rules below is the final visible response.

---

Thanks, I've recorded your browser check as PASS. I didn't start Stage 02.

I also closed the two Stage 01 gaps that could be closed quickly:
- Failing-test path: PASS. A temporary addon outside the repo held one deliberately failing test. `scripts/dev.sh test azk_failcheck` reported "1 failed, 0 error(s) of 1 tests" and exited with 1, so a failing test can't slip through as a pass. I removed the temporary files and the test database afterwards.
- `scripts/dev.sh logs`: PASS. It shows the server log.

The only Stage 01 item still NOT RUN is `scripts/dev.sh source` itself. The equivalent command already made the source copy, so a long re-copy of 34,383 files isn't worth it.

I updated `docs/environment.md`, `docs/STATE.md` (Stage 01 is now fully DONE), the Stage 01 handoff and the AI log, in one new local commit.

Nothing else is required before Stage 02. Since Stage 02 freezes the design, these are worth doing now:

1. Send the team lead the three open questions. The answers can change the Stage 02 design; until they arrive, I'll keep using the documented defaults:

```text
1. Is Odoo 18 Community acceptable for Exercises 1 and 2?
2. Can you share the original views specification, the Trial Balance wizard mockup, and the azk_zkteco_machine_proxy documentation link?
3. Should the Trial Balance match a specific existing report exactly (opening balances / fiscal year, analytic filtering), or is documented ledger-based behavior acceptable?
```

2. Decide the public identity:
   - Commits use `fahimnox <mohamed.fahim@noxholding.com>`, which becomes public in Stage 15. If you'd rather use a personal email or a GitHub noreply address, tell me now. Only new commits would change; the 5 existing ones would need a history rewrite, which I'd only do with your explicit go-ahead.
   - The addon manifests list `fahimnox` as author. Tell me if you want your full name instead.

3. Optional:
   - Answer the three comprehension questions from the Stage 01 report.
   - Try `scripts/dev.sh shell` and run `env["res.partner"].search([], limit=5).mapped("name")` to get a feel for the ORM.
   - Run `scripts/dev.sh stop` when you're not working. The stack uses RAM, and the PC had only about 3 GB free.

When you're ready:

```text
Read prompts/02_requirements_and_design.txt and execute Stage 02 only, following solution/AGENTS.md.
```

---
