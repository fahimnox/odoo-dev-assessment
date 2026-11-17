# Stage 15 handoff: publication

Date: 2026-11-17. Edition: `enterprise-20241208`. Status: **DONE**. Repository: https://github.com/fahimnox/odoo-dev-assessment (public). Submitted commit: `513145da3c270a0de6b180462e5af41baddf173a`, tag `submission-v1`.

## What this stage delivers

- **The public repository**, under the GitHub account `fahimnox`, the author name of every commit. It was created with the GitHub API: the GitHub CLI is not installed here, and Git Credential Manager holds the login.
- **What was pushed:**
  - `main`, with its full history unchanged;
  - the tag `submission-rc1`, the reviewed release candidate (`32445f0`);
  - the tag `submission-v1`, the submitted commit (`513145d`): `submission-rc1` plus documentation only.
  - This handoff and the Stage 15 log are in the next commit on `main`.
- **Documentation brought to the published state:**
  - README: the URL, a clone step, the status, and the license still open;
  - STATE: Stage 13 PAUSED, Stage 14 DEFERRED, Stage 15 DONE;
  - the release checklist: your decisions and the repeated review;
  - the requirement matrix: G-01 DONE, so 148 of 152 rows are DONE;
  - assumptions (D-71), the test results, an acceptance note, the AI index and the paused Stage 13 log.

## Your decisions, as applied

- The history and the author metadata are published unchanged, so your work email address is public: in every commit and in four documents.
- Both tags are pushed.
- No license file: Q-06 stays open (D-70, D-71).
- Published with the documented defaults: Q-02 to Q-06 were not asked.
- Not marked complete: Stage 13, Stage 14, your manual check (T-19) and P-17.3.

## What I checked, and how

- **Account:** one stored GitHub login, `fahimnox`. `GET /user` confirmed it, with the `repo` scope. The credential was never printed or written to a file.
- **Name:** `fahimnox/odoo-dev-assessment` did not exist (HTTP 404). It was created empty and public (HTTP 201).
- **Review before the push:** the Stage 12 script, with GitHub token prefixes added, over the 199 files and every blob of the 25 earlier commits: PASS. It found no secret value, key, token, local user path, vendor license header, dump, runtime file or private note.
- **Documents:** links PASS (442 in 51 files, 0 broken), ASCII PASS, and the matrix count gives 148 DONE, 2 IN PROGRESS and 2 OUT OF SCOPE.
- **After the push:** `git ls-remote` equals the local refs. Without signing in:
  - the repository is public and `main` is `513145d`;
  - the README and both manifests download with the same SHA-256 as the local files;
  - the tree has 199 files, 62 and 33 of them in the two addons.
- **Not rerun:** the application checks. Since `submission-rc1`, only documentation changed; since the Stage 11 acceptance (261 of 261 tests), no addon code or setup file changed.

## Install commands for a reviewer

You need:
- Docker with Compose v2, and bash;
- the public Odoo Community source at commit `4e5027c159a9d9a8dd006618486c8e54cb1eb453`;
- authorized Odoo Enterprise addons of build `18.0+e.20241208`.

The pinned images provide Python 3.12, requests 2.31.0, beautifulsoup4 4.12.3, XlsxWriter 3.1.9 and wkhtmltopdf 0.12.6.1.

```bash
git clone https://github.com/fahimnox/odoo-dev-assessment.git
cd odoo-dev-assessment
git checkout submission-v1
ENTERPRISE_ADDONS=/path/to/enterprise-18.0-20241208 \
COMMUNITY_SOURCE_20241208=/path/to/odoo-4e5027c1 \
scripts/dev.sh setup     # writes .env, pulls the pinned images, creates azk_ee24 with both addons and demo data
scripts/dev.sh start     # http://127.0.0.1:8071, admin / admin
scripts/dev.sh test      # expect "0 failed, 0 error(s) of 261 tests"
```

## Limitations to state with the link

- Odoo 18.0 is our assumption (Q-04). We tested one runtime pair, on one Windows host, with a trial database.
- The live website was read only in bounded samples (39 requests). We never ran a full crawl, and never tested multi-process workers.
- The views and the wizard layout are our proposal: the specification and the mockup were never supplied (P-17.3).
- The Trial Balance covers one company per report and filters analytic accounts by whole journal items. Parity with the standard report is claimed only for the compared cases.
- Without an outgoing mail server, failure notes reach an inbox only with "Handle in Odoo".
- There is no license file, and your manual check is still pending.

## Open items

- Sending the link to the assessor is your own action.
- Still yours to decide: the license (Q-06), your manual check (T-19), whether to ask Q-02 to Q-06, and whether to mention the supplied archive.
- Stage 13 resumes at section 1, whose question is still open; Stage 14 follows it.
- On this machine, the Stage 11 acceptance project (318 MB) is kept for the demo.

## Changed files

- **Commit `513145d` (tag `submission-v1`):**
  - updated: `README.md`, `docs/STATE.md`, `docs/release_checklist.md`, `docs/requirements_matrix.md`, `docs/assumptions.md`, `docs/test_results.md`, `docs/acceptance_results.md`, `docs/ai/README.md`;
  - new: `docs/ai/stage_13.md`.
- **The next commit on `main`:**
  - new: `docs/ai/stage_15.md` and this handoff;
  - updated: `docs/test_results.md` (the push checks), `docs/ai/README.md`, and links in `docs/STATE.md`, `docs/release_checklist.md` and `docs/requirements_matrix.md`.
- **No addon, setup or script file changed.**

## Comprehension questions

1. `git ls-remote` printed two lines for each tag, one of them ending in `^{}`. What does each line identify, and which one must equal the commit you submit?
2. Your work email address is now in the public history. Why would removing it now need a history rewrite and a force-push, and why would that still not remove it from copies made before?
3. `submission-v1` points to `513145d`, but `main` has one more commit. What does that commit contain, and why could it not be part of the tagged commit itself?

## Next stage

Resume Stage 13 at section 1, then Stage 14, when you ask.
