"""Compare the Dynamic Trial Balance engine with the standard Trial Balance
on a database's own journal items (Stage 08).

Runs inside the Odoo shell, as the administrator user (not the superuser), on
the administrator's company, and rolls back at the end: it writes nothing.

    scripts/dev.sh shell azk_ee24 < scripts/tb_engine_vs_native.py

For each case, both reports get the same company (the only active one), the
same dates, the same Draft Entries option and the same journal, with no
hierarchy. It prints, per case, how many account lines each report has and
every account whose Initial, period or End debit or credit differs by more
than 0.005, then one PASS or FAIL line per case.

The standard report lists every account that has journal items in its
queries, even when all its numbers are zero; our report uses Skip Zero
Balance here. All-zero standard lines are therefore set aside and counted.
"""
import copy

from dateutil.relativedelta import relativedelta

from odoo import fields

admin = env.ref("base.user_admin")
company = admin.company_id
user_env = env(user=admin.id, context={"allowed_company_ids": [company.id]})
Engine = user_env["azk_dynamic_trial_balance.engine"]
report = user_env.ref("account_reports.trial_balance_report")
today = fields.Date.context_today(Engine)
fiscal_year = company.compute_fiscalyear_dates(today)
previous_year = company.compute_fiscalyear_dates(fiscal_year["date_from"] - relativedelta(days=1))
month_start = today.replace(day=1)
month_end = month_start + relativedelta(months=1, days=-1)
sales_journal = user_env["account.journal"].search(
    [("company_id", "=", company.id), ("type", "=", "sale")], limit=1)

CASES = [
    ("this month, posted", month_start, month_end, False, None),
    ("this month, with drafts", month_start, month_end, True, None),
    ("fiscal year to date, posted", fiscal_year["date_from"], today, False, None),
    ("fiscal year to date, with drafts", fiscal_year["date_from"], today, True, None),
    ("previous fiscal year, posted", previous_year["date_from"], previous_year["date_to"], False, None),
    ("fiscal year to date, sales journal", fiscal_year["date_from"], today, False, sales_journal),
]


def native_lines(date_from, date_to, draft, journal):
    options = report.get_options({
        "selected_variant_id": report.id,
        "date": {"date_from": fields.Date.to_string(date_from), "date_to": fields.Date.to_string(date_to),
                 "mode": "range", "filter": "custom"},
        "all_entries": draft,
        "hierarchy": False,
        "unfold_all": True,
    })
    if journal:
        options = copy.deepcopy(options)
        for item in options["journals"]:
            item["selected"] = item.get("model") == "account.journal" and item["id"] == journal.id
    lines = {}
    for line in report._get_lines(options):
        model, res_id = report._get_model_info_from_id(line["id"])
        values = tuple(round(column["no_format"] or 0.0, 2) for column in line["columns"])
        if model == "account.account":
            lines[res_id] = values
        elif line["name"] == "Total":
            lines["total"] = values
    return lines


def engine_lines(date_from, date_to, draft, journal):
    result = Engine.compute({
        "date_from": fields.Date.to_string(date_from), "date_to": fields.Date.to_string(date_to),
        "company_id": company.id, "include_unposted": draft,
        "journal_id": journal.id if journal else None, "skip_zero_balance": True,
    })
    keys = ("initial_debit", "initial_credit", "debit", "credit", "ending_debit", "ending_credit")
    lines = {row["account_id"]: tuple(row[key] for key in keys) for row in result["leaf_rows"]}
    lines["total"] = tuple(result["totals"][key] for key in keys)
    return lines


print(f"company: {company.name} ({company.currency_id.name}); today: {today}; "
      f"user: {admin.login}; fiscal year: {fiscal_year['date_from']} to {fiscal_year['date_to']}")
failures = 0
for name, date_from, date_to, draft, journal in CASES:
    theirs = native_lines(date_from, date_to, draft, journal)
    ours = engine_lines(date_from, date_to, draft, journal)
    zero = [key for key, values in theirs.items() if key != "total" and not any(values)]
    for key in zero:
        del theirs[key]
    differences = []
    for key in sorted(set(theirs) | set(ours), key=str):
        a, b = theirs.get(key), ours.get(key)
        if a is None or b is None or any(abs(x - y) > 0.005 for x, y in zip(a, b)):
            label = key if key == "total" else user_env["account.account"].browse(key).display_name
            differences.append(f"    {label}: standard {a}, ours {b}")
    status = "PASS" if not differences else "FAIL"
    failures += bool(differences)
    print(f"{status} {name} ({date_from} to {date_to}{', journal ' + journal.code if journal else ''}): "
          f"{len(theirs) - 1} standard and {len(ours) - 1} engine account lines; "
          f"{len(zero)} all-zero standard lines set aside; totals {ours['total']}")
    for difference in differences:
        print(difference)
print(f"{len(CASES) - failures} of {len(CASES)} cases match")
env.cr.rollback()
