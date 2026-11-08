# AI usage log

The assessment recommends GenAI and asks for a log of the prompts used and the resulting outputs. This folder holds that log, one file per stage.

- **Tool / model:** Claude Code (Anthropic's terminal agent), Opus 5.5 (`claude-opus-5-5`), as reported by the session environment.
- **Workflow:** the work follows a staged prompt kit kept outside this repository. Each user prompt names one stage file. The stage file's text is reproduced in the log because it is the instruction the agent actually received.

## How the logs are produced

- User prompts are copied verbatim, including the text of any instruction file they reference.
- The assistant's visible messages are copied verbatim, in the language they were written in. See the language note below.
- Tool calls and their raw outputs are not reproduced. Where they matter, they are summarized in a section labeled **Summary**.
- Hidden reasoning, system instructions and unrelated terminal history are never collected.
- The raw local session transcript is not committed because it contains system and tool content.

## Language change (correction R0, 2026-11-01)

- Stage 00 ran under the original kit, whose contract asked for explanations in Egyptian Arabic. The Stage 00 final report in [stage_00.md](stage_00.md) is therefore in Egyptian Arabic. The `/init` replies and the progress messages were in English.
- R0 refers to an earlier terminal rendering issue. The Stage 00 report mixed right-to-left Arabic with left-to-right English and used wide Markdown tables. The agent did not see the rendered terminal output itself.
- After the Stage 00 commits (13:07 and 13:17 local time), the kit's files were replaced with a revised English-only edition; the kit zip and the `prompts/` folder were modified at 13:36. [stage_00.md](stage_00.md) keeps the original Stage 00 prompt that was actually executed, while the kit's current `prompts/00_operating_contract.txt` is the revised text.
- From R0 onward, terminal output, new documentation, code comments and commit messages are in English (AGENTS.md rule 7). The user's Arabic coaching happens outside this terminal.
- Historical transcripts are kept unchanged. [../handoffs/stage_00_en.md](../handoffs/stage_00_en.md) is a new English summary of Stage 00 written during R0. It is not an original transcript.

## Redactions

| Log | Redaction |
|---|---|
| All logs | Absolute local paths are replaced with `<kit-root>` |
| [stage_01b.md](stage_01b.md) | Names of earlier customer projects found in the company-supplied archive, and the Windows user profile of its old virtual environment, are not reproduced (described generically). No credential or subscription value was ever printed |

## Index

| Log | Stage | Content |
|---|---|---|
| [pre_stage_init.md](pre_stage_init.md) | Before 00 | Two `/init` runs that produced a guidance file for the kit (outside this repository) |
| [stage_00.md](stage_00.md) | 00 | Operating contract, workspace, state files, first requirement inventory |
| [correction_r0.md](correction_r0.md) | After 00 | Language correction R0: English-only output, guidance updates, Stage 00 English handoff |
| [stage_01.md](stage_01.md) | 01 | Docker Compose environment with pinned images, addon skeletons, verification runs |
| [stage_01b.md](stage_01b.md) | 01B | Inspection of the company-supplied Enterprise archive, Enterprise service and database next to the Community baseline, native Trial Balance findings; follow-up of 2026-11-04: official Community revision of the archive's build identified by content, validation blocked by disk space; continuation of 2026-11-05: matched pair fetched, verified and validated on port 8071 |
| [stage_02.md](stage_02.md) | 02 | Requirements matrix, assumptions, architecture and test plan; source checks in the pinned 18.0 core and Enterprise addons; native Trial Balance probe on the matched pair; the same prompt re-sent on 2026-11-08, answered with a status check and no rework |
| [stage_03.md](stage_03.md) | 03 | Partner Monitor models, access rules, basic views, demo data and 53 tests; install, upgrade, shell and HTTP checks on port 8071 |

## Mistakes found and corrected

| Stage | What went wrong | How it was detected | Correction |
|---|---|---|---|
| 00 | The agent tried to extract the kit zip based on the state seen in the earlier `/init` session, without re-checking. The user had already extracted it and removed the zip. | The `unzip` command failed: the archive no longer existed | Re-listed the directory, used `reference/assessment.pdf`, and corrected the kit's guidance file |
| 01 | The first version of `scripts/dev.sh test` trusted Odoo's exit code, which is 0 when no test matches the selection | Reading `ThreadedServer.run()` in the pinned source, which logs "of 0 tests" as a WARNING and still returns 0 | Added a check on the "of N tests" summary line; a no-match run now fails with exit code 1 (verified) |
| 01B | The first `odoo-ee` port mapping (host 8070 to container 8069) left wkhtmltopdf unable to reach `web.base.url`, so the native PDF came out without CSS | The server log warned "wkhtmltopdf: Exit with code 1 due to network error: ConnectionRefusedError" during the PDF check | `odoo-ee` now listens on the same port inside and outside the container; the rerun produced a styled PDF without warnings |
| 01B | The docs claimed Compose would refuse a missing Enterprise folder (`create_host_path: false`) | An explicit check: a raw `docker compose run` with a wrong path exited 0 and Docker Desktop created the folder | Removed the empty folder, corrected the docs, added a warning in `compose.yaml` and the default name to `.gitignore`; the `dev.sh` check remains the guard (verified) |
| 01B | Two commands used POSIX paths while Git Bash path conversion was disabled (`docker compose cp` destination, then `pdftotext`) | Both tools reported that the path did not exist | Reran both with Windows-style paths |
| 01B | `docs/enterprise_transition.md` (commit `2078515`) counted 16 helper scripts at the archive root; the 16th Python file there is the vendor `setup.py` | A recount (`ls *.py`, excluding `setup.py`) while fact-checking the final response | Corrected to 15 scripts in a follow-up commit; the final response states 15 |
| 01B | Stage 01B judged the archive's files by timestamp: it reported 13 files "changed after the build date" (also in the final response) and suspected code changes in `ir_actions.py` | Follow-up of 2026-11-04: content comparison with the official build commit `4e5027c1` | 2 of those files are unchanged, 6 differ only in formatting (identical Python syntax trees, including `ir_actions.py`), 2 have real local edits, 3 are config files; documents corrected |
| 01B follow-up | `certificate`, `l10n_it_edi_website_sale` and `project_hr_skills` were classified as Enterprise modules of the 2024 build ("623 modules") and copied to an extra folder, because their manifests say OEEL-1 there while the 2026 image says LGPL-3 | 2026-11-05: in the first matched-pair database, `certificate` loaded from the official Community folder; a check against the official tree confirmed all three are Community-repository modules | Corrected to 620 Enterprise modules in all documents; the redundant folder was removed and deleted, and both test commands were rerun on the final configuration |
| 01B continuation | Two inline check scripts failed: a backslash in a Windows path broke a Python string, and a file comparison did not skip translation files that the fetched source excludes by design | The scripts' own errors (`SyntaxError`, `FileNotFoundError`) | Rerun with the path cosmetics removed and translation files skipped; the checks themselves were unaffected |
| 01B follow-up | A `df -h /` check of Docker's file system failed because Git Bash rewrote `/` into a Windows path | The command printed a "No such file or directory" error for the Git install path | Reran with path conversion disabled |
| 01B | A draft of `docs/STATE.md` attributed most of the lost disk space to Docker growth from this stage's runs, which could not be verified | Review before the commit: the virtual disk's size at the start of the stage was unknown, and another project shares it | Reworded to state only the measured 0.65 GB and leave the rest unattributed |
| 01B (all three parts) | The three "Assistant final response" sections of [stage_01b.md](stage_01b.md) held the drafts prepared before display. The displayed responses were reworded: the results and statuses are the same, but some details and commit IDs differ | Stage 02 compared every logged response with the session transcript; the conversation sections matched, the final-response sections did not | Each final-response section now holds the displayed text, extracted from the transcript, with a correction note. Stage 02's own final response is displayed exactly as logged |
| 02 | The first draft of [architecture.md](../architecture.md) said the admin's notifications go to the Odoo Inbox by default | A read-only query of `res_users.notification_type` in `azk_ee24_clean`: `admin` has `email`, only `__system__` has `inbox` | Corrected before the commit; decision D-08 and the demo steps account for it |
| 02 | The script that corrected the Stage 01B log matched the first "final response" heading instead of the last, and replaced far more than one section | `git diff --stat` showed 223 deleted lines | Restored the file from Git and redid the correction on the right sections; a paragraph-by-paragraph check against the transcript confirmed the result |
| 02 | [architecture.md](../architecture.md) said the partial unique indexes would be built with `odoo.tools.sql.create_index(..., where=...)`, which builds non-unique indexes; it also planned a post-init hook to find the installing user, but hooks run as the superuser | Reading `odoo/tools/sql.py` and `odoo/modules/loading.py` while implementing Stage 03 | Stage 03 creates the indexes with parameterized SQL in `init()`, and defaults the recipient to the administrator (D-19); architecture 5.2 and 5.7 corrected |
| 03 | A security-test fixture was stored as `cls.run`, which replaced unittest's `TestCase.run()`, so the test runner crashed and the remaining test classes never ran | The first test run logged "TypeError: 'azk_odoo_partner_monitor.sync.run' object is not callable" and ended with "of 0 tests" and exit code 255; `scripts/dev.sh test` reported "no tests ran" | Renamed the fixture to `sync_run`; the rerun passed 53 of 53 |
| 03 | Re-adding a removed reference hit the one-active-per-key index: the ORM delayed the UPDATE that closed the old record, while the INSERT of the new one ran at once | `TestReferences.test_returning_reference_opens_a_new_interval` failed with a unique violation in the first run | `_sync_references` now flushes pending closures before inserting and right after closing; `action_retry` flushes its change too; two regression checks read the database directly |
| 03 | Two fields of `sync.run` had the same label, "Errors" | An install warning in the first test run | Renamed the counter labels; the rerun logged 0 warnings |
