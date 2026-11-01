# Before Stage 00 — `/init` sessions (kit setup)

- **Date:** 2026-11-01
- **Tool / model:** Claude Code, Opus 5.5 (`claude-opus-5-5`)
- **Working directory:** the assessment kit root (outside this repository)
- **Output:** a `CLAUDE.md` guidance file in the kit root. It is not part of this repository.

**Transcription method:** the user turns and the assistant's visible messages are copied verbatim from the session. `/init` is a built-in Claude Code command; its built-in instruction template is not reproduced. Tool calls and their outputs (directory listings, file reads) are not reproduced.

**Redactions:** absolute local paths are replaced with `<kit-root>`.

---

## Exchange 1

At this point the kit directory was empty.

### User

```text
/init
```

### Assistant (visible response, verbatim)

I didn't create a CLAUDE.md. `<kit-root>` is empty: there's no code, no README, no Cursor or Copilot rules, and it isn't a git repo. Any build commands or architecture notes I wrote now would be made up.

From the folder name, this looks like it's for an Odoo assessment. You have two options:

- **Add the project files first** (for example, clone the repo or copy in the assessment brief), then run `/init` again. I'll write CLAUDE.md from what's actually there.
- **Tell me what you're building**, such as the Odoo version, whether it's a custom addon or a full instance, and how you'll run it (Docker, local `odoo-bin`, etc.). I can then write a starter CLAUDE.md with the run, test and upgrade commands for that setup.

I also found an OpenAI Codex config at `~/.codex/config.toml`. To bring its settings into Claude Code (MCP servers, slash commands, subagents, skills, instructions), reply `/import` to see what can be imported. Then run `/import --yes=<digest>`, using the digest shown in the scan output, to apply the user-level items. If `/import` isn't available here, run `claude import` from a terminal.

---

## Exchange 2

The user had added the assessment PDF, the kit zip, `PROMPT_SHEET_EN.md` and `START_HERE_AR.md`.

### User

```text
/init
```

### Assistant (visible messages, verbatim)

Intermediate message:

> I've read the kit's guide and prompt sheet. Now I'm pulling text from the assessment PDF so CLAUDE.md can cite its actual requirements.

Final response:

I've created `CLAUDE.md` at the root of the folder. There's no application code here yet, only the assessment PDF and the AI kit for working through it, so the file explains how to run the kit rather than describing an existing codebase.

It covers:
- **What's in the folder:** the assessment PDF is the source of truth for requirements. The step-by-step instructions (one per stage) are in `PROMPT_SHEET_EN.md` and the zip. The actual work will go in a `solution/` folder, which is the only part that becomes a git repo and gets published.
- **How to work:** run one stage at a time, use the two recovery prompts for resuming a session or fixing a failure, explain in Egyptian Arabic, and only publish to GitHub in Stage 15.
- **What's in scope:** Exercises 1 and 2 on Odoo 18 Community, with no Enterprise-only modules. Exercise 3 (POS) is out. The views spec, the Trial Balance mockup and the example repo the PDF mentions were never supplied, so the file says not to claim otherwise.
- **The planned design for both exercises:** for Partner Monitor, how the scraper survives interruptions without redoing work. For the Trial Balance, one calculation shared by the on-screen preview, PDF and Excel, plus the hand-checked bank example (1,200 posted-only, 1,000 with drafts).
- **Evidence rules:** report every check as passed, failed, blocked or not run, and keep the AI logs to what actually appeared in the conversation. It also says where Claude Code saves its transcripts, which you'll need for the AI log the assessment asks for.

Things to know:
- **There are no build or test commands yet.** None exist until Stage 01 sets up the Odoo environment. The Commands section is a placeholder that tells a future session to fill it in from `solution/docs/environment.md` once that's written.
- **`prompts/` and `reference/` are still inside the zip.** I checked that the zip's copies of the two guides and the PDF are byte-identical to the ones already here, so `unzip -n Odoo_Assessment_AI_Kit.zip` safely adds just the missing folders. I can run it now if you like.
- **Your PDF tool can't display pages here.** Text extraction with `pdftotext` works, and the file notes that.
- **Your Codex config is still available to import.** Reply `/import` to see what can be brought over from `~/.codex/config.toml`, then `/import --yes=<digest>` to apply it.

When you're ready to start: `Read prompts/00_operating_contract.txt and execute Stage 00 only.`
