# Stage 01 handoff (English)

Stage 01: build and verify the local development environment. Written on 2026-11-01 from the commands and results recorded in `docs/environment.md`.

## Status

- Stage 01 is complete. One manual check is still open: the browser login and the Apps list (NOT RUN, see below).
- No business features are implemented. Both addons are installable skeletons with smoke tests.
- Tests: `scripts/dev.sh test` ran 4 tests, with 0 failed and 0 errors.
- Next stage: 02, requirements, assumptions, architecture and acceptance plan.

## What was set up

- Route: Docker Compose, with the official images pinned by digest:
  - `odoo:18.0@sha256:9668abacd894276ed009e8db7db1d1ffb8068af6982f76a3400ed0d68e40432d`: Odoo 18.0-20261015, Ubuntu 24.04.5, Python 3.12.3, wkhtmltopdf 0.12.6.1 with patched Qt, XlsxWriter 3.1.9, beautifulsoup4 4.12.3, requests 2.31.0.
  - `postgres:16@sha256:5db6dac2ef5dcff512f4f00a009c3c332b9f2f28f24277175bf3e4a3d02ef83a`: PostgreSQL 16.15.
- Why: Docker Desktop was already installed and running, and the image already contains wkhtmltopdf and every needed library. Nothing on the host had to change. The host PostgreSQL 18 service and another project's containers (ports 5433, 8000, 9000) were left alone.
- The official requirements were checked against both the documentation and the pinned source: Python 3.10 or later, PostgreSQL 12 or later, wkhtmltopdf 0.12.6, and no connection as `postgres`.
- The matching Odoo source was copied from the same image to the kit's `runtime/odoo18` folder, outside the repository and without translations, for reading API details.
- Security:
  - Odoo is published only on 127.0.0.1:8069, and PostgreSQL is not published.
  - Odoo connects as the role `odoo`, which can create databases but is not a superuser.
  - Passwords live only in the ignored `.env`.
  - The database manager is disabled (`list_db = False`).
- Databases:
  - `azk_dev`: development, with demo data. The web server serves only this one.
  - `azk_test`: recreated by every test run.
  - `azk_clean`: recreated by every clean install.
  - The reset command accepts only `azk_test` and `azk_clean`.
- Addons, under `addons/`:
  - `azk_odoo_partner_monitor`: depends on `mail`, external dependencies `requests` and `beautifulsoup4`, application.
  - `azk_dynamic_trial_balance`: depends on `account`, external dependency `XlsxWriter`.

## Commands run and results

- `scripts/dev.sh setup`: PASS. 48 modules loaded, 3m06s.
- `GET /web/login`: 200. JSON-RPC login as `admin` returned uid 2, and both addons read back as installed. Calls without a session were refused. PASS.
- Database manager: its page shows the "disabled" notice, and the `db` service refused `list` and `drop` with AccessDenied. PASS.
- Shell query on `azk_dev`: role `odoo`, PostgreSQL 16.15, both addons installed with demo data. PASS.
- PDF prerequisite: wkhtmltopdf state `ok`, and a real 1-page PDF rendered through QWeb, with the header and the "1/1" page counter. PASS.
- `scripts/dev.sh test`: 4 tests, 0 failed, 0 errors. PASS.
- Single test by tag: exactly 1 test ran. PASS.
- No-match run: Odoo exited 0 with "0 tests"; the script rejected it with exit code 1. PASS (the guard works).
- Each addon installed alone in a fresh `azk_clean`: PASS. Installing the second addon into that database later also worked.
- `update` with the server running (reload and restart): PASS. `reset-db azk_dev` was refused: PASS. The stop/start cycle: PASS.
- NOT RUN: the browser check, a deliberately failing test, `scripts/dev.sh source` itself (an equivalent command made the copy), and `logs`.

## Manual check for the user (NOT RUN until reported)

1. Open http://127.0.0.1:8069/web/login while the server runs.
2. Log in as `admin` with password `admin`.
3. Open Apps, remove the default "Apps" filter, and search for `azk`.
4. Expected: "Odoo Partner Monitor" and "Dynamic Trial Balance" are both installed.

## Open items and assumptions

- A-04 to A-07 were added: Docker Compose route, addons in `addons/`, manifest author `fahimnox` with license LGPL-3 (unconfirmed default), demo data in all databases.
- The admin/admin login and Odoo's default master password are acceptable only because everything listens on 127.0.0.1. Every database-management call is refused anyway.
- Drive C: has 10.2 GB free (18.0 GB before Stage 01).
- Still unconfirmed from Stage 00: Odoo 18 Community (A-02), and questions Q-01 to Q-03.

## How the Odoo pieces differ

- `addons_path`: the folders Odoo scans for modules. Here it is `/mnt/extra-addons` (our `addons/`), plus the core and data-dir folders that Odoo adds itself.
- `__manifest__.py`: the module's metadata, dependencies, data files to load, and external Python packages.
- `__init__.py`: imports the module's Python code. Anything it does not import never runs.
- Install creates tables and loads data. Update reloads data and applies field changes. A restart reloads Python code only.
- In practice: Python-only change -> restart; XML, CSV, manifest or field change -> update.

## Comprehension questions

1. You add a new field to an existing model and only restart the server. What happens when Odoo reads that field, and which command fixes it?
2. Why does `scripts/dev.sh test` treat "of 0 tests" as a failure, even though Odoo exits with code 0?
3. The image entrypoint passes the database password as a command-line argument. Where is that visible, and why is it acceptable here but not on a shared server?

## Next stage

```text
Read prompts/02_requirements_and_design.txt and execute Stage 02 only, following solution/AGENTS.md.
```
