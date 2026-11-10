"""The sync engine: the four cron entry points, the queue worker and its units.

Unit of work: one work item (the country list, one country's listing, or one
partner's page). Transaction story (docs/resilience.md):

- The scheduler (odoo/addons/base/models/ir_cron.py, _run_job) commits before
  and after each call of the worker job, up to 10 calls per run of the job.
  That commit is the only durability point: nothing here commits.
- One call processes one bounded batch: at most ``max_units`` units, and no
  new unit after ``time_budget`` seconds.
- Each unit is claimed with a row lock (FOR NO KEY UPDATE SKIP LOCKED) that
  lasts until the batch's transaction ends, and runs in its own savepoint.
  A failing unit rolls back to its savepoint only; its failure is recorded
  after that rollback, in the same transaction, and is committed with the
  batch. A crash rolls back the whole batch, so its units are pending again
  and are replayed; batches committed earlier are never repeated.
"""

import logging
import time
import traceback
from datetime import timedelta

import psycopg2

from odoo import api, fields, models
from odoo.tools import SQL

from ..services import reader
from .common import MAX_ATTEMPTS, retry_delay

_logger = logging.getLogger(__name__)

BATCH_SIZE_PARAM = "azk_odoo_partner_monitor.worker_batch_size"
TIME_BUDGET_PARAM = "azk_odoo_partner_monitor.worker_time_budget"
DEFAULT_BATCH_SIZE = 20
DEFAULT_TIME_BUDGET = 60  # seconds; the scheduler's real-time limit must exceed it plus the longest unit
STALE_DETAILS_AFTER = timedelta(days=7)
STALE_DETAILS_PER_RUN = 200
NO_PAGE_SOURCE = ("no page source is available (the page-download module is not installed; "
                  "Stage 04 is partial)")
# The country list feeds the country units, which feed the partner units.
KIND_ORDER = SQL("CASE kind WHEN 'country_list' THEN 0 WHEN 'country_partners' THEN 1 ELSE 2 END")


class _UrlTracker:
    """Wraps a fetch callable and remembers the last URL asked for, for error context."""

    def __init__(self, fetch):
        self.fetch = fetch
        self.last_url = None

    def __call__(self, url):
        self.last_url = url
        return self.fetch(url)


def _config_number(env, key, default):
    value = env["ir.config_parameter"].sudo().get_param(key) or ""
    try:
        number = float(value)
    except ValueError:
        return default
    return number if number > 0 else default


class PartnerMonitorWorker(models.AbstractModel):
    _name = "azk_odoo_partner_monitor.worker"
    _description = "Partner Monitor Sync Worker"

    # ------------------------------------------------------------------
    # Page source: integration point of the deferred page-download module
    # ------------------------------------------------------------------

    @api.model
    def _get_page_source(self):
        """Return the page source, a ``fetch(url)`` callable, or None when there is none.

        Contract (services/reader.py): ``fetch(url)`` returns
        ``(final_url, html)``, the URL after redirects and the page text, and
        RAISES on any failure: timeout, connection error, HTTP error, login or
        rate-limit page. A failure must never come back as an empty page.

        The requests-based module (services/http_client.py) is deferred
        (Stage 04 PARTIAL), so this returns None: the worker then keeps every
        unit queued and marks the open runs as waiting. Tests replace this
        method with a fixture-backed fetch (tests/common.py, FixtureSite).
        """
        return None

    # ------------------------------------------------------------------
    # Cron entry points (data/ir_cron.xml). Producers only enqueue.
    # ------------------------------------------------------------------

    @api.model
    def _cron_daily_discovery(self):
        """Daily job (P-04): queue a full sync and wake the worker. Never scrapes."""
        run = self.env["azk_odoo_partner_monitor.sync.run"]._queue_full_sync("daily")
        if run:
            _logger.info("Partner Monitor: %s queued its country list.", run.display_name)
        else:
            _logger.info("Partner Monitor: a full sync is already queued; nothing more was queued.")
        self.env["azk_odoo_partner_monitor.work.item"]._trigger_worker()
        return run

    @api.model
    def _cron_process_queue(self):
        """Worker job: one bounded batch per scheduler call, then report progress.

        With units left and progress made, the scheduler calls again at once
        (up to 10 times), committing after each call. Without progress (no
        page source, or every due unit locked by another worker) it reports
        nothing done, which the scheduler treats as finished: no tight loop.
        """
        result = self._process_queue(
            self._get_page_source(),
            max_units=int(_config_number(self.env, BATCH_SIZE_PARAM, DEFAULT_BATCH_SIZE)),
            time_budget=_config_number(self.env, TIME_BUDGET_PARAM, DEFAULT_TIME_BUDGET))
        self.env["ir.cron"]._notify_progress(done=result["processed"], remaining=result["remaining"])
        return result

    @api.model
    def _cron_validate_countries(self, now=None):
        """Country-validation job (P-19): re-scrape flagged countries, with bounded retries.

        A flagged country gets one queued listing unit (de-duplicated) when its
        next try is due and fewer than MAX_ATTEMPTS were used for the current
        mismatch. Each queued try is counted and pushes the next one back
        (common.retry_delay). A match clears the flag and the count
        (country._record_validation); a mismatch that never clears stops
        after the last try and stays visible (reprocess_exhausted).
        """
        now = now or fields.Datetime.now()
        # "Not exhausted" rather than "attempts < 5": the boolean test also
        # matches rows whose count is still NULL (regression test
        # test_flag_without_a_retry_count_is_still_validated).
        countries = self.env["azk_odoo_partner_monitor.country"].search([
            ("to_reprocess_partners", "=", True), ("is_demo", "=", False),
            ("reprocess_exhausted", "=", False),
            "|", ("next_reprocess_at", "=", False), ("next_reprocess_at", "<=", now),
        ])
        return self._queue_validation("country_partners", countries, now, counted=countries)

    @api.model
    def _cron_validate_references(self, now=None):
        """Reference-validation job (P-21): re-read flagged partners' pages, with bounded retries.

        Flagged partners are handled like flagged countries. In addition, the
        pages read the longest ago, more than 7 days back, are re-read (at most
        STALE_DETAILS_PER_RUN per call): a matching count does not prove that
        the references themselves are unchanged. These periodic re-reads use
        no retry budget.
        """
        now = now or fields.Datetime.now()
        Partner = self.env["azk_odoo_partner_monitor.partner"]
        flagged = Partner.search([
            ("to_reprocess_references", "=", True), ("is_demo", "=", False),
            ("reprocess_exhausted", "=", False),
            "|", ("next_reprocess_at", "=", False), ("next_reprocess_at", "<=", now),
        ])
        stale = Partner.search([
            ("to_reprocess_references", "=", False), ("is_demo", "=", False),
            ("details_synced_at", "!=", False), ("details_synced_at", "<", now - STALE_DETAILS_AFTER),
        ], order="details_synced_at, id", limit=STALE_DETAILS_PER_RUN)
        return self._queue_validation("partner_details", flagged | stale, now, counted=flagged)

    @api.model
    def _queue_validation(self, kind, targets, now, counted):
        """Queue one unit per target that has none pending, all in one validation run.

        Returns the queued work items. Each queued target in ``counted`` uses
        one try of its retry budget. A target whose unit is already pending
        (from any run) is skipped and uses no try: duplicate scheduling never
        adds work.
        """
        WorkItem = self.env["azk_odoo_partner_monitor.work.item"]
        field = "country_id" if kind == "country_partners" else "partner_id"
        pending = WorkItem.search([("state", "=", "pending"), ("kind", "=", kind),
                                   (field, "in", targets.ids)])[field]
        todo = targets - pending
        if not todo:
            return WorkItem
        run = self.env["azk_odoo_partner_monitor.sync.run"].with_context(
            mail_create_nolog=True, mail_create_nosubscribe=True).create({"trigger": "validation"})
        queued = WorkItem
        for target in todo:
            item = WorkItem._enqueue(kind, run, **{field.removesuffix("_id"): target})
            if item.run_id != run:
                continue  # queued by another transaction at the same moment
            queued |= item
            if target in counted:
                attempts = target.reprocess_attempts + 1
                target.write({"reprocess_attempts": attempts,
                              "next_reprocess_at": now + retry_delay(attempts)})
        if not queued:
            run.unlink()
            return queued
        _logger.info("Partner Monitor: %s queued %s %s units.", run.display_name, len(queued), kind)
        WorkItem._trigger_worker()
        return queued

    # ------------------------------------------------------------------
    # The worker
    # ------------------------------------------------------------------

    @api.model
    def _process_queue(self, fetch, max_units=DEFAULT_BATCH_SIZE, time_budget=DEFAULT_TIME_BUDGET,
                       now=None):
        """Process one bounded batch of due units with ``fetch`` (see _get_page_source).

        Returns a summary: processed (done + failed tries), the done and
        failed item ids, the due units remaining, and whether the batch was
        waiting for a page source. Never commits.
        """
        now = now or fields.Datetime.now()
        WorkItem = self.env["azk_odoo_partner_monitor.work.item"]
        Run = self.env["azk_odoo_partner_monitor.sync.run"]
        if fetch is None:
            return self._wait_for_page_source(now)
        Run.search([("state", "=", "running"), ("waiting_reason", "!=", False)]).write(
            {"waiting_reason": False})
        started = time.monotonic()
        done = failed = WorkItem
        while len(done) + len(failed) < max_units and time.monotonic() - started < time_budget:
            item = self._claim_next(now)
            if not item:
                break
            if self._run_unit(item, fetch, now):
                done |= item
            else:
                failed |= item
        Run._finalize_finished(now)
        remaining = WorkItem.search_count([("state", "=", "pending"), ("next_attempt_at", "<=", now)])
        return {"processed": len(done) + len(failed), "done": done.ids, "failed": failed.ids,
                "remaining": remaining, "waiting": False}

    @api.model
    def _wait_for_page_source(self, now):
        """No page source: keep every unit queued, mark the runs waiting, report no progress."""
        pending = self.env["azk_odoo_partner_monitor.work.item"].search([("state", "=", "pending")])
        due = pending.filtered(lambda item: item.next_attempt_at <= now)
        if pending:
            pending.run_id._set_waiting(NO_PAGE_SOURCE)
            _logger.warning("Partner Monitor: %s queued units are waiting, none was attempted: %s.",
                            len(pending), NO_PAGE_SOURCE)
        return {"processed": 0, "done": [], "failed": [], "remaining": len(due), "waiting": bool(pending)}

    @api.model
    def _claim_next(self, now):
        """Lock and return the next due unit, or an empty recordset.

        ``FOR NO KEY UPDATE SKIP LOCKED`` skips units locked by another
        worker's open transaction, so two workers never get the same unit.
        The lock lasts until this transaction ends (the scheduler's commit,
        or the rollback of a crashed process), so a claim never outlives its
        transaction and needs no lease.

        Odoo runs transactions in REPEATABLE READ. If another worker committed
        the next unit after this transaction began, PostgreSQL refuses to lock
        it (serialization failure). That ends this batch, and the next batch
        sees the committed state.
        """
        WorkItem = self.env["azk_odoo_partner_monitor.work.item"]
        WorkItem.flush_model()
        try:
            with self.env.cr.savepoint(flush=False):
                self.env.cr.execute(SQL(
                    "SELECT id FROM %s WHERE state = 'pending' AND next_attempt_at <= %s"
                    " ORDER BY %s, next_attempt_at, id LIMIT 1 FOR NO KEY UPDATE SKIP LOCKED",
                    SQL.identifier(WorkItem._table), now, KIND_ORDER), log_exceptions=False)
                row = self.env.cr.fetchone()
        except psycopg2.errors.SerializationFailure:
            _logger.info("Partner Monitor: the next unit was processed by another worker; "
                         "this batch stops here.")
            return WorkItem
        return WorkItem.browse(row[0]) if row else WorkItem

    @api.model
    def _run_unit(self, item, fetch, now):
        """Run one claimed unit in its own savepoint. Returns True when it is done.

        Any exception rolls back to the savepoint only, so the cursor stays
        usable and the batch goes on with other units (P-05). The failure is
        then recorded outside the savepoint: an error row, a log line and one
        counted try with backoff (P-06). Nothing is swallowed silently.
        """
        tracker = _UrlTracker(fetch)
        handler = getattr(self, f"_unit_{item.kind}")
        try:
            with self.env.cr.savepoint():
                summary = handler(item, tracker, now)
        except Exception as exc:  # noqa: BLE001 - recorded below, see the docstring
            self._record_unit_failure(item, exc, tracker.last_url, now)
            return False
        item._mark_done(summary, now)
        return True

    @api.model
    def _record_unit_failure(self, item, exc, url, now):
        message = str(exc) or exc.__class__.__name__
        final = item._mark_failed_attempt(f"{exc.__class__.__name__}: {message}", now)
        self.env["azk_odoo_partner_monitor.sync.error"].create({
            "run_id": item.run_id.id,
            "work_item_id": item.id,
            "country_id": item.country_id.id,
            "partner_id": item.partner_id.id,
            "url": url,
            "error_class": exc.__class__.__name__,
            "message": message,
            "trace": "".join(traceback.format_exception(exc, limit=6))[-4000:],
        })
        _logger.warning(
            "Partner Monitor: %s (run %s, unit %s) failed, try %s of %s%s; URL %s: %s: %s",
            item.display_name, item.run_id.id, item.id, item.attempt_count, MAX_ATTEMPTS,
            ", no retry left" if final else f", next try at {item.next_attempt_at}",
            url, exc.__class__.__name__, message)

    # ------------------------------------------------------------------
    # Units: read with the page source, store through models/ingest.py
    # ------------------------------------------------------------------

    def _unit_country_list(self, item, fetch, now):
        country_list = reader.read_country_list(fetch)
        summary = self.env["azk_odoo_partner_monitor.ingest"]._ingest_country_list(
            country_list, now.date(), now=now)
        countries = self.env["azk_odoo_partner_monitor.country"].search([("is_demo", "=", False)])
        WorkItem = self.env["azk_odoo_partner_monitor.work.item"]
        for country in countries:
            WorkItem._enqueue("country_partners", item.run_id, country=country)
        return (f"{summary['countries']} countries read, list "
                f"{'complete' if summary['complete'] else 'incomplete'}, "
                f"{len(summary['deactivated'])} deactivated, {len(countries)} countries to read")

    def _unit_country_partners(self, item, fetch, now):
        country = item.country_id
        pages = reader.read_country_listing(fetch, country.source_key)
        country_list = None
        if pages and pages[0].scope == "empty_country":
            # D-27: the notice counts only if a complete country list confirms
            # it; read the list now, in this same unit.
            country_list = reader.read_country_list(fetch)
        summary = self.env["azk_odoo_partner_monitor.ingest"]._ingest_country_listing(
            country, pages, now.date(), country_list=country_list, now=now)
        WorkItem = self.env["azk_odoo_partner_monitor.work.item"]
        for partner in self.env["azk_odoo_partner_monitor.partner"].browse(summary["unread"]):
            WorkItem._enqueue("partner_details", item.run_id, partner=partner)
        return (f"{summary['scope']}: {summary['found']} of {summary['expected']} partners, "
                f"{'complete' if summary['complete'] else 'incomplete'}, "
                f"{len(summary['archived'])} archived, {len(summary['unread'])} pages to read, "
                f"{len(summary['changed'])} changed cards")

    def _unit_partner_details(self, item, fetch, now):
        partner = item.partner_id
        if not partner.partner_url:
            raise ValueError(f"partner {partner.source_id} has no page URL")
        page = reader.read_partner_page(fetch, partner.partner_url)
        summary = self.env["azk_odoo_partner_monitor.ingest"]._ingest_partner_page(
            partner, page, now.date(), now=now)
        return (f"{summary['found']} of {summary['expected']} references, "
                f"{'matched' if summary['matched'] else 'mismatch'}, "
                f"{len(summary['added'])} added, {len(summary['removed'])} removed")
