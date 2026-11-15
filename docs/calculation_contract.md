# Trial Balance calculation contract

_Written in Stage 07 (2026-11-15), before the calculation engine; Stage 08 (2026-11-15) implemented it in `models/trial_balance_engine.py` (section 15). It fixes the arithmetic that the Preview, PDF and XLSX will all use: each output renders one engine result and computes no numbers of its own (K-01). Requirement IDs (T-xx) refer to [requirements_matrix.md](requirements_matrix.md), decisions (A-xx, D-xx, Q-xx) to [assumptions.md](assumptions.md), and fixtures (TB-xx) to [test_plan.md](test_plan.md) 4.1 and `addons/azk_dynamic_trial_balance/tests/common.py`._

## 1. Sources

Read in the pinned sources of the matched pair (edition `enterprise-20241208`). Enterprise code is cited by name only.

- **Journal items** (`account.move.line`): `company_id`, `journal_id`, `account_id`, `date`, `parent_state` (the entry's state, stored), `display_type`, `debit`, `credit`, `balance`, `currency_id`, `amount_currency`, `analytic_distribution`. A database check forbids an item with both a debit and a credit.
- **Accounts** (`account.account`): `code` (computed per company from `code_store`, searched through `_search_code`), `account_type`, `internal_group`, `include_initial_balance` (false only for income and expense), `group_id`, `deprecated`. Codes use `ACCOUNT_CODE_REGEX` (letters, digits and dots).
- **Account groups** (`account.group`): `code_prefix_start`, `code_prefix_end`, `parent_id` (maintained by Odoo from the prefixes), `company_id` (the root company).
- **Fiscal year:** `res.company.compute_fiscalyear_dates`. `account_accountant` overrides it to honour custom fiscal years (`account.fiscal.year`). It is installed with `account_reports`, which depends on `accountant` in this build.
- **Standard Trial Balance:** `account_reports.trial_balance_report`, handler `account.trial.balance.report.handler`, built on `account.general.ledger.report.handler`. That handler provides `_get_options_initial_balance`, `_get_query_sums` and `_get_options_unaffected_earnings`. The report framework provides `account.report._get_options_domain`, `_get_options_all_entries_domain`, `_get_report_query` (which applies record rules through `_apply_ir_rules`) and `_create_hierarchy`.
- **Analytic filter:** `analytic.mixin._condition_to_sql`. With the operator `in`, it tests whether the distribution's account ids overlap the selected ids (composite keys are split on commas). The standard report adds the same overlap test to its query.

## 2. Terms, on the base fixture

- **Journal entry** (`account.move`): one balanced business event with a date, a journal and a state: draft, posted or cancelled. Example: "2026-01-10, Misc: Expense debit 300 / Bank credit 300".
- **Journal item** (`account.move.line`): one line of an entry, on one account. It has either a debit or a credit, never both. Its `balance` is debit minus credit, and its `parent_state` copies the entry's state. The example entry has two items: Expense +300 and Bank -300.
- **Debit and credit:** the two sides of every item. A debit increases an asset or an expense; a credit increases a liability, equity or income. The debits of an entry always equal its credits.
- **Balance:** debit minus credit. A positive balance is a debit balance (Bank +1,200), a negative one a credit balance (Revenue -500).

## 3. Inputs

The engine receives only the normalized options returned by `models/report_options.py` `normalize_options(env, raw)`. That function runs for the wizard and again for any option set sent back by a client. Keys:

- `date_from` (F) and `date_to` (T): ISO dates, F <= T, both inclusive.
- `company_id` (K): a company the user may access and that is active in the company switcher (D-45).
- `include_unposted`: drafts join posted items. Posted items are always in, so "posted entries" is not an option.
- `hierarchy_subtotals`, `hierarchy_only_parents`, `account_level` (1 to 5, or none): see section 10 for the valid combinations.
- `account_prefixes`: a list of literal code prefixes; empty means all accounts.
- `journal_id`, `analytic_account_id`: one id or none (D-02).
- `skip_zero_balance`, `show_amount_currency`.

**Valid combinations** (enforced in `check_combination`, the wizard constraints and `normalize_options`):

- No hierarchy, Hierarchy and Subtotals, or Hierarchy and Subtotals with Hierarchy Only Parents and a level from 1 to 5.
- Only Parents needs Hierarchy and Subtotals; the level is required with Only Parents and refused without it (D-46).
- Show Amount Currency is refused with Only Parents, which shows no account lines (D-43).
- Include Unposted Entries, Skip Zero Balance and the filters combine with everything.

**Refused:** unknown keys, values of the wrong type (for example the string "false" for a boolean), a journal or analytic account the user cannot read or that the company cannot use, and prefixes outside the code alphabet.

## 4. Scope of journal items

The same scope applies to the opening balance, the carry-forward and the movement. A journal item i is in scope when:

1. `i.company_id = K`. Branches are separate companies; a branch is reported by selecting it (D-16).
2. `i.parent_state = 'posted'`; with Include Unposted Entries, `i.parent_state != 'cancel'`. This is the standard domain of `_get_options_all_entries_domain`. Cancelled items never count.
3. `i.display_type` is not `line_section` or `line_note`.
4. If a journal J is selected: `i.journal_id = J`.
5. If an analytic account A is selected: `('analytic_distribution', 'in', [A])`, which is whole-item selection (section 9).
6. The user may read i: the query goes through the ORM as the user, so access rights and every record rule apply, the multi-company rule included (TB-R).

The account prefixes are not a condition on items. They select which account rows are shown (section 7), so that the carry-forward can include every income and expense account, as in the standard report (D-15).

## 5. Opening, movement and ending

Notation: S is the start of the fiscal year that contains F, that is `K.compute_fiscalyear_dates(F)['date_from']`. All amounts are in K's currency.

- **Movement** of an account: the items in scope dated F <= date <= T.
  - Movement debit (MD) is the sum of their debits and movement credit (MC) the sum of their credits, both gross.
  - Movement balance (MB) = MD - MC.
- **Opening balance** (OB) of an account:
  - balance-sheet accounts (`include_initial_balance` true): the balance of the items in scope dated before F;
  - income and expense accounts: the balance of the items in scope dated S <= date < F. This is zero when F = S.
- **Carry-forward** (CF): the balance of the items in scope on all income and expense accounts dated before S.
  - CF is added to the opening balance of K's Current Year Earnings account (`account_type = 'equity_unaffected'`).
  - It is a presentation of the report, as in the standard report. No journal entry is created and no retained-earnings posting is invented.
  - If K has no such account, the engine returns a warning and shows no invented row.
- **Ending balance** (EB) = OB + MB.

**Why this is the standard behavior:** `_get_options_initial_balance` treats two cases, and both give the rule above.

- **F is the fiscal-year start:**
  - the opening column covers the previous fiscal year, with `include_current_year_in_unaff_earnings`;
  - balance-sheet accounts sum everything up to F - 1;
  - income and expense accounts are left out of the account sums;
  - `_get_options_unaffected_earnings` sums income and expense up to F - 1, which is before S.
- **F is later in the year:**
  - the opening column covers S to F - 1;
  - balance-sheet accounts again sum everything up to F - 1 (`from_beginning` with the fiscal-year condition);
  - income and expense accounts sum S to F - 1;
  - the unaffected earnings sum income and expense up to S - 1.

The tests compare the standard report with our hand calculation in both cases: TB-X for January and February 2026.

**Reconciliation:**

- Per row: EB = OB + MD - MC.
- The carry-forward only moves amounts between rows: the earlier results of the income and expense rows appear on the earnings row instead. So the sum of all opening balances equals the balance of all items in scope dated before F.
- For a complete company ledger (no prefix, journal or analytic filter), that sum is 0, because every entry is balanced.
- The only adjustment between the ledger and the report is the carry-forward. Closing entries that a company really posts are ordinary journal items and count like any other.

**Fiscal years:** the engine calls the same `compute_fiscalyear_dates` as the standard report, so a custom fiscal year (`account.fiscal.year`) moves S for both. Only the calendar year was compared (Stage 07).

## 6. Columns, display and rounding

Each row has nine numbers:

- **Initial Balance:** Debit = max(OB, 0), Credit = max(-OB, 0), Balance = OB.
- **Movement during the period:** Debit = MD, Credit = MC, Balance = MB.
- **End Balance:** Debit = max(EB, 0), Credit = max(-EB, 0), Balance = EB.

**Net versus gross:**

- Initial and End are positions, so they show only the net side, as the standard report does: it nets them per line in `_dynamic_lines_generator`.
- Movement is activity, so both sides are shown in full.
- The Balance columns are an addition the assessment requires (T-15); the standard report has only Debit and Credit.

**Display grain:** one row per account; with Show Amount Currency, one row per account and transaction currency (section 8).

**Rounding:** amounts are summed from the stored item amounts, which are already rounded, and each result is rounded once with K's currency (`currency.round`). Zero tests use `currency.is_zero`.

## 7. Rows, prefixes and zero filtering

**Account prefixes:**

- An account row is included when its code in K (from `code_store` of K's root company, as `code` computes it) starts with at least one prefix. The prefixes are combined with OR.
- An empty list means all accounts.
- Matching is literal and case-sensitive, like Odoo's own search by code (`account.account._search_display_name` uses `=like`).
- Prefixes are trimmed, at most 64 characters, use only letters, digits and dots, and are de-duplicated (D-44).
  - So "%", "_" and "\" are refused before they reach a query.
  - The engine still escapes them before any `=like` search, as a second safeguard.
- The earnings row is shown only if its own code matches. When shown, its opening includes the whole carry-forward (D-15).

**Rows listed when Skip Zero Balance is off (D-12):**

- every account of K that matches the prefixes and is not deprecated, even without journal items;
- plus every account that has amounts, deprecated or not.

The standard report lists only accounts with amounts. This difference is intended: the PDF describes Skip Zero Balance as hiding such accounts, so without it they are listed.

**Skip Zero Balance on (D-48):**

- A row is hidden only when all of these are zero (`currency.is_zero`): the opening balance, the movement debit, the movement credit and the ending balance. With currency rows, the row's amount-currency movement must also be zero, tested with its own currency.
- "Activity" means a gross debit or credit. An account whose movement debit equals its movement credit stays visible: TB-Z's Current Assets moved 250 / 250, with 0 opening and 0 ending.
- Items of 0.00 are not activity.
- With a hierarchy, a group row is shown when at least one row under it is shown.

## 8. Show Amount Currency

- **Rows:** one per (account, `currency_id` of the item).
  - Items in K's currency have `currency_id` = K's currency and `amount_currency` = balance, so they form the (account, EGP) row.
  - The base-currency columns follow sections 5 and 6, per row.
  - The carry-forward goes to the (earnings account, K's currency) row.
- **The Amount Currency column:**
  - It is the sum of `amount_currency` of the row's movement items (F to T, inclusive), shown with the currency's symbol and rounded with that currency (D-11).
  - Opening and ending amounts in foreign currency are not shown.
- **Group and total rows** leave the column empty. A separate section lists one total per currency, so different currencies are never added together. TB-C: USD 100 - 40 = USD 60.00 and EUR 70 - 20 = EUR 50.00, never 110.
- **No revaluation:** company-currency amounts are used as booked. Nothing is revalued at today's rate.
- **Reconciliation across groupings:**
  - For each account, its currency rows add up to the account row without the option, for the opening balance, movement debit, movement credit, movement balance and ending balance. TB-C: the USD and EUR rows give 3,000 + 2,750 = 5,750, the movement balance of the account.
  - The netted Initial and End debit and credit can differ, because netting happens per row (D-49). TB-C's opening is 1,000 debit on the USD row and 1,650 credit on the EUR row. For the account as a whole it is 650 credit. The signed balance is -650 either way.
  - Report totals therefore show 1,650 / 1,650 with currency rows and 650 / 650 without them.
- **With Only Parents:** refused (D-43).

## 9. Analytic accounts: whole-item selection

Decision (A-15, D-07; confirmation asked in Q-03):

- With an analytic account A selected, a journal item is in scope when A appears in any key of its distribution. Composite keys such as "A1,B1" are split on commas.
- The item counts once, at its full amount. Its distribution percentages do not scale it.
- Items without a distribution are left out. So an analytic report need not balance: in TB-A the Bank items carry no distribution.
- Without a selection, each item counts once at its full amount. Items are never multiplied by the number of keys or plans.
- The rule also applies to the opening balance and the carry-forward.

This is the behavior of the standard report and of Odoo's journal-item search, compared in Stage 07 (TB-A).

| TB-A, March 2026, Expense movement debit | A1 | A2 | B1 | No filter |
|---|---|---|---|---|
| Whole item (selected) | 1,000 + 200 = 1,200 | 1,000 | 200 | 1,200 |
| Proportional (rejected) | 600 + 200 = 800 | 400 | 200 | 1,200 |

**Why proportional allocation was not chosen:**

- The assessment asks for Odoo's behavior on the other Trial Balance options.
- The standard report selects whole items.
- A proportional report would show amounts that match no journal item, and the same item would appear in several reports with different amounts.

It stays a documented alternative.

## 10. Hierarchy

- **Structure:**
  - Groups are the `account.group` records of K's root company.
  - An account's group is `account.account.group_id` in K's context: the most specific group whose prefix range contains the code. Ancestors follow `parent_id`.
  - The level of a group is its number of ancestors plus 1, so a top group is level 1. TB-H: "1" is level 1 and "10140" is level 5.
- **Hierarchy and Subtotals:**
  - Rows appear in code order. Each group row comes before its child groups and accounts, as in the standard report.
  - Accounts without a group are shown under "(No Group)", a level-1 row after the real groups.
- **Group row amounts:**
  - A group row adds up its descendant leaf rows, each displayed column separately, so it can show both sides. TB-H: group "4" ends with 120 debit and 500 credit, because Cash Discount Loss ends at 120 debit and Product Sales at 500 credit.
  - The group's Balance columns are the sums of the leaf balances.
  - This matches the standard hierarchy (`_create_hierarchy` sums the netted account lines; Stage 07 compared it on TB-H).
- **Totals:** each leaf counts once in each of its ancestors. The total row sums leaf rows only, never group rows, so a hierarchy cannot double-count.
- **Hierarchy Only Parents with Account Level Up To N:**
  - Shows the group rows of level N or less and "(No Group)", and no account rows.
  - Each shown group still includes all its descendants: deeper groups and their accounts. Ungrouped accounts stay in "(No Group)".
  - Nothing is dropped: the level-1 rows plus "(No Group)" add up to the total for every N (TB-H).
  - TB-H with N = 1 shows "1", "4" and "(No Group)"; N = 3 adds "10" and "101".

## 11. Totals

- The total row is the sum of the leaf rows (account rows, or account and currency rows) for each of the nine numbers. It is never a sum of group rows.
- Without prefix, journal or analytic filters, every entry is balanced, so:
  - the total opening balance is 0;
  - the movement debit equals the movement credit;
  - the total ending balance is 0;
  - so the Debit and Credit totals are equal in each of the three column groups. TB-BASE: 1,000 / 1,000, 800 / 800 and 1,500 / 1,500.
- A filtered report need not balance (TB-A, filter A1: 1,200 debit and 0 credit).

## 12. Access

- Every read runs as the calling user through the ORM (grouped `_read_group` queries on `account.move.line`), so access rights and record rules apply. TB-R shows the standard report doing the same.
- No `sudo()` in the calculation.
- If raw SQL is ever needed:
  - its values are parameters;
  - its scope comes from the ORM: `_where_calc` with the domain above, then `_apply_ir_rules`, as the standard report does.
- The options are validated again on every path (section 3).
- Wizard records and prefix tags are private to their creator: there is a record rule on `create_uid`.

## 13. Intended differences from the standard Trial Balance

- Balance columns in all three column groups (T-15).
- Exactly one company, which must be active. Branches are not added together (D-16).
- One journal and one analytic account, as the PDF specifies (D-02); the standard filters take several.
- Literal account-code prefixes. The standard report has a text search on the account name and code instead.
- Skip Zero Balance, and the listing of accounts without amounts when it is off (D-12).
- Rows per transaction currency, with the Amount Currency column (D-11, D-49).
- Hierarchy Only Parents with a level limit (D-13, D-46).
- The hierarchy is an option, off by default. The standard report turns it on by default when account groups exist.

## 14. Fixtures, expected results and native comparisons

The fixtures are real, balanced entries in fresh EGP companies with the generic chart and a calendar fiscal year. They are posted, left in draft or cancelled through Odoo's own methods (`action_post`, then `button_cancel` for the cancelled entry).

- The expected numbers are written by hand in `tests/common.py`, never computed by a report.
- The tests check them for internal consistency (balance = debit - credit, ending = opening + movement, totals = the sum of rows).
- Stage 07 compares them with the standard Trial Balance, run with the same company, dates and options.
- Stage 08 compares our engine with the same constants.

**The Bank account of TB-BASE, by hand (January 2026):**

```text
Opening      2025-12-31 posted debit                        1,000
Movement     2026-01-20 posted debit       +500
             2026-01-10 posted credit      -300
             movement balance                                +200
Ending       1,000 + 500 - 300                              1,200   (debit)

Including drafts:
Movement     credits 300 + 200 (2026-01-25 draft) = 500
             movement balance 500 - 500                         0
Ending       1,000 + 500 - 500                              1,000   (debit)

Never counted: the cancelled credit of 400 (2026-01-26) and the
February credit of 50 (after Date To).
```

**Compared with the standard Trial Balance in Stage 07** (parity is claimed only for these cases):

| Fixture | Period and options | Compared |
|---|---|---|
| TB-BASE | January, posted; January with drafts | All lines and totals |
| TB-BASE | January, Bank journal only; Misc journal only | All lines and totals, including the journal's effect on the opening |
| TB-X | January (fiscal-year start); February; February with drafts | All lines and totals, including the carry-forward |
| TB-Z | January | All lines: the zero-net account is listed |
| TB-C | January | Company-currency lines and totals only; the currency rows are ours |
| TB-A | March: no filter, A1, A2, B1 | All lines and totals (whole-item selection) |
| TB-M | January: company 1, company 2 | All lines and totals per company; a reader of company 1 is refused company 2 |
| TB-R | January, as a restricted reader and as the accountant | All lines and totals: the record rule is applied |
| TB-H | January with the hierarchy | Account lines, group lines, "(No Group)", group depths and totals |

**Not compared** (there is no standard equivalent, or it was not checked):

- currency rows and the Amount Currency column;
- Skip Zero Balance and the listing of accounts without amounts;
- Hierarchy Only Parents and the level limit;
- the prefix filter;
- custom fiscal years;
- branches;
- period comparisons.

Stage 08 tests them against the hand-calculated constants.

## 15. As implemented in Stage 08

The engine is `azk_dynamic_trial_balance.engine` (an AbstractModel service, `models/trial_balance_engine.py`). Its one entry point, `compute(options)`:

1. requires the accounting read-only group (`account.group_account_readonly`), as the standard Trial Balance's menu does (D-50);
2. validates the raw options with `normalize_options` (section 3);
3. switches to the report company (`with_company`), so account codes and groups are read in it;
4. runs the calculation as the calling user.

**Steps, in `_compute`:**

- `_accounts_in_scope`: the company's accounts whose code matches a prefix (`like_prefix_pattern`), or all of them.
- `_scope_domain`: the item scope of section 4.
- `_add_movement`, `_add_opening` and `_add_carry_forward`: three grouped `_read_group` queries on `account.move.line`, for the movement, the opening and the carry-forward. They are grouped by account, or by account and currency.
- `_add_accounts_without_items`: without Skip Zero Balance, the accounts with no items.
- `_leaf_rows` and `_amounts`: the nine numbers per row.
- `_is_zero_row`: the Skip Zero Balance test.
- `_hierarchy`: group rows, levels, display order and Only Parents.
- `_sum_amounts` and `_currency_totals`: the totals.

The number of queries does not depend on the number of accounts (measured in `test_query_count_does_not_grow_with_accounts`).

**Result** (plain values, ready to be passed as JSON):

- `filters`: the normalized options, plus `company_name`, `journal_name` and `analytic_account_name`.
- `leaf_rows`: one row per shown account, or per account and transaction currency, in code order. Each row has:
  - `id`, `type` ("account"), `level`, `parent_id`;
  - `account_id`, `account_code`, `account_name`, `group_id`;
  - `currency_id`, `currency_name`, `currency_symbol` and `amount_currency` (only with Show Amount Currency, otherwise None);
  - the nine numbers: `initial_debit`, `initial_credit`, `initial_balance`, `debit`, `credit`, `balance`, `ending_debit`, `ending_credit`, `ending_balance`.
- `hierarchy_rows`: the group rows in display order. Each has `type` "group", `group_id` (None for "(No Group)"), `group_code`, `group_name`, `level`, `parent_id` and the nine numbers, with no amount currency.
- `lines`: the rows to display, in order.
  - Without a hierarchy, the leaf rows.
  - With Hierarchy and Subtotals, each group row followed by its child groups and accounts in code order, with "(No Group)" last.
  - With Hierarchy Only Parents, the group rows of the chosen level or higher only.
- `totals`: the nine numbers summed over `leaf_rows`, never over group rows.
- `currency_totals`: with Show Amount Currency, one entry per transaction currency. Each has the amount-currency total and the base-currency movement debit, credit and balance of its rows.
- `warnings`: each with a `code` and a `message`.
  - `no_earnings_account`: earlier years' result cannot be shown.
  - `no_account_groups`: a hierarchy was asked for, but no account of the report has a group.
- `metadata`:
  - the company and its currency, the dates and the fiscal-year start;
  - `earnings_account_id` and `carry_forward`: None when the earnings row is outside the prefixes;
  - `balanced` (Debit equals Credit in each column group), and `leaf_count`.

**Details that the rules above left open, decided in Stage 08:**

- With Show Amount Currency, an account without items is listed (Skip Zero Balance off) in the account's own currency, or in the company currency, with an amount currency of 0 (D-51).
- A leaf row's level is its group's level plus 1, or 2 under "(No Group)". Without a hierarchy, every row is level 1.
- The carry-forward is computed only when the earnings account is in the report. Without an earnings account, a non-zero carry-forward produces the warning `no_earnings_account` (D-52).

## 16. How the outputs show the result (Stage 09)

The outputs add no arithmetic. Each request (a preview reload, a PDF, an XLSX) validates the options again and calls `compute()` once; the handler turns the result into report lines.

- **Columns:** the nine numbers in three groups, Initial Balance, the period and End Balance, each with Debit, Credit and Balance; with Show Amount Currency a tenth column, "Movement" under "Amount Currency", holds the row's `amount_currency`.
- **Rows:** `lines` in order (group rows, then accounts), then one Total row (`totals`), then with Show Amount Currency one "Total in XXX" row per entry of `currency_totals`. A per-currency total shows the base-currency movement debit, credit and balance and the amount-currency total of its rows; its initial and ending cells stay empty, because they are only meaningful per account.
- **Display:** amounts are rounded by the engine to the company currency (section 6). The preview and the PDF format them with the company currency, and the amount currency with the row's currency. The XLSX writes the same rounded numbers as numbers with the format `#,##0.00;-#,##0.00;0.00`, and the currency code in its own column.
- **Search and folding:** a display filter only. Hidden rows keep their place in every total, as in the preview.
