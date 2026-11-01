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

## Index

| Log | Stage | Content |
|---|---|---|
| [pre_stage_init.md](pre_stage_init.md) | Before 00 | Two `/init` runs that produced a guidance file for the kit (outside this repository) |
| [stage_00.md](stage_00.md) | 00 | Operating contract, workspace, state files, first requirement inventory |
| [correction_r0.md](correction_r0.md) | After 00 | Language correction R0: English-only output, guidance updates, Stage 00 English handoff |

## Mistakes found and corrected

| Stage | What went wrong | How it was detected | Correction |
|---|---|---|---|
| 00 | The agent tried to extract the kit zip based on the state seen in the earlier `/init` session, without re-checking. The user had already extracted it and removed the zip. | The `unzip` command failed: the archive no longer existed | Re-listed the directory, used `reference/assessment.pdf`, and corrected the kit's guidance file |
