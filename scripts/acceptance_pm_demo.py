"""Partner Monitor acceptance demonstration (Stage 11). COMMITTED, disposable databases only.

    docker compose run --rm -T -e PM_DEMO_PHASE=prepare -e ACC_DB_CREATED_AFTER odoo-ee-20241208 \
        odoo shell --database=azk_ee24 --no-http < scripts/acceptance_pm_demo.py

Run the phases in this order, before the web server starts (its scheduled jobs
would otherwise mark the run as waiting between the phases):

  prepare  Through the Settings form's own code (res.config.settings): tick
           Pause Website Downloads, so that only these phases read the website,
           and make acc_pm_manager (scripts/acceptance_users.py) the recipient
           of sync notes.
  (then)   scripts/pm_live_check.py with PM_LIVE_KEEP=1: a bounded LIVE sample
           (country list, Andorra, one partner page), kept.
  fail     A simulated network outage (NO request is sent: the page source
           raises the client's own FetchConnectionError) on the partner page the
           sample left queued. The worker tries it 5 times on a simulated clock
           (each try when its retry delay has passed, 15 to 120 minutes apart,
           so the times stored for these tries are in the future), then marks
           it failed; the run ends partial and its note goes to the recipient.
  recover  acc_pm_manager clicks Retry (work_item.action_retry, as that user),
           then the real worker job reads the page from the LIVE website with
           at most 2 requests. The run ends done and is not notified again.

Each phase prints the stored state; "LIVE" and "SIMULATED" say where data came
from. Guard: the database must have been created on or after
ACC_DB_CREATED_AFTER (YYYY-MM-DD), because the acceptance database has the
development database's name in another Compose project.
"""
import os
import sys
from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.addons.azk_odoo_partner_monitor.models.common import MAX_ATTEMPTS
from odoo.addons.azk_odoo_partner_monitor.models.worker import PartnerMonitorWorker
from odoo.addons.azk_odoo_partner_monitor.services import http_client

# `env` is provided by the Odoo shell.
PHASE = os.environ.get("PM_DEMO_PHASE", "")
created_after = os.environ.get("ACC_DB_CREATED_AFTER", "")
created_on = str(env.ref("base.user_root").create_date.date())  # noqa: F821
if not created_after or created_on < created_after:
    sys.exit(f"refusing to run on {env.cr.dbname}: created on {created_on}, not after ACC_DB_CREATED_AFTER")  # noqa: F821
if PHASE not in ("prepare", "fail", "recover"):
    sys.exit("PM_DEMO_PHASE must be prepare, fail or recover")

Run = env["azk_odoo_partner_monitor.sync.run"]  # noqa: F821
WorkItem = env["azk_odoo_partner_monitor.work.item"]  # noqa: F821
Worker = env["azk_odoo_partner_monitor.worker"]  # noqa: F821
Partner = env["azk_odoo_partner_monitor.partner"].with_context(active_test=False)  # noqa: F821
manager = env["res.users"].search([("login", "=", "acc_pm_manager")])  # noqa: F821
MAX_REQUESTS = 2


def out(*parts):
    print("PM_DEMO", *parts, flush=True)


def show_run(run):
    run.invalidate_recordset()
    out(f"run {run.id} ({run.trigger}): state {run.state}, waiting {run.waiting_reason or '-'}, "
        f"finished {run.finished_at or '-'}, notified {run.notified_at or '-'}")
    for item in run.work_item_ids.filtered(lambda i: i.state != "cancelled").sorted("id"):
        target = item.country_id.name or item.partner_id.name or ""
        out(f"  unit {item.id} {item.kind} {target!r}: {item.state}, tries {item.attempt_count}, "
            f"{item.result_summary or item.last_error or ''}"[:220])
    out(f"  cancelled units (the live sample keeps Andorra only): "
        f"{len(run.work_item_ids.filtered(lambda i: i.state == 'cancelled'))}")
    for message in run.message_ids.filtered(lambda m: m.message_type == "comment").sorted("id"):
        out(f"  note {message.id} by {message.author_id.name!r} to {message.partner_ids.mapped('name')}: "
            f"{message.preview[:200]!r}")
        for notification in message.notification_ids:
            out(f"    notification for {notification.res_partner_id.name!r}: type "
                f"{notification.notification_type}, status {notification.notification_status}, "
                f"read {notification.is_read}")


def show_website_partners():
    for partner in Partner.search([("is_demo", "=", False)], order="source_id"):
        out(f"LIVE partner {partner.source_id} {partner.name!r}: {partner.current_status}, active "
            f"{partner.active}, details read {partner.details_synced_at or 'never'}, references listed "
            f"{partner.total_references_count}, stored active {partner.active_reference_count}, "
            f"validation {partner.reference_validation_state}, history rows {len(partner.status_history_ids)}")


class BudgetClient(http_client.PartnersHttpClient):
    """The real client, with a hard limit on the number of HTTP requests."""

    def _attempt(self, url):
        if len(self.log) >= MAX_REQUESTS:
            raise http_client.FetchError(f"request budget of {MAX_REQUESTS} used", url)
        return super()._attempt(url)


def outage(url):
    """Page source during a simulated network outage: no request is sent."""
    raise http_client.FetchConnectionError(
        "SIMULATED network outage (Stage 11 acceptance demonstration): no request was sent", url)


if PHASE == "prepare":
    if not manager:
        sys.exit("acc_pm_manager does not exist: run scripts/acceptance_users.py first")
    settings = env["res.config.settings"].create({  # noqa: F821
        "partner_monitor_downloads_paused": True,
        "partner_monitor_notify_user_id": manager.id,
    })
    settings.execute()
    ICP = env["ir.config_parameter"].sudo()  # noqa: F821
    out("Settings saved: Pause Website Downloads =",
        ICP.get_param("azk_odoo_partner_monitor.downloads_paused"),
        "; notification recipient =", Run._get_failure_recipient().login)
    out("page source now:", Worker._get_page_source())
    # The Odoo shell rolls back at the end: without this commit the settings
    # are lost (the first Stage 11 run of this phase had no commit).
    env.cr.commit()  # noqa: F821
    out("committed")

elif PHASE == "fail":
    item = WorkItem.search([("state", "=", "pending"), ("kind", "=", "partner_details")], order="id", limit=1)
    if not item:
        # No page is left queued by the live sample: as a manager would, ask
        # for a re-scrape of the first live partner whose page was read, then
        # let the reference-validation job queue it (in a validation run).
        partner = Partner.search([("is_demo", "=", False), ("details_synced_at", "!=", False)],
                                 order="source_id", limit=1)
        if not partner:
            sys.exit("no live partner with a read page: run scripts/pm_live_check.py with PM_LIVE_KEEP=1 first")
        out(f"{manager.login} marks LIVE partner {partner.name!r} for a re-scrape (partner.action_mark_for_rescrape)")
        partner.with_user(manager).action_mark_for_rescrape()
        item = Worker._cron_validate_references().filtered(lambda unit: unit.partner_id == partner)[:1]
        if not item:
            sys.exit("the reference-validation job queued nothing")
        out(f"the reference-validation job queued unit {item.id} in run {item.run_id.id} ({item.run_id.trigger})")
    run = item.run_id
    out("before the outage:")
    show_run(run)
    show_website_partners()
    now = fields.Datetime.now()
    for attempt in range(1, MAX_ATTEMPTS + 1):
        result = Worker._process_queue(outage, max_units=1, now=now)
        item.invalidate_recordset()
        out(f"SIMULATED try {attempt} at {now} (simulated clock): processed {result['processed']}, "
            f"unit {item.state}, tries {item.attempt_count}, next try {item.next_attempt_at if item.state == 'pending' else '-'}")
        if item.state != "pending":
            break
        now = item.next_attempt_at + timedelta(seconds=1)
    out("after the outage:")
    show_run(run)
    show_website_partners()
    out("sync error rows of the run:", len(run.error_ids) if "error_ids" in run else
        env["azk_odoo_partner_monitor.sync.error"].search_count([("run_id", "=", run.id)]))  # noqa: F821
    env.cr.commit()  # noqa: F821
    out("committed")

elif PHASE == "recover":
    failed = WorkItem.search([("state", "=", "failed"), ("kind", "=", "partner_details")], order="id")
    if not failed:
        sys.exit("no failed partner page: run the fail phase first")
    run = failed.run_id
    out(f"Retry as {manager.login} (manager action work_item.action_retry) on units {failed.ids}")
    failed.with_user(manager).action_retry()
    show_run(run)
    client = BudgetClient()
    with patch.object(PartnerMonitorWorker, "_get_page_source", lambda worker: client):
        result = Worker._cron_process_queue()
    out(f"worker job: processed {result['processed']}, done {result['done']}, failed {result['failed']}, "
        f"remaining {result['remaining']}")
    for entry in client.log:
        out(f"LIVE request {entry['status']} {entry['bytes']} bytes {entry['seconds']:.2f} s {entry['url']}")
    out("LIVE requests:", len(client.log), "of at most", MAX_REQUESTS)
    show_run(run)
    show_website_partners()
    env.cr.commit()  # noqa: F821
    out("committed")
