# Demo script (about 7 minutes)

_Written in Stage 12 (2026-11-16). Every number below comes from a check that ran, or is marked as a hand calculation. Times are a guide for a 5 to 8 minute demo._

## What the demo shows

- **Partner Monitor:** the dashboard with its shared filters and four charts; one live partner with its history and references; one failure and its recovery, with the note it produced.
- **Dynamic Trial Balance:** the wizard; the preview with Bank at 1,200.00 (posted only), then 1,000.00 (drafts included); the hierarchy; the currency rows; the PDF and XLSX.
- **Where the code is,** and what the tests cover.

## Where each piece of data comes from

Say these labels aloud when the data appears:

- **DEMO:** records installed with the modules' demo data. Partner Monitor demo records are named "Demo ...", flagged as demo and shown under "Demo data" with a banner. The Trial Balance demo data is the company "AZK Trial Balance Demo (EGP)".
- **LIVE:** pages read from www.odoo.com by the module, on the date stated. Shown under "Website data".
- **FIXTURE:** trimmed copies of live pages saved on 2026-11-08 (`addons/azk_odoo_partner_monitor/tests/fixtures/`), used by the tests and the restart check. Never shown as website data in the development database.
- **SIMULATED:** a network outage produced by a script. No request is sent.

## Before the demo (not timed)

Choose one of three set-ups. Option A is ready on the candidate's machine; option B rebuilds it from a clean checkout; option C needs no network.

### Option A: the prepared acceptance copy (this machine)

Stage 11 left a complete copy in its own Compose project, `azk-stage11-acc`, with its own database ([acceptance_results.md](acceptance_results.md)). Its state, read again on 2026-11-16 (read-only SQL):

- DEMO: 50 Partner Monitor demo partners (47 active) and the Trial Balance demo company with 16 entries.
- LIVE (read on 2026-11-16): Andorra and its 2 partners; BDR GROUP SLU with 17 active references.
- Run 1 (Manual): ended **Partial** after a SIMULATED outage (5 errors), notified the administrator, then recovered by a manager's Retry with 1 LIVE request: now **Done**.
- Run 2 (Validation): ended **Failed** after a SIMULATED outage (5 errors), notified "Acceptance PM Manager", then recovered the same way: now **Done**.
- Run 3 (Manual): queued by a Sync Now during the access checks; **waiting**, because Pause Website Downloads is on.
- The notes: run 1's went to the administrator, whose preference is "Handle by Emails"; with no mail server its email failed (status "exception"). Run 2's went to "Acceptance PM Manager" ("Handle in Odoo"): delivered to that user's inbox.

Start it (stop the development server first if memory is short, with `scripts/dev.sh stop` in the repository):

```text
cd <kit-root>/runtime/acceptance/stage11_3b92f98
COMPOSE_PROJECT_NAME=azk-stage11-acc scripts/dev.sh start
# open http://127.0.0.1:8073/web/login  (admin / admin)
```

- **Do not untick Pause Website Downloads in this copy:** run 3's queued country list would start a full crawl of the website.
- The acceptance users' password was random and was never stored. To show "Acceptance PM Manager"'s inbox, set a new password for that user first (Settings > Users & Companies > Users > the user > gear menu > Change Password) and log in in a private window.
- Stop it afterwards with `COMPOSE_PROJECT_NAME=azk-stage11-acc scripts/dev.sh stop` in the same folder.

### Option B: rebuild the same state from a clean checkout

About 15 minutes after the quick start, and about 6 requests to www.odoo.com (robots.txt and 4 pages for the LIVE sample, 1 page for the recovery). These are the Stage 11 acceptance scripts; each script's header explains it. They write to the database, so use them only on a fresh copy (for example a second copy with its own project name, [README section 6](../README.md#6-a-second-isolated-copy-and-reusing-volumes)), never on a database you want to keep unchanged.

1. Follow the quick start of the [README](../README.md#4-installation-from-a-clean-checkout). It creates `azk_ee24` with the demo data.
2. Stop the web server, so that its scheduled jobs do not act between the steps: `scripts/dev.sh stop`.
3. In the same bash session, choose a password for the demo users (it is never printed or stored) and give the database's creation date, which the scripts check before they write:

```text
export ACC_PASSWORD='choose-one'
export ACC_DB_CREATED_AFTER=YYYY-MM-DD        # the day azk_ee24 was created by setup
RUN="docker compose run --rm -T"
SHELL_ARGS="odoo-ee-20241208 odoo shell --database=azk_ee24 --no-http"
$RUN -e ACC_PASSWORD -e ACC_DB_CREATED_AFTER $SHELL_ARGS < scripts/acceptance_users.py
$RUN -e PM_DEMO_PHASE=prepare -e ACC_DB_CREATED_AFTER $SHELL_ARGS < scripts/acceptance_pm_demo.py
$RUN -e PM_LIVE_KEEP=1 -e PM_LIVE_DB_CREATED_AFTER=$ACC_DB_CREATED_AFTER $SHELL_ARGS < scripts/pm_live_check.py
$RUN -e PM_DEMO_PHASE=fail -e ACC_DB_CREATED_AFTER $SHELL_ARGS < scripts/acceptance_pm_demo.py
$RUN -e PM_DEMO_PHASE=recover -e ACC_DB_CREATED_AFTER $SHELL_ARGS < scripts/acceptance_pm_demo.py
scripts/dev.sh start
```

What each step does:

- `acceptance_users.py`: creates `acc_pm_reader`, `acc_pm_manager` ("Handle in Odoo"), `acc_tb_reader` and `acc_no_rights`.
- `prepare`: through the Settings form's own code, ticks Pause Website Downloads and makes `acc_pm_manager` the Failure Recipient.
- `pm_live_check.py` with `PM_LIVE_KEEP=1`: the LIVE bounded sample through the real worker (at most 8 requests; in Stage 11, robots.txt and 4 pages): the country list, Andorra and one partner page. It keeps the result and leaves the second partner's page queued.
- `fail`: the SIMULATED outage on that queued page: 5 tries on a simulated clock, then the unit is failed, the run ends partial and its note goes to `acc_pm_manager`.
- `recover`: `acc_pm_manager`'s Retry, then the real worker reads the page LIVE (at most 2 requests). The run ends done and is not notified again.

Skip `recover` if you want to press Retry yourself during the demo; see step 3 of the walkthrough. The result is the state of option A with one recovered run instead of two, and no run 3.

### Option C: offline fallback (no network)

Without network access there is **no LIVE data and no live recovery**. Say so at the start. What still works:

- The Partner Monitor dashboard and partner forms on DEMO data (the quick start database).
- The whole Trial Balance part (DEMO company, no network needed).
- A failure-and-recovery story from FIXTURE pages, shown as terminal output: before the demo, run `scripts/dev.sh test azk_odoo_partner_monitor` (it creates the disposable database `azk_ee24_test`; about 3 to 8 minutes on the test machine), then `scripts/restart_check.sh` (about 2 minutes), and keep its output. It shows:
  - run A: a country unit whose saved pages are incomplete fails its last try, the run ends failed and posts exactly one note;
  - run B: the worker process is killed with SIGKILL in the middle of a batch; after the restart only the interrupted batch's units run again; no history row, reference or note is duplicated;
  - 12 of 12 checks PASS (Stages 05, 10 and 11).
- Optional, to show run A in the browser: a temporary server for the disposable database (Stage 10 command), then http://127.0.0.1:8072 (admin / admin):

```text
docker compose run -d --rm --name azk-demo-test -p 127.0.0.1:8072:8072 odoo-ee-20241208 \
    odoo --http-port=8072 --database=azk_ee24_test --db-filter=^azk_ee24_test$ --max-cron-threads=0
docker stop azk-demo-test          # afterwards
```

Limitations to state in option C: the pages are saved copies from 2026-11-08, the failure is a missing saved page rather than a network outage, and the recovery is a crash recovery rather than a manager's Retry.

## The walkthrough

Steps for option A (port 8073). For option B use port 8071; for option C see the notes in each part.

### 1. Introduction (0:00 to 0:30)

- Two addons on Odoo 18.0 Enterprise (the matched pair of Community `4e5027c1` and Enterprise build 18.0+e.20241208).
- 261 automated tests pass in a fresh database (147 Partner Monitor, 114 Trial Balance); the install was accepted from a clean checkout.
- The data labels: DEMO, LIVE, FIXTURE, SIMULATED.

### 2. Partner Monitor dashboard (0:30 to 2:15)

1. Log in as admin. Open the **Partner Monitor** app: it opens on the **Dashboard**.
   - Option A shows "Website data (2)" selected: the LIVE Andorra sample of 2026-11-16, with four charts. With one country, the dashboard says "Fewer than 5 countries match: both groups list all of them."
2. Click **"Demo data (47)"**. The blue DEMO banner appears. Expected (from the dashboard tests, `test_demo_data_ranking`): 47 active partners in 12 countries; Top 5 Epsilon 8, Zeta 7, Eta 6, Alpha 5, Iota 5; Bottom 5 Beta 1, Gamma 1, Nu 1, Mu 2, Kappa 3 (each "Demo Country ...").
3. **Status: Gold**, then **Year First Seen: 2025**. All four charts and both tables change together. Expected (`test_walkthrough_gold_2025`): Top 5 Epsilon 3, Zeta 2, Alpha 1, Gamma 1, Iota 1; Bottom 5 Alpha 1, Gamma 1, Iota 1, Kappa 1, Zeta 2. Six countries match, so the notice says "Only 6 countries match: the Top 5 and Bottom 5 groups share countries."
4. Click Epsilon's bar in the Top 5 chart: the list of its partners opens, 3 Gold partners first seen in 2025. Go back. **Clear filters.**
5. Point at the lower charts: the project-size distribution (Below 5, 5 to below 11, 11 to below 25, 25 and above, Unknown) of the same Top 5 and Bottom 5 countries.
6. **Partners**, filter **Website Data**, open **BDR GROUP SLU** (LIVE, option A): the Status History tab (its initial row) and the References tab (17 references, read on 2026-11-16).
   - Option C: open any demo partner instead, for example one of Epsilon's.

Code: `models/dashboard.py` (`get_dashboard_data`: one domain, grouped queries as the user, the reader check), `static/src/dashboard/` (the client action), `views/dashboard_views.xml` (the four graph views), `models/partner.py` and `models/ingest.py` (history and references).

### 3. A failure and its recovery (2:15 to 4:00)

1. **Partner Monitor > Sync > Runs.** Option A lists Run 1 (Manual, Done), Run 2 (Validation, Done) and Run 3 (Manual, Running, with a waiting reason).
2. Open **Run 1**. Read the note in its chatter: "Partner Monitor Run 1 (Manual) ended as Partial: 3 units done, 1 failed, 0 pending, 5 errors logged.", then the failed scope with its last error, the retry policy and the recovery actions.
   - The **Errors** tab: 5 rows, "FetchConnectionError", each saying the outage was SIMULATED and no request was sent.
   - The **Work Items** tab: the partner page unit is now done.
3. Tell the story: the page failed 5 times, 15 to 120 minutes apart (on a simulated clock); the unit was marked failed; the run ended partial and posted **one** note. A manager pressed **Retry** on the failed work item (Sync > Work Items, filter Failed). The worker read the page LIVE with 1 request, the run ended done, and it was not notified a second time.
   - To press Retry live (option B without `recover`): Settings > Partner Monitor > untick Pause Website Downloads > Save; Sync > Work Items > Failed > the unit > **Retry**; wait about a minute and reload the run (1 LIVE request); then tick Pause Website Downloads again. Never do this in option A (run 3 would start a full crawl).
4. **Where the note went** (chatter, inbox, email):
   - Run 1's note is on its chatter. It was addressed to the administrator, whose preference is "Handle by Emails"; with no mail server, the email failed. So it is not in the administrator's Discuss inbox.
   - Open **Run 2**: the same kind of note, addressed to "Acceptance PM Manager", whose preference is "Handle in Odoo": it reached that user's Discuss inbox (optional login, see option A).
   - The fix for a real deployment: an outgoing mail server, or "Handle in Odoo" for the recipient ([README section 7](../README.md#failure-notifications-chatter-inbox-and-email)).
5. Open **Run 3**: the "Waiting" banner, "website downloads are paused". The queue is kept and nothing is marked failed.
   - Option C: show the restart check's output instead (run A failed with one note; run B killed and replayed without duplicates).

Code: `models/worker.py` (`_process_queue`, `_run_unit`, `_record_unit_failure`), `models/work_item.py` (`_mark_failed_attempt`, `action_retry`), `models/common.py` (`retry_delay`), `models/sync_run.py` (`_finalize`, `_notify_failure`, `_post_note`), `data/ir_cron.xml`, and [resilience.md](resilience.md).

### 4. Dynamic Trial Balance (4:00 to 6:30)

DEMO data: the company "AZK Trial Balance Demo (EGP)", January 2026.

1. In the company switcher (top right), select **AZK Trial Balance Demo (EGP)** as the current company.
2. **Accounting > Reporting > Audit Reports > Dynamic Trial Balance.** Show the fields and their help texts. Set **Date From 01/01/2026**, **Date To 01/31/2026**, Company "AZK Trial Balance Demo (EGP)" and tick **Skip Zero Balance**. Leave Include Unposted Entries unticked. Click **Preview**.
3. Expected, posted entries only, row **101401 Bank** (checked in the browser in Stages 09 and 11, and in the committed sample `samples/stage09_trial_balance_amount_currency.xlsx`):
   - Initial Balance: Debit 1,000.00, Credit 0.00, Balance 1,000.00;
   - Jan 2026: Debit 500.00, Credit 300.00, Balance 200.00;
   - End Balance: Debit **1,200.00**, Credit 0.00, Balance 1,200.00.
   - The Total row is balanced in each column group: 1,700.00, 12,750.00 and 7,300.00 on both sides (a hand calculation from the demo entries; the 12,750.00 and 7,300.00 also appear in that committed sample).
4. Open the **"Posted Entries"** options button (sliders icon) and tick **Draft Entries**; the button now reads "With Draft Entries". The report recalculates: Bank's period credit becomes 500.00 and it ends at **1,000.00** (the draft payment of 200.00 counts; the cancelled 400.00 and the February 50.00 never do). Totals: 1,700.00, 13,450.00 and 7,800.00 (checked in Stage 11 and in `samples/stage09_trial_balance.xlsx`).
5. **Trial Balance > Hierarchy and Subtotals:** the groups 1 Assets > 10 Current Assets > 101 Cash and Receivables > 1014 Bank and Cash > 10140 Bank Accounts appear above Bank, with subtotals. Fold **10140 Bank Accounts**: Bank is hidden; unfold it again.
6. **Trial Balance > Show Amount Currency** (untick Draft Entries first to match the sample): 101000 Current Assets now has one row per transaction currency, EGP, EUR and USD, with the Amount Currency "Movement" column: EUR 50.00 and USD 60.00 for January, and one total per currency. Different currencies are never added together.
7. Click **PDF**: a landscape page with the report company's name and address, "Period: From 01/01/2026 to 01/31/2026", every option, and the column groups. Then the **gear menu > Download Excel**: the same lines, options above the table, numbers as numbers.
8. Optional, if asked about the analytic filter: it appears with Accounting > Configuration > Settings > Analytic Accounting; Stage 10 checked it in a browser (March 2026, Sales Department: whole journal items are selected, as in the standard report).

Code: `models/trial_balance_wizard.py` (the wizard), `models/report_options.py` (`normalize_options`, used on every request), `models/trial_balance_engine.py` (`compute`: three grouped queries as the user), `models/trial_balance_report_handler.py` (`_dynamic_lines_generator` feeds the standard preview, PDF and XLSX), `models/account_report.py` (our XLSX sheet), `data/pdf_export_templates.xml`, `models/demo_data.py`, and [calculation_contract.md](calculation_contract.md) (the Bank example by hand in section 14).

### 5. Tests, limits and questions (6:30 to 7:30)

- Show `addons/azk_dynamic_trial_balance/tests/common.py`: the hand-calculated constants of TB-BASE; the tests check that the standard Trial Balance, our engine and all three outputs give them.
- 261 tests, no network in tests (saved pages, fake HTTP session). The run: `scripts/dev.sh test`.
- State the limits: no full live crawl was run (bounded samples only); the original views specification and the wizard mockup were never supplied; the major version 18.0 and several defaults are our assumptions, not approvals; the questions Q-02 to Q-06 are still open ([README section 12](../README.md#12-assumptions-open-questions-and-limitations)).

## If something goes wrong during the demo

- **The page does not load:** run `scripts/dev.sh status`; after a Docker Desktop restart, run `scripts/dev.sh start` again. The first page after a start builds the asset bundles and can take about a minute.
- **The wizard refuses the company:** the company must be active in the company switcher (step 4.1).
- **No Analytic Accounts field:** expected; the Analytic Accounting setting is off (step 4.8).
- **A run says "waiting":** downloads are paused; that is the intended safe state.
- **No network** in the middle of the demo: switch to option C's material; the Trial Balance part needs no network.
