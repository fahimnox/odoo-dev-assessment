# Stage 11 handoff: clean acceptance

Date: 2026-11-16. Edition: `enterprise-20241208`. Status: **DONE**.

The full record, with every command, count, log name and requirement result, is [acceptance_results.md](../acceptance_results.md). The addon code is unchanged since Stage 10 (`e54214b`).

## What this stage delivers

- **A reproduced install, the way an assessor would do it:** from `git archive` exports of the repository (no `.env`, nothing untracked), in a separate Compose project with empty volumes, following only the documentation and the declared dependencies.
- **Three packaging and documentation fixes,** found by following the documentation literally:
  - AC-01: the first documented command failed in a fresh checkout;
  - AC-02: a rerun could not repair an interrupted first install;
  - AC-03: stale setup lines.
- **A quick start for a clean checkout** in [environment.md](../environment.md).
- **Six acceptance scripts:** `scripts/acceptance_*.py`. Also, `scripts/pm_live_check.py` can now keep its sample on a disposable database.
- **Evidence** for both addons: install, demo data, upgrade, tests, restart, browser, live sample, notifications and access.

## The three findings that mattered

1. **AC-01, the first command failed.**
   - In a fresh checkout, `scripts/dev.sh setup` wrote a `.env` for the Community edition and stopped with exit code 255: the Trial Balance addon depends on the Enterprise module `account_reports`.
   - An assessor would have failed on the very first command.
   - Now the default edition is the target, `enterprise-20241208`. `setup` writes `.env` first and asks for the two source folders, with a message that names the quick start.
2. **AC-02, no way back from a failed first install.**
   - Odoo rolls a failed first install back. It leaves only its module table, with even `base` uninstalled.
   - The old `setup` then said "already exists; leaving it unchanged", and only a manual `dropdb` helped.
   - Now `setup` installs what is missing, `base` first in that case, and never drops the database. Checked on the very database the failure left.
3. **O-01, notes by email without a mail server** (an observation, not a code change).
   - Run 1's note went to the default recipient, the administrator, whose Odoo preference is "Handle by Emails". With no outgoing mail server, the email failed and the inbox stayed empty; the note is on the run's chatter only.
   - The configured recipient, set to "Handle in Odoo", found run 2's note in the Discuss inbox.
   - The README must explain this (D-69).

## Short walkthrough

- **Repeat the clean install** (about 9 minutes): the quick start in [environment.md](../environment.md). To run it next to the development environment, as this stage did, give the copy its own project name and port: `COMPOSE_PROJECT_NAME=...` and `ODOO_EE_20241208_HTTP_PORT` in its `.env`.
- **Look at the acceptance database:** in `<kit-root>/runtime/acceptance/stage11_3b92f98`, run `COMPOSE_PROJECT_NAME=azk-stage11-acc scripts/dev.sh start`, then open http://127.0.0.1:8073 (admin / admin).
  - Partner Monitor > Dashboard opens on "Website data (2)": the LIVE Andorra sample of 2026-11-16. "Demo data (47)" is next to it.
  - Partner Monitor > Partners > BDR GROUP SLU has 17 live references.
  - Partner Monitor > Sync > Runs: after a simulated outage, run 1 ended partial and run 2 ended failed. Both then recovered and show "done"; their notes stay on their chatter. Run 3, queued by the access check's Sync Now, waits because downloads are paused.
  - The acceptance users' password was random and is not stored in the repository. Set a new one as admin to log in as them.
  - Downloads are paused there.
  - Stop it again with `COMPOSE_PROJECT_NAME=azk-stage11-acc scripts/dev.sh stop`.
- **The development server** (http://127.0.0.1:8071, `azk_ee24`) runs as before. This stage did not change its databases; it only made a few read-only SQL queries on `azk_ee24` at the start.

## Checks performed

All on 2026-11-16, from the export of `3b92f98` unless noted. Every install and update log had 0 WARNING, ERROR or CRITICAL lines.

- **The first documented run, export of `e54214b`:** FAIL (AC-01). The rerun with the fixed helper: PASS.
- **Quick start, steps 1 to 3:** PASS; `azk_ee24` with 92 modules in 8 min 44 s.
- **Demo data at install:** PASS. 13 countries, 50 partners, 57 history rows and 6 references; the Trial Balance demo company with 16 entries (13 posted, 2 draft, 1 cancelled).
- **Each addon alone, and then updated (TP-G-01):** PASS. The Partner Monitor has 34 modules and no accounting; the Trial Balance has 91 modules and no `l10n_eg`.
- **Both addons without demo data:** PASS; no demo record at all.
- **Upgrade from the Stage 09 release, with seeded history:** PASS. The state reports before and after differ only in the Partner Monitor's version; all fingerprints are equal.
- **`scripts/dev.sh test`:** PASS, 261 of 261 (147 and 114, the Stage 10 baseline). No skipped test, warning or import error. Every test file is imported.
- **`scripts/restart_check.sh`:** PASS, 12 of 12.
- **Browser checks** (headless Chrome, by the agent): dashboard 7 of 7, Trial Balance wizard 7 of 7, preview and downloads 20 of 20 (Bank 1,200.00 posted, 1,000.00 with drafts), Partner Monitor demonstration 7 of 7 (on run 3, after AC-06).
- **The standard Trial Balance:** PASS, 6 of 6.
- **Access over HTTP:** PASS, 24 of 24. Partner Monitor reader, manager, two users without its group, a read-only accountant, users without accounting, another user's wizard, tampered and anonymous downloads.
- **Live:** 7 requests to www.odoo.com, all allowed by robots.txt ([live_site_notes.md](../live_site_notes.md)).

## Open issues and remaining gaps

- **Stage 12:** the README (G-02 to G-06, G-08, T-19, T-20), including O-01.
- **Stage 15:** publication (G-01).
- **Your own browser check** (TP-G-05). The headless checks are the agent's, not yours.
- **Team-lead questions** Q-02 to Q-06; P-17.3 needs the original views specification.
- **Not repeated here:** a full live crawl (on purpose), a live empty-country check, and the Partner Monitor tests on Community (optional).
- **The acceptance project's volumes are kept** (318 MB); deleting them is your decision (STATE, open items).

## Changed files

- `scripts/dev.sh`: default edition, `ensure_env`, `main` (`.env` before the check), `cmd_setup` and `installed_count` (repeat setup), `DEFAULT_ADDONS` (Community runs the Partner Monitor only).
- `.env.example`: the target edition by default.
- `scripts/pm_live_check.py`: `PM_LIVE_KEEP` and `PM_LIVE_DB_CREATED_AFTER`; restores the batch-size setting.
- New scripts:
  - `scripts/acceptance_state.py`: state report and fingerprints, read-only;
  - `scripts/acceptance_users.py`: the acceptance users;
  - `scripts/acceptance_upgrade_seed.py`: seed and probe for the upgrade check;
  - `scripts/acceptance_pm_demo.py`: settings, simulated outage, recovery;
  - `scripts/acceptance_pm_ui_check.py`: the browser demonstration;
  - `scripts/acceptance_access_check.py`: access over HTTP.
- Documentation:
  - new: [acceptance_results.md](../acceptance_results.md);
  - updated: [environment.md](../environment.md) (quick start, troubleshooting, verification), [STATE.md](../STATE.md), [requirements_matrix.md](../requirements_matrix.md) (G-11), [assumptions.md](../assumptions.md) (D-67 to D-69), [test_plan.md](../test_plan.md), [test_results.md](../test_results.md), [live_site_notes.md](../live_site_notes.md), [ai/stage_11.md](../ai/stage_11.md) and the AI log index.
- Outside Git: the exports and the acceptance Compose project under `<kit-root>/runtime/acceptance/`, and the full logs under `<kit-root>/runtime/logs/stage11/`.

## Comprehension questions

1. The acceptance ran with `COMPOSE_PROJECT_NAME=azk-stage11-acc` from an exported folder. What would the first `scripts/dev.sh setup` in that folder have done to the development containers and their database server if the project name had come from `compose.yaml`, with a new `.env` holding new random passwords?
2. Odoo's statistics printed "177 tests" for the Partner Monitor while the summary counted 147 of its tests. Where do the 30 extra entries come from, and which number belongs in a comparison with the Stage 10 baseline?
3. Run 1's failure note reached no inbox, while run 2's did, although the code that posts them is the same. What differed between the two recipients, and why did the local setup make that difference visible?

## Next stage

Stage 12 (submission documentation), when you ask for it.
