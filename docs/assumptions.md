# Assumptions, missing inputs and open clarifications

The assessment PDF is the source of requirements. Everything below is our interpretation or a gap in the supplied material, not an assessor requirement. Stage 02 expands this file with the full design decisions.

## Missing inputs

These are referenced by the PDF but were **not supplied**. They have not been read, and no part of the solution claims to follow them.

| ID | PDF p. | Referenced material | Consequence |
|---|---|---|---|
| M-01 | 4 | "The views detailed in the original specification", including its required filters, groupings and pivot table configurations (Exercise 1, Part 2) | Views, filters, groupings and pivots will be proposed in Stage 02 and recorded here as assumptions |
| M-02 | 6 | "The provided mockup" for the Trial Balance wizard fields (Exercise 2, Part 1.1) | Wizard layout and any field not listed in the PDF text (e.g. dates, company) are our design |
| M-03 | 1 | `azk_zkteco_machine_proxy`, named as an example of good documentation, with no link or file | README structure will follow the PDF's explicit README list instead |

## Working assumptions

| ID | Assumption | Basis | Status |
|---|---|---|---|
| A-01 | Exercises 1 and 2 are selected; Exercise 3 (POS) is intentionally unselected | PDF p. 3: "Pickup two of the three exercises" | Decided by the user |
| A-02 | Target is Odoo 18 Community | Kit proposal. The PDF names Odoo 18 only for Exercise 3 (p. 8) and doesn't fix a version or edition for Exercises 1–2 | Unconfirmed; question Q-01 |
| A-03 | Exercise 2 addon name is `azk_dynamic_trial_balance` | The PDF gives the report name but no module name (p. 6) | Unconfirmed default |
| A-04 | Development and verification run on Docker Compose with the official `odoo:18.0` and `postgres:16` images, pinned by digest | Stage 01 host inspection; see [environment.md](environment.md) | Decided in Stage 01 |
| A-05 | The addons live in `addons/` inside this repository, not at the repository root | Keeps configuration, documentation and secrets out of the Odoo addons path | Decided in Stage 01 |
| A-06 | Manifest `author` is `fahimnox` (the Git user name) and `license` is `LGPL-3` | The assessment gives no author or license | Unconfirmed default |
| A-07 | The development, test and clean-install databases load demo data | Odoo 18 default; the Trial Balance exercise requires demo data (T-21 to T-23) | Decided in Stage 01 |

## Ambiguities to resolve in Stage 02

| ID | PDF p. | Ambiguity |
|---|---|---|
| D-01 | 6–7 | Wizard comparisons to "TB", "same as Odoo behavior" and "Odoo's dynamic reports": which existing report is meant, and whether it exists in the chosen edition, must be checked against the pinned source |
| D-02 | 7 | Journals and Analytic Accounts are specified as Many2One, but their help texts use plural wording ("specific journals", "specific analytic accounts") |
| D-03 | 7 | The wizard field list has no date or company fields, yet the PDF header requires "the selected date range" and the columns need a period |
| D-04 | 7 | Meaning of Debit/Credit for the Initial and Ending columns (net side vs. gross) is not defined |
| D-05 | 6 | Example project-size buckets "<5, 5-10, 11-25, 25+" leave a gap between 10 and 11 for fractional `average_project_size` values and overlap at 25 |
| D-06 | 5 | Top/Bottom 5 ranking: whether it is computed before or after the shared dashboard filters, and tie handling |
| D-07 | 6–7 | How the Analytic Account filter applies to journal items whose analytic distribution spans several accounts |

## Open clarifications for the team lead

We continue under the documented defaults until answered.

| ID | Question | Status |
|---|---|---|
| Q-01 | Is Odoo 18 Community acceptable for Exercises 1 and 2? | Not yet asked |
| Q-02 | Can you share the original views specification, the Trial Balance wizard mockup, and the `azk_zkteco_machine_proxy` documentation link? | Not yet asked |
| Q-03 | Must the Trial Balance match a specific existing report exactly (opening balances / fiscal-year handling, analytic filtering), or is documented ledger-based behavior acceptable? | Not yet asked |
