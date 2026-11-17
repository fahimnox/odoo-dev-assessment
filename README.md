# Odoo Partner Monitor and Dynamic Trial Balance (Odoo 18.0 Enterprise)

Two Odoo addons written for an Odoo developer technical assessment:

- `azk_odoo_partner_monitor` (Exercise 1): reads the public Odoo Partners pages of www.odoo.com, stores partners, their status history and client references, and shows them on a filterable dashboard.
- `azk_dynamic_trial_balance` (Exercise 2): a Dynamic Trial Balance wizard with account, journal and analytic filters, hierarchy and currency options, and an on-screen Preview, PDF and XLSX built on the Enterprise report framework.

**Status (published on 2026-11-17, tag `submission-v1`):** both addons are built, tested and accepted from a clean checkout. 261 automated tests pass (147 and 114). Two requirements stay open: P-17.3, because the original views specification was never supplied, and T-19, because the candidate's own manual check of the final screens is still to be done. Repository: https://github.com/fahimnox/odoo-dev-assessment. Details: [Status](#13-status-complete-and-pending).

## Contents

1. [Scope](#1-scope)
2. [Target platform and pinned runtime](#2-target-platform-and-pinned-runtime)
3. [Dependencies and prerequisites](#3-dependencies-and-prerequisites)
4. [Installation from a clean checkout](#4-installation-from-a-clean-checkout)
5. [Everyday commands](#5-everyday-commands)
6. [A second, isolated copy, and reusing volumes](#6-a-second-isolated-copy-and-reusing-volumes)
7. [Configuration](#7-configuration)
8. [Features](#8-features)
9. [How the sync survives interruptions](#9-how-the-sync-survives-interruptions)
10. [Testing](#10-testing)
11. [Demo](#11-demo)
12. [Assumptions, open questions and limitations](#12-assumptions-open-questions-and-limitations)
13. [Status: complete and pending](#13-status-complete-and-pending)
14. [Evidence and documentation](#14-evidence-and-documentation)
15. [AI use](#15-ai-use)
16. [Repository layout](#16-repository-layout)
17. [License](#17-license)

## 1. Scope

- **Selected:** Exercise 1, the Odoo Partner Monitor (module name `azk_odoo_partner_monitor`, as the assessment requires), and Exercise 2, the Dynamic Trial Balance (module name `azk_dynamic_trial_balance`; the assessment gives no module name, so this is our choice, assumption A-03).
- **Not selected, on purpose:** Exercise 3, the Odoo 18 POS enhancements. The assessment asks for two of the three exercises (A-01). Nothing in this repository implements it.
- Every requirement is traced from the assessment to the code, the tests and the evidence in [docs/requirements_matrix.md](docs/requirements_matrix.md).

## 2. Target platform and pinned runtime

- **Edition: Odoo Enterprise.** Confirmed by the team lead, recorded on 2026-11-03 (clarification C-01, assumption A-08).
- **Major version: Odoo 18.0. Not confirmed.** The supplied Enterprise archive and the runtime are both 18.0, but no employer statement fixes the version. It is our assumption A-09; question Q-04 has not been asked yet.
- **Pinned builds** (the "matched pair", A-12):
  - Odoo Community: the official source `odoo/odoo` at commit `4e5027c159a9d9a8dd006618486c8e54cb1eb453` (2024-12-08), verified file by file against GitHub (21,846 files identical).
  - Odoo Enterprise addons: build `18.0+e.20241208`, the 620 Enterprise-repository modules of the company-supplied archive. They are proprietary and are kept outside this repository.
  - Docker image `odoo:18.0@sha256:9668abacd894276ed009e8db7db1d1ffb8068af6982f76a3400ed0d68e40432d`. It provides Python 3.12.3, the Python libraries and wkhtmltopdf 0.12.6.1; the official Community source is mounted read-only over the image's own Odoo package.
  - Docker image `postgres:16@sha256:5db6dac2ef5dcff512f4f00a009c3c332b9f2f28f24277175bf3e4a3d02ef83a` (PostgreSQL 16.15).
- **Why this pair:** the image's own 2026 core with the 2024 Enterprise addons fails a standard Enterprise test (`TestTrialBalanceReport.test_trial_balance_comparisons`); the matched pair passes all eight. Details: [docs/enterprise_transition.md](docs/enterprise_transition.md).
- **Tested host:** Windows 11 Pro, Docker Desktop (engine 29.9.2, Compose v5.6.1), Git Bash. Linux and macOS hosts were not tested.

## 3. Dependencies and prerequisites

### Declared dependencies

- **`azk_odoo_partner_monitor` 18.0.1.5.0:** depends on `mail` only; Python packages `requests` and `beautifulsoup4` (`external_dependencies`; versions 2.31.0 and 4.12.3 in the pinned image). No Enterprise dependency.
- **`azk_dynamic_trial_balance` 18.0.1.3.0:** depends on `account_reports`, an Enterprise module (license OEEL-1). In this build it brings `accountant` and `account_accountant`. Python package `XlsxWriter` (3.1.9 in the image). PDFs need wkhtmltopdf 0.12.6 with patched Qt (in the image).

### What you need outside this repository

- Docker with Compose v2 (Docker Desktop on Windows) and bash (Git Bash on Windows; in PowerShell, `bash` starts WSL instead).
- **The Odoo 18.0 Community source** of commit `4e5027c159a9d9a8dd006618486c8e54cb1eb453`: the folder that contains `odoo/` and `addons/`, for example extracted from https://github.com/odoo/odoo/archive/4e5027c159a9d9a8dd006618486c8e54cb1eb453.tar.gz. It is public.
- **The Odoo 18.0 Enterprise addons of build `18.0+e.20241208`:** the folder that directly contains `web_enterprise/` and `account_reports/`. They are proprietary: you need authorized access to Odoo Enterprise (for example through an Enterprise subscription or the employer). They are not part of this repository and must never be committed to it.
- **Internet access** only for the Partner Monitor's website downloads. The demo data, the tests and the Trial Balance work offline.
- **Resources:** the checks ran on a 16 GB machine with 0.5 to 2.7 GB of free RAM, so heavy steps were run one at a time. Keep several GB free on the Docker disk.
- The Enterprise database stays an unregistered trial. Registration needs the employer's subscription code and is not required for anything below.

## 4. Installation from a clean checkout

These are the steps of [docs/environment.md](docs/environment.md#quick-start-clean-checkout). In Stage 11 they were followed literally from a `git archive` export of the repository (no `.env`, empty Docker volumes) and passed; see [docs/acceptance_results.md](docs/acceptance_results.md). Run them from the repository root in bash.

Get the code first:

```bash
git clone https://github.com/fahimnox/odoo-dev-assessment.git
cd odoo-dev-assessment
git checkout submission-v1    # optional: the submitted commit; main may carry later documentation-only commits
```

1. `scripts/dev.sh setup`
   - The first run writes `.env` (ignored by Git) with random database passwords and `ODOO_EDITION=enterprise-20241208`, then stops with "needs ENTERPRISE_ADDONS in .env". No container is created yet.
2. In `.env`, set the two source folders (absolute paths, or relative to the repository root):
   - `ENTERPRISE_ADDONS=/path/to/enterprise-18.0-20241208`
   - `COMMUNITY_SOURCE_20241208=/path/to/odoo-4e5027c1`
   - They can also be given on the first run: `ENTERPRISE_ADDONS=... COMMUNITY_SOURCE_20241208=... scripts/dev.sh setup` writes them into the new `.env`.
3. `scripts/dev.sh setup` again. It pulls the two pinned images, starts PostgreSQL and creates the database `azk_ee24` with `web_enterprise`, `accountant` and both addons, **with their demo data**. In Stage 11: 92 modules in 8 min 44 s, 0 warnings.
4. `scripts/dev.sh start`, then open http://127.0.0.1:8071/web/login and log in with `admin` / `admin`. The server listens on 127.0.0.1 only.
5. `scripts/dev.sh test` runs the tests of both addons in a fresh database `azk_ee24_test` (expected: "0 failed, 0 error(s) of 261 tests"; 11 min 37 s in Stage 11).

Good to know:

- No manual database step is needed. Demo data is loaded at install: Partner Monitor demo records (labeled "Demo") and a Trial Balance demo company, "AZK Trial Balance Demo (EGP)".
- If `setup` stops part-way (for example on a wrong folder), fix the cause and run it again: it installs what is missing, `base` first if needed, and never drops the database.
- The Partner Monitor reads the live website only when a manager clicks Sync Now, or on its daily schedule from 02:00 UTC on the day after the install. To prevent every website request, tick Settings > Partner Monitor > Pause Website Downloads (section 7).
- If port 8071 is taken, set `ODOO_EE_20241208_HTTP_PORT` in `.env`. The server uses the same port inside its container, so that wkhtmltopdf can load the report styles.
- Troubleshooting: [docs/environment.md](docs/environment.md#troubleshooting).

### Installing into another Odoo 18.0 Enterprise server (not tested)

The Docker route above is the only one we ran. On an existing Odoo 18.0 Enterprise server (ideally the same build), the usual steps would be: copy the two folders of `addons/` into a folder on the server's `addons_path`; make sure `requests`, `beautifulsoup4` and `XlsxWriter` are importable by the server's Python and wkhtmltopdf 0.12.6 is installed; restart the server; then install both modules, for example with `odoo -d DB -i azk_odoo_partner_monitor,azk_dynamic_trial_balance --stop-after-init`, or from Apps after Update Apps List (developer mode). These steps were not run outside this repository's Docker setup.

## 5. Everyday commands

All from the repository root, in bash. Most commands first print the edition, service and database they use.

```text
scripts/dev.sh start | stop | restart | status | logs
scripts/dev.sh update azk_odoo_partner_monitor,azk_dynamic_trial_balance   # after changing XML, CSV or fields (dev DB azk_ee24)
scripts/dev.sh test                                    # both addons, fresh azk_ee24_test: 261 tests
scripts/dev.sh test azk_odoo_partner_monitor           # one addon: 147 tests
scripts/dev.sh test azk_dynamic_trial_balance          # one addon: 114 tests
scripts/dev.sh test azk_dynamic_trial_balance /azk_dynamic_trial_balance:TestBaseFixture   # one class
scripts/dev.sh clean-install azk_odoo_partner_monitor  # one addon alone in a fresh azk_ee24_clean
scripts/dev.sh clean-install azk_odoo_partner_monitor,azk_dynamic_trial_balance --without-demo
scripts/dev.sh shell                                   # Odoo shell on azk_ee24; pipe a script into it
scripts/dev.sh psql                                    # psql on azk_ee24 as the odoo role
scripts/restart_check.sh                               # crash-and-restart check, after a Partner Monitor test run
scripts/dev.sh help                                    # every command
```

- `test` fails when a test fails and also when Odoo reports "of 0 tests" (Odoo itself exits with 0 when nothing matched).
- `update` restarts the web server afterwards when it runs. Python-only changes need a restart; XML, CSV, manifest or field changes need an update.
- The helper refuses databases of another edition, and `reset-db` accepts only the disposable `azk_ee24_test` and `azk_ee24_clean`.
- The `community` edition (`ODOO_EDITION=community`, port 8069) is the Stage 01 baseline: it installs and tests the Partner Monitor only, because the Trial Balance needs Enterprise. The `enterprise` edition (port 8070) is a blocked earlier pair, kept for history. Both are described in [docs/environment.md](docs/environment.md#editions).

## 6. A second, isolated copy, and reusing volumes

Docker Compose names containers, networks and volumes after the **project name**. `compose.yaml` sets `name: azk-odoo-assessment`, so every checkout on one machine is the same project unless the name is overridden. The `-p` option, an exported `COMPOSE_PROJECT_NAME`, and a `COMPOSE_PROJECT_NAME=` line in `.env` all take precedence over `name:` (checked with `docker compose config` on 2026-11-16).

**To run a second copy next to an existing one** (Stage 11 ran its clean acceptance this way, as project `azk-stage11-acc` on port 8073):

1. Export or clone the repository into another folder.
2. Before the first `setup` there, give the copy its own name and port, either in the shell (`export COMPOSE_PROJECT_NAME=azk-copy`) or in its `.env` after setup step 1 (`COMPOSE_PROJECT_NAME=azk-copy`, `ODOO_EE_20241208_HTTP_PORT=8073`).
3. Follow section 4 there. The copy gets its own containers, network and empty volumes, so its database names (`azk_ee24`, ...) live in a separate PostgreSQL cluster.
4. Remove it later with `docker compose -p azk-copy down --volumes` from that folder. This deletes that copy's databases only.

**What happens if a new folder reuses an existing project's volumes with a new `.env`** (the same project name, new random passwords). Checked on 2026-11-16 on a throwaway project, `azk-s12-envcheck`, with the database service only, then removed:

- `docker compose up` **recreates** the existing database container (a new container id) but **keeps its volume**, with every database in it.
- PostgreSQL applies `POSTGRES_PASSWORD` and our role script (`docker/db/init/10-create-odoo-role.sh`) only when the data volume is empty. So the role `odoo` keeps its **old** password: a login with the new `.env` password failed with `FATAL: password authentication failed for user "odoo"`, and the old password still worked.
- Logins through the container's local socket need no password (also checked). `scripts/dev.sh setup` checks the databases that way, so it would find the old `azk_ee24` and report "already exists ... leaving it unchanged": a supposedly clean install would silently run on old data.
- The web server logs in over the network with the new password, so it would be refused. And by the same recreate rule, `up` would replace the other folder's web server container with one that mounts the new folder's `addons/` and configuration. These two consequences follow from the check above; they were not run with Odoo itself.

**How to recover:** put the original `.env` passwords back, or change the role's password inside the database container to the new value, or, only if the data may be lost, delete the volumes (`docker compose down --volumes`, which deletes every database of that project). For a real clean test, always use a new project name.

## 7. Configuration

Nothing is required after the installation; the defaults work. The settings that matter:

### Partner Monitor

- **Access groups** (Settings > Users & Companies > Users, category "Partner Monitor"):
  - **Reader:** the dashboard, partners, countries, status history, references, runs and their notes. Read-only.
  - **Manager:** also work items and errors, and four actions: Sync Now, Retry (failed work items), and Mark for Re-scrape on countries and on partners.
  - Nobody can edit scraped data, history or sync checkpoints through the access rules; only the sync engine writes them.
- **Settings > Partner Monitor** (Partner Monitor > Configuration > Settings; system administrators only):
  - **Pause Website Downloads** (off by default): while ticked, the jobs keep their queue and download nothing; open runs show "waiting" and the recipient gets one note per run. Tick it on any machine that must not crawl the website. A full sync is estimated at about 330 listing pages and, the first time, about 4,500 partner pages, at one request every 3 seconds or more (an estimate, never run here).
  - **Failure Recipient:** the internal user who receives the note about a failed or partial run. Default: the administrator. An invalid value falls back to the administrator.
- **Schedules** (Settings > Technical > Automation > Scheduled Actions, developer mode): "Partner Monitor: Daily Discovery" (daily, first run 02:00 UTC the day after the install), "Partner Monitor: Sync Worker" (every 10 minutes, and woken at once by Sync Now and Retry), "Partner Monitor: Country Validation" and "Partner Monitor: Reference Validation" (every 6 hours).
- **Tuning** (Settings > Technical > Parameters > System Parameters, developer mode; optional): `azk_odoo_partner_monitor.worker_batch_size` (units per batch, default 20) and `azk_odoo_partner_monitor.worker_time_budget` (seconds after which a batch starts no new unit, default 60).

### Failure notifications: chatter, inbox and email

When a sync run ends **partial** (some work units failed) or **failed** (none succeeded), the module posts **one internal note** on that run, addressed to the Failure Recipient. Three different things are involved:

- **The chatter message.** The note is always stored on the run's chatter (Partner Monitor > Sync > Runs > the run). It holds the counts, the failed scopes with their last error, the retry policy and the recovery actions. Anyone who may read the run sees it there.
- **The inbox notification.** If the recipient's preference is **"Handle in Odoo"**, Odoo also puts the note in that user's Discuss inbox.
- **The email.** If the preference is **"Handle by Emails"** (Odoo's default, including for the administrator), Odoo sends the note by email instead, through an outgoing mail server. **Without a configured mail server the email fails** (its notification status becomes "exception") and nothing reaches the user's inbox; the note stays on the run's chatter. This happened to the administrator in the Stage 11 acceptance (observation O-01).

So, for the recipient to be told, do one of these:

- **Configure an outgoing mail server:** Settings > General Settings > Emails > Use Custom Email Servers > Outgoing Email Servers (or Settings > Technical > Email > Outgoing Mail Servers in developer mode), and keep "Handle by Emails"; or
- **Choose "Handle in Odoo"** for the recipient: the user's own avatar menu > Preferences > Notification, or, as an administrator, Settings > Users & Companies > Users > the user > Preferences tab > Notification.

The local Docker setup has no mail server, so the second option is the one verified here: in Stage 11, the configured recipient with "Handle in Odoo" found the note in the inbox. A run that waits (paused downloads, or a rate limit) gets one "waiting" note the same way. A run is never notified twice, also not after a manager's Retry.

### Dynamic Trial Balance

- **Access:** users need the group the standard Trial Balance requires, `account.group_account_readonly` ("Show Accounting Features - Readonly"). Users with full accounting features have it; billing-only users do not. Without it, every path (wizard, preview, downloads) is refused.
- **Report company:** a report covers exactly one company, which must be active in the company switcher (top right). Branches are separate reports (D-16).
- **Analytic filter:** the Analytic Accounts field and the preview's analytic menu appear only with Accounting > Configuration > Settings > Analytic Accounting (D-62). If the field is missing, enable that setting.
- Nothing else to configure. The wizard is under Accounting > Reporting > Audit Reports > Dynamic Trial Balance.

## 8. Features

### Partner Monitor (`azk_odoo_partner_monitor`)

- **Data model** (the assessment's four models and fields, plus three sync models):
  - `azk_odoo_partner_monitor.country`, `.partner`, `.status.history` and `.reference`, with the assessment's field names and types;
  - `.sync.run` (with a chatter), `.work.item` (the durable queue) and `.sync.error` (one row per failed try).
  - Identities are the website's own ids, unique in the database; unknown measurements are kept apart from real zeros.
- **Scraping:** `services/http_client.py` downloads pages with `requests` (bounded timeouts, size and retries, at least 3 s between requests, robots.txt rules, gzip only); `services/parsers.py` reads them with BeautifulSoup; `models/ingest.py` stores the results.
- **History:** first seen date, one status-history row per real change (`initial`, `promoted`, `demoted`), references added and removed with their dates.
- **Two-level validation:** the partners found for a country are compared with the count the site shows; the active references of a partner are compared with its reference count. A mismatch sets the re-scrape flag, and two separate jobs re-read flagged countries and partners. The "empty country returns every partner" case of the site is detected and never stored as data.
- **Dashboard** (the app's first menu, Partner Monitor > Dashboard): Status (Gold, Silver, Ready), Year First Seen and Country filters shared by all four charts; Top 5 and Bottom 5 countries by active partners, stacked by status; the project-size distribution (Below 5, 5 to below 11, 11 to below 25, 25 and above, Unknown) of the same two cohorts; the sync state; website data and demo data shown separately, demo data with a banner.
- **Views:** list, form and search views for every model; pivots for partners, status history and references; graphs for partners and status history; menus Dashboard, Partners, Countries, Status History, References, Sync (Runs, Work Items, Errors) and Configuration.
- **Demo data:** 13 countries (12 active), 50 partners (47 active), 57 history rows and 6 references, all named "Demo ..." and flagged as demo, with reserved ids that website data can never use.

### Dynamic Trial Balance (`azk_dynamic_trial_balance`)

- **Wizard** (Accounting > Reporting > Audit Reports > Dynamic Trial Balance): Date From, Date To and Company; Posted Entries (always on), Include Unposted Entries, Hierarchy and Subtotals, Hierarchy Only Parents with Account Level Up To (1 to 5), Skip Zero Balance, Show Amount Currency; Accounts (code prefixes, as tags), Journals (one journal) and Analytic Accounts (one account), with the assessment's help texts word for word. Buttons: Preview, PDF, XLSX.
- **One calculation for every output:** the engine (`models/trial_balance_engine.py`) computes one normalized result as the requesting user. Our `account.report` record and custom handler feed it to the standard Enterprise report view, its PDF export and its XLSX export, so the three outputs cannot disagree.
- **Columns:** Initial Balance, the period and End Balance, each with Debit, Credit and Balance; with Show Amount Currency, rows per account and transaction currency and an Amount Currency column, with one total per currency.
- **Preview:** the standard report view with its date filter, Draft Entries, search and folding, plus our filter bar: the report company, a "Trial Balance" menu (hierarchy, only parents and level, Skip Zero Balance, Show Amount Currency), account prefixes, journal and analytic account. Each change recalculates.
- **PDF:** landscape, the report company's name and address, "Period: From ... to ...", every option, the column groups repeated on every page. **XLSX:** the options above the table, numbers stored as numbers with a number format, codes as text, group rows indented, a frozen header.
- **Conventions** (written down in [docs/calculation_contract.md](docs/calculation_contract.md) before any calculation code): those of the standard Enterprise Trial Balance for opening balances, the fiscal-year carry-forward, draft and cancelled entries, journals, analytic accounts and the hierarchy.
- **Demo data:** the company "AZK Trial Balance Demo (EGP)" (Egypt, EGP) with 16 entries (13 posted, 2 draft, 1 cancelled), entries in USD and EUR, a 60/40 analytic distribution and a key across two analytic plans, and account groups five levels deep above Bank (1 > 10 > 101 > 1014 > 10140). It reproduces the assessment's worked example (section 10).

## 9. How the sync survives interruptions

The full design is in [docs/resilience.md](docs/resilience.md); the parts the assessment asks about:

- **Interruptions.** The work is split into durable work items: the country list, one country's listing pages, one partner's page. Four scheduled jobs are separate: a daily discovery and two validation jobs only queue work; one worker job processes the queue in bounded batches (at most 20 units or 60 seconds). Odoo's scheduler commits after each batch, which is the only point where work becomes durable. Each unit runs in its own savepoint, so one failed partner or country never stops the batch. Units are claimed with row locks (`FOR NO KEY UPDATE SKIP LOCKED`) that disappear with a crashed transaction, so nothing stays half-claimed.
- **Recovery without repeating work.** Finished units are never run again; after a crash only the batch that was open is replayed. Every write is keyed on the website's ids with database uniqueness, so a replay creates nothing new. Shown by `scripts/restart_check.sh`: the worker process is killed with SIGKILL in the middle of a batch, then restarted; 12 of 12 checks pass (no duplicate history row, reference or note).
- **Pulling only what changed.** The site sends no `ETag` or `Last-Modified` header, so conditional requests are impossible. Listing pages are read daily, because they are how new partners are found. A partner's own page is read only when the partner is new, when the metrics on its listing card changed (a hash of retention rate, project sizes and reference count), when it was flagged by a mismatch, or when it was last read more than 7 days ago.
- **Failures.** A failed unit is retried at most 5 times (15, 30, 60 and 120 minutes apart), then stays "failed" and visible until a manager's Retry. Every failed try is logged and stored as an error row. A failed or partial run notifies the configured user once (section 7).
- **Partial results never delete anything.** Countries, partners and references are deactivated or closed only after a complete, validated snapshot of their scope. A failed or incomplete read keeps the existing data and sets the re-scrape flag.
- **Overlap.** Odoo runs one copy of each job at a time; claims skip locked units; a database index allows one pending unit per target; Sync Now and the daily job add nothing while a country list is already queued.

## 10. Testing

### Automated tests: 261 test methods

`scripts/dev.sh test` installs both addons with demo data in a fresh database and runs every test. In the Stage 11 acceptance (2026-11-16, clean export, final code): **"0 failed, 0 error(s) of 261 tests"**, no skipped test, no warning, every test file imported.

- **Partner Monitor, 147 tests in 13 files:** URL rules (8), parsers on saved live pages (13), ingestion (18), models (12), status history (13), references (7), security (12), notifications (7), the worker (21) and its concurrency on two real database connections (2), the page download with a fake HTTP session (16), the dashboard (16) and the install (2).
- **Dynamic Trial Balance, 114 tests in 12 files:** the wizard and option validation (16), the base fixture (13), the standard report's conventions (7), the advanced fixtures (34), date boundaries (8), engine access (5), fiscal years and branches (9), the outputs (11), report access and tampered options (3), demo data (4), the standard reports unchanged (2) and the install (2).
- **What the numbers mean.** 261 counts executed test methods: Odoo's summary line "of 261 tests" and one "Starting ..." line per test method. Odoo's per-module statistics lines say 177 and 150 "tests", because `odoo/tests/suite.py` also records each test class's `setUpClass` and `tearDownClass`: 147 + 2 x 15 classes = 177, and 114 + 2 x 18 classes = 150. Compare 147 and 114, not 177 and 150.
- **No network in tests.** The Partner Monitor tests use seven trimmed pages saved from the live site on 2026-11-08 ([fixtures README](addons/azk_odoo_partner_monitor/tests/fixtures/README.md)) and synthetic answers built in code (login pages, rate limits, cut-off pages). Odoo's test framework blocks real HTTP requests.

### The Trial Balance against a known dataset

- The fixtures are real, balanced journal entries in fresh test companies: TB-BASE, TB-X (across a fiscal-year boundary), TB-Z (zero activity), TB-C (currencies), TB-A (analytic), TB-M (two companies), TB-R (restricted access), TB-H (hierarchy), TB-D (date boundaries), TB-F (a July-to-June fiscal year) and TB-B (branches).
- Their expected numbers were **calculated by hand** and written as constants in `addons/azk_dynamic_trial_balance/tests/common.py` (TB-F and TB-B in `test_fiscal_years_and_branches.py`), never produced by a report.
- The tests check three things: the standard Enterprise Trial Balance gives the hand-calculated numbers on the same data; our engine gives them too; and the preview lines, the PDF content and the XLSX cells equal the engine's result.
- **The assessment's worked example** (TB-BASE, and the demo company, January 2026): Bank opens at 1,000.00, receives 500.00 and pays 300.00, so it ends at **1,200.00 with posted entries only**. A draft payment of 200.00 makes it **1,000.00 with drafts included**. A cancelled payment of 400.00 and a February fee of 50.00 never count.
- What is and is not compared with the standard report is listed in [docs/calculation_contract.md](docs/calculation_contract.md#14-fixtures-expected-results-and-native-comparisons). We do not claim complete parity with the standard Trial Balance.

### Other checks that ran (by the AI agent)

- **Clean install:** from `git archive` exports, both addons alone, together, with and without demo data, and an upgrade from the previous release that kept every history row and reference (Stage 11).
- **Browser checks** with headless Chrome through the DevTools protocol (scripts in `scripts/`): the dashboard 7 of 7, the wizard 7 of 7, the preview and both downloads 20 of 20 (Bank 1,200.00, then 1,000.00 with Draft Entries), the Partner Monitor demonstration 7 of 7 (Stage 11), and the analytic filter as a read-only accountant 6 of 6 (Stage 10).
- **Access over HTTP** as four non-admin users and an anonymous visitor, including both downloads and tampered options: 24 of 24.
- **The standard Trial Balance** on Odoo's own demo accounting data: 6 of 6 cases equal (`scripts/tb_engine_vs_native.py`). The standard `account_reports` tests of the Trial Balance and of the annotation export still pass with our addon installed (11 of 11, Stage 10).
- **Crash and restart:** 12 of 12 (above).
- **Live website:** small, bounded samples only, every request allowed by robots.txt: 9 manual requests on 2026-11-08, 23 on 2026-11-15 (the live check through the worker and diagnostics), 7 on 2026-11-16 (the acceptance demonstration). Each one is listed in [docs/live_site_notes.md](docs/live_site_notes.md). A full crawl was never run, on purpose.

### Manual checks

- The checks above were scripted and run by the AI agent, and their screenshots and PDF renders were looked at by the agent. They are not a person's judgment.
- The candidate reported a browser check of an earlier Enterprise environment (Stage 01B, 2026-11-04, without detailed results). **The candidate's own manual check of the final screens is still pending** (test plan TP-G-05); the steps are those of the demo script.

Full results: [docs/test_results.md](docs/test_results.md) and [docs/acceptance_results.md](docs/acceptance_results.md). Test plan: [docs/test_plan.md](docs/test_plan.md).

## 11. Demo

[docs/demo_script.md](docs/demo_script.md) is a 7-minute walkthrough with exact menus, the expected numbers, one failure-and-recovery story and code pointers. It labels every piece of data as DEMO (installed demo records), LIVE (read from www.odoo.com), FIXTURE (saved pages used by tests and checks) or SIMULATED (a network outage without any request), and it has an offline fallback.

## 12. Assumptions, open questions and limitations

### Defaults are assumptions, not approvals

Where the assessment was silent or ambiguous, we chose a default and wrote it down ([docs/assumptions.md](docs/assumptions.md): assumptions A-01 to A-22, decisions D-01 to D-70). Apart from the Enterprise edition (C-01), **none of them was approved by the assessor or the team lead.** The most visible ones:

- Odoo 18.0 as the major version (A-09).
- The module name `azk_dynamic_trial_balance` (A-03); author `fahimnox` and license LGPL-3 in the manifests (A-06).
- The standard Enterprise Trial Balance as the reference for opening balances, the fiscal-year carry-forward and draft entries (A-14).
- **Whole-item analytic filtering:** a journal item counts at its full amount when its distribution contains the selected analytic account, as in the standard report; proportional allocation by percentage was not chosen (A-15, D-07).
- One journal and one analytic account, as the assessment's field types say (D-02); Date From, Date To and one Company added to the wizard (D-03).
- Project-size buckets below 5, 5 to below 11, 11 to below 25, 25 and above, and Unknown (D-05); "Year First Seen" is the year our scraper first saw the partner (D-14).
- The failure note goes to the administrator by default, because Odoo installs modules as the superuser and cannot tell who clicked Install (D-19).

### Open questions (not yet asked)

- **Q-02:** the original views specification, the Trial Balance wizard mockup and the `azk_zkteco_machine_proxy` documentation example.
- **Q-03:** is the standard Enterprise Trial Balance the intended reference, including its carry-forward and its whole-item analytic filter?
- **Q-04:** is Odoo 18.0 the required major version?
- **Q-05:** Enterprise addons matching a newer core, as an alternative to the 2024 pair (environment only, not blocking).
- **Q-06:** which license should the Trial Balance addon declare, given that it depends on the OEEL-1 module `account_reports`?

### Inputs that were never supplied

- **M-01:** the "original specification" of the Partner Monitor views. Our views, filters, groupings and pivots are our own proposal (A-16), so requirement P-17.3 ("the required filters, groupings and pivot configurations remain the same") cannot be checked and stays IN PROGRESS.
- **M-02:** the Trial Balance wizard mockup. The layout is ours; the fields follow the assessment's text.
- **M-03:** the `azk_zkteco_machine_proxy` documentation example. This README follows the assessment's own list of README contents instead.

### Measured limitations

- **Live website:** only the bounded samples of section 10 were read. A full sync has never run from this machine, so its duration, the site's behavior under a long crawl and rate limits in practice are unknown. Downloads are paused on the development database.
- **No conditional requests:** the site offers none, so every listing page is read daily in full.
- **Storage cost per card** (review finding RF-11): storing a listing costs 7 queries per partner card on a first read and 4 on a repeat (benchmark at 100 and 1,000 cards). The dashboard ran 21 queries with 1,150 partners.
- **Long units** (RF-12): one country is one unit. The largest country on 2026-11-08, the United States, has 14 listing pages: at least 42 s at the enforced spacing, about 50 s with transfers. With multi-process workers, Odoo stops a scheduled call after 120 s by default (`limit_time_real`); a bigger country would need page-level checkpoints. Multi-process mode was not tested.
- **The Trial Balance** ran a constant 15 to 16 queries per report at 2,000 and 10,000 journal items (0.03 to 0.07 s); larger volumes were not measured.
- **One company per report:** branches are not added together, unlike the standard report (D-16).
- **Parity** with the standard Trial Balance is claimed only for the compared cases; currency rows, Skip Zero Balance, prefixes and the level limit have no standard equivalent and are tested against hand-calculated numbers only.
- **Environment:** one Windows host; the matched 2024-12-08 pair only; an unregistered trial database; no outgoing mail server; the Odoo `admin` / `admin` login, acceptable only because the server listens on 127.0.0.1.

## 13. Status: complete and pending

**Complete** (implemented, tested, with evidence in the requirements matrix):

- Exercise 1: models, scraping, history, two-level validation, the empty-country case, scheduled jobs, resilience, failure notes, dashboard with four charts and shared filters, views, security and demo data.
- Exercise 2: the wizard with every field and help text, the calculation engine, the Preview, PDF and XLSX, access on every path, and demo data with posted, draft, cancelled, foreign-currency and analytic entries and a five-level hierarchy.
- Packaging: a pinned Docker setup, a clean-checkout quick start (accepted in Stage 11), this README, the documentation and the AI logs.
- Publication (G-01): this public repository, published in Stage 15 (2026-11-17). The submitted commit is tagged `submission-v1`; it equals the reviewed release candidate `submission-rc1` plus documentation.

**Pending:**

- **P-17.3:** checking the views against the original specification, which was never supplied (Q-02). IN PROGRESS.
- **T-19, the candidate's own manual check** of the final screens (TP-G-05): IN PROGRESS until it is done and recorded in section 10.
- **The license** (Q-06): still undecided at publication (section 17).
- **Answers to Q-02 to Q-06.** Until then the defaults above stand.
- Not done, by choice: a full live crawl; the Partner Monitor test suite on the Community baseline (optional, TP-G-03).

The final requirement matrix and its status summary: [docs/requirements_matrix.md](docs/requirements_matrix.md). The release checklist: [docs/release_checklist.md](docs/release_checklist.md).

## 14. Evidence and documentation

- [docs/requirements_matrix.md](docs/requirements_matrix.md): every requirement, its interpretation, implementation, tests, evidence and status.
- [docs/assumptions.md](docs/assumptions.md): assumptions, decisions, version notes, open questions, missing inputs.
- [docs/architecture.md](docs/architecture.md): components, models and the security boundary, with dated "as built" sections.
- [docs/resilience.md](docs/resilience.md): the sync's jobs, units, commit boundary, replay, retries, validation and notifications.
- [docs/calculation_contract.md](docs/calculation_contract.md): the Trial Balance arithmetic, the worked example, the comparisons and the intended differences.
- [docs/test_plan.md](docs/test_plan.md), [docs/test_results.md](docs/test_results.md), [docs/acceptance_results.md](docs/acceptance_results.md): what was planned, run and observed.
- [docs/review_findings.md](docs/review_findings.md): the engineering review (Stage 10), findings RF-01 to RF-15.
- [docs/live_site_notes.md](docs/live_site_notes.md): every request made to www.odoo.com, robots.txt and the selectors.
- [docs/environment.md](docs/environment.md) and [docs/enterprise_transition.md](docs/enterprise_transition.md): the runtime, its pins and how it was chosen.
- [docs/demo_script.md](docs/demo_script.md) and [docs/release_checklist.md](docs/release_checklist.md).
- [docs/samples/](docs/samples/): PDF and XLSX files exported from the demo company (Stage 09). [docs/screenshots/](docs/screenshots/): screenshots taken by the browser checks (Stages 06 to 10).
- [docs/STATE.md](docs/STATE.md) and [docs/handoffs/](docs/handoffs/): the state and a handoff for every stage.

## 15. AI use

- The assessment encourages generative AI and asks for the prompts and outputs. This solution was built with **Claude Code** (Anthropic's terminal agent), model **Opus 5.5** (`claude-opus-5-5`), as each log records.
- The candidate chose the exercises, ran the work one stage at a time with written stage prompts, relayed the team lead's clarification (Enterprise), made the recorded scope decisions (for example deferring the page download in Stage 04, until Stage 10), and reviewed the results. The AI agent wrote the code, tests and documentation, and ran the commands and checks reported here. The scraping logic was generated with AI, as the assessment asks (P-03.1).
- [docs/ai/](docs/ai/README.md) holds, for every stage, the user's prompts and the agent's visible answers verbatim, a summary of its tool activity (labeled as a summary), and a table of the agent's mistakes and how they were found and corrected. Hidden reasoning, system prompts and raw tool output are not included. Redactions (local paths) are listed there.
- The candidate's learning stages are not finished: Stage 13 (a walkthrough of this code) is paused after its first section, and Stage 14 (a mock interview) is deferred until after publication. They prepare the candidate and change nothing in the submission unless they find a defect. The log of Stage 15, which records this publication, follows the submitted commit on `main`.

## 16. Repository layout

```text
addons/azk_odoo_partner_monitor/     Exercise 1 (models, services, views, static, data, demo, tests)
addons/azk_dynamic_trial_balance/    Exercise 2 (models, views, static, data, demo, tests)
compose.yaml, config/, docker/       the pinned Docker setup (no secrets; .env is created locally)
.env.example                         the template of the local .env
scripts/dev.sh                       setup, start, update, test and the other commands
scripts/*.py, scripts/*.sh           checks: browser, access, restart, live sample, benchmarks, acceptance
docs/                                the documentation listed in section 14
docs/ai/                             the AI logs
AGENTS.md                            the working rules given to the AI agent
```

Not in this repository, on purpose: Odoo itself, the Enterprise addons, `.env`, databases and filestores, the assessment PDF and the prompt kit.

## 17. License

Both manifests declare **LGPL-3**, an unconfirmed default (A-06). The Trial Balance addon depends on the proprietary Enterprise module `account_reports` (OEEL-1), so its license is open question Q-06. No license file is included until that is decided. This was still undecided at publication (Stage 15, 2026-11-17): the repository is public without a license file, and the manifests still declare LGPL-3.
