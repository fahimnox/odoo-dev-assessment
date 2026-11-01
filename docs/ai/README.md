# AI usage log

The assessment recommends GenAI and asks for a log of the prompts used and the resulting outputs. This folder holds that log, one file per stage.

- **Tool / model:** Claude Code (Anthropic's terminal agent), Opus 5.5 (`claude-opus-5-5`), as reported by the session environment.
- **Workflow:** the work follows a staged prompt kit kept outside this repository. Each user prompt names one stage file. The stage file's text is reproduced in the log because it is the instruction the agent actually received.

## How the logs are produced

- User prompts are copied verbatim, including the text of any instruction file they reference.
- The assistant's visible messages are copied verbatim. Assistant explanations are in Egyptian Arabic by the user's choice, so transcripts keep that language.
- Tool calls and their raw outputs are not reproduced. Where they matter, they are summarized in a section labeled **Summary**.
- Hidden reasoning, system instructions and unrelated terminal history are never collected.
- The raw local session transcript is not committed because it contains system and tool content.

## Redactions

| Log | Redaction |
|---|---|
| All logs | Absolute local paths are replaced with `<kit-root>` |

## Index

| Log | Stage | Content |
|---|---|---|
| [pre_stage_init.md](pre_stage_init.md) | Before 00 | Two `/init` runs that produced a guidance file for the kit (outside this repository) |
| [stage_00.md](stage_00.md) | 00 | Operating contract, workspace, state files, first requirement inventory |

## Mistakes found and corrected

| Stage | What went wrong | How it was detected | Correction |
|---|---|---|---|
| 00 | The agent tried to extract the kit zip based on the state seen in the earlier `/init` session, without re-checking. The user had already extracted it and removed the zip. | The `unzip` command failed: the archive no longer existed | Re-listed the directory, used `reference/assessment.pdf`, and corrected the kit's guidance file |
