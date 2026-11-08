# Stage 03 handoff: Partner Monitor models, permissions and basic UI

Date: 2026-11-08. Edition: `enterprise-20241208` (port 8071). Status: DONE. No scraping yet (Stage 04).

## What was done

- **Addon `azk_odoo_partner_monitor` 18.0.1.1.0:**
  - the four PDF models with their exact field names and types;
  - supporting models: `sync.run` (with chatter), `work.item` and `sync.error`.
- **Observation API in the models**, which the Stage 05 worker will call:
  - `country._record_observation`;
  - `partner._record_observation`;
  - `partner._sync_references`.
- **Access:** Reader and Manager groups, read-only access rules, four manager actions and Settings for the failure recipient.
- **UI:** list, form and search views for countries, partners, status history, references, runs, work items and errors, plus menus.
- **Demo data:** deterministic and labeled demo.
- **Tests:** 53 automated tests in 6 files.
- **Documentation:**
  - [architecture.md](../architecture.md) 5.10 (as built);
  - decisions D-18 to D-22 in [assumptions.md](../assumptions.md);
  - the requirements matrix and the test plan (section 3.1).

## How to open a partner

1. Open http://127.0.0.1:8071 and log in as `admin`.
2. On the home screen, open the **Partner Monitor** app.
3. Click **Partners** in the top menu. The menu path is **Partner Monitor > Partners**.
4. The list shows the active partners: the 5 active demo partners in `azk_ee24`. The **Archived** filter also shows Demo Partner Ember.
5. Click a row, for example **Demo Partner Aurora**. The form shows:
   - the status, country, website ID and dates;
   - the metrics ("Unknown" when the site gave none);
   - the **Status History** and **References** tabs. Aurora shows Silver, then a promotion to Gold, and the reference "Demo Client South" removed and listed again (two records).

Behind it: the menu `azk_odoo_partner_monitor.menu_partners` (`views/menus.xml`) opens the action `partner_action`. That action shows the list, form and search views in `views/partner_views.xml` for the model `azk_odoo_partner_monitor.partner`. The menu needs the Reader group; `admin` is a Manager, which includes Reader.

## The test for Silver -> Gold -> Gold

- **File and test:** `addons/azk_odoo_partner_monitor/tests/test_status_history.py`, `TestStatusHistory.test_silver_gold_gold_records_initial_then_one_promotion`.
- **Result:** PASS in the full suite run of 2026-11-08 (53 of 53).
- **Run it alone** (documented, not run separately in this stage):

```text
scripts/dev.sh test azk_odoo_partner_monitor /azk_odoo_partner_monitor:TestStatusHistory.test_silver_gold_gold_records_initial_then_one_promotion
```

## What is stored after each observation

The test observes the same partner (website ID 5002, country Belgium) three times through `partner._record_observation`. Each observation is one scrape of the listing on a different date.

**Observation 1, 2026-01-05, Silver: first sighting.**

- No partner has website ID 5002, so one partner record is created. It stores:
  - `source_id` 5002, the name and the country;
  - `current_status` silver;
  - `first_seen_on` 2026-01-05 and `last_seen_on` 2026-01-05;
  - `active` True.
- One `status.history` row is created: `change_type` initial, `previous_status` empty, `new_status` silver, `change_date` 2026-01-05.
- Total: 1 partner, 1 history row.

**Observation 2, 2026-02-02, Gold: a promotion.**

- The website ID matches the existing record, so nothing new is created for the partner.
- The record changes:
  - `current_status` becomes gold;
  - `last_seen_on` becomes 2026-02-02;
  - `first_seen_on` stays 2026-01-05.
- Gold ranks above Silver, so one `promoted` row is added: silver to gold, `change_date` 2026-02-02.
- Total: 1 partner, 2 history rows.

**Observation 3, 2026-03-02, Gold again: no change.**

- Only `last_seen_on` moves, to 2026-03-02.
- The status did not change, so no history row is added; `first_seen_on` stays 2026-01-05.
- Total: 1 partner, 2 history rows. The test also checks that exactly one partner has website ID 5002.

**Replays and late data:**

- Replaying an observation adds nothing (`test_replayed_observation_adds_nothing`).
- A late replay of observation 1 after observation 3 is ignored (D-21, `test_older_observation_is_ignored`), so it cannot record a false demotion.
- An unknown status label writes nothing at all (`test_unknown_status_writes_nothing`).

## Real commands and results

- `df -h /c`: 14 GB free at the start of the stage, 9.7 GB after the two test runs. Docker's virtual disk was 14.6 GB on 2026-11-03 and 15.4 GB afterwards, so it explains at most 0.8 GB of the drop; the rest is not attributed.
- `scripts/dev.sh test azk_odoo_partner_monitor`, first run: FAIL.
  - One error: re-adding a removed reference hit the unique index, because the ORM had delayed the closing UPDATE.
  - Then the run stopped: a security-test fixture named `run` replaced unittest's `TestCase.run()` ("'azk_odoo_partner_monitor.sync.run' object is not callable").
  - It also logged a warning about two fields sharing the label "Errors".
  - All three were fixed in the code, with regression checks added.
- The same command, second run: PASS. "0 failed, 0 error(s) of 53 tests" in a fresh `azk_ee24_test` with demo data; 0 warnings in the whole log; exit code 0; 6 min 26 s.
- `scripts/dev.sh update azk_odoo_partner_monitor` (upgrade of `azk_ee24` from the Stage 01 skeleton): PASS, 0 warnings or errors, demo data loaded, 3 min 16 s. Run again: PASS, 0 warnings or errors, 2 min 45 s, no duplicates.
- `scripts/dev.sh shell azk_ee24` (read-only check): PASS.
  - Version 18.0.1.1.0, installed with demo data.
  - 4 countries (3 active), 6 partners (5 active), 10 history rows, 6 references.
  - The 3 partial unique indexes and the 14 check and unique constraints are present.
  - The failure recipient is the admin, whose notification preference is email. The admin is a Manager.
- HTTP check on port 8071 as admin: PASS. Login, partner search (5 active demo partners), list, form and search views, and the 11 Partner Monitor menus.
- NOT RUN:
  - the browser check (no browser here); the suggested steps are above;
  - the single-test command shown above.

## Concepts in our files (with Django comparisons)

- **Model:** `models/partner.py`, `class PartnerMonitorPartner(models.Model)` with `_name = "azk_odoo_partner_monitor.partner"`.
  - Like a Django model; `_name` also gives the table `azk_odoo_partner_monitor_partner`.
  - There are no migration files: Odoo creates and alters columns on install and upgrade (`-u`).
- **Fields:** `fields.Char`, `fields.Selection`, `fields.Date`, and so on, as in Django.
  - `required=True` becomes NOT NULL.
  - `readonly=True` only affects the UI.
  - `_sql_constraints` are database constraints, like `Meta.constraints`.
  - `@api.constrains` methods are Python validations that run on every create and write, even for the superuser.
- **Recordsets:** `self` is an ordered set of records.
  - `partner.status_history_ids` is another recordset.
  - `filtered`, `sorted` and `mapped` work like evaluated QuerySet operations.
  - `ensure_one()` asserts a single record.
- **env:** `self.env` carries the cursor, the user and the context.
  - `self.env["azk_odoo_partner_monitor.reference"]` is like `apps.get_model`.
  - `with_user(user)` runs as that user; the tests use it for readers and managers.
  - `sudo()` switches to superuser mode; `env.su` tells you if you are in it.
- **Relational fields:**
  - `country_id` is a Many2one, a ForeignKey with `ondelete="restrict"` (like `PROTECT`).
  - `status_history_ids` is a One2many: the reverse side of the history's `partner_id`, like `related_name`.
  - `res.groups.users` in `security/partner_monitor_security.xml` is a Many2many.
- **XML IDs:** `id="demo_partner_aurora"` in `demo/partner_monitor_demo.xml` becomes `azk_odoo_partner_monitor.demo_partner_aurora` in `ir.model.data`.
  - It is a stable name for a database row, like a fixture natural key; `env.ref()` reads it.
  - `noupdate="1"` (in `data/partner_monitor_config.xml`) keeps an administrator's later change on upgrade.
- **ACLs:** `security/ir.model.access.csv` gives each group read, write, create or delete rights per model.
  - Like Django's view, change, add and delete permissions, but the ORM checks them on every call, RPC included.
  - All our rows are read-only.
- **Record rules:** `ir.rule` adds a row filter for a group, like a queryset filter forced on every query.
  - We have none on purpose: the scraped data is public and shared by every company.
  - A company rule would hide partners from users of other companies. `test_data_is_shared_across_companies` proves there is no such isolation.
- **Groups:** `group_reader` and `group_manager` (which implies Reader) in `security/partner_monitor_security.xml`, like Django groups where one includes the other.

## Decisions taken in this stage

- **D-18:** nobody edits scraped data, history or sync checkpoints through access rules. Managers get four actions instead:
  - Sync Now;
  - Retry;
  - Mark for Re-scrape, on countries and on partners.

  Each action checks the group, then writes with a narrow `sudo()`. History rows refuse any edit.
- **D-19:** the default failure recipient is `base.user_admin`. Odoo runs install hooks as the superuser, so the user who clicked Install is unknown.
- **D-20:** demo records are labeled, and use reserved website IDs (negative partner IDs, "demo-" country IDs) enforced by the database.
- **D-21:** an observation older than the partner's last one is ignored.
- **D-22:** `total_references_count` has a known flag too, and an unknown measurement carries no number.
- **Stage 02 corrections** ([architecture.md](../architecture.md) 5.2, 5.7):
  - partial unique indexes need raw SQL in `init()`, not `create_index`;
  - the post-init-hook plan for the recipient was replaced by D-19.

## Open issues and assumptions

- **Sync Now:** it creates a run and queues the country-list unit, but nothing processes the queue until the Stage 05 worker. A run created now stays "Running".
- **Concurrency:** two workers observing the same partner is tested in Stage 05 (TP-PM-14), as is the failure note at the end of a run (TP-PM-16).
- **Live site (Stage 04):**
  - the canonical URL rule (`https://www.odoo.com/partners/<slug>-<id>`) is checked against the live site;
  - the reference key (link or normalized name) is decided there.
- **Notifications:** `admin` gets notifications by email in this build. To see a failure note in the Discuss Inbox, choose "Handle in Odoo" in the user's preferences.
- **Team-lead questions Q-02 to Q-06:** unchanged, none blocking.
- **Disk:** 9.7 GB free on C:. Test runs use a fresh database each time.

## Changed files

- **New (in `addons/azk_odoo_partner_monitor/`):**
  - `models/` (8 models and `common.py`);
  - `services/urls.py`;
  - `security/partner_monitor_security.xml`, `security/ir.model.access.csv`;
  - `data/partner_monitor_config.xml`;
  - `views/` (6 view files and `menus.xml`);
  - `demo/partner_monitor_demo.xml`;
  - `static/description/icon.png`;
  - `tests/common.py` and 5 new test files.
- **Updated (addon):** `__manifest__.py`, `__init__.py`, `tests/__init__.py`.
- **Updated (docs):**
  - `docs/architecture.md`, `docs/assumptions.md`, `docs/requirements_matrix.md`;
  - `docs/test_plan.md`, `docs/STATE.md`;
  - `docs/ai/README.md`, `docs/ai/stage_03.md` (new);
  - this handoff (new).
- **Outside Git:** the private logs `runtime/logs/stage03_*`; the databases `azk_ee24` (upgraded) and `azk_ee24_test` (recreated).

## Comprehension questions

1. Why does `_sync_references` flush pending reference changes before it inserts new references?
2. No access rule lets a manager write a partner. Why does "Mark for Re-scrape" still work, and why is it not a blanket `sudo()`?
3. In Silver -> Gold -> Gold, why does the third observation add no history row, and which field still changes?

## Next stage

04 - Partner scraping: fetch and parse layers, tested on saved pages.
