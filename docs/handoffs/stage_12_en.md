# Stage 12 handoff: submission documentation

Date: 2026-11-16. Edition: `enterprise-20241208`. Status: **DONE**. Local release checkpoint: the Stage 12 commit, annotated tag `submission-rc1` (not pushed).

## What this stage delivers

- **[README.md](../../README.md)**, built on the quick start that Stage 11 followed literally from a clean checkout:
  - the scope (Exercises 1 and 2; Exercise 3 not selected on purpose);
  - the platform: Enterprise confirmed by the team lead, the major version 18.0 not confirmed (A-09, Q-04), the pinned Community commit, Enterprise build and images;
  - the declared dependencies and what must come from outside the repository (the public Community source; the proprietary Enterprise addons, which need authorized access);
  - installation, everyday commands, and a section on running a second, isolated copy, with what goes wrong when a new `.env` meets an existing project's volumes;
  - configuration, including how failure notes reach people: the chatter message, the inbox notification and the email, with an outgoing mail server or "Handle in Odoo";
  - the features, the resilience design, the testing strategy (261 executed test methods, 147 and 114, and why Odoo's statistics say 177 and 150), the demo, the assumptions, open questions and measured limitations, the status, the evidence, the AI use and the license.
- **[demo_script.md](../demo_script.md):** a 7-minute walkthrough with exact menus, DEMO, LIVE, FIXTURE and SIMULATED labels, the expected numbers (Bank 1,200.00, then 1,000.00 with drafts), one failure-and-recovery story, code pointers, and an offline fallback whose limits it states.
- **[release_checklist.md](../release_checklist.md):** what the checkpoint contains, the publication review, the decisions that are yours before Stage 15, and the pending work.
- **The design documents describe the final implementation:**
  - [architecture.md](../architecture.md) opens with section 0 (both addons as built, the model relations, where the build differs from the plan); its intro no longer says that later parts are "not implemented yet";
  - [resilience.md](../resilience.md) has a map of topics, the three ways a note is delivered, a partial-snapshot section and the Stage 11 results;
  - [calculation_contract.md](../calculation_contract.md) opens with a reviewer summary; its fiscal-year and branch notes now include the Stage 10 comparisons.
- **The final [requirements_matrix.md](../requirements_matrix.md):** 152 rows, 147 DONE. P-17.3 and T-19 are IN PROGRESS, G-01 is NOT STARTED, G-12 and X-01 are OUT OF SCOPE; a summary explains each.

## What I checked, and how

- **No application check was rerun,** because no addon code, configuration or setup script changed. The results of record stay those of Stage 11 (261 of 261 tests and the rest).
- **The volume-reuse warning in README section 6 was observed, not assumed.** On a throwaway Compose project with only the database service, a second `docker compose up` with new passwords recreated the container but kept the volume and its databases; the new password was refused ("password authentication failed for user "odoo""), the old one accepted, and the container's local socket needed no password, which is why `setup` cannot notice. The project was removed afterwards.
- **`COMPOSE_PROJECT_NAME`** overrides `name:` in `compose.yaml` whether it is exported, written in `.env` or given with `-p` (`docker compose config`).
- **The demo's numbers** come from the committed sample exports (read with openpyxl), the dashboard tests, and a read-only look at the Stage 11 acceptance database.
- **Documentation checks:** relative links and anchors (434 in 50 Markdown files, 0 broken), the commands and paths named in the documents, ASCII text in everything new or changed.
- **Publication review** of 198 files and every blob of the 24 commits: no secret value, key, token, local user path, vendor license header or copied vendor code. One personal-data item: your Git identity's work email address, in every commit and in four documents.

## What you can demonstrate now

- A clean installation with three commands (about 9 minutes on this machine), and `scripts/dev.sh test` with 261 passing tests (about 12 minutes).
- The Partner Monitor: the dashboard on demo data with the three filters acting on all four charts; the live Andorra sample of 2026-11-16 with BDR GROUP SLU's 17 references; two simulated outages, their notes and their recovery by a manager's Retry; paused downloads.
- The Trial Balance: the wizard with the assessment's fields and help texts; the preview with Bank at 1,200.00 and then 1,000.00 with drafts; the hierarchy and folding; currency rows; the PDF and the XLSX.
- The crash-and-restart check (offline, 12 of 12).

## Limitations you must mention

- Odoo 18.0 is our assumption; only the edition (Enterprise) was confirmed. Only the matched 2024-12-08 build was tested, on one Windows machine, with a trial database.
- The website was read in bounded samples only (39 requests over three days). A full crawl was never run, so its duration and the site's behavior under it are unknown; one large country could approach Odoo's time limit in multi-process mode (RF-12), which was not tested.
- The original views specification and the wizard mockup were never supplied: the views and the wizard layout are our proposal (P-17.3 stays open).
- The Trial Balance selects whole journal items for an analytic account (as the standard report does), reports one company at a time, and matches the standard report only in the compared cases.
- Without an outgoing mail server, failure notes reach an inbox only for a recipient set to "Handle in Odoo".
- The browser checks were scripted and run by the AI agent; your own manual check is still pending (T-19).
- The code was written by an AI agent under your direction; Stages 13 and 14 prepare you to explain it.

## Open items

- Your decisions before Stage 15 ([release_checklist.md](../release_checklist.md) section 4): the Git identity's email address, the license (Q-06, D-70), the manual check, whether to ask Q-02 to Q-06 first, and the tag.
- P-17.3 and T-19 IN PROGRESS; G-01 (publication) is Stage 15.
- The Stage 11 acceptance project and its volumes are kept; the demo script uses them.

## Changed files

- New: `README.md`, `docs/demo_script.md`, `docs/release_checklist.md`, `docs/handoffs/stage_12_en.md`, `docs/ai/stage_12.md`.
- Updated: `docs/architecture.md` (title, intro, section 0, 5.7, 5.12, 6), `docs/resilience.md` (header, sections 1, 10, 13, new 16 and 17), `docs/calculation_contract.md` (header, section 0, 5, 14), `docs/requirements_matrix.md` (intro, final summary, rows G-02 to G-09, G-11, K-05, T-19, T-20), `docs/assumptions.md` (D-69, D-70, the questions' intro), `docs/test_results.md` (final summary, Stage 12), `docs/test_plan.md` (TP-G-04, TP-G-05), `docs/acceptance_results.md` (a dated note), `docs/STATE.md`, `docs/ai/README.md`.
- Outside `docs/`: `addons/azk_odoo_partner_monitor/tests/fixtures/README.md` (the synthetic cases exist since Stage 10) and a comment in `scripts/fixture_sync_demo.py`. No code changed.

## Comprehension questions

1. A second checkout is set up on the same machine without its own project name, and its first `scripts/dev.sh setup` writes a new `.env` with new passwords. Why does `setup` then report that `azk_ee24` "already exists", and why can the web server still not connect to PostgreSQL?
2. In the demo company, Bank opens January 2026 at 1,000.00, ends at 1,200.00 with posted entries only, and ends at 1,000.00 with drafts included. Which journal entries explain each of these numbers, and which two entries never count?
3. The release checklist says that rewriting the commits' author must happen before the first push. Why would it be much harder to hide the email address after the repository has been published?

## Next stage

Stage 13 (code walkthrough), when you ask for it.
