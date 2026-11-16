# Release checklist

_Stage 12, 2026-11-16. The local release checkpoint is the Stage 12 commit, marked with the annotated tag `submission-rc1`. The tag is local: nothing is pushed or published before Stage 15._

## 1. What the checkpoint contains

- **The two addons:** `addons/azk_odoo_partner_monitor` 18.0.1.5.0 and `addons/azk_dynamic_trial_balance` 18.0.1.3.0. Their code is unchanged since Stage 10 (`e54214b`); Stage 12 changed only the fixtures README of the Partner Monitor tests (documentation).
- **Setup:** `compose.yaml`, `config/`, `docker/`, `.env.example` and `scripts/dev.sh`, with the quick start accepted from a clean checkout in Stage 11.
- **Checks:** the scripts in `scripts/` (browser, access, restart, live sample, benchmarks, acceptance).
- **Documentation:** [README.md](../README.md), this folder, the AI logs in [ai/](ai/README.md), the handoffs, small sample exports ([samples/](samples/)) and screenshots ([screenshots/](screenshots/)) produced by the checks.
- **Not included, on purpose:** Odoo core and the Enterprise addons, `.env`, database dumps and filestores, virtual environments, caches, the full command logs and saved live pages (kept privately under the kit root), the assessment PDF, the prompt kit and private study notes.

## 2. Checklist

Verified for this checkpoint:

- [x] Installation from a clean checkout, following only the documentation and the declared dependencies: PASS in Stage 11 (each addon alone, both together, with and without demo data, and an upgrade from Stage 09). [acceptance_results.md](acceptance_results.md)
- [x] Automated tests: 261 of 261 (147 Partner Monitor, 114 Trial Balance) in a fresh database, Stage 11. No addon code changed afterwards.
- [x] Restart check 12 of 12; browser checks 7, 7, 20 and 7 of the same; access checks 24 of 24; the standard Trial Balance 6 of 6 (Stage 11).
- [x] README with the scope, the platform and its pins, the prerequisites, installation, commands, isolated copies, configuration (including mail delivery of the failure notes), features, resilience, testing, demo, assumptions and limitations, status, evidence, AI use and license (Stage 12).
- [x] Architecture, resilience and calculation documents describe the final implementation (Stage 12 updates).
- [x] Demo script with exact menus, data labels, expected numbers, a failure-and-recovery story and an offline fallback: [demo_script.md](demo_script.md).
- [x] Final requirement matrix with a status summary: [requirements_matrix.md](requirements_matrix.md).
- [x] Documentation checks (Stage 12): relative links and anchors of every Markdown file, the commands and file paths named in the README and the demo script, ASCII text in the new and updated documents. Results: [test_results.md](test_results.md).
- [x] Publication review of the files and of the Git history (section 3).

Not done (see section 5):

- [ ] The candidate's own manual check of the final screens (TP-G-05; requirement T-19).
- [ ] The decisions of section 4.
- [ ] The public repository (Stage 15).

## 3. Publication review (2026-11-16)

A script read every file to be published (198 files, 4.15 MB) and every blob of the repository's 24 commits. Results:

- **Files:** no `.env`, dump, log, virtual environment, cache or vendor folder; the largest file is a 171 kB screenshot; no blob over 500 kB in the history; every path ever committed is still present, so no deleted file hides in the history.
- **Secrets:** the real database passwords of the local `.env` files and the acceptance users' password occur in no file and in no blob of the history. No private key or access token. The password-like matches are code that reads environment variables, and the role script's parameter.
- **Local paths:** no Windows or Unix user path in any published file. The AI logs and documents use `<kit-root>`, `<home>` and `<scratchpad>` instead.
- **Vendor content:** no Odoo license header. No published line equals a line of the Enterprise modules the solution uses (`account_reports`, `account_accountant`, `accountant`, `web_enterprise`), apart from interface lines that extending the framework requires: imports, the report handler's hook signatures and standard field names in XML records. No Odoo or Enterprise source file is in the repository or its history.
- **Personal data:**
  - The Git identity (user name and work email address) is in the metadata of all 24 commits. The email address also appears in four documents: `docs/STATE.md`, `docs/handoffs/stage_00_en.md`, and the transcripts `docs/ai/stage_00.md` and `docs/ai/stage_01.md`. The candidate chose this identity in Stage 00. See decision 1.
  - The test addresses are `@example.com`. The live-derived fixtures are trimmed public listing pages without email addresses or phone numbers.
- **AI logs:** visible user and assistant text only, with the redactions listed in [ai/README.md](ai/README.md). Non-ASCII text appears only in the historical Stage 00 transcript (Arabic), in one dash of the first log, and in two symbols of `AGENTS.md`, all written before the English-only correction.
- **Commit messages:** no path, secret or address other than the agent's `Co-Authored-By` line.

## 4. Decisions for the candidate before publication

1. **Git identity.** Keep the work email address public, or rewrite the commits' author (for example to a GitHub "noreply" address) and redact the four documents, recording the redaction in [ai/README.md](ai/README.md). Rewriting history changes every commit id, so it must happen before the first push.
2. **License (Q-06).** The manifests declare LGPL-3 as an unconfirmed default (A-06), and no license file is included (D-70). Decide the license, add the file and align both manifests; `azk_dynamic_trial_balance` depends on the OEEL-1 module `account_reports`.
3. **The manual check (TP-G-05).** Follow [demo_script.md](demo_script.md) in a normal browser and record the result in README section 10; then T-19 becomes DONE.
4. **The open questions Q-02 to Q-06.** Ask them before publication, or publish with the documented defaults.
5. **The supplied archive.** It contains an earlier implementation of this assessment's modules, which was never opened or used. Whether to mention it to the team lead is the candidate's decision ([STATE.md](STATE.md), open items).
6. **The tag.** Push `submission-rc1` with the branch, or tag the published commit anew in Stage 15.

## 5. Pending work

- **P-17.3, IN PROGRESS:** the original views specification was never supplied (M-01, Q-02), so "the required filters, groupings and pivot configurations remain the same" cannot be checked.
- **T-19, IN PROGRESS:** the candidate's manual check (decision 3).
- **G-01, NOT STARTED:** the public GitHub repository and its link (Stage 15).
- **Questions Q-02 to Q-06:** unanswered; the defaults stand ([assumptions.md](assumptions.md)).
- **Stages 13 and 14** (code walkthrough and mock interview) are interactive preparation for the candidate; they change nothing in the submission unless a defect is found.
- **Not planned:** a full live crawl (on purpose, D-64); the Partner Monitor test suite on the Community baseline (optional, TP-G-03); multi-process Odoo workers; other hosts and operating systems.
- **Local clean-up (no effect on the submission):** the Stage 11 acceptance project `azk-stage11-acc` and its volumes (318 MB) are kept for the demo; delete them when no longer needed ([STATE.md](STATE.md)).

## 6. How to check the checkpoint again

```text
git checkout submission-rc1          # or the branch it marks
scripts/dev.sh setup                 # quick start, README section 4 (in a new folder: README section 6)
scripts/dev.sh test                  # expect "0 failed, 0 error(s) of 261 tests"
scripts/dev.sh start                 # then the demo script
```
