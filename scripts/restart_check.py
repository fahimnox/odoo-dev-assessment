# Partner Monitor restart check (test plan TP-PM-15, docs/resilience.md).
#
# Run by scripts/restart_check.sh, never directly: it is piped into
# "odoo shell" on the disposable test database, once per phase, and reads the
# phase from the PM_PHASE environment variable (env and odoo are provided by
# the shell):
#   setup   seed the queue and commit it
#   crash   run the real worker job through the scheduler's own functions;
#           batch 1 commits, batch 2 blocks inside a page read until the
#           harness kills the container
#   resume  run the same job again in a new process
#   verify  check the stored result and print PASS or FAIL per check
#
# Pages come from the saved live-derived fixtures (tests/common.py,
# FixtureSite), so the check is repeatable and never contacts the website.

import os
import sys
import time
from datetime import date, timedelta
from unittest.mock import patch

import odoo
from odoo import fields
from odoo.addons.azk_odoo_partner_monitor.models.sync_run import NOTIFY_USER_PARAM
from odoo.addons.azk_odoo_partner_monitor.models.worker import BATCH_SIZE_PARAM
from odoo.addons.azk_odoo_partner_monitor.services import parsers, urls

# This script is a test harness, so it reuses the tests' fixture-backed fetch.
# Odoo logs an error when the test framework is imported outside test mode (a
# guard meant for business code), so test mode is declared around this import
# only. The registry is already loaded, so no test runs.
odoo.tools.config["test_enable"] = True
try:
    from odoo.addons.azk_odoo_partner_monitor.tests.common import (
        ALL_PAGES, ANDORRA, EGYPT_P1, EGYPT_P11, ROAYATEC, FixtureSite, andorra_variant, fixture)
finally:
    odoo.tools.config["test_enable"] = False

PHASE = os.environ.get("PM_PHASE", "")
TAG = "PM-RESTART:"
WORKER_CRON = "azk_odoo_partner_monitor.ir_cron_worker"
INBOX_LOGIN = "pm_restart_inbox"

if not env.cr.dbname.endswith("_test"):  # noqa: F821 (provided by odoo shell)
    sys.exit(f"{TAG} refusing to run on {env.cr.dbname}: a disposable *_test database is required")  # noqa: F821

Country = env["azk_odoo_partner_monitor.country"].with_context(active_test=False)  # noqa: F821
Partner = env["azk_odoo_partner_monitor.partner"].with_context(active_test=False)  # noqa: F821
Run = env["azk_odoo_partner_monitor.sync.run"]  # noqa: F821
WorkItem = env["azk_odoo_partner_monitor.work.item"]  # noqa: F821
Worker = env["azk_odoo_partner_monitor.worker"]  # noqa: F821


def say(text):
    print(f"{TAG} {text}", flush=True)


def describe(unit):
    target = unit.country_id.name or unit.partner_id.name
    return f"unit {unit.id} ({unit.kind}: {target}, run {unit.run_id.id})"


# ---------------------------------------------------------------- setup

def setup():
    if Run.search_count([]):
        sys.exit(f"{TAG} this database already has sync runs; recreate it with scripts/dev.sh test")
    users = env["res.users"].with_context(active_test=False)  # noqa: F821
    inbox = users.search([("login", "=", INBOX_LOGIN)]) or users.create({
        "name": "Restart Check Inbox", "login": INBOX_LOGIN, "notification_type": "inbox",
        "groups_id": [(6, 0, [env.ref("base.group_user").id])]})  # noqa: F821
    params = env["ir.config_parameter"].sudo()  # noqa: F821
    params.set_param(NOTIFY_USER_PARAM, str(inbox.id))  # an Inbox user: no email is queued
    params.set_param(BATCH_SIZE_PARAM, "2")
    now = fields.Datetime.now()
    NewRun = Run.with_context(mail_create_nolog=True, mail_create_nosubscribe=True)  # as the jobs do
    ingest = env["azk_odoo_partner_monitor.ingest"]  # noqa: F821
    andorra = Country._record_observation({"source_key": "1", "name": "Andorra", "total_partner_count": 2})
    anguilla = Country._record_observation({"source_key": "5", "name": "Anguilla", "total_partner_count": 1})
    egypt = Country._record_observation({"source_key": "64", "name": "Egypt", "total_partner_count": 210})
    # Data stored by earlier scrapes:
    # - Andorra's two partners, seen on 2026-11-01 as Ready, with their pages
    #   marked as read then (no saved page exists for them);
    # - an Anguilla partner;
    # - Egypt's first and last saved pages (an incomplete snapshot).
    andorra_pages = [parsers.parse_listing_page(fixture(ANDORRA[1]), ANDORRA[0], "1")]
    ingest._ingest_country_listing(andorra, andorra_pages, date(2026, 11, 1), now=now)
    Partner.search([("country_id", "=", andorra.id)]).write({"details_synced_at": now})
    Partner._record_observation({"source_id": 990201, "name": "Earlier Anguilla partner",
                                 "current_status": "ready", "country_id": anguilla.id}, "2026-10-01")
    pages = [parsers.parse_listing_page(fixture(name), url, "64") for url, name in (EGYPT_P1, EGYPT_P11)]
    ingest._ingest_country_listing(egypt, pages, now.date(), now=now)
    roayatec = Partner.search([("source_id", "=", 17207720)])
    devoneers = Partner.search([("source_id", "=", 32297621)])
    # Run A: one Egypt listing unit that has already failed 4 times (its
    # pages 2 to 10 are not saved). Its 5th and last try comes in batch 1.
    run_a = NewRun.create({"trigger": "validation"})
    WorkItem.create({"kind": "country_partners", "run_id": run_a.id, "country_id": egypt.id,
                     "attempt_count": 4, "next_attempt_at": now - timedelta(hours=1),
                     "last_error": "LookupError: (seeded) 4 earlier tries failed"})
    # Run B: two country listings and two partner pages.
    run_b = NewRun.create({"trigger": "manual"})
    for country in (andorra, anguilla):
        WorkItem._enqueue("country_partners", run_b, country=country)
    for partner in (roayatec, devoneers):
        WorkItem._enqueue("partner_details", run_b, partner=partner)
    env.cr.commit()  # noqa: F821
    say(f"seeded run {run_a.id} (1 unit, 4 tries used) and run {run_b.id} (4 units); "
        f"batch size 2; failure notes go to the Inbox user {INBOX_LOGIN}")


# ---------------------------------------------------------------- the worker job

class BlockingSite(FixtureSite):
    """The saved pages, with BDR GROUP SLU promoted to Silver on Andorra's
    listing (a variant made in code). In the crash phase, reading
    ``block_url`` never returns."""

    def __init__(self, block_url=None):
        super().__init__(ALL_PAGES, html={
            urls.listing_url("1"): andorra_variant(statuses={22015187: "Silver"})})
        self.block_url = block_url

    def __call__(self, url):
        if url == self.block_url:
            say(f"blocked while reading {url} (batch 2, not committed); waiting to be killed")
            time.sleep(600)
            raise TimeoutError("the restart check expected to be killed here")
        return super().__call__(url)


def run_worker_job(site):
    """Run the worker job exactly as the scheduler does: _acquire_one_job, then
    _process_job (which calls _run_job: up to 10 callbacks, committing before
    and after each). Only the page source is replaced, by the saved pages."""
    WorkerClass = type(Worker)
    original_process = WorkerClass._process_queue
    original_run_unit = WorkerClass._run_unit
    batches = []

    def process_queue(worker, fetch, **kwargs):
        batches.append(len(batches) + 1)
        say(f"batch {batches[-1]} starts")
        result = original_process(worker, fetch, **kwargs)
        say(f"batch {batches[-1]} returns: {result['processed']} processed, {result['remaining']} "
            f"due units remaining; the scheduler commits now")
        return result

    def run_unit(worker, item, fetch, now):
        done = original_run_unit(worker, item, fetch, now)
        say(f"batch {batches[-1]}: {describe(item)} -> {'done' if done else 'failed try'}")
        return done

    cron = env.ref(WORKER_CRON)  # noqa: F821
    cron._trigger()
    env.cr.commit()  # noqa: F821 - the trigger must be visible to the scheduler's cursor
    IrCron = env.registry["ir.cron"]  # noqa: F821
    db = odoo.sql_db.db_connect(env.cr.dbname)  # noqa: F821
    with patch.object(WorkerClass, "_get_page_source", lambda worker: site), \
            patch.object(WorkerClass, "_process_queue", process_queue), \
            patch.object(WorkerClass, "_run_unit", run_unit), \
            db.cursor() as cron_cr:
        job = IrCron._acquire_one_job(cron_cr, cron.id)
        if not job:
            sys.exit(f"{TAG} the worker job is not ready or is locked by another process")
        say(f"worker job acquired (last progress: done {job['done']}, timed_out_counter "
            f"{job['timed_out_counter']})")
        IrCron._process_job(db, cron_cr, job)
    say(f"worker job finished after {len(batches)} batches; pages read: {', '.join(site.requested)}")


# ---------------------------------------------------------------- verify

def verify():
    env.invalidate_all()  # noqa: F821
    failures = []

    def check(label, condition, detail=""):
        print(f"{TAG} {'PASS' if condition else 'FAIL'} {label}{(': ' + detail) if detail else ''}", flush=True)
        if not condition:
            failures.append(label)

    run_a, run_b = Run.search([], order="id")
    units = {(unit.kind, (unit.country_id.source_key or unit.partner_id.source_id)): unit
             for unit in WorkItem.search([])}
    egypt_unit = units[("country_partners", "64")]
    check("batch 1's failed unit was not run again", egypt_unit.state == "failed"
          and egypt_unit.attempt_count == 5 and len(egypt_unit.error_ids) == 1,
          f"state {egypt_unit.state}, tries {egypt_unit.attempt_count}, error rows {len(egypt_unit.error_ids)}")
    bdr = Partner.search([("source_id", "=", 22015187)])
    history = bdr.status_history_ids.sorted("id")
    check("batch 1's promotion of BDR GROUP SLU is recorded once",
          history.mapped("change_type") == ["initial", "promoted"] and bdr.current_status == "silver",
          f"history {history.mapped('change_type')}")
    check("batch 1's Andorra unit was not run again", units[("country_partners", "1")].state == "done"
          and Partner.search_count([("country_id.source_key", "=", "1")]) == 2)
    replayed = [units[("country_partners", "5")], units[("partner_details", 17207720)]]
    check("the interrupted batch was replayed once and finished",
          all(unit.state == "done" and unit.attempt_count == 0 for unit in replayed),
          ", ".join(f"{describe(unit)} {unit.state}, tries {unit.attempt_count}" for unit in replayed))
    earlier = Partner.search([("source_id", "=", 990201)])
    check("the replayed Anguilla unit archived the earlier partner, without a history row",
          not earlier.active and len(earlier.status_history_ids) == 1)
    roayatec = Partner.search([("source_id", "=", 17207720)])
    check("RoayaTec has its 3 saved references once", roayatec.active_reference_count == 3
          and len(roayatec.reference_ids) == 3, f"{len(roayatec.reference_ids)} reference rows")
    partners = Partner.search([("is_demo", "=", False)])
    rows = partners.status_history_ids
    check("no duplicate status history: one initial row per partner, plus the one promotion",
          len(rows.filtered(lambda row: row.change_type == "initial")) == len(partners)
          and len(rows) == len(partners) + 1,
          f"{len(partners)} partners, {len(rows)} history rows")
    check("run A ended failed with exactly one note", run_a.state == "failed"
          and len(run_a.message_ids.filtered(lambda m: m.message_type == "comment")) == 1)
    notifications = env["mail.notification"].search(  # noqa: F821
        [("mail_message_id", "in", run_a.message_ids.ids)])
    check("the note reached the Inbox user once", len(notifications) == 1
          and notifications.notification_type == "inbox"
          and notifications.res_partner_id.user_ids.login == INBOX_LOGIN)
    check("run B ended done, without a note", run_b.state == "done"
          and not run_b.message_ids.filtered(lambda m: m.message_type == "comment"))
    check("no unit is left pending", not WorkItem.search_count([("state", "=", "pending")]))
    check("no email was queued", not env["mail.mail"].search_count(  # noqa: F821
        [("model", "=", "azk_odoo_partner_monitor.sync.run")]))
    say(f"{'all checks passed' if not failures else str(len(failures)) + ' checks failed'}")
    if failures:
        sys.exit(1)


if PHASE == "setup":
    setup()
elif PHASE == "crash":
    run_worker_job(BlockingSite(block_url=ROAYATEC[0]))
elif PHASE == "resume":
    run_worker_job(BlockingSite())
elif PHASE == "verify":
    verify()
else:
    sys.exit(f"{TAG} unknown phase {PHASE!r}")
