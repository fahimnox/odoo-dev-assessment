# Stage 02 handoff: requirements, assumptions, architecture and test plan

Date: 2026-11-05. Edition: `enterprise-20241208` (port 8071). Status: DONE. No feature code was written.

## What was done

- Re-read the assessment PDF (pp. 1-8) and the later stage prompts, so the design fits Stages 03-09.
- Read the version-sensitive APIs in the pinned 18.0 sources. Enterprise code is cited by name only.
  - cron batching and commits (`ir.cron._run_job`, `_notify_progress`);
  - ORM constraints (`_sql_constraints`; no `models.Constraint` in 18.0) and transient-model access (no implicit owner rule);
  - company-dependent account codes;
  - account groups;
  - analytic distribution search;
  - mail notification preferences;
  - graph view attributes, the embeddable `View` component, `board`, spreadsheet global filters;
  - the `account_reports` extension points and exports;
  - the 18.0 module behind the public `/partners` pages, `website_crm_partner_assign`.
- Created the disposable database `azk_ee24_clean` with `accountant`. Ran a native Trial Balance probe there with eight option sets, then rolled it back.
- Wrote:
  - [architecture.md](../architecture.md) and [test_plan.md](../test_plan.md) (new);
  - [requirements_matrix.md](../requirements_matrix.md) (rewritten, one row per requirement);
  - [assumptions.md](../assumptions.md) (expanded).
- Updated STATE, the environment notes and the Stage 01B decision list.

## Real commands and results

- `df -h /c`: 13 GB free at the start and the end, down from 17-19 GB in the previous session. The cause was not investigated.
- `ODOO_EDITION=enterprise-20241208 scripts/dev.sh clean-install accountant`: PASS. Exit 0, "90 modules loaded", 0 warnings, 0 errors, 5 min 20 s.
- `scripts/dev.sh shell azk_ee24_clean` with the probe script: PASS. Exit 0; the eight report runs printed and rolled back. Key observations:
  - Bank, January, posted: Initial 1,000 / Movement 500-300 / End 1,200. With drafts: End 1,000. The cancelled entry never counts.
  - Income and expense open from the fiscal-year start. Earlier results appear on "Undistributed Profits/Losses" (999999).
  - Analytic filter A1 on a 60/40 item: the full 1,000, not 600. A composite key counts once.
  - The journal filter also restricts the opening balance.
  - Hierarchy groups appear at levels 1-5, with "(No Group)" for ungrouped accounts. Group subtotals add their children's netted values.
- Read-only checks:
  - in `azk_ee24_clean`, `admin` has notification type "email";
  - the image has `freezegun` 1.2.1, `openpyxl` 3.1.2 and `xlrd` 2.0.1, and no Chrome/Chromium.
- NOT RUN:
  - addon tests: no addon code changed;
  - browser checks: no browser is available to the agent.

## Key decisions

**Trial Balance:**

- Our own engine runs inside our own `account.report` record and handler.
- The native preview, PDF and XLSX all render its one normalized result.
- The native opening, carry-forward and netting conventions apply.
- Analytic filtering is native whole-item inclusion.
- Journal and analytic account stay Many2one.
- One authorized company, plus Date From and Date To.
- Amount Currency shows the period movement per transaction currency, never summed across currencies.

**Partner Monitor:**

- Stable site ids with database uniqueness.
- Removals only after complete, validated snapshots.
- Four crons; durable work items that only the worker processes, in bounded batches.
- Commits are the scheduler's; claims are row locks.
- A failure note goes on the run's chatter, addressed to the configured user.
- The dashboard is a small OWL client action that embeds four XML graph views with shared filters.

## Open issues and assumptions

- Questions for the team lead (Q-02 to Q-06), none blocking:
  - the missing views specification, mockup and documentation example;
  - the intended reference report and analytic semantics;
  - the major version;
  - a matched Enterprise build;
  - the license of an addon that depends on `account_reports`.
- The live site may differ from the 18.0 module. Stage 04 verifies it on a small sample.
- The `account_reports` hooks (column groups, PDF header template, preview filter component) are verified in Stages 08-09; the fallback is documented.
- In this build the admin's notification type is "email". The note is always on the run's chatter; the Inbox needs "Handle in Odoo".

## Changed files

- New:
  - `docs/architecture.md`
  - `docs/test_plan.md`
  - `docs/handoffs/stage_02_en.md`
  - `docs/ai/stage_02.md`
- Updated:
  - `docs/requirements_matrix.md`
  - `docs/assumptions.md`
  - `docs/STATE.md`
  - `docs/environment.md`
  - `docs/enterprise_transition.md`
  - `docs/ai/README.md`
- Outside Git:
  - the kit's `CLAUDE.md` (the architecture summary aligned with Stage 02);
  - `runtime/logs/stage02_*` (private logs);
  - the disposable database `azk_ee24_clean`.

## Comprehension questions

1. Why can a crash in the middle of a worker batch never leave a work item permanently claimed?
2. Why must the Trial Balance engine re-validate the company, journal and analytic ids even though the wizard already checked them?
3. In the probe, why did the prior-year revenue appear on account 999999 instead of the revenue account?

## Next stage

03 - Partner Monitor models, permissions and basic UI.
