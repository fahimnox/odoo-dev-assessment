# Acceptance results (Stage 11)

_2026-11-16 (times in UTC). Clean-checkout acceptance of the submission, run by the AI agent on this machine. The user's own browser check is still pending; see "UI steps"._

_Update, Stage 12 (2026-11-16): the README now exists, and the requirement rows marked "Stage 12" below have their final status in [requirements_matrix.md](requirements_matrix.md). Stage 12 also checked the consequence of reusing a project's volumes with a new `.env` on a throwaway project ([test_results.md](test_results.md)). This record is otherwise unchanged._

## Verdict

- **Installation:** both addons install from a clean export of the repository, following the documented quick start and their declared dependencies, on the pinned Enterprise runtime: alone, together, with and without demo data. Every install and update log has 0 WARNING, ERROR or CRITICAL lines.
- **Demo data** loads automatically on a fresh install with demo data, and is absent without it.
- **Upgrade:** an upgrade from the previous release (Stage 09) keeps every history row, reference, partner, country and demo journal entry (equal fingerprints).
- **Tests:** 261 of 261 pass in a fresh database (147 Partner Monitor, 114 Trial Balance), the Stage 10 baseline; no skipped, missing or uncollected test.
- **Demonstrations and access:** every check passes:
  - the restart check, 12 of 12;
  - the dashboard on demo data, 7 of 7;
  - the Trial Balance wizard, 7 of 7;
  - the preview and downloads, 20 of 20;
  - the comparison with the standard Trial Balance, 6 of 6;
  - the Partner Monitor demonstration in the browser, 7 of 7;
  - the access checks over HTTP, 24 of 24.
- **Defects found:** three packaging and documentation defects, now fixed (AC-01 to AC-03, below). The first documented command did not work in a fresh checkout. No addon code changed in Stage 11.
- **Not done by this stage:**
  - the README (Stage 12) and publication (Stage 15);
  - the user's manual check (TP-G-05);
  - the team-lead questions Q-02 to Q-06;
  - P-17.3, which needs the original views specification.

## Tested code and environment

- **Commits:**
  - baseline `e54214b` (Stage 10);
  - setup fixes `a203291` and `3b92f98` (scripts/dev.sh, .env.example, environment.md only);
  - the Stage 11 commit adds this document, the acceptance scripts and the other documentation. `git diff 3b92f98 -- addons/` is empty for the final commit, so the installation evidence applies to it unchanged.
- **Isolated exports** (`git archive`, outside the repository, under `<kit-root>/runtime/acceptance/`):
  - `e54214b`: the first run exactly as documented;
  - `3b92f98`: every other install, update, test, restart and browser check. 184 files, no `.env`;
  - `564b71b` (Stage 09): the old release of the upgrade check.
- **Acceptance scripts:**
  - new: `scripts/acceptance_state.py`, `acceptance_users.py`, `acceptance_upgrade_seed.py`, `acceptance_pm_demo.py`, `acceptance_pm_ui_check.py`, `acceptance_access_check.py`;
  - changed: `scripts/pm_live_check.py` (option to keep the sample);
  - they ran from the working tree and are committed in the Stage 11 commit. The existing checks (`ui_smoke_check.py`, `tb_wizard_smoke_check.py`, `tb_preview_smoke_check.py`, `tb_engine_vs_native.py`, `restart_check.sh`) ran from the export.
- **Runtime:**
  - the images pinned by digest in `compose.yaml` (Odoo 18.0 image, PostgreSQL 16.15);
  - the official Community source `odoo/odoo@4e5027c1` and the Enterprise addons of build 18.0+e.20241208, both outside the repository;
  - Docker Desktop engine 29.9.2, Compose v5.6.1, Windows 11 Pro.
- **Isolation:**
  - a separate Compose project, `COMPOSE_PROJECT_NAME=azk-stage11-acc`, with its own empty volumes (a new PostgreSQL cluster), on port 8073 (`ODOO_EE_20241208_HTTP_PORT` in its `.env`);
  - its databases have the development names (`azk_ee24`, `azk_ee24_test`, `azk_ee24_clean`), but in that other cluster. Scripts that write to them check the database creation date, because the name cannot tell them apart;
  - the development project (`azk-odoo-assessment`) was started at 13:22 and its eight databases were listed (azk_clean, azk_dev, azk_ee24, azk_ee24_clean, azk_ee24_test, azk_ent, azk_ent_test, azk_test). It was stopped during the heavy steps for memory and restarted at the end. Its databases were not changed: the only access was a few read-only SQL queries on `azk_ee24` at the start (module versions, Partner Monitor settings and counts).
- **Resources:** C: had 46 GB free throughout. Free RAM was sampled every 15 s; the lowest value was 0.48 GB, during the first full setup. Other applications used most of the 16 GB.
- **Logs:** the full logs are private, under `<kit-root>/runtime/logs/stage11/`, named by step (a01 to j05).

## What a clean install proves, and what it does not

It proves that:
- the committed files, the documented steps and the declared dependencies are enough on the pinned runtime, without any manual database step;
- demo data loads at install and is labeled;
- the tests pass in a database that only Odoo and our modules created;
- an upgrade from the previous release keeps the data;
- the outputs (preview, PDF, XLSX) and the access rules work on a server that was never used for development.

It does not prove:
- behavior on other Odoo builds. Only the matched pair was used; the 2026 core with the 2024 Enterprise addons fails a vendor test, see [environment.md](environment.md);
- behavior on other hosts or operating systems;
- a production setup: multi-process workers (RF-12), a reverse proxy, an outgoing mail server, backups;
- a full crawl of the live website. Only a bounded sample of 7 requests was read;
- performance beyond the modest Stage 10 benchmark;
- registration of the Enterprise database (it is a trial);
- the user's own judgment of the screens and files.

## Findings of this stage

Defects in the submission, fixed and verified:

- **AC-01, high: the first documented command failed in a fresh checkout.**
  - Location: `scripts/dev.sh` (default edition, `ensure_env`, `main`), `.env.example`, `docs/environment.md`.
  - Evidence: in the export of `e54214b`, `scripts/dev.sh setup` wrote a `.env` with `ODOO_EDITION=community` and exited with 255: "You try to install module "azk_dynamic_trial_balance" that depends on module "account_reports". But the latter module is not available in your system." (log a01, 13:28 to 13:29).
  - Fix (`a203291`): the default edition is `enterprise-20241208`. `setup` writes `.env` before checking the source folders and keeps folders given on the first run. The Community baseline installs and tests the Partner Monitor only. `environment.md` has a quick start for a clean checkout.
  - Verification: quick start steps 1 to 3 in the export of `3b92f98` (below).
- **AC-02, medium: a rerun of setup could not repair an interrupted first install.**
  - Location: `scripts/dev.sh` (`cmd_setup`, `installed_count`).
  - Evidence: the failed first install left `azk_dev` with Odoo's module table only: base and every other module "uninstalled", because Odoo rolled the install back. The old `setup` would then print "already exists; leaving it unchanged" and serve a database without our modules. Repairing it needed a manual `dropdb`.
  - Fix (`a203291`, `3b92f98`): when the development database exists but not every setup module is installed, `setup` installs the missing ones, with `base` first if even `base` is missing. It never drops the database.
  - Verification:
    - on that very database, with the fixed helper copied in as a `git pull` would, the rerun installed base and the Partner Monitor with its 50 demo partners (exit 0, 49 s, log a02);
    - a third run printed "already exists with azk_odoo_partner_monitor; leaving it unchanged" (log a03).
- **AC-03, low: stale setup documentation.**
  - Location: `docs/environment.md`.
  - Evidence:
    - it called the blocked Stage 01B pair "the target";
    - it named an `.env` key (`ENTERPRISE_EXTRA_20241208`) removed on 2026-11-05;
    - it said the default edition was `community`;
    - it listed `ODOO_EDITION=community scripts/dev.sh test`, which could no longer install the Trial Balance.
  - Fix: corrected in `a203291`, with the quick start and two troubleshooting entries.

Defects in the Stage 11 acceptance scripts (not in the submission's addons), fixed while running:

- **AC-04: the kept live sample left a tuning setting behind.** `scripts/pm_live_check.py` with `PM_LIVE_KEEP=1` committed `worker_batch_size = 2`, the value it uses for its second batch. It now restores the previous value. The acceptance database was reset with `ir.config_parameter.set_param(..., False)`, which removes the setting.
- **AC-05: the settings phase of `acceptance_pm_demo.py` had no commit.** The Odoo shell rolls back at the end, so the first run's Pause Website Downloads and recipient were lost. As a result:
  - the live sample ran with downloads not paused, which made no difference, because the check uses its own page source with a request budget;
  - the note of run 1 went to the default recipient, the administrator (see O-01).
  The phase now commits. The second run stored both settings, checked in the database: `downloads_paused = True`, `notify_user_id = 9`.
- **AC-06: two timing assumptions in `acceptance_pm_ui_check.py`.**
  - The first navigation after a server restart, while the asset bundles were built, timed out the 30 s DevTools call. The steps after it then saw "Session expired".
  - A Country filter on the one-country website sample did not change the summary.
  Navigation now tolerates the busy browser, and the filter is shown on the demo data. Runs 1 and 2 had 2 of 5 and 5 of 6 PASS; run 3 had 7 of 7.

Observations, not defects:

- **O-01: notification by email without a mail server.** With Odoo's default preference "Handle by Emails", the note of run 1 for the administrator was posted on the run's chatter, but its email could not be sent: no outgoing mail server is configured locally, and the notification status became "exception". Nothing reached the administrator's inbox. The configured recipient `acc_pm_manager`, set to "Handle in Odoo", found the notes in the Discuss inbox. The module follows the user's preference by design (D-08). The README (Stage 12) must say to configure an outgoing mail server, or to choose "Handle in Odoo" for the recipient.
- **O-02: the old code's queue timing in the upgrade seed.** In the Stage 09 code, units queued during a batch were not due in that batch (RF-03, fixed in Stage 10). So the seed's first RoayaTec page did not run ("FIXTURE unit False" in log e02), and the seeded data has no removed reference. Reference removal remains covered by the tests.
- **O-03: memory.** Free RAM fell to 0.48 GB during the first full setup. Every heavy step ran alone; the browser checks ran under a memory guard (lowest commit headroom 3,569 MB, never triggered).

## Results by check

Each line gives the result, the evidence and the log name under `runtime/logs/stage11/`.

1. **First run as documented, export of `e54214b`:** FAIL (AC-01), exit 255 after 52 s (a01).
2. **Rerun after that failure, fixed helper:** PASS. Base and the Partner Monitor installed, exit 0, 49 s; a third run left the database unchanged (a02, a03). Community edition, as written to `.env` by the old helper.
3. **Quick start, export of `3b92f98`, new Compose project with empty volumes:** PASS.
   - Step 1, `scripts/dev.sh setup`: wrote `.env` with random passwords and `ODOO_EDITION=enterprise-20241208`, then stopped with "needs ENTERPRISE_ADDONS in .env". No container was created (b01).
   - Step 2: `ENTERPRISE_ADDONS` and `COMMUNITY_SOURCE_20241208` set in `.env`, and `ODOO_EE_20241208_HTTP_PORT=8073` so as not to collide with the development server.
   - Step 3, `scripts/dev.sh setup`: exit 0 in 8 min 44 s; `azk_ee24` with 92 modules; 0 WARNING, ERROR or CRITICAL lines, no traceback (b02).
4. **Demo data loaded automatically at install:** PASS (c01, `scripts/acceptance_state.py`).
   - Partner Monitor: 13 demo countries (12 active), 50 partners (47 active), 57 history rows, 6 references (5 active); no website record.
   - Trial Balance: "AZK Trial Balance Demo (EGP)", EGP, Egypt, 16 entries (13 posted, 2 draft, 1 cancelled), 32 journal items, 10 account groups, 3 analytic accounts, 2 currency rates.
   - The same counts as in Stages 09 and 10.
5. **Partner Monitor alone, `scripts/dev.sh clean-install azk_odoo_partner_monitor`:** PASS. 34 modules, no accounting module, 2 min 16 s, 0 warnings. Its demo fingerprints equal those of the combined install (d01).
6. **Trial Balance alone, `scripts/dev.sh clean-install azk_dynamic_trial_balance`:** PASS. 91 modules, 4 min 20 s, 0 warnings. The demo fingerprints are equal. The installed localizations are Odoo's own `l10n_us` set, for the main company; there is no `l10n_eg`, so the RF-07 fix holds on a fresh install (d02).
7. **TP-G-01, each addon alone and then updated:** see "Each addon alone, then updated" below (j01 to j04).
8. **Both addons without demo data, `clean-install ... --without-demo`:** PASS. 79 modules, 6 min 17 s, 0 warnings. No demo record in either addon, the scheduled jobs active, downloads not paused (d03).
9. **Upgrade from the previous release:** PASS.
   - The export of `564b71b` (Partner Monitor 18.0.1.4.0, Trial Balance 18.0.1.3.0) installed both addons with demo data: 92 modules, 7 min 15 s, 0 warnings (e01).
   - Seeded through that release's own worker, from the saved fixture pages (e02, O-02): 2 website countries, 5 partners, 2 references and 4 runs. The 6 history rows are 5 initial rows and 1 promotion, BDR GROUP SLU shown as Silver on day 2.
   - `scripts/dev.sh update azk_odoo_partner_monitor,azk_dynamic_trial_balance azk_ee24_clean` from the export of `3b92f98`: exit 0, 2 min 6 s, 0 warnings (e04).
   - The before and after state reports differ in one line only, the Partner Monitor version, 18.0.1.4.0 to 18.0.1.5.0. Every count is equal, and so are the fingerprints of the countries (15), partners (55), status history (63), references (8), demo entries (16) and demo journal items (32), as are the runs, queued work, jobs and settings (e03, e05).
   - Probe, rolled back: the new worker read Andorra's page again on day 3; the history stayed at 63 rows, and the new setting field exists (e06).
10. **Full test suites, `scripts/dev.sh test` (both addons, fresh `azk_ee24_test`):** PASS, exit 0 in 11 min 37 s (f01).
    - "0 failed, 0 error(s) of 261 tests"; "261 post-tests in 305.14s".
    - "Starting" lines: 147 Partner Monitor and 114 Trial Balance, equal to the Stage 10 baseline and to the test methods in the export: 147 in 13 test files, 114 in 12 files. Every test file is imported in its `tests/__init__.py`.
    - Odoo's statistics lines say 177 and 150 "tests": `odoo/tests/suite.py` also records each class's `setUpClass` and `tearDownClass`, so 147 + 2 x 15 classes = 177 and 114 + 2 x 18 = 150. 260 test names are unique, because `TestModuleInstalled.test_module_is_installed` exists in both addons.
    - In the log before the summary: 0 "skipped", 0 WARNING, 0 ERROR, 0 CRITICAL, 0 FAIL, 0 tracebacks, 0 import errors.
11. **Restart scenario, `scripts/restart_check.sh` from the export:** PASS, 12 of 12 (f02).
    - The worker container was killed with SIGKILL at 14:40:29 inside batch 2 (exit status 137).
    - After the restart, only the uncommitted units ran again.
    - One promotion row and 3 references were kept once; no duplicate history (13 partners, 14 history rows).
    - Run A failed with one note, delivered once; no email was queued.
    - Fixture pages only.
12. **Dashboard on demo data, `scripts/ui_smoke_check.py`, headless Chrome, port 8073:** PASS, 7 of 7 (g01). The app opens on the dashboard with four charts; demo data is labeled; Gold and 2025 apply to all four charts; a Top 5 country opens a list of equal size; no JavaScript error.
13. **Trial Balance wizard, `scripts/tb_wizard_smoke_check.py`:** PASS, 7 of 7 (g02).
14. **Trial Balance preview and downloads, `scripts/tb_preview_smoke_check.py`:** PASS, 20 of 20 (g03). See "Trial Balance reconciliation" below.
15. **The engine against the standard Trial Balance, `scripts/tb_engine_vs_native.py`, rolled back:** PASS, 6 of 6 cases, on Odoo's own accounting demo data in the main company (USD) (g04).
16. **Partner Monitor demonstration, live sample, outage, recovery:** PASS, after the AC-05 fix (h01 to h08). See "Partner Monitor demonstration" below.
17. **Partner Monitor in the browser, `scripts/acceptance_pm_ui_check.py`:** PASS, 7 of 7 on run 3, after AC-06 (i04).
18. **Access over HTTP, `scripts/acceptance_access_check.py`:** PASS, 24 of 24 (i02). See "Access" below.

## Partner Monitor demonstration

The acceptance web server was stopped during these phases, so that its scheduled jobs could not act between them. Where each piece of data comes from:
- DEMO: the installed demo records, flagged `is_demo`, with keys `demo-01` and so on, shown under "Demo data" on the dashboard.
- LIVE: pages read from www.odoo.com on 2026-11-16, flagged `is_demo = False`, shown under "Website data".
- FIXTURE: the saved live-derived pages of the tests (restart check and upgrade seed only).
- SIMULATED: the outage. No request was sent.

1. **Users** (`scripts/acceptance_users.py`), with one random password from the environment, never printed:
   - `acc_pm_reader` (Partner Monitor Reader);
   - `acc_pm_manager` (Manager, notifications "Handle in Odoo");
   - `acc_tb_reader` (Accounting read-only, demo company only);
   - `acc_no_rights` (internal user only).
2. **Settings** through the Settings form's own code (`res.config.settings`): Pause Website Downloads ticked, recipient `acc_pm_manager`. The first run was lost (AC-05); the second run stored both.
3. **LIVE bounded sample** through the real worker entry point (`scripts/pm_live_check.py`, `PM_LIVE_KEEP=1`, at most 8 requests):
   - robots.txt: HTTP 200, 1,627 bytes, 56 rules for all crawlers, with the same size, rule count and disallowed query keys as in Stage 10; both planned URLs allowed;
   - the country list, `/partners?country_all=1`: HTTP 200, 381,630 bytes;
   - `/partners/country/1`: HTTP 301 to `/partners/country/andorra-1`, read with HTTP 200, 322,042 bytes;
   - BDR GROUP SLU's page: HTTP 200, 87,050 bytes.
   - That is 4 page requests. Result: 170 countries, a complete list, 0 deactivated (demo countries are never deactivated by a website list); Andorra 2 of 2 partners, matched; BDR GROUP SLU 17 of 17 references, matched; 0 error rows. The 169 other country units were cancelled. The second partner's page stayed queued.
4. **SIMULATED outage (run 1).** That queued page failed 5 times on a simulated clock (15 to 120 minutes apart, so the stored try times are up to 4 hours ahead) and was marked failed, with 5 error rows. Run 1 ended "Partial: 3 units done, 1 failed". Its note went to the administrator: the setting had been lost, AC-05, so this is the default recipient. The administrator's preference is email, which failed with no mail server (O-01). The stored partners and references were unchanged.
5. **Recovery of run 1.** `acc_pm_manager` pressed Retry (`work_item.action_retry` as that user). The worker job read the page LIVE, 1 request (HTTP 200, 76,042 bytes): "3 of 3 references, matched". Run 1 ended done.
6. **SIMULATED outage (run 2), with the settings stored.** `acc_pm_manager` used Mark for Re-scrape on BDR GROUP SLU. The reference-validation job queued it in validation run 2. The outage failed it 5 times, and run 2 ended "Failed: 0 units done, 1 failed". Its note went to "Acceptance PM Manager", type inbox, status sent, unread. BDR GROUP SLU kept its 17 active references and its history.
7. **Recovery of run 2.** Retry as `acc_pm_manager`. The page was read LIVE, 1 request (HTTP 200, 87,050 bytes): "17 of 17 references, matched, 0 added, 0 removed". Run 2 ended done and was not notified a second time.
8. **In the browser** (7 of 7):
   - the dashboard opens on "Website data (2)" with four charts;
   - "Demo data (47)" is separate and labeled;
   - the Country filter narrows the four charts to Demo Country Alpha;
   - BDR GROUP SLU's form shows 1 history row and 17 references;
   - run 1's chatter holds its note;
   - `acc_pm_manager`'s Discuss inbox shows run 2's note. It also holds run 3's "waiting: website downloads are paused" note, from the Sync Now of the access check.

**Live requests:** 7 in this stage, all to www.odoo.com and all allowed by robots.txt: robots.txt, 4 pages in the sample and 2 recovery pages. Downloads are left paused in the acceptance database.

## Trial Balance reconciliation

- **Golden fixture** (calculation contract, TB-BASE), in the demo company for January 2026:
  - Bank ends at 1,200.00 with posted entries only (initial 1,000.00, debit 500.00, credit 300.00);
  - and at 1,000.00 with drafts included.
  This held in the real preview, in its PDF and XLSX, through the download route for both option sets, and in the engine called over HTTP by the read-only accountant.
- **Another filter:** the search box keeps Bank only; an account prefix without accounts shows the no-results message. In the route checks, the analytic filter (whole-item inclusion) and zero filtering were also checked against the engine.
- **Hierarchy:** Hierarchy and Subtotals adds the group rows down to 10140 Bank Accounts, and folding hides Bank. "Hierarchy" and "parents only" also passed through the route.
- **Currency:** with Show Amount Currency, rows are grouped by account and transaction currency (9 rows; Bank's row is in EGP), and the XLSX equals the engine.
- **Real files:**
  - the short PDF is one landscape page with the company, period, every option, the column groups and balanced totals (1,700.00, 13,450.00, 7,800.00 on both sides). Its PNG render was viewed;
  - without Skip Zero Balance, the PDF has 3 pages, each with the column header;
  - the XLSX stores numbers with a number format and codes as text, with the header frozen.
- **Standard Enterprise Trial Balance:** 6 of 6 cases equal on the main company's data:
  - this month, posted and with drafts;
  - the fiscal year to date, posted and with drafts;
  - the previous fiscal year;
  - the sales journal.
  The hand-calculated test fixtures (TB-BASE, TB-X, TB-Z, TB-C, TB-A, TB-M, TB-R, TB-H, TB-F, TB-B), each in its own test company, are compared with the standard report in the test suite.
- **Intended differences** (calculation contract): one company per report (D-16); whole-item analytic filtering; account rows with no amount are set aside on the standard side.

## Access

24 of 24, each user in its own HTTP session, through the endpoints the web client uses:

- **Partner Monitor reader:** reads the dashboard data and the partners. Writing a partner is refused (AccessError), and so is Sync Now ("Only Partner Monitor managers can do this.").
- **No Partner Monitor group** (`acc_no_rights`, and `acc_tb_reader`): the dashboard data is refused ("Only Partner Monitor readers can see this dashboard."), partner records are refused, and no Partner Monitor menu is visible.
- **Partner Monitor manager:** Sync Now queues run 3, which waits because downloads are paused. No request was sent.
- **Read-only accountant, Trial Balance:**
  - options are served; the engine computes Bank at 1,200.00 as the user;
  - the PDF downloads (HTTP 200, application/pdf, 30,491 bytes) and so does the XLSX (9,193 bytes);
  - tampered options are refused: another company ("You are not allowed to report on this company.") and a wildcard prefix (ValidationError);
  - creating its own wizard is allowed; reading the administrator's wizard is refused by the record rule.
- **Without accounting rights** (`acc_no_rights`, `acc_pm_reader`): the download is refused (AccessError on account.report), and so are creating a wizard and the engine ("The Dynamic Trial Balance needs read access to accounting.").
- **No session:** no file; the route redirects to `/web/login`.
- The server logged each refusal as a WARNING from `odoo.http`, and nothing else beyond the waiting notice of run 3.

## Each addon alone, then updated

Test plan TP-G-01, from the export of `3b92f98`:

- **Partner Monitor:** PASS. `scripts/dev.sh clean-install azk_odoo_partner_monitor`: exit 0 in 1 min 37 s, 34 modules (j01). Then `scripts/dev.sh update azk_odoo_partner_monitor azk_ee24_clean`: exit 0 in 47 s (j02).
- **Trial Balance:** PASS. `scripts/dev.sh clean-install azk_dynamic_trial_balance`: exit 0 in 3 min 7 s, 91 modules (j03). Then `scripts/dev.sh update azk_dynamic_trial_balance azk_ee24_clean`: exit 0 in 1 min 3 s (j04).
- All four logs: 0 WARNING, ERROR or CRITICAL lines, no traceback.

## Results by requirement

The requirement IDs are those of [requirements_matrix.md](requirements_matrix.md). PASS means "shown by a Stage 11 check above"; requirements that Stage 11 did not exercise again cite the test suite (261 of 261 above) or their stage.

- **P-01** (module name): PASS, installed as `azk_odoo_partner_monitor`.
- **P-02, P-03.2** (scrape with requests and BeautifulSoup): PASS, the live sample (checks 16 and 17). Both libraries are declared as `external_dependencies` and present in the pinned image. **P-03.1** (scraping logic made with GenAI): see [ai/](ai/).
- **P-04** (daily job): PASS for configuration and tests. The Daily Discovery job is active after install, next run at 02:00 the next day. It was not left to fire here, because it starts a full crawl.
- **P-05.1, P-05.2, P-06** (one failure does not stop the job; errors logged): PASS. The outage failed one unit while the others were done, with 5 error rows; the restart check's failed Egypt unit did not stop its batch.
- **P-07.1 to P-07.4** (notification of a partial or failed run; configurable recipient; administrator by default): PASS. Run 1, partial, notified the default recipient, the administrator. Run 2, failed, notified the configured `acc_pm_manager` in the inbox. Delivery by email needs a mail server (O-01).
- **P-08.1 to P-08.3** (interruptions, recovery without repeating work, only changes): PASS. The restart check (12 of 12); Retry ran only the failed units; a page read again changed nothing ("0 added, 0 removed").
- **P-09 to P-12** (the four models and their fields): PASS. Installed and upgraded; shown in the partner form in the browser; covered by the test suite.
- **P-13 to P-16** (first seen, status history, references added and removed): PASS.
  - First seen and initial history: live sample.
  - Status change: upgrade seed.
  - One promotion row only: restart check.
  - Reference removal: test suite only in this stage (O-02).
- **P-17.1, P-17.2** (menus, actions, the new data model): PASS in the browser. **P-17.3** (original filters, groupings and pivots kept): IN PROGRESS, because the original specification was never supplied (Q-02).
- **P-18 to P-21** (validation of countries and references, and their jobs): PASS. The reference-validation job queued validation run 2, and the matched counts were stored. Country validation is covered by the test suite.
- **P-22.1, P-22.2** (empty-country case, URL check): PASS in the test suite and the Stage 04/10 live notes; not exercised live in Stage 11.
- **P-23** (deactivation only after a complete country list): PASS. The complete live list deactivated nothing and left demo countries alone.
- **P-24 to P-28** (the dashboard, filters and four charts): PASS in the browser: checks 12 and 17, Status, Year and Country filters on all four charts.
- **T-01 to T-18, T-21 to T-23** (wizard, options, preview, PDF, XLSX, demo data): PASS, checks 4, 13 to 15 and 18.
  - Company and period: T-03.1, T-03.2.
  - Posted and draft entries: T-04, T-05.
  - Hierarchy and parents: T-06, T-07.
  - Prefixes, journal and analytic account: T-08 to T-10.
  - Zero balances and amount currency: T-11, T-12.
  - Columns and outputs: T-13 to T-18.
  - Demo data: T-21 to T-23.
- **T-19, T-20** (README on testing): NOT STARTED, Stage 12.
- **G-01** (public repository): NOT STARTED, Stage 15.
- **G-02 to G-06, G-08** (README): NOT STARTED, Stage 12.
- **G-07** (assumptions): IN PROGRESS, [assumptions.md](assumptions.md).
- **G-09** (AI logs): IN PROGRESS, [ai/](ai/) holds Stage 11.
- **G-10** (code quality): reviewed in Stage 10; no addon code changed since.
- **G-11** (packaging, easy install and test): installation and tests reproduced from a clean export (PASS); the README with the testing instructions is Stage 12.
- **G-12, X-01**: out of scope. **G-13** (two exercises): done.
- **G-14** (robustness): PASS, through the outage, recovery and restart checks.
- **K-01** (one result for all outputs): PASS, the route outputs equal the engine.
- **K-02** (access on every path): PASS, the 24 access checks.
- **K-03** (identities and idempotence): PASS, the upgrade fingerprints and the restart check.
- **K-04** (removals only after a complete snapshot): PASS, the outage kept the data.
- **K-05** (version-sensitive APIs read from the pinned source): IN PROGRESS. In this stage: the test statistics in `odoo/tests/suite.py`, the database creation in `odoo/cli/server.py`.
- **K-06** (no Enterprise source in the repository): PASS. The export holds only the two addons, licensed LGPL-3; no OEEL-1 file and no Enterprise module folder.
- **K-07** (hand-calculated expectations, standard parity): PASS, 1,200.00 and 1,000.00, and 6 of 6.
- **K-08** (readers cannot act as managers): PASS.
- **K-09** (labeled demo data): PASS, the separate demo source on the dashboard.
- **K-10** (unknown measurements are not zeros): covered by the test suite; not exercised separately here.

## UI steps: performed by the agent, and awaiting the user

- **Performed by the agent with headless Chrome** (DevTools protocol, the scripts named above): the dashboard on demo and website data with all three filters; the partner list; the partner form's tabs; the run's chatter; the Discuss inbox of the recipient; the Trial Balance wizard; the preview with Draft Entries, search, hierarchy and folding; both downloads and their content; the empty state. The PDF render and the inbox and partner screenshots were viewed.
- **Awaiting the user (TP-G-05):** opening the same screens in a normal browser and judging them; downloading and opening a PDF and an XLSX in a desktop viewer; Settings > Partner Monitor. The acceptance server can be started again with `COMPOSE_PROJECT_NAME=azk-stage11-acc scripts/dev.sh start` in the export folder (http://127.0.0.1:8073, admin / admin), or the development server used as before.

## Reproduce these checks

From a clean checkout, after the quick start in [environment.md](environment.md):

```text
scripts/dev.sh shell azk_ee24 < scripts/acceptance_state.py         # installed modules, demo data, fingerprints
scripts/dev.sh clean-install azk_odoo_partner_monitor                 # one addon alone (then the other)
scripts/dev.sh clean-install azk_odoo_partner_monitor,azk_dynamic_trial_balance --without-demo
scripts/dev.sh test                                                   # both suites: 261 tests
scripts/restart_check.sh                                              # after the test run
scripts/dev.sh start
python scripts/ui_smoke_check.py OUT          # PM_UI_URL, PM_UI_LOGIN, PM_UI_PASSWORD
python scripts/tb_wizard_smoke_check.py OUT
python scripts/tb_preview_smoke_check.py OUT
scripts/dev.sh shell azk_ee24 < scripts/tb_engine_vs_native.py
```

The demonstration scripts write to a database, so they refuse any database created before the date in `ACC_DB_CREATED_AFTER` (or `PM_LIVE_DB_CREATED_AFTER`). They need `docker compose run -e` to receive their variables; each script's header gives the exact command. Stop the web server first (`scripts/dev.sh stop`):

```text
acceptance_users.py -> acceptance_pm_demo.py (prepare) -> pm_live_check.py (PM_LIVE_KEEP=1)
  -> acceptance_pm_demo.py (fail) -> acceptance_pm_demo.py (recover)
then scripts/dev.sh start, acceptance_pm_ui_check.py and acceptance_access_check.py
```

The upgrade check: install the previous release from its own export, run `scripts/acceptance_upgrade_seed.py` (`ACC_PHASE=seed`) and `acceptance_state.py`, update from the new export, then run `acceptance_state.py` and `ACC_PHASE=probe` again.

## Remaining gaps and blockers

- **Stage 12:** README.md with features, installation, configuration, the testing strategy, the resilience design, and what is done and pending (G-02 to G-06, G-08, T-19, T-20). It must include O-01 (mail server or "Handle in Odoo").
- **Stage 15:** the public repository (G-01).
- **The user's manual check** (TP-G-05).
- **Open questions for the team lead:** Q-02 (original specification; P-17.3), Q-03 (the standard Trial Balance as reference), Q-04 (the version 18.0), Q-05 (newer Enterprise addons), Q-06 (the license of the Trial Balance addon).
- **Not repeated in Stage 11:** a full live crawl (on purpose, D-64), a live empty-country check (P-22.1; tests and the Stage 04 notes only), and the Partner Monitor on the Community baseline beyond its install with demo data in the AC-02 check (TP-G-03, optional).
