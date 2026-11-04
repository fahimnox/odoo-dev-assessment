# Stage 01B handoff (English)

Stage 01B: adapt the completed Community setup to the confirmed Enterprise target. Written on 2026-11-03 from the commands and results recorded in `docs/enterprise_transition.md` and `docs/environment.md`.

## Status (updated 2026-11-04)

- **BLOCKED. The Enterprise environment is not ready.** The failing vendor Trial Balance test is an unresolved compatibility blocker (user decision, 2026-11-04), even though this single-company assessment does not use that code path.
- The fix is identified and verified by content: the official Community commit `odoo/odoo@4e5027c1` with the Enterprise modules of the same build. Its validation was not run, because drive C: is nearly full. See "Compatibility follow-up" below.
- The browser smoke check of the Stage 01B environment was reported done by the user (no detailed results given); it was not run by the agent.
- Server-side Stage 01B checks on the Stage 01B pair: PASS, except the vendor test.
- No business features are implemented yet. Both addons are installable skeletons with smoke tests.
- Next: free disk space, then finish the follow-up. Stage 02 waits.

## What the archive is

- `<kit-root>/odoo/odoo18` is an Odoo 18.0 Enterprise nightly source tarball, build `18.0+e.20241208` (from `PKG-INFO` and `odoo/release.py`). It has the server, the Community addons and the Enterprise addons in one `odoo/addons` folder: 1,243 modules, 614 of them under the Enterprise license OEEL-1.
- `web_enterprise`, `accountant`, `account_accountant` and `account_reports` are present, with dependencies that all resolve.
- Its core and some Community files were modified after the build date, for example `base/models/ir_actions.py`. Its Enterprise modules were not.
- Not vendor source, and not used: an old virtualenv, five config files with credentials (values never printed), an old data dir, repair and SQL scripts (never run), old agent files, a byte-identical copy of the assessment PDF, and custom projects. One of those projects is an earlier implementation of this assessment's modules, which was not opened.

## What was decided and set up

- Pairing: keep the pinned image's Community core (18.0-20261015, git head `8e50ecb1...`) and add only the archive's 620 Enterprise-repository modules on the addons path. This is the official model ("run the Community server with the Enterprise addons on the addons path"). The archive's own core was rejected because it was modified after its build. A matched Enterprise build is requested (Q-05).
- The private copy is `<kit-root>/runtime/enterprise/18.0-20241208/`: 27,897 files, tree SHA-256 `f2c60cc6...b499`. Three modules that moved to Community were left out.
- New Compose service `odoo-ee`: the same image and PostgreSQL, the Enterprise folder mounted read-only, its own config (`config/odoo-enterprise.conf`), its own data volume, http://127.0.0.1:8070, serving only `azk_ent`.
- `scripts/dev.sh`: `ODOO_EDITION` switches between `enterprise` (the default in this workspace's `.env`) and `community`, and the script refuses the other edition's databases.
- New database `azk_ent`: `web_enterprise`, `accountant` and both addons with demo data, 93 modules. `azk_dev` was not touched.
- Backup before the changes: an `azk_dev` dump and filestore, `.env` and config copies, and Git HEAD `af31554`, all in `<kit-root>/runtime/backups/2026-11-03_pre_stage01b/`.

## Commands run and results

- `scripts/dev.sh setup` (Enterprise): PASS. 93 modules, 0 warnings, 3m21s.
- Odoo shell checks on `azk_ent` (module states and paths, addons path order, company, subscription parameters): PASS.
- `scripts/dev.sh start`, then HTTP login, the web client page, the asset bundles, the native report RPC, and a refusal without a session: PASS.
- `scripts/dev.sh update azk_odoo_partner_monitor,azk_dynamic_trial_balance`: PASS.
- `scripts/dev.sh test` (Enterprise): 4 tests, 0 failed, 0 errors. PASS.
- `ODOO_EDITION=community scripts/dev.sh test`: 4 tests, 0 failed, 0 errors. PASS (the baseline still works).
- Native Trial Balance (shell): lines computed; debit equals credit in each group; Initial and End are net-side. XLSX: valid workbook. PDF: one page with header and footer, after a port fix. PASS.
- `scripts/dev.sh test account_reports /account_reports:TestTrialBalanceReport`: 7 of 8 passed, FAIL. The cause is in the 2026 Community currency-table code. The control run on the matched 2024 build passed 8 of 8.
- Full vendor `account_reports` suite: NOT RUN. It was stopped before its first test because drive C: was down to 2.0 GB free.
- `dev.sh` guards (8 cases): PASS. The Compose-level missing-folder guard does not work on Docker Desktop; this is documented, and `dev.sh` remains the guard.

## Manual check for the user (NOT RUN by the agent)

1. `scripts/dev.sh start`, then open http://127.0.0.1:8070/web/login and log in as `admin` / `admin`.
2. Expected: the Enterprise home menu with app icons, and a registration banner for administrators. Don't register and don't buy.
3. Open Accounting > Reporting > Trial Balance (in the "Audit Reports" section), change the date, toggle "Draft Entries", and click PDF and "Download Excel".
4. Open Apps, remove the "Apps" filter, search for `azk`: both addons should be installed.
5. Report any red error dialog, blank page or browser-console error.

## Native Trial Balance: what to remember for Stage 02

- Model and record: `account.report`, `account_reports.trial_balance_report`. Handler `account.trial.balance.report.handler`, which reuses the General Ledger handler. Client action `account_reports.action_account_report_coa`.
- Columns: Initial Balance, the period and End Balance, each with Debit and Credit only. Initial and End are netted to one side.
- Opening of income and expense accounts starts at the fiscal-year start, and earlier results go to undistributed profits.
- The analytic filter includes whole journal items, with no proration.
- "Draft Entries" means posted plus drafts, never cancelled.
- Gaps against the assessment: the wizard, the nine columns, account prefixes, Many2one journal and analytic filters, skip-zero, amount currency per account and currency, and the level-limited hierarchy. The standard demo data also lacks drafts, a second currency and account groups.

## How the Odoo pieces differ (Django bridge)

- The Enterprise "edition" is not a different server. It is the same Community server process with an extra addons folder, much as a Django project gains features from extra apps in `INSTALLED_APPS`. The core is still Community code.
- `addons_path` order matters only for duplicate module names. Odoo always searches its own core folder first, so the image's Community modules win a name clash.
- `auto_install` acts like a signal that installs a module once its dependencies are present. `web_enterprise` auto-installs whenever `web` is installed, which is why a Community database must never be opened with the Enterprise path.
- `web_enterprise` changes the reported version string at import time (`18.0+e-...`), so the version string alone doesn't tell you where the Enterprise addons came from.

## Open items and assumptions

- New assumptions A-08 (Enterprise confirmed), A-09 (18.0 provisional), A-10 (the runtime pairing) and A-11 (an unregistered trial). New questions Q-04 (major version) and Q-05 (a matched Enterprise build).
- `azk_ent` is unregistered. Registration needs the employer's subscription code.
- Whether to mention the earlier assessment implementation found in the archive to the team lead is the user's decision.
- **Disk space is now the main environment risk.** Drive C: went from 7.9 GB free at the start of this stage to 2.0 GB at the end. Our new files and databases account for about 0.65 GB; the rest is not attributed (Docker's shared virtual disk, 14.6 GB, which only grows, and other activity). Free space before Stage 02's long runs; a full disk can damage the PostgreSQL cluster.

## Compatibility follow-up (2026-11-04)

What was done (read-only, no server, database or test run):

- Disk: C: had 2.5 GB free at the start and 1.5 to 1.7 GB during the work, while the agent only read files. Docker's disk did not grow. Large items are the page file (10.9 GB), the hibernation file (6.8 GB) and Docker's disk (14.6 GB). D: has 8.5 GB free.
- No employer-provided matching pair exists in the workspace.
- Official baseline: the archive's Community files were compared with the official GitHub tree of `odoo/odoo` commit `4e5027c159a9d9a8dd006618486c8e54cb1eb453` (18.0, 2024-12-08 01:24 UTC) using git blob hashes, which depend on content only.
  - 36,514 of 37,496 files are identical, including all translations.
  - The 972 absent files are packaging exclusions (`doc/`, `debian/`, `setup/`, ...).
  - 10 files differ, all explained.
  - No commit landed on 18.0 between that commit and the 07:05 UTC checkout.
  - The archive's 30 theme modules equal `design-themes@3057d466` byte for byte.
- The 13 files flagged by timestamp in Stage 01B, checked against that baseline:
  - 2 are unchanged;
  - 6 differ only in formatting, with identical Python syntax trees (including core `ir_actions.py`);
  - 2 have real local edits: debugging `print` calls in `website_sale` `shop_checkout`, and rearranged `test_website` data;
  - 3 are configuration files;
  - in addition, `release.py` and `setup.cfg` show the expected packaging changes.
- The 3 Enterprise modules the 2024 pair needs (`certificate`, `l10n_it_edi_website_sale`, `project_hr_skills`) were copied to `<kit-root>/runtime/enterprise/18.0-20241208-moved-to-community/` (0.72 MB, tree SHA-256 `ec0225f5...82c4`). After that, no runtime needs the extracted archive.

The pins for the pair to validate:

- Community: `odoo/odoo` `4e5027c159a9d9a8dd006618486c8e54cb1eb453`. Not downloaded yet; 0.20 GB without translations.
- Enterprise: build 18.0+e.20241208, 623 modules: `runtime/enterprise/18.0-20241208/` (620, SHA-256 `f2c60cc6...b499`) plus the 3-module folder above.

Not run, because of disk space: fetching the source, the new service, fresh databases, the eight `TestTrialBalanceReport` tests, the custom tests, and the login, Trial Balance, PDF and XLSX smoke checks. The exact steps are in `docs/enterprise_transition.md`.

How you could free space (your decision; I deleted nothing):

- Restart Windows: a system-managed page file usually shrinks back. The containers stop, and `scripts/dev.sh start` brings ours back.
- Delete the extracted archive `<kit-root>/odoo/odoo18` (1.76 GB), only if you keep the original archive file elsewhere.
- Move Docker Desktop's disk image to D: (Docker Desktop settings). This also affects the other project's containers.
- Other files of yours on C:.

## Comprehension questions

1. Why does `scripts/dev.sh` refuse to run an install on `azk_dev` when the edition is `enterprise`, and which manifest key creates that risk?
2. The server reports `18.0+e-20261015`. Which part of that string comes from the image, which part from `web_enterprise`, and why does it not prove that the Enterprise addons are from 2026?
3. The vendor test failed on our runtime and passed on the archive's own core. What does that control run tell you that the failing test alone could not?

## Next step

Not Stage 02 yet. First free at least 5 GB on drive C:, then ask for the remaining compatibility follow-up steps (fetch the pinned Community source, set up the matched-pair service, and run the eight vendor tests, the custom tests and the smoke checks on fresh databases). Stage 02 starts only after the blocker is resolved:

```text
Read prompts/02_requirements_and_design.txt and execute Stage 02 only, following solution/AGENTS.md.
```
