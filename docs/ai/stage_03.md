# Stage 03 - Partner Monitor models, permissions and basic UI

- **Date:** 2026-11-08
- **Tool / model:** Claude Code, Opus 5.5 (`claude-opus-5-5`), in the same CLI session as Stages 01B and 02, resumed on 2026-11-08
- **Working directory:** the assessment kit root (`<kit-root>`) and `<kit-root>/solution`
- **Commit:** this log is part of the Stage 03 commit

**Transcription method:** see [README.md](README.md). The user text and the referenced instruction file are verbatim. The assistant messages are the text blocks recorded in the CLI's local session transcript, verbatim and in order, extracted by a script. Tool calls and their outputs are summarized, not reproduced.

**Redactions:** absolute local paths are replaced with `<kit-root>`, `<home>` or `<scratchpad>`. The CLI's paste markers around the user's pasted text are omitted. A local `/auto-mode-setup` command sent with the prompt is a CLI setting, not part of the conversation, and is not reproduced. No credential or subscription value was printed.

## User prompt (verbatim)

The whole message was pasted text.

```text
Read prompts/03_partner_models.txt and execute Stage 03 only.
Follow solution/AGENTS.md and the completed Stage 02 design.
Use the validated Enterprise environment on port 8071.

Run the Stage 03 install, upgrade, model, and permission checks.
In the handoff, show me the menu path to open a partner and identify
the test that covers the sequence Silver -> Gold -> Gold.
Explain what is stored after each observation. Use English only.
```

## Referenced instruction file: `prompts/03_partner_models.txt` (verbatim)

```text
STAGE 03  -  Implement the Partner Monitor models, permissions, and basic UI

LANGUAGE: English only for all newly authored terminal prose, explanations, questions, and reports. Use simple ASCII formatting and short paragraphs/bullets instead of wide or box-drawn tables. Preserve source data and original historical logs. Arabic coaching happens outside this terminal.

Follow AGENTS.md and the accepted design/assumptions. Check the pinned source for syntax and dependencies. Implement azk_odoo_partner_monitor as an installable Odoo addon, without network scraping yet.

Required models and fields from the assessment:
- azk_odoo_partner_monitor.country: name, active default True, total_partner_count, to_reprocess_partners.
- azk_odoo_partner_monitor.partner: name, partner_url, current_status, country_id, first_seen_on, retention_rate, total_references_count, largest_project_size, average_project_size, to_reprocess_references, status_history_ids, reference_ids.
- azk_odoo_partner_monitor.status.history: partner_id, previous_status, new_status, change_date, change_type with promoted/demoted/initial.
- azk_odoo_partner_monitor.reference: partner_id, name, is_active, added_on, removed_on.

Use the PDF for exact field types and relations. Preserve its standalone country model rather than silently replacing it with res.country. Add stable external identities, canonical URL constraints, partner active/last-seen metadata, and required run/work/error support from our design. Distinguish unknown/missing measurements from genuine zero values where that matters.

Define and enforce invariants:
1. Re-ingesting the same partner must not duplicate the partner or its status history.
2. first_seen_on does not change during later scrapes.
3. A status history event is recorded once for an actual transition; initial observation has an explicit interpretation.
4. Reference removal is reversible and retains history according to our documented reactivation policy. Do not pretend one added_on/removed_on pair captures unlimited removal/reactivation cycles; add event history only if justified.
5. Unique identities and foreign keys prevent invalid relations. Normal users cannot directly manufacture audit events or edit sync checkpoints.

Create reader/manager permissions with appropriate ACLs and record rules. Scope protected configuration and manual scrape/retry actions to authorized managers. Explain whether public partner data is shared across companies, and avoid introducing accidental data isolation behavior. Use Odoo mail integration for the configured internal failure recipient, with a real tested message destination rather than inventing a chatter API on res.users.

Add menus, actions, list/form/search views for countries, partners, status histories, references, runs/errors, and configuration. Use valid view syntax for the actual pinned Enterprise/core release. Show relevant related records and filters. Keep dashboard integration for Stage 06. Create deterministic synthetic demo records clearly labeled as demo.

Run install/update and model/security tests: uniqueness, relations, initial history, unchanged updates, allowed reader access, denied manager operations, and unauthorized writes. Explain Model, fields, recordsets, env, relational fields, XML IDs, ACLs, and record rules using these actual files. Update the matrix and stop with the standard report.
```

## Conversation during the stage (recorded text, verbatim, in order)

Assistant message 1:

> Starting Stage 03. I've read the Stage 03 prompt, Exercise 1 in the PDF and the Stage 02 design. Next I'll check the pinned 18.0 sources for the APIs the models, security and views will use.

Assistant message 2:

> I've finished checking the sources and the helper commands. Now I'm writing the addon: models, security, views, demo data and tests.

Assistant message 3:

> The country and partner models are written, including the API that records each website observation. Next: status history, references, and the sync run, work item and error models.

Assistant message 4:

> The models and the business-data views are done. Now I'm writing the sync views, settings, menus, demo data and the tests.

Assistant message 5:

> The status-history tests are written, including the Silver -> Gold -> Gold sequence. Next: tests for models, references, security and notifications. Then I'll run them on port 8071.

Assistant message 6:

> The tests are almost done. I checked how Odoo computes visible menus so the menu test expects the right items. Now I'm fixing one sloppy test and writing the notification test.

Assistant message 7:

> The first test run is still installing the module into the fresh test database. I'll continue as soon as its results come in.

Assistant message 8:

> I'm rerunning the 53 tests after the fixes, and preparing the test plan and requirements matrix updates while they run.

Assistant message 9:

> Nearly done: docs, matrix, handoff and the kit's `CLAUDE.md` summary are updated. I'm doing a last code tidy and ASCII/secrets check, then I'll assemble the AI log and commit.

Assistant message 10:

> I'm assembling the Stage 03 AI log. Some of my progress messages are missing from the transcript extract, so I'm checking how they were recorded before I commit.

## Notes on accuracy

- This log was assembled from the transcript just before its own commit. Progress messages written after that point, while committing, are not included. The final response below is included as prepared, and it was displayed unchanged.
- Facts in the messages that were later corrected stay as written here; corrections are listed in [README.md](README.md) (mistakes table).
- Several progress notes of this stage were written inside the agent's reasoning, not as visible messages: the transcript records them only in reasoning blocks. They were not displayed as messages, and hidden reasoning is never collected, so they are not reproduced.

## Summary of tool activity (summary, not verbatim)

1. Checked Git (clean at `ed435c3`) and the disk (14 GB free on C:). Read `prompts/03_partner_models.txt`, the PDF's Exercise 1 pages with `pdftotext`, the Stage 02 design documents (`docs/architecture.md`, `docs/assumptions.md`, `docs/requirements_matrix.md`, `docs/test_plan.md`, `docs/STATE.md`) and the Stage 04 to 06 prompts, to keep the stage's scope.
2. Read the version-sensitive code in the pinned Community source `<kit-root>/runtime/community/18.0-4e5027c1/`:
   - `odoo/tools/sql.py`: the index helpers; `create_index` builds non-unique indexes, and `create_unique_index` has no WHERE clause;
   - `odoo/modules/loading.py` and `graph.py`: install hooks get a superuser environment; demo data loads on install and on upgrade;
   - `odoo/models.py`: `_sql_constraints`, including empty-definition entries backed by a custom index, and `check_access`;
   - `odoo/sql_db.py`: flushing savepoints;
   - `res.config.settings`: Many2one config parameters, the settings view layout and its access rule;
   - the `<list>` and `<chatter/>` view syntax, `res.groups` fields and `ir.ui.menu._visible_menu_ids`;
   - `mail.thread.message_post` and the mail test mocks (`MockEmail`);
   - `new_test_user` and `assertRecordValues`.
3. Wrote the addon:
   - models, `services/urls.py`, security, data, views and demo data;
   - an app icon generated by a standard-library Python script;
   - six test files.
   Updated the manifest to 18.0.1.1.0, then compiled the Python files and parsed the XML and CSV files on the host.
4. Ran `scripts/dev.sh test azk_odoo_partner_monitor` twice, in a fresh `azk_ee24_test` each time. The first run failed: a fixture named `run`, a delayed write against a partial unique index, and a duplicate field label. The second run passed 53 of 53, after the fixes and two regression checks. Full logs: `<kit-root>/runtime/logs/stage03_test_run1.log`, `stage03_test_run2.log`.
5. Upgraded `azk_ee24` twice with `scripts/dev.sh update azk_odoo_partner_monitor`, with 0 warnings each time. Ran a read-only check through `scripts/dev.sh shell azk_ee24`, and an HTTP check on port 8071 as admin: login, partner search, views and menus. Checked the Docker disk size.
6. Updated the documentation and the kit-root `CLAUDE.md` (outside Git). Checked the changes for non-ASCII text, absolute paths and secret values, and committed only the intended files.

## Assistant final response (verbatim)

Everything between the two rules below is the final visible response.

---

Stage 03 is done. The Partner Monitor addon now has its data model, permissions, basic screens and demo data, and all 53 tests pass on the 8071 setup. There is no scraping yet; that comes in Stage 04.

**What I built**
- **Models:**
  - The four models from the PDF, with its exact field names and types.
  - Three supporting models: sync runs (with a chatter), work items and sync errors.
- **One entry point that records what the website shows**, inside the models: `country._record_observation`, `partner._record_observation` and `partner._sync_references`. It enforces the five invariants of the stage:
  - no duplicates;
  - `first_seen_on` never changes;
  - one history row per real status change, plus an explicit "initial" row;
  - removing a reference can be undone, and each removal is kept as history;
  - unique website IDs and checked relations.
- **Permissions:**
  - Reader and Manager groups. Nobody can edit scraped data, history or sync records directly.
  - Managers get four checked actions: Sync Now, Retry, and Mark for Re-scrape on countries and on partners.
  - There are no record rules on purpose: the data is public and shared by all companies, and a test proves it.
  - The failure-recipient setting is for system administrators only.
- **Failure note:** it is posted on the run's chatter for the configured user. It is tested for a user who reads in Odoo and for one who gets email, without sending real email.
- **Screens and demo data:**
  - Screens and menus for every model.
  - Demo data: 4 countries, 6 partners, 10 status changes and 6 references, all labeled as demo.

**Real commands and results**
- `df -h /c`: 14 GB free at the start, 9.7 GB after the test runs. Docker's disk grew by at most 0.8 GB since 2026-11-03, so most of the drop is unexplained.
- `scripts/dev.sh test azk_odoo_partner_monitor`, first run: FAIL. It found two bugs of mine and one warning:
  - a test fixture named `run` broke the test runner;
  - re-adding a removed reference hit the unique index, because Odoo delays writes;
  - two fields had the same label.
  I fixed all three and added regression checks.
- The same command, second run: PASS, 53 of 53, with 0 warnings in the whole log (6 min 26 s).
- `scripts/dev.sh update azk_odoo_partner_monitor` on `azk_ee24`, twice: PASS, 0 warnings, no duplicated demo records.
- A read-only shell check of `azk_ee24` and an HTTP check on port 8071 (login, partner list, views, 11 menus): PASS.
- NOT RUN: a browser check (I have no browser) and the single-test command below on its own.

**What you asked for (details in the handoff)**
- **Menu path to a partner:** Partner Monitor > Partners, then click a partner, for example Demo Partner Aurora.
- **Test for Silver -> Gold -> Gold:** `tests/test_status_history.py`, `TestStatusHistory.test_silver_gold_gold_records_initial_then_one_promotion` (PASS). To run it alone:
  `scripts/dev.sh test azk_odoo_partner_monitor /azk_odoo_partner_monitor:TestStatusHistory.test_silver_gold_gold_records_initial_then_one_promotion`
- **What is stored after each observation:**
  1. Silver on 2026-01-05: a new partner with status Silver, first seen and last seen 2026-01-05, and one "initial" history row with no previous status.
  2. Gold on 2026-02-02: the same record. The status becomes Gold and last seen moves to 2026-02-02; first seen stays 2026-01-05. One "promoted" row, Silver to Gold.
  3. Gold on 2026-03-02: the same record. Only last seen moves, to 2026-03-02. No new row, because the status did not change.

**Decisions (D-18 to D-22)**
- **D-18:** the manager actions check the group, then write with a narrow `sudo()`. History rows refuse any edit.
- **D-19:** the default failure recipient is the administrator. Odoo runs install hooks as the superuser, so it cannot know who clicked Install. This replaces the Stage 02 plan.
- **D-20:** demo records use reserved website IDs (negative partner IDs, "demo-" country IDs), so a real scrape can never collide with them.
- **D-21:** an observation older than the last one is ignored, so a late replay cannot record a false demotion.
- **D-22:** the listed reference count also has an "unknown" flag, and an unknown value carries no number.
- **Correction to Stage 02:** the partial unique indexes need raw SQL in `init()`. The helper the design named only builds non-unique indexes.

**How the Odoo concepts map to our files (more in the handoff)**
- **Model and fields:** `models/partner.py` is like a Django model. Odoo creates and alters the columns on install and upgrade; there are no migration files.
- **Recordsets and env:** `self` is a set of records. `self.env` holds the cursor, the user and the context. `with_user()` and `sudo()` change who the code runs as.
- **Relational fields:**
  - `country_id` is like a ForeignKey with PROTECT;
  - `status_history_ids` is the reverse side of the history's `partner_id`, like `related_name`.
- **XML IDs:** `demo_partner_aurora` in `demo/partner_monitor_demo.xml` is a stable name for a database row.
- **Access rules (ACLs):** `security/ir.model.access.csv` holds read, write, create and delete rights per group, like Django model permissions, but Odoo checks them on every call.
- **Record rules:** they would filter rows per user. We have none, so data is never hidden between companies.

**Open issues and assumptions**
- Sync Now queues a run, but nothing processes it until the Stage 05 worker. A run created now stays "Running".
- Two workers on the same partner, and the failure note at the end of a run, are tested in Stage 05.
- The canonical URL rule and the reference key are checked against the live site in Stage 04.
- The browser check is recommended: log in on port 8071 and open Partner Monitor > Partners.
- 9.7 GB free on C:. The team-lead questions Q-02 to Q-06 are unchanged, and none blocks Stage 04.

**Changed files**
- **New, in `addons/azk_odoo_partner_monitor/`:**
  - `models/` (country, partner, status history, reference, sync run, work item, sync error, settings, `common.py`);
  - `services/urls.py`;
  - `security/`;
  - `data/partner_monitor_config.xml`;
  - `views/` (6 view files and `menus.xml`);
  - `demo/partner_monitor_demo.xml`;
  - `static/description/icon.png`;
  - `tests/` (`common.py` and 5 test files).
- **Updated in the addon:** `__manifest__.py` (version 18.0.1.1.0), `__init__.py`, `tests/__init__.py`.
- **Docs:**
  - `architecture.md` (new section 5.10), `assumptions.md` (D-18 to D-22);
  - `requirements_matrix.md` (42 rows updated, K-08 to K-10 added);
  - `test_plan.md` (section 3.1), `STATE.md`, `environment.md`;
  - `ai/README.md`, `ai/stage_03.md` (new);
  - `handoffs/stage_03_en.md` (new).
- **Outside Git:**
  - the kit's `CLAUDE.md` architecture notes;
  - the private logs `runtime/logs/stage03_*`;
  - `azk_ee24`, which was upgraded.
- **Commit:** "Stage 03: Partner Monitor models, permissions and basic UI".

**Comprehension questions**
1. Why does `_sync_references` flush pending reference changes before it inserts new references?
2. No access rule lets a manager write a partner. Why does "Mark for Re-scrape" still work, and why is it not a blanket `sudo()`?
3. In Silver -> Gold -> Gold, why does the third observation add no history row, and which field still changes?

**Next stage:** 04, Partner scraping. I'm stopping here. When you're ready:

Read prompts/04_partner_scraping.txt and execute Stage 04 only, following solution/AGENTS.md.

---
