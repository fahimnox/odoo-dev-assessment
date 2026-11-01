# Stage 00 handoff (English)

This is a new English summary, written on 2026-11-01 during language correction R0. It restates Stage 00 from the repository files and the commands recorded in the AI logs. It is not an original transcript. The original Stage 00 exchange, with its report in Egyptian Arabic, is in `docs/ai/stage_00.md`.

## Status

- Stage 00 (operating contract, workspace, state files, first requirement inventory) is complete.
- No business features are implemented.
- Tests: NOT RUN. Stage 00 has no code to test.
- Next stage: 01, build and verify the local development environment.

## Completed work

- Read the assessment PDF, kept in the kit as `reference/assessment.pdf` and never committed. It has 14 pages. Pages 1-8 were read in full. Pages 9-14 were skimmed (opening lines and a keyword search) and contain only the POS exercise.
- Created `solution/` as a local Git repository on branch `main`, containing:
  - `AGENTS.md`: the persistent working contract (scope, rules, state files, what must never be committed).
  - `docs/STATE.md`: stage tracker, decisions in force, open items, observed host facts.
  - `docs/requirements_matrix.md`: the first requirement inventory, with PDF page references.
  - `docs/assumptions.md`: missing inputs, working assumptions, ambiguities, questions for the team lead.
  - `docs/ai/`: the AI usage log index and the verbatim logs.
  - `.gitignore` and `.gitattributes` (line endings normalized to LF).
- Updated the kit-root `CLAUDE.md` (outside the repository) to match the extracted kit layout.
- Explained addon, model, view, action and wizard with Django analogies. An English restatement is at the end of this file.

## Selected scope

- Exercise 1, `azk_odoo_partner_monitor` (PDF pages 2-6):
  - Scrape the official Odoo Partners pages with `requests` and `BeautifulSoup`, triggered by a daily cron.
  - Store countries, partners, status history and client references.
  - Track first-seen dates, status promotions and demotions, and added or removed references.
  - Validate counts, with two separate re-processing crons (countries and partner references).
  - Handle the case where an empty country returns all partners.
  - Continue past a failing partner or country, log all errors, and post a chatter message to a configurable user.
  - Provide an XML dashboard as the module's entry point: four charts sharing the Status, Country and Year First Seen filters.
  - Explain the resilience design in the README.
- Exercise 2, Dynamic Trial Balance (PDF pages 6-8), addon `azk_dynamic_trial_balance` (assumed name):
  - A transient wizard with account-prefix, journal and analytic filters.
  - Options: include unposted entries, hierarchy and subtotals, parents only up to level 1-5, skip zero balance, show amount currency.
  - Initial balance, period movement and ending balance columns, each with debit, credit and balance.
  - Preview, PDF and XLSX outputs.
  - Demo/test data and tests that check the calculations against a known dataset.
- Exercise 3 (POS) is out of scope. The PDF asks candidates to pick two of the three exercises (page 3).
- Platform: Odoo 18 Community. This is a working assumption the assessor has not confirmed.

## Requirement inventory

- `docs/requirements_matrix.md` lists 64 requirements:
  - G-01 to G-13: general and submission requirements (pages 1-3).
  - P-01 to P-27: Partner Monitor (pages 2-6).
  - T-01 to T-23: Dynamic Trial Balance (pages 6-8).
  - X-01: POS exercise (pages 8-14).
- Status: G-13 (pick two exercises) is DONE. G-07 (document assumptions) and G-09 (GenAI prompt log) are IN PROGRESS. X-01 is OUT OF SCOPE. The other 60 are NOT STARTED.
- The interpretation, implementation and evidence columns are filled in from Stage 02 onward.

## Missing inputs (not supplied, not read)

- M-01, page 4: the original views specification, with its filters, groupings and pivot configurations.
- M-02, page 6: the Trial Balance wizard mockup.
- M-03, page 1: the `azk_zkteco_machine_proxy` documentation example, named without a link or file.

## Working assumptions

- A-01: Exercises 1 and 2 are selected and Exercise 3 is not (decided by the user).
- A-02: the target is Odoo 18 Community (unconfirmed; see Q-01).
- A-03: the Exercise 2 addon is named `azk_dynamic_trial_balance` (unconfirmed default).

## Ambiguities to resolve in Stage 02

- D-01: which existing report "TB" and "Odoo's dynamic reports" refer to, and whether it exists in Community.
- D-02: Journals and Analytic Accounts are Many2One fields, but their help texts use plural wording.
- D-03: the wizard field list has no date or company fields, although the PDF header needs the selected date range.
- D-04: what Debit and Credit mean for the Initial and Ending columns.
- D-05: the example project-size buckets leave a gap between 10 and 11 and overlap at 25.
- D-06: whether Top/Bottom 5 rankings are computed before or after the dashboard filters, and how ties are handled.
- D-07: how the analytic filter treats journal items whose distribution spans several analytic accounts.

## Questions for the team lead (not yet asked)

- Q-01: Is Odoo 18 Community acceptable for Exercises 1 and 2?
- Q-02: Can you share the original views specification, the Trial Balance wizard mockup, and the azk_zkteco_machine_proxy documentation link?
- Q-03: Must the Trial Balance match a specific existing report exactly (opening balances / fiscal-year handling, analytic filtering), or is documented ledger-based behavior acceptable?

Work continues under the documented defaults until answers arrive.

## Commands run and results

- `unzip -n Odoo_Assessment_AI_Kit.zip`: FAIL. The archive did not exist at that time because the kit had already been extracted. The agent had relied on the folder state from the earlier `/init` session (recorded in `docs/ai/README.md`).
- `ls -la` and `find` in the kit root: `prompts/` and `reference/assessment.pdf` present; no `solution/` yet.
- `pdftotext -layout -f N -l N reference/assessment.pdf -`: full text for pages 1-8; opening lines plus a keyword search for pages 9-14.
- `git --version`: `git version 2.53.0.windows.2`.
- `git rev-parse --is-inside-work-tree` in the kit root: `fatal: not a git repository (or any of the parent directories)`, so `solution/` is not nested inside another repository.
- `git init -b main` in `solution/`: `Initialized empty Git repository`.
- `git add` (eight files, by name) and `git commit`: commit `50c1465`.
- A short Python script inserted the Stage 00 prompt text into `docs/ai/stage_00.md` (25 lines), then `git commit`: commit `868fefa`. The working tree was clean afterwards.
- Both commits use the global identity `fahimnox <mohamed.fahim@noxholding.com>`, chosen by the user.
- During R0, a count of `pdftotext` page breaks confirmed the PDF has 14 pages.
- Earlier, during the `/init` session: `python --version` reported `Python 3.12.0`, and `pdftotext` was found in Git Bash.

## Blockers and open items

- No blocker for Stage 01.
- A-02 and A-03 are unconfirmed, and Q-01 to Q-03 have not been sent yet.
- The commit email (`mohamed.fahim@noxholding.com`) becomes public in Stage 15 unless the identity is changed before publication.
- Not yet checked: Docker/WSL, PostgreSQL, wkhtmltopdf, RAM and disk. Stage 01 covers these.

## Concept primer (English restatement)

This is background from general Odoo knowledge, first given in Stage 00 in Arabic. It has not yet been checked against the pinned Odoo 18 source, which Stage 01 sets up.

- Addon (module): like a Django app. `__manifest__.py` declares the dependencies and the data files (XML, CSV) to load, in order. A module is installed per database, from Apps or with `-i`, not through `INSTALLED_APPS`. There is no `makemigrations` step: the ORM creates and alters tables when the module is installed or updated.
- Model: like a Django `models.Model`. It is named by a string such as `azk_odoo_partner_monitor.partner` and stored in the table `azk_odoo_partner_monitor_partner`. Other modules can extend it with `_inherit`. `self` is usually a recordset, which is similar to a QuerySet but has methods that act on it directly.
- View: not a Django view. It is closer to a template plus `ModelAdmin` settings: XML that describes a screen (list, form, search, pivot, graph), stored in the database, with no business logic. Some tag and attribute names changed between versions, so they must be checked against the Odoo 18 source.
- Action: like a URLconf entry plus generic-view settings. It is a record that says "open model X with these views and this filter". Menus point to actions. Types include window, report (for PDF), server and client actions.
- Wizard: like a plain Django `Form` (not a `ModelForm`) shown in a dialog. It is a `TransientModel`: stored temporarily and cleaned up by Odoo periodically. The Trial Balance filters belong here; partner history does not, because it must persist.
- Chains in this project:
  - menu -> action -> dashboard or list view
  - menu -> action -> wizard -> Preview, PDF or XLSX -> one shared calculation engine

## Comprehension questions (translated from the Stage 00 report)

1. When a user clicks the "Partners" menu in our module, what chain of steps leads to the partner list appearing, and which link in that chain decides the model and the filter?
2. Why does the PDF require a standalone country model instead of Odoo's existing `res.country`, and what could break if we used the existing one?
3. If the scraper requests a country with no partners and gets every partner back, what would go wrong in the data if we trusted that result?

## Next stage

```text
Read prompts/01_environment.txt and execute Stage 01 only, following solution/AGENTS.md.
```
