# Partner Monitor: one country sync, a status change and a reference change,
# through the real worker, with evidence printed before and after (Stage 06).
#
# SOURCE: the saved live-derived fixture pages in tests/fixtures (read from
# odoo.com on 2026-11-08) and variants made in code from them. No live page is
# read: the page-download module is deferred (Stage 04 PARTIAL).
#
# Run it piped into "odoo shell" on the disposable test database, for example:
#   docker compose run --rm -T odoo-ee-20241208 odoo shell --database=azk_ee24_test \
#       --no-http --log-level=warn < scripts/fixture_sync_demo.py
# Nothing is committed: the shell rolls the transaction back at the end.

import sys
from datetime import timedelta

import odoo
from bs4 import BeautifulSoup
from odoo import fields
from odoo.addons.azk_odoo_partner_monitor.services import parsers

# This script reuses the tests' fixture-backed fetch; see scripts/restart_check.py.
odoo.tools.config["test_enable"] = True
try:
    from odoo.addons.azk_odoo_partner_monitor.tests.common import (
        ALL_PAGES, EGYPT_P1, ROAYATEC, FixtureSite, andorra_variant, fixture)
finally:
    odoo.tools.config["test_enable"] = False

if not env.cr.dbname.endswith("_test"):  # noqa: F821 (provided by odoo shell)
    sys.exit(f"refusing to run on {env.cr.dbname}: a disposable *_test database is required")  # noqa: F821

Country = env["azk_odoo_partner_monitor.country"].with_context(active_test=False)  # noqa: F821
Partner = env["azk_odoo_partner_monitor.partner"].with_context(active_test=False)  # noqa: F821
Run = env["azk_odoo_partner_monitor.sync.run"]  # noqa: F821
WorkItem = env["azk_odoo_partner_monitor.work.item"]  # noqa: F821
Worker = env["azk_odoo_partner_monitor.worker"]  # noqa: F821
DAY1 = fields.Datetime.now().replace(microsecond=0)
DAY2 = DAY1 + timedelta(days=1)


def say(text=""):
    print(text, flush=True)


def queue(kind, **target):
    return WorkItem._enqueue(kind, Run.create({"trigger": "manual"}), **target)


def run_worker(site, now):
    result = Worker._process_queue(site, max_units=1, now=now)
    unit = WorkItem.browse(result["done"] + result["failed"])
    say(f"  worker: {unit.display_name} -> {unit.state}; {unit.result_summary or unit.last_error}")
    say(f"  pages read: {', '.join(site.requested)}")


def show_partners(country):
    for partner in Partner.search([("country_id", "=", country.id)], order="source_id"):
        history = ", ".join(
            f"{row.change_type} {row.previous_status + ' -> ' if row.previous_status else ''}{row.new_status} "
            f"on {row.change_date}" for row in partner.status_history_ids.sorted("id"))
        say(f"  partner {partner.source_id} {partner.name!r}: status {partner.current_status}, first seen "
            f"{partner.first_seen_on}, last seen {partner.last_seen_on}; history: {history}")


def show_references(partner):
    for ref in partner.reference_ids.sorted("id"):
        say(f"  reference {ref.source_key} {ref.name!r}: active {ref.is_active}, added {ref.added_on}, "
            f"removed {ref.removed_on or '-'}")
    say(f"  expected {partner.total_references_count}, found {partner.snapshot_reference_count}, "
        f"active {partner.active_reference_count}, validation {partner.reference_validation_state}, "
        f"flag {partner.to_reprocess_references}")


say("SOURCE: saved live-derived fixture pages (tests/fixtures, read from odoo.com on 2026-11-08) and")
say("variants made in code from them. No live page is read.")
say(f"Dates: day 1 = {DAY1.date()}, day 2 = {DAY2.date()}")
andorra = Country._record_observation({"source_key": "1", "name": "Andorra"})
egypt = Country._record_observation({"source_key": "64", "name": "Egypt"})

say()
say("1. Country sync: Andorra's listing page (fixture live_listing_andorra.html), day 1")
say("  before: " + str(Partner.search_count([("country_id", "=", andorra.id)])) + " partners stored for Andorra")
queue("country_partners", country=andorra)
run_worker(FixtureSite(ALL_PAGES), DAY1)
show_partners(andorra)
say(f"  country: listed {andorra.total_partner_count}, found {andorra.snapshot_partner_count}, "
    f"validation {andorra.validation_state}")

say()
say("2. Status change: the same page with BDR GROUP SLU shown as Silver (variant made in code), day 2")
queue("country_partners", country=andorra)
run_worker(FixtureSite(ALL_PAGES, html={"https://www.odoo.com/partners/country/1":
                                        andorra_variant(statuses={22015187: "Silver"})}), DAY2)
show_partners(andorra)

queued = WorkItem.search([("state", "=", "pending"), ("kind", "=", "partner_details")])
say(f"  the first sync also queued the pages of its new partners: {', '.join(queued.mapped('display_name'))}")
say("  (no saved page exists for them; they are cancelled for this demonstration)")
queued.write({"state": "cancelled"})

say()
say("3. Reference change: RoayaTec's page (fixture live_partner_roayatec.html: 3 of 135 references)")
page1 = parsers.parse_listing_page(fixture(EGYPT_P1[1]), EGYPT_P1[0], "64")
env["azk_odoo_partner_monitor.ingest"]._ingest_country_listing(egypt, [page1], DAY1.date(), now=DAY1)  # noqa: F821
roayatec = Partner.search([("source_id", "=", 17207720)])
queue("partner_details", partner=roayatec)
run_worker(FixtureSite(ALL_PAGES), DAY1)
show_references(roayatec)
say("  then the page lists only 2 references and says 'References - 2' (variant made in code), day 2:")
soup = BeautifulSoup(fixture(ROAYATEC[1]), "html.parser")
soup.select("h3#references ~ div.card")[-1].decompose()
two_left = str(soup).replace("References - 135", "References - 2")
queue("partner_details", partner=roayatec)
run_worker(FixtureSite(ALL_PAGES, html={ROAYATEC[0]: two_left}), DAY2)
show_references(roayatec)
say()
say("Nothing was committed (the shell rolls back).")
