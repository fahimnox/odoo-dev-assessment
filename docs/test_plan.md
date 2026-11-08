# Test and acceptance plan (Stage 02)

_Written 2026-11-05 as the plan. Stage 03 (2026-11-08) implemented TP-PM-01 to TP-PM-05 (section 3.1), and Stage 04 (partial) the offline parser and ingestion tests (section 3.2); the other tests do not exist yet. The design they verify is in [architecture.md](architecture.md), the requirements in [requirements_matrix.md](requirements_matrix.md)._

## 1. Rules for every result

- Every check is reported as PASS, FAIL, BLOCKED or NOT RUN. A run that collects zero tests is a failure: `scripts/dev.sh test` already fails on Odoo's "of 0 tests" line.
- Tests run in a fresh disposable database of the target edition (`azk_ee24_test`, edition `enterprise-20241208`) through `scripts/dev.sh test`.
- Normal tests never touch the live website; they use saved HTML fixtures labeled live-derived or synthetic.
- Tests send no real email; they use Odoo's mail mocks.
- Dates are frozen with `freezegun` (1.2.1 in the image) where the result depends on today.
- **Trial Balance:** expected values are written by hand from the documented contract, never produced by the code under test. Comparisons with the native Trial Balance are extra evidence, not a replacement.
- **Browser:** neither the image nor the agent has Chrome or Chromium. Browser tours and screenshots are NOT RUN unless a browser becomes available. The user's manual browser checks are recorded separately, as the user's results.
- **Where results go:**
  - `docs/test_results.md` from Stage 08;
  - `docs/resilience.md` in Stage 05;
  - `docs/acceptance_results.md` in Stage 11;
  - full command logs privately in `<kit-root>/runtime/logs/`.

## 2. Test levels

| Level | What | How | Stages |
|---|---|---|---|
| L1 | Pure functions: HTML parsers, URL rules, bucket and ranking helpers, amount netting | Odoo test classes without database writes, on saved fixtures | 04, 06, 08 |
| L2 | ORM behavior: models, constraints, ingestion, history, engine numbers, access rules | `TransactionCase` (rolled back), several users and companies | 03-09 |
| L3 | Commit boundaries and crashes: the worker cron in a real process, killed and restarted | A script against a disposable database; SQL state before and after; it cannot run inside `TransactionCase`, which forbids commits | 05 |
| L4 | HTTP and RPC: dashboard method, report RPC, download route, access denial | `HttpCase` with real sessions (no browser) | 06, 09 |
| L5 | Rendered outputs: PDF text and layout, XLSX cells | Native exporters through a running server (wkhtmltopdf needs the HTTP server for CSS). XLSX cells are read in tests with `openpyxl` (3.1.2 in the image). PDF text is checked with the host's `pdftotext` (not in the image), and the PDF is inspected visually | 09 |
| L6 | Manual and browser checks | Steps for the user; screenshots only if a browser is available | 06, 09, 11 |

## 3. Exercise 1: Partner Monitor

| ID | Stage | Check | Expected result | Requirements |
|---|---|---|---|---|
| TP-PM-01 | 03 | Install and upgrade; required models, field names and types match the PDF (field introspection) | The four models exist with exactly the PDF's fields and types; the module upgrades without warnings | P-01, P-09 to P-12 |
| TP-PM-02 | 03 | Uniqueness | A duplicate `country.source_key`, a duplicate `partner.source_id`, a second active reference with the same key, a second `initial` history row, and a second pending work item for the same target are all rejected by the database | K-03 |
| TP-PM-03 | 03 | First observation | One partner and exactly one `initial` history row (empty previous status). `first_seen_on` = the frozen run date; it is unchanged after a later ingestion | P-13, P-14 |
| TP-PM-04 | 03 | Transitions | ready -> gold is `promoted`, gold -> silver is `demoted`; an unchanged status adds no row; replaying the same unit adds no row; an unknown label fails the unit without writes | P-14, D-09 |
| TP-PM-05 | 03 | Permissions | A reader can read business data but cannot write it, create history or see work items; a manager can schedule Sync now and Retry; a user without the groups cannot read anything | K-02, A-22 |
| TP-PM-06 | 04 | Parsers on fixtures | The country list yields ids, names and counts; listing pages yield partner ids, names, statuses, reference counts and pagination; detail pages yield metrics and references; missing values are flagged unknown, never 0 | P-02, P-09, P-10 |
| TP-PM-07 | 04 | Broken input | Truncated or unexpected markup, a login page, a rate-limit page, an HTTP error and a timeout (mocked) are each a failure with a clear error, never an empty result | P-05, P-06, K-04 |
| TP-PM-08 | 04 | Country-scope rule | A link with the right `country_id` is kept, also as the second parameter; a missing or different `country_id` is ignored and logged; a page with the fallback alert is unscoped; the check happens before canonicalization | P-22 |
| TP-PM-09 | 05 | Idempotent ingestion | The same snapshot ingested twice creates no duplicate partner, reference or history row | P-08.2, K-03 |
| TP-PM-10 | 05 | Failure isolation | In one batch, partner A fails and partner B succeeds; A's error is stored with its context; the cursor stays usable; B's data is written | P-05, P-06 |
| TP-PM-11 | 05 | Country validation | A count mismatch sets `to_reprocess_partners` and blocks archiving; the validation cron re-enqueues once (de-duplicated); a matching retry clears the flag; a permanent mismatch stops after the retry limit and stays visible | P-18, P-19 |
| TP-PM-12 | 05 | Reference validation | An expected count different from the active count sets `to_reprocess_references`; a changed metric schedules one detail refresh, not a loop; a complete matching fetch clears the flag | P-20, P-21 |
| TP-PM-13 | 05 | Partial snapshots | A truncated country fetch archives no partner; a partial reference list removes no reference; an incomplete country list deactivates no country; a valid empty country is handled as empty | P-16, P-23, K-04 |
| TP-PM-14 | 05 | Overlap | Two cursors claim units concurrently and never get the same unit (`SKIP LOCKED`); duplicate scheduling creates one pending unit | P-08.1 |
| TP-PM-15 | 05 | Crash and restart (L3) | Kill the worker process mid-run, then restart: committed batches stay done, the interrupted batch is replayed once, nothing is duplicated; SQL counts before and after are recorded | P-08.1, P-08.2 |
| TP-PM-16 | 05 | Failure notification | A partial run posts exactly one note on its chatter with the configured user as recipient (a `mail.notification` row for that partner); a second finalization posts nothing; no email leaves the system | P-07 |
| TP-PM-17 | 05 | Change-aware pulling | An unchanged listing card triggers no detail fetch; a changed card or stale details do; a 304 is used only with a known-good snapshot | P-08.3 |
| TP-PM-18 | 06 | Dashboard data | Filter propagation to all four charts; ranking after filters; ties; fewer than 5 and fewer than 10 countries; empty state; bucket boundaries 4.99, 5, 10.99, 11, 24.99, 25 and unknown; chart totals equal the filtered record counts | P-24 to P-27, D-05, D-06 |
| TP-PM-19 | 06 | Dashboard access (L4) | A reader gets data; a user without the reader group is refused by the server, whatever domain the client sends | P-24, K-02 |
| TP-PM-20 | 06 | UI (L6) | Menu opens the dashboard first; four charts render; each filter changes all four; a bar opens the matching partners | P-24, P-25 |
| TP-PM-21 | 04, 06 | Bounded live smoke | One or two country pages fetched live; evidence saved and labeled live with its date; BLOCKED if there is no connectivity | P-02 |

### 3.1 Implemented in Stage 03 (2026-11-08)

The checks TP-PM-01 to TP-PM-05 are automated in `addons/azk_odoo_partner_monitor/tests/` (`TransactionCase`, tagged `post_install`). Results are in [STATE.md](STATE.md) and the Stage 03 handoff.

- **TP-PM-01** (models and fields): `test_models.py`, `TestDataModel.test_required_models_and_field_types_match_the_pdf`. Install and upgrade are checked with the commands in section 6.
- **TP-PM-02** (uniqueness, identities, relations): `TestDataModel`:
  - `test_country_identity_is_the_website_id`, `test_partner_identity_is_the_website_id`;
  - `test_demo_and_website_ids_never_collide`, `test_relations_are_enforced`;
  - `test_work_item_target_matches_its_kind`, `test_one_pending_work_item_per_target`;
  - `test_partner_url_must_be_canonical`, `test_canonical_url_rule`;
  - `test_unknown_metric_is_not_zero`, `test_observation_cannot_set_protected_fields`, `test_demo_records_are_labeled`;
  - plus `test_references.py`, `TestReferences.test_reference_rules_in_database` and `test_status_history.py`, `TestStatusHistory.test_history_rules_in_database_and_model`.
- **TP-PM-03 and TP-PM-04** (first observation, transitions): `test_status_history.py`, `TestStatusHistory`:
  - `test_first_observation_creates_partner_and_initial_row`;
  - `test_silver_gold_gold_records_initial_then_one_promotion`, the sequence Silver -> Gold -> Gold;
  - `test_ranking_types_promotions_and_demotions`, `test_replayed_observation_adds_nothing`, `test_older_observation_is_ignored`;
  - `test_unknown_status_writes_nothing`, `test_first_seen_on_cannot_be_rewritten`;
  - `test_archived_partner_reappears_with_its_history`, `test_country_move_updates_the_same_partner`;
  - `test_history_rows_cannot_be_changed`, `test_users_cannot_record_observations`, `test_demo_history_is_consistent`.
- **Reference intervals** (D-10, the model part of TP-PM-12 and TP-PM-13): `test_references.py`, `TestReferences` (7 tests).
- **TP-PM-05** (permissions): `test_security.py`, `TestSecurity` (12 tests): reader reads and is refused writes, work items, errors and manager actions; manager actions; manager refused direct edits; no access without a group; data shared across companies; Settings for system administrators only; menus and views per role.
- **Notification destination** (the Stage 03 part of TP-PM-16): `test_notification.py`, `TestFailureNotification` (7 tests). The worker's call at the end of a run, and its tests, come in Stage 05.

### 3.2 Implemented in Stage 04 (2026-11-08, PARTIAL)

38 offline tests use only the seven live-derived fixtures in `tests/fixtures/` (provenance in their README). Pages reach the parsers through `services/reader.py` with `FixtureSite`, a fixture-backed `fetch` function in `tests/common.py`. No test touches the network.

- **TP-PM-06** (parsers): `test_parsers.py`, `TestParsers` (12 tests):
  - the country list (170 countries, counts add up to 4517) and a variant with one country removed (incomplete);
  - Andorra (complete page); Egypt page 1 (page 1 of 11, the next-page link) and page 11 (last page, missing retention, known zeros);
  - partner pages (RoayaTec: 3 of 135 references, identified by link id; DEVONEERS: no references);
  - wrong page types and empty input raise ParseError.
- **TP-PM-08** (country scope):
  - `test_urls.py`, `TestUrlRules` (8 tests): `country_id` in any position; missing, empty, repeated and wrong values rejected; the check needs the raw link; canonical URLs; reference keys; robots.txt rules;
  - `TestParsers`: Anguilla's 3 global links rejected for "missing country_id"; the Andorra page read for Egypt is "unscoped".
- **Ingestion** (`test_ingest.py`, `TestIngest`, 18 tests), including the cases the user named:
  - Andorra ingested twice (and again on a later date) creates no duplicate partner or history row;
  - RoayaTec's 3-of-135 list keeps a seeded reference active and flags the partner;
  - Anguilla is empty only when a complete country list confirms it; without that, or with an incomplete list, or with the country listed with partners, everything is kept and the country is flagged;
  - Egypt: the reader follows the pager and a missing page 2 fails the read; the last page alone, or pages 1 and 11 with a gap, are incomplete and archive nothing.
  It also covers: the raw-URL-to-stored-partner walkthrough; a complete snapshot archiving an unlisted partner; a timeout failing the read with no change; an unknown status card skipped; a page of another country changing nothing; complete and incomplete country lists; a valid empty reference list; and a page of another partner refused.
- **Partly covered:**
  - TP-PM-07: page-type errors and source failures at the reader (a timeout, a missing page) are covered. A login page, a rate-limit page, HTTP errors and truncated markup are not: the synthetic fixtures for them and the page-download module were deferred.
  - TP-PM-13: incomplete snapshots are covered at the ingestion level; the worker path comes in Stage 05.
- **TP-PM-21** (live): a manual sample with curl (9 requests) and a manual parser check on the saved full pages ([live_site_notes.md](live_site_notes.md)). A live run through the module is NOT RUN: the page-download module is deferred.

## 4. Exercise 2: Dynamic Trial Balance

### 4.1 Fixtures and hand-calculated expectations

All fixtures use one company with currency EGP and a calendar fiscal year. They are built from real, balanced journal entries posted, left in draft or cancelled through Odoo's own methods.

**TB-BASE** (Stage 07's base fixture). Period 2026-01-01 to 2026-01-31.

- Posted 2025-12-31: Bank debit 1,000 / Equity credit 1,000.
- Posted 2026-01-10: Expense debit 300 / Bank credit 300.
- Posted 2026-01-20: Bank debit 500 / Revenue credit 500.
- Draft 2026-01-25: Expense debit 200 / Bank credit 200.
- Cancelled 2026-01-26: Expense debit 400 / Bank credit 400.
- Posted 2026-02-01: Expense debit 50 / Bank credit 50.

Expected, posted only. Each group reads Debit / Credit / Balance:

- Bank: Initial 1,000 / 0 / 1,000; Movement 500 / 300 / 200; End 1,200 / 0 / 1,200.
- Expense: Initial 0 / 0 / 0; Movement 300 / 0 / 300; End 300 / 0 / 300.
- Revenue: Initial 0 / 0 / 0; Movement 0 / 500 / -500; End 0 / 500 / -500.
- Equity: Initial 0 / 1,000 / -1,000; Movement 0 / 0 / 0; End 0 / 1,000 / -1,000.
- Total: Initial 1,000 / 1,000 / 0; Movement 800 / 800 / 0; End 1,500 / 1,500 / 0.

Expected with Include Unposted Entries:

- Bank: Movement 500 / 500 / 0; End 1,000 / 0 / 1,000.
- Expense: Movement 500 / 0 / 500; End 500 / 0 / 500.
- Revenue and Equity: unchanged.
- Total: Movement 1,000 / 1,000 / 0; End 1,500 / 1,500 / 0.
- The cancelled and February entries never count.

**TB-X** (cross-year): TB-BASE plus a posted entry on 2025-06-30, Current Assets debit 700 / Revenue credit 700.

- January 2026, posted:
  - Revenue Initial 0 / 0 / 0, because income opens at the fiscal-year start.
  - Current Year Earnings Initial 0 / 700 / -700, from the 2025 result.
  - Current Assets Initial 700 / 0 / 700.
  - Total Initial 1,700 / 1,700 / 0; End 2,200 / 2,200 / 0.
- February 2026, posted:
  - Bank Initial 1,200 / 0 / 1,200.
  - Expense Initial 300 / 0 / 300 and Revenue Initial 0 / 500 / -500 (January of the current fiscal year).
  - Current Year Earnings Initial 0 / 700 / -700 (prior years only).
  - Movement: Expense 50 / 0 / 50 and Bank 0 / 50 / -50.

**TB-C** (currencies). January 2026, one account X with lines in two transaction currencies and balanced counterparts on another account. Rates: USD = 50 EGP, EUR = 55 EGP.

- Lines on X:
  - USD +100 (debit 5,000) and -40 (credit 2,000);
  - EUR +70 (debit 3,850) and -20 (credit 1,100).
- With Show Amount Currency:
  - Row (X, USD): Movement 5,000 / 2,000 / 3,000, Amount Currency USD 60.00.
  - Row (X, EUR): Movement 3,850 / 1,100 / 2,750, Amount Currency EUR 50.00.
  - Group and Total rows: no amount currency.
  - Per-currency totals: USD 60.00 and EUR 50.00, never 110.
- Without the option: X Movement 8,850 / 3,100 / 5,750. Signed balances and gross movements reconcile between the two modes.

**TB-A** (analytic). March 2026.

- Lines:
  - Expense debit 1,000 with distribution A1 60% / A2 40%, against Bank credit 1,000 without distribution;
  - Expense debit 200 with the composite key "A1,B1" at 100%, against Bank credit 200.
- Results under the selected policy (whole-item inclusion):
  - filter A1: Expense Movement 1,200 / 0 / 1,200; Bank absent;
  - filter A2: Expense 1,000;
  - filter B1: Expense 200;
  - no filter: Expense 1,200 and Bank credit 1,200, each item once.
- Under the rejected proportional alternative, A1 would give 800 (600 + 200). That number is documented, not implemented.

**TB-H** (hierarchy):

- Groups at five levels above a bank account ("1" > "10" > "101" > "1014" > "10140").
- A group "4" holding an income and an expense account by code prefix.
- Equity and Current Year Earnings ungrouped.

Expected:

- Each group row equals the sum of its descendant leaf rows; "(No Group)" holds the ungrouped accounts.
- Only Parents with N = 1 shows "1", "4" and "(No Group)".
- N = 3 adds "10" and "101".
- Grand totals never change with the hierarchy options.

### 4.2 Checks

| ID | Stage | Check | Expected result | Requirements |
|---|---|---|---|---|
| TP-TB-01 | 07 | Wizard validation | Missing or reversed dates, an unauthorized company, a journal or analytic account of another company, Only Parents without Hierarchy, a level outside 1-5, and blank or over-long prefixes are refused server-side; the Many2one fields stay single | T-02, T-03, T-07 to T-10, K-02 |
| TP-TB-02 | 07, 08 | TB-BASE posted only | The numbers listed above, exactly | T-04, T-14, T-15 |
| TP-TB-03 | 07, 08 | TB-BASE with drafts | The numbers listed above; cancelled and February entries excluded | T-05 |
| TP-TB-04 | 08 | TB-X cross-year | The numbers listed above, for January and for February | T-15, A-14 |
| TP-TB-05 | 08 | Date boundaries | Items on Date From and Date To count; items on the day before or after don't; an empty period gives a valid empty report; a negative balance shows on the credit side | T-15 |
| TP-TB-06 | 08 | Prefixes and journal | OR semantics over several prefixes; `_` and `%` in a prefix match literally; the journal filter also restricts the opening balance | T-08, T-09 |
| TP-TB-07 | 08 | Skip Zero Balance | Equal debit and credit movement stays visible; an account with nothing is hidden only when the option is on; with it off, every non-deprecated matching account is listed | T-11, D-12 |
| TP-TB-08 | 08 | TB-C currencies | The rows, columns and per-currency totals listed above; base amounts reconcile between modes | T-12, D-11 |
| TP-TB-09 | 08 | TB-A analytic | The whole-item results listed above; composite keys count once; no filter never duplicates | T-10, D-07 |
| TP-TB-10 | 08 | TB-H hierarchy | Levels 1-5, subtotals, "(No Group)", Only Parents for N = 1 to 5, no double counting in totals | T-06, T-07, D-13 |
| TP-TB-11 | 08, 09 | Access | User B cannot read, preview or export user A's wizard; a company outside B's active companies, a forbidden journal or analytic id, and tampered options sent to the download route are refused; restricted journal items stay invisible | K-02 |
| TP-TB-12 | 08 | Native parity | For TB-BASE, TB-X and TB-A with matched options (posted, drafts, January and February, analytic A1, bank journal), our Initial, Movement and End debit and credit per account and the totals equal the native Trial Balance's | A-14, A-15 |
| TP-TB-13 | 09 | Preview | Opens from the wizard with its options; changing the date or Draft Entries recalculates; the search bar filters lines; folding works; an empty result shows a clear message | T-13, T-16 |
| TP-TB-14 | 09 | PDF (L5) | A real wkhtmltopdf PDF whose text contains the company name, "From ... to ...", the selected filters and the nine column titles; a multi-page sample repeats the header; inspected visually | T-14, T-17 |
| TP-TB-15 | 09 | XLSX (L5) | A real workbook: numeric cells numeric, codes and names as text, no formulas from user text, hierarchy readable, metadata rows present, currencies separate; cell values equal the engine result | T-14, T-18 |
| TP-TB-16 | 09 | Consistency | For the same options on an unchanged database, preview lines, PDF values and XLSX cells are identical | K-01 |
| TP-TB-17 | 07+ | Demo data | Installs with the module: posted and draft entries, several currencies, analytic distributions, and an account-group chart deep enough for levels 1-5 | T-21 to T-23 |

## 5. Acceptance (Stage 11) and general checks

| ID | Check | Expected result | Requirements |
|---|---|---|---|
| TP-G-01 | Each addon installs alone into a fresh database of edition `enterprise-20241208`, then upgrades | No errors or warnings | G-11, P-01, T-01 |
| TP-G-02 | Full custom test suite | All tests pass, with more than 0 tests collected | G-10, G-11 |
| TP-G-03 | Partner Monitor on the Community baseline (optional) | Installs and passes, proving it has no Enterprise dependency | A-17 |
| TP-G-04 | README instructions followed literally from a fresh clone | The documented commands work as written | G-02 to G-05, T-19, T-20 |
| TP-G-05 | Manual demo script (user) | Dashboard, sync status, TB preview, PDF and XLSX checked in a browser; recorded as the user's results | G-11 |

## 6. Commands

Run in `solution/` with Git Bash (see [environment.md](environment.md)):

```text
scripts/dev.sh test azk_odoo_partner_monitor
scripts/dev.sh test azk_dynamic_trial_balance
scripts/dev.sh test azk_dynamic_trial_balance /azk_dynamic_trial_balance:TestNativeParity
scripts/dev.sh test account_reports /account_reports:TestTrialBalanceReport   # vendor regression check
scripts/dev.sh clean-install                                                   # acceptance install
```

Test class names are provisional; Stage 03 onward records the real ones (section 3.1). One Stage 03 test can be run alone, for example:

```text
scripts/dev.sh test azk_odoo_partner_monitor /azk_odoo_partner_monitor:TestStatusHistory.test_silver_gold_gold_records_initial_then_one_promotion
```
