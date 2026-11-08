# Requirements matrix

Source: the assessment PDF (14 pages, kept outside this repository). Page numbers refer to that PDF. Stage 00 listed the requirements; Stage 02 (2026-11-05) split them into individual requirements and added each one's interpretation, planned implementation location and planned test. Stage 03 (2026-11-08) implemented the Partner Monitor data model, access rules and basic views, and recorded its test evidence in the rows it touched (and in K-08 to K-10).

**Status values:**

- NOT STARTED: nothing decided or built yet.
- DESIGNED: the interpretation, location and test were decided in Stage 02; not implemented.
- IN PROGRESS: partly implemented.
- DONE: implemented and verified, with evidence.
- BLOCKED.
- OUT OF SCOPE.

**Evidence values:** PASS, FAIL, BLOCKED, NOT RUN.

**Columns:**

- **Implementation:** a planned path, relative to the addon folder (`addons/<addon>/`), unless the row says otherwise.
- **Test:** the test-plan IDs (TP-xx) in [test_plan.md](test_plan.md).
- **Interpretation:** may cite assumptions and decisions (A-xx, D-xx, M-xx, V-xx, Q-xx), defined in [assumptions.md](assumptions.md). The design is in [architecture.md](architecture.md).

"Native baseline" evidence describes the standard Enterprise report on the same runtime; it is not evidence of our implementation. Stage 01 Community results are baseline evidence, not Enterprise acceptance.

Stage 00 IDs that Stage 02 split keep their number as a prefix: for example, T-08 is now T-08.1 to T-08.4, and P-10 is P-10.01 to P-10.12. Earlier documents that cite a Stage 00 ID refer to the whole family.

## Employer clarifications

| ID | Source | Requirement | Interpretation | Implementation | Test / evidence | Status |
|---|---|---|---|---|---|---|
| C-01 | Team lead, recorded 2026-11-03 | The assessment target is Odoo Enterprise | A-08; major version 18.0 still provisional (A-09) | Matched-pair service `odoo-ee-20241208` and database `azk_ee24` (`compose.yaml`, `config/odoo-enterprise-20241208.conf`, `scripts/dev.sh`); the Stage 01B service `odoo-ee` and `azk_ent` are preserved | 2026-11-05 on the matched pair (fresh databases): vendor `TestTrialBalanceReport` 8/8 PASS, custom tests 4/4 PASS, login, Trial Balance, PDF and XLSX smoke checks PASS; browser check NOT RUN. Earlier pair: 7/8 FAIL, kept blocked. See [enterprise_transition.md](enterprise_transition.md) | DONE |

## General and submission (pp. 1-3)

| ID | PDF p. | Requirement | Interpretation | Implementation | Test / evidence | Status |
|---|---|---|---|---|---|---|
| G-01 | 1 | Submit the module(s) in a public GitHub repository and share the link | Publication is Stage 15; sharing the link is the user's action | Repository root | Stage 15 | NOT STARTED |
| G-02 | 1 | README.md: module features and functionality | One README for both addons | `README.md` (Stage 12) | TP-G-04 | NOT STARTED |
| G-03 | 1 | README.md: installation instructions | Docker Compose route plus plain addons-path instructions | `README.md` | TP-G-04 | NOT STARTED |
| G-04 | 1 | README.md: configuration steps (if any) | Failure recipient, sync parameters, demo notes | `README.md` | TP-G-04 | NOT STARTED |
| G-05 | 1 | README.md: description of the testing strategy | Summarizes [test_plan.md](test_plan.md) and the real results | `README.md` | TP-G-04 | NOT STARTED |
| G-06 | 1-2 | README.md: Partner Monitor resilience design (interruptions, recovery without repeating work, pulling only changes) | Summarizes the design in architecture 5.6 and Stage 05's `docs/resilience.md` | `README.md` | TP-PM-15 | NOT STARTED |
| G-07 | 1 | Document reasonable assumptions | [assumptions.md](assumptions.md), linked from the README | `docs/assumptions.md` | Stage 02 | IN PROGRESS |
| G-08 | 1 | If parts are not done, state what is done and what is pending | A "Status and limitations" README section generated from this matrix | `README.md` | Stage 12 | NOT STARTED |
| G-09 | 1 | GenAI use: a `docs` folder logging the prompts used and the resulting outputs | Logs under `docs/ai/`, one per stage, with redactions noted | `docs/ai/` | Stages 00-03 logged | IN PROGRESS |
| G-10 | 1-2 | Clean, readable code following Odoo and Python best practices; efficient data model, queries and report generation | Grouped ORM queries (no query per account or partner), stored keys and indexes, layers kept separate | Both addons | Review in Stage 10; TP-G-02 | DESIGNED |
| G-11 | 2 | Well-packaged, easy to install and test; clear functional-testing instructions | Pinned Docker Compose setup with one helper script and an edition switch; README in Stage 12 | `compose.yaml`, `scripts/dev.sh`, [environment.md](environment.md) | Stage 01 and 01B setup and tests PASS; matched pair 2026-11-05 PASS ([environment.md](environment.md)) | IN PROGRESS |
| G-12 | 2 | (Recommendation) Jupyter Notebook connected to the Odoo shell | Optional; `scripts/dev.sh shell` is used instead | - | - | OUT OF SCOPE |
| G-13 | 3 | Pick two of the three exercises | Exercises 1 and 2 (A-01) | - | - | DONE |
| G-14 | 2 | Robust handling of errors, edge cases and resilience; UI interactions and data persistence (evaluation criteria) | Covered by K-02 to K-04 and the exercise rows | Both addons | TP-PM-07 to TP-PM-15, TP-TB-05, TP-TB-11 | DESIGNED |

## Contract requirements from the kit (not PDF text)

| ID | Source | Requirement | Interpretation | Implementation | Test / evidence | Status |
|---|---|---|---|---|---|---|
| K-01 | Kit, Stage 02 prompt | One normalized calculation result feeds Preview, PDF and XLSX | Engine result, then our handler, then the native `_get_lines`, then the native UI and exporters (A-13) | `models/trial_balance_engine.py`, `models/trial_balance_report_handler.py` | TP-TB-16 | DESIGNED |
| K-02 | Kit, AGENTS.md | Access enforced server-side on every path; no blanket `sudo()` | Architecture section 3: options re-validated in the engine; wizard owner rule; dashboard method as the calling user; a narrow `sudo()` only for `_trigger()` and for manager actions after an explicit group check (D-18) | Both addons | Partner Monitor models and actions: Stage 03, 2026-11-08: TP-PM-05 PASS (`test_security.py`, 12 tests). TP-PM-19, TP-TB-01 and TP-TB-11 NOT RUN (later stages) | IN PROGRESS |
| K-03 | Kit | Stable source identities, database uniqueness, idempotent writes | `source_key` and `source_id` with `_sql_constraints`; partial unique indexes created in `init()`; the observation API matches on these ids, so replays create nothing | Partner Monitor models | Stage 03, 2026-11-08: TP-PM-02 PASS; replayed observations PASS (`test_status_history.py`). Replays through the worker (TP-PM-09) NOT RUN until Stage 05 | IN PROGRESS |
| K-04 | Kit | Removals and deactivations only after a complete, validated snapshot; a failure is never an empty result | Architecture 5.5 | `models/work_item.py` | TP-PM-07, TP-PM-13 | DESIGNED |
| K-05 | Kit, AGENTS.md rule 1 | Version-sensitive APIs verified in the pinned core and Enterprise sources | Stage 02 read the cron, ORM, account, analytic, mail and web sources and the `account_reports` hooks by name, and ran the native probe | Architecture sections 1, 4, 5 | Stage 02 source reads and probe (`stage02_native_tb_probe.log`, private) | IN PROGRESS |
| K-06 | Kit, AGENTS.md | Never copy Enterprise source into the repository or patch vendor code | Names only; our own report record and handler | - | Review in Stage 10 | IN PROGRESS |
| K-07 | Kit | Trial Balance expectations are hand-calculated; native parity is additional evidence | [test_plan.md](test_plan.md) 4.1 | `tests/` | TP-TB-02 to TP-TB-04, TP-TB-12 | DESIGNED |
| K-08 | Kit, Stage 03 prompt | Normal users cannot manufacture audit events or edit sync checkpoints; manual scrape and retry actions are for managers | D-18: read-only ACLs; four manager actions with an explicit group check and a narrow `sudo()`; history rows refuse edits | `security/ir.model.access.csv`, `models/common.py` (`ensure_manager`), `models/*.py` | Stage 03, 2026-11-08: `test_reader_cannot_write_create_or_delete`, `test_reader_cannot_run_manager_actions`, `test_manager_cannot_edit_data_events_or_checkpoints`, `test_users_cannot_record_observations` PASS | DONE |
| K-09 | Kit, Stage 03 prompt | Deterministic synthetic demo records, clearly labeled as demo | D-20: `is_demo`, "Demo" names, reserved website ids enforced by the database | `demo/partner_monitor_demo.xml` | Stage 03, 2026-11-08: `test_demo_records_are_labeled`, `test_demo_history_is_consistent`, `test_demo_and_website_ids_never_collide` PASS; no duplicates after two upgrades of `azk_ee24` | DONE |
| K-10 | Kit, Stage 03 prompt | Unknown or missing measurements are distinct from genuine zeros | `_known` flags; an unknown measurement carries no number (D-22) | `models/partner.py` | Stage 03, 2026-11-08: `test_unknown_metric_is_not_zero` PASS | DONE |

## Exercise 1: Odoo Partner Monitor (`azk_odoo_partner_monitor`)

### Core functionality, scraping and resilience (pp. 2-3)

| ID | PDF p. | Requirement | Interpretation | Implementation | Test / evidence | Status |
|---|---|---|---|---|---|---|
| P-01 | 3 | Module named `azk_odoo_partner_monitor` | As written | `addons/azk_odoo_partner_monitor/` | Stage 01: installs in `azk_dev` and alone in a fresh `azk_clean`; Stage 01B: installs and updates in `azk_ent`; 2026-11-05: smoke tests PASS on the matched pair; Stage 03, 2026-11-08: installs alone with demo data into a fresh `azk_ee24_test` (0 warnings) and upgrades `azk_ee24` twice (0 warnings) | DONE |
| P-02 | 3 | Scrape partner data from the official Odoo Partners page, store it, track historical changes, provide analytical views and dashboards | Separate fetch, parse and ingest layers; source model A-19 | `services/`, `models/` | TP-PM-06, TP-PM-21 | DESIGNED |
| P-03.1 | 3 | Scraping logic generated with a GenAI tool | Generated with Claude Code in Stage 04; prompts and outputs logged | `services/parsers.py`, `services/http_client.py` | Stage 04 AI log | DESIGNED |
| P-03.2 | 3 | Uses standard libraries such as `requests` and `BeautifulSoup` | requests 2.31.0 and beautifulsoup4 4.12.3 come with the pinned image; no browser dependency | Manifest `external_dependencies` | Stage 01: `test_beautifulsoup_parses_html` PASS | IN PROGRESS |
| P-04 | 3 | Scraping is triggered by a daily cron job | The daily discovery cron creates a run, enqueues the country list and triggers the worker (A-18) | `data/ir_cron.xml`, `models/sync_run.py` | TP-PM-09, TP-PM-15 | DESIGNED |
| P-05.1 | 3 | A failure while processing one partner does not halt the job | One savepoint per unit; other units continue in the same batch | `models/work_item.py` | TP-PM-10 | DESIGNED |
| P-05.2 | 3 | A failure while processing one country page does not halt the job | A country unit fails alone and is retried with backoff | `models/work_item.py` | TP-PM-07, TP-PM-10 | DESIGNED |
| P-06 | 3 | Log all errors encountered during the scrape | Python logger plus one `sync.error` row per failure with run, unit and URL context, written outside the failed savepoint | `models/sync_error.py` | TP-PM-07, TP-PM-10 | DESIGNED |
| P-07.1 | 3 | On a partial job failure, post a message in the internal chatter of a designated user | D-08: one internal note on the run's chatter, addressed to the user | `models/sync_run.py` (`_notify_failure`) | Stage 03, 2026-11-08: destination PASS (`test_notification.py`, 7 tests): a note on the run's chatter, a `mail.notification` for the configured user (Inbox or email, as the user prefers), posted once, website text escaped. Calling it when a run ends: Stage 05 (TP-PM-16) | IN PROGRESS |
| P-07.2 | 3 | On a full job failure, the same | A run whose discovery fails ends `failed` and notifies the same way | `models/sync_run.py` (`_notify_failure`) | Stage 03, 2026-11-08: a `failed` run notifies the same way PASS (`test_notification.py`). Calling it when a run ends: Stage 05 | IN PROGRESS |
| P-07.3 | 3 | The designated user is configurable | Settings field stored as `ir.config_parameter` (A-22); an invalid setting falls back to the administrator | `models/res_config_settings.py`, `views/res_config_settings_views.xml`, `models/sync_run.py` (`_get_failure_recipient`) | Stage 03, 2026-11-08: `test_settings_are_for_system_administrators` and `test_invalid_recipient_falls_back_to_the_administrator` PASS | DONE |
| P-07.4 | 3 | Example default: the administrator who installed the module | D-19: `base.user_admin`, set by a `noupdate` data record. Odoo runs install hooks as the superuser, so the user who clicked Install is not known | `data/partner_monitor_config.xml` | Stage 03, 2026-11-08: `test_default_recipient_is_the_administrator` PASS; `azk_ee24` holds the admin's id after upgrade | DONE |
| P-08.1 | 2 | Resilient to interruptions (long-running server actions are often terminated) | Bounded cron callbacks; the scheduler commits after each; claims are row locks that die with a crashed transaction | `models/work_item.py`, `data/ir_cron.xml` | TP-PM-14, TP-PM-15 | DESIGNED |
| P-08.2 | 2 | Recover from a failure without repeating completed work | Durable work items: done units never re-run; only the interrupted batch is replayed | `models/work_item.py` | TP-PM-09, TP-PM-15 | DESIGNED |
| P-08.3 | 2 | Pull only what changed, where possible | Details fetched only for new, changed, flagged or stale partners; conditional HTTP if the site supports it; content fingerprints | `models/work_item.py`, `services/http_client.py` | TP-PM-17 | DESIGNED |

### Data models (pp. 3-4)

| ID | PDF p. | Requirement | Interpretation | Implementation | Test / evidence | Status |
|---|---|---|---|---|---|---|
| P-09.1 | 3 | Model `azk_odoo_partner_monitor.country`: standalone, stores the countries found on the partner page | Standalone, not `res.country`; identity `source_key` (unique, never rewritten) | `models/country.py` | Stage 03, 2026-11-08: `test_required_models_and_field_types_match_the_pdf`, `test_country_identity_is_the_website_id` PASS | DONE |
| P-09.2 | 3 | `name`: Char | As written | `models/country.py` | Stage 03, 2026-11-08: TP-PM-01 PASS | DONE |
| P-09.3 | 3 | `active`: Boolean, default True | Cleared only from a complete, validated country list (P-23, Stage 05); a country seen again is reactivated | `models/country.py` | Stage 03, 2026-11-08: TP-PM-01 PASS (type and default); reactivation PASS | DONE |
| P-09.4 | 3 | `total_partner_count`: Integer, the number of partners listed for the country in the last scrape, used for validation | The expected count shown by the site; the actual snapshot count is stored separately (Stage 05) | `models/country.py` | Stage 03, 2026-11-08: TP-PM-01 PASS; its use in validation is P-18 | DONE |
| P-09.5 | 3 | `to_reprocess_partners`: Boolean flag for re-scraping | Set on a mismatch (P-18, Stage 05) or by a manager (Mark for Re-scrape); cleared by a complete, matching snapshot | `models/country.py` | Stage 03, 2026-11-08: TP-PM-01 PASS; manager action PASS (`test_security.py`) | DONE |
| P-10.01 | 3 | Model `azk_odoo_partner_monitor.partner`; `name`: Char | Identity is `source_id` (unique, never rewritten), never the name | `models/partner.py` | Stage 03, 2026-11-08: TP-PM-01 PASS; `test_partner_identity_is_the_website_id` PASS | DONE |
| P-10.02 | 4 | `partner_url`: Char, the link to the partner's page | Canonical URL `https://www.odoo.com/partners/<slug>-<source_id>` without query string, checked by a model constraint; the country-scope check before canonicalization is P-22.2 (Stage 04) | `models/partner.py`, `services/urls.py` | Stage 03, 2026-11-08: `test_partner_url_must_be_canonical`, `test_canonical_url_rule` PASS | DONE |
| P-10.03 | 4 | `current_status`: Selection (e.g. gold, silver, ready) | Selection `ready`/`silver`/`gold`, ordered ready < silver < gold; unknown labels are refused without writes (D-09) | `models/partner.py`, `models/common.py` | Stage 03, 2026-11-08: TP-PM-01 PASS; `test_unknown_status_writes_nothing` PASS | DONE |
| P-10.04 | 4 | `country_id`: Many2one to `azk_odoo_partner_monitor.country` | Required, `ondelete='restrict'`; updated if the partner is listed under another country (D-17) | `models/partner.py` | Stage 03, 2026-11-08: TP-PM-01 PASS; `test_country_move_updates_the_same_partner`, `test_relations_are_enforced` PASS | DONE |
| P-10.05 | 4 | `first_seen_on`: Date | Set once at creation (P-13); the model refuses a different value afterwards | `models/partner.py` | Stage 03, 2026-11-08: `test_first_seen_on_cannot_be_rewritten` PASS | DONE |
| P-10.06 | 4 | `retention_rate`: Float | With a known flag, because Odoo reads NULL as 0; an unknown value carries no number (D-22) | `models/partner.py` | Stage 03, 2026-11-08: TP-PM-01 PASS; `test_unknown_metric_is_not_zero` PASS | DONE |
| P-10.07 | 4 | `total_references_count`: Integer | The expected reference count shown by the site (P-20.1), with a known flag (D-22) | `models/partner.py` | Stage 03, 2026-11-08: TP-PM-01 PASS; `test_unknown_metric_is_not_zero` PASS | DONE |
| P-10.08 | 4 | `largest_project_size`: Integer | With a known flag | `models/partner.py` | Stage 03, 2026-11-08: TP-PM-01 PASS; `test_unknown_metric_is_not_zero` PASS | DONE |
| P-10.09 | 4 | `average_project_size`: Float | With a known flag; drives the stored project-size bucket (D-05, added in Stage 06) | `models/partner.py` | Stage 03, 2026-11-08: TP-PM-01 PASS; `test_unknown_metric_is_not_zero` PASS | DONE |
| P-10.10 | 4 | `to_reprocess_references`: Boolean flag to re-scrape the partner's details | P-20 (Stage 05) or a manager (Mark for Re-scrape) | `models/partner.py` | Stage 03, 2026-11-08: TP-PM-01 PASS; manager action PASS (`test_security.py`) | DONE |
| P-10.11 | 4 | `status_history_ids`: One2many to `status.history` | As written | `models/partner.py` | Stage 03, 2026-11-08: TP-PM-01 PASS | DONE |
| P-10.12 | 4 | `reference_ids`: One2many to `reference` | As written | `models/partner.py` | Stage 03, 2026-11-08: TP-PM-01 PASS | DONE |
| P-11.1 | 4 | Model `azk_odoo_partner_monitor.status.history` (tracks every status change); `partner_id`: Many2one to partner | Required; deleted with the partner; rows are append-only (D-18) | `models/status_history.py` | Stage 03, 2026-11-08: TP-PM-01 PASS; `test_history_rows_cannot_be_changed` PASS | DONE |
| P-11.2 | 4 | `previous_status`: Selection | Same values as `current_status`; empty exactly for `initial` (database check) | `models/status_history.py` | Stage 03, 2026-11-08: TP-PM-01, `test_history_rules_in_database_and_model` PASS | DONE |
| P-11.3 | 4 | `new_status`: Selection | Same values as `current_status`; differs from the previous status | `models/status_history.py` | Stage 03, 2026-11-08: TP-PM-01 PASS | DONE |
| P-11.4 | 4 | `change_date`: Date | Run date (A-20); the initial row is dated on `first_seen_on`, no row before it | `models/status_history.py` | Stage 03, 2026-11-08: `test_history_rules_in_database_and_model` PASS | DONE |
| P-11.5 | 4 | `change_type`: Selection (promoted, demoted, initial) | Exactly these three values; must follow the ranking | `models/status_history.py` | Stage 03, 2026-11-08: TP-PM-01, `test_ranking_types_promotions_and_demotions` PASS | DONE |
| P-12.1 | 4 | Model `azk_odoo_partner_monitor.reference` (client references per partner); `partner_id`: Many2one to partner | Identity (partner, `source_key`), D-10 | `models/reference.py` | Stage 03, 2026-11-08: TP-PM-01, `test_reference_rules_in_database` PASS | DONE |
| P-12.2 | 4 | `name`: Char, the name of the reference client | As written; a renamed reference keeps its record | `models/reference.py` | Stage 03, 2026-11-08: `test_snapshot_duplicates_and_renames` PASS | DONE |
| P-12.3 | 4 | `is_active`: Boolean | At most one active record per (partner, key) (partial unique index); active exactly when there is no removal date | `models/reference.py` | Stage 03, 2026-11-08: `test_reference_rules_in_database` PASS | DONE |
| P-12.4 | 4 | `added_on`: Date | Run date when first listed in this interval | `models/reference.py` | Stage 03, 2026-11-08: `test_new_references_are_active` PASS | DONE |
| P-12.5 | 4 | `removed_on`: Date | Run date of the complete snapshot that no longer lists it; never before `added_on` | `models/reference.py` | Stage 03, 2026-11-08: `test_complete_snapshot_closes_missing_reference` PASS | DONE |

### Historical data logic (p. 4)

| ID | PDF p. | Requirement | Interpretation | Implementation | Test / evidence | Status |
|---|---|---|---|---|---|---|
| P-13 | 4 | New partner: record `first_seen_on` when first seen | Set at creation by the observation API; never rewritten | `models/partner.py` (`_record_observation`) | Stage 03, 2026-11-08: model logic PASS (`test_status_history.py`, 13 tests). The sync calls it from Stage 05 | IN PROGRESS |
| P-14 | 4 | Status change: create a `status.history` record | `promoted` or `demoted` by rank; an `initial` row on first observation; nothing for an unchanged status, a replay or an older observation (D-21); concurrency checked in Stage 05 | `models/partner.py` (`_record_observation`) | Stage 03, 2026-11-08: model logic PASS, including `test_silver_gold_gold_records_initial_then_one_promotion`. The sync calls it from Stage 05 | IN PROGRESS |
| P-15 | 4 | New reference: create a reference record with `is_active=True` | `added_on` = run date | `models/partner.py` (`_sync_references`) | Stage 03, 2026-11-08: model logic PASS (`test_references.py`, 7 tests). The sync calls it from Stage 05 | IN PROGRESS |
| P-16 | 4 | Removed reference: set `is_active=False` and record `removed_on` | Only from a complete snapshot; a partial snapshot removes nothing; reactivation opens a new record (D-10). Completeness validation: Stage 05 | `models/partner.py` (`_sync_references`) | Stage 03, 2026-11-08: model logic PASS (`test_references.py`). The sync calls it from Stage 05 | IN PROGRESS |

### User interface (p. 4)

| ID | PDF p. | Requirement | Interpretation | Implementation | Test / evidence | Status |
|---|---|---|---|---|---|---|
| P-17.1 | 4 | Menu items and actions for the views of the original specification | The specification was not supplied (M-01); our proposal is A-16 | `views/menus.xml`, `views/*_views.xml` | Stage 03, 2026-11-08: menus and actions for countries, partners, status history, references, runs, work items, errors and Settings; `test_menus_follow_the_groups` and `test_views_load_for_each_role` PASS; menus and views over HTTP as admin on 8071 PASS. Dashboard: Stage 06. Browser check NOT RUN | IN PROGRESS |
| P-17.2 | 4 | Update all model and field references to the new data model | Every view uses the PDF's model and field names | `views/*_views.xml` | Stage 03, 2026-11-08: views validated at install and both upgrades (0 warnings); TP-PM-01 PASS | DONE |
| P-17.3 | 4 | The required filters, groupings and pivot configurations remain the same | Unknown without the specification; our filters, groupings and pivots are A-16; question Q-02 | `views/*_views.xml` | Stage 03, 2026-11-08: search filters and groupings for every model (A-16). Pivots and graphs: Stage 06 | IN PROGRESS |

### Two-level validation and the empty-country edge case (p. 5)

| ID | PDF p. | Requirement | Interpretation | Implementation | Test / evidence | Status |
|---|---|---|---|---|---|---|
| P-18 | 5 | Country level: compare the partners found for a country with its `total_partner_count`; on a mismatch set `to_reprocess_partners = True` | Distinct valid partners of a complete fetch versus the count shown on the same fetch; a mismatch also blocks archiving | `models/work_item.py` | TP-PM-11 | DESIGNED |
| P-19 | 5 | A separate cron job finds countries with `to_reprocess_partners = True` and re-triggers their scraping | The country-validation cron enqueues a de-duplicated unit per due country (bounded retries) and triggers the worker | `data/ir_cron.xml`, `models/country.py` | TP-PM-11 | DESIGNED |
| P-20.1 | 5 | When a partner's details are scraped, store the expected number of references | `total_references_count` | `models/work_item.py` | TP-PM-12 | DESIGNED |
| P-20.2 | 5 | If the active reference count in the database doesn't match, set `to_reprocess_references = True` | Compared after each detail fetch; cleared by a complete, matching fetch | `models/work_item.py` | TP-PM-12 | DESIGNED |
| P-20.3 | 5 | Changes in fields such as `retention_rate` or `largest_project_size` can also trigger the flag | A changed listing card or metric schedules one detail refresh; bounded, no self-triggering loop | `models/work_item.py` | TP-PM-12, TP-PM-17 | DESIGNED |
| P-21 | 5 | A separate cron job loops over partners with `to_reprocess_references = True` and re-scrapes their details | The reference-validation cron enqueues `partner_details` units and triggers the worker | `data/ir_cron.xml`, `models/partner.py` | TP-PM-12 | DESIGNED |
| P-22.1 | 5 | Handle the scenario where querying an empty country returns all partners | Verified in the 18.0 module: the controller falls back to all countries and shows an alert (architecture 5.1) | `services/parsers.py` | TP-PM-08 | DESIGNED |
| P-22.2 | 5 | Validate the partner URL: when processing a specific country, ignore records lacking `?country_id=` | Checked before canonicalization, in any query position; the value must equal the expected country; rejects are logged | `services/urls.py` | TP-PM-08 | DESIGNED |
| P-23 | 5 | During the country-list scrape, set `active = False` on database countries missing from the fetched list | Only from a complete, validated list; its partners are archived unless seen in another country (D-17) | `models/work_item.py` | TP-PM-13 | DESIGNED |

### Dashboard (pp. 5-6)

| ID | PDF p. | Requirement | Interpretation | Implementation | Test / evidence | Status |
|---|---|---|---|---|---|---|
| P-24.1 | 5 | A custom dashboard | A small OWL client action with four embedded standard graph views (A-17) | `static/src/dashboard/`, `views/dashboard_views.xml`, `models/dashboard.py` | TP-PM-18, TP-PM-20 | DESIGNED |
| P-24.2 | 5 | It is the module's main entry point | The root menu opens the dashboard | `views/menus.xml` | TP-PM-20 | DESIGNED |
| P-24.3 | 5 | Defined in XML | Action, menu, graph views and the OWL template are XML | `views/dashboard_views.xml`, `static/src/dashboard/dashboard.xml` | TP-PM-20 | DESIGNED |
| P-24.4 | 5 | Insights from custom queries or existing pivot views | Ranking by one ORM `_read_group` method; charts are standard graph views | `models/dashboard.py` | TP-PM-18 | DESIGNED |
| P-25.1 | 5 | Filterable by Status (Gold, Silver, Ready) | Multi-select; empty means all | `static/src/dashboard/` | TP-PM-18 | DESIGNED |
| P-25.2 | 5 | Filterable by Country | Multi-select of active countries | `static/src/dashboard/` | TP-PM-18 | DESIGNED |
| P-25.3 | 5 | Filterable by Year First Seen | Year of `first_seen_on` (D-14); stored `first_seen_year` | `models/partner.py`, `static/src/dashboard/` | TP-PM-18 | DESIGNED |
| P-25.4 | 5 | The entire dashboard responds to these filters | The same domain goes to all four charts and to the ranking | `static/src/dashboard/`, `models/dashboard.py` | TP-PM-18, TP-PM-20 | DESIGNED |
| P-26.1 | 5 | Active Partners by Country: a Top 5 bar chart by partner count | Ranking after filters, with deterministic ties (D-06) | `models/dashboard.py`, `views/dashboard_views.xml` | TP-PM-18 | DESIGNED |
| P-26.2 | 5 | A Bottom 5 bar chart | Same ranking, ascending; overlap allowed below 10 countries (D-06) | `models/dashboard.py` | TP-PM-18 | DESIGNED |
| P-26.3 | 6 | Each bar represents a country | Graph row group `country_id` | `views/dashboard_views.xml` | TP-PM-20 | DESIGNED |
| P-26.4 | 6 | Stacked bars for Gold, Silver and Ready within each country | Graph column group `current_status`, `stacked` | `views/dashboard_views.xml` | TP-PM-20 | DESIGNED |
| P-27.1 | 6 | Project Size Distribution by Country for the Top 5 countries (by partner count) | Same cohort as P-26.1 | `views/dashboard_views.xml` | TP-PM-18 | DESIGNED |
| P-27.2 | 6 | The same for the Bottom 5 countries | Same cohort as P-26.2 | `views/dashboard_views.xml` | TP-PM-18 | DESIGNED |
| P-27.3 | 6 | Show the distribution of `average_project_size` in buckets (e.g. <5, 5-10, 11-25, 25+) | Non-overlapping buckets plus Unknown (D-05), counting partners | `models/partner.py` (stored bucket) | TP-PM-18 | DESIGNED |
| P-27.4 | 6 | This chart is filterable by partner status | The shared Status filter | `static/src/dashboard/` | TP-PM-18 | DESIGNED |
| P-27.5 | 6 | Bar chart or pie chart | Stacked bars per country by bucket, so each country's distribution is visible | `views/dashboard_views.xml` | TP-PM-20 | DESIGNED |
| P-28 | 5 | The candidate suggests appropriate charts; at least the four above | The four required charts plus a sync-status summary line; no further charts planned | `static/src/dashboard/` | TP-PM-20 | DESIGNED |

## Exercise 2: Dynamic Trial Balance (`azk_dynamic_trial_balance`, A-03)

### Module and wizard (pp. 6-7)

| ID | PDF p. | Requirement | Interpretation | Implementation | Test / evidence | Status |
|---|---|---|---|---|---|---|
| T-01 | 6 | A new module introducing a "Dynamic Trial Balance" report with filters, grouping levels and PDF, XLSX and on-screen outputs | Our own report inside the native framework (A-13); the manifest will declare `account_reports` instead of `account` | `addons/azk_dynamic_trial_balance/` | Stage 01 and 01B installs PASS; matched pair 2026-11-05 smoke tests PASS (skeleton only) | IN PROGRESS |
| T-02 | 6 | A new transient model (wizard) is the interface for generating the report | `azk_dynamic_trial_balance.wizard`, one record per user and run, with an owner record rule | `models/trial_balance_wizard.py`, `security/` | TP-TB-01, TP-TB-11 | DESIGNED |
| T-03 | 6 | Wizard fields as in the provided mockup | The mockup was not supplied (M-02); the fields come from the PDF text plus D-03 | `views/trial_balance_wizard_views.xml` | TP-TB-01 | DESIGNED |
| T-03.1 | 6-7 | (Clarification) A period for the report and the PDF header | Date From and Date To, required, inclusive (D-03) | `models/trial_balance_wizard.py` | TP-TB-01, TP-TB-05 | DESIGNED |
| T-03.2 | 6-7 | (Clarification) Company selection | One company from the user's active, authorized companies (D-03, D-16) | `models/trial_balance_wizard.py` | TP-TB-01, TP-TB-11 | DESIGNED |
| T-04 | 6 | Posted entries are always set to True | A read-only, always-true display field; posted items are always in scope | `models/trial_balance_wizard.py`, engine | TP-TB-02 | DESIGNED |
| T-05 | 6 | Include Unposted Entries: draft entries are included, cancelled ones never (same as Odoo) | `parent_state != 'cancel'`. Native baseline, probe R2: the native Draft Entries option includes drafts and never cancelled entries (architecture 4.8) | `models/trial_balance_engine.py` | TP-TB-03 | DESIGNED |
| T-05.1 | 6 | Include Unposted Entries and Hierarchy and Subtotals can be selected together | Independent options | `models/trial_balance_wizard.py` | TP-TB-01 | DESIGNED |
| T-06 | 6 | Hierarchy and Subtotals: the report with account groups (same as Odoo) | `account.group` tree with native-like subtotals and "(No Group)"; native baseline: probe R8 | `models/trial_balance_engine.py` | TP-TB-10 | DESIGNED |
| T-07.1 | 6 | Hierarchy Only Parents | Only group rows up to the selected level; requires Hierarchy and Subtotals (D-13) | wizard, engine | TP-TB-10 | DESIGNED |
| T-07.2 | 6 | Selecting it shows Account Level Up To, with levels 1 to 5 (as in TB) | Selection 1-5, required while Only Parents is set; level = account-group depth | `views/trial_balance_wizard_views.xml` | TP-TB-01, TP-TB-10 | DESIGNED |
| T-08.1 | 6 | Accounts: a multi-search field accepting several texts | Tags on a transient prefix model | `models/trial_balance_wizard.py` | TP-TB-06 | DESIGNED |
| T-08.2 | 6 | Matches accounts whose code starts with those texts | Literal prefixes with OR semantics, evaluated in the report company's context (V-06) | `models/trial_balance_engine.py` | TP-TB-06 | DESIGNED |
| T-08.3 | 6 | Empty means all accounts are reported | No account restriction | engine | TP-TB-07 | DESIGNED |
| T-08.4 | 6 | Help text: "Specify the account prefix to view only matching accounts. If no prefix is entered, all accounts will be displayed." | Verbatim | `models/trial_balance_wizard.py` | TP-TB-01 | DESIGNED |
| T-09.1 | 7 | Journals: Many2one from `account.journal` | One journal (D-02); journals of the selected company only | `models/trial_balance_wizard.py` | TP-TB-06 | DESIGNED |
| T-09.2 | 7 | Nothing selected means all journals | No journal restriction; a selected journal also restricts the opening balance (native baseline, probe R7) | engine | TP-TB-06 | DESIGNED |
| T-09.3 | 7 | Help text: "Select specific journals to include in the report, or leave the field empty to include all journals." | Verbatim | `models/trial_balance_wizard.py` | TP-TB-01 | DESIGNED |
| T-10.1 | 7 | Analytic Accounts: Many2one from `account.analytic.account` | One analytic account (D-02); whole-item inclusion (D-07); native baseline: probe R4-R6 | `models/trial_balance_wizard.py`, engine | TP-TB-09 | DESIGNED |
| T-10.2 | 7 | Nothing selected means all analytic accounts | Each journal item counts once, never once per plan | engine | TP-TB-09 | DESIGNED |
| T-10.3 | 7 | Help text: "Select specific analytic accounts to include in the report, or leave the field empty to include all." | Verbatim | `models/trial_balance_wizard.py` | TP-TB-01 | DESIGNED |
| T-11.1 | 7 | Skip Zero Balance: accounts with zero initial balance, zero movements and zero ending balance are not listed | Hidden only if opening, movement debit and movement credit are all zero; equal debit and credit stay visible (D-12) | engine | TP-TB-07 | DESIGNED |
| T-11.2 | 7 | Help text: "Select this option to hide accounts that have neither an initial balance nor any transactions in this report." | Verbatim | `models/trial_balance_wizard.py` | TP-TB-01 | DESIGNED |
| T-12.1 | 7 | Show Amount Currency: a new "amount currency" column showing the amount with its currency symbol | Period movement in the transaction currency (D-11) | engine, `models/trial_balance_report_handler.py` | TP-TB-08 | DESIGNED |
| T-12.2 | 7 | Grouped by account, then by amount currency, with the sum of the amount currency | Rows per (account, transaction currency); per-currency totals; currencies never summed together | engine | TP-TB-08 | DESIGNED |
| T-12.3 | 7 | The same account can be shown on several lines | One row per currency used on the account | engine | TP-TB-08 | DESIGNED |
| T-12.4 | 7 | Help text (PDF wording, from "Enable this option to group the report by Account..." onwards) | The PDF's text verbatim, plus one sentence stating the column's date scope (D-11) | `models/trial_balance_wizard.py` | TP-TB-01 | DESIGNED |
| T-13.1 | 7 | PDF: export the report in PDF format | Wizard button returning the native download action | `models/trial_balance_wizard.py` | TP-TB-14 | DESIGNED |
| T-13.2 | 7 | XLSX: export the report in XLSX format | Wizard button returning the native download action | `models/trial_balance_wizard.py` | TP-TB-15 | DESIGNED |
| T-13.3 | 7 | Preview: view the selection on screen, the same as the TB, with the filters added | Native report UI on our report record | `models/trial_balance_wizard.py`, handler | TP-TB-13 | DESIGNED |
| T-14 | 7 | Every XLSX or PDF export has Debit and Credit for Initial Balance, Movement and Ending Balance | Three column groups with Debit, Credit and Balance each | handler | TP-TB-14, TP-TB-15 | DESIGNED |

### Report logic and outputs (p. 7)

| ID | PDF p. | Requirement | Interpretation | Implementation | Test / evidence | Status |
|---|---|---|---|---|---|---|
| T-15.1 | 7 | Each account line: Initial Balance (Debit, Credit, Balance) | Native opening and carry-forward rules (A-14), net side, signed balance (D-04); native baseline: probe R1 and R3 | `models/trial_balance_engine.py` | TP-TB-02, TP-TB-04 | DESIGNED |
| T-15.2 | 7 | Movement during the period (Debit, Credit, Balance) | Gross debit and credit, dates inclusive; Balance = debit - credit | engine | TP-TB-02, TP-TB-05 | DESIGNED |
| T-15.3 | 7 | End Balance (Debit, Credit, Balance) | Opening + movement, net side, signed balance | engine | TP-TB-02, TP-TB-04 | DESIGNED |
| T-16.1 | 7 | Preview renders on screen within the Odoo interface | Client action `account_report` with our report and options | handler | TP-TB-13 | DESIGNED |
| T-16.2 | 7 | It matches the standard look and feel of Odoo's dynamic reports | It is the native `account_reports` UI | handler | TP-TB-13 | DESIGNED |
| T-16.3 | 7 | The view is filterable | Native date range and Draft Entries; our options as custom keys (architecture 4.3) | handler | TP-TB-13 | DESIGNED |
| T-16.4 | 7 | The view is searchable | The native search bar | handler | TP-TB-13 | DESIGNED |
| T-17.1 | 7 | PDF: generates and downloads a PDF report | Native `export_to_pdf` through `export_file` and the `/account_reports` route | handler | TP-TB-14 | DESIGNED |
| T-17.2 | 7 | The PDF looks professional | Native layout; visual inspection required | handler | TP-TB-14 | DESIGNED |
| T-17.3 | 7 | The header includes the company name | Native header shows the company name and address | handler | TP-TB-14 | DESIGNED |
| T-17.4 | 7 | The header includes the selected date range | Added through a custom header template (`pdf_export` display hook); the native header shows only a period column title | `data/pdf_templates.xml`, handler | TP-TB-14 | DESIGNED |
| T-18.1 | 7 | XLSX: generates and downloads an Excel file with the report data | Native `export_to_xlsx` | handler | TP-TB-15 | DESIGNED |
| T-18.2 | 7 | It preserves the structure and hierarchy | Level indentation of group and account rows | handler | TP-TB-15 | DESIGNED |
| T-18.3 | 7 | The columns are properly formatted | Numeric cells with number formats; codes and names as text | handler | TP-TB-15 | DESIGNED |

### Testing and data (p. 8)

| ID | PDF p. | Requirement | Interpretation | Implementation | Test / evidence | Status |
|---|---|---|---|---|---|---|
| T-19 | 8 | README explains how the module was tested: the manual testing steps performed | The user's manual checks are recorded as theirs | `README.md` (Stage 12) | TP-G-04, TP-G-05 | NOT STARTED |
| T-20 | 8 | README explains the automated tests verifying the calculations against a known dataset | The TB-BASE, TB-X, TB-C, TB-A and TB-H fixtures | `README.md`, `tests/` | TP-TB-02 to TP-TB-12 | NOT STARTED |
| T-21 | 8 | Demo or test data: sample journal entries, posted and unposted | Demo journal entries posted and in draft, plus one cancelled entry | `data/demo/` | TP-TB-17 | DESIGNED |
| T-22 | 8 | Demo or test data: entries with different currencies and analytic accounts | At least two foreign currencies and a 60/40 distribution | `data/demo/` | TP-TB-17 | DESIGNED |
| T-23 | 8 | Demo or test data: a chart of accounts deep enough to test the hierarchy | Account groups at five levels | `data/demo/` | TP-TB-17 | DESIGNED |

## Exercise 3: Odoo 18 POS Enhancements

| ID | PDF p. | Requirement | Interpretation | Implementation | Test / evidence | Status |
|---|---|---|---|---|---|---|
| X-01 | 8-14 | Salesperson Assignment and Enhanced Receipt Layout POS addons | Intentionally unselected (A-01) | - | - | OUT OF SCOPE |
