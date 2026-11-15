# Modest, reproducible benchmark of the Partner Monitor storage and dashboard (Stage 10).
#
# Disposable test database only, after the Partner Monitor tests installed
# the module there:
#
#     scripts/dev.sh shell azk_ee24_test < scripts/pm_benchmark.py
#
# No network: the pages are synthetic parse results (services/parsers.py
# dataclasses), built from a seed, 20 cards per page as on the live site.
# Measured, as the cron's superuser would run them:
#   - one country listing of 100 cards, then of 1,000 cards: first read
#     (partners and history created), then the same pages again (nothing new);
#   - one partner page with 135 references (RoayaTec's size), first and second read;
#   - the dashboard data with every partner of the database.
# Each figure is the median of 3 runs where the step can repeat (the first
# read can run only once). Queries are counted with the cursor's statement
# counter. Everything is ROLLED BACK at the end.
import random
import statistics
import time
from datetime import date

from odoo.addons.azk_odoo_partner_monitor.services import parsers

assert env.cr.dbname == "azk_ee24_test", f"refusing to run on {env.cr.dbname}: azk_ee24_test only"
LOG_PREFIX = "PM_BENCH"
DAY = date(2026, 11, 15)
rng = random.Random(20261115)
Ingest = env["azk_odoo_partner_monitor.ingest"]
Country = env["azk_odoo_partner_monitor.country"]


def out(*parts):
    print(LOG_PREFIX, *parts, flush=True)


def run(label, function, repeat=1):
    seconds, queries, result = [], [], None
    for _run in range(repeat):
        env.invalidate_all()
        before, started = env.cr.sql_log_count, time.perf_counter()
        result = function()
        seconds.append(time.perf_counter() - started)
        queries.append(env.cr.sql_log_count - before)
    out(f"  {label}: median {statistics.median(seconds):.3f} s, queries {queries}")
    return result, statistics.median(seconds), statistics.median(queries)


def listing(country_key, first_id, count):
    cards = [parsers.PartnerCard(
        source_id=first_id + number, name=f"Benchmark Partner {first_id + number}",
        status=rng.choice(("ready", "silver", "gold")),
        raw_url=f"/partners/benchmark-partner-{first_id + number}?country_id={country_key}",
        partner_url=f"https://www.odoo.com/partners/benchmark-partner-{first_id + number}",
        retention_rate=float(rng.randint(50, 100)), average_project_size=float(rng.randint(1, 60)),
        largest_project_size=rng.randint(1, 500), total_references_count=rng.randint(0, 40),
    ) for number in range(count)]
    last = (count + 19) // 20
    base = f"https://www.odoo.com/partners/country/benchmark-{country_key}"
    return [parsers.ListingPage(
        source_url=base if number == 1 else f"{base}/page/{number}", country_key=country_key, scope="country",
        partners=cards[(number - 1) * 20:number * 20], rejected=[], invalid=[], listed_count=count,
        page=number, last_page=last, next_url=f"{base}/page/{number + 1}" if number < last else None,
    ) for number in range(1, last + 1)]


for count, key in ((100, "990100"), (1000, "991000")):
    country = Country._record_observation({"source_key": key, "name": f"Benchland {count}",
                                           "total_partner_count": count})
    pages = listing(key, int(key) * 100, count)
    out(f"listing of {count} cards on {len(pages)} pages")
    summary, seconds, queries = run("first read", lambda: Ingest._ingest_country_listing(country, pages, DAY))
    out(f"  -> found {summary['found']}, complete {summary['complete']}, "
        f"{queries / count:.1f} queries and {1000 * seconds / count:.1f} ms per card")
    summary, seconds, queries = run("same pages again", lambda: Ingest._ingest_country_listing(country, pages, DAY),
                                    repeat=3)
    out(f"  -> {queries / count:.1f} queries and {1000 * seconds / count:.1f} ms per card")

partner = env["azk_odoo_partner_monitor.partner"].search([("source_id", "=", 990100 * 100)])
references = [parsers.Reference(str(5_000_000 + number), f"Benchmark Client {number}", "link") for number in range(135)]
page = parsers.PartnerPage(
    source_url=partner.partner_url, source_id=partner.source_id, partner_url=partner.partner_url, name=partner.name,
    status=partner.current_status, retention_rate=None, average_project_size=None, largest_project_size=None,
    expected_reference_count=135, references=references)
out("partner page with 135 references")
summary, _seconds, _queries = run("first read", lambda: Ingest._ingest_partner_page(partner, page, DAY))
out(f"  -> {summary['found']} of {summary['expected']}, matched {summary['matched']}")
run("same page again", lambda: Ingest._ingest_partner_page(partner, page, DAY), repeat=3)

partners = env["azk_odoo_partner_monitor.partner"].with_context(active_test=False).search_count([])
dashboard = env(su=True)["azk_odoo_partner_monitor.dashboard"]
out(f"dashboard with {partners} partners in the database")
run("get_dashboard_data, no filter", lambda: dashboard.get_dashboard_data({}), repeat=3)
run("get_dashboard_data, status gold", lambda: dashboard.get_dashboard_data({"statuses": ["gold"]}), repeat=3)

env.cr.rollback()
out("rolled back; benchmark countries left:", Country.search_count([("source_key", "in", ["990100", "991000"])]))
