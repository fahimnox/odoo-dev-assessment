"""Count the Dynamic Trial Balance demo records (Stage 09). Read-only.

Usage: scripts/dev.sh shell azk_ee24 < scripts/tb_demo_data_counts.py

Run it before and after an upgrade of azk_dynamic_trial_balance: equal
counts show that the upgrade duplicated nothing. The transaction is rolled
back at the end. Output lines start with "TB_DEMO".
"""
# `env` is provided by the Odoo shell.
company = env.ref("azk_dynamic_trial_balance.demo_company", raise_if_not_found=False)  # noqa: F821
if not company:
    print("TB_DEMO demo company: none")
else:
    in_company = [("company_id", "=", company.id)]
    demo_entries = [*in_company, ("ref", "=like", "TB Demo:%")]
    counts = {
        "companies with the demo name": env["res.company"].search_count([("name", "=", company.name)]),  # noqa: F821
        "demo entries": env["account.move"].search_count(demo_entries),  # noqa: F821
        "posted, draft, cancelled": [
            env["account.move"].search_count([*demo_entries, ("state", "=", state)])  # noqa: F821
            for state in ("posted", "draft", "cancel")
        ],
        "demo journal items": env["account.move.line"].search_count(  # noqa: F821
            [*in_company, ("move_id.ref", "=like", "TB Demo:%")]),
        "account groups": env["account.group"].search_count(in_company),  # noqa: F821
        "analytic plans": env["account.analytic.plan"].search_count(  # noqa: F821
            [("name", "in", ("Demo Departments", "Demo Projects"))]),
        "analytic accounts": env["account.analytic.account"].search_count(in_company),  # noqa: F821
        "currency rates": env["res.currency.rate"].search_count(in_company),  # noqa: F821
        "journals": env["account.journal"].search_count(in_company),  # noqa: F821
    }
    print(f"TB_DEMO demo company: id {company.id}, currency {company.currency_id.name}, "
          f"country {company.country_id.code}, fiscal country {company.account_fiscal_country_id.code}")
    for key, value in counts.items():
        print(f"TB_DEMO {key}: {value}")
env.cr.rollback()  # noqa: F821
