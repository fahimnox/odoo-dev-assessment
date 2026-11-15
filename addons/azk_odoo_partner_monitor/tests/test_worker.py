from datetime import datetime, timedelta
from unittest.mock import patch

from odoo.addons.mail.tests.common import MockEmail
from odoo.tests import TransactionCase, new_test_user, tagged
from odoo.tools import SQL, mute_logger

from ..models.common import MAX_ATTEMPTS, retry_delay
from ..models.sync_run import NOTIFY_USER_PARAM
from ..models.worker import BATCH_SIZE_PARAM, DOWNLOADS_PAUSED, DOWNLOADS_PAUSED_PARAM
from ..services import http_client, parsers, urls
from .common import (ALL_PAGES, EGYPT_P1, EGYPT_P11, MANAGER, ROAYATEC, FixtureSite,
                     andorra_variant, country_list_variant, fixture, listing_card_variant)

WORKER_LOG = "odoo.addons.azk_odoo_partner_monitor.models.worker"
NOW = datetime(2026, 11, 10, 8, 0, 0)
DAY = NOW.date()
ANDORRA_URL = urls.listing_url("1")


class WorkerCase(TransactionCase, MockEmail):
    """The worker with a fixture-backed page source (tests/common.py, FixtureSite).

    Time is frozen at NOW; tests that need later moments pass ``now``
    explicitly. Failure notes go to an Inbox user, and the mail gateway is
    mocked where a note can be posted, so no email leaves the test.
    """

    freeze_time = "2026-11-10 08:00:00"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        cls.Worker = env["azk_odoo_partner_monitor.worker"]
        cls.Ingest = env["azk_odoo_partner_monitor.ingest"]
        cls.Run = env["azk_odoo_partner_monitor.sync.run"]
        cls.WorkItem = env["azk_odoo_partner_monitor.work.item"]
        cls.SyncError = env["azk_odoo_partner_monitor.sync.error"]
        cls.Country = env["azk_odoo_partner_monitor.country"].with_context(active_test=False)
        cls.Partner = env["azk_odoo_partner_monitor.partner"].with_context(active_test=False)
        cls.andorra = cls.Country._record_observation(
            {"source_key": "1", "name": "Andorra", "total_partner_count": 2})
        cls.anguilla = cls.Country._record_observation(
            {"source_key": "5", "name": "Anguilla", "total_partner_count": 1})
        cls.egypt = cls.Country._record_observation(
            {"source_key": "64", "name": "Egypt", "total_partner_count": 210})
        cls.inbox_user = new_test_user(env, login="pm_worker_inbox", groups="base.group_user",
                                       notification_type="inbox", email="worker.inbox@example.com")
        env["ir.config_parameter"].set_param(NOTIFY_USER_PARAM, str(cls.inbox_user.id))

    # ---------------------------------------------------------------- helpers

    def site(self, html=None):
        return FixtureSite(ALL_PAGES, html=html)

    def queue(self, kind, target=None, run=None):
        run = run or self.Run.create({"trigger": "manual"})
        if target is None:
            return self.WorkItem._enqueue(kind, run)
        key = "country" if target._name.endswith(".country") else "partner"
        return self.WorkItem._enqueue(kind, run, **{key: target})

    def process(self, site, now=NOW, **limits):
        with mute_logger(WORKER_LOG), self.mock_mail_gateway():
            return self.Worker._process_queue(site, now=now, **limits)

    def earlier_partner(self, country, source_id):
        """A partner stored by an earlier scrape and absent from today's pages."""
        return self.Partner._record_observation(
            {"source_id": source_id, "name": f"Earlier partner {source_id}", "current_status": "ready",
             "country_id": country.id}, "2026-10-01")

    def egypt_partners(self):
        """Egypt's first and last saved pages, stored directly (an incomplete snapshot)."""
        pages = [parsers.parse_listing_page(fixture(name), url, "64") for url, name in (EGYPT_P1, EGYPT_P11)]
        self.Ingest._ingest_country_listing(self.egypt, pages, DAY, now=NOW)
        return {p.source_id: p for p in self.Partner.search([("country_id", "=", self.egypt.id)])}

    def partner(self, source_id):
        return self.Partner.search([("source_id", "=", source_id)])

    @staticmethod
    def notes(run):
        return run.message_ids.filtered(lambda message: message.message_type == "comment")


@tagged("post_install", "-at_install")
class TestWorker(WorkerCase):
    """TP-PM-09 to TP-PM-17 through the worker (docs/resilience.md)."""

    # ---------------------------------------------------------------- page source

    def test_paused_downloads_keep_the_queue_and_say_so(self):
        run = self.Worker._cron_daily_discovery()
        unit = run.work_item_ids
        self.assertRecordValues(unit, [{"kind": "country_list", "state": "pending", "attempt_count": 0}])
        # Without the setting, the page source is the HTTP client (never
        # called here); with it, there is none.
        self.assertIsInstance(self.Worker._get_page_source(), http_client.PartnersHttpClient)
        self.env["ir.config_parameter"].set_param(DOWNLOADS_PAUSED_PARAM, "True")
        self.assertIsNone(self.Worker._get_page_source())
        # The real cron entry point, while a system administrator pauses the downloads.
        with self.mock_mail_gateway(), self.assertLogs(WORKER_LOG, "WARNING") as logs:
            first = self.Worker._cron_process_queue()
            second = self.Worker._cron_process_queue()
        self.assertEqual((first["processed"], first["waiting"], first["remaining"]), (0, True, 1))
        self.assertEqual((second["processed"], second["waiting"]), (0, True))
        self.assertIn("1 queued units are waiting, no request is sent", logs.output[0])
        # Nothing was attempted, failed or lost.
        self.assertRecordValues(unit, [{"state": "pending", "attempt_count": 0, "last_error": False}])
        self.assertFalse(self.SyncError.search([("run_id", "=", run.id)]))
        self.assertRecordValues(run, [{"state": "running", "waiting_reason": DOWNLOADS_PAUSED}])
        # The configured user is told once, not at every worker call.
        notes = self.notes(run)
        self.assertEqual(len(notes), 1)
        self.assertIn("is waiting", notes.body)
        self.assertEqual(notes.partner_ids, self.inbox_user.partner_id)
        self.assertFalse(self._new_mails)
        # With a page source, the same unit runs and the run stops waiting.
        site = self.site({urls.COUNTRY_LIST_URL: country_list_variant(keep={"1"})})
        result = self.process(site, max_units=1)
        self.assertEqual(result["done"], unit.ids)
        self.assertFalse(run.waiting_reason)

    def test_units_queued_by_a_unit_are_due_in_the_same_batch(self):
        # Regression (Stage 10 live check): a batch fixes its moment when it
        # starts, and units queued seconds later used the current time, so
        # they were neither claimable nor counted as remaining in that batch.
        # Here the batch started 30 seconds before the frozen clock.
        started = NOW - timedelta(seconds=30)
        unit = self.queue("country_partners", self.andorra)
        unit.next_attempt_at = started
        result = self.process(self.site(), now=started, max_units=5)
        pages = self.WorkItem.search([("kind", "=", "partner_details"), ("run_id", "=", unit.run_id.id)])
        self.assertEqual(len(pages), 2)
        self.assertEqual(pages.mapped("next_attempt_at"), [started + retry_delay(1)] * 2)
        # Both pages were tried in the same batch (they are not saved, so the try failed).
        self.assertEqual(result["processed"], 3)
        self.assertEqual(pages.mapped("attempt_count"), [1, 1])

    # ---------------------------------------------------------------- a whole run

    def test_daily_run_retries_failed_units_then_notifies_once(self):
        # The country list holds Andorra only (still complete: its counts add
        # up). The two Andorra partner pages are not saved, so reading them
        # fails at every try.
        site = self.site({urls.COUNTRY_LIST_URL: country_list_variant(keep={"1"})})
        run = self.Worker._cron_daily_discovery()
        first = self.process(site)
        self.assertEqual((len(first["done"]), len(first["failed"])), (2, 2))
        self.assertFalse(self.egypt.active)  # absent from a complete list
        details = run.work_item_ids.filtered(lambda unit: unit.kind == "partner_details")
        self.assertRecordValues(details, [
            {"state": "pending", "attempt_count": 1, "next_attempt_at": NOW + timedelta(minutes=15)}] * 2)
        self.assertEqual(self.process(site, now=NOW + timedelta(minutes=14))["processed"], 0)
        when = NOW
        for attempt in range(1, MAX_ATTEMPTS):
            when += retry_delay(attempt)
            self.assertEqual(self.process(site, now=when)["processed"], 2)
        self.assertRecordValues(details, [{"state": "failed", "attempt_count": MAX_ATTEMPTS}] * 2)
        self.assertRecordValues(run, [{"state": "partial", "finished_at": when}])
        # One note, with the counts, the failed scopes and the recovery action.
        notes = self.notes(run)
        self.assertEqual(len(notes), 1)
        self.assertIn("2 units done, 2 failed, 0 pending, 10 errors logged", notes.body)
        self.assertIn("Partner details: BDR GROUP SLU: LookupError: no saved page for "
                      "https://www.odoo.com/partners/bdr-group-slu-22015187", notes.body)
        self.assertIn("Managers can retry failed work", notes.body)
        self.assertEqual(notes.partner_ids, self.inbox_user.partner_id)
        errors = self.SyncError.search([("run_id", "=", run.id)])
        self.assertEqual(len(errors), 2 * MAX_ATTEMPTS)
        self.assertEqual(set(errors.mapped("error_class")), {"LookupError"})
        self.assertEqual(set(errors.mapped("url")), set(details.partner_id.mapped("partner_url")))
        # Later worker calls change nothing and post nothing.
        self.assertEqual(self.process(site, now=when + timedelta(days=1))["processed"], 0)
        self.assertEqual(len(self.notes(run)), 1)
        partners = self.Partner.search([("country_id", "=", self.andorra.id)])
        self.assertEqual(len(partners), 2)
        self.assertEqual(len(partners.status_history_ids), 2)

    # ---------------------------------------------------------------- idempotency

    def test_repeated_identical_ingestion_creates_nothing_new(self):
        site = self.site()
        for _repeat in range(2):
            unit = self.queue("country_partners", self.andorra)
            self.assertEqual(self.process(site, max_units=1)["done"], unit.ids)
        partners = self.Partner.search([("country_id", "=", self.andorra.id)])
        self.assertEqual(sorted(partners.mapped("source_id")), [22015187, 24934006])
        self.assertEqual(len(partners.status_history_ids), 2)  # one initial row each
        self.assertEqual(set(partners.mapped("first_seen_on")), {DAY})
        # Their pages were queued once, by the first read only.
        self.assertEqual(self.WorkItem.search_count(
            [("kind", "=", "partner_details"), ("partner_id", "in", partners.ids)]), 2)
        self.assertFalse(any(partners.mapped("to_reprocess_references")))
        self.assertRecordValues(self.andorra, [{
            "validation_state": "matched", "snapshot_partner_count": 2, "to_reprocess_partners": False}])

    # ---------------------------------------------------------------- isolation

    def test_one_failed_partner_does_not_stop_the_others(self):
        partners = self.egypt_partners()
        run = self.Run.create({"trigger": "manual"})
        units = {source_id: self.queue("partner_details", partners[source_id], run)
                 for source_id in (167908, 17207720, 32297621)}
        # IT SYS (167908) has no saved page: its download fails.
        with self.assertLogs(WORKER_LOG, "WARNING") as logs:
            result = self.Worker._process_queue(self.site(), now=NOW)
        self.assertEqual(result["failed"], units[167908].ids)
        self.assertEqual(sorted(result["done"]), sorted([units[17207720].id, units[32297621].id]))
        self.assertRecordValues(units[167908], [{"state": "pending", "attempt_count": 1}])
        self.assertRecordValues(units[167908].error_ids, [{
            "run_id": run.id, "partner_id": partners[167908].id, "error_class": "LookupError",
            "url": "https://www.odoo.com/partners/it-sys-corporation-167908"}])
        self.assertIn(f"(run {run.id}, unit {units[167908].id}) failed, try 1 of 5", logs.output[0])
        # The other partners were stored in the same batch.
        self.assertEqual(len(partners[17207720].reference_ids), 3)
        self.assertRecordValues(partners[32297621], [{"reference_validation_state": "matched"}])
        self.assertEqual(run.state, "running")  # IT SYS will be tried again

    def test_database_error_in_one_unit_leaves_the_cursor_usable(self):
        partners = self.egypt_partners()
        run = self.Run.create({"trigger": "manual"})
        bad = self.queue("partner_details", partners[17207720], run)
        good = self.queue("partner_details", partners[32297621], run)
        Ingest = type(self.Ingest)
        original = Ingest._ingest_partner_page

        def write_then_fail(ingest, partner, page, observed_on, now=None):
            summary = original(ingest, partner, page, observed_on, now=now)
            if partner.source_id == 17207720:
                ingest.env.cr.execute("SELECT 1 / 0")  # a real SQL error after the writes
            return summary

        with patch.object(Ingest, "_ingest_partner_page", write_then_fail), \
                mute_logger("odoo.sql_db", WORKER_LOG):
            result = self.Worker._process_queue(self.site(), now=NOW)
        self.assertEqual((result["failed"], result["done"]), (bad.ids, good.ids))
        self.assertEqual(bad.error_ids.error_class, "DivisionByZero")
        # The failed unit's writes were rolled back with its savepoint ...
        self.assertFalse(partners[17207720].reference_ids)
        # ... the next unit was stored, and the cursor is still usable.
        self.assertRecordValues(partners[32297621], [{"reference_validation_state": "matched"}])
        self.env.cr.execute("SELECT 1")
        self.assertEqual(self.env.cr.fetchone(), (1,))

    # ---------------------------------------------------------------- validation

    def test_reference_mismatch_then_recovery(self):
        roayatec = self.egypt_partners()[17207720]
        seeded, _removed = roayatec._sync_references(
            [{"source_key": "999001", "name": "Client seen in an earlier scrape"}], "2026-11-01", complete=False)
        self.queue("partner_details", roayatec)
        self.process(self.site())  # the saved page lists 3 of its 135 references
        self.assertRecordValues(roayatec, [{
            "total_references_count": 135, "snapshot_reference_count": 3, "active_reference_count": 4,
            "reference_validation_state": "mismatch", "to_reprocess_references": True,
            "reprocess_attempts": 0, "next_reprocess_at": NOW}])
        self.assertTrue(seeded.is_active)  # an incomplete list removes nothing
        # The reference-validation job queues one re-read, and only once.
        queued = self.Worker._cron_validate_references(now=NOW)
        self.assertEqual((queued.partner_id, queued.run_id.trigger), (roayatec, "validation"))
        self.assertFalse(self.Worker._cron_validate_references(now=NOW + timedelta(hours=1)))
        self.assertRecordValues(roayatec, [{"reprocess_attempts": 1,
                                            "next_reprocess_at": NOW + timedelta(minutes=15)}])
        # The website now lists every reference it counts: the re-read matches.
        complete = fixture(ROAYATEC[1]).replace("References - 135", "References - 3")
        self.process(self.site({ROAYATEC[0]: complete}), now=NOW + timedelta(hours=1))
        self.assertRecordValues(roayatec, [{
            "total_references_count": 3, "previous_references_count": 135,
            "snapshot_reference_count": 3, "active_reference_count": 3,
            "reference_validation_state": "matched", "to_reprocess_references": False,
            "reprocess_attempts": 0, "next_reprocess_at": False}])
        self.assertRecordValues(seeded, [{"is_active": False, "removed_on": DAY}])

    def test_country_mismatch_then_recovery(self):
        earlier = self.earlier_partner(self.andorra, 990101)
        self.queue("country_partners", self.andorra)
        # The site says 3 partners but lists 2.
        self.process(self.site({ANDORRA_URL: andorra_variant(listed=3)}), max_units=1)
        self.assertRecordValues(self.andorra, [{
            "total_partner_count": 3, "previous_partner_count": 2, "snapshot_partner_count": 2,
            "validation_state": "mismatch", "to_reprocess_partners": True,
            "reprocess_attempts": 0, "next_reprocess_at": NOW}])
        self.assertTrue(earlier.active)  # no archiving from an incomplete snapshot
        queued = self.Worker._cron_validate_countries(now=NOW)
        self.assertEqual((queued.country_id, queued.run_id.trigger), (self.andorra, "validation"))
        self.assertFalse(self.Worker._cron_validate_countries(now=NOW + timedelta(hours=1)))
        # The re-scrape sees the real page: 2 listed, 2 found.
        self.process(self.site(), now=NOW + timedelta(hours=1), max_units=1)
        self.assertRecordValues(self.andorra, [{
            "total_partner_count": 2, "previous_partner_count": 3, "snapshot_partner_count": 2,
            "validation_state": "matched", "to_reprocess_partners": False,
            "reprocess_attempts": 0, "next_reprocess_at": False}])
        self.assertFalse(earlier.active)

    def test_genuine_change_in_partner_count_is_no_false_mismatch(self):
        self.queue("country_partners", self.andorra)
        self.process(self.site(), max_units=1)
        self.queue("country_partners", self.andorra)
        one_left = andorra_variant(listed=1, drop_ids=[24934006])
        self.process(self.site({ANDORRA_URL: one_left}), max_units=1)
        self.assertRecordValues(self.andorra, [{
            "total_partner_count": 1, "previous_partner_count": 2, "snapshot_partner_count": 1,
            "validation_state": "matched", "to_reprocess_partners": False}])
        gone = self.partner(24934006)
        self.assertFalse(gone.active)
        self.assertEqual(len(gone.status_history_ids), 1)  # archiving adds no history row

    def test_same_count_with_changed_identities_and_status(self):
        self.queue("country_partners", self.andorra)
        self.process(self.site(), max_units=1)
        changed = andorra_variant(statuses={22015187: "Silver"}, new_ids={24934006: 24934099})
        self.queue("country_partners", self.andorra)
        self.process(self.site({ANDORRA_URL: changed}), max_units=1)
        # Same count (2 listed, 2 found), yet one partner left, one arrived and one was promoted.
        self.assertRecordValues(self.andorra, [{
            "total_partner_count": 2, "snapshot_partner_count": 2, "validation_state": "matched"}])
        bdr, gone, newcomer = self.partner(22015187), self.partner(24934006), self.partner(24934099)
        self.assertEqual(bdr.status_history_ids.sorted("id").mapped("change_type"), ["initial", "promoted"])
        self.assertFalse(gone.active)
        self.assertTrue(newcomer.active)
        self.assertEqual(newcomer.status_history_ids.change_type, "initial")

    def test_failed_or_partial_reads_delete_nothing(self):
        kept = self.earlier_partner(self.egypt, 990102)
        # Egypt's page 2 cannot be downloaded: the unit fails and stores nothing.
        unit = self.queue("country_partners", self.egypt)
        self.process(self.site(), max_units=1)
        self.assertRecordValues(unit, [{"state": "pending", "attempt_count": 1}])
        self.assertEqual(unit.error_ids.url, "https://www.odoo.com/partners/country/egypt-64/page/2")
        self.assertTrue(kept.active)
        self.assertFalse(self.partner(17207720))  # page 1's cards went with the failed unit
        self.assertEqual(self.egypt.validation_state, "unchecked")
        # An incomplete country list (Andorra missing, total unchanged) deactivates nothing.
        self.queue("country_list")
        site = self.site({urls.COUNTRY_LIST_URL: country_list_variant(drop={"1"})})
        self.process(site, max_units=1)
        self.assertTrue(self.andorra.active and self.anguilla.active and self.egypt.active)

    def test_valid_empty_country_is_confirmed_by_the_country_list(self):
        gone = self.earlier_partner(self.anguilla, 990103)
        self.queue("country_partners", self.anguilla)
        site = self.site()
        self.process(site, max_units=1)
        # The no-partners notice, then the country list that confirms it (D-27).
        self.assertEqual(site.requested, [urls.listing_url("5"), urls.COUNTRY_LIST_URL])
        self.assertFalse(gone.active)
        self.assertRecordValues(self.anguilla, [{
            "total_partner_count": 0, "previous_partner_count": 1, "snapshot_partner_count": 0,
            "validation_state": "matched", "to_reprocess_partners": False}])
        # The global cards shown on the page were never recorded.
        self.assertFalse(self.Partner.search([("source_id", "in", [990138, 4155, 732280])]))

    def test_unconfirmed_empty_notice_keeps_the_data(self):
        kept = self.earlier_partner(self.anguilla, 990104)
        self.queue("country_partners", self.anguilla)
        site = self.site({urls.COUNTRY_LIST_URL: country_list_variant(drop={"1"})})  # incomplete
        self.process(site, max_units=1)
        self.assertTrue(kept.active)
        self.assertRecordValues(self.anguilla, [{
            "total_partner_count": 1, "validation_state": "mismatch", "to_reprocess_partners": True}])

    # ---------------------------------------------------------------- bounded retries

    def test_unit_retries_are_bounded_with_growing_delays(self):
        run = self.Run.create({"trigger": "manual"})
        unit = self.queue("country_partners", self.egypt, run)  # page 2 is never available
        when, delays = NOW, []
        for attempt in range(1, MAX_ATTEMPTS + 1):
            self.assertEqual(self.process(self.site(), now=when, max_units=1)["processed"], 1)
            self.assertEqual(unit.attempt_count, attempt)
            if attempt < MAX_ATTEMPTS:
                delays.append(unit.next_attempt_at - when)
                too_early = unit.next_attempt_at - timedelta(minutes=1)
                self.assertEqual(self.process(self.site(), now=too_early)["processed"], 0)
                when = unit.next_attempt_at
        self.assertEqual(delays, [timedelta(minutes=minutes) for minutes in (15, 30, 60, 120)])
        self.assertRecordValues(unit, [{"state": "failed", "attempt_count": MAX_ATTEMPTS}])
        self.assertEqual(len(unit.error_ids), MAX_ATTEMPTS)
        self.assertEqual(run.state, "failed")  # its only unit failed
        self.assertEqual(len(self.notes(run)), 1)
        self.assertEqual(self.process(self.site(), now=when + timedelta(days=2))["processed"], 0)

    def test_permanent_mismatch_stops_after_the_retry_limit(self):
        site = self.site({ANDORRA_URL: andorra_variant(listed=3)})  # never matches
        self.queue("country_partners", self.andorra)
        self.process(site, max_units=1)
        when = NOW
        for attempt in range(1, MAX_ATTEMPTS + 1):
            self.assertEqual(len(self.Worker._cron_validate_countries(now=when)), 1)
            self.process(site, now=when, max_units=1)
            self.assertRecordValues(self.andorra, [{
                "reprocess_attempts": attempt, "to_reprocess_partners": True}])
            when = self.andorra.next_reprocess_at
        self.assertFalse(self.Worker._cron_validate_countries(now=when + timedelta(days=30)))
        self.assertRecordValues(self.andorra, [{
            "to_reprocess_partners": True, "reprocess_exhausted": True, "validation_state": "mismatch"}])
        # The mismatch stays visible; a manager can give it a new budget.
        self.andorra.action_mark_for_rescrape()
        self.assertEqual(len(self.Worker._cron_validate_countries(now=when + timedelta(days=30))), 1)
        self.assertFalse(self.andorra.reprocess_exhausted)

    def test_flag_without_a_retry_count_is_still_validated(self):
        """Regression found in Stage 05: a row whose retry count is NULL (for
        example created before the field existed) was never re-scraped,
        because SQL never matches "NULL < 5"."""
        partner = self.earlier_partner(self.andorra, 990105)
        self.andorra.write({"to_reprocess_partners": True})
        partner.write({"to_reprocess_references": True})
        self.env.flush_all()
        for record in (self.andorra, partner):
            self.env.cr.execute(SQL("UPDATE %s SET reprocess_attempts = NULL WHERE id = %s",
                                    SQL.identifier(record._table), record.id))
        self.env.invalidate_all()
        self.assertEqual(self.Worker._cron_validate_countries(now=NOW).country_id, self.andorra)
        self.assertEqual(self.Worker._cron_validate_references(now=NOW).partner_id, partner)
        self.assertEqual((self.andorra.reprocess_attempts, partner.reprocess_attempts), (1, 1))

    # ---------------------------------------------------------------- scheduling

    def test_duplicate_scheduling_adds_no_work(self):
        first = self.Worker._cron_daily_discovery()
        self.assertTrue(first)
        self.assertFalse(self.Worker._cron_daily_discovery())
        self.Run.action_sync_now()  # a manager's click while the sync is queued
        self.assertEqual(self.WorkItem.search_count(
            [("kind", "=", "country_list"), ("state", "=", "pending")]), 1)
        self.assertEqual(self.Run.search_count([("trigger", "in", ("daily", "manual"))]), 1)
        # A flagged country whose listing is already queued gets no second
        # unit, and uses no retry.
        daily_unit = self.queue("country_partners", self.egypt, first)
        self.egypt.action_mark_for_rescrape()
        self.assertFalse(self.Worker._cron_validate_countries(now=NOW))
        self.assertEqual(self.egypt.reprocess_attempts, 0)
        self.assertEqual(self.WorkItem.search([("kind", "=", "country_partners"), ("state", "=", "pending"),
                                               ("country_id", "=", self.egypt.id)]), daily_unit)
        # The validation job run twice queues one unit.
        self.andorra.action_mark_for_rescrape()
        self.assertEqual(len(self.Worker._cron_validate_countries(now=NOW)), 1)
        self.assertFalse(self.Worker._cron_validate_countries(now=NOW))
        # The same partner page asked for twice: one unit.
        roayatec = self.egypt_partners()[17207720]
        self.assertEqual(self.queue("partner_details", roayatec, first),
                         self.queue("partner_details", roayatec))

    def test_manager_retry_reopens_the_run_and_wakes_the_worker(self):
        manager = new_test_user(self.env, login="pm_worker_manager", groups=MANAGER)
        run = self.Run.create({"trigger": "manual"})
        # Anguilla's unit queues no further work, so the run can finish.
        unit = self.WorkItem.create({"kind": "country_partners", "run_id": run.id,
                                     "country_id": self.anguilla.id, "state": "failed",
                                     "attempt_count": MAX_ATTEMPTS})
        run.write({"state": "partial", "notified_at": NOW})
        cron = self.env.ref("azk_odoo_partner_monitor.ir_cron_worker")
        triggers_before = self.env["ir.cron.trigger"].search_count([("cron_id", "=", cron.id)])
        unit.with_user(manager).action_retry()
        self.assertRecordValues(unit, [{"state": "pending", "attempt_count": 0}])
        self.assertEqual(run.state, "running")
        self.assertEqual(self.env["ir.cron.trigger"].search_count([("cron_id", "=", cron.id)]),
                         triggers_before + 1)
        self.process(self.site(), max_units=1)
        self.assertRecordValues(run, [{"state": "done", "notified_at": NOW}])
        self.assertFalse(self.notes(run))

    # ---------------------------------------------------------------- change-aware pulling

    def test_details_refresh_policy(self):
        last_page = parsers.parse_listing_page(fixture(EGYPT_P11[1]), EGYPT_P11[0], "64")
        summary = self.Ingest._ingest_country_listing(self.egypt, [last_page], DAY, now=NOW)
        devoneers = self.partner(32297621)
        # A new partner: its page is read in the same run; it is not a mismatch.
        self.assertIn(devoneers.id, summary["unread"])
        self.assertEqual(summary["changed"], [])
        self.assertFalse(devoneers.to_reprocess_references)
        self.queue("partner_details", devoneers)
        self.process(self.site())
        self.assertRecordValues(devoneers, [{"reference_validation_state": "matched", "details_synced_at": NOW}])
        # The same card again: nothing to refresh.
        summary = self.Ingest._ingest_country_listing(self.egypt, [last_page], DAY, now=NOW)
        self.assertNotIn(devoneers.id, summary["unread"] + summary["changed"])
        self.assertFalse(devoneers.to_reprocess_references)
        # A changed metric on the card asks for one re-read (P-20.3).
        changed_html = listing_card_variant(EGYPT_P11[1], 32297621, "Average Project: 0", "Average Project: 4")
        changed_page = parsers.parse_listing_page(changed_html, EGYPT_P11[0], "64")
        later = NOW + timedelta(hours=2)
        summary = self.Ingest._ingest_country_listing(self.egypt, [changed_page], DAY, now=later)
        self.assertEqual(summary["changed"], devoneers.ids)
        self.assertRecordValues(devoneers, [{"to_reprocess_references": True, "reprocess_attempts": 0,
                                             "average_project_size": 4.0}])
        self.assertEqual(self.Worker._cron_validate_references(now=later).partner_id, devoneers)
        self.process(self.site(), now=later)
        self.assertRecordValues(devoneers, [{"to_reprocess_references": False, "details_synced_at": later}])
        # The partner page shows another average than the card; reading it
        # does not count as a card change, so there is no refresh loop.
        summary = self.Ingest._ingest_country_listing(self.egypt, [changed_page], DAY, now=later)
        self.assertEqual(summary["changed"], [])
        self.assertFalse(devoneers.to_reprocess_references)
        # Details read more than 7 days ago are read again, without a flag or a retry count.
        devoneers.details_synced_at = later - timedelta(days=6)
        self.assertFalse(self.Worker._cron_validate_references(now=later))
        devoneers.details_synced_at = later - timedelta(days=8)
        flagged = self.partner(5912889)  # SHARP 4 IT, on the same page
        flagged._request_details_refresh(later)
        queued = self.Worker._cron_validate_references(now=later)
        self.assertEqual(queued.partner_id, devoneers | flagged)
        self.assertEqual(len(queued.run_id), 1)  # one validation run per job call
        self.assertRecordValues(devoneers, [{"to_reprocess_references": False, "reprocess_attempts": 0}])
        self.assertEqual(flagged.reprocess_attempts, 1)  # only the flagged partner uses a try

    # ---------------------------------------------------------------- the scheduler

    def test_worker_job_runs_bounded_batches_through_the_scheduler(self):
        """The real ir.cron path (_process_job, _run_job, _notify_progress), in test mode:
        each commit of the scheduler becomes a savepoint of the test transaction."""
        cron = self.env.ref("azk_odoo_partner_monitor.ir_cron_worker")
        self.env["ir.config_parameter"].set_param(BATCH_SIZE_PARAM, "1")
        run = self.Run.create({"trigger": "manual"})
        for country in (self.andorra, self.anguilla, self.egypt):
            self.queue("country_partners", country, run)
        site = self.site()
        Worker = type(self.Worker)
        job = {**cron.read(load=None)[0], "done": 0, "remaining": 0, "timed_out_counter": 0}
        self.env.flush_all()
        self.registry.enter_test_mode(self.cr)
        try:
            with patch.object(Worker, "_get_page_source", lambda worker: site), \
                    mute_logger(WORKER_LOG, "odoo.addons.base.models.ir_cron"):
                self.registry["ir.cron"]._process_job(self.registry.db_name, self.registry.cursor(), job)
        finally:
            self.registry.leave_test_mode()
        self.env.invalidate_all()
        # One unit per scheduler call: Andorra, Anguilla, Egypt (fails), then
        # the two Andorra partner pages it queued (not saved: they fail).
        progress = self.env["ir.cron.progress"].search([("cron_id", "=", cron.id)], order="id")
        self.assertEqual(progress.mapped("done"), [1, 1, 1, 1, 1])
        self.assertEqual(progress[-1].remaining, 0)
        units = run.work_item_ids
        self.assertEqual(sorted(units.mapped("state")), ["done", "done", "pending", "pending", "pending"])
        self.assertEqual(set(units.filtered(lambda u: u.state == "pending").mapped("attempt_count")), {1})
        # Fully done: the scheduler rescheduled the job at its interval, with no failure.
        self.assertRecordValues(cron, [{"lastcall": NOW, "failure_count": 0}])

    def test_sync_jobs_are_scheduled(self):
        root = self.env.ref("base.user_root")
        expected = {
            "ir_cron_daily_discovery": ("_cron_daily_discovery", 1, "days"),
            "ir_cron_worker": ("_cron_process_queue", 10, "minutes"),
            "ir_cron_validate_countries": ("_cron_validate_countries", 6, "hours"),
            "ir_cron_validate_references": ("_cron_validate_references", 6, "hours"),
        }
        for xmlid, (method, number, unit) in expected.items():
            with self.subTest(cron=xmlid):
                cron = self.env.ref(f"azk_odoo_partner_monitor.{xmlid}")
                self.assertRecordValues(cron, [{"active": True, "interval_number": number,
                                                "interval_type": unit, "user_id": root.id}])
                self.assertEqual(cron.model_id.model, "azk_odoo_partner_monitor.worker")
                self.assertEqual(cron.code.strip(), f"model.{method}()")
