# Architecture (Stage 02)

_Written 2026-11-05 in Stage 02 as the agreed design. Stage 03 (2026-11-08) built the Partner Monitor models, access rules and basic views; section 5.10 records what was built and what changed. Stage 04 (2026-11-08, partial) built the parsers and the ingestion; see section 5.11. Stage 05 (2026-11-10) built the scheduled jobs and the worker; see section 5.12 and [resilience.md](resilience.md). Stage 06 (2026-11-10) built the dashboard and the remaining views; see section 5.13. Stage 07 (2026-11-15) built the Trial Balance wizard, its option contract and its test fixtures, and wrote [calculation_contract.md](calculation_contract.md); see section 4.9. Stage 08 (2026-11-15) built the calculation engine; see section 4.10. The rest is not implemented yet. Requirement IDs (P-xx, T-xx, G-xx, K-xx) refer to [requirements_matrix.md](requirements_matrix.md), assumption IDs (A-xx, D-xx, M-xx, Q-xx) to [assumptions.md](assumptions.md), and test IDs (TP-xx) to [test_plan.md](test_plan.md)._

## 1. Target and sources used

- **Runtime:** edition `enterprise-20241208` (service `odoo-ee-20241208`, port 8071). It is the official Community source `odoo/odoo@4e5027c1` plus the 620 Enterprise modules of build 18.0+e.20241208 (A-12). Odoo Enterprise is confirmed (A-08); the major version 18.0 is provisional (A-09, Q-04).
- **How the design was checked:** every version-sensitive API below was read in the pinned sources, `runtime/community/18.0-4e5027c1/` and `runtime/enterprise/18.0-20241208/`, both outside this repository. Enterprise code is cited by module, model, method and XML ID names only.
- **Native Trial Balance probe (2026-11-05):** a read-only script ran the native Trial Balance on a small known dataset in the disposable database `azk_ee24_clean`, then rolled back. Its results are in section 4.8. The full log is private (`<kit-root>/runtime/logs/stage02_native_tb_probe.log`).

## 2. Components

```text
EXERCISE 1: azk_odoo_partner_monitor (depends: mail; no Enterprise dependency)

  odoo.com/partners (public HTML, untrusted input)
        |
        v
  [Fetch layer]   services/http_client.py   requests: timeouts, limited retries,
        |                                   polite delay, error classification
        v  (status, final URL, HTML)
  [Parse layer]   services/parsers.py       pure functions: HTML -> typed results
  [URL rules]     services/urls.py          country_id check, canonical identity
        |  (records + expected counts + completeness flags)
        v
  [Sync engine]   models/work_item.py, models/sync_run.py (ORM)
        |  claim units -> one savepoint per unit -> upsert by source keys
        |  -> status/reference diffs -> validation flags -> errors
        v
  [Business models] country, partner, status.history, reference
        |
        v  ORM _read_group as the calling user
  [Dashboard]  client action (OWL, small) with shared filters
               + 4 embedded standard graph views defined in XML

  Crons (ir.cron): daily discovery, worker, country validation,
  reference validation. Producers enqueue work items; only the worker
  processes them. A failed run posts a note to the configured user.

EXERCISE 2: azk_dynamic_trial_balance (depends: account_reports)

  [Wizard] TransientModel, one record per user and run
        |  Preview / PDF / XLSX buttons
        v
  options = the normalized filter contract (plain JSON-able values)
        |
        v
  [Report adapter] our own account.report record "Dynamic Trial Balance"
                   + our custom handler (account.report.custom.handler)
        |  validates every option on every call
        v
  [Engine] AbstractModel service: grouped ORM queries on account.move.line
           -> leaf rows -> hierarchy rows -> totals -> warnings
        |  one normalized result
        v
  native report UI (Preview) | native PDF export | native XLSX export
  (+ the handler's display hooks, e.g. a PDF header with company and dates)
```

## 3. Security boundary

```text
  Browser / RPC client  (untrusted: ids, options, domains, filter values)
        |  session-authenticated JSON-RPC and HTTP routes
  ======|=========================== server boundary ===================
        v
  Entry points: wizard buttons, report handler, dashboard method,
                manual sync buttons, download route
        |  check groups; re-validate every id and option; never trust a
        |  client-sent company, journal, analytic account or domain
        v
  ORM as the calling user: ACLs + record rules (incl. multi-company)
        |  no blanket sudo(); raw SQL only for row locks, parameterized
        v
  PostgreSQL
```

- **Accounting data** (Exercise 2) is read as the calling user. Every query goes through the ORM's `_read_group` on `account.move.line`, which applies ACLs and record rules. The selected company must be one of the user's active, authorized companies (`env.companies`). Journal and analytic account ids must be readable by the user and belong to that company (analytic accounts may also be shared). These checks run in the engine itself, because the native download route can pass client-sent options straight to the export method.
- **Wizard isolation:** Odoo 18 has no implicit owner rule for transient models: `BaseModel._check_access` only applies `ir.model.access` and `ir.rule`. So the wizard gets an explicit record rule, `create_uid = user`. Another user's wizard id cannot be read, previewed or exported.
- **Scraped data** (Exercise 1) is public website data and is not company-specific. It is shared across companies on purpose: no `company_id`, no multi-company rules. Readers can read the business data and the dashboard. Managers can also see sync runs, work items and errors, and can schedule a sync or a retry. Nobody can create status history or edit sync checkpoints through ACLs; only the sync engine writes them.
- **Cron engine:** crons run as `base.user_root`. In this version `api.Environment` turns superuser mode on for that uid, so the engine bypasses ACLs by design, as every Odoo cron does. Interactive actions never call the engine directly: they enqueue work and call the worker cron's `_trigger()`. `_trigger()` creates an `ir.cron.trigger` record, which only system administrators may create, so this one call uses a narrow, documented `sudo()`.
- **Untrusted HTML:** parsed text is stored as plain strings and rendered by QWeb/OWL with escaping. Nothing from the site is evaluated, and no site HTML is rendered as markup.

## 4. Exercise 2: Dynamic Trial Balance

### 4.1 Why our own engine inside the native report framework

The native Trial Balance (`account_reports.trial_balance_report`, handler `account.trial.balance.report.handler`, built on `account.general.ledger.report.handler`) lacks several required features:

- the Balance columns;
- account-prefix filtering;
- Skip Zero Balance;
- per-currency rows;
- a level limit.

Its journal and analytic filters are multi-select. So:

- **Reused natively:** the report framework (`account.report`) provides the on-screen UI, which is the "look and feel of Odoo's dynamic reports" (T-16), plus the date filter, the Draft Entries toggle, the search bar, the PDF export and the XLSX export. All of them consume the lines produced by our handler, so the three outputs cannot drift apart (K-01).
- **Ours:** the arithmetic, the engine. It reproduces the native conventions verified in section 4.8 and adds the assessment's features. It is a small service: three grouped ORM queries and plain Python aggregation, and it is testable without the UI.
- **Not done:** we do not prototype-inherit the native Trial Balance handler for its numbers. That would leave two engines (native sums plus our currency and level logic) and break the "one normalized result" rule.
- **Not modified:** the native Trial Balance itself. Our report is a separate `account.report` record, not a variant of `trial_balance_report`.

Verified extension points (names only):

- report fields: `custom_handler_model_id`, `filter_date_range`, `filter_show_draft`, `filter_multi_company`, `filter_hierarchy`, `filter_journals`, `filter_analytic`, `search_bar`;
- handler hooks: `_custom_options_initializer`, `_dynamic_lines_generator`, `_custom_line_postprocessor` (runs after the native hierarchy step in `_get_lines`), `_get_custom_display_config` (keys `components`, `templates`, `pdf_export`);
- line helpers: `_get_generic_line_id`, `_build_column_dict`;
- exports: `export_file(options, file_generator)`, which returns the `ir_actions_account_report_download` action, plus `export_to_pdf` and `export_to_xlsx`;
- the download route `/account_reports` (`auth='user'`);
- the client action `account_report`, which reads `context.report_id` and `params.options` with `params.ignore_session`. The native `account.move` code opens reports the same way.

### 4.2 Wizard (TransientModel `azk_dynamic_trial_balance.wizard`)

Fields, with the PDF's labels and help texts:

- `date_from`, `date_to` (Date, required; default: the current month, like the native report). Added because the PDF requires a period and a header date range (D-03).
- `company_id` (one company, required; default `env.company`; domain: the active allowed companies).
- Posted Entries: a read-only, always-true display field mirroring "Posted entries are always set to True".
- `include_unposted` "Include Unposted Entries": drafts join posted; cancelled entries never do.
- `hierarchy_subtotals` "Hierarchy and Subtotals".
- `hierarchy_only_parents` "Hierarchy Only Parents": visible and valid only with Hierarchy and Subtotals. It reveals `account_level` "Account Level Up To" (selection 1 to 5), which is required while Only Parents is set.
- `account_prefix_ids` "Accounts": several literal code prefixes (OR), entered as tags. The tags are a small transient model, `azk_dynamic_trial_balance.account.prefix` (transient-to-transient many2many is allowed). Empty means all accounts.
- `journal_id` "Journals" (Many2one `account.journal`) and `analytic_account_id` "Analytic Accounts" (Many2one `account.analytic.account`). The PDF's cardinality is kept despite the plural help texts (D-02). Empty means all.
- `skip_zero_balance` "Skip Zero Balance".
- `show_amount_currency` "Show Amount Currency". The help text is the PDF's, plus one sentence giving the column's date scope (D-11).
- Buttons: Preview, PDF, XLSX.

Server-side validation (constraints plus engine checks):

- `date_from <= date_to`;
- the company is in `env.companies`;
- the journal belongs to the company; the analytic account belongs to it or is shared;
- Only Parents requires Hierarchy and Subtotals, and the level must be 1 to 5;
- prefixes are trimmed, non-empty, at most 64 characters and de-duplicated.

Prefixes are matched literally: `%`, `_` and `\` are escaped before the `=like` search, so `1_` never acts as a wildcard. (Stage 07 went further, D-44: prefixes may contain only the characters of account codes, so such prefixes are refused with a message, and the engine's escaping is a second safeguard.) Account codes are company-dependent in 18.0: `account.account.code` is computed from `code_store` and searched by `_search_code`, using the root company of `env.company`. So the engine always runs with `with_company(company)`.

### 4.3 Flow and the normalized filter contract

1. A wizard button validates the record and converts it to plain option values: dates, company id, include_unposted, hierarchy flags and level, prefix strings, journal id, analytic id, skip_zero, show_amount_currency.
2. `report.get_options(previous_options)` builds the full native options. Our `_custom_options_initializer` copies only our known keys, re-validates them, and pins `options['companies']` to the one validated company.
3. Each button returns a different action:
   - Preview returns the `account_report` client action with `params.options` and `ignore_session`;
   - PDF returns `report.export_file(options, 'export_to_pdf')`;
   - XLSX returns `report.export_file(options, 'export_to_xlsx')`.
4. Every path ends in `report._get_lines(options)`, then our `_dynamic_lines_generator`, then `engine.compute(params)`, which returns the normalized result. From there the native UI renders the lines and the native exporters write them.
5. **Exports from the preview** send the preview's current options back to the server. So they match what the user sees, including filter changes made in the preview.
6. **Isolation:**
   - the options travel with each request;
   - each wizard is private to its creator (section 3);
   - nothing is cached between requests or users;
   - each output is a live recalculation from the same options. Stage 09 tests that the three outputs are equivalent on an unchanged database.

Preview filters:

- **Native:** the date range, Draft Entries (mapped to Include Unposted Entries) and the search bar. These are native because their semantics match ours.
- **Disabled native filters:**
  - the multi-select journal and analytic filters (they would break the Many2one contract);
  - native multi-company (we use one company per report);
  - the native hierarchy builder (our engine builds the hierarchy rows, section 4.6).
- **Our other options** travel as custom option keys. Stage 09 shows them in the preview through the handler's `_get_custom_display_config` filter component. If that hook proves unsuitable, the preview shows them read-only with a button that reopens the wizard.

### 4.4 Calculation contract (summary; the full contract is Stage 07's `docs/calculation_contract.md`)

Notation: report company K, period [F, T], S = start of the fiscal year that contains F (from `res.company.compute_fiscalyear_dates(F)`), all amounts in K's currency.

**Scope of every query** (opening, carry-forward and movement alike):

- `company_id = K`;
- `parent_state = 'posted'`, or `parent_state != 'cancel'` with Include Unposted Entries;
- `display_type` not in (`line_section`, `line_note`);
- the journal, if one is selected;
- the analytic account, if one is selected: `('analytic_distribution', 'in', [id])`;
- the user's record rules.

**Opening (Initial) balance per account:**

- Balance-sheet accounts (`include_initial_balance` true, computed from `internal_group`): all scope items dated before F.
- Income and expense accounts: scope items dated S <= date < F. This is zero when F = S.
- Carry-forward: income and expense items dated before S are added to the opening balance of K's "Current Year Earnings" account (`account_type = 'equity_unaffected'`). This is a report presentation, as in the native report, not a journal entry. If K has no such account, the engine returns a warning instead of inventing a row.
- The carry-forward sums all income and expense accounts within the scope; the account-prefix filter only decides whether the earnings row is displayed. This matches the native report, whose search filter does not restrict the carry-forward.

**Movement:** gross debit and gross credit of the scope items with F <= date <= T, inclusive. Movement Balance = debit - credit.

**Ending:** Ending Balance = Opening Balance + Movement Balance.

**Display:**

- Initial and End Debit/Credit are the net side of the signed balance: debit = max(balance, 0), credit = max(-balance, 0).
- Each group also shows its signed Balance (debit positive), so a line has nine numbers (T-15).
- Every number is rounded to K's currency, and zero tests use `currency.is_zero`.

**Grain, groups and totals:**

- A row is an account, or an (account, currency) pair with Show Amount Currency.
- A group row is the sum of its descendant leaf rows: debit and credit separately, so a group can show both sides, as the native hierarchy does.
- The Total row is the sum of the leaf rows, never of group rows.

**Skip Zero Balance:**

- On: a row is hidden when its opening balance, movement debit and movement credit are all zero. An account with equal debit and credit movement stays visible.
- Off: every non-deprecated account of K that matches the account filter is listed, even without journal items. Any account with amounts is also listed (D-12).

**Show Amount Currency** (T-12):

- Rows are grouped by account and the journal item's `currency_id`, sorted by account code, then currency.
- The extra column is the period movement in that transaction currency, the sum of `amount_currency` for F <= date <= T, shown with its currency symbol (D-11).
- Group and total rows leave the column empty. A separate section lists one total per currency, so different currencies are never added together.
- Historical company-currency amounts are used as stored; nothing is revalued at today's rate.
- The carry-forward is attributed to the earnings row in company currency.

**Analytic** (D-07): native whole-item inclusion. A journal item is included at its full amount once when any key of its distribution contains the selected account. Composite keys such as `"12,40"` count once. Without a filter every item counts once, and items are never multiplied by analytic plans. An analytic-scoped report need not balance. Proportional allocation remains a documented alternative (Q-03).

### 4.5 Why these conventions

They are the native conventions, observed on the same dataset with the same options (section 4.8). They are also read in the pinned code by name:

- `account.general.ledger.report.handler._get_options_initial_balance`, `_get_query_sums` and `_get_options_unaffected_earnings`;
- `account.trial.balance.report.handler._dynamic_lines_generator`, which nets Initial and End and computes End from the other groups;
- `account.report._get_options_all_entries_domain`;
- the analytic condition in `account.report._get_report_query` (the `analytic.mixin` overlap test).

The only deliberate differences from the native report are the assessment's additions: Balance columns, prefixes, Skip Zero Balance, currency rows, the level limit and the single journal and analytic account.

### 4.6 Hierarchy (T-06, T-07)

- An account's group is `account.account.group_id`: the most specific `account.group` of K's root company whose prefix range contains the code. Ancestors follow `parent_id`, which Odoo maintains from the prefixes. Level = number of ancestors + 1. Accounts without a group go under "(No Group)" at level 1, after the real groups, as in the native report.
- **Hierarchy and Subtotals:** group rows in code order, each followed by its child groups and accounts.
- **Hierarchy Only Parents** with Account Level Up To N shows only group rows of level N or less, plus "(No Group)", and no account rows. A shown group still aggregates all of its descendants, so deeper groups and ungrouped accounts are never dropped.
- The engine builds these rows itself, so it can apply the level limit and keep currencies apart. The native hierarchy builder (`account.report._create_hierarchy`) sums every numeric column, including a currency column. Its grouping and subtotal behavior is the parity reference (probe R8).

### 4.7 Outputs (T-13 to T-18)

- **Preview:** the native UI on our report record (search bar, date filter, Draft Entries, fold and unfold of group rows).
- **PDF:** the native `export_to_pdf`, which needs a real wkhtmltopdf. The native header shows the company name and address, but the period appears only as the column header (for example "Jan 2026"). So a small header template, supplied through the handler's `pdf_export` display hook, adds an explicit "From F to T" line and the selected filters (T-17).
- **XLSX:** the native `export_to_xlsx`. Stage 09 checks numeric cells, indentation by level and number formats against the specification, and adds a writer hook only for a verified gap.
- **Fallback:** if a native exporter cannot meet a requirement, a custom QWeb `ir.actions.report` or a custom xlsxwriter writer consumes the same engine result.
- **As built (Stage 09):** see 4.11. The standard exporters are used; the XLSX sheet of this report is written by our own writer from the same lines (D-56), and no custom `ir.actions.report` was needed.

### 4.8 Evidence: native Trial Balance on the matched pair (probe, 2026-11-05)

Dataset: company "AZK TB Probe" (EGP, generic chart, calendar fiscal year), created in `azk_ee24_clean` and rolled back. All moves are in the Misc journal except M4, which is in the bank journal:

- M1 2025-06-30: Current Assets debit 700 / Revenue credit 700;
- M2 2025-12-31: Bank debit 1,000 / Capital credit 1,000;
- M3 2026-01-10: Expense debit 300 / Bank credit 300;
- M4 2026-01-20, bank journal: Bank debit 500 / Revenue credit 500;
- M5 2026-01-25: draft, Expense debit 200 / Bank credit 200;
- M6 2026-01-26: cancelled, Expense debit 400 / Bank credit 400;
- M7 2026-02-01: Expense debit 50 / Bank credit 50;
- M8 2026-03-10: Expense debit 1,000 with distribution A1 60% / A2 40%; Bank credit 1,000;
- M9 2026-03-12: Expense debit 200 with the composite key "A1,B1" at 100%; Bank credit 200.

Observed (Initial D/C, period D/C, End D/C):

- **R1, January, posted:**
  - Bank 1,000/0, 500/300, 1,200/0.
  - Revenue 0/0, 0/500, 0/500.
  - Expense 0/0, 300/0, 300/0.
  - Undistributed Profits/Losses (999999) 0/700, 0/0, 0/700: the prior-year revenue is carried forward.
  - Totals 1,700/1,700, 800/800, 2,200/2,200.
- **R2, January, with drafts:** Bank period credit 500 and End 1,000/0; Expense End 500. The cancelled M6 never counts.
- **R3, February** (the period starts after the fiscal-year start):
  - Revenue Initial 0/500 and Expense Initial 300/0: income and expense open from the fiscal-year start.
  - Earnings row Initial 0/700: prior years only.
  - Bank Initial 1,200/0.
- **R4, March, analytic A1:** only Expense, period debit 1,200 = M8 at 1,000 (full item, not 600) + M9 at 200. The report does not balance.
- **R5, March, analytic B1:** only Expense, 200 (M9's composite key, counted once).
- **R6, March, no analytic filter:** Expense period debit 1,200, each item once. Bank End 0/50: a negative balance is shown on the credit side.
- **R7, January, bank journal only:** Bank Initial 0/0 (M2 is in Misc), period 500/0; Revenue 0/500. The journal filter also applies to the opening balance.
- **R8, January, hierarchy on:**
  - Five nested groups above Bank appear at levels 1 to 5, with Bank at level 6. Current Assets (101000) sits under group "101" at level 4.
  - Group "4" holds codes 400000 and 443000 by prefix. Its period and End show both sides, 300/500, because subtotals sum the children's netted values.
  - "(No Group)" (level 1) holds Capital and 999999.
  - The Total row equals R1's totals.

The Stage 07 base fixture expects Bank 1,000 / +500 / -300 = 1,200 (posted) and 1,000 (with drafts). R1 and R2 show the native report computing the same values with the same options. Stage 07 still keeps hand-calculated expectations, so no test only compares our code with the native code.

### 4.9 As built in Stage 07 (2026-11-15): wizard, option contract and fixtures

- **Manifest:** `azk_dynamic_trial_balance` 18.0.1.1.0 now depends on `account_reports` (V-05), which in this build brings `accountant` and `account_accountant` (V-08).
- **Wizard** `azk_dynamic_trial_balance.wizard` (`models/trial_balance_wizard.py`): the fields of section 4.2, with the PDF's help texts word for word.
  - Show Amount Currency adds one sentence on its dates (D-11).
  - `posted_entries` is a read-only field that defaults to true, and a constraint refuses false. The calculation never reads it.
  - Onchanges keep the hierarchy options consistent, and constraints refuse invalid combinations (D-43, D-46).
- **Prefix tags** `azk_dynamic_trial_balance.account.prefix` (`models/account_prefix.py`): a transient model shown as tags. Each prefix is trimmed and checked when created (D-44).
- **One option contract** (`models/report_options.py`):
  - `normalize_options(env, raw)` turns the wizard (or, later, client-sent options) into plain values.
  - It refuses unknown keys, wrong types, a company that is not authorized or not active (`check_company`, D-45), a journal or analytic account unusable in the company (searched as the user with the model's `_check_company_domain`), invalid combinations and non-code prefixes.
  - The wizard's constraints call the same functions.
- **Security:** read, write, create and unlink for `account.group_account_readonly` (the native Trial Balance's group) on both transient models, plus global record rules `create_uid = user`, so wizards and prefixes are private.
- **UI:** a form dialog with a notice that the outputs are not connected yet, and the menu Accounting > Reporting > Audit Reports > Dynamic Trial Balance.
- **Entry points:** the Preview, PDF and XLSX buttons validate the options with `_get_report_options()`, then raise a clear "not available yet" message (D-47). Stage 09 connects them.
- **Calculation rules:** [calculation_contract.md](calculation_contract.md). The engine is Stage 08.
- **Tests and fixtures:** `tests/common.py` builds the fixtures of [test_plan.md](test_plan.md) 4.1 from real entries and holds the hand-calculated constants. `native_trial_balance()` runs the standard report with one active company and matched options. The test classes:
  - `TestTrialBalanceWizard`;
  - `TestBaseFixture`;
  - `TestCrossYearConventions`;
  - one class per advanced fixture: `TestZeroActivityFixture`, `TestCurrencyFixture`, `TestAnalyticFixture`, `TestMultiCompanyFixture`, `TestRestrictedAccessFixture`, `TestHierarchyFixture`.

### 4.10 As built in Stage 08 (2026-11-15): the calculation engine

- **Service:** `azk_dynamic_trial_balance.engine` (`models/trial_balance_engine.py`), an AbstractModel with one entry point, `compute(options)`. It returns the normalized result described in [calculation_contract.md](calculation_contract.md) 15:
  - filters, leaf rows, hierarchy rows and display lines;
  - base-currency totals and per-currency totals;
  - warnings and metadata.
- **Validation on every call:** `compute` checks the accounting read-only group (D-50), then validates the raw options again with `normalize_options`. So the wizard, and the Stage 09 handler that will pass client-sent options, both go through the same checks.
- **Arithmetic as the user:** three grouped `_read_group` queries on `account.move.line` (movement, opening, carry-forward) plus one account search, all as the calling user. `_read_group` checks access rights and applies every record rule. There is no `sudo()` and no SQL, and the number of queries does not depend on the number of accounts.
- **Company context:** the engine runs `with_company(report company)`, because account codes (`code_store`) and account groups are company-dependent.
- **Hierarchy:** built in Python from `account.account.group_id` and `account.group.parent_id`, so it can apply the level limit, list "(No Group)" and keep currencies apart. The display order, levels and group sums match the standard hierarchy on TB-H.
- **Wizard:** `TrialBalanceWizard._compute_report()` returns the engine result for the wizard's options, with the caller's access. The Preview, PDF and XLSX buttons still only validate (D-47); Stage 09 builds the handler and report record that render the result (D-53).
- **Not used from `account_reports` yet:** the report framework itself. The engine reuses the ORM and the same model helpers as the standard report; parity is tested, not inherited (architecture 4.1).

### 4.11 As built in Stage 09 (2026-11-15): Preview, PDF and XLSX

- **One path for every output (K-01).** The report record `dynamic_trial_balance_report` (`data/trial_balance_report.xml`) names our custom handler `azk_dynamic_trial_balance.report.handler` (`models/trial_balance_report_handler.py`). The standard report UI, `export_to_pdf` and `export_to_xlsx` all get their lines from `account.report._get_lines(options)`. That method calls the handler's `_dynamic_lines_generator`, which calls `engine.compute()` once per request. No output computes an amount itself, so the outputs cannot drift apart.
- **Options on every request.** The handler's `_custom_options_initializer` runs on the first opening, after every filter change and for each export:
  - it rebuilds the engine options from `options['azk_tb']` plus the standard `date` and `all_entries` (Draft Entries) keys;
  - it validates them with `normalize_options`, so options sent back by the browser (preview reloads, the `/account_reports` download route) pass the same checks as the wizard;
  - it sets `options['companies']` to the report company only (D-45), which the download route also uses for the active companies;
  - it lays out the columns and stores the display texts (`azk_tb_display`) and the preview's journal and analytic choices (`azk_tb_choices`).
- **Columns.** Three column groups (Initial Balance, the period, End Balance), each with Debit, Credit and Balance, plus an Amount Currency group (the period movement) when asked. The standard PDF header ignores the groups' width, so our header template replaces it (D-55).
- **Lines.** Group, account, total and per-currency total lines from the engine rows. Line ids are hierarchical (`parent|child`), so the standard fold, unfold and search work. Every line is sent with its `unfolded` flag: folding hides children in the browser, and unfolding never needs a server call.
- **Preview.** The wizard's Preview returns the standard `account_report` client action with the wizard's options (`ignore_session`, so stale session options are not reused). Our OWL component `TrialBalanceFilters` (`static/src/components/trial_balance/`) extends the standard filter bar through `_get_custom_display_config()['components']`. It adds a company badge, a "Trial Balance" menu (hierarchy, only parents and level, Skip Zero Balance, Show Amount Currency), account prefixes, journal and analytic account. Each change calls the standard `applyFilters`, which reloads the report from the server, so the engine recalculates. The standard date filter, Draft Entries, Unfold All and search bar stay. Messages: the engine's warnings, an empty result, and filters that make the report unbalanced. Group rows are bold, as in the PDF (`trial_balance.scss`).
- **PDF.** The standard `export_to_pdf` (wkhtmltopdf; landscape because the report has more than five columns; the table header repeats on every page). Our three templates (`data/pdf_export_templates.xml`), plugged in through the `pdf_export` display hook:
  - the company block shows the report company, not the company switcher's (D-55);
  - the filters block lists every option as "label: value";
  - the table header shows the column groups with their widths.
- **XLSX.** For this report only, `account.report._inject_report_into_xlsx_sheet` writes our own sheet (`models/account_report.py`, D-56) from the same `_get_lines` output:
  - the company, the period and every option above the table;
  - merged group headers, then Code, Account, the column names and Currency;
  - codes and names written as text, amounts with `write_number` and a number format;
  - the currency code in its own column, frozen header rows and fixed widths.
  The standard exporter creates the workbook with `strings_to_formulas` off, and its Filters sheet lists the same summary.
- **Exports follow the preview (D-57).** In print mode, `_custom_line_postprocessor` applies the preview's search rule (a match, its ancestors and its descendants, the rule of the standard `isLineRelatedTo`), and the standard `_filter_out_folded_children` drops the children of folded groups.
- **Freshness and isolation (D-58).** No result is stored. Every request recalculates as the requesting user, so a result cannot be reused by someone else. The download route needs a session (`auth='user'`) and checks the options again. A wizard is readable only by its creator, and each button reads it first.
- **Demo data (D-59).** `models/demo_data.py` and `demo/trial_balance_demo.xml` create a dedicated Egyptian company in EGP when the module is installed with demo data, after every module is loaded (`_register_hook`). Odoo runs functions of demo files at install only, and the function checks the company's XML id, so upgrades never duplicate it. A database that got the module earlier receives it by calling the function once from an Odoo shell.
- **Display options kept from the standard report.** The rounding unit changes the amounts shown in the preview and the PDF, and the PDF prints it; the XLSX keeps exact numbers (D-61). Analytic fields show only with Odoo's Analytic Accounting setting (D-62).
- **Testing the PDF (D-63).** Unit tests replace wkhtmltopdf with a stub that keeps the HTML document `export_to_pdf` hands over, and compare it with the printed lines; real PDFs and the download route are checked on the running server.
- **Not covered, for Stage 10:** custom fiscal years (`account.fiscal.year`) and branch companies (D-60).

### 4.12 Changed in Stage 10 (2026-11-15)

- **Branch-only users** (D-66, review finding RF-06): `TrialBalanceEngine._chart_accounts()` searches the report company's chart as the user with an explicit order (by id). The default order of `account.account` joins each account to its first company among the user's own companies, so a user with a branch but not its root company lost the Current Year Earnings row, the accounts without items and every prefix match. Still no `sudo()` and no SQL.
- **Fiscal years and branches** are now tested (TB-F, TB-B; D-60): the engine and the standard report follow `compute_fiscalyear_dates` of the report company, and a report covers exactly one company (D-16).
- **Demo data** (D-59, review finding RF-07): the demo company is created with the `chart_template_load` flag, so a call from an Odoo shell never installs the Egyptian localization.

## 5. Exercise 1: Odoo Partner Monitor

### 5.1 What the source looks like (verified in Odoo 18's own module; live site checked in Stage 04)

The public `/partners` pages come from the `website_crm_partner_assign` module. Its pinned 18.0 controller (`WebsiteCrmPartnerAssign.partners`) and templates show:

- **Routes:** `/partners`, `/partners/page/<n>`, `/partners/country/<slug>`, `/partners/grade/<slug>` and their combinations. Pages hold 40 partners (`_references_per_page = 40`).
- **Geo-IP default:** without a country, the page infers the visitor's country from geo-IP. The `country_all=True` parameter shows all countries.
- **Country counts:** every listing page renders the country list with a partner count per country.
- **Empty-country fallback:** when the selected country has no partners, the controller drops the country and lists all partners, with the alert "There are no matching partners found for the selected country. Displaying results across all countries instead." This is the PDF's "No Matching Partners" case (P-22).
- **Partner links:** `/partners/<name-id>?grade_id=<g>&country_id=<c>`. `country_id` is present only while a country is selected, and it need not be the first parameter.
- **Ordering and cards:** partners are sorted by grade sequence, then reference count. The card shows "<N> references". The detail page lists references by avatar and name, without links.
- **Checked live in Stage 04 (2026-11-08):** odoo.com behaves like this module, with differences recorded in [live_site_notes.md](live_site_notes.md):
  - 20 partners per page instead of 40;
  - the cards also show the retention rate, average and largest project size, and the reference count;
  - references link to `/customers/<slug>-<id>`.
  The empty-country fallback and `country_id` in country-scoped links are as described above. robots.txt disallows requesting URLs with `country_id`, `grade_id` or `page` query keys (D-25).

### 5.2 Data model

Required by the PDF (names and types kept exactly; P-09 to P-12):

- `azk_odoo_partner_monitor.country`: `name`, `active` (default True), `total_partner_count`, `to_reprocess_partners`. It stays a standalone model, not `res.country`.
- `azk_odoo_partner_monitor.partner`: `name`, `partner_url`, `current_status` (selection `ready`/`silver`/`gold`), `country_id`, `first_seen_on`, `retention_rate`, `total_references_count`, `largest_project_size`, `average_project_size`, `to_reprocess_references`, `status_history_ids`, `reference_ids`.
- `azk_odoo_partner_monitor.status.history`: `partner_id`, `previous_status`, `new_status`, `change_date`, `change_type` (`promoted`/`demoted`/`initial`).
- `azk_odoo_partner_monitor.reference`: `partner_id`, `name`, `is_active`, `added_on`, `removed_on`.

Supporting fields and models (each justified by a requirement):

- **Stable identities** (P-13, P-22, K-03):
  - `country.source_key`: the site's country id from the `/country/<slug-id>` link; `UNIQUE`.
  - `partner.source_id`: the numeric id from the partner slug; `UNIQUE`.
  - `reference.source_key`: a link or id if the live site provides one, otherwise the normalized name (Stage 04 tests the fallback).
  - Names alone are never identities.
- **Partner activity** (P-23 analogue for partners): `partner.active` (archived when absent from a validated complete snapshot of its country) and `partner.last_seen_on`.
- **Unknown versus zero:** `retention_rate_known`, `largest_project_size_known`, `average_project_size_known`. Odoo reads a NULL numeric column as 0, so a flag is needed. Plus `details_synced_at` and `details_fingerprint` (a hash of the normalized detail data).
- **Dashboard support:** `project_size_bucket` (stored selection computed from the average and its known flag) and `first_seen_year` (stored integer).
- **Validation bookkeeping** (P-18, P-20, K-04):
  - on countries: the expected count (`total_partner_count`, PDF), `snapshot_partner_count` (actual, from the last complete snapshot), `validation_state`, `reprocess_attempts`, `next_reprocess_at`;
  - on partners: `active_reference_count`, plus the same retry fields.
- **`azk_odoo_partner_monitor.sync.run`** (inherits `mail.thread`): one record per discovery or manual run, with trigger, state (`running`/`done`/`partial`/`failed`), times, unit counters and `notified_at`. Its chatter carries the failure note (P-07).
- **`azk_odoo_partner_monitor.work.item`:** the durable unit of work. Kind is `country_list`, `country_partners` or `partner_details`, with a target country or partner, state (`pending`/`done`/`failed`/`cancelled`), `attempt_count`, `next_attempt_at`, `last_error` and `run_id`. A partial unique index on (kind, target) WHERE state = 'pending' de-duplicates enqueueing. It is created in `init()` with parameterized SQL, because `_sql_constraints` cannot express a partial index. (Corrected in Stage 03: `odoo.tools.sql.create_index` builds a non-unique index, and `create_unique_index` takes no WHERE clause, so neither helper can build it. The index is also listed in `_sql_constraints` with an empty definition, so a violation shows its message, the pattern `account_edi_proxy_client` uses in this release.)
- **`azk_odoo_partner_monitor.sync.error`:** one row per failed unit (run, work item, URL, error class, message, short trace) for P-06. The Python logger records the same errors.
- **Uniqueness:**
  - `_sql_constraints` (the 18.0 mechanism, verified in `odoo/models.py`) on `country.source_key` and `partner.source_id`;
  - partial unique indexes for one active reference per (partner, source_key), one `initial` history row per partner, and one pending work item per (kind, target).

### 5.3 Status and history rules (P-13, P-14)

- **Ordering:** ready < silver < gold.
- **First observation:** create the partner with `first_seen_on` = run date. Also create one `initial` history row with an empty previous status and new status = the observed status. `first_seen_on` is never rewritten afterwards.
- **Transitions:** a status change creates exactly one row, `promoted` if the new status ranks higher and `demoted` if lower. An unchanged status creates none. The comparison and the write happen under a row lock in the unit's transaction, so a replayed unit cannot record the same transition twice.
- **Unknown site labels:** an unknown status is a parse error for that partner. The unit fails, the error is logged and retried, and nothing is written. It is never coerced to Ready, and no fourth change type is invented (D-09).
- **Disappearance and return:** absence from a validated complete snapshot archives the partner (`active = False`) without a history row. If the partner reappears, it is reactivated; `first_seen_on` is kept, and a status difference is recorded as a promotion or demotion.

### 5.4 References (P-15, P-16, P-20)

- **New:** a new reference creates a record with `is_active = True` and `added_on` = run date.
- **Removed:** a reference missing from a complete, validated reference snapshot of that partner gets `is_active = False` and `removed_on` = run date.
- **Reactivation (D-10):** each record is one listing interval. A reference that comes back starts a new record, so earlier intervals keep their dates. At most one active record exists per (partner, source_key).
- **Validation:** after a detail fetch, if the active reference count differs from the expected count (`total_references_count`, as shown by the site), set `to_reprocess_references`. A changed retention rate, largest or average project size, or reference count on the listing also schedules a detail refresh. The refresh does not loop on itself: retries are bounded and the flag is cleared only by a complete, matching fetch.

### 5.5 Snapshot completeness (K-04)

Removal or archiving needs a complete, validated snapshot of exactly that scope:

- **Countries** (P-23): deactivated only from a country list that parsed fully, is not empty, and is not an error or blocked page.
- **Partners of a country:** archived only when every listing page of that country was fetched and parsed, every kept record passed the country-scope check, and the number of distinct partners equals the count shown for that country on the same fetch.
- **References of a partner:** removed only when the reference list was fully retrieved and its size equals the expected count.
- **What does not count as a snapshot:** a timeout, an HTTP error, a login, rate-limit or unexpected page, or a parse failure is a failed unit, never an empty result. A count mismatch sets the reprocess flag and blocks removals, but additions and updates from the fetched data still apply.
- **The PDF's empty-country rule** (P-22): for a country-scoped fetch, the `country_id` query value of every partner link is checked against the expected country before the URL is canonicalized. Links without it, or with another country, are ignored and logged. The fallback alert also marks the page as unscoped. A country absent from a validated country list is deactivated, and its partners are archived unless they are seen in another country.

### 5.6 Sync workflow, commit boundaries and overlap (P-04, P-05, P-08, P-19, P-21)

Verified Odoo 18.0 cron behavior (`odoo/addons/base/models/ir_cron.py`):

- **Commits:** `_run_job` runs the server action up to 10 times (`MAX_BATCH_PER_CRON_JOB`). Each run gets a fresh `ir.cron.progress` record, commits before the callback, and commits again after it returns. On an exception, `_callback` rolls back and re-raises.
- **Progress:** a callback reports `_notify_progress(done=..., remaining=...)`. Remaining work makes the job run again at once, and after 10 rounds it is rescheduled as soon as possible.
- **One job, one worker:** `_acquire_one_job` locks the job row with `FOR NO KEY UPDATE SKIP LOCKED`, so the same cron never runs twice at once.
- **Timeouts:** three consecutive time-outs without progress count as a failure. Deactivation needs 5 failures over at least 7 days.
- **Time limits:** a cron thread's real-time limit is `limit_time_real_cron`, or `limit_time_real` (default 120 s) when that is -1.

Design:

- **Daily discovery cron:**
  - creates a run;
  - finalizes a still-open older run as `partial`, cancelling its pending units because the new run rediscovers everything;
  - enqueues a `country_list` unit and triggers the worker. It does no scraping itself.
- **Worker cron**, every 10 minutes and triggered on demand. Each callback:
  - claims due pending units with `SELECT ... FOR UPDATE SKIP LOCKED` (parameterized SQL; 18.0 has no ORM lock helper), up to a unit limit and a time budget (provisional: 20 units, 60 s);
  - processes each unit in its own savepoint;
  - records failures outside the savepoint;
  - reports progress and returns.
  The scheduler's commit after the callback is the durability boundary: a crash loses at most the current batch, and those units are replayed. The claim is a row lock held until that commit, so it dies with a crashed transaction and needs no lease or stale-claim cleanup. The units are:
  - `country_list`: upsert countries and their expected counts. A validated list deactivates missing countries and enqueues a `country_partners` unit per active country.
  - `country_partners`: fetch all listing pages of one country, upsert partners and status history, check completeness, then archive or flag. Enqueue `partner_details` for new partners, for partners whose card changed, and for stale details (default 7 days).
  - `partner_details`: metrics, references and validation.
  When no unit of a run remains, the worker finalizes it.
- **Country validation cron** (default every 6 hours): flagged countries whose retry is due get a `country_partners` unit (de-duplicated), then the worker is triggered. The country page itself shows a fresh count for that country, so a genuine change in partner numbers does not leave a permanent false mismatch.
- **Reference validation cron** (default every 6 hours): the same pattern for flagged partners, with `partner_details` units.
- **Retries:** HTTP calls get at most 3 attempts with backoff and honor `Retry-After`. Units get at most 5 attempts with exponential backoff (15 minutes doubling, capped at 24 hours). After the last attempt a unit stays `failed` and visible. A manager can reset it with "Retry".
- **Isolation:** one unit's failure rolls back only its savepoint, so the cursor stays usable and other units continue (P-05). Errors are never swallowed: each one is logged, stored and counted.
- **Manual actions:** "Sync now" and "Retry" only enqueue and call `_trigger()`. The UI never runs a crawl.
- **Change-aware pulling** (P-08.3):
  - listing pages are fetched daily, since they are the discovery source;
  - detail pages only for new partners, changed cards, flags or stale details;
  - conditional HTTP headers (`ETag`/`Last-Modified`) only if Stage 04 shows the site sends them, and a 304 is accepted only when a known-good snapshot exists;
  - an unchanged detail fingerprint skips writes.
  A country count alone cannot reveal status, reference or metric changes, which is why stale details are revalidated periodically.

### 5.7 Failure notification (P-07)

- **Recipient:** the configured user is stored as `ir.config_parameter` `azk_odoo_partner_monitor.notify_user_id` and set in Settings, which is restricted to system administrators.
- **Default (changed in Stage 03, D-19):** the administrator, `base.user_admin`, set by the `noupdate` data record `config_notify_user`. The planned post-init hook cannot know who installed the module: in this release, `load_modules` builds its environment with `SUPERUSER_ID` and passes it to every hook (`odoo/modules/loading.py`), whether the install starts from the Apps screen or the command line. If the setting points to a missing, archived or non-internal user, the run falls back to the administrator and logs a warning.
- **When a run ends `partial` or `failed`**, the worker posts one internal note on the run's chatter (`message_post` with `partner_ids` = the recipient's partner). It lists the counts, the failed scopes and the scheduled recovery.
- **Delivery:** Odoo delivers the note according to the recipient's own `notification_type` (`res.users`, mail module): Inbox for "Handle in Odoo", an email for "Handle by Emails". In a fresh database of this build, `admin` has `email`; only `__system__` has `inbox` (checked in `azk_ee24_clean`). So the note is always visible in the run's chatter. The demo instructions tell the reviewer to switch the recipient to "Handle in Odoo" to see it in the Discuss Inbox. We do not override user preferences (D-08).
- **Once per run:** `notified_at` prevents a second note. Tests use Odoo's mail mocks and assert the `mail.notification` rows, so no real email is sent.

### 5.8 Dashboard (P-24 to P-27)

Options checked in this build:

- **`board`:** embeds standard views with `View` from `@web/views/view`, but each action keeps its own domain. It has no shared filters.
- **`spreadsheet_dashboard`:** its global filters support only `date`, `relation` and `text`, so there is no selection filter for the status. Its content is JSON data, not an XML definition. Top or Bottom 5 after filters would need spreadsheet formulas.
- **Plain menus with four graph actions:** this would not share filters, and the prompt rules it out.

So the module adds a small OWL client action, the module's main menu entry:

- **Filters:** a shared bar with multi-selects for Status (Gold, Silver, Ready), Country and Year First Seen; empty means all.
- **One server method,** `azk_odoo_partner_monitor.dashboard.get_dashboard_data(filters)`:
  - validates the filter values;
  - ranks countries with ORM `_read_group` as the calling user;
  - returns the Top 5 and Bottom 5 country ids, the counts, the last-sync status and empty-state flags.
- **Four embedded standard graph views**, defined in XML on the partner model:
  - stacked bars by country and status, in descending order for Top 5 and ascending for Bottom 5;
  - stacked bars by country and project-size bucket for each cohort.
  Each receives the shared domain plus its cohort's country ids, and is remounted when a filter changes. Clicking a bar opens the matching partners.
- **Ranking (D-06):**
  - counts active partners in active countries after all three filters;
  - only countries with at least one matching partner take part;
  - ties are broken by count, then country name, then id;
  - with fewer than 5 countries a chart shows all of them; with fewer than 10 the two cohorts may overlap, and the dashboard says so;
  - an empty result shows a clear message.
- **Buckets (D-05):** [0, 5) "Below 5", [5, 11) "5 to below 11", [11, 25) "11 to below 25", [25, inf) "25 and above", and "Unknown" when the average is not known. 25 belongs only to "25 and above".
- **Dependencies:** only Community web components (`View`, the graph view, OWL), so the dashboard works on both editions.

### 5.9 Views, menus and permissions (P-17, M-01)

The original views specification was not supplied. The proposed views are an assumption (A-16):

- **Countries:** list, form and search (filters Active, Archived and Needs reprocess; group by validation state).
- **Partners:**
  - list, form with Status History and References tabs, and search (Gold, Silver, Ready, Active, Archived, Needs reference reprocess; group by Country, Status, Year First Seen, Project size bucket);
  - pivot (country by status, count and average project size) and graph.
- **Status History:** list, search (promoted, demoted, initial; group by type, partner, month), pivot (month by change type) and graph.
- **References:** list, search (active or removed; group by partner, month added) and pivot.
- **Sync (managers):** runs with chatter, work items with Retry, and errors.
- **Menus:** Partner Monitor > Dashboard (the root action) / Partners / Countries / Status History / References / Sync / Configuration.
- **Groups:** "Partner Monitor / Reader" (read business data, dashboard and runs) and "Partner Monitor / Manager" (implies Reader; work items, errors, Sync now, Retry). `base.user_admin` is a manager by default.

### 5.10 As built in Stage 03 (2026-11-08)

- **Models:** the four PDF models with their exact field names and types, plus `sync.run`, `work.item` and `sync.error`. The project-size bucket, the year field and the validation bookkeeping fields are added with the features that use them (Stages 05 and 06).
- **Ingestion API in the models**, so the invariants live next to the data. The Stage 05 worker calls:
  - `country._record_observation(values)`: upsert by `source_key`; seeing a country again reactivates it.
  - `partner._record_observation(values, observed_on)`: upsert by `source_id`; sets `first_seen_on` once; records one `initial` row, then one row per real transition; ignores an observation older than `last_seen_on` (D-21); refuses unknown status labels and any field outside the observed set.
  - `partner._sync_references(items, observed_on, complete)`: the D-10 interval policy; only a complete snapshot closes references.
- **Database rules:** unique website ids; a demo namespace (D-20); ordered seen dates; non-negative metrics; an unknown metric carries no value (D-22); history rows consistent with their type; one `initial` row per partner, one active reference per key and one pending work item per target (partial unique indexes); work-item targets that match their kind.
- **Model rules:** canonical `partner_url` (`services/urls.py`); `source_id`, `source_key` and `first_seen_on` cannot be rewritten; history rows cannot be edited; the change type must follow the ranking.
- **Access:** read-only ACLs for every group. Readers read the business data and runs. Managers also read work items and errors, and run four actions: Sync Now, Retry, and Mark for Re-scrape on countries and partners. Each action checks the manager group, then writes with a narrow `sudo()` (D-18). There are no record rules: the data is public and shared by all companies, and company rules would hide it (A-21).
- **Notification:** `sync.run._notify_failure()` posts the internal note described in 5.7. The Stage 05 worker calls it when a run ends `partial` or `failed`.
- **Views:** list, form and search views for every model, Settings and menus. The root menu opens Partners until Stage 06 adds the dashboard.

### 5.11 As built in Stage 04 (2026-11-08, PARTIAL)

```text
  [page source]  fetch(url) -> (final URL, HTML); raises on any failure
        |        (the requests-based module is deferred; tests use saved pages)
        v
  services/reader.py     refuses URLs that robots.txt disallows; follows the
        |                site's pager; stops at the first page that is not
        |                this country's listing
        v
  services/parsers.py    country list | listing page | partner page
        |                -> typed results with counts, scope, paging,
        |                   rejected and invalid links, problems
        v
  models/ingest.py       -> country._record_observation,
                            partner._record_observation,
                            partner._sync_references (Stage 03)
```

- **Raw link to stored partner:** the listing parser checks each card's raw link with `urls.check_country_scope` BEFORE `urls.canonical_partner_url` drops the query string. A link with a missing, empty, repeated or different `country_id` is rejected and reported, never recorded.
- **Page scope** (`parse_listing_page`):
  - "country": the page lists partners of this country;
  - "empty_country": the page shows the site's no-partners notice;
  - "unscoped": anything else, for example another country's page, or a global list without the notice.
- **Completeness and removals:**
  - A country snapshot is complete only under D-28. A complete snapshot archives the partners the country no longer lists. An incomplete one archives nothing and sets `to_reprocess_partners`.
  - The no-partners notice is a valid empty snapshot only when a complete country list confirms it (D-27).
  - A partner's reference list is complete only when its size equals the expected count: the page's "References - N", or, when the page shows no count, the listing's known count. An incomplete list adds new references, closes none, and sets `to_reprocess_references`.
  - Only a complete country list deactivates missing countries. Demo records are never touched.
- **Failures:** a ParseError, a refused URL or any exception from the page source propagates. Nothing is ingested for that scope. A failure is never treated as an empty result.
- **Missing in Stage 04, built in Stage 10:** the requests-based page download and a live run through it (section 5.14).

### 5.12 As built in Stage 05 (2026-11-10)

The sync engine follows section 5.6. Details, commit story and evidence are in [resilience.md](resilience.md).

```text
  ir.cron (data/ir_cron.xml), all calling azk_odoo_partner_monitor.worker
    Daily Discovery (1 day)   --> sync.run + country_list unit ----+
    Country Validation (6 h)  --> country_partners units (flagged) -+--> work.item queue
    Reference Validation (6 h)--> partner_details units (flagged,  -+    (one pending unit
                                  stale)                                 per kind and target)
    Sync Worker (10 min, or woken by _trigger)                           |
      _cron_process_queue: one bounded batch per scheduler call <--------+
        _claim_next   FOR NO KEY UPDATE SKIP LOCKED, one unit at a time
        _run_unit     savepoint -> services/reader.py (fetch from
                      _get_page_source) -> models/ingest.py
        failures      sync.error row + try count + log line, after the rollback
        _finalize     done / partial / failed, one note per run
      the scheduler commits after each call: the durability point
```

- **Engine:** `models/worker.py` (AbstractModel `azk_odoo_partner_monitor.worker`). The units are the three work-item kinds of section 5.2. The country unit queues the pages of partners never read; the validation jobs queue flagged and stale targets.
- **Page source:** `worker._get_page_source()` is the integration point of the deferred page-download module. It returns None today, so the worker attempts nothing and marks the runs as waiting (D-33).
- **Changes from section 5.6:**
  - claims are taken one at a time, so units queued earlier in the same batch can run in it;
  - a REPEATABLE READ serialization failure on a claim ends the batch (D-35);
  - recorded dates are the date the page is read (D-30);
  - details are refreshed by the policy of D-31; a changed card sets the flag and the reference-validation job reads the page;
  - validation re-scrapes have their own bounded budget (D-32);
  - an empty-country notice is confirmed by reading the country list in the same unit (D-36);
  - there is no `details_fingerprint`: writes are already idempotent and the site offers no conditional requests, so the listing card hash (`listing_fingerprint`) is the change detector.
- **New fields:** validation bookkeeping on countries and partners (expected, found, previous, outcome, retry count and time, "Retries Exhausted"), `active_reference_count`, `details_synced_at`, `listing_fingerprint`; `finished_at` and `result_summary` on work items; `waiting_reason` on runs.

### 5.13 As built in Stage 06 (2026-11-10): the dashboard

From the menu to the numbers:

```text
  Menu "Partner Monitor" (menu_root, group Reader)
    -> first child "Dashboard" (menu_dashboard, group Reader, D-39)
    -> ir.actions.client dashboard_action, tag "azk_odoo_partner_monitor.dashboard"
    -> OWL component PartnerMonitorDashboard (static/src/dashboard/dashboard.js),
       registered under that tag in the "actions" registry
         keeps only the filter VALUES: statuses, country ids, years, data source
         |  orm.call("azk_odoo_partner_monitor.dashboard", "get_dashboard_data", [filters])
         v
       models/dashboard.py, get_dashboard_data (runs as the calling user)
         1. ensure_reader: AccessError for anyone without the Reader group
         2. drop unknown or invalid filter values; never accept a domain
         3. build ONE domain: active partners, active countries, one data source,
            then status, country and year
         4. _read_group(domain, [country], [count], order="__count desc, country_id")
            -> Top 5; the same with "asc" -> Bottom 5 (D-06, D-42)
         5. per cohort: rows by status, the five bucket counts, and the chart
            domain = the shared domain + [("country_id", "in", cohort)]
         6. the real sync state (last run, last success, waiting; the queue for managers)
         |  JSON: rankings, domains, counts, graph view ids, sync state
         v
       four embedded <View type="graph"> components (@web/views/view), one per
       chart, each with its server-built domain and its XML view:
         partner_view_graph_dashboard_top / _bottom (country x status, sorted)
         partner_view_graph_dashboard_top_size / _bottom_size (bucket x country)
         -> the graph view itself calls web_read_group on the same domain as the user
```

- **Why a client action** (A-17): a window action shows one view with its own search. Here four views must share one set of filters, and two of them must be limited to countries ranked after those filters. So the shared state and the ranking need a small component and one server method.
- **Why the totals cannot drift:** the summaries and the charts read the same records through the same domain, with grouped ORM queries. A test calls `web_read_group` exactly as the graph view does and compares it with a plain search (`test_chart_totals_equal_the_filtered_records`).
- **Access:** the menu and the server method check the Reader group. The graph views read partners through the ORM as the user. The client sends filter values only. A tampered domain sent straight to `web_read_group` is still limited by the access rules, and those let a reader read exactly what the dashboard shows.
- **Escaping:** the template prints every value with `t-esc`; the chart labels are drawn on a canvas.
- **Charts:** a graph view `js_class` in Odoo's lazy view bundle (`static/src/dashboard_graph/`) hides the toolbar and gives Gold, Silver and Ready fixed colors (D-42). A bar click opens the matching partners. The tables link each country to its partners with the same filters, and "Show them" opens all matching partners.
- **Data sources:** website data or demo data, one at a time, with a banner for demo data (D-37). The demo data has 13 countries (12 active), 50 partners and 57 history rows (`demo/partner_monitor_demo.xml`).
- **Other views:** pivots for partners, status history and references; graphs for partners and status history; groupings by project size and year. Partner metrics are not offered as sums or averages (D-40).

### 5.14 As built in Stage 10 (2026-11-15): the page download

```text
  worker._cron_process_queue()        one bounded batch per scheduler call
     |  _get_page_source(): None while Settings > Pause Website Downloads is on (D-64),
     |  else a new services/http_client.PartnersHttpClient
     v
  PartnersHttpClient(url)  = the fetch(url) of services/reader.py
     |  urls.fetch_allowed(url)      www.odoo.com over HTTPS, robots.txt rules (D-25)
     |  RequestPacer.wait()          >= 3 s between requests of the process
     |  session.get(stream, no auto redirects, timeouts 5 s / 20 s)
     |  status: 200 page | 3xx -> check the target, follow (max 5)
     |          429, 503 + Retry-After -> pause the process, RateLimitedError
     |          502/503/504 -> retry (max 3 tries, 2 s then 4 s) | other -> HttpStatusError
     |  body: <= 3 MB, <= 30 s, HTML only, not empty, not a login or rate-limit page
     v
  (final URL, text)  or a FetchError subclass: never an empty page
```

- **One client per batch, one pacer per process:** the session (and its connections) lives for one batch; the spacing and the pause after a rate limit are kept by `DEFAULT_PACER`, which every client of the process shares, because the scheduler may run up to 10 batches in a row.
- **A rate limit stops the batch:** after the unit that met it (one counted try, with the unit's own backoff), the worker starts no other unit, marks the open runs as waiting with the time the pause ends, and reports no progress, so the scheduler does not loop (`_process_queue`, `_cron_process_queue`).
- **Work queued by a unit** (the country units of the country list, the partner pages of a listing) is due at the batch's own moment (`_enqueue(now=...)`), so it can run in the same batch and counts as remaining (review finding RF-03).
- **Headers:** a generic User-Agent naming the module, English pages, and gzip only (review finding RF-02).
- **Tests:** `tests/test_http_client.py` replaces the session with a fake that answers prepared `requests.Response` objects and the clock with a fake; Odoo's test framework blocks real requests anyway. The bounded live check is `scripts/pm_live_check.py` (disposable database, at most 8 requests, rolled back).

## 6. Version and edition notes

- The PDF's option names come from older Enterprise releases: "Include Unposted Entries" is "Draft Entries" in 18.0. The wizard keeps the PDF's labels and maps them to the 18.0 semantics, which are the same.
- In 18.0 an account can be shared by several companies (`account.account.company_ids`), and its code is company-dependent. Prefix matching therefore always runs in the report company's context.
- `account_reports` is an Enterprise module (OEEL-1). `azk_dynamic_trial_balance` must declare it, and it only installs where the Enterprise addons are present. Its own license (A-06, Q-06) is a decision for the user or team lead.
- The cron progress API (`_notify_progress`, `ir.cron.progress`) and the 10-callback loop are specific to this release line; they were read in the pinned 18.0 source. If the required major version changes (Q-04), section 5.6 must be checked again.
- The live partners site is a newer, customized deployment. Section 5.1 is our working model until Stage 04 verifies it.
