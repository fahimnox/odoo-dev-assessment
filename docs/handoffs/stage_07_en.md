# Stage 07 handoff: Trial Balance wizard and calculation contract

_2026-11-15. Edition `enterprise-20241208` (port 8071). Stage 04 stays PARTIAL. Before this stage, the Stage 06 dashboard smoke check was rerun at commit `3222285`: 7 of 7 PASS, recorded in the Stage 06 handoff (commit `597e0e8`)._

## What this stage delivers

- **The wizard** `azk_dynamic_trial_balance.wizard`, with every field of the PDF, server-side validation, private records and a menu entry.
- **The calculation contract** [calculation_contract.md](../calculation_contract.md), written before any calculation code.
- **Fixtures** built from real, balanced journal entries, with hand-calculated expected numbers. The standard Enterprise Trial Balance agrees with them on every case compared.
- **The Preview, PDF and XLSX buttons are entry points only.** They validate the options, then say that the output is not available yet. The calculation engine is Stage 08 and the outputs are Stage 09. These requirements are not marked done.

## Menu path and the wizard

Accounting > Reporting > Audit Reports > Dynamic Trial Balance. It opens a dialog. Users need the read-only accounting group (`account.group_account_readonly`), the same as for the standard Trial Balance.

- **Period:**
  - Date From and Date To default to the current month and are both inclusive.
  - Company is shown to users with several companies. It must be one of the user's companies and active in the company switcher.
- **Options:**
  - Posted Entries: always ticked, read-only.
  - Include Unposted Entries.
  - Hierarchy and Subtotals.
  - Hierarchy Only Parents: appears after Hierarchy and Subtotals is ticked.
  - Account Level Up To (1 to 5): appears after Hierarchy Only Parents is ticked, and is required then.
  - Skip Zero Balance.
  - Show Amount Currency.
- **Filters:**
  - Accounts: type a code prefix and press Enter to make a tag; several tags are combined with OR.
  - Journals: one journal or empty.
  - Analytic Accounts: one or empty; shown with the analytic feature.
- **Help texts:** the PDF's texts, word for word. Show Amount Currency adds one sentence on its dates.
- **Buttons:** Preview, PDF, XLSX, Cancel. A notice at the top says that the outputs are not connected yet.

**Valid option combinations,** checked on the server:

- no hierarchy;
- Hierarchy and Subtotals;
- Hierarchy and Subtotals plus Hierarchy Only Parents with a level from 1 to 5.

**Refused:**

- Only Parents without Hierarchy and Subtotals.
- A level without Only Parents, or Only Parents without a level.
- Show Amount Currency with Only Parents, which has no account lines to split by currency (D-43).

Include Unposted Entries, Skip Zero Balance and the filters combine with everything. Ticking one of two exclusive options unticks the other in the form.

## The January example by hand: Bank

The base fixture (TB-BASE) has these entries. The report period is 2026-01-01 to 2026-01-31.

```text
2025-12-31  posted     Bank debit 1,000   / Capital credit 1,000
2026-01-10  posted     Expense debit 300  / Bank credit 300
2026-01-20  posted     Bank debit 500     / Revenue credit 500
2026-01-25  draft      Expense debit 200  / Bank credit 200
2026-01-26  cancelled  Expense debit 400  / Bank credit 400
2026-02-01  posted     Expense debit 50   / Bank credit 50
```

**Posted entries only:**

```text
Opening   everything posted before 2026-01-01:  debit 1,000      1,000
Movement  2026-01-20 posted debit                 +500
          2026-01-10 posted credit                -300
          movement balance                                        +200
Ending    1,000 + 500 - 300                                      1,200  (debit)
```

**With Include Unposted Entries:**

```text
Opening   unchanged (no draft before 2026-01-01)                 1,000
Movement  debit                                    500
          credit 300 + 200 (the 2026-01-25 draft)  500
          movement balance 500 - 500                                 0
Ending    1,000 + 500 - 500                                      1,000  (debit)
```

**Why the ending falls from 1,200 to 1,000:**

- The draft entry takes another 200 out of the bank, to pay an expense.
- Posted-only reporting ignores it until someone posts it; including drafts counts it as if it were posted.
- The 200 does not disappear: Expense rises from 300 to 500. The report still balances at 1,500 debit and 1,500 credit, because the draft moves 200 from Bank to Expense.
- The cancelled 400 never counts, with or without drafts: Odoo excludes cancelled entries.
- The February 50 is after Date To.

The full expected tables (Debit / Credit / Balance for Initial, Movement and End):

```text
Posted only        Initial               Movement              End
Bank               1,000 /     0 / 1,000   500 / 300 /  200   1,200 /     0 /  1,200
Expense                0 /     0 /     0   300 /   0 /  300     300 /     0 /    300
Revenue                0 /     0 /     0     0 / 500 / -500       0 /   500 /   -500
Equity (Capital)       0 / 1,000 / -1,000    0 /   0 /    0       0 / 1,000 / -1,000
Total              1,000 / 1,000 /     0   800 / 800 /    0   1,500 / 1,500 /      0

With drafts: Bank movement 500 / 500 / 0, End 1,000 / 0 / 1,000;
Expense movement 500 / 0 / 500, End 500 / 0 / 500; Revenue and Equity
unchanged; Total movement 1,000 / 1,000 / 0, End 1,500 / 1,500 / 0.
```

## Comparison with the standard Trial Balance

**How it was compared** (automated, on the disposable database):

1. `scripts/dev.sh test azk_dynamic_trial_balance` drops and recreates `azk_ee24_test`, installs the addon with `account_reports` and demo data, and runs the tests.
2. `TestBaseFixture` creates a new company in EGP with Odoo's generic chart and a calendar fiscal year. It books the six entries above through Odoo's own methods:
   - `action_post` for the posted entries;
   - the draft entry is left in draft;
   - the cancelled entry is posted, then cancelled with `button_cancel`.
3. It runs the standard Trial Balance (`account_reports.trial_balance_report`) with:
   - the same company, and only that company active;
   - Date From 2026-01-01 and Date To 2026-01-31, as a custom range;
   - Draft Entries off, then on (Draft Entries is the standard report's name for Include Unposted Entries);
   - hierarchy off, all journals and no analytic filter.
4. It compares every Initial, period and End debit and credit, and the totals, with the hand-written constants in `tests/common.py`. Neither side is computed from the other.

**Results** (run 3, final code): PASS.

- **Posted only:** all exactly as the hand calculation, Initial / period / End.
  - Bank: 1,000 / 0, then 500 / 300, then 1,200 / 0.
  - Expense: 0 / 0, then 300 / 0, then 300 / 0.
  - Revenue: 0 / 0, then 0 / 500, then 0 / 500.
  - Capital: 0 / 1,000, then 0 / 0, then 0 / 1,000.
  - Total: 1,000 / 1,000, then 800 / 800, then 1,500 / 1,500.
- **With drafts:** Bank moves 500 / 500 and ends at 1,000 / 0; Expense moves 500 and ends at 500 / 0. The totals are 1,000 / 1,000 for the movement and 1,500 / 1,500 at the end. Exactly as the hand calculation.
- **Excluded entries:** in both cases the standard report lists exactly these four accounts and the total, so the cancelled and February entries add nothing.
- **Balance columns:** the standard report has none. Our Balance numbers are debit minus credit (D-04); `test_hand_calculations_are_consistent` checks them.

**Also compared the same way, all PASS:**

- TB-BASE with only the Bank journal, and with only the Misc journal: the journal filter also restricts the opening.
- The cross-year fixture TB-X in January, February, and February with drafts:
  - the 2025 revenue moves to Current Year Earnings;
  - no journal entry exists behind that 700.
- The zero-activity fixture.
- The company-currency amounts of the currency fixture.
- The analytic filter: no filter, A1, A2 and B1.
- Two companies.
- A record rule.
- The hierarchy with five group levels.

Parity is claimed only for these cases ([calculation_contract.md](../calculation_contract.md) 14).

## Concepts, with the example

- **Debit and credit** are the two sides of every journal item.
  - A debit increases an asset (Bank) or an expense.
  - A credit increases a liability, equity (Capital) or income (Revenue).
  - In every entry, the debits equal the credits: the 2026-01-10 entry has Expense debit 300 and Bank credit 300.
- **Balance** is debit minus credit.
  - Bank ends at +1,200, a debit balance: the money in the bank.
  - Revenue ends at -500, a credit balance: income earned.
  - The opening and ending columns show only the side the balance falls on (Bank: 1,200 debit, 0 credit).
  - The movement columns show both sides in full (Bank: 500 debit and 300 credit), because they describe activity, not a position.
- **Journal entry and journal item:**
  - A journal entry (`account.move`) is one business event, such as "pay a 300 expense from the bank". It has a date, a journal and a state: draft, posted or cancelled.
  - Its journal items (`account.move.line`) are its lines, one per account: Expense +300 and Bank -300.
  - The report adds up journal items. The state that decides whether an item counts is its entry's state, copied onto the item as `parent_state`.
  - In Django terms: the entry is a parent model, the items are child rows with a foreign key to it, and the report is a grouped aggregate over the child rows.
- **Wizard and persistent model:**
  - The wizard is a `TransientModel`: a short-lived row that holds one user's choices for one report. It is not business data, and Odoo deletes old wizard rows automatically.
  - Journal entries and accounts are ordinary persistent models (`models.Model`) that live as long as the company's books.
  - In Django terms, the wizard is closer to a form with server-side validation than to a model, except that Odoo stores the form's values in a table between the dialog and the button click.
  - A record rule keeps each wizard private to the user who created it. Without it, another user could guess the row's id and run a report with someone else's options.

## Checks performed

All of these were run by the agent on 2026-11-15. Full logs are in `<kit-root>/runtime/logs/`.

1. **Free space on C:** before any Docker work: 54 GB.
2. **Stage 06 smoke check:** rerun at commit `3222285`: PASS, 7 of 7. It is recorded in the Stage 06 handoff (commit `597e0e8`).
3. **`scripts/dev.sh test azk_dynamic_trial_balance`,** each run on a fresh `azk_ee24_test`:
   - Run 1: FAIL. 1 failure and 2 errors of 47 tests, all in the wizard tests, plus 88 translation warnings. Every fixture and standard-report comparison already passed.
   - Run 2: PASS, 0 failed and 0 errors of 48 tests.
   - **Run 3, on the final code: PASS.** "0 failed, 0 error(s) of 48 tests", 0 warning lines, exit code 0, 289 s.
4. **Free space during the runs,** sampled every 30 s:
   - Run 1: from 54.7 to 50.0 GB, mostly while the database was created.
   - Run 2: from about 49 to 45.7 GB.
   - Run 3: from 46.4 to 46.2 GB.
   - Docker's virtual disk stayed at 17.63 GB (not sparse), and there is no WSL swap file. When idle, free space stayed stable.
   - The use during runs 1 and 2 is not attributed. Windows shadow storage could explain it, but checking it needs administrator rights.
   - After the stage: about 46 GB free.
5. **`scripts/dev.sh update azk_dynamic_trial_balance` on `azk_ee24`:** PASS twice, the second time on the final code (75 s), with 0 warnings. Version 18.0.1.1.0 is installed, and the login page answers.
6. **Headless Chrome check of the wizard** (`scripts/tb_wizard_smoke_check.py`) on `azk_ee24`:
   - Run 1: 6 of 7. The one failure was the check's own label comparison.
     - The agent also looked at the screenshot and found a real bug: Posted Entries was unticked in the new form. It was fixed.
   - **Run 2, on the final code: PASS, 8 of 8:**
     - no loading error;
     - the menu opens the dialog;
     - the notice is shown;
     - Posted Entries is ticked in the new form;
     - every field is there, and the dependent options appear in order;
     - a typed prefix becomes a tag;
     - Preview shows "The Preview is not available yet. Your options are valid, ...";
     - no JavaScript error.
   - Screenshots: `docs/screenshots/stage07_wizard.png` and `stage07_wizard_preview_message.png`.
   - The runs left a few wizard and prefix records of the admin in `azk_ee24`. They are temporary records, which Odoo removes automatically.

**NOT RUN:**

- Our calculation engine: Stage 08.
- The Preview, PDF and XLSX outputs: Stage 09.
- In a browser:
  - the Company field: it is hidden for `azk_ee24`'s admin, who is not in the multi-company group;
  - the Analytic Accounts field: the admin does not have analytic accounting;
  - the wizard as a read-only accountant: tested in Python only.

## Manual checks for you (NOT RUN by the agent)

On http://127.0.0.1:8071 (`azk_ee24`):

1. Open Accounting > Reporting > Audit Reports > Dynamic Trial Balance. Check the layout in a normal browser window, in a light and a dark color scheme.
2. Tick Hierarchy and Subtotals, then Hierarchy Only Parents: Account Level Up To appears and is required. Then tick Show Amount Currency: Hierarchy Only Parents unticks itself.
3. In Accounts, type `1_` and choose "Create": a message refuses it ("can contain only letters, digits and dots"). Type `10` and choose "Create": it becomes a tag.
4. Set Date From after Date To and click Preview: a message refuses the dates.
5. With valid options, click Preview, PDF and XLSX: each says that the output is not available yet.
6. Optional, with a second user:
   - In Settings > Users, give a user "Accounting: Read-only" access and log in with it: the menu and the wizard work.
   - A user without accounting access does not see the menu.
7. Optional: turn on Analytic Accounting (Accounting > Configuration > Settings) to see the Analytic Accounts field.

Please tell me the results; they will be recorded as yours.

## Problems found and fixed

- **The company check failed on an inactive company.** It read the company's name for its message, and Odoo's company rule hides companies that are not active, so the user got an access error instead of the intended message. Found by two failing tests in run 1. The message no longer names the company; no `sudo()` was added.
- **88 translation warnings in the test log.** The option helpers are plain functions, and a bare `_()` could not find the language. They now use Odoo 18's `env._()`, and a test checks that no warning is logged.
- **Posted Entries showed unticked in a new dialog.** It was a computed field without dependencies, and the form of a new record showed it as false. The Python tests passed, because they read saved records. Found in the browser screenshot. It is now a read-only field with a default of true and a constraint; the form test checks the new form.
- **Two mistakes in checks:** a test expected the menu path with spaces around "/", and the browser check compared labels without removing their "?" help marker. Both corrected.
- **The Stage 06 AI log was inaccurate.** It said the Stage 06 final response was displayed unchanged, but after a context compaction a reworded version was displayed: the commit ID was added and several sentences were rephrased, with the same results and statuses. The log now holds the displayed text, extracted from the transcript, with a correction note.
- **The pre-commit scan did not stop the commit chain.** It reported two lines in STATE.md, but always exited with 0, so the commit went ahead. Both lines were already in the previous commit (a Git identity note and a generic per-user install path). The scan now checks only added lines and exits with 1 on a finding.

## Open issues and remaining gaps

- **No calculation engine yet (Stage 08).** Our report computes nothing; the numbers above are checked against the standard report only.
- **No Preview, PDF or XLSX yet (Stage 09).** The buttons are entry points that say so (D-47).
- **No demo data for the Trial Balance yet** (T-21 to T-23). The fixtures are test data, created and rolled back inside the tests.
- **Not compared with the standard report:** currency rows, Skip Zero Balance, Hierarchy Only Parents and its level, the prefix filter, custom fiscal years and branches. The standard report has no equivalent option, or it was not checked; Stage 08 tests these against the hand-calculated constants.
- **Analytic policy:** whole-item selection follows the standard report (A-15, D-07). Proportional allocation is documented, not implemented. Question Q-03 for the team lead is still open.
- **Missing inputs:** the PDF's wizard mockup (M-02) was not supplied, so the dialog's layout is our design.
- **License question Q-06** is still open. The addon declares LGPL-3 and depends on `account_reports` (OEEL-1).

## Changed files

All paths are relative to the repository; the addon is `addons/azk_dynamic_trial_balance/`.

**New:**

- `models/__init__.py`.
- `models/report_options.py`: `normalize_options`, `check_company`, `check_combination`, `clean_prefix` and `clean_prefixes`.
- `models/account_prefix.py`.
- `models/trial_balance_wizard.py`:
  - `TrialBalanceWizard._get_report_options` and `_output_not_available`;
  - `action_preview`, `action_export_pdf` and `action_export_xlsx`;
  - the constraints and onchanges.
- `security/ir.model.access.csv`, `security/trial_balance_security.xml`.
- `views/trial_balance_wizard_views.xml`: the form, the action and the menu.
- `tests/common.py`:
  - `TrialBalanceCase._entry`, `_build_tb_base`, `native_trial_balance` and `assertExpectationsConsistent`;
  - the `TB_*` constants.
- `tests/test_wizard.py`, `tests/test_base_fixture.py`, `tests/test_native_conventions.py`, `tests/test_advanced_fixtures.py`.
- `scripts/tb_wizard_smoke_check.py`.
- `docs/calculation_contract.md`, `docs/handoffs/stage_07_en.md`, `docs/ai/stage_07.md`, and two screenshots in `docs/screenshots/`.

**Updated:**

- The addon's `__init__.py`, `__manifest__.py` (18.0.1.1.0, depends on `account_reports`) and `tests/__init__.py`.
- `docs/STATE.md` and `docs/assumptions.md` (D-43 to D-49, V-08; A-14 and A-15 evidence).
- `docs/architecture.md` (a 4.2 note, and section 4.9).
- `docs/test_plan.md` (rules, 4.1 to 4.3).
- `docs/requirements_matrix.md`: 35 Trial Balance rows, K-02 and K-05.
- `docs/ai/README.md`.
- `docs/ai/stage_06.md`: its final-response section now holds the text actually displayed, with a correction note.

**Committed separately before the stage** (`597e0e8`): the Stage 06 rerun, in `docs/handoffs/stage_06_en.md`, `docs/STATE.md` and `docs/requirements_matrix.md`.

## Comprehension questions

1. Why does the wizard refuse Show Amount Currency together with Hierarchy Only Parents?
2. In January, the 700 of 2025 revenue appears on Current Year Earnings, not on Revenue. Which dates decide this, and what does February's report show for Revenue?
3. Why must the chosen company be active in the company switcher, not just one of the user's companies?

## Next stage

Stage 08: the Trial Balance calculation engine, tested against the same hand-calculated constants.
