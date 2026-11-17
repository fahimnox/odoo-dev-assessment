# Project state

_Last updated: 2026-11-17, Stage 15 (publication): the repository is public at https://github.com/fahimnox/odoo-dev-assessment, and the submitted commit is tagged `submission-v1`. Stage 13 is PAUSED and Stage 14 is DEFERRED until after publication. Stage 04 is DONE since Stage 10._

## Current position

- **Stage 15: DONE (2026-11-17).** Published, on the user's explicit request, to https://github.com/fahimnox/odoo-dev-assessment (public), under the GitHub account `fahimnox`, the author name of every commit.
  - **What was published:** the branch `main` with its full history, unchanged (the user chose to keep the author metadata and history), and the tags `submission-rc1` (the reviewed release candidate) and `submission-v1` (the submitted commit: `submission-rc1` plus documentation only).
  - **Checked before the push:** the publication review of Stage 12, repeated over the files and every commit ([release_checklist.md](release_checklist.md) section 3), and the documentation links. No application check was rerun: no addon code or setup file changed since the Stage 11 acceptance, and nothing but documentation since `submission-rc1`.
  - **Checked after the push:** the remote branch and tags against the local ones, and the README and both manifests read without signing in; recorded in [test_results.md](test_results.md) and the Stage 15 log, [ai/stage_15.md](ai/stage_15.md), which follows the submitted commit on `main` with the handoff, [handoffs/stage_15_en.md](handoffs/stage_15_en.md).
  - **Still open:** the license (Q-06, D-70), the candidate's manual check (T-19), the views specification (P-17.3, Q-02), and the questions Q-02 to Q-06. Sending the link to the assessor is the candidate's own action.
- **Stage 14: DEFERRED (2026-11-17)** by the user until after publication. Not started.
- **Stage 13: PAUSED (2026-11-17)** by the user after section 1 of 7, to publish first. Section 1 (the project overview) was taught; its comprehension question has not been answered yet. As the Stage 13 prompt requires, the code map and the record of the candidate's answers are private study notes outside this repository. The partial log is [ai/stage_13.md](ai/stage_13.md). The stage resumes after publication and stays unfinished until the walkthrough is completed. No addon code changed.
- **Stage 12: DONE (2026-11-16).** Submission documentation and a local release checkpoint (the Stage 12 commit, annotated tag `submission-rc1`, not pushed). No addon code or setup file changed.
  - **New:** [README.md](../README.md) (scope, the Enterprise target with the unconfirmed version 18.0, the pins, prerequisites, the verified quick start, commands, isolated copies and volume reuse, configuration with mail delivery of the failure notes, features, resilience, testing with 261 = 147 + 114, demo, assumptions and limitations, status, evidence, AI use, license), [demo_script.md](demo_script.md) (about 7 minutes, data labels, expected numbers, a failure-and-recovery story, an offline fallback) and [release_checklist.md](release_checklist.md) (the publication review, the candidate's decisions, the pending work).
  - **Updated to the final implementation:** [architecture.md](architecture.md) (a new section 0; the stale "not implemented yet" intro removed), [resilience.md](resilience.md) (a map, notification delivery, partial-snapshot safety, Stage 11 results), [calculation_contract.md](calculation_contract.md) (a reviewer summary; fiscal years and branches compared in Stage 10), the final [requirements_matrix.md](requirements_matrix.md) (147 of 152 rows DONE; P-17.3 and T-19 IN PROGRESS; G-01 NOT STARTED), [test_results.md](test_results.md) (a final summary), [test_plan.md](test_plan.md), [assumptions.md](assumptions.md) (D-69 documented, D-70), the fixtures README and one script comment.
  - **Checked in this stage:** reusing a project's volumes with a new `.env` (a throwaway project: the container was recreated, the volume kept, the new password refused); the project-name precedence; the demo state of the acceptance database (read-only); links, anchors, commands, paths and ASCII; a publication review of the files and of the 24 commits (no secret, local path or vendor code; the Git identity's email address is a decision for the candidate).
  - **Not rerun:** the application checks, because nothing they test changed. The test count and every result stay those of Stage 11.

- **Stage 11: DONE (2026-11-16).** Clean-checkout acceptance: [acceptance_results.md](acceptance_results.md). The addon code is unchanged since Stage 10 (`e54214b`).
  - **Found and fixed (packaging and documentation):**
    - AC-01: the first documented command, `scripts/dev.sh setup`, failed in a fresh checkout, because the default edition was Community. The default is now `enterprise-20241208`, `setup` writes `.env` first and asks for the two source folders, and `environment.md` has a quick start (D-67);
    - AC-02: a rerun of `setup` now installs what an interrupted first install left out, `base` included, without dropping the database;
    - AC-03: stale lines in `environment.md`.
  - **Evidence (2026-11-16)**, from `git archive` exports outside the repository, in a separate Compose project with empty volumes on port 8073 (D-68):
    - installs:
      - the quick start;
      - demo data at install (13 countries and 50 partners; the Trial Balance demo company with 16 entries);
      - the Partner Monitor alone (34 modules) and the Trial Balance alone (91 modules), each then updated;
      - both without demo data;
      - all with 0 warnings;
    - an upgrade from the Stage 09 release: the state reports before and after differ only in the Partner Monitor's version;
    - `scripts/dev.sh test`: 261 of 261 (147 and 114, the Stage 10 baseline), with no skipped or uncollected test;
    - the restart check, 12 of 12;
    - browser checks on the fresh database: dashboard 7 of 7, wizard 7 of 7, preview and downloads 20 of 20 (Bank 1,200.00 and 1,000.00);
    - the standard Trial Balance, 6 of 6;
    - the Partner Monitor demonstration: a kept LIVE sample (7 requests to www.odoo.com in all), two SIMULATED outages, notes to the default and then to the configured recipient, recovery by a manager's Retry; in the browser 7 of 7;
    - access over HTTP for four non-admin users and an anonymous one, 24 of 24.
  - **Observation O-01 (for the README, D-69):** with the default "Handle by Emails" and no mail server, a failure note reaches the run's chatter but not the recipient's inbox.
  - **Environment after the stage:**
    - The development stack runs again on port 8071. Its eight databases were not changed; only a few read-only SQL queries were made on `azk_ee24` at the start.
    - The acceptance project `azk-stage11-acc` is stopped, and its volumes are kept. Downloads are paused there, and its run 3 waits.
    - The exports are under `<kit-root>/runtime/acceptance/`.

- **Stage 10: DONE (2026-11-15).** Engineering review of both addons: [review_findings.md](review_findings.md) (findings RF-01 to RF-15, with severity, evidence, fix and verification). `azk_odoo_partner_monitor` 18.0.1.5.0; `azk_dynamic_trial_balance` still 18.0.1.3.0 (Python changes only).
  - **Partner Monitor, Stage 04 completed:**
    - `services/http_client.py`, the page download (D-65): bounded timeouts, size, spacing and retries; redirects checked against the URL and robots rules; HTTP errors, login pages and rate limits raise;
    - connected to the worker; Settings > Pause Website Downloads (D-64), on for `azk_ee24`;
    - one bounded live check through the worker on `azk_ee24_test` (the country list, Andorra, one partner page; rolled back).
  - **Fixed and verified:**
    - RF-02: the website closed connections that offered `deflate`, so the client asks for gzip only;
    - RF-03: work queued by a unit is due in the same batch;
    - RF-04: empty reference cards are skipped;
    - RF-05: the pause switch;
    - RF-06: branch-only users get the full Trial Balance (accounts searched with an explicit order);
    - RF-07: the demo company never triggers a localization install.
  - **Trial Balance coverage:** custom fiscal years and branches (TB-F, TB-B), standard reports unchanged, the analytic selector in a browser, a benchmark (D-60 closed; D-66).
  - **Evidence (2026-11-15):**
    - tests on fresh `azk_ee24_test` databases: Partner Monitor 147 of 147 and Trial Balance 114 of 114, both with 0 warning lines. Trial Balance runs 1 and 2 failed on RF-06, which was fixed in run 3. The vendor's `TestTrialBalanceReport` and annotation-export tests passed 11 of 11 with our addon installed;
    - the bounded live check through the worker: run 4 PASS on the final code. Runs 1 to 3 found RF-02 to RF-04. 23 requests to www.odoo.com in all, every one listed in [live_site_notes.md](live_site_notes.md);
    - the analytic browser check as a read-only accountant, on a temporary server for the disposable database: 6 of 6. The restart check: 12 of 12;
    - an install without demo data: 0 warnings. The documented demo call then created no localization and gave the install-time counts;
    - benchmarks (rolled back): constant Trial Balance query counts from 2,000 to 10,000 journal items; 7 and 4 queries per Partner Monitor card;
    - `azk_ee24` upgraded with 0 warnings. Downloads stay paused there, and its browser checks pass again: dashboard 7 of 7, preview 20 of 20.
- **Stage 09: DONE (2026-11-15).** `azk_dynamic_trial_balance` 18.0.1.3.0, on top of the Stage 08 commit `845accb`.
  - **Implemented:**
    - the Preview, PDF and XLSX through the standard `account_reports` framework: our report record (`data/trial_balance_report.xml`) and custom handler (`models/trial_balance_report_handler.py`) feed the standard UI and exporters from one engine call per request (K-01, D-54);
    - a filter bar component with the Trial Balance options, account prefixes, journal and analytic account (`static/src/components/trial_balance/`); every change recalculates; search, folding and messages;
    - three PDF templates (report company, every option, column groups with a repeating header; D-55) and our own XLSX sheet for this report (numbers with a number format, text codes and names, currency column, options above the table, frozen header; D-56);
    - exports follow the preview's search and folded groups (D-57); nothing is stored, every request recalculates as the user (D-58);
    - the wizard's Preview, PDF and XLSX buttons connected (D-47 superseded);
    - installable demo data: an Egyptian company in EGP with posted, draft, cancelled, USD, EUR and analytic entries and groups five levels deep, reproducing Bank 1,200 and 1,000 (D-59).
    Design: [architecture.md](architecture.md) 4.11, [calculation_contract.md](calculation_contract.md) 16; decisions D-54 to D-63. Results: [test_results.md](test_results.md). Samples: [samples/](samples/). Handoff: [handoffs/stage_09_en.md](handoffs/stage_09_en.md).
  - **Evidence (2026-11-15):**
    - `scripts/dev.sh test azk_dynamic_trial_balance` on the final code: PASS, "0 failed, 0 error(s) of 102 tests" (85 earlier, 17 new), 0 warning lines, exit code 0, 438 s. Run 2 passed 101 of 101; run 1 was stopped (below); run 3 was superseded.
    - Demo data and upgrades: a fresh install then an upgrade of `azk_ee24_test`, and three upgrades of `azk_ee24`, left every demo count unchanged (16 entries, 32 items, 10 groups, 2 plans, 3 analytic accounts, 2 rates). On `azk_ee24`, which had the module since Stage 07, the demo was created once by calling the demo function from an Odoo shell, because Odoo runs demo-file functions at install only.
    - Headless Chrome on `azk_ee24` (`scripts/tb_preview_smoke_check.py`), final code: PASS, 20 of 20. It covers the real Preview, Draft Entries, search, folding, both downloads, a 1-page and a 3-page PDF, the empty state, the download route (tampered options refused, no file without a session) and the eight option sets through the real route against the engine. The updated wizard check: PASS, 7 of 7.
    - The PDFs were rendered to PNG and inspected: landscape, readable, no clipping, the header on every page.
  - **Run 1 stopped:** the CLI stopped the first test run's background command at about 08:41 UTC because the machine was critically low on memory (1.0 GB free). Its container was stuck in a real wkhtmltopdf render and was stopped with `docker stop`. Unit tests now replace wkhtmltopdf with a stub that keeps the HTML (as Odoo's own tests do), and the `HttpCase` class was removed (it made Odoo build every asset bundle, about 13 minutes). Real PDFs are checked on the running server (D-63).
  - **Memory and disk:** RAM was tight all stage (other applications used most of it); free RAM was sampled during the runs (0.9 to 2.7 GB) and the browser checks ran under a guard (lowest commit headroom 1.34 GB). C: stayed at about 48 GB free.
- **Stage 08: DONE (2026-11-15).** `azk_dynamic_trial_balance` 18.0.1.2.0, on top of the Stage 07 commit `cabfb75`.
  - **Implemented:**
    - the calculation engine `azk_dynamic_trial_balance.engine` (`models/trial_balance_engine.py`), whose `compute(options)` returns one normalized result: filters, display lines, leaf and hierarchy rows, totals, per-currency totals, warnings and metadata;
    - the engine checks the accounting read-only group (D-50) and validates every option again;
    - three grouped `_read_group` queries as the calling user (movement, opening, carry-forward), so record rules apply, with no `sudo()` and no SQL;
    - the wizard's `_compute_report()`.
    The Preview, PDF and XLSX buttons are still entry points (Stage 09). Design: [architecture.md](architecture.md) 4.10, [calculation_contract.md](calculation_contract.md) 15; decisions D-50 to D-53. Results: [test_results.md](test_results.md). Handoff: [handoffs/stage_08_en.md](handoffs/stage_08_en.md).
  - **Evidence (2026-11-15):**
    - `scripts/dev.sh test azk_dynamic_trial_balance` on the final code: PASS. "0 failed, 0 error(s) of 85 tests" (48 from Stage 07, 37 new), 0 warning lines, exit code 0, 326 s. Runs 1 and 2 also passed (84 and 85 tests).
    - The engine equals the hand-calculated constants of every fixture, and the standard Trial Balance wherever both have the option. The exact scope is in [test_results.md](test_results.md).
    - Query count: 15 to 16 per report after warm-up, whether 4 or 24 accounts have amounts.
    - The standard report on `azk_ee24`'s own data (`scripts/tb_engine_vs_native.py`, admin, rolled back): 6 of 6 cases match.
    - `scripts/dev.sh update azk_dynamic_trial_balance` on `azk_ee24`: PASS, 0 warnings.
    - Headless Chrome check of the wizard: PASS, 8 of 8, after restarting the web server.
  - **Docker restart:** both containers stopped at 06:20:26 UTC, between Stage 07 and Stage 08. The web server exited with 255 and the database with 0. Docker's engine now reports version 29.9.2 (29.4.0 in Stage 01), so Docker Desktop was most likely updated. `scripts/dev.sh start` brought the web server back.
  - **Disk:** 47 to 48 GB free on C: during the stage, stable during all three runs.
- **Stage 07: DONE (2026-11-15).** `azk_dynamic_trial_balance` 18.0.1.1.0 now depends on `account_reports`.
  - **Before the stage:** the Stage 06 dashboard smoke check was rerun at commit `3222285` on `azk_ee24`: PASS, 7 of 7 (committed separately as `597e0e8`).
  - **Implemented:**
    - the wizard `azk_dynamic_trial_balance.wizard` (Accounting > Reporting > Audit Reports > Dynamic Trial Balance) with every PDF field and help text;
    - one option contract (`models/report_options.py`, `normalize_options`), used by the wizard and meant for every later entry path. It checks dates, an authorized and active company, the journal and analytic account, option combinations and literal code prefixes;
    - private wizard and prefix records (record rules on `create_uid`);
    - [calculation_contract.md](calculation_contract.md), written before any calculation code;
    - fixtures from real entries, with hand-calculated constants: TB-BASE, TB-X, TB-Z, TB-C, TB-A, TB-M, TB-R and TB-H.
    The Preview, PDF and XLSX buttons are entry points only: they validate, then say that the output is not available yet (D-47). Design: [architecture.md](architecture.md) 4.9; decisions D-43 to D-49 and V-08. Handoff: [handoffs/stage_07_en.md](handoffs/stage_07_en.md).
  - **Evidence (2026-11-15):**
    - `scripts/dev.sh test azk_dynamic_trial_balance` on the final code: PASS. "0 failed, 0 error(s) of 48 tests" in a fresh `azk_ee24_test`; 0 warning lines; exit code 0; 289 s.
      - Run 1 had 1 failure and 2 errors in the wizard tests, plus 88 translation warnings, all fixed.
      - In every run, the standard Trial Balance gave exactly the hand-calculated numbers for every fixture compared (TB-BASE posted, with drafts and per journal; TB-X in January and February; TB-Z; TB-C in company currency; TB-A; TB-M; TB-R; TB-H with its hierarchy).
    - `scripts/dev.sh update azk_dynamic_trial_balance` on `azk_ee24`, twice, the second time on the final code: PASS, 0 warnings.
    - Headless Chrome (`scripts/tb_wizard_smoke_check.py`) on `azk_ee24`, on the final code: PASS, 8 of 8. The menu opens the dialog; the notice is shown; Posted Entries is ticked; the fields are there; the dependent options appear in order; a typed prefix becomes a tag; Preview shows "not available yet"; no JavaScript error. The first run found that Posted Entries showed unticked in a new form, which was fixed. Screenshots: [screenshots/](screenshots/).
  - **Disk:** free space on C: was sampled every 30 s during each test run.
    - Run 1: from 54.7 to 50.0 GB. Run 2: from about 49 to 45.7 GB. Run 3: from 46.4 to 46.2 GB.
    - Docker's virtual disk stayed at 17.63 GB (not sparse), and there is no WSL swap file. While idle, free space was stable.
    - The use during runs 1 and 2 is not attributed: shadow storage needs administrator rights to inspect.
    - Free space after the stage: about 46 GB.
- **Stage 06: DONE (2026-11-10).** `azk_odoo_partner_monitor` 18.0.1.4.0.
  - **Implemented:**
    - the dashboard, the module's entry point (Partner Monitor > Dashboard): an OWL client action with shared Status, Year First Seen and Country filters;
    - one server method (`models/dashboard.py`) that ranks countries after the filters, with grouped ORM queries as the user;
    - four standard graph views defined in XML: Top 5 and Bottom 5 by status, and the project-size buckets of the same two cohorts;
    - the sync state on the dashboard, including "waiting for a page source", and Sync Now for managers;
    - website data and demo data shown separately, with a demo banner;
    - pivots and graphs for partners, status history and references;
    - larger demo data: 13 countries, 50 partners.
    Design: [architecture.md](architecture.md) 5.13; decisions D-37 to D-42. Handoff: [handoffs/stage_06_en.md](handoffs/stage_06_en.md).
  - **Evidence (2026-11-10):**
    - `scripts/dev.sh test azk_odoo_partner_monitor` on the final code: PASS. "0 failed, 0 error(s) of 129 tests" in a fresh `azk_ee24_test`: 113 earlier tests plus 16 dashboard tests. 0 warning lines, exit code 0, 8 min 27 s; the host was slow, as an earlier run took 3 min 31 s. The first run found one failure (the dashboard menu without its own group), fixed before the later runs.
    - Fixture sync demonstration (`scripts/fixture_sync_demo.py`, `azk_ee24_test`, saved fixture pages, nothing committed): PASS. One country sync, a promotion and a reference removal, printed before and after.
    - `scripts/dev.sh update azk_odoo_partner_monitor` on `azk_ee24`: PASS, 0 warnings.
    - Headless Chrome (`scripts/ui_smoke_check.py`) on `azk_ee24`: run 4 PASS, 7 of 7. The code differed from the final code only by one space character in the template. An earlier run (run 2) with `--sync` PASSED Sync Now and the waiting state. Screenshots: [screenshots/](screenshots/). The final browser run was BLOCKED on 2026-11-10: after the disk-full event below, the host answered a page in 24 s (2 GB of RAM free). Rerun on 2026-11-15 at commit `3222285` (the final code, clean tree): PASS, 7 of 7, with the same numbers ([handoffs/stage_06_en.md](handoffs/stage_06_en.md)).
  - **Disk event, 2026-11-10 at about 11:35 UTC:**
    - drive C: fell to 0.15 GB free;
    - the largest recent writes were Windows' page file (12.4 GB), Docker's virtual disk (17.6 GB, growing), a 1.84 GB backup of another project, and a CLI update;
    - Docker's VM stopped our two containers abruptly (exit 255). `scripts/dev.sh start` restarted them, PostgreSQL recovered automatically, and `azk_ee24` was checked intact;
    - free space then went back to 3.6 GB.
- **Stage 05: DONE for the worker, tested offline (2026-11-10).** `azk_odoo_partner_monitor` 18.0.1.3.0.
  - **Implemented:** the sync engine `models/worker.py` and four scheduled jobs (`data/ir_cron.xml`): daily discovery, a worker processing bounded batches, country validation and reference validation.
    - Claims are row locks (`FOR NO KEY UPDATE SKIP LOCKED`). Each unit runs in its own savepoint, and failures are recorded after the rollback.
    - The scheduler's commit after each batch is the only durability point.
    - Retries are bounded (5 tries, backoff from 15 minutes).
    - Expected, found, previous and stored counts are kept apart, with the validation outcome.
    - Details are refreshed when the card's metrics hash changes (no self-triggering loop).
    - One failure note per run.
    - Without a page source, the worker keeps the queue and marks the runs as waiting.
    Design, commit story and limits: [resilience.md](resilience.md). Handoff: [handoffs/stage_05_en.md](handoffs/stage_05_en.md).
  - **Evidence (automated, 2026-11-10):**
    - `scripts/dev.sh test azk_odoo_partner_monitor` on the final code: PASS. "0 failed, 0 error(s) of 113 tests" in a fresh `azk_ee24_test`: the 91 earlier tests plus 22 new ones (20 worker tests and 2 concurrency tests on real, separate connections). 0 warning lines, exit code 0, 1 min 58 s. Earlier runs: 112 of 112 on the first code, 113 of 113 after two fixes.
    - Restart check `scripts/restart_check.sh` (TP-PM-15) on the same database: PASS, 12 of 12 checks. The worker's container was killed with SIGKILL during its second batch, after the first batch committed. After the restart, only the interrupted batch's two units ran again, then the last unit. No duplicated work, history row, reference or note. Details: [resilience.md](resilience.md) section 12.
    - `scripts/dev.sh update azk_odoo_partner_monitor` on `azk_ee24`: PASS, 0 warnings. The four jobs are active; the first daily discovery is due 2026-11-11 02:00 UTC. 0 runs; login page HTTP 200.
  - **NOT RUN:** a live sync. The page-download module is still deferred (Stage 04 PARTIAL), so `worker._get_page_source()` returns None. A browser check was not run either.
- **Stage 04: PARTIAL (2026-11-08).** `azk_odoo_partner_monitor` 18.0.1.2.0.
  - **Implemented:**
    - `services/urls.py`: the `country_id` check on raw links before canonicalization, canonical partner URLs, listing URLs, reference identities (D-23) and the robots.txt rules (D-25);
    - `services/parsers.py`: BeautifulSoup parsers for the country list, listing pages and partner pages;
    - `services/reader.py`: passes pages from any `fetch(url)` to the parsers, following the pager;
    - `models/ingest.py`: ingestion through the Stage 03 observation methods. Removals happen only for complete snapshots (D-27, D-28); incomplete ones set the re-scrape flags and keep existing data.
  - **Missing:**
    - the requests-based page-download module (`services/http_client.py`) and its mocked-response tests. The response that was writing it, and a later one writing a synthetic fixture, were stopped by a safety classifier; the user deferred both files;
    - the synthetic fixtures for login, rate-limit, truncated and duplicate pages;
    - a live run through the module.
    See [handoffs/stage_04_en.md](handoffs/stage_04_en.md).
  - **Evidence:**
    - this morning's manual live sample (curl, 9 requests) and the manual parser check on the saved full pages: [live_site_notes.md](live_site_notes.md);
    - the automated offline tests below.
- **Stage 04 checks** (edition `enterprise-20241208`):
  - `scripts/dev.sh test azk_odoo_partner_monitor`: PASS. "0 failed, 0 error(s) of 91 tests" in a fresh `azk_ee24_test`: the 53 Stage 03 tests plus 38 new ones (8 URL-rule, 12 parser, 18 ingestion). 0 warnings in the log, exit code 0, 2 min 28 s. Rerun on the committed code: 91 of 91 again, 0 warnings, 1 min 56 s.
  - `scripts/dev.sh update azk_odoo_partner_monitor` on `azk_ee24`: PASS, 0 warnings or errors, 1 min 15 s.
  - NOT RUN: the fetcher tests and a live run through the module (no fetcher); a browser check.
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
- **Next step:** when the user asks, resume Stage 13 at section 1 (its question is still unanswered), then Stage 14 (mock interview). The candidate's open decisions are in [release_checklist.md](release_checklist.md) section 4: the license, the manual check, the questions Q-02 to Q-06 and the supplied archive.
- **Browser checks:** the user reported a browser smoke check of the Stage 01B environment (port 8070) in the 2026-11-04 message, without detailed results. On port 8071 the agent ran headless Chrome (installed on this machine) through the DevTools protocol in Stage 06: the Partner Monitor dashboard check passed 7 of 7 (`scripts/ui_smoke_check.py`). Other screens of the environment were not checked in a browser; the manual steps are in the Stage 06 handoff.
- **Business features implemented:**
  - the Partner Monitor data model, access rules, basic views and demo data (Stage 03);
  - its parsers and ingestion, tested offline (Stage 04);
  - its scheduled jobs and worker, tested offline (Stage 05);
  - its dashboard, pivots and graphs (Stage 06).
  - its page download and a bounded live check through the worker (Stage 10, completing Stage 04).
  - The Trial Balance wizard, its validation and the calculation contract (Stage 07), the calculation engine (Stage 08), and the Preview, PDF and XLSX outputs with the demo data (Stage 09).
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
| 04 | Partner scraping | DONE (2026-11-15, completed in Stage 10): parsers, ingestion, the page download and a bounded live check through the worker |
| 05 | Partner resilience | DONE for the worker (2026-11-10): jobs, worker, retries, validation and notes; tests and the restart check pass offline; live sync NOT RUN (needs Stage 04's page-download module) |
| 06 | Partner dashboard | DONE (2026-11-10): dashboard entry point, shared filters, four charts, sync state; 129 tests pass; browser check 7 of 7; rerun on the final code on 2026-11-15: 7 of 7 |
| 07 | Trial Balance wizard and calculation contract | DONE (2026-11-15): wizard, option contract, calculation contract and fixtures; 48 tests pass; the standard Trial Balance matches the hand-calculated numbers; browser check of the wizard 8 of 8; outputs are entry points only |
| 08 | Trial Balance calculation engine | DONE (2026-11-15): engine with one normalized result; 85 tests pass; equal to the hand-calculated constants and to the standard Trial Balance where both apply; constant query count |
| 09 | Trial Balance outputs (Preview, PDF, XLSX) | DONE (2026-11-15): Preview, PDF and XLSX from one engine call per request; demo data; 102 tests pass; browser and download-route check 20 of 20; upgrades duplicate no demo record |
| 10 | Engineering review | DONE (2026-11-15): review findings with evidence; the page download and a live check; fiscal years, branches and analytics tested; 147 Partner Monitor and 114 Trial Balance tests pass, the vendor's 11 tests pass with our addon, and the live, analytic, restart and no-demo checks pass |
| 11 | Clean acceptance | DONE (2026-11-16): from clean exports in a separate Compose project, both addons install alone and together, with and without demo data, and upgrade from Stage 09 keeping all data; 261 of 261 tests; restart 12 of 12; browser checks 7, 7, 20 and 7 of the same; access 24 of 24; the first setup command fixed (AC-01, AC-02) |
| 12 | Submission documentation | DONE (2026-11-16): README, demo script, release checklist, final requirement matrix (147 of 152 rows DONE), design documents brought to the final implementation, publication review; local tag `submission-rc1` |
| 13 | Code walkthrough | PAUSED (2026-11-17) by the user after section 1 of 7; resumes after publication; the code map and answer notes are private, outside the repository |
| 14 | Mock interview | DEFERRED (2026-11-17) by the user until after publication; not started |
| 15 | Publish | DONE (2026-11-17): public repository https://github.com/fahimnox/odoo-dev-assessment; `main` and the tags `submission-rc1` and `submission-v1` pushed; history unchanged; the remote compared with the local refs after the push |

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
  - The manifest depends on `account_reports` since Stage 07.
- **Stage 03 decisions** ([assumptions.md](assumptions.md)):
  - D-18: nobody edits scraped data, history or checkpoints through access rules; managers use four checked actions;
  - D-19: the default failure recipient is the administrator, because install hooks run as the superuser;
  - D-20: demo records are labeled and use reserved website ids;
  - D-21: an observation older than the last one is ignored;
  - D-22: `total_references_count` also has a known flag, and unknown measurements carry no number.
- **Stage 04 decisions** ([assumptions.md](assumptions.md)):
  - D-23: a reference is identified by its `/customers/` link id, then its avatar id, then its name;
  - D-24: an unknown status on a listing card skips that card and makes the snapshot incomplete;
  - D-25: robots.txt is followed; links with `country_id` are read, never requested;
  - D-26: the parsers read English labels;
  - D-27: the no-partners notice counts as empty only when a complete country list confirms it;
  - D-28: a country snapshot is complete only with every page, every card in scope, and the site's count;
  - D-29: the listing card decides when a metric is unknown.
- **Stage 05 decisions** ([assumptions.md](assumptions.md)):
  - D-30: recorded dates are the UTC date on which the page is read (replaces A-20);
  - D-31: when a partner's own page is read: new partners in the same run; a changed card hash sets the flag; flagged and 7-day-old pages;
  - D-32: retry limits for units and for validation re-scrapes;
  - D-33: without a page source the worker attempts nothing and marks runs as waiting;
  - D-34: run end states and one note per run;
  - D-35: claims are row locks, no lease;
  - D-36: an empty-country notice is confirmed by the country list read in the same unit; a country missing from a complete list has its partners archived.
- **Stage 06 decisions** ([assumptions.md](assumptions.md)):
  - D-37: website data and demo data are shown one at a time, demo with a banner;
  - D-38: everyone sees the run state and waiting reason; managers also see the queue and Sync Now;
  - D-39: the dashboard is the first menu, with its own reader group;
  - D-40: no sums or averages of the partner metrics (unknown values are stored as 0);
  - D-41: the bucket keys carry their order;
  - D-42: the four charts use a graph view without toolbar and with fixed status colors; ranking ties follow the country order in the database.
- **Stage 07 decisions** ([assumptions.md](assumptions.md)):
  - D-43: Show Amount Currency is refused with Hierarchy Only Parents;
  - D-44: account prefixes use the account-code alphabet, are trimmed, at most 64 characters, de-duplicated, and match literally and case-sensitively;
  - D-45: the company must be one of the user's companies and active in the company switcher;
  - D-46: Account Level Up To exists only with Hierarchy Only Parents, and is required then;
  - D-47: the Preview, PDF and XLSX buttons validate, then say that the output is not available yet, until Stage 09 (superseded in Stage 09 by D-54);
  - D-48: Skip Zero Balance hides a row only when its opening, gross movement debit and credit, and ending are all zero;
  - D-49: with currency rows, netting happens per row, so netted totals can differ while balances reconcile;
  - V-08: `account_reports` brings `accountant` and `account_accountant`, whose fiscal-year override the contract follows.
- **Stage 08 decisions** ([assumptions.md](assumptions.md)):
  - D-50: the engine requires the accounting read-only group, like the standard Trial Balance;
  - D-51: with currency rows, an account without items is listed in its own currency or the company currency;
  - D-52: the carry-forward is computed only when the earnings row is in the report; without an earnings account, a warning;
  - D-53: the engine is a plain service on the ORM; the `account_reports` handler that renders it is Stage 09.
- **Stage 10 decisions** ([assumptions.md](assumptions.md)):
  - D-64: website downloads run by default and can be paused in Settings; paused on `azk_ee24`;
  - D-65: the page download's bounds, headers (gzip only) and failure kinds;
  - D-66: users with a branch but not its root company are supported (accounts searched with an explicit order).
- **Stage 11 and 12 decisions** ([assumptions.md](assumptions.md)):
  - D-67: the default edition is the target; a repeated setup installs what is missing;
  - D-68: the acceptance ran in a separate Compose project;
  - D-69: failure notes follow the recipient's preference; the README explains mail delivery;
  - D-70: no license file until Q-06 is answered.
- **Stage 15 decision** ([assumptions.md](assumptions.md)):
  - D-71: publish the history and author metadata unchanged, with both tags, and without a license file.
- **Stage 09 decisions** ([assumptions.md](assumptions.md)):
  - D-54: our report record and custom handler in the standard framework; competing standard filters off; per-currency totals as lines;
  - D-55: our PDF company block, options block and grouped column header;
  - D-56: our XLSX sheet for this report only;
  - D-57: exports follow the preview's search and folded groups;
  - D-58: no stored results, every request recalculates as the user;
  - D-59: the demo company, created once at install;
  - D-60: custom fiscal years and branches kept for Stage 10, and two standard-framework limits;
  - D-61: the standard rounding unit is kept and printed, the XLSX keeps exact numbers;
  - D-62: analytic fields only with Odoo's Analytic Accounting setting;
  - D-63: unit tests capture the PDF's HTML; real PDFs are checked on the running server.

## Corrections applied

- **R0, 2026-11-01:** switched the project from Egyptian Arabic explanations to English-only output. AGENTS.md rules 7 and 9 now match the revised kit, the Stage 00 English handoff is in [handoffs/stage_00_en.md](handoffs/stage_00_en.md), and [ai/README.md](ai/README.md) records the change. The kit-root CLAUDE.md (outside this repository) was aligned as well. No scope, requirement or completion status changed, and the historical Stage 00 transcript is unchanged.
- **Stage 01B, 2026-11-03:** Enterprise replaced the Community assumption. AGENTS.md has a dated clarification, and the kit-root CLAUDE.md was aligned. The Stage 00 and 01 transcripts are unchanged; Stage 01 results remain baseline evidence.

## Missing inputs

The original views specification (M-01), the Trial Balance mockup (M-02) and the `azk_zkteco_machine_proxy` documentation example (M-03) were not supplied and have not been read. The company-supplied archive contains only a byte-identical copy of the assessment PDF, nothing more. Details in [assumptions.md](assumptions.md).

## Open items

- **Disk space:** resolved by the user before the 2026-11-05 continuation. C: had 17 to 19 GB free during that work, and 13 GB during Stage 02. The drop happened between the two sessions and was not investigated. On 2026-11-08, C: had 14 GB free before Stage 03's two test runs and 9.7 GB after them. Docker's virtual disk (`docker_data.vhdx`, shared with another project) was 14.6 GB on 2026-11-03 and 15.4 GB after the runs, so it explains at most 0.8 GB of the drop; the rest is not attributed. Keep several GB free before long test runs (see [environment.md](environment.md)).
- **After a machine restart:** the Compose services use `restart: "no"`, so `scripts/dev.sh start` is needed once Docker Desktop is up (found on 2026-11-08, after the restart of 2026-11-06).
- **Analytic Accounting is off on `azk_ee24`:** so the wizard's Analytic Accounts field and the preview's analytic dropdown are hidden there (D-62). To try them, enable Accounting > Configuration > Settings > Analytic Accounting. Stage 10 tried them in a browser on a disposable database with the setting on (review finding RF-15).
- **Website downloads are paused on `azk_ee24`** (D-64): its run 1 (2026-11-10) waits with that reason. Untick Settings > Partner Monitor > Pause Website Downloads only to start a real, full sync from this machine (about 330 listing pages and, the first time, about 4,500 partner pages, at one request per 3 s or more).
- **Memory:** in Stage 09 the CLI stopped a background test run when the machine was critically low on memory. Close unused applications before long runs; the browser checks need about 0.5 GB more.
- **Failure notes and mail:** with Odoo's default "Handle by Emails" and no outgoing mail server, a failure note stays on the run's chatter and its email fails (O-01, D-69). Documented in README section 7 (Stage 12): configure a mail server, or set the recipient to "Handle in Odoo".
- **The candidate's decisions** ([release_checklist.md](release_checklist.md) section 4): decided on 2026-11-17, before the push: keep the Git identity and the history unchanged (the work email address is public, in every commit and four documents), and push both tags. Still open: the license file (Q-06, D-70), the manual check (TP-G-05, T-19), the questions Q-02 to Q-06 (the repository was published with the documented defaults), and the supplied archive.
- **Acceptance project (Stage 11):** the Compose project `azk-stage11-acc` is stopped, and its volumes are kept for inspection (297 MB of PostgreSQL data and 21 MB of filestore, measured with `docker system df -v`). Delete it with `docker compose -p azk-stage11-acc down --volumes` from its export folder, when no longer needed (the user's decision).
- **Browser check of the Trial Balance (user, recommended):** the walkthrough is in [handoffs/stage_09_en.md](handoffs/stage_09_en.md).
- **Browser check of the Partner Monitor UI (user, recommended):** the agent's headless check covered the dashboard (Stage 06). Still for the user, in a normal browser: the country selector, a click on a chart bar, the reader role, the pivot and graph views, a partner form and Settings > Partner Monitor (steps in the Stage 06 handoff).
- **Compatibility blocker:** resolved on 2026-11-05 for the matched pair (all eight `TestTrialBalanceReport` tests pass). The Stage 01B pair still fails `test_trial_balance_comparisons` and stays blocked; it is kept only for `azk_ent`.
- **Browser check (user, recommended):** the user reported a browser check of the Stage 01B environment (no detailed results given). The matched-pair environment on port 8071 has not been checked in a browser yet; steps are in [enterprise_transition.md](enterprise_transition.md).
- **Enterprise source verification:** the Enterprise files cannot be checked against an official baseline without access to the private repository. Only the tarball's file list and timestamps support them.
- **Matched Enterprise build for the 2026 core:** question Q-05 for the team lead. It would be an alternative to the 2024 pair.
- **Extracted archive:** no runtime needs `<kit-root>/odoo/odoo18`: the matched pair uses the official Community source and the 620-module Enterprise copy. Deleting it (1.76 GB) is the user's decision, and only sensible if the original archive file is kept elsewhere.
- **Decision for the user:** the supplied archive contains an earlier implementation of this assessment's modules (`projects/assessment/`, not opened or used). Whether to mention it to the team lead is the user's decision.
- **Subscription:** `azk_ee24` and `azk_ent` are unregistered trials; registering needs the employer's subscription code.
- Clarifications Q-02 to Q-06 for the team lead are drafted in [assumptions.md](assumptions.md) and not yet asked. None blocks Stage 06.
- Ambiguities D-01 to D-07 were resolved in Stage 02, and D-08 to D-17 were added and decided ([assumptions.md](assumptions.md)).
- **Verification still ahead:**
  - The live partners site was checked on a small manual sample in Stage 04 (A-19) and through the module and the worker in Stage 10 ([live_site_notes.md](live_site_notes.md)); a full live sync has not been run from this machine, on purpose (D-64).
  - The `account_reports` display and export hooks were verified and used in Stage 09 (column groups, the PDF templates, the XLSX writer, the preview filter component); the fallback of [architecture.md](architecture.md) 4.7 was not needed.
- Manifest author `fahimnox` and license LGPL-3 are unconfirmed defaults (A-06). The license of `azk_dynamic_trial_balance`, which will depend on the OEEL-1 module `account_reports`, is question Q-06.
- Commits use the global Git identity `fahimnox <mohamed.fahim@noxholding.com>`, which is public since Stage 15 (2026-11-17): the user chose to publish the author metadata and history unchanged.
- Not exercised: `scripts/dev.sh source` itself (an equivalent command made the source copy).

## Host facts

Inspected in Stage 01 and rechecked in Stage 01B; details in [environment.md](environment.md).

- Windows 11 Pro 10.0.26200, Intel Core i7-8650U (4 cores, 8 threads), 15.9 GB RAM. Drive C: had 18.0 GB free before Stage 01, 10.2 GB after it, 7.9 GB at the start of Stage 01B (after the archive had been extracted) and 2.0 GB at its end. The files and databases created in Stage 01B account for about 0.65 GB. The rest is not attributed: Docker's virtual disk (shared with the other running project, size at the start of the stage unknown) grew during the install and test runs, and other Windows activity may also contribute.
- The agent works through Git Bash (installed per user under `%LOCALAPPDATA%\Programs\Git`) and PowerShell. In PowerShell, `bash` starts WSL, not Git Bash.
- Docker Desktop 29.4.0 with Compose v5.1.1 (WSL2 backend). On 2026-11-15 the engine reported version 29.9.2, after a restart that stopped all containers at 06:20 UTC. Another project (ots-local) uses 127.0.0.1 ports 5433, 8000 and 9000; ports 8069 and 8070 were free. On this host Docker Desktop creates missing bind-mount folders even with `create_host_path: false`.
- A host PostgreSQL 18 service listens on port 5432; this project does not use it.
- Host `python` 3.12.0, `git` 2.53.0.windows.2 and `pdftotext` are available. wkhtmltopdf is not installed on the host; the Odoo image provides it.
- Since Stage 09, a private virtual environment `runtime/tools/venv` (outside git) holds websocket-client 1.9.2, openpyxl 3.1.5 and PyMuPDF 2.1, used by `scripts/tb_preview_smoke_check.py` to read the downloaded files and render PDF pages to PNG. The image has PyPDF2 2.12.1, openpyxl 3.1.2 and XlsxWriter 3.1.9.
