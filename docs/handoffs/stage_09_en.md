# Stage 09 handoff: Trial Balance outputs (Preview, PDF, XLSX)

_2026-11-15. Edition `enterprise-20241208` (port 8071), continuing from the Stage 08 commit `845accb`. Stage 04 stays PARTIAL._

## What this stage delivers

- **One path for every output.** Our `account.report` record "Dynamic Trial Balance" and its custom handler connect the Stage 08 engine to the standard report framework of `account_reports`:
  - the standard report UI renders the Preview;
  - the standard exporters produce the PDF and the XLSX.
  All three take their lines from the handler, and the handler calls the engine once per request. No output computes an amount itself (K-01, D-54).
- **Preview:** the wizard's Preview opens the standard report view with the wizard's options. A filter bar component adds the Trial Balance options (hierarchy, only parents and level, Skip Zero Balance, Show Amount Currency), account prefixes, journal and analytic account next to the standard date filter, Draft Entries, Unfold All and search. Every change reloads the report from the server, so the engine recalculates. Group rows fold and unfold. Messages: an empty result, filters that make the report unbalanced, and the engine's warnings.
- **PDF:** the standard exporter (wkhtmltopdf, landscape), with three of our templates:
  - the report company's name and address;
  - every option as "label: value", including the period and the amount-currency scope;
  - the column groups with their widths, in a header that repeats on every page (D-55).
- **XLSX:** our own sheet for this report only (D-56):
  - the options above the table;
  - merged group headers;
  - codes and names as text, amounts as numbers with a number format;
  - a separate currency column, frozen header rows.
- **Exports follow the preview:** the current options, the search text and the folded groups (D-57). Nothing is stored: every request recalculates as the requesting user (D-58).
- **Demo data:** a dedicated company, "AZK Trial Balance Demo (EGP)":
  - posted, draft and cancelled entries;
  - USD and EUR entries, and analytic distributions;
  - account groups five levels deep.
  It reproduces the assessment's January example and is created once, so upgrades never duplicate it (D-59).
- **Tests:** 102 tests in total, 17 of them new (output consistency, access and tampering, demo data). The browser and server check covers the real Preview, the real downloads and the download route.

## Short browser walkthrough

Log in on http://127.0.0.1:8071 and select only "AZK Trial Balance Demo (EGP)" in the company switcher.

1. Open Accounting > Reporting > Audit Reports > Dynamic Trial Balance. Set Date From 01/01/2026 and Date To 01/31/2026, tick Skip Zero Balance, and click Preview.
2. The standard report view opens. Bank (101401) shows Initial Balance 1,000.00, Movement 500.00 debit and 300.00 credit, End Balance 1,200.00.
3. Open Options and tick Draft Entries. The report reloads, and Bank now ends at 1,000.00: the draft credit of 200 joined the movement.
4. Type "bank" in the search bar: only Bank (and, with the hierarchy on, its groups) stays visible. Clear it.
5. Open the "Trial Balance" menu and tick Hierarchy and Subtotals. Group rows appear (1 Assets > 10 Current Assets > ... > 10140 Bank Accounts). Click a group to fold it and again to unfold it.
6. Click PDF, and in the gear menu "Download Excel". Both files show the same rows and numbers as the screen, with the company, the period and every option printed above the table.
7. Untick Skip Zero Balance and print again: a multipage PDF whose column header repeats on every page.
8. In the Accounts filter type 8 (no account starts with 8): the report says that no journal items match.
9. Optional, the analytic filter: it appears only with Odoo's Analytic Accounting setting (Accounting > Configuration > Settings), which is off on `azk_ee24` (D-62). With it on, choose March 2026 and "Sales Department": the report keeps the journal items whose analytic distribution contains that account, each at its full amount (D-07).

What the agent ran in headless Chrome, and what it found, is under "Checks performed". This stage has no browser check by the user.

## From the wizard to each output: files and functions

**Opening the Preview**

1. `views/trial_balance_wizard_views.xml`: the dialog's Preview button calls `action_preview`.
2. `models/trial_balance_wizard.py`:
   - `TrialBalanceWizard.action_preview()` reads the wizard (the record rule makes it readable by its creator only);
   - `_get_report()` returns the report record `azk_dynamic_trial_balance.dynamic_trial_balance_report`;
   - `_get_preview_options()` turns the wizard into report options: the date range, `all_entries` (Draft Entries), `unfold_all`, and our keys in `azk_tb`. It goes through `_get_report_options()`, which validates with `normalize_options()` (`models/report_options.py`);
   - the method returns the client action `account_report` with these options.
3. In the browser, the standard report controller (`account_reports`) calls `account.report.get_options()`, then `get_report_information()`, over RPC.
4. `models/trial_balance_report_handler.py`, `TrialBalanceReportHandler._custom_options_initializer()` runs inside `get_options()`:
   - `_raw_engine_options()` and `normalize_options()` validate the options again;
   - `options['companies']` becomes the report company;
   - `_set_columns()` lays out the column groups;
   - `_display_values()` builds the printed texts, and `_filter_choices()` lists the journals and analytic accounts.
5. `get_report_information()` calls `account.report._get_lines()`, which calls the handler's `_dynamic_lines_generator()`:
   - `TrialBalanceEngine.compute(self._engine_options(options))` (`models/trial_balance_engine.py`) returns the result;
   - `_report_lines()` turns the rows into lines, and `_columns()` builds each cell with the standard `_build_column_dict()`;
   - `_add_warnings()` adds the messages.
6. A filter change in the browser: `TrialBalanceFilters.setTbOptions()` (`static/src/components/trial_balance/filters.js`) updates `options.azk_tb` and calls the standard `applyFilters()`, so steps 4 and 5 run again.

**PDF** (the preview's PDF button, or the wizard's PDF button)

1. The preview's button calls `dispatch_report_action(options, 'export_file', 'export_to_pdf')`. The wizard's `action_export_pdf()` calls `_export()`, which builds the same options. Both end in `account.report.export_file()`, which returns a download action.
2. The browser posts the options to `/account_reports` (`AccountReportController.get_report`, `account_reports`). It takes the active companies from `options['companies']` and calls `dispatch_report_action(options, 'export_to_pdf')`.
3. `account.report.export_to_pdf()`:
   - `get_options(... 'export_mode': 'print')` runs our `_custom_options_initializer()` again;
   - `_get_lines()` runs the engine again;
   - our `_custom_line_postprocessor()` applies the search text, and `_filter_out_folded_children()` drops folded children;
   - `_get_pdf_export_html()` renders the QWeb template `account_reports.pdf_export_main`. It calls our `pdf_company_information`, `pdf_export_filters` and `pdf_export_main_table_header` (`data/pdf_export_templates.xml`), named in the handler's `_get_custom_display_config()`;
   - `ir.actions.report._run_wkhtmltopdf()` turns the HTML into the PDF.

**XLSX** (the preview's gear menu "Download Excel", or the wizard's XLSX button)

1. Steps 1 and 2 as for the PDF, with `export_to_xlsx`.
2. `account.report.export_to_xlsx()` creates the workbook and calls `_inject_report_into_xlsx_sheet()`. For our report, our override in `models/account_report.py` calls `_write_dynamic_trial_balance_sheet()`:
   - `_get_lines()` with `no_format` runs the engine again;
   - the same search and folding rules apply;
   - xlsxwriter writes the cells.
3. The Filters sheet comes from our `_inject_report_options_into_xlsx_sheet()`, from the same printed texts.

## Four explanations

- **QWeb** is Odoo's XML templating language: `t-if`, `t-foreach`, `t-out` (escaped output), `t-call` (include another template) and `t-att-*` (computed attributes). On the server it renders the PDF's HTML. The standard template `account_reports.pdf_export_main` calls sub-templates by name, taken from the handler's display configuration, and that is how our three templates replace three parts without copying the rest. In the browser, OWL components use the same language: our filter template inherits the standard one with `t-inherit` and an XPath, much like a Django template that `{% extends %}` a base and overrides a `{% block %}`.
- **`ir.actions.report`** is Odoo's report action model. A record names a QWeb template and a paper format; `_render_qweb_pdf()` renders the HTML and converts it with wkhtmltopdf through `_run_wkhtmltopdf()`. The `account_reports` framework has no such record per report: `export_to_pdf()` renders its own template and calls the same converter directly. So Stage 09 needed no new `ir.actions.report` record. A custom one stays the documented fallback (architecture 4.7) and was not needed.
- **Transient wizard state.** `azk_dynamic_trial_balance.wizard` is a TransientModel: its records live in a normal table, and Odoo's daily autovacuum deletes those older than `transient_age_limit` (1 hour by default). A record rule on `create_uid` keeps each wizard private. The wizard holds the choices only until Preview or an export is clicked; they then become report options. The preview keeps its own state in those options in the browser, which travel with every reload and export. So a preview keeps working after its wizard has been vacuumed, and no other user can reach someone's wizard (each button reads it first, and a stranger gets AccessError).
- **Why one shared engine prevents drift.** The Preview, the PDF and the XLSX never compute: they all call `_get_lines()`, which calls the handler, which calls `compute()` with the same validated options. A rounding rule, a draft rule or an analytic rule therefore exists once. Fixing it fixes every output, and no output can disagree with another. The tests check this directly: for eight option sets, the preview lines equal the engine rows, the XLSX cells equal the printed lines, and every PDF row prints exactly the cells of one printed line. In Django terms: one service function returns the data, and three renderers (a template, a PDF view, an Excel view) only format it.

## Checks performed

All on 2026-11-15, edition `enterprise-20241208`. Details and the earlier runs are in [test_results.md](../test_results.md).

- **Automated tests:** PASS on the final code. `scripts/dev.sh test azk_dynamic_trial_balance` (fresh `azk_ee24_test`) gave "0 failed, 0 error(s) of 102 tests", 0 warning lines, exit 0, 438 s.
  - Run 2 passed 101 of 101.
  - Run 1 was stopped (see "Problems found and fixed"), and run 3 was superseded by run 4.
- **The three outputs against the engine (unit tests):** for eight option sets the preview lines equal the engine rows, the XLSX cells equal the printed lines, and every PDF row prints exactly the cells of one printed line. Bank is 1,200 posted only and 1,000 with drafts in all three.
- **Demo data and upgrades:** PASS. The counts come from `scripts/dev.sh shell DB < scripts/tb_demo_data_counts.py`.
  - `azk_ee24_test`: counted after the install, upgraded with `scripts/dev.sh update azk_dynamic_trial_balance azk_ee24_test` (exit 0, 62 s, 0 warnings), and counted again: the same.
  - `azk_ee24`: the demo function was called once from an Odoo shell, then three upgrades ran (exit 0, 0 warnings each): the same counts each time.
  - The counts: 16 entries (13 posted, 2 draft, 1 cancelled), 32 items, 10 groups, 2 plans, 3 analytic accounts, 2 rates, 7 journals.
- **Browser (the agent's headless Chrome on `azk_ee24`, final code):** `scripts/tb_preview_smoke_check.py` PASS, 20 of 20; the updated `scripts/tb_wizard_smoke_check.py` PASS, 7 of 7. Screenshots: [screenshots/](../screenshots/) (`stage09_*.png`).
- **XLSX against the engine:** in the same check, the XLSX downloaded from "Download Excel" equals the engine result (19 rows with the Total), and so do the eight XLSX files from the download route.
  - Amounts are numeric with the format `#,##0.00;-#,##0.00;0.00`.
  - Codes and names are text, and the header is frozen at C17.
- **PDF text and visual inspection:**
  - The real PDFs contain every row of the engine for the eight option sets.
  - Three PDFs were rendered to PNG and inspected (1 page, 3 pages, amount currency): landscape, readable and not clipped, with the report company, the period and every option, the column groups, bold groups and balanced totals, and the header on every page.
  - One cosmetic detail: two slightly taller row gaps on pages 2 and 3 of the 3-page PDF.
  - Samples: [samples/](../samples/).
- **Access:**
  - Unit tests: an accounting reader previews and exports; employees and billing users get AccessError; another user's wizard gives AccessError on all three buttons; tampered options are refused on the preview and both exports.
  - On the server: the route refused a tampered prefix with a `ValidationError` and gave only the login page without a session.
- **NOT RUN:**
  - the analytic dropdown in the browser (Odoo's Analytic Accounting setting is off on `azk_ee24`, D-62);
  - custom fiscal years and branch companies (Stage 10, D-60);
  - a real wkhtmltopdf inside unit tests (replaced by a stub by design, D-63);
  - a browser check by the user.

## Problems found and fixed

- **First test run stopped by the CLI.** The run's background command was stopped at about 08:41 UTC because the machine was critically low on memory. Three causes were found in its log:
  - an `HttpCase` class made Odoo build every asset bundle before the tests (about 13 minutes);
  - the first real PDF render in a unit test made no progress;
  - the container stayed stuck after the command was stopped, until the agent stopped it with `docker stop`.
  Fix: unit tests replace `_run_wkhtmltopdf` with a stub that keeps the HTML document (Odoo's own `account_reports` tests replace it too), the `HttpCase` class was removed, and the route and real PDFs are checked on the running server (D-63).
- **Warning at install:** "Incorrect usage of try_loading without a fully loaded registry". The demo company was created while modules were still loading. Fix: the creation waits for `_register_hook`, as the `account` module does for its own first chart. No warning since.
- **The first upgrade of `azk_ee24` created no demo data.** Odoo loads demo files as noupdate data and runs their functions at install only; `azk_ee24` had the module since Stage 07. Fix: the comments were corrected, and the demo function was called once from an Odoo shell on `azk_ee24`. Upgrades then left every count unchanged.
- **"United States" under an Egyptian company in the PDF.** Without a country, loading the generic chart sets its fiscal country as the company's country. Fix: the demo company is created with Egypt, plus a regression assertion; `azk_ee24`'s demo company got the same value.
- **Group rows not bold on screen.** Our stylesheet set weight 600 on their cells, which overrode the standard bold of unfolded rows (found with a computed-style probe). Fix: bold.
- **The PDF lost the rounding unit.** Our filters template replaced the standard one, which prints "Amounts in Thousands" when a rounding unit is chosen. Fix: printed again, with a regression test; the XLSX keeps exact numbers (D-61).
- **Browser check mistakes, fixed in the checks themselves:**
  - the XLSX download is "Download Excel" in the gear menu, not a button named XLSX;
  - a refused download answers HTTP 200 with a JSON error body, so the check now reads the error instead of the status.
- **Before the first run:**
  - a non-dictionary `azk_tb` would have raised TypeError instead of a validation error; fixed;
  - the description of the standard XLSX writer was corrected after reading it (it writes numbers, but in the General format).

## Open issues and remaining gaps

- **For Stage 10 (D-60):**
  - custom fiscal years (`account.fiscal.year`) and branch companies are not covered by the tests;
  - two limits of the standard framework are kept as they are: the date filter's fiscal-year presets follow the company that is current in the switcher, and the standard "unposted Journal Entries" banner counts the drafts of every active company.
- **Stage 04 stays PARTIAL:** the page-download module of the Partner Monitor is still deferred.
- **Browser check by the user:** recommended, with the walkthrough above, in a normal browser.
- **Unit tests and real PDFs:** unit tests capture the HTML that wkhtmltopdf prints, and do not start the binary (as Odoo's own tests do). Real PDFs were rendered only on the running server, by the browser check.
- **`azk_ee24` demo data:** created by one shell call because the module was installed before Stage 09; a fresh install creates it automatically.
- **Analytic Accounting** is off on `azk_ee24`, so its analytic filter is hidden there (D-62).
- **Memory on the host** is tight with the current applications; close unused ones before long runs.
- **Cosmetic:** two slightly taller row gaps in the 3-page PDF.

## Changed files

New in the addon `addons/azk_dynamic_trial_balance/`:

- `models/trial_balance_report_handler.py`: `TrialBalanceReportHandler`:
  - display and options: `_get_custom_display_config`, `_custom_options_initializer`, `_raw_engine_options`, `_engine_options`, `_display_values`, `_filter_choices`, `_set_columns`;
  - lines: `_dynamic_lines_generator`, `_report_lines`, `_columns`, `_custom_line_postprocessor`, `_add_warnings`.
- `models/account_report.py`: `AccountReport._is_dynamic_trial_balance`, `_inject_report_into_xlsx_sheet`, `_inject_report_options_into_xlsx_sheet`, `_write_dynamic_trial_balance_sheet`.
- `models/demo_data.py`: `TrialBalanceDemo._create_demo_data`, `_register_hook`, `_demo_accounts`, `_demo_journals`, `_demo_analytic_accounts`, `_demo_entries`.
- `data/trial_balance_report.xml` (the report record and its columns), `data/pdf_export_templates.xml` (`pdf_company_information`, `pdf_export_filters`, `pdf_export_main_table_header`), `demo/trial_balance_demo.xml`.
- `static/src/components/trial_balance/filters.js` (`TrialBalanceFilters`: `tbOptions`, `tbChoices`, `toggleTb`, `setTbOptions`, `setPrefixes`), `filters.xml` (the filter bar and the message templates), `trial_balance.scss`.
- `tests/test_report_outputs.py`, `tests/test_report_access.py`, `tests/test_demo_data.py`.

Changed in the addon:

- `__manifest__.py`: version 18.0.1.3.0; the report, PDF and demo files; the asset bundle.
- `models/__init__.py`.
- `models/trial_balance_wizard.py`: `_get_report`, `_get_preview_options`, `action_preview`, `_export`, `action_export_pdf`, `action_export_xlsx`.
- `views/trial_balance_wizard_views.xml`: the "not connected yet" notice is gone.
- `tests/__init__.py`, `tests/common.py` (`capture_wkhtmltopdf`, `html_text`, `pdf_rows`, `STUB_PDF`), `tests/test_wizard.py`, `tests/test_engine_access.py`.

Scripts:

- new: `scripts/tb_preview_smoke_check.py`, `scripts/tb_demo_data_counts.py`;
- changed: `scripts/tb_wizard_smoke_check.py`.

Documentation:

- [STATE.md](../STATE.md), [requirements_matrix.md](../requirements_matrix.md), [assumptions.md](../assumptions.md) (D-47 superseded; D-54 to D-63), [architecture.md](../architecture.md) 4.7 and 4.11, [calculation_contract.md](../calculation_contract.md) 16, [test_plan.md](../test_plan.md) 4.5 and 6, [test_results.md](../test_results.md);
- [samples/](../samples/) (five exports and a README), [screenshots/](../screenshots/) (eleven `stage09_*.png`);
- this handoff, [ai/stage_09.md](../ai/stage_09.md) and [ai/README.md](../ai/README.md).

## Comprehension questions

1. The PDF button of the preview and the XLSX item of its gear menu both end in the same route. Which function validates the options again there, and why must it, even though the preview already validated them?
2. Why does the handler mark every group line `unfolded` or not, and send all child lines, instead of loading children when a group is unfolded? What would the PDF and XLSX lose otherwise?
3. The demo data is created by a function called from a demo XML file. Why does an upgrade never run that function, and why must the function still check the company's XML id before it creates anything?

## Next stage

Stage 10 (engineering review), when the user requests it.
