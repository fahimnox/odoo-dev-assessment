# Enterprise transition (Stage 01B)

Carried out on 2026-11-03. This file records how the Stage 01 Community setup was adapted to the confirmed Enterprise target: the prior baseline, the Enterprise source used and why, the runtime changes, the new database, backup and rollback, the real check results, the native Trial Balance found in this build, and the open decisions for Stage 02.

Enterprise source is proprietary. This file names modules, models, methods and XML IDs and describes behavior in our own words. It quotes no Enterprise source.

## Outcome

- **Edition:** Odoo Enterprise, confirmed by the team lead (A-08). **Major version:** Odoo 18.0, still provisional (A-09, question Q-04).
- **Runtime:** the pinned image's Community core (Odoo 18.0-20261015) with the Enterprise addons of the company-supplied archive (build 18.0+e.20241208) on the addons path. It runs as a second service, `odoo-ee`, with its own database `azk_ent`, next to the untouched Community baseline.
- **Result:** the transition passes the server-side checks for this assessment's scope: start, registry load, installed Enterprise modules, our addons, update, tests on both editions, the native Trial Balance with PDF and XLSX, and HTTP access. Details are in [Verification results](#verification-results).
- **Unresolved compatibility blocker** (user decision, 2026-11-04): the vendor test `test_trial_balance_comparisons` fails with "division by zero" for reports across companies with different currencies. It passes on the archive's own 2024 build, so it comes from this pairing. Single-company use does not reach that code, but the Enterprise environment stays marked as blocked until a verified matched pair passes all eight tests. See [Compatibility follow-up](#compatibility-follow-up-2026-11-04).
- **Not run:** the browser check (manual steps at the end), the full vendor `account_reports` suite (stopped because the disk was nearly full) and subscription registration (the employer's action).
- **Residual risk:** Odoo never released this exact core/Enterprise pair; the two snapshots are about 22 months apart on the same 18.0 branch. A matched Enterprise build is requested in Q-05. It does not block Stage 02, but final acceptance (Stage 11) should state which pair was used.

## Prior baseline (Stage 01, kept)

- Docker Compose with `odoo:18.0` and `postgres:16`, both pinned by digest; Odoo 18.0-20261015 Community on Python 3.12.3, PostgreSQL 16.15, wkhtmltopdf 0.12.6.1 with patched Qt. Details in [environment.md](environment.md).
- The image's `odoo/release.py` records the git heads of that nightly build: `odoo` `8e50ecb100695e2d4c98bf3bd88463f2cfb53cad`, `enterprise` `08df1575b018ef7682a40b1ddac26c7fcde6b983`. The first pins our Community core; the second names the Enterprise revision that would match it exactly.
- `azk_dev` (Community, demo data, both addons) and `azk_clean` were not modified in Stage 01B. The Stage 01 tests and checks remain historical baseline evidence, not Enterprise acceptance.

## Enterprise source: the company-supplied archive

The user extracted an archive previously supplied by the company to `<kit-root>/odoo/odoo18`, outside this repository. It was inspected read-only. Nothing in it was executed.

**Identity (from package metadata, not the folder name):**

- `PKG-INFO` and `odoo.egg-info/PKG-INFO`: `Version: 18.0+e.20241208`.
- `odoo/release.py`: `version_info = (18, 0, 0, FINAL, 0, '')`, with the packaging suffix `+e-20241208`. This is an Odoo 18.0 Enterprise nightly source tarball of 2024-12-08. It has no git metadata and no recorded git heads.
- Layout: the Enterprise tarball layout, with the server and the Community and Enterprise addons merged in one `odoo/addons` folder of 1,243 modules (626 LGPL-3, 614 OEEL-1, 3 OPL-1).

**Modules this assessment needs (from their manifests):**

- `web_enterprise` 1.0, OEEL-1: depends on `web`, `base_setup`; auto-installs as soon as `web` is installed.
- `accountant` 1.1, OEEL-1, application "Accounting": depends on `account_accountant`.
- `account_accountant` 1.1, OEEL-1: depends on `account`, `mail_enterprise`, `web_tour`; auto-installs with `account`.
- `account_reports`, OEEL-1: depends on `accountant`; auto-installs with it. Post-init hook `set_periodicity_journal_on_companies`.
- `mail_enterprise` (depends on `mail`, `web_mobile`) and `web_mobile` (depends on `web_enterprise`): both auto-install.

**Integrity of the vendor tree** (compared with the tarball's own `odoo.egg-info/SOURCES.txt` and with the build date):

- 68,688 files under `odoo/`; 6 not listed in `SOURCES.txt`, 2 listed but missing:
  - 4 server configuration files placed into the vendor `odoo/conf/` package folder (credentials of earlier projects; values not read);
  - 2 `sign` module files whose folder names start with a space in the original tarball; the Windows extraction dropped the space (the same 2 files are the "missing" ones).
- 13 files modified after the build date (by timestamp; the 2026-11-04 follow-up checked their content against the official baseline: 2 are unchanged, 6 differ only in formatting, 2 have real local edits, 3 are configuration files): core `base/models/ir_actions.py` (2025-01-19; compared with the 2026 Community version it shows IDE line rewrapping mixed with code differences that cannot be attributed without the original file; against the build's own official baseline the code is identical), files in `sale`, `website_sale`, `website` and `test_website` (2024-12 and 2025-01), the 4 configuration files, and an `hr_recruitment` test fixture (changed on 2026-11-03, after extraction).
- No file of an Enterprise-repository module was modified after the build date.

**Not vendor source (inventoried, not used):**

- an old virtual environment (CPython 3.12.10, created under another Windows user profile);
- five server configuration files with database and admin credentials for earlier projects (only option names were listed);
- an old data directory (7 filestores, 57 sessions), PyCharm project files and old agent settings;
- an old `CLAUDE.md` and development notes (headings read as reference only, not followed);
- 15 database check, repair, cleanup and uninstall scripts and one SQL file at the archive root (not executed; the root `setup.py` is vendor packaging);
- a copy of the assessment PDF, byte-identical to our reference PDF (SHA-256 `e54e5f13720b9a66ded1a466e2ab002850720d11b068ea109793f23f4deadd10`), so it adds no new requirements material;
- four custom project folders: an earlier implementation of this assessment's modules (only the manifest metadata was read; the code was not opened, copied or used), a training module, a customer project and a third-party (OCA) module.

## Pairing decision

Options considered:

1. **Chosen:** keep the pinned image's Community core (18.0-20261015) and add the archive's Enterprise-repository modules on the addons path. This is how the official 18.0 documentation describes Enterprise ("running the server from the Community version with the addons-path option set to the folder with the Enterprise edition"), and it keeps the core that Stage 01 verified.
2. **Rejected:** run the archive's own server and Community addons (18.0+e.20241208) as one consistent build. Its core files were modified after the build, so it is not a clean vendor build, and it would replace the verified core with one about 22 months older.
3. **Not available:** Enterprise addons matching our core (the `enterprise` head recorded in the image). This needs the employer (Q-05).

Both parts are on the 18.0 release branch, so release branches are not mixed. Stage 01B accepts different revisions of the same major release once the combined installation is validated. The static evidence:

- **Module sets.** The Enterprise-repository subset is 620 modules: 611 OEEL-1, 3 OPL-1, and 6 LGPL-3 modules that depend on OEEL-1 modules. Three modules moved from Enterprise to Community during 18.0 (`certificate`, `l10n_it_edi_website_sale`, `project_hr_skills`); they are left out of the copy and the image's versions are used. Odoo always searches its own core addons folder first (`initialize_sys_path()` and `get_module_path()` in `odoo/modules/module.py`), so a duplicate name would resolve to the image anyway. 27 shared Community modules have newer manifest versions in the image (for example `analytic` 1.1 to 1.2), and the image has 62 Community modules the archive lacks.
- **Reporting data model.** The field definitions of `account.report` and its related models are identical in the archive's Community `account` module and in the image's.
- **Client-side audit.** A script checked all 620 modules for JS imports and named exports, OWL `t-inherit` parents and xpaths, and manifest asset directives that name Community files. It ran twice: against the image's 2026 Community code, and, as a control, against the archive's own 2024 Community code. Only two findings are unique to the 2026 pairing, both in the Knowledge app, which is not installed: `website_knowledge` imports an Excalidraw component that `html_editor` no longer has, and one `knowledge` toolbar xpath no longer matches. Findings about the spreadsheet library were false positives: the 2026 library is pre-transpiled and exports through `Object.assign(__exports, ...)`. Nothing was flagged in `web_enterprise`, `account_accountant` or `account_reports`.

## Runtime changes

Private, outside this repository:

- `<kit-root>/runtime/enterprise/18.0-20241208/`: the 620 Enterprise-repository modules copied from the archive without `__pycache__` or compiled files. 27,897 files, 404,523,903 bytes. Pinned by a tree digest, SHA-256 `f2c60cc6b5145e41bafe9271f36840900e4bc44b3ef963201b2c342bf369b499`, computed over the sorted `sha256  path` lines stored in `SHA256SUMS.txt` in that folder.
- `<kit-root>/runtime/backups/2026-11-03_pre_stage01b/` and `<kit-root>/runtime/logs/stage01b_*`: backups and full command logs.

In this repository:

- `compose.yaml`: new service `odoo-ee` in the `enterprise` profile. It uses the same pinned image and the same `db` service, mounts `config/odoo-enterprise.conf`, mounts the Enterprise folder read-only from `ENTERPRISE_ADDONS`, mounts `addons/`, and has its own data volume `odoo-ee-data`. It serves only `azk_ent`, on 127.0.0.1:8070, and listens on the same port inside the container (see the PDF finding below). The `db` and `odoo` services are unchanged.
- `config/odoo-enterprise.conf`: `addons_path = /mnt/enterprise-addons,/mnt/extra-addons`. The server reports the effective order `/usr/lib/python3/dist-packages/odoo/addons`, `/var/lib/odoo/addons/18.0`, `/mnt/enterprise-addons`, `/mnt/extra-addons`. `config/odoo.conf` is unchanged.
- `scripts/dev.sh`: `ODOO_EDITION` (`community` or `enterprise`, from the environment or `.env`, default `community`) selects the service, databases and port. It refuses databases of the other edition: opening `azk_dev` with the Enterprise addons path would auto-install `web_enterprise` into it on the next install, and an Enterprise database cannot load without the Enterprise addons. In Enterprise mode it checks that `ENTERPRISE_ADDONS` contains `web_enterprise` before running anything, and `setup` creates `azk_ent` with `web_enterprise`, `accountant` and both addons. That check is the real guard: on this host Docker Desktop creates a missing bind-mount folder even with `create_host_path: false` (verified: a raw `docker compose run` with a wrong path created an empty folder and started), so raw `docker compose` commands bypass it.
- `.env.example`: documents `ODOO_EDITION`, `ENTERPRISE_ADDONS` and `ODOO_EE_HTTP_PORT`. The local, ignored `.env` now sets the Enterprise edition, the folder above (as a path relative to `solution/`) and port 8070.

Databases:

- `azk_ent`: new Enterprise development database with demo data: `web_enterprise`, `accountant` and both addons, 93 modules in total, 44 of them OEEL-1. The Enterprise web server serves only this database.
- `azk_ent_test` and `azk_ent_clean`: disposable, recreated by `test` and `clean-install` in Enterprise mode.
- `azk_dev` and `azk_clean`: Community, unchanged.

## Backup and rollback

Taken before any configuration or database change, in `<kit-root>/runtime/backups/2026-11-03_pre_stage01b/` (private, never committed):

- `azk_dev.dump`: `pg_dump --format=custom` of `azk_dev`, 3,860,654 bytes (357 table-data entries); `azk_dev_filestore.tar`, 16,619,520 bytes (1,039 entries); SHA-256 sums in `SHA256SUMS.txt`.
- Copies of `.env`, `compose.yaml` and `config/odoo.conf`, and the Git checkpoint: HEAD `af3155462394d41d3a9974917da7f0b24cdce88b`, clean working tree.

Rollback path:

1. `scripts/dev.sh stop`.
2. Revert the Stage 01B commit (or check out `compose.yaml`, `scripts/dev.sh` and `.env.example` from `af31554`) and set `ODOO_EDITION=community` in `.env` (or remove the three new keys).
3. Optionally drop `azk_ent`, `azk_ent_test` and `azk_ent_clean` and remove the `odoo-ee-data` volume. Nothing else depends on them.
4. `azk_dev` was never modified. If it is ever needed, restore the dump with `pg_restore` into a new database name rather than over the existing one.

## Verification results

All checks ran on 2026-11-03 on this host. Full logs are kept privately in `<kit-root>/runtime/logs/stage01b_*`.

Inspection and preparation:

- Archive inspection, read-only, nothing from it executed: PASS. Version identity from metadata: `18.0+e.20241208`.
- Enterprise module dependencies: PASS. Every dependency of the 620 Enterprise-repository modules resolves against the archive plus the image.
- Static client-side audit: PASS for every installed module. Two findings remain in the Knowledge app, which is not installed.
- Backup before changes: PASS. `pg_restore --list` reads 357 table-data entries from the dump, and `tar` lists 1,039 filestore entries.
- `docker compose --profile enterprise config`: PASS. It resolves the Enterprise folder as a read-only bind and leaves the `odoo` service unchanged.
- `scripts/dev.sh` edition guards: PASS. All 8 cases were refused with a clear message: Community databases in Enterprise mode (install, shell, reset), Enterprise databases in Community mode (install, reset), dev databases for reset, an invalid edition, and an Enterprise folder without `web_enterprise`.
- Compose-level guard for a missing Enterprise folder: does not work on this host. A raw `docker compose run` with a wrong `ENTERPRISE_ADDONS` exited 0 and Docker created the empty folder, despite `create_host_path: false`. The folder was removed, the documentation corrected, and the `dev.sh` check remains the guard.

Enterprise runtime:

- `scripts/dev.sh setup`: PASS. It created `azk_ent` with `web_enterprise`, `accountant` and both addons (with demo data) in 3m21s: "93 modules loaded", 0 WARNING, ERROR or CRITICAL lines, no traceback.
- Registry and module state (Odoo shell on `azk_ent`): PASS.
  - The Enterprise modules (`web_enterprise`, `web_mobile`, `mail_enterprise`, `account_accountant`, `accountant`, `account_reports`) are installed from `/mnt/enterprise-addons`, the Community modules (`account` 18.0.1.3, ...) from the image, and our two addons from `/mnt/extra-addons`.
  - 93 installed modules, 44 of them OEEL-1, none in a pending state.
  - PostgreSQL 16.15, role `odoo`.
  - The company is "YourCompany" (US, USD, chart template `generic_coa`, fiscal year ending 31 December).
- `scripts/dev.sh start`: PASS. `/web/login` returned 200, and the server logged no warning or error while serving the checks below.
- HTTP checks against http://127.0.0.1:8070 (standard-library client, not a browser): PASS.
  - JSON-RPC login as `admin` returned uid 2, `server_version` `18.0+e-20261015` and `server_version_info` ending in `'e'`.
  - `/odoo` returned the web client page.
  - The bundles `web.assets_web.min.js` (5,844,485 bytes), `web.assets_web.min.css` and `web.assets_web_print.min.css` all returned 200. The CSS had no compilation-error marker. The JS bundle registers 863 templates and 41 template extensions, holds JS modules of `web_enterprise`, `account_reports`, `account_accountant`, `mail_enterprise` and `web_mobile`, and contains no server-side "missing parent template" error. The only match for that text is the checker function's own definition.
  - `account.report.get_options` and `get_report_information` for the Trial Balance worked over RPC.
  - The same call without a session was refused with `SessionExpiredException`.
- `scripts/dev.sh update azk_odoo_partner_monitor,azk_dynamic_trial_balance`: PASS. 93 modules loaded in 36s, 0 warnings.
- `scripts/dev.sh test` (Enterprise, both skeletons in a fresh `azk_ent_test`): PASS. "0 failed, 0 error(s) of 4 tests when loading database 'azk_ent_test'", 139s.
- Native Trial Balance smoke test (Odoo shell, 2026, with and without drafts): PASS. The numbers are in the next section.
- Native XLSX export (`export_to_xlsx`): PASS. 6,668 bytes, a valid workbook.
- Native PDF export (`export_to_pdf`, run inside the running Enterprise server): PASS after one fix. The first run logged "wkhtmltopdf: Exit with code 1 due to network error: ConnectionRefusedError": `web.base.url` had become http://127.0.0.1:8070 through the HTTP login, but inside the container the server listened on 8069, so wkhtmltopdf could not download the report CSS. The fix was in `compose.yaml`: `odoo-ee` now listens on the same port inside and outside the container. The rerun logged no warning and produced an 18,880-byte, one-page PDF. `pdftotext` shows the "TRIAL BALANCE" title, the company name and address, the Initial Balance / 2026 / End Balance groups with Debit and Credit, the account lines, the total and the "1/1" page footer.
- Vendor test class `scripts/dev.sh test account_reports /account_reports:TestTrialBalanceReport`: **FAIL**, 7 of 8 passed.
  - The failing test is `test_trial_balance_comparisons`: "division by zero" in `res.currency._create_currency_table()` (Community `account`), called from `account.report._init_currency_table()` (Enterprise).
  - Cause: the 2026 Community code coalesces a missing average rate to 1.0. A zero-day currency period then computes `0 / 0`, where the 2024 code computed `NULL / 0`, which PostgreSQL returns as NULL without an error. The 2026 Community test helpers also add a 1900-01-01 rate. Both were verified: the source diff, and a direct PostgreSQL check of the two expressions.
  - Control: the same 8 tests on the archive's own matched 2024 core (a one-off diagnostic container on a disposable database, dropped afterwards; not our runtime): "0 failed, 0 error(s) of 8 tests". So this is a real incompatibility of this core/Enterprise pairing.
  - Scope: the code path runs only when a report spans companies with different currencies (currency table type other than `monocurrency`). Our single-company `azk_ent` uses `monocurrency`, and its Trial Balance with a comparison period runs without error. Multi-currency journal items inside one company don't use this path.
- Full vendor suite `scripts/dev.sh test account_reports /account_reports` (286 test methods): NOT RUN. It was started for broader evidence and stopped before its first test, during asset pre-generation, because drive C: had fallen to 2.0 GB free. Docker Desktop's virtual data disk (`docker_data.vhdx`, 14.6 GB) grows with every write and does not shrink by itself, and a full disk could damage the shared PostgreSQL cluster. Run it once there is more free space (see [environment.md](environment.md), host notes).
- Community baseline, `ODOO_EDITION=community scripts/dev.sh test`: PASS. "0 failed, 0 error(s) of 4 tests when loading database 'azk_test'", 84s. Stage 01 still works after the Compose and `dev.sh` changes.
- Both editions side by side: `ODOO_EDITION=community scripts/dev.sh start` while `odoo-ee` was running gave `/web/login` 200 on port 8069 and 200 on port 8070: PASS. The Community server was stopped again afterwards.

Not run:

- Browser check of the Enterprise web client, the Trial Balance UI and the Apps list: NOT RUN, because the agent has no browser here. Steps for the user are at the end of this file. Server-side checks cannot prove that the JavaScript runs without errors in a browser.
- Subscription registration: NOT RUN. It is the employer's action, and the trial database is enough for development.

## Subscription and registration

- `azk_ent` is unregistered. `database.expiration_date`, `database.expiration_reason` and `database.enterprise_code` are not set, and the session reports no expiration date, with the subscription warning type `admin`. The Enterprise web client then assumes 30 days from today and shows its registration banner to administrators.
- Registering means entering the employer's subscription code in that banner. It is the employer's action, it was not attempted, and nothing was bought. The `database.*` parameters are never edited.
- Odoo's standard publisher-warranty call (`publisher_warranty.contract.update_notification`, a daily scheduled action that also runs on registration) sends database metadata to Odoo's servers. This is standard behavior in both editions and was already present in the Stage 01 Community setup.

## The native Trial Balance in this build

References (names only):

- Report record `account_reports.trial_balance_report` (model `account.report`) with columns `account_reports.trial_balance_report_debit` and `..._credit`.
- Custom handler `account.trial.balance.report.handler` (an abstract model inheriting `account.report.custom.handler`). It builds its lines with the General Ledger handler, `account.general.ledger.report.handler`.
- Client action `account_reports.action_account_report_coa` (tag `account_report`, URL path `trial-balance`), menu `account_reports.menu_action_account_report_coa` "Trial Balance" in the "Audit Reports" section (`account_reports.account_reports_audit_reports_menu`) under Accounting > Reporting, for `account.group_account_readonly`.
- Framework methods on `account.report`: `get_options`, the `_init_options_*` initializers, `_get_lines`, `get_report_information` (what the report UI calls), `export_to_pdf`, `export_to_xlsx`. Vendor tests: `account_reports/tests/test_trial_balance_report.py`, class `TestTrialBalanceReport`.

Options available in this build:

- date range with comparison periods (default: this month);
- journals and analytic accounts, both multi-select;
- "Draft Entries" (`all_entries`): posted only by default; with the option, every state except cancelled;
- account groups hierarchy (on by default), unfold all, multi-company selector, a text search bar;
- "Hide lines at 0" is set to never for this report;
- buttons PDF and "Download Excel".

Behavior:

- Three column groups: Initial Balance, the period, and End Balance, each with Debit and Credit only. There is no Balance column.
- Initial and End Balance are netted to one side per account. The period shows gross debit and credit. End Balance is the sum of the other groups, not a separate query.
- Initial balance follows the General Ledger convention. Balance-sheet accounts (`include_initial_balance`) take all history before the start date. Income and expense accounts start at the current fiscal year, and earlier results appear on the undistributed profits line. When the start date is the first day of a fiscal year, the previous year's result is carried as current-year earnings.
- Analytic filter, without analytic group-by: a journal item is included at its full amount when its distribution contains any selected analytic account. There is no proration. Prorated amounts are used only for analytic group-by columns, from posted analytic lines.

Observed on `azk_ent` demo data for 2026-01-01 to 2026-12-31: 8 account lines; totals Initial 0.00 / 0.00, period 264,070.03 / 264,070.03, End 12,444.87 / 12,444.87; debit equals credit in every group, and no account line shows both a debit and a credit in Initial or End. The standard demo data has 57 posted journal items, no draft or cancelled ones, a single currency (USD), 23 analytic accounts and no account groups. It therefore cannot exercise drafts, currency grouping or the hierarchy; our module must add that demo data (T-21 to T-23).

## Gaps between the native report and the assessment

The native report is a baseline and an extension opportunity, not proof that the assessment is met.

- **TransientModel wizard** as the interface (T-02): the native report is a client action with options. Required custom work.
- **Nine numeric columns** (T-15): the native report has Debit and Credit per group, no Balance.
- **Account code prefixes** (T-08): the native report has a free-text search bar, not a list of prefixes.
- **Journals and Analytic Accounts** (T-09, T-10): the PDF specifies Many2one fields; the native filters are multi-select (D-02).
- **Skip Zero Balance** (T-11): not offered by the native Trial Balance.
- **Show Amount Currency** with one row per account and transaction currency (T-12): not in the native Trial Balance.
- **Hierarchy Only Parents with Account Level Up To 1-5** (T-07): the native hierarchy has no level limit, and the standard chart of accounts has no account groups.
- **Include Unposted Entries** (T-04, T-05): the native "Draft Entries" option has the required semantics.
- **Outputs** (T-13, T-16 to T-18): the native report already offers an on-screen view, PDF and XLSX. Whether our outputs reuse them is a Stage 02 decision; whichever is chosen, all three must come from one calculation.

## Decisions for Stage 02

- Whether `azk_dynamic_trial_balance` extends the native framework (declaring `account_reports`) or keeps its own engine on `account`. The kit prefers native extension where it meets the assessment.
- The opening-balance convention: the native fiscal-year-aware rule or all history. Decide, document, and test with a cross-year fixture (Stage 07).
- Analytic filter semantics: native whole-item inclusion or proportional allocation (D-07).
- Which edition the final tests run on. The target is Enterprise; Community runs can still catch accidental Enterprise dependencies in the Partner Monitor.
- PDF tests need a running web server, because wkhtmltopdf downloads the report CSS over HTTP.

## Compatibility follow-up (2026-11-04)

Requested by the user after Stage 01B: resolve the failing `TestTrialBalanceReport` case with a verified compatible source pair, without patching vendor code, skipping the test or changing its expectations, and without adopting the archive's modified core. `azk_ent` and `azk_dev` are preserved and were not opened by any other core.

### Result in short

- **The official Community revision of the archive's build is identified and verified by content:** `odoo/odoo` commit `4e5027c159a9d9a8dd006618486c8e54cb1eb453` on branch 18.0 (committed 2024-12-08 01:24:52 UTC, "[I18N] Update translation terms from Transifex").
- **The matched pair to validate** is that commit plus the 623 Enterprise-repository modules of the same build, 18.0+e.20241208. Both are pinned below.
- **Validation was NOT RUN:** drive C: had 2.5 GB free at the start and 1.5 to 1.7 GB during the follow-up. That is too little to fetch the source and build fresh databases safely (see [Disk check](#disk-check)).
- **The blocker remains unresolved and the Enterprise environment is not ready.**

### User-reported browser check

The user's follow-up message (2026-11-04) says the requested browser smoke check was done. It was done by the user on the Stage 01B environment (http://127.0.0.1:8070, `azk_ent`); the agent did not run it. The message gave no detailed observations, and states that it does not resolve the failing vendor test.

### Disk check

Measured before and during the follow-up:

- C: had 2.5 GB free at the start. It fell to 1.5 GB within minutes while the agent was only reading files, then stood at 1.5 to 1.7 GB.
- Docker's virtual disk stayed at 14,626,586,624 bytes; its file system holds 12 GB.
- Windows `pagefile.sys` is 10.9 GB and `hiberfil.sys` 6.8 GB. A system-managed page file grows under memory pressure; that is a possible, unproven cause of the drop.
- Drive D: has 8.5 GB free. Docker's disk and the PostgreSQL clusters (ours and the other project's) are on C:, so a full C: endangers all of them.

### Employer-provided matching pair

None is available in the workspace. The only supplied Enterprise build is the 2024-12-08 archive. Nothing outside the kit was searched. Question Q-05 (Enterprise addons matching our 2026 core, enterprise commit `08df1575b018ef7682a40b1ddac26c7fcde6b983`) is still open.

### Official baseline for the archive's Community part

Method: no download of the repository. The archive's files were compared with the official GitHub trees by git blob SHA-1, which is computed from file content only, so it does not depend on timestamps.

- The archive's files were checked out at 2024-12-08 07:05-07:06 UTC: 422 of `account`'s files share that minute, packaging edited `release.py` at 07:06:46, and `PKG-INFO` was built at 07:55.
- The GitHub commits API lists no `odoo/odoo` 18.0 commit dated between `4e5027c1` (01:24:52 UTC) and 07:06 UTC that day. The date filter alone was not taken as proof; the content comparison below is the proof.
- Comparison with the recursive tree of `4e5027c1` (37,496 files):
  - 36,514 files are byte-identical in the archive, including all 15,650 translation files.
  - The 972 official files absent from the archive are all outside `addons/` and `odoo/` (`doc/` 929, `debian/` 17, `setup/` 17, `.github` 3, `.tx`, and root files such as `odoo-bin` and `CONTRIBUTING.md`), so they are packaging exclusions. No module file is missing. The only official trace of `website_twitter` is one translation file, which the archive also has.
  - 10 files differ; see the next section.
- The archive's remaining modules have three sources: 623 Enterprise-repository modules (the 620 copied in Stage 01B plus `certificate`, `l10n_it_edi_website_sale` and `project_hr_skills`, all OEEL-1 in this build), and 30 `theme_*`/`test_themes` modules. The 30 themes are byte-identical to official `odoo/design-themes` commit `3057d4661952300a5725159dd2df412af0f2da85` (2024-12-08 02:04:57 UTC, that repository's head before the checkout): 4,266 of 4,268 files, with only `.gitignore` and `.tx/config` absent.
- Conclusion: the archive is Odoo's 18.0+e.20241208 nightly composition of `odoo/odoo@4e5027c1`, `design-themes@3057d466` and the Enterprise repository at the same time, plus the local changes listed next. The Enterprise part itself could not be compared with an official baseline, because the Enterprise repository is private. Its only integrity evidence is the tarball's own file list (`SOURCES.txt`) and build-time timestamps, and timestamps alone prove neither modification nor its absence.

### Verification of the files flagged in Stage 01B

Stage 01B flagged 13 files with timestamps after the build date. Against the official baseline:

- **Identical content, only the timestamp changed (2):** `website/views/website_templates.xml` and `hr_recruitment/tests/resume.eml`.
- **Same code, formatting only (6):** `base/models/ir_actions.py`, `sale/controllers/product_configurator.py`, `website_sale/controllers/combo_configurator.py`, `website_sale/controllers/product_configurator.py` and `website_sale/controllers/variant.py` have an identical Python syntax tree (AST), with only line wrapping and indentation differing; `sale/static/src/js/product/product.xml` differs only in whitespace. This corrects the Stage 01B note that `ir_actions.py` "shows code differences that cannot be attributed": against the build's own baseline it has none.
- **Real local changes (2):**
  - `website_sale/controllers/main.py`: function `shop_checkout` gained two debugging `print(...)` statements, plus re-indentation.
  - `test_website/data/test_website_data.xml`: records rearranged and content reduced (213 fewer non-whitespace characters).
- **Not vendor files (3, plus 1 older):** configuration files with credentials in `odoo/conf/`.
- **Packaging changes, expected:** `odoo/release.py` gained only the line `version += '+e-20241208'`, and `setup.cfg` was re-serialized by setuptools with an `[egg_info]` section.

So the archive's core is not pristine, as Stage 01B said, but its server package differs from official only in formatting. It is still not adopted: the official commit is used instead.

### Identified matched pair (pins)

- **Community:** `odoo/odoo` `4e5027c159a9d9a8dd006618486c8e54cb1eb453` (GitHub, branch 18.0). Official tree: 37,496 files; without translations 21,846 files, 0.20 GB. Not downloaded yet.
- **Enterprise:** build 18.0+e.20241208, 623 Enterprise-repository modules in two private folders:
  - `<kit-root>/runtime/enterprise/18.0-20241208/`: 620 modules, tree SHA-256 `f2c60cc6b5145e41bafe9271f36840900e4bc44b3ef963201b2c342bf369b499` (unchanged from Stage 01B);
  - `<kit-root>/runtime/enterprise/18.0-20241208-moved-to-community/`: the 3 modules that later moved to Community, copied on 2026-11-04, 106 files, 722,254 bytes, tree SHA-256 `ec0225f50aacc43c90c38fdc2c80a88c2e1ce16705e8203c91ce47a79e9482c4`.
- **Supporting:** `odoo/design-themes` `3057d4661952300a5725159dd2df412af0f2da85`. Website themes are not needed for this assessment and would not be mounted.
- Evidence that this is a compatible pair: it is the composition Odoo itself built and shipped as 18.0+e.20241208, verified on the Community side by content. A matching major version or date alone was not taken as proof. Test evidence on the official source is still missing: the Stage 01B control run (8 of 8) used the archive's core, which differs from the official one in the files listed above.

### Remaining steps (blocked by disk space)

Once C: has at least 5 GB free (estimate: 0.20 GB of source, about 0.15 GB of new databases, and an unpredictable growth of Docker's disk during installs and tests, with a margin for the shared PostgreSQL clusters):

1. Fetch `odoo/odoo@4e5027c1` from GitHub without `i18n/` to `<kit-root>/runtime/community/18.0-4e5027c1/`. Check every file's git blob SHA against the official tree, and write `SHA256SUMS.txt` and a tree digest.
2. Add a separate Compose service for the pair, using the same pinned image for Python and wkhtmltopdf:
   - the official `odoo/` mounted read-only over the image's server package;
   - the official `addons/` and both Enterprise folders on the addons path, then our `addons/`;
   - its own data volume, its own port (8071, the same inside and outside the container) and its own database prefix.
   - Add a `dev.sh` edition with the same guards. The Stage 01B `odoo-ee` service and `azk_ent` stay as they are, and no older core ever opens `azk_ent`.
3. On fresh databases:
   - all eight `TestTrialBalanceReport` tests, including `test_trial_balance_comparisons`;
   - both custom addons' tests;
   - a new development database with `web_enterprise`, `accountant` and both addons for the login, Trial Balance, XLSX and PDF smoke checks.
   - No full accounting suite.
4. Only if all of that passes: make the new edition the default and mark the blocker resolved.

## Manual browser check (for the user)

Not run by the agent, which has no browser here:

1. `scripts/dev.sh start` (the Enterprise edition is the default in this workspace), then open http://127.0.0.1:8070/web/login.
2. Log in as `admin` with password `admin`.
3. Expected: the Enterprise home menu with app icons, and a registration or expiration banner for administrators. Don't register and don't click "buy". There should be no red error dialog and no blank page.
4. Open Accounting > Reporting > Trial Balance (in the "Audit Reports" section of the Reporting menu), or go directly to http://127.0.0.1:8070/odoo/trial-balance. Expected: the report shows Initial Balance, the period and End Balance. Change the date filter, toggle "Draft Entries", then click PDF and "Download Excel" and open both files.
5. Open Apps, remove the "Apps" filter and search for `azk`. Expected: both addons are installed.
6. Report anything unexpected, especially error dialogs or messages in the browser console.
