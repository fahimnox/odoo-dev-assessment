# Correction R0 - English-only terminal output

- **Date:** 2026-11-01
- **Tool / model:** Claude Code, Opus 5.5 (`claude-opus-5-5`)
- **Working directory:** the assessment kit root (`<kit-root>`)
- **Scope:** language and formatting correction only. No stage work, and no change to scope or completion status.

**Transcription method:** see [README.md](README.md). User text, the referenced instruction file and the assistant's visible messages are verbatim. Tool activity is a labeled summary.

## User prompt (verbatim)

```text
Read prompts/R0_english_only.txt and apply the language correction only. Preserve the existing Stage 00 work.
```

## Referenced instruction file: `prompts/R0_english_only.txt` (verbatim)

```text
CORRECTION R0 - Switch the existing project to English-only terminal output

Stage 00 has already been completed in this workspace. Preserve that work. This is a language/formatting correction, not a request to start the assessment again.

MY UPDATED LANGUAGE PREFERENCE
From now on, use English only for all terminal replies, progress updates, explanations, questions, stage reports, newly authored project documentation, comments, and commit messages. This supersedes my earlier request for Egyptian Arabic. I will discuss the work in Arabic separately with ChatGPT, outside this terminal session. Use plain English text, short paragraphs or bullets, and simple ASCII formatting. Avoid wide tables, box-drawing characters, mixed RTL/LTR prose, and decorative Unicode formatting. Preserve actual source data and historical transcripts faithfully; do not transliterate data values or rewrite original logs just to fit this presentation preference.

DO NOW
1. Inspect the current workspace and Git status. Read the existing project state and identify the current completed stage. Do not unzip a missing archive, recreate solution/, initialize a new repository, rerun Stage 00, reinstall the environment, or change assessment scope.
2. Update conflicting language instructions in existing project-local guidance, including solution/AGENTS.md, kit-root CLAUDE.md if present, and relevant scoped AGENTS.md/CLAUDE.md files that apply to this project. Preserve all unrelated instructions. Do not edit account-wide or unrelated-project configuration.
3. Check the active prompt files and PROMPT_SHEET_EN.md for remaining directions to explain or ask questions in Arabic. If the revised kit is already present, preserve it; otherwise make the minimal matching language correction locally. Stage 13/14 teaching and questions must also be English. Treat START_HERE_AR.md as a human-only guide, not terminal-agent instructions.
4. Keep previous actual prompts/responses unchanged as historical evidence. Add an English note to the AI-log index identifying this preference change and the earlier terminal rendering issue. If a past reply needs an English restatement, label it as a new summary, not an original transcript. Ongoing state/design documents may be translated into English without changing their facts or completion status.
5. Save a readable English Stage 00 handoff at solution/docs/handoffs/stage_00_en.md, based on the actual files and evidence. Include completed work, requirement inventory scope, assumptions, real commands/results, blockers, and the next stage. Do not copy unverifiable claims as proven results. Report tests not executed as NOT RUN. Use bullets instead of terminal tables.
6. Update STATE.md with the language correction and the actual next stage. Log this real request/output. If making a local commit, stage only the intended documentation/guidance changes under the existing repository; do not rewrite existing commits or change Git identity.

Finish with a concise English summary of the correction and, if Stage 00 is indeed the last completed stage, this next command:
Read prompts/01_environment.txt and execute Stage 01 only, following solution/AGENTS.md.

Stop after the correction. Do not start Stage 01 automatically in this turn.
```

## Assistant intermediate message (verbatim)

1. Checks are done: the revised kit is already in place and matches the new zip, so only the project guidance and logs need edits. Updating AGENTS.md, the kit CLAUDE.md, STATE.md and the AI log index now, then writing the English Stage 00 handoff.

## Summary of tool activity (summary, not verbatim)

1. Read `prompts/R0_english_only.txt` and listed `prompts/`.
2. Inspected the kit root and the repository: the working tree was clean, with commits `50c1465` and `868fefa`. A count of `pdftotext` page breaks gave 14 pages.
3. Searched `prompts/*.txt` and `PROMPT_SHEET_EN.md` for directions to use Arabic. None remain: Arabic is mentioned only as coaching that happens outside the terminal, and no Arabic-script text was found.
4. Compared each file in the new `Odoo_Assessment_AI_Kit.zip` with the extracted kit. All 22 files are identical, so the revised kit was already present and was left unchanged.
5. Confirmed that `docs/ai/stage_00.md` holds the original Stage 00 prompt (rule 7: "Explain in Egyptian Arabic"), while the kit's current Stage 00 prompt is the revised English-only text.
6. Looked for other project guidance files (CLAUDE.md or AGENTS.md in parent directories and in the repository, `.claude` folders, `~/.claude/CLAUDE.md`). None exist.
7. Edited `AGENTS.md` (a scope bullet marking `START_HERE_AR.md` human-only, rules 7 and 9, a `docs/handoffs/` row), the kit-root `CLAUDE.md` (file list, handoff note, language rule), `docs/STATE.md` (R0 record) and `docs/ai/README.md` (language note, index row).
8. Wrote `docs/handoffs/stage_00_en.md` and this log, then inserted the R0 file text with a short Python script.
9. Staged the five repository files by name and made one local commit.

## Assistant final response (verbatim)

Everything between the two rules below is the final visible response.

---

Correction R0 is applied. Stage 00 is still the last completed stage, and its scope, requirements and status are unchanged.

Changes:
- `solution/AGENTS.md`: rule 7 now carries the revised kit's English-only rule, with the ASCII-formatting part applied to terminal output and handoffs. Rule 9 also requires an English handoff per stage in `docs/handoffs/`. `START_HERE_AR.md` is marked human-only.
- Kit-root `CLAUDE.md` (outside the repo): the same language rule and handoff note, `START_HERE_AR.md` marked human-only, and R0 and the new zip added to the file list.
- `solution/docs/handoffs/stage_00_en.md`: a new English Stage 00 handoff, built from the repo files and the recorded commands. Tests are listed as NOT RUN.
- `solution/docs/ai/README.md`: an English note on the language change and the earlier terminal rendering issue. The Arabic Stage 00 transcript is unchanged.
- `solution/docs/STATE.md`: records R0. The next stage is still 01.
- `solution/docs/ai/correction_r0.md`: the log of this request and reply.

Checks:
- The revised kit was already in place. All 22 files in the new zip match the extracted kit, and no prompt still asks for Arabic in the terminal, including Stages 13 and 14. I left the kit prompts and `PROMPT_SHEET_EN.md` untouched.
- The kit was replaced after Stage 00 ran, so `docs/ai/stage_00.md` holds the original prompt that was actually executed. The log index now says so.
- No other project-level `CLAUDE.md` or `AGENTS.md` exists, and nothing account-wide was edited.

Git: one new local commit on `main`, containing only those five repo files. The Stage 00 commits and the git identity are unchanged, and nothing was pushed.

One judgment call: repository docs such as the requirements matrix keep their Markdown tables, because I applied the formatting rule to terminal output and handoffs only. Say if you want those converted to bullets too.

Next command:

```text
Read prompts/01_environment.txt and execute Stage 01 only, following solution/AGENTS.md.
```

---
