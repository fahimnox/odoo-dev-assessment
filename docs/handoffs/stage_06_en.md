# Stage 06 handoff: Partner Monitor dashboard

Date: 2026-11-10. Edition: `enterprise-20241208` (port 8071). Status: **DONE**. Stage 04 stays **PARTIAL** (no page-download module, so no live data). The dashboard shows the demo data and the real sync state.

## Menu path

- **Partner Monitor > Dashboard.** It is the app's first menu, so the app tile on the home screen opens it directly. You need the group "Partner Monitor / Reader"; the administrator is a manager.
- **URL:** http://127.0.0.1:8071/odoo, then the "Partner Monitor" tile. Login: admin (the local development login).

## Walkthrough: Gold, one year, one country, and its count

Uses the demo data of `azk_ee24`. The dashboard opens on "Demo data (47)", because there is no website data yet.

1. **Open the dashboard.**
   - A blue banner says the records are synthetic demo data.
   - A yellow banner says the sync is waiting: "no page source is available ...". That is run 1, queued by Sync Now during this stage.
2. **Click "Gold", then "2025"** (Status and Year First Seen rows).
   - The summary reads "9 active partners in 6 countries match the filters".
   - A note says the Top 5 and Bottom 5 groups share countries, because only 6 countries match.
   - Top 5: Demo Country Epsilon 3, Zeta 2, then Alpha, Gamma and Iota with 1 each. Kappa also has 1, but ties are broken by country name, so it is sixth.
   - Bottom 5: Alpha, Gamma, Iota, Kappa (1 each), then Zeta (2).
   - All four charts changed: gold bars only, and the project-size charts of the same two groups.
3. **Click "Demo Country Epsilon"** in the Top 5 table.
   - The partner list opens, titled "Demo Country Epsilon: matching partners", with the pager at "1-3 / 3".
   - The three partners are Gold and were first seen in 2025: Demo Partner Epsilon 1, 2 and 3.
4. **Verify the count independently**, without the dashboard: Partner Monitor > Partners, then in the search:
   - the filters "Gold" and "Demo Data";
   - type "2025" and choose "Search Year First Seen for: 2025";
   - type "Epsilon" and choose "Search Country for: Epsilon".
   The pager shows 3. The list shows active partners only, as the dashboard counts. Epsilon's archived partner (Demo Partner Epsilon 9) is Silver and first seen in 2023, so no filter here would count it.

The test `TestDashboardDemoData.test_walkthrough_gold_2025` checks these numbers automatically.

## Browser checks

**Performed by the agent:** headless Chrome 157 (installed on this machine), driven through the DevTools protocol by `scripts/ui_smoke_check.py` against `azk_ee24`.

- **Run 4, 7 of 7 PASS.** Its code differed from the final code only by one space character in the template.
  - no asset or module loading error;
  - the app tile opens the dashboard, with four charts;
  - the charts use the dashboard graph view (no toolbar);
  - the demo banner is shown;
  - Gold and 2025 are applied to all four charts (the numbers above);
  - Epsilon's partner list holds the 3 partners the dashboard shows;
  - no JavaScript error.
- **Run 2, with `--sync`:** "Sync Now" queued Run 1 (Manual), and after the worker job ran, the dashboard showed "Sync waiting: no page source is available ..." (PASS).
- **Screenshots** (no secrets; demo data): `docs/screenshots/stage06_dashboard_demo.png`, `stage06_dashboard_gold_2025.png`, `stage06_country_partners.png`.
- **Problems these runs found, fixed before run 4:**
  - the first screenshot showed squashed charts, a repeated toolbar, and status colors that changed between charts;
  - a later run showed a module-loading error that the first version of the check had missed: the custom graph view must sit in Odoo's lazy view bundle.
- **The final browser run was BLOCKED on 2026-11-10.** After the disk-full event (below), the host answered a page in 24 s, with 2 GB of RAM free. The check timed out while loading the login page.
- **Rerun on 2026-11-15, on the final code: 7 of 7 PASS.** Run by the agent before Stage 07, at commit `3222285` with a clean working tree, against `azk_ee24` on port 8071. Drive C: had 54 GB free.
  - The containers had stopped three days earlier, so `scripts/dev.sh start` started them first; the login page answered after about 35 s.
  - The check ran without `--sync`, so it changed no data.
  - The same seven checks as run 4 passed, with the same numbers: 47 active partners in 12 countries without filters, and 9 partners in 6 countries with Gold and 2025 (Epsilon 3, Zeta 2, then Alpha, Gamma and Iota with 1 each). Epsilon's list showed "1-3 / 3".
  - The agent viewed the Gold and 2025 screenshot. The layout, the status colors and the overlap note were correct.
  - The screenshots and the full output were saved outside the repository (`<kit-root>/runtime/logs/`). The committed screenshots are unchanged.

**Manual checks for you (NOT RUN by the agent):**

1. **Normal browser, normal window size:** the layout of the filters, the tables and the charts, in a light and a dark color scheme.
2. **The Country filter:** open the selector, type "Eps", pick Demo Country Epsilon, then also pick Zeta. The tables and all four charts should show only those countries. Expected with no other filter: Epsilon 8, Zeta 7.
3. **A chart bar:** click Epsilon's Gold segment in the Top 5 status chart. The list of Epsilon's Gold partners should open (3 with all years).
4. **The reader role:** in Settings > Users, create a user with "Partner Monitor: Reader" only, and log in with it.
   - The dashboard shows the same data and the waiting banner, but no "Sync Now" button and no queue numbers.
   - Partner Monitor > Sync > Work Items is not in the menu.
5. **The other views:** the pivot and graph views of Partners and Status History, and the pivot of References. Check them through the view switcher of each list.
6. **Run 1's note:** Partner Monitor > Sync > Runs > Run 1 > chatter. One note says the run is waiting. The administrator's preference is email, so Odoo queued an email for it. No mail server is configured, so the email cannot leave; it will stay in the outgoing queue as failed, like the 7 older failed emails of this database.

## How it works: menu, action, client action, aggregation

- **Menu:** "Partner Monitor" (group Reader) opens its first child, "Dashboard" (group Reader). The client action has no model, so the menu needs the group itself (D-39). The first test run found this gap.
- **Action:** `dashboard_action`, an `ir.actions.client` with tag `azk_odoo_partner_monitor.dashboard`.
- **Client action:** the OWL component `PartnerMonitorDashboard` (`static/src/dashboard/dashboard.js`) keeps only the filter values. It calls `get_dashboard_data(filters)` and mounts four standard graph views (`@web/views/view`), each with a domain computed by the server.
- **Model aggregation:** `models/dashboard.py`:
  - checks the Reader group and drops invalid filter values (it accepts no domain);
  - builds one domain: active partners, active countries, one data source, then the filters;
  - ranks countries with `_read_group(..., order="__count desc, country_id")` (and `asc` for the Bottom 5) as the user;
  - returns, for each cohort, its rows, its bucket counts and its chart domain (the shared domain plus the cohort's countries).
  The graph views then call `web_read_group` on those domains as the user, so a chart and its table read the same records.
- **Django analogy:** a view function that validates query parameters, builds one QuerySet, uses `.values("country").annotate(Count("id")).order_by("-count", "country__name")`, and hands that same QuerySet to four chart widgets.
- **Details:** [../architecture.md](../architecture.md) 5.13.

## One country sync, a status change and a reference change (evidence)

- **Source: saved live-derived fixture pages** (`tests/fixtures`, read from odoo.com on 2026-11-08) and variants made in code from them. No live page was read.
- **Run:** `scripts/fixture_sync_demo.py`, through the real worker, on the disposable `azk_ee24_test`. Nothing was committed. Output: `<kit-root>/runtime/logs/stage06_fixture_sync_demo.log`.

1. **Country sync, day 1 (2026-11-10).** Andorra's listing page: before, 0 partners; after, BDR GROUP SLU and Process Control Technology Andorra, both Ready, each with one initial history row. The country shows listed 2, found 2, validation matched.
2. **Status change, day 2.** The same page with BDR GROUP SLU shown as Silver: the history is now "initial ready on 2026-11-10, promoted ready -> silver on 2026-11-11". The other partner is unchanged.
3. **Reference change.**
   - Day 1, RoayaTec's page (3 of 135 references): 3 references added; expected 135, found 3; validation mismatch; flagged.
   - Day 2, a variant that lists 2 references and says "References - 2": AROSCENT FOR FRAGRANCE S.A.E. is removed (removed on 2026-11-11). Expected 2, active 2, matched; the flag is cleared.

## Automated tests

- `scripts/dev.sh test azk_odoo_partner_monitor` on the final code: **PASS**, "0 failed, 0 error(s) of 129 tests", 0 warning lines.
  - That is 113 earlier tests plus 16 new ones in `tests/test_dashboard.py`.
  - The run took 8 min 27 s on a slow host; the previous run took 3 min 31 s.
  - The first run had 1 failure (the menu group), fixed before the later runs.
- **What the new tests check:**
  - ranking after the filters, and the name tie-break, compared with the graph view's own group order;
  - countries without a match take no part;
  - fewer than 5 and fewer than 10 countries;
  - the empty result;
  - chart totals equal the filtered records: `web_read_group` called as each graph view calls it, compared with a plain search;
  - bucket boundaries (4.99, 5, 10.99, 11, 24.99, 25, a known 0, unknown);
  - invalid filter values and a sent domain are dropped;
  - access: no group refused, reader, manager;
  - demo and website data are never mixed;
  - the sync state, including waiting;
  - the entry point; the views load for readers; the template escapes text;
  - the demo ranking and the walkthrough.
- `scripts/dev.sh update azk_odoo_partner_monitor` on `azk_ee24`: **PASS**, 0 warnings. Afterwards, `azk_ee24` holds version 18.0.1.4.0, 13 demo countries, 50 demo partners and 57 history rows.

## Problems found and fixed

- **The Dashboard menu was visible to users without the Reader group** in Odoo's menu list (`_visible_menu_ids`), because a client action has no model to check. Found by `test_dashboard_is_the_entry_point`; the menu now has the group.
- **Bucket order.** Grouped queries order a selection by its stored key, so the bucket chart would have put "11 to below 25" first. The keys now carry their order (D-41).
- **Status order.** The dashboard first listed statuses in rank order (Ready first); it now lists Gold, Silver, Ready.
- **Chart look.** The first screenshot showed squashed charts, a repeated graph toolbar, and status colors that changed between charts. Fixed with a chart height and a small graph view `js_class` (D-42).
- **Module loading error.** That `js_class` first failed to load: Odoo 18 loads graph views lazily. It now sits in `web.assets_backend_lazy`, as CRM's forecast graph does. The smoke check now fails on Odoo's module-loading error message; its first version had passed despite the error.

## Disk event during this stage

- **What happened:**
  - at about 11:35 UTC, drive C: fell to 0.15 GB free;
  - the largest recent writes were Windows' page file (12.4 GB), Docker's virtual disk (17.6 GB), a 1.84 GB backup of another project (`Desktop\tmp-cor-testing`, not touched), and a CLI update;
  - Docker's VM then stopped our two containers abruptly (exit 255).
- **What I did:**
  - stopped my running jobs;
  - removed only my own temporary browser profiles (16 MB);
  - restarted our services with `scripts/dev.sh start`. PostgreSQL recovered automatically ("database system was not properly shut down; automatic recovery in progress ... ready to accept connections"), and `azk_ee24` was checked intact.
- **Now:** 3.6 GB free. Your other project's containers were already stopped two days earlier and were not changed.
- **Before Stage 07:** please free disk space. The test runs need several GB, and Docker's virtual disk does not shrink by itself.

## Remaining Partner Monitor gaps

- **No live data.** The page-download module is still deferred (Stage 04 PARTIAL). Its mocked-response tests, the synthetic fixtures (login, rate-limit and truncated pages), and a bounded live run are missing.
- **Manual browser checks** 1 to 6 above are NOT RUN by the agent.
- **No JavaScript unit tests.** Odoo's own browser tests need Chrome inside the Odoo container, which this image does not have. The browser check is our own DevTools script, run from the host.
- **One country listing is one unit** (resilience.md, section 13).
- **The original views specification was never supplied** (M-01). Our views are assumption A-16, and question Q-02 is still open.
- **Mail delivery** depends on a mail server, which this local setup does not have.

## Changed files

- **New:**
  - `models/dashboard.py`, `views/dashboard_views.xml`;
  - `static/src/dashboard/` (`dashboard.js`, `dashboard.xml`, `dashboard.scss`), `static/src/dashboard_graph/` (`dashboard_graph.js`, `dashboard_graph.xml`);
  - `tests/test_dashboard.py`;
  - `scripts/ui_smoke_check.py`, `scripts/fixture_sync_demo.py`;
  - `docs/screenshots/` (3 PNG files), this handoff, `docs/ai/stage_06.md`.
- **Updated:**
  - `models/common.py`: buckets, `ensure_reader`;
  - `models/partner.py`: `project_size_bucket`, `first_seen_year`, no aggregation on metrics;
  - `models/country.py`, `models/worker.py` (one summary wording), `models/__init__.py`;
  - `views/menus.xml`, `views/partner_views.xml`, `views/status_history_views.xml`, `views/reference_views.xml`;
  - `demo/partner_monitor_demo.xml`: 9 more countries, 44 more partners, their history;
  - `tests/__init__.py`, and the manifest (18.0.1.4.0, assets);
  - the docs: STATE, architecture (5.13), assumptions (D-37 to D-42, A-16, A-17), requirements matrix, test plan (3.4), `ai/README.md`.

## Comprehension questions

1. Why does the dashboard send filter values to the server instead of a domain, and what still protects the data if someone calls `web_read_group` with a domain of their own?
2. Why can the Top 5 status chart and the Top 5 project-size chart never disagree about which countries they show?
3. Why did the Dashboard menu need its own group when the other menus did not?

## Next stage

Stage 07: Trial Balance wizard and calculation contract. Free disk space first.
