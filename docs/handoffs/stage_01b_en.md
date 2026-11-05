# Stage 01B handoff (English)

Stage 01B: adapt the completed Community setup to the confirmed Enterprise target. Written on 2026-11-03 from the commands and results recorded in `docs/enterprise_transition.md` and `docs/environment.md`.

## Status (updated 2026-11-05)

- **DONE. Stage 02 is ready.** The compatibility blocker is resolved by the matched pair: the official Community source `odoo/odoo@4e5027c1` with the 620 Enterprise modules of build 18.0+e.20241208, run as edition `enterprise-20241208` (the default). See "Follow-up continuation" below.
- On fresh databases, all eight `TestTrialBalanceReport` tests passed (including `test_trial_balance_comparisons`), the custom addon tests passed 4 of 4, and the login, Trial Balance, PDF and XLSX smoke checks passed.
- The Stage 01B pair (`odoo-ee`, `azk_ent`) still fails that vendor test. It stays blocked and is kept only as evidence.
- Browser checks: the user reported one for the Stage 01B environment (no detailed results given). None has been done yet for the matched pair on port 8071; it is recommended and was not part of the agreed checks.
- No business features are implemented yet. Both addons are installable skeletons with smoke tests.

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

1. `scripts/dev.sh start`, then open http://127.0.0.1:8071/web/login (the matched pair, the default edition since 2026-11-05; the Stage 01B environment was on 8070) and log in as `admin` / `admin`.
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
- The 3 modules `certificate`, `l10n_it_edi_website_sale` and `project_hr_skills` were copied to a separate folder as "Enterprise modules the 2024 pair needs". Corrected 2026-11-05: they are part of the official Community source, which carries an OEEL-1 license key for them, so the copy was redundant and has been deleted. No runtime needs the extracted archive.

The pins for the pair to validate:

- Community: `odoo/odoo` `4e5027c159a9d9a8dd006618486c8e54cb1eb453`. Not downloaded yet; 0.20 GB without translations.
- Enterprise: build 18.0+e.20241208, the 620 modules in `runtime/enterprise/18.0-20241208/` (SHA-256 `f2c60cc6...b499`). This line first said 623 plus a 3-module folder; corrected 2026-11-05.

Not run, because of disk space: fetching the source, the new service, fresh databases, the eight `TestTrialBalanceReport` tests, the custom tests, and the login, Trial Balance, PDF and XLSX smoke checks. The exact steps are in `docs/enterprise_transition.md`.

How you could free space (your decision; I deleted nothing):

- Restart Windows: a system-managed page file usually shrinks back. The containers stop, and `scripts/dev.sh start` brings ours back.
- Delete the extracted archive `<kit-root>/odoo/odoo18` (1.76 GB), only if you keep the original archive file elsewhere.
- Move Docker Desktop's disk image to D: (Docker Desktop settings). This also affects the other project's containers.
- Other files of yours on C:.

## Follow-up continuation (2026-11-05)

What was done (the user had freed disk space first: 17 GB, watched by a background monitor):

- Fetched the official GitHub archive of `odoo/odoo@4e5027c1` without translations into `<kit-root>/runtime/community/18.0-4e5027c1/`. All 21,846 files are identical to the official tree by git blob SHA (0 different, 0 missing, 0 extra). Pinned: tree SHA-256 `7699e418...e0e6`.
- Correction: `certificate`, `l10n_it_edi_website_sale` and `project_hr_skills` are in the official Community source (with an OEEL-1 license key in their manifests). So the Enterprise side is the 620-module folder, and the extra 3-module folder from 2026-11-04 was redundant. It was removed and deleted, and both test commands were rerun on the final configuration.
- New service `odoo-ee-20241208`:
  - the same pinned image, with the official `odoo/` mounted read-only over its Odoo package;
  - the official `addons/`, the 620 Enterprise modules and our addons on the addons path;
  - its own volume and port 8071, serving `azk_ee24`.
- New `dev.sh` edition `enterprise-20241208`, with prefix-based database ownership (10 refusal cases verified).

Results, all PASS, on fresh databases:

- `scripts/dev.sh test account_reports /account_reports:TestTrialBalanceReport`: 8 tests, 0 failed, 0 errors.
- `scripts/dev.sh test`: 4 tests, 0 failed, 0 errors.
- `scripts/dev.sh setup`: `azk_ee24` with 92 modules, 0 warnings.
- Shell: Enterprise modules from `/mnt/enterprise-addons`, Community from `/mnt/community-addons`, version `18.0+e`. The Trial Balance is balanced and net-side.
- HTTP: login uid 2, web client and bundles 200, report RPC OK, refusal without a session.
- PDF (one page, with header and footer) and XLSX (a valid workbook), both rendered inside the running server. The server log has 0 warnings.

Preserved: `azk_dev`, `azk_ent`, the `odoo` and `odoo-ee` services and volumes, the backups, and the other project's containers.

Follow-up comprehension questions:

1. Why does mounting the official `odoo/` folder over the image's Odoo package not count as patching vendor code?
2. What could go wrong if `azk_ent`, created by the 2026 core, were opened by the 2024 core?
3. Why was a matching build date not accepted as proof that `4e5027c1` is the build's Community revision, and what was?

## Comprehension questions

1. Why does `scripts/dev.sh` refuse to run an install on `azk_dev` when the edition is `enterprise`, and which manifest key creates that risk?
2. The server reports `18.0+e-20261015`. Which part of that string comes from the image, which part from `web_enterprise`, and why does it not prove that the Enterprise addons are from 2026?
3. The vendor test failed on our runtime and passed on the archive's own core. What does that control run tell you that the failing test alone could not?

## Next stage

Stage 02, on edition `enterprise-20241208` (the default in `.env`). Recommended first: a quick browser check of http://127.0.0.1:8071 (steps in `docs/enterprise_transition.md`).

```text
Read prompts/02_requirements_and_design.txt and execute Stage 02 only, following solution/AGENTS.md.
```
