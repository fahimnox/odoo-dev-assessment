"""Read-only state report of one database (Stage 11 acceptance). Lines start with "STATE".

Usage: scripts/dev.sh shell DB < scripts/acceptance_state.py

It prints:
- the number of installed modules, and the state and version of the two
  addons and of the modules they rely on;
- Partner Monitor: demo and website records, history, references, runs,
  queued work, scheduled jobs and settings;
- Dynamic Trial Balance: the demo company and its records (as
  scripts/tb_demo_data_counts.py does);
- fingerprints: a SHA-256 of the content an upgrade must keep (countries,
  partners, status history, references, the demo journal entries and their
  items). Database ids are left out, so equal content gives equal
  fingerprints, also in two different databases.

Run it before and after an upgrade and compare the lines. Nothing is written:
the transaction is rolled back at the end.
"""
import hashlib

# `env` is provided by the Odoo shell.


def out(*parts):
    print("STATE", *parts, flush=True)


def fingerprint(label, rows):
    rows = sorted(rows, key=repr)
    digest = hashlib.sha256("\n".join(map(repr, rows)).encode()).hexdigest()[:16]
    out(f"fingerprint {label}: {len(rows)} rows, sha256 {digest}")


Module = env["ir.module.module"]  # noqa: F821
out("database", env.cr.dbname)  # noqa: F821
out("installed modules:", Module.search_count([("state", "=", "installed")]))
for name in ("web_enterprise", "mail", "account", "account_accountant", "accountant", "account_reports",
             "azk_odoo_partner_monitor", "azk_dynamic_trial_balance"):
    module = Module.search([("name", "=", name)])
    out(f"module {name}: {module.state or 'absent'} {module.latest_version or ''}".rstrip())
base = Module.search([("name", "=", "base")])
out("demo data enabled for the database (base module):", base.demo)
out("installed localizations:", Module.search([("state", "=", "installed"), ("name", "=like", "l10n_%")]).mapped("name"))

if "azk_odoo_partner_monitor.partner" in env:  # noqa: F821
    Country = env["azk_odoo_partner_monitor.country"].with_context(active_test=False)  # noqa: F821
    Partner = env["azk_odoo_partner_monitor.partner"].with_context(active_test=False)  # noqa: F821
    History = env["azk_odoo_partner_monitor.status.history"]  # noqa: F821
    Reference = env["azk_odoo_partner_monitor.reference"].with_context(active_test=False)  # noqa: F821
    Run = env["azk_odoo_partner_monitor.sync.run"]  # noqa: F821
    WorkItem = env["azk_odoo_partner_monitor.work.item"]  # noqa: F821
    for demo, label in ((True, "demo"), (False, "website")):
        out(f"PM {label} countries: {Country.search_count([('is_demo', '=', demo)])} "
            f"(active {Country.search_count([('is_demo', '=', demo), ('active', '=', True)])}), "
            f"partners: {Partner.search_count([('is_demo', '=', demo)])} "
            f"(active {Partner.search_count([('is_demo', '=', demo), ('active', '=', True)])}), "
            f"history rows: {History.search_count([('partner_id.is_demo', '=', demo)])}, "
            f"references: {Reference.search_count([('partner_id.is_demo', '=', demo)])} "
            f"(active {Reference.search_count([('partner_id.is_demo', '=', demo), ('is_active', '=', True)])})")
    runs = Run.search([], order="id")
    out("PM runs:", len(runs), [f"{run.id} {run.trigger} {run.state}" for run in runs])
    out("PM work items by state:", dict(sorted(
        (state, WorkItem.search_count([("state", "=", state)]))
        for state in ("pending", "done", "failed", "cancelled"))))
    out("PM sync error rows:", env["azk_odoo_partner_monitor.sync.error"].search_count([]))  # noqa: F821
    for cron in env["ir.cron"].with_context(active_test=False).search(  # noqa: F821
            [("cron_name", "like", "Partner Monitor:")], order="cron_name"):
        out(f"PM job {cron.cron_name!r}: active {cron.active}, every {cron.interval_number} "
            f"{cron.interval_type}, next {cron.nextcall}")
    ICP = env["ir.config_parameter"].sudo()  # noqa: F821
    for key in ("downloads_paused", "notify_user_id", "batch_size"):
        out(f"PM setting {key}: {ICP.get_param('azk_odoo_partner_monitor.' + key)!r}")
    fingerprint("PM countries", [(c.source_key, c.name, c.active, c.is_demo) for c in Country.search([])])
    fingerprint("PM partners", [(p.source_id, p.name, p.active, p.is_demo, p.current_status, p.first_seen_on,
                                 p.country_id.source_key) for p in Partner.search([])])
    fingerprint("PM status history", [(h.partner_id.source_id, h.change_type, h.previous_status, h.new_status,
                                       h.change_date) for h in History.search([])])
    fingerprint("PM references", [(r.partner_id.source_id, r.source_key, r.name, r.is_active, r.added_on,
                                   r.removed_on) for r in Reference.search([])])
else:
    out("PM not installed")

if "azk_dynamic_trial_balance.engine" in env:  # noqa: F821
    company = env.ref("azk_dynamic_trial_balance.demo_company", raise_if_not_found=False)  # noqa: F821
    if not company:
        out("TB demo company: none")
    else:
        Move = env["account.move"]  # noqa: F821
        demo = [("company_id", "=", company.id), ("ref", "=like", "TB Demo:%")]
        moves = Move.search(demo)
        out(f"TB demo company: {company.name!r}, currency {company.currency_id.name}, "
            f"country {company.country_id.code}, companies with that name: "
            f"{env['res.company'].search_count([('name', '=', company.name)])}")  # noqa: F821
        out("TB demo entries:", len(moves), "posted/draft/cancelled:",
            [Move.search_count([*demo, ("state", "=", state)]) for state in ("posted", "draft", "cancel")],
            "items:", len(moves.line_ids),
            "groups:", env["account.group"].search_count([("company_id", "=", company.id)]),  # noqa: F821
            "analytic accounts:", env["account.analytic.account"].search_count(  # noqa: F821
                [("company_id", "=", company.id)]),
            "rates:", env["res.currency.rate"].search_count([("company_id", "=", company.id)]))  # noqa: F821
        fingerprint("TB demo entries", [(m.ref, m.date, m.state, m.journal_id.code, m.amount_total,
                                         m.currency_id.name) for m in moves])
        fingerprint("TB demo items", [(line.move_id.ref, line.account_id.code, line.debit, line.credit,
                                       line.amount_currency, line.currency_id.name) for line in moves.line_ids])
else:
    out("TB not installed")

env.cr.rollback()  # noqa: F821
