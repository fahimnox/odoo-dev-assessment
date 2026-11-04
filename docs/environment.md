# Development environment

Set up and verified in Stage 01 on 2026-11-01 (Community). Extended in Stage 01B on 2026-11-03 with an Enterprise service, which is now the target edition; see [enterprise_transition.md](enterprise_transition.md) for the source, the pairing decision and the native Trial Balance. The verification results of both stages are at the end of this file.

## Editions

- **Enterprise (target):** service `odoo-ee`, http://127.0.0.1:8070, databases `azk_ent` (development, demo data), `azk_ent_test` and `azk_ent_clean`. It runs the image's Community server with a private Enterprise addons folder on the addons path, which is how the official documentation describes running Enterprise.
- **Community (Stage 01 baseline):** service `odoo`, http://127.0.0.1:8069, databases `azk_dev`, `azk_test` and `azk_clean`. Unchanged since Stage 01; its results are baseline evidence, not Enterprise acceptance.
- `scripts/dev.sh` works on one edition at a time, chosen by `ODOO_EDITION` (environment or `.env`; default `community`). In this workspace `.env` sets `enterprise`. Example: `ODOO_EDITION=community scripts/dev.sh test`.

## Route and why

- Docker Compose runs the official Odoo 18 Community image and a dedicated PostgreSQL 16 container. Both images are pinned by digest.
- Why this route on this host:
  - Docker Desktop 29.4.0 with Compose v5.1.1 (WSL2 backend) was already installed and running, so nothing new had to be installed on Windows.
  - The official image already contains the parts that are hard to set up on Windows: wkhtmltopdf 0.12.6.1 with patched Qt, Python 3.12 and every library the two addons need (requests, beautifulsoup4, XlsxWriter).
  - A dedicated database container keeps the assessment separate from what already runs on this machine: a host PostgreSQL 18 service on port 5432, and another project's containers on 127.0.0.1 ports 5433, 8000 and 9000. None of them was changed.
- Not chosen: a native Windows source checkout. It would need wkhtmltopdf installed with administrator rights, possibly C++ build tools for some Python packages, and a new role on the host PostgreSQL 18 service, which needs that server's superuser password.

## Pinned versions

- Odoo image: `odoo:18.0@sha256:9668abacd894276ed009e8db7db1d1ffb8068af6982f76a3400ed0d68e40432d` (multi-platform index; the linux/amd64 manifest is `sha256:5cd180474d3861295b4b727f4d63ab172ff870c2ae9c937abdafbeae939ee3cf`). Image labels: built from github.com/odoo/docker commit `bf04b8fe14d39e4e1090bc41e56460341ad3a994` (18.0 folder), version `18.0-20261015`.
  - Odoo Server 18.0-20261015 (Debian package `odoo` 18.0.20261015, the nightly build of 2026-10-15).
  - Ubuntu 24.04.5 LTS, Python 3.12.3.
  - wkhtmltopdf 0.12.6.1 (with patched qt), package `wkhtmltox` 1:0.12.6.1-3.jammy.
  - XlsxWriter 3.1.9, beautifulsoup4 4.12.3, soupsieve 2.5, requests 2.31.0, lxml 5.2.1, psycopg2 2.9.9.
- PostgreSQL image: `postgres:16@sha256:5db6dac2ef5dcff512f4f00a009c3c332b9f2f28f24277175bf3e4a3d02ef83a`, PostgreSQL 16.15 (Debian 16.15-1.pgdg13+2).
- Both images were pulled by digest, so no local image tag was moved (other projects use `postgres:16-alpine` and `postgres:18`).
- Community core revision: the image's `odoo/release.py` records the git heads of its nightly build, `odoo` `8e50ecb100695e2d4c98bf3bd88463f2cfb53cad` (and `enterprise` `08df1575b018ef7682a40b1ddac26c7fcde6b983`, `design-themes` `9a621969625c30867e90608796d2c84465a23350`, which are not part of the public image).
- Enterprise addons (Stage 01B): build `18.0+e.20241208` (Odoo 18.0 Enterprise nightly source tarball of 2024-12-08, supplied by the company; no git metadata). Curated copy of the 620 Enterprise-repository modules in `<kit-root>/runtime/enterprise/18.0-20241208/`: 27,897 files, 404,523,903 bytes, tree SHA-256 `f2c60cc6b5145e41bafe9271f36840900e4bc44b3ef963201b2c342bf369b499` (from `SHA256SUMS.txt` in that folder). Same 18.0 release branch as the core; about 22 months older.
- **Unresolved compatibility blocker (2026-11-04):** the Stage 01B pair above (2026 core with 2024 Enterprise addons) fails the vendor test `TestTrialBalanceReport.test_trial_balance_comparisons`. The user decided that the Enterprise environment stays blocked until a verified matched pair passes all eight tests.
- Matched pair identified on 2026-11-04, **not set up yet** (blocked by disk space; see [enterprise_transition.md](enterprise_transition.md#compatibility-follow-up-2026-11-04)):
  - Community `odoo/odoo` `4e5027c159a9d9a8dd006618486c8e54cb1eb453` (18.0, 2024-12-08 01:24:52 UTC). Verified by git blob SHA as the Community source of the archive's build: 36,514 identical files and 10 explained differences.
  - Enterprise build 18.0+e.20241208, 623 modules: the 620-module folder above plus `<kit-root>/runtime/enterprise/18.0-20241208-moved-to-community/` (`certificate`, `l10n_it_edi_website_sale`, `project_hr_skills`), tree SHA-256 `ec0225f50aacc43c90c38fdc2c80a88c2e1ce16705e8203c91ce47a79e9482c4`.
- With `web_enterprise` loaded, the server reports its version as `18.0+e-20261015` and `server_version_info` `[18, 0, 0, 'final', 0, 'e']`: `web_enterprise/version.py` adds the `+e` marker to the Community build string at import time. It does not mean that the Enterprise addons are from 2026-10-15.
- Host: Windows 11 Pro 10.0.26200, Intel Core i7-8650U (4 cores, 8 threads), 15.9 GB RAM (3.2 GB free at inspection), 18.0 GB free on C:. Docker Desktop VM: 8 CPUs, 8,263,008,256 bytes of memory. Git Bash with git 2.53.0.windows.2.

## Prerequisites check

Each line gives the official Odoo 18 documentation (source installation page), the pinned source, and what this setup provides.

- Python: the docs say "Odoo requires Python 3.10 or later to run". `odoo/__init__.py` sets `MIN_PY_VERSION = (3, 10)` and `MAX_PY_VERSION = (3, 14)`. The image has Python 3.12.3.
- PostgreSQL: the docs list "supported versions: 12.0 or above". The pinned source has no minimum-version check. This setup uses 16.15.
- wkhtmltopdf: the docs say it "must be installed manually in version 0.12.6 for it to support headers and footers" and link to release 0.12.6.1-3. The image ships exactly that build, with patched Qt. `ir.actions.report` reports state `ok` for 0.12.0 and later (`odoo/addons/base/models/ir_actions_report.py`).
- Database user: the docs say "As Odoo forbids connecting as `postgres`, create a new PostgreSQL user". `check_postgres_user()` in `odoo/cli/server.py` aborts when `db_user` or `PGUSER` is `postgres`. Odoo connects as the `odoo` role here.

## Architecture

```text
browser on this PC
   |
   |  http://127.0.0.1:8069   (published on the loopback interface only)
   v
odoo container  (odoo:18.0, pinned)
   - /mnt/extra-addons    <- ./addons            (bind mount, our two addons)
   - /etc/odoo/odoo.conf  <- ./config/odoo.conf  (bind mount, read-only)
   - /var/lib/odoo        <- volume odoo-data    (filestore, sessions)
   |
   |  PostgreSQL protocol, role "odoo", compose network only
   v
db container  (postgres:16, pinned, no published port)
   - /var/lib/postgresql/data <- volume db-data
   - /docker-entrypoint-initdb.d <- ./docker/db/init (read-only)
```

Enterprise service (Stage 01B), next to the one above and sharing the `db` service:

```text
browser on this PC
   |
   |  http://127.0.0.1:8070   (loopback only; the same port inside the container)
   v
odoo-ee container  (same pinned odoo:18.0 image, compose profile "enterprise")
   - /mnt/enterprise-addons <- ENTERPRISE_ADDONS (read-only, private, outside Git)
   - /mnt/extra-addons      <- ./addons
   - /etc/odoo/odoo.conf    <- ./config/odoo-enterprise.conf (read-only)
   - /var/lib/odoo          <- volume odoo-ee-data (separate filestore, sessions)
```

- Effective addons path, as logged by the server: `/usr/lib/python3/dist-packages/odoo/addons` (image core, always first), `/var/lib/odoo/addons/18.0`, `/mnt/enterprise-addons`, `/mnt/extra-addons`.
- Compose project name: `azk-odoo-assessment`. Its network and volumes are prefixed with that name, so they cannot collide with other projects.
- Odoo core stays inside the image. It is not vendored into this repository and not modified.
- Matching source for reading: `scripts/dev.sh source` copies `/usr/lib/python3/dist-packages/odoo` from the same pinned image to `../runtime/odoo18` (outside this repository), without translations. This is the exact code that runs. On Windows a few font symlinks cannot be created; code files are unaffected.

## Configuration and secrets

- `.env` (ignored by Git) holds `POSTGRES_PASSWORD`, `ODOO_DB_PASSWORD` and `ODOO_HTTP_PORT`, and since Stage 01B `ODOO_EDITION`, `ENTERPRISE_ADDONS` (path of the Enterprise addons folder; relative paths are resolved from `solution/`) and `ODOO_EE_HTTP_PORT`. `scripts/dev.sh setup` creates it with random 48-character hex passwords. `.env.example` is the committed template.
- `config/odoo.conf` and `config/odoo-enterprise.conf` (committed) contain no secrets: `addons_path`, `data_dir`, `list_db = False` and `log_level`.
- The Enterprise source is proprietary. It is mounted read-only from outside the repository and is never committed, copied into `addons/` or quoted in documentation.
- The database connection comes from the `PG*` variables in `compose.yaml`. The image entrypoint turns them into `--db_host`, `--db_port`, `--db_user` and `--db_password` arguments, so the password is visible in the process list inside the container. That is acceptable for local development.
- PostgreSQL roles:
  - `postgres`: bootstrap superuser of the db container. Only the container's own initialization uses it.
  - `odoo`: `LOGIN CREATEDB NOSUPERUSER NOCREATEROLE`, created by `docker/db/init/10-create-odoo-role.sh` when the data volume is first initialized. Odoo uses only this role.
- Local-only access: Odoo is published on 127.0.0.1 only, and PostgreSQL is not published at all.
- The database manager is disabled (`list_db = False`). `check_db_management_enabled()` in `odoo/service/db.py` then refuses database listing, creation, backup and deletion over HTTP and RPC. The master password (`admin_passwd`) is left at Odoo's default because no database operation accepts it in this configuration; set a real one before ever enabling the database manager.
- The web server serves only `azk_dev` (`--database=azk_dev --db-filter=^azk_dev$` in `compose.yaml`).
- Databases created from the command line get Odoo's default administrator login `admin` with password `admin`. This is acceptable only because the server listens on loopback.

## Databases

- `azk_dev`: development and demo database, with demo data (the Odoo 18 default; `--without-demo` defaults to False in `odoo/tools/config.py`). The web server uses it. `setup` creates it, and no script command drops it.
- `azk_test`: disposable. Every `scripts/dev.sh test` run drops and recreates it.
- `azk_clean`: disposable. Every `scripts/dev.sh clean-install` run drops and recreates it.
- `scripts/dev.sh reset-db NAME` accepts only `azk_test` or `azk_clean`. It drops that database (`dropdb --force`) and its filestore folder `/var/lib/odoo/filestore/NAME`, and refuses any other name.
- Removing the Docker volumes (`docker compose down --volumes`) deletes all databases and filestores. No script does that.
- Enterprise (Stage 01B): `azk_ent` is the development database with demo data, created by `scripts/dev.sh setup` in Enterprise mode with `web_enterprise`, `accountant` and both addons (93 modules). The Enterprise web server serves only `azk_ent`. `azk_ent_test` and `azk_ent_clean` are disposable, like their Community counterparts.
- Each edition keeps to its own databases: `scripts/dev.sh` refuses `azk_ent*` names in Community mode and any other name in Enterprise mode. `web_enterprise` auto-installs as soon as `web` is installed, so running a Community database with the Enterprise addons path would convert it on the next install.
- `azk_ent` is unregistered (trial). Registration needs the employer's subscription code; see [enterprise_transition.md](enterprise_transition.md).

## Commands

Run these from `solution/` in Git Bash. Each command acts on the edition chosen by `ODOO_EDITION` (see [Editions](#editions)) and prints it first, for example `edition: enterprise (service odoo-ee, database azk_ent)`. In Enterprise mode, read "azk_dev/azk_test/azk_clean" below as "azk_ent/azk_ent_test/azk_ent_clean" and port 8069 as 8070.

```text
scripts/dev.sh setup                     # first run: .env, images, PostgreSQL, the dev DB with both addons
                                         # (enterprise: azk_ent with web_enterprise and accountant as well)
scripts/dev.sh start                     # web server at http://127.0.0.1:8069/web/login (enterprise: 8070)
scripts/dev.sh stop
scripts/dev.sh restart
scripts/dev.sh status
scripts/dev.sh logs
scripts/dev.sh install ADDONS [DB]       # comma-separated; DB defaults to azk_dev
scripts/dev.sh update ADDONS [DB]        # restarts the web server afterwards if it runs
scripts/dev.sh shell [DB]                # interactive, or pipe Python code into it
scripts/dev.sh psql [DB]
scripts/dev.sh test                      # both addons, in a fresh azk_test
scripts/dev.sh test azk_dynamic_trial_balance
scripts/dev.sh test azk_odoo_partner_monitor /azk_odoo_partner_monitor:TestModuleInstalled.test_module_is_installed
scripts/dev.sh clean-install             # both addons, in a fresh azk_clean
scripts/dev.sh clean-install azk_odoo_partner_monitor
scripts/dev.sh reset-db azk_test
scripts/dev.sh source                    # copy the pinned Odoo source to ../runtime/odoo18
scripts/dev.sh test account_reports /account_reports:TestTrialBalanceReport   # enterprise: native TB tests
ODOO_EDITION=community scripts/dev.sh test                                    # Community baseline
```

- Test selection uses Odoo's `--test-tags` syntax, `[-][tag][/module][:class][.method]` (from the option help in `odoo/tools/config.py`). The second argument of `test` is passed as is.
- `test` prints the matching log lines and Odoo's summary, for example `0 failed, 0 error(s) of 4 tests when loading database 'azk_test'`. It fails when a test fails, when no summary is found, or when no test ran. That last check matters because Odoo exits with 0 when no test matched.

## Windows notes

- Use Git Bash. In PowerShell, `bash` resolves to `C:\WINDOWS\system32\bash.exe`, which starts WSL (whose default distribution here is `docker-desktop`), not Git Bash. From PowerShell, call Git Bash explicitly: `& "$env:LOCALAPPDATA\Programs\Git\bin\bash.exe" scripts/dev.sh status`.
- `scripts/dev.sh` sets `MSYS_NO_PATHCONV=1`, because Git Bash otherwise rewrites container paths such as `/var/lib/odoo` into Windows paths.
- Interactive `shell` and `psql` need a real terminal. If docker reports "the input device is not a TTY" in mintty, use Windows Terminal or prefix the command with `winpty`.
- Docker Desktop must be running. If port 8069 is taken, set another `ODOO_HTTP_PORT` in `.env` and restart.
- Shell scripts and config files must keep LF line endings; `.gitattributes` enforces this. A CRLF init script fails inside the Linux container.

## Odoo concepts in this setup

- `addons_path` lists the folders where Odoo looks for modules; a module is a folder containing `__manifest__.py`. Here it is `/mnt/extra-addons`, our `addons/` folder. Odoo also always adds its data-dir addons folder and its own core addons folder (`initialize_sys_path()` in `odoo/modules/module.py`); the startup log shows all three.
- `__manifest__.py` describes a module: name, version, `depends` (installed first), `data` files (loaded in the listed order on install and update) and `external_dependencies`. Odoo checks the latter before installing, using `importlib.metadata`, so they must be PyPI distribution names such as `beautifulsoup4` and `XlsxWriter` (`check_python_external_dependency()` in `odoo/modules/module.py`).
- `__init__.py` makes the module a Python package and imports its Python code (models, wizards, controllers). Code that is not imported is never loaded. Tests are not imported there: Odoo discovers the `tests` package itself.
- Installing a module (`-i`, or Install in Apps) installs its dependencies, creates the tables and columns for its models, and loads its data files and, if enabled, its demo data. A module that is new on disk must first appear in the module list. The command line does this automatically; in the UI, use Apps > Update Apps List in developer mode.
- Updating a module (`-u`, or Upgrade) reloads its data files (views, actions, menus, security, data records) and applies model changes, such as new or changed fields, to the database.
- Restarting the server reloads Python code. A restart alone does not reload XML or CSV data and does not create columns for new fields; that needs an update. In practice: Python-only change -> restart; manifest, XML, CSV or field change -> update (`scripts/dev.sh update` restarts the server afterwards).

## Troubleshooting

- "set POSTGRES_PASSWORD in .env": `.env` is missing. Run `scripts/dev.sh setup`.
- "port is already allocated" on start: another process uses the Odoo port. Change `ODOO_HTTP_PORT` in `.env`.
- "Using the database user 'postgres' is a security risk, aborting.": `PGUSER` or `db_user` is `postgres`. Keep `odoo`.
- A changed `ODOO_DB_PASSWORD` does not reach an existing role, because init scripts run only on an empty data volume. Change it with `ALTER ROLE` as `postgres`, or delete the volumes, which destroys every assessment database.
- A module is missing from Apps: check that it sits directly under `addons/`, has a `__manifest__.py`, and that its external dependencies are installed, then update the apps list.
- Tests seem to pass but nothing ran: look for the summary line and check that it counts more than 0 tests. Odoo logs that line as a WARNING when no test ran, and `scripts/dev.sh test` treats it as a failure.
- PDF output without styling: wkhtmltopdf downloads the CSS from the Odoo server at `web.base.url` (or `report.url`). Generate PDFs from the running server, as the check below does.
- Harmless log noise: the Odoo shell prints "Warn: Can't find .pfb for face 'Courier'" when it starts, and docutils prints two RST formatting messages while the core `mail` module installs. Neither affected the checks below.
- `scripts/dev.sh source` reports "Cannot create symlink" for a few font files on Windows. This is expected.
- "ODOO_EDITION=enterprise needs ENTERPRISE_ADDONS" or "has no web_enterprise module": set `ENTERPRISE_ADDONS` in `.env` to the Enterprise addons folder (the one that directly contains `web_enterprise/`). `scripts/dev.sh` checks this before every Enterprise command. Raw `docker compose` commands do not: on this host Docker Desktop silently creates a missing bind-mount folder (despite `create_host_path: false`) and starts Odoo without the Enterprise addons. Use `scripts/dev.sh`, and delete any empty folder created that way.
- "the enterprise edition only uses azk_ent* databases" or "is an Enterprise database": the command targeted the other edition's database. Switch `ODOO_EDITION` instead of forcing it.
- Enterprise PDF without styling, with "wkhtmltopdf: Exit with code 1 due to network error: ConnectionRefusedError" in the log: wkhtmltopdf runs inside the container and downloads the CSS from `report.url` or else `web.base.url`, which a browser login sets to the host URL. That is why `odoo-ee` listens on the same port inside and outside the container. If you change `ODOO_EE_HTTP_PORT`, recreate the service (`docker compose up -d odoo-ee`, or `stop` then `start`). The Community service has the same constraint with `ODOO_HTTP_PORT`: its container port is fixed at 8069.
- Low disk space: Docker Desktop keeps all images, containers and volumes in one virtual disk (`%LOCALAPPDATA%\Docker\wsl\disk\docker_data.vhdx`, 14.6 GB on 2026-11-03). It grows with every write, including test runs and PostgreSQL WAL, and does not shrink by itself. Pruning inside Docker frees space for reuse but returns none to Windows. Keep several GB free on C: before long test runs: a full disk can damage the PostgreSQL cluster that holds every assessment database. On 2026-11-03 C: had 2.0 GB free, so the full vendor `account_reports` suite was stopped. On 2026-11-04 C: had 2.5 GB, then 1.5 to 1.7 GB free while the agent was only reading files, so the matched-pair setup was not started. Large items on C: then were `pagefile.sys` (10.9 GB, system-managed; it usually shrinks after a restart), `hiberfil.sys` (6.8 GB) and Docker's disk (14.6 GB, holding 12 GB). Drive D: had 8.5 GB free.
- Registration or expiration banner in the Enterprise web client: expected for an unregistered trial database. Registering needs the employer's subscription code; don't edit the `database.*` parameters to hide it.
- `release.version` shows `18.0+e-20261015`: added by `web_enterprise` at import time; the Enterprise addons are still the 2024-12-08 build (see [Pinned versions](#pinned-versions)).

## Verification results (2026-11-01)

All commands ran on this host through Git Bash. Full logs are kept outside the repository, in the kit's `runtime/logs/` folder.

- `scripts/dev.sh setup`: PASS. It created `.env` with two 48-character hex passwords, started PostgreSQL, and created `azk_dev` with both addons and demo data: "48 modules loaded in 131.86s". Total time 3m06s, exit code 0.
- Roles and ownership: PASS. `odoo` is `super=false createdb=true createrole=false login=true`; `postgres` is the db container's superuser. `azk_dev`, `azk_test` and `azk_clean` are all owned by `odoo`.
- Ports: PASS. Odoo is published only on `127.0.0.1:8069`, and PostgreSQL has no published port. The other project's containers kept running throughout.
- Login page: `GET /web/login` returned 200. PASS.
- Login and module visibility over HTTP (JSON-RPC calls, not a browser): PASS.
  - `/web/session/authenticate` as `admin` on `azk_dev` returned uid 2 and server version 18.0-20261015.
  - `/web/dataset/call_kw` listed `azk_odoo_partner_monitor` (application, installed, 18.0.1.0.0) and `azk_dynamic_trial_balance` (installed, 18.0.1.0.0).
  - The same call without a session was refused with `SessionExpiredException`.
- Database manager: PASS. `/web/database/manager` returns a page with the notice "The database manager has been disabled by the administrator". The page's HTML still contains the create-database form, but the JSON-RPC `db` service refused both `list` and `drop` (with the default master password) with `AccessDenied`.
- Odoo shell (`scripts/dev.sh shell` with piped code): PASS. It reported Odoo 18.0-20261015, database `azk_dev`, PostgreSQL role `odoo` and PostgreSQL 16.15; `account`, `mail` and both addons are installed with demo data; 37 partners and 1 company.
- PDF prerequisite: PASS. In a shell inside the running server container, `get_wkhtmltopdf_state()` returned `ok`. `_render_qweb_pdf("base.ir_module_reference_print", ...)` produced a 13,764-byte PDF 1.4. `pdftotext` shows 1 page with the company header, the "1/1" page counter and the module data.
- `scripts/dev.sh test`: PASS. 4 tests ran (2 per addon): "0 failed, 0 error(s) of 4 tests when loading database 'azk_test'". Exit code 0, 2m37s.
- Single test, `scripts/dev.sh test azk_odoo_partner_monitor /azk_odoo_partner_monitor:TestModuleInstalled.test_module_is_installed`: PASS. Exactly 1 test ran, 1m28s.
- No-match guard, `scripts/dev.sh test azk_odoo_partner_monitor /azk_odoo_partner_monitor:NoSuchClass`: PASS. Odoo logged "0 failed, 0 error(s) of 0 tests" as a WARNING and exited with 0; the script printed "error: no tests ran; check ADDONS and TAGS" and exited with 1.
- Independent installation: PASS.
  - `scripts/dev.sh clean-install azk_odoo_partner_monitor` installed the partner monitor and `mail`, and left `account` and the trial balance addon uninstalled (1m27s).
  - `scripts/dev.sh clean-install azk_dynamic_trial_balance` installed the trial balance addon with `account`, and left the partner monitor uninstalled (2m20s).
- `scripts/dev.sh install azk_odoo_partner_monitor azk_clean`, on the database that already had the trial balance addon: PASS. Both addons were then installed (20s).
- `scripts/dev.sh update azk_odoo_partner_monitor` on `azk_dev` while the server ran: PASS. The module reloaded and the server restarted (23s).
- `scripts/dev.sh reset-db azk_dev`: PASS. Refused with "only azk_test azk_clean can be reset", exit code 1.
- `scripts/dev.sh psql` with piped SQL: PASS. Used for the ownership and `azk_clean` module-state queries above. The role query ran directly with `docker compose exec db psql` as `postgres`.
- `scripts/dev.sh stop`, then `start`: PASS. Both containers stopped, then started, and `/web/login` returned 200 again.
- From PowerShell, `& "$env:LOCALAPPDATA\Programs\Git\bin\bash.exe" scripts/dev.sh status`: PASS.
- Failing test, checked after the stage report: PASS.
  - Setup: a temporary addon `azk_failcheck` with one deliberately failing test, kept outside the repository and mounted through a temporary compose override.
  - `scripts/dev.sh test azk_failcheck` logged "FAIL: TestDeliberateFailure.test_fails_on_purpose" and "1 failed, 0 error(s) of 1 tests when loading database 'azk_test'". Odoo exited with 1 and so did the script (37s).
  - The temporary files and `azk_test` were removed afterwards.
- `scripts/dev.sh logs`, checked after the stage report: PASS. It showed the server log; the check stopped it after 8 seconds with `timeout`.
- Browser check of login and the Apps list: PASS, reported by the user after the stage report (see the manual check below).
- NOT RUN: `scripts/dev.sh source` itself. The same copy was made earlier with the equivalent `docker run ... tar` command.
- Disk use: Docker images now total 6.75 GB and local volumes 3.46 GB. Drive C: had 18.0 GB free before Stage 01 and 10.2 GB after.

### Manual UI check (done by the user)

1. With the server running (`scripts/dev.sh status` shows `odoo` running), open http://127.0.0.1:8069/web/login.
2. Log in as `admin` with password `admin`.
3. Open Apps, remove the default "Apps" filter in the search bar, and search for `azk`.
4. Expected: "Odoo Partner Monitor" and "Dynamic Trial Balance" are both listed as installed.

Result: PASS, reported by the user on 2026-11-01 after the stage report ("logged in and searched, found the apps skeleton azk").
