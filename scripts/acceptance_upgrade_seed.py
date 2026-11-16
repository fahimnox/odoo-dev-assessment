"""Upgrade check helper (Stage 11): seed history before an upgrade, probe the data after it.

    docker compose run --rm -T -e ACC_PHASE=seed -e ACC_DB_CREATED_AFTER odoo-ee-20241208 \
        odoo shell --database=azk_ee24_clean --no-http < scripts/acceptance_upgrade_seed.py

FIXTURE data only (the saved live-derived pages of the tests, read from
odoo.com on 2026-11-08, and variants made in code); no request is sent.
Written to run on the Stage 09 code (commit 564b71b) as well as on later code.

  seed   COMMITTED, on the old code, through the real worker:
         day 1: Andorra's listing (its partners are first seen) and RoayaTec's
                page (3 of 135 references);
         day 2: Andorra's listing with BDR GROUP SLU shown as Silver (a status
                change) and RoayaTec's page with 2 references (one removed).
         Day 2 is tomorrow's date. Partner pages without a fixture are cancelled.
  probe  ROLLED BACK, on the upgraded code: the new worker reads Andorra's
         day-2 page again on day 3. Nothing changed on that page, so no history
         row may be added; the new settings field must exist.

Guard: the database must have been created on or after ACC_DB_CREATED_AFTER
(YYYY-MM-DD), because the names of the acceptance databases are those of the
development project.
"""
import os
import sys
from datetime import timedelta

import odoo
from bs4 import BeautifulSoup
from odoo import fields

# `env` is provided by the Odoo shell. The tests' fixture-backed fetch is
# imported in test mode only (see scripts/restart_check.py).
odoo.tools.config["test_enable"] = True
try:
    from odoo.addons.azk_odoo_partner_monitor.tests.common import (
        ALL_PAGES, EGYPT_P1, ROAYATEC, FixtureSite, andorra_variant, fixture)
finally:
    odoo.tools.config["test_enable"] = False
from odoo.addons.azk_odoo_partner_monitor.services import parsers

PHASE = os.environ.get("ACC_PHASE", "")
created_after = os.environ.get("ACC_DB_CREATED_AFTER", "")
created_on = str(env.ref("base.user_root").create_date.date())  # noqa: F821
if not created_after or created_on < created_after:
    sys.exit(f"refusing to run on {env.cr.dbname}: created on {created_on}, not after ACC_DB_CREATED_AFTER")  # noqa: F821
if PHASE not in ("seed", "probe"):
    sys.exit("ACC_PHASE must be seed or probe")

Country = env["azk_odoo_partner_monitor.country"].with_context(active_test=False)  # noqa: F821
Partner = env["azk_odoo_partner_monitor.partner"].with_context(active_test=False)  # noqa: F821
History = env["azk_odoo_partner_monitor.status.history"]  # noqa: F821
Run = env["azk_odoo_partner_monitor.sync.run"]  # noqa: F821
WorkItem = env["azk_odoo_partner_monitor.work.item"]  # noqa: F821
Worker = env["azk_odoo_partner_monitor.worker"]  # noqa: F821
DAY1 = fields.Datetime.now().replace(microsecond=0)
ANDORRA_URL = "https://www.odoo.com/partners/country/1"
SILVER = {ANDORRA_URL: andorra_variant(statuses={22015187: "Silver"})}
version = env["ir.module.module"].search([("name", "=", "azk_odoo_partner_monitor")]).latest_version  # noqa: F821


def out(*parts):
    print("UPGRADE", *parts, flush=True)


def queue(kind, **target):
    return WorkItem._enqueue(kind, Run.create({"trigger": "manual"}), **target)


def run_worker(site, now):
    result = Worker._process_queue(site, max_units=1, now=now)
    unit = WorkItem.browse(result["done"] + result["failed"])
    out(f"  FIXTURE unit {unit.display_name}: {unit.state}; {unit.result_summary or unit.last_error}")


out(f"phase {PHASE} on {env.cr.dbname}, azk_odoo_partner_monitor {version}")  # noqa: F821
if PHASE == "seed":
    andorra = Country._record_observation({"source_key": "1", "name": "Andorra"})
    egypt = Country._record_observation({"source_key": "64", "name": "Egypt"})
    out("day 1: Andorra's listing")
    queue("country_partners", country=andorra)
    run_worker(FixtureSite(ALL_PAGES), DAY1)
    out("day 2: Andorra's listing, BDR GROUP SLU shown as Silver")
    queue("country_partners", country=andorra)
    run_worker(FixtureSite(ALL_PAGES, html=SILVER), DAY1 + timedelta(days=1))
    cancelled = WorkItem.search([("state", "=", "pending"), ("kind", "=", "partner_details")])
    cancelled.write({"state": "cancelled"})
    out(f"  partner pages without a fixture, cancelled: {len(cancelled)}")
    out("day 1: RoayaTec's page (3 of 135 references)")
    page1 = parsers.parse_listing_page(fixture(EGYPT_P1[1]), EGYPT_P1[0], "64")
    env["azk_odoo_partner_monitor.ingest"]._ingest_country_listing(egypt, [page1], DAY1.date(), now=DAY1)  # noqa: F821
    roayatec = Partner.search([("source_id", "=", 17207720)])
    queue("partner_details", partner=roayatec)
    run_worker(FixtureSite(ALL_PAGES), DAY1)
    out("day 2: RoayaTec's page with 2 references")
    soup = BeautifulSoup(fixture(ROAYATEC[1]), "html.parser")
    soup.select("h3#references ~ div.card")[-1].decompose()
    two_left = str(soup).replace("References - 135", "References - 2")
    queue("partner_details", partner=roayatec)
    run_worker(FixtureSite(ALL_PAGES, html={ROAYATEC[0]: two_left}), DAY1 + timedelta(days=1))
    cancelled = WorkItem.search([("state", "=", "pending")])
    cancelled.write({"state": "cancelled"})
    out(f"  other queued units, cancelled: {len(cancelled)}")
    env.cr.commit()  # noqa: F821
    out("committed")
else:
    andorra = Country.search([("source_key", "=", "1"), ("is_demo", "=", False)])
    before = History.search_count([])
    queue("country_partners", country=andorra)
    run_worker(FixtureSite(ALL_PAGES, html=SILVER), DAY1 + timedelta(days=2))
    out(f"history rows before the probe {before}, after it {History.search_count([])} (no change expected)")
    out("settings field partner_monitor_downloads_paused exists:",
        "partner_monitor_downloads_paused" in env["res.config.settings"]._fields)  # noqa: F821
    env.cr.rollback()  # noqa: F821
    out("rolled back")
