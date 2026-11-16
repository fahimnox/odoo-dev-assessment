# Bounded live check of the page download through the worker (Stage 10, TP-PM-21).
#
# Disposable test database only, after the Partner Monitor tests installed the
# module there:
#
#     scripts/dev.sh shell azk_ee24_test < scripts/pm_live_check.py
#
# It reads the live https://www.odoo.com public pages through the real cron
# entry point (worker._cron_process_queue), services/http_client.py and the
# real parsers and ingestion:
#   1. robots.txt, once, read directly: every URL the check requests must be
#      allowed by its rules for all crawlers;
#   2. batch 1 (one unit): the country list, the first unit of a full sync;
#   3. every queued country unit except Andorra's is cancelled;
#   4. batch 2 (two units): Andorra's listing, then the first partner page that
#      unit queued.
# A hard budget of 8 HTTP requests (redirects and retries included) and the
# client's spacing of at least 3 s apply. It prints the requests, the units,
# the stored rows and the timings, and finally ROLLS BACK: nothing is kept.
#
# Stage 11 acceptance option: keep the sample in another disposable database,
# for the demonstration (environment variables, so docker compose run -e):
#   PM_LIVE_KEEP=1                commit instead of rolling back;
#   PM_LIVE_DB_CREATED_AFTER=DATE allow a database other than azk_ee24_test if
#                                 it was created on or after DATE (YYYY-MM-DD).
#                                 The acceptance database has the same name as
#                                 the development database (azk_ee24) in another
#                                 Compose project, so the name cannot be the guard.
import os
import re
import sys
import time
from unittest.mock import patch
from urllib.parse import urlsplit

import requests

from odoo.addons.azk_odoo_partner_monitor.models.worker import BATCH_SIZE_PARAM, PartnerMonitorWorker
from odoo.addons.azk_odoo_partner_monitor.services import http_client, urls

KEEP = os.environ.get("PM_LIVE_KEEP") == "1"
if env.cr.dbname != "azk_ee24_test":
    created_after = os.environ.get("PM_LIVE_DB_CREATED_AFTER", "")
    created_on = str(env.ref("base.user_root").create_date.date())
    if not created_after or created_on < created_after:
        sys.exit(f"refusing to run on {env.cr.dbname} (created on {created_on}): azk_ee24_test only, "
                 "or a database created on or after PM_LIVE_DB_CREATED_AFTER")
MAX_REQUESTS = 8
LOG_PREFIX = "PM_LIVE"


def out(*parts):
    print(LOG_PREFIX, *parts, flush=True)


class BudgetClient(http_client.PartnersHttpClient):
    """The real client, with a hard limit on the number of HTTP requests."""

    def _attempt(self, url):
        if len(self.log) >= MAX_REQUESTS:
            raise http_client.FetchError(f"request budget of {MAX_REQUESTS} used", url)
        return super()._attempt(url)


def robots_rules(text):
    """Allow and Disallow rules of the 'User-agent: *' groups, as (kind, pattern)."""
    rules, agents, in_rules = [], [], False
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if ":" not in line:
            continue
        key, value = (part.strip() for part in line.split(":", 1))
        key = key.lower()
        if key == "user-agent":
            if in_rules:
                agents, in_rules = [], False
            agents.append(value)
        elif key in ("allow", "disallow"):
            in_rules = True
            if "*" in agents and value:
                rules.append((key, value))
    return rules


def robots_verdict(rules, url):
    """None if ``url`` is allowed, else the Disallow rule (longest match wins, Allow on ties)."""
    parts = urlsplit(url)
    target = parts.path + (f"?{parts.query}" if parts.query else "")
    best = None
    for kind, pattern in rules:
        regex = re.escape(pattern).replace(r"\*", ".*")
        if regex.endswith(r"\$"):
            regex = regex[:-2] + "$"
        if re.match(regex, target):
            key = (len(pattern), kind == "allow")
            if best is None or key > best[0]:
                best = (key, kind, pattern)
    return best[2] if best and best[1] == "disallow" else None


Worker = env["azk_odoo_partner_monitor.worker"]
WorkItem = env["azk_odoo_partner_monitor.work.item"]
Country = env["azk_odoo_partner_monitor.country"].with_context(active_test=False)
Partner = env["azk_odoo_partner_monitor.partner"].with_context(active_test=False)
ICP = env["ir.config_parameter"].sudo()
client = BudgetClient()
out("start", time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()), "database", env.cr.dbname)
out("page source without the patch:", type(Worker._get_page_source()).__name__)

# 1. robots.txt (plain text, so not through the HTML client).
started = time.monotonic()
answer = requests.get(f"{urls.SITE}/robots.txt", timeout=(5, 20), allow_redirects=False,
                      headers={**http_client.REQUEST_HEADERS, "Accept": "text/plain"})
rules = robots_rules(answer.text)
out(f"robots.txt: HTTP {answer.status_code}, {len(answer.content)} bytes, {time.monotonic() - started:.2f} s, "
    f"{len(rules)} rules for all crawlers")
for pattern in sorted({p for kind, p in rules if kind == "disallow"
                       and re.search(r"country_id|grade_id|page|search|order", p)}):
    out("  disallow", pattern)
for url in (urls.COUNTRY_LIST_URL, urls.listing_url("1")):
    verdict = robots_verdict(rules, url)
    out("  planned", url, "->", verdict or "allowed")
    assert answer.status_code == 200 and rules, "robots.txt could not be read: stopping before any page"
    assert not verdict, f"robots.txt now disallows {url} ({verdict}): stopping before any page"
time.sleep(http_client.MIN_INTERVAL)

# 2-4. Two worker batches through the cron entry point.
run = env["azk_odoo_partner_monitor.sync.run"]._queue_full_sync("manual")
out("queued", run.display_name, "units", WorkItem.search_count([("run_id", "=", run.id)]))
previous_batch_size = ICP.get_param(BATCH_SIZE_PARAM)
with patch.object(PartnerMonitorWorker, "_get_page_source", lambda worker: client):
    ICP.set_param(BATCH_SIZE_PARAM, "1")
    started = time.monotonic()
    first = Worker._cron_process_queue()
    out(f"batch 1: {time.monotonic() - started:.2f} s, processed {first['processed']}, "
        f"done {first['done']}, failed {first['failed']}, remaining {first['remaining']}")
    andorra = Country.search([("source_key", "=", "1"), ("is_demo", "=", False)])
    others = WorkItem.search([("run_id", "=", run.id), ("state", "=", "pending"),
                              ("kind", "=", "country_partners"), ("country_id", "!=", andorra.id)])
    out("countries from the live list:", Country.search_count([("is_demo", "=", False)]),
        "queued country units:", len(others) + 1, "- cancelling all but Andorra's:", len(others))
    others.write({"state": "cancelled"})
    ICP.set_param(BATCH_SIZE_PARAM, "2")
    started = time.monotonic()
    second = Worker._cron_process_queue()
    out(f"batch 2: {time.monotonic() - started:.2f} s, processed {second['processed']}, "
        f"done {second['done']}, failed {second['failed']}, remaining {second['remaining']}")
# The batch sizes above are for this check only: put the setting back, so that
# a kept sample (PM_LIVE_KEEP=1) leaves no tuning behind (found in Stage 11).
ICP.set_param(BATCH_SIZE_PARAM, previous_batch_size or False)

for entry in client.log:
    out(f"request {entry['status']} {entry['bytes']:>7} bytes {entry['seconds']:>6.2f} s {entry['url']} "
        f"-> {robots_verdict(rules, entry['url']) or 'allowed by robots.txt'}")
out("requests:", len(client.log), "of at most", MAX_REQUESTS)
for item in WorkItem.search([("run_id", "=", run.id), ("state", "!=", "cancelled")], order="id"):
    target = item.country_id.name or item.partner_id.name or ""
    out(f"unit {item.kind} {target!r}: {item.state}, tries {item.attempt_count}, "
        f"{item.result_summary or item.last_error or ''}")
out(f"Andorra: listed {andorra.total_partner_count}, stored {andorra.partner_count}, "
    f"validation {andorra.validation_state}, to re-scrape {andorra.to_reprocess_partners}")
for partner in Partner.search([("country_id", "=", andorra.id)], order="source_id"):
    out(f"partner {partner.source_id} {partner.name!r} {partner.current_status} first seen {partner.first_seen_on} "
        f"retention {partner.retention_rate if partner.retention_rate_known else 'unknown'} "
        f"references listed {partner.total_references_count} stored {len(partner.reference_ids)} "
        f"history {len(partner.status_history_ids)} url {partner.partner_url}")
errors = env["azk_odoo_partner_monitor.sync.error"].search([("run_id", "=", run.id)])
out("error rows:", len(errors), [f"{error.error_class}: {error.message}" for error in errors])
if KEEP:
    env.cr.commit()
    out("committed (PM_LIVE_KEEP=1): the sample is kept in", env.cr.dbname, "as run", run.id)
else:
    env.cr.rollback()
    out("rolled back; units left in the database for this run:", WorkItem.search_count([("run_id", "=", run.id)]))
