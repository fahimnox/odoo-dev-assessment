# Modest, reproducible benchmark of the Dynamic Trial Balance (Stage 10).
#
# Disposable test database only, after the Trial Balance tests installed the
# module there:
#
#     scripts/dev.sh shell azk_ee24_test < scripts/tb_benchmark.py
#
# Dataset (seeded, so every run builds the same data): a new company with
# Odoo's generic chart plus 100 extra accounts; balanced two-line entries in
# its miscellaneous journal, dated 2025-01-01 to 2026-03-31, about 10% left
# in draft. Measured at two sizes (1,000 then 5,000 entries), as the admin
# user, for two option sets: the engine, the preview lines (_get_lines),
# the XLSX export and the PDF export without wkhtmltopdf (the HTML that it
# would print; the real conversion is not timed here). Each figure is the
# median of 3 runs with the ORM cache cleared; queries are counted with the
# cursor's statement counter. Everything is ROLLED BACK at the end.
import random
import statistics
import time
from datetime import date, timedelta
from unittest.mock import patch

from odoo import Command

assert env.cr.dbname == "azk_ee24_test", f"refusing to run on {env.cr.dbname}: azk_ee24_test only"
LOG_PREFIX = "TB_BENCH"
SIZES = (1000, 5000)
BATCH = 500


def out(*parts):
    print(LOG_PREFIX, *parts, flush=True)


rng = random.Random(20261115)
egp = env.ref("base.EGP")
egp.active = True
# No country: in a shell, a company with a country makes Odoo install that
# country's localization, and a module install commits (docs/review_findings.md).
company = env["res.company"].create({"name": "AZK TB Benchmark", "currency_id": egp.id})
env["account.chart.template"].try_loading("generic_coa", company=company, install_demo=False)
company.currency_id = egp
admin = env.ref("base.user_admin")
admin.write({"company_ids": [Command.link(company.id)]})
Account = env["account.account"].with_company(company)
extra = Account.create([{
    "name": f"Benchmark account {number:03d}", "code": f"BEN{number:03d}",
    "account_type": "expense" if number % 2 else "asset_current",
} for number in range(1, 101)])
chart = Account.search([*Account._check_company_domain(company), ("deprecated", "=", False),
                        ("account_type", "not in", ("asset_receivable", "liability_payable", "off_balance"))])
pool = list(chart)
journal = env["account.journal"].search([("company_id", "=", company.id), ("type", "=", "general")], limit=1)
out("company", company.name, "accounts in the chart", len(chart), "of which extra", len(extra),
    "journal", journal.code)

first_day = date(2025, 1, 1)


def add_entries(count):
    for start in range(0, count, BATCH):
        values = []
        for _number in range(min(BATCH, count - start)):
            debit_account, credit_account = rng.sample(pool, 2)
            amount = round(rng.uniform(1, 5000), 2)
            values.append({
                "move_type": "entry", "date": first_day + timedelta(days=rng.randrange(455)),
                "journal_id": journal.id, "company_id": company.id, "ref": "benchmark",
                "line_ids": [
                    Command.create({"account_id": debit_account.id, "debit": amount, "credit": 0.0, "name": "bench"}),
                    Command.create({"account_id": credit_account.id, "debit": 0.0, "credit": amount, "name": "bench"}),
                ],
            })
        moves = env["account.move"].with_company(company).create(values)
        moves.filtered(lambda _move: rng.random() >= 0.1).action_post()
        env.flush_all()
        env.invalidate_all()


user_env = env(user=admin.id, context=dict(env.context, allowed_company_ids=[company.id]))
engine = user_env["azk_dynamic_trial_balance.engine"]
report = user_env.ref("azk_dynamic_trial_balance.dynamic_trial_balance_report")
option_sets = {
    "all accounts, posted": {},
    "drafts, hierarchy, skip zero": {"include_unposted": True, "hierarchy_subtotals": True, "skip_zero_balance": True},
}


def measure(label, function, repeat=3):
    seconds, queries, result = [], [], None
    for _run in range(repeat):
        env.invalidate_all()
        before, started = env.cr.sql_log_count, time.perf_counter()
        result = function()
        seconds.append(time.perf_counter() - started)
        queries.append(env.cr.sql_log_count - before)
    out(f"  {label}: median {statistics.median(seconds):.3f} s (min {min(seconds):.3f}, max {max(seconds):.3f}), "
        f"queries {queries}")
    return result


def stub_wkhtmltopdf(report_model, bodies, **kwargs):
    stub_wkhtmltopdf.html_bytes = sum(len(body) for body in bodies)
    return b"%PDF-1.4 benchmark stub"


done = 0
for size in SIZES:
    started = time.perf_counter()
    add_entries(size - done)
    done = size
    lines = env["account.move.line"].search_count([("company_id", "=", company.id)])
    posted = env["account.move"].search_count([("company_id", "=", company.id), ("state", "=", "posted")])
    out(f"size {size} entries ({posted} posted), {lines} journal items; created in "
        f"{time.perf_counter() - started:.1f} s")
    for name, extra_options in option_sets.items():
        raw = {"date_from": "2026-01-01", "date_to": "2026-03-31", "company_id": company.id, **extra_options}
        out(f" option set '{name}'")
        result = measure("engine compute", lambda: engine.compute(raw))
        out(f"  rows: {len(result['lines'])} lines, {len(result['leaf_rows'])} account rows, "
            f"balanced {result['metadata']['balanced']}")
        options = report.get_options({
            "date": {"date_from": raw["date_from"], "date_to": raw["date_to"], "mode": "range", "filter": "custom"},
            "all_entries": raw.get("include_unposted", False), "unfold_all": True,
            "azk_tb": {key: value for key, value in raw.items()
                       if key not in ("date_from", "date_to", "include_unposted")},
        })
        measure("preview lines (_get_lines)", lambda: report._get_lines(options))
        xlsx = measure("XLSX export", lambda: report.export_to_xlsx(options))
        with patch.object(type(env["ir.actions.report"]), "_run_wkhtmltopdf", stub_wkhtmltopdf):
            measure("PDF export without wkhtmltopdf", lambda: report.export_to_pdf(options))
        out(f"  file sizes: XLSX {len(xlsx['file_content'])} bytes, PDF HTML {stub_wkhtmltopdf.html_bytes} bytes")

env.cr.rollback()
out("rolled back; benchmark companies left:", env["res.company"].search_count([("name", "=", "AZK TB Benchmark")]))
