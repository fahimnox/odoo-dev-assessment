# Requirements matrix

Source: the assessment PDF (14 pages, kept outside this repository). Page numbers refer to that PDF. This is the Stage 00 inventory: requirements are listed as written; interpretation, implementation and evidence are filled in from Stage 02 onward.

**Status values:** NOT STARTED · IN PROGRESS · DONE (implemented and verified, with evidence) · BLOCKED · OUT OF SCOPE.
**Evidence values:** PASS · FAIL · BLOCKED · NOT RUN.

Missing inputs (M-xx), assumptions (A-xx) and ambiguities (D-xx) are defined in [assumptions.md](assumptions.md).

Stage 01B (2026-11-03) moved the target to Odoo Enterprise. Evidence marked "Stage 01" was produced on the Community baseline and is not Enterprise acceptance. Observations about the native Enterprise Trial Balance are recorded in [enterprise_transition.md](enterprise_transition.md); they describe the baseline we can build on, not our implementation.

## Employer clarifications

| ID | Source | Requirement | Interpretation | Implementation | Test / evidence | Status |
|---|---|---|---|---|---|---|
| C-01 | Team lead, recorded 2026-11-03 | The assessment target is Odoo Enterprise | A-08; major version 18.0 still provisional (A-09) | Matched-pair service `odoo-ee-20241208` and database `azk_ee24` (`compose.yaml`, `config/odoo-enterprise-20241208.conf`, `scripts/dev.sh`); the Stage 01B service `odoo-ee` and `azk_ent` are preserved | Stage 01B: `azk_ent` created with `web_enterprise` and `accountant` (93 modules, no warnings), skeleton tests 4/4 PASS on Enterprise, but vendor `TestTrialBalanceReport` 7/8 FAIL on that pair. 2026-11-04: matched pair `odoo/odoo@4e5027c1` with Enterprise 18.0+e.20241208 identified by content. 2026-11-05, on that pair (edition `enterprise-20241208`, fresh databases): `TestTrialBalanceReport` 8/8 PASS, custom tests 4/4 PASS, and login, Trial Balance, PDF and XLSX smoke checks PASS; browser check of that environment NOT RUN; see [enterprise_transition.md](enterprise_transition.md) | DONE |

## General / submission

| ID | PDF p. | Requirement | Interpretation | Implementation | Test / evidence | Status |
|---|---|---|---|---|---|---|
| G-01 | 1 | Submit the module(s) in a public GitHub repository and share the link | Publication is Stage 15; sharing the link is the user's action | — | — | NOT STARTED |
| G-02 | 1 | README.md: module features and functionality | — | — | — | NOT STARTED |
| G-03 | 1 | README.md: installation instructions | — | — | — | NOT STARTED |
| G-04 | 1 | README.md: configuration steps (if any) | — | — | — | NOT STARTED |
| G-05 | 1 | README.md: description of the testing strategy | — | — | — | NOT STARTED |
| G-06 | 1–2 | README.md: Partner Monitor resilience design — resilience to interruptions, recovery without repeating completed work, pulling only what changed where possible | — | — | — | NOT STARTED |
| G-07 | 1 | Document reasonable assumptions in the submission | [assumptions.md](assumptions.md) | — | — | IN PROGRESS |
| G-08 | 1 | If parts of an exercise are not done, state what is done and what is pending | — | — | — | NOT STARTED |
| G-09 | 1 | GenAI use: a `docs` folder with a document logging the prompts used and the resulting outputs | Logs under `docs/ai/` | — | — | IN PROGRESS |
| G-10 | 1–2 | Clean, readable code following Odoo and Python best practices; efficient data model, queries and report generation | — | — | — | NOT STARTED |
| G-11 | 2 | Well-packaged and easy to install and test; clear functional-testing instructions | Pinned Docker Compose setup with one helper script and an edition switch; README instructions follow in Stage 12 | `compose.yaml`, `scripts/dev.sh`, [environment.md](environment.md) | Stage 01: setup, tests and separate installs of each addon PASS on Community. Stage 01B: Enterprise setup, update and tests PASS; Community baseline tests still PASS ([environment.md](environment.md)) | IN PROGRESS |
| G-12 | 2 | (Recommendation) Jupyter Notebook connected to the Odoo shell for development | Optional; not required for the solution | — | — | NOT STARTED |
| G-13 | 3 | Pick two of the three exercises | Exercises 1 and 2 (A-01) | — | — | DONE |

## Exercise 1 — Odoo Partner Monitor (`azk_odoo_partner_monitor`)

| ID | PDF p. | Requirement | Interpretation | Implementation | Test / evidence | Status |
|---|---|---|---|---|---|---|
| P-01 | 3 | Module named `azk_odoo_partner_monitor` | — | `addons/azk_odoo_partner_monitor/` | Stage 01: installs into `azk_dev` and alone into a fresh `azk_clean`; smoke tests PASS. Stage 01B: installs and updates in `azk_ent` (Enterprise); smoke tests PASS in `azk_ent_test` | DONE |
| P-02 | 3 | Scrape partner data from the official Odoo Partners page, store it, track historical changes, provide analytical views and dashboards | — | — | — | NOT STARTED |
| P-03 | 3 | Scraping logic generated with a GenAI tool, using standard libraries such as `requests` and `BeautifulSoup` | requests 2.31.0 and beautifulsoup4 4.12.3 come with the pinned image | Declared in the manifest's `external_dependencies` (Stage 01); scraper follows in Stage 04 | Stage 01: `test_beautifulsoup_parses_html` PASS | IN PROGRESS |
| P-04 | 3 | Scraping is triggered by a daily cron job | — | — | — | NOT STARTED |
| P-05 | 3 | A failure while processing one partner or one country page does not halt the entire job | — | — | — | NOT STARTED |
| P-06 | 3 | Log all errors encountered during the scrape | — | — | — | NOT STARTED |
| P-07 | 3 | On partial or full job failure, post a message in the internal chatter of a designated, configurable user (e.g. the installing administrator) | — | — | — | NOT STARTED |
| P-08 | 2 | Process is resilient to interruptions (long-running server actions are often terminated), recovers without repeating completed work, and fetches only what changed where possible | — | — | — | NOT STARTED |
| P-09 | 3 | Model `azk_odoo_partner_monitor.country` (standalone): `name` Char; `active` Boolean, default True; `total_partner_count` Integer (partners listed for the country in the last scrape, used for validation); `to_reprocess_partners` Boolean | — | — | — | NOT STARTED |
| P-10 | 3–4 | Model `azk_odoo_partner_monitor.partner`: `name` Char; `partner_url` Char; `current_status` Selection (e.g. gold/silver/ready); `country_id` Many2one country; `first_seen_on` Date; `retention_rate` Float; `total_references_count` Integer; `largest_project_size` Integer; `average_project_size` Float; `to_reprocess_references` Boolean; `status_history_ids` One2many status.history; `reference_ids` One2many reference | — | — | — | NOT STARTED |
| P-11 | 4 | Model `azk_odoo_partner_monitor.status.history`: `partner_id` Many2one partner; `previous_status` Selection; `new_status` Selection; `change_date` Date; `change_type` Selection (promoted/demoted/initial) | — | — | — | NOT STARTED |
| P-12 | 4 | Model `azk_odoo_partner_monitor.reference`: `partner_id` Many2one partner; `name` Char; `is_active` Boolean; `added_on` Date; `removed_on` Date | — | — | — | NOT STARTED |
| P-13 | 4 | New partner: record `first_seen_on` when first seen | — | — | — | NOT STARTED |
| P-14 | 4 | Status change: create a `status.history` record | — | — | — | NOT STARTED |
| P-15 | 4 | New reference: create a `reference` record with `is_active=True` | — | — | — | NOT STARTED |
| P-16 | 4 | Removed reference: set `is_active=False` and record `removed_on` | — | — | — | NOT STARTED |
| P-17 | 4 | Menu items and actions for the views in the original specification, with its filters, groupings and pivot configurations, updated to this data model | Original specification not supplied (M-01) | — | — | NOT STARTED |
| P-18 | 5 | Country-level validation: compare partners found for a country with `total_partner_count`; on mismatch set `to_reprocess_partners = True` | — | — | — | NOT STARTED |
| P-19 | 5 | A separate cron job re-triggers scraping for countries with `to_reprocess_partners = True` | — | — | — | NOT STARTED |
| P-20 | 5 | Partner-level validation: store the expected reference count; if the active reference count in the DB differs, set `to_reprocess_references = True`; changes in fields such as `retention_rate` and `largest_project_size` can also set it | — | — | — | NOT STARTED |
| P-21 | 5 | A separate cron job re-scrapes details for partners with `to_reprocess_references = True` | — | — | — | NOT STARTED |
| P-22 | 5 | Empty-country edge case: when processing a specific country, ignore partner URLs that lack the `?country_id=` parameter | — | — | — | NOT STARTED |
| P-23 | 5 | During the country-list scrape, set `active = False` on DB countries no longer in the fetched list | — | — | — | NOT STARTED |
| P-24 | 5 | Custom dashboard defined in XML as the module's main entry point, using custom queries or existing pivot views | — | — | — | NOT STARTED |
| P-25 | 5 | The entire dashboard is filterable by Status (Gold/Silver/Ready), Country and Year First Seen | — | — | — | NOT STARTED |
| P-26 | 5–6 | Active Partners by Country: two bar charts (Top 5 and Bottom 5 countries by partner count), one bar per country, stacked by Gold/Silver/Ready | Ranking vs. filters: D-06 | — | — | NOT STARTED |
| P-27 | 6 | Project Size Distribution by Country: two charts (bar or pie) for the Top 5 and Bottom 5 countries by partner count, showing the distribution of `average_project_size` in buckets (e.g. <5, 5-10, 11-25, 25+), filterable by partner status | Bucket boundaries: D-05 | — | — | NOT STARTED |

## Exercise 2 — Dynamic Trial Balance (`azk_dynamic_trial_balance`, A-03)

| ID | PDF p. | Requirement | Interpretation | Implementation | Test / evidence | Status |
|---|---|---|---|---|---|---|
| T-01 | 6 | New module introducing a "Dynamic Trial Balance" report with filters, grouping levels and PDF/XLSX/on-screen outputs | Addon `azk_dynamic_trial_balance` (A-03), depending on `account` for now; whether to declare `account_reports` is a Stage 02 decision | `addons/azk_dynamic_trial_balance/` (manifest and smoke tests only so far) | Stage 01: installs into `azk_dev` and alone into a fresh `azk_clean`; smoke tests PASS. Stage 01B: installs and updates in `azk_ent` next to `accountant`/`account_reports`; smoke tests PASS on Enterprise | IN PROGRESS |
| T-02 | 6 | A new transient model (wizard) is the interface for generating the report | — | — | — | NOT STARTED |
| T-03 | 6 | Wizard fields "as shown in the provided mockup" | Mockup not supplied (M-02) | — | — | NOT STARTED |
| T-04 | 6 | Posted entries are always included | — | — | — | NOT STARTED |
| T-05 | 6 | Include Unposted Entries option: includes draft entries, never cancelled ones | Stage 01B observation: the native "Draft Entries" option (`all_entries`) has these semantics | — | — | NOT STARTED |
| T-06 | 6 | Hierarchy and Subtotals option: report with account groups; selectable together with Include Unposted Entries | — | — | — | NOT STARTED |
| T-07 | 6 | Hierarchy Only Parents: reveals Account Level Up To, selectable from 1 to 5 | — | — | — | NOT STARTED |
| T-08 | 6 | Accounts: multiple text prefixes matching accounts that start with them; empty means all accounts; given help text | — | — | — | NOT STARTED |
| T-09 | 7 | Journals: Many2One `account.journal`; empty means all journals; given help text | Cardinality vs. plural help text: D-02 | — | — | NOT STARTED |
| T-10 | 7 | Analytic Accounts: Many2One `account.analytic.account`; empty means all; given help text | Cardinality: D-02; distribution handling: D-07 | — | — | NOT STARTED |
| T-11 | 7 | Skip Zero Balance: hide accounts with zero initial balance, zero movements and zero ending balance; given help text | — | — | — | NOT STARTED |
| T-12 | 7 | Show Amount Currency: extra "amount currency" column with the currency symbol, grouped by account then transaction currency (an account can span several lines); given help text | — | — | — | NOT STARTED |
| T-13 | 7 | Wizard has PDF, XLSX and Preview actions | — | — | — | NOT STARTED |
| T-14 | 7 | PDF and XLSX exports include Debit and Credit for Initial Balance, Movement and Ending Balance | Initial/Ending Debit/Credit meaning: D-04 | — | — | NOT STARTED |
| T-15 | 7 | Each account line shows Initial Balance, Movement during the Period and End Balance, each as Debit, Credit, Balance | Stage 01B observation: the native Trial Balance shows only Debit and Credit per group (gap) | — | — | NOT STARTED |
| T-16 | 7 | Preview renders on-screen in Odoo, matching the look and feel of Odoo's dynamic reports; filterable and searchable | Reference report: D-01; Stage 01B: the native Enterprise Trial Balance (`account_reports`) is the likely reference | — | Baseline only, Stage 01B: the native report's RPC entry point `get_report_information` works over HTTP; the browser view is NOT RUN (manual check) | NOT STARTED |
| T-17 | 7 | PDF: professional-looking; header with company name and selected date range | Date/company fields: D-03 | — | Prerequisite only, Stage 01: wkhtmltopdf 0.12.6.1 (patched Qt) rendered a real QWeb PDF, PASS. Stage 01B: the native Enterprise Trial Balance PDF rendered inside the running Enterprise server (1 page, company header, page counter), PASS | NOT STARTED |
| T-18 | 7 | XLSX: report data preserving structure and hierarchy; properly formatted columns | — | — | Prerequisite only, Stage 01: XlsxWriter 3.1.9 smoke test PASS. Stage 01B: native Enterprise XLSX export produced a valid workbook, PASS | NOT STARTED |
| T-19 | 8 | README explains testing: manual testing steps performed | — | — | — | NOT STARTED |
| T-20 | 8 | README explains automated tests verifying the report's calculations against a known dataset | — | — | — | NOT STARTED |
| T-21 | 8 | Demo/test data: sample journal entries, both posted and unposted | — | — | — | NOT STARTED |
| T-22 | 8 | Demo/test data: entries with different currencies and analytic accounts | — | — | — | NOT STARTED |
| T-23 | 8 | Demo/test data: a chart of accounts deep enough to test the hierarchy features | — | — | — | NOT STARTED |

## Exercise 3 — Odoo 18 POS Enhancements

| ID | PDF p. | Requirement | Interpretation | Implementation | Test / evidence | Status |
|---|---|---|---|---|---|---|
| X-01 | 8–14 | Salesperson Assignment and Enhanced Receipt Layout POS addons | Intentionally unselected (A-01) | — | — | OUT OF SCOPE |
