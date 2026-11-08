from datetime import date

from psycopg2 import IntegrityError

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import new_test_user, tagged
from odoo.tools import mute_logger

from .common import READER, PartnerMonitorCase


@tagged("post_install", "-at_install")
class TestStatusHistory(PartnerMonitorCase):
    """Invariants 1 to 3 of Stage 03: no duplicates, first_seen_on is fixed,
    one history event per real transition (docs/architecture.md 5.3)."""

    def test_first_observation_creates_partner_and_initial_row(self):
        partner = self.observe(5001, "silver", "2026-01-05")
        self.assertRecordValues(partner, [{
            "source_id": 5001, "current_status": "silver", "active": True,
            "first_seen_on": date(2026, 1, 5), "last_seen_on": date(2026, 1, 5),
        }])
        self.assertRecordValues(self.history_of(partner), [{
            "change_type": "initial", "previous_status": False,
            "new_status": "silver", "change_date": date(2026, 1, 5),
        }])

    def test_silver_gold_gold_records_initial_then_one_promotion(self):
        """The sequence Silver -> Gold -> Gold, one observation per scrape."""
        # Observation 1, Silver: the partner is created with first_seen_on, and
        # one 'initial' row (no previous status) is recorded.
        partner = self.observe(5002, "silver", "2026-01-05")
        self.assertRecordValues(partner, [{
            "current_status": "silver",
            "first_seen_on": date(2026, 1, 5), "last_seen_on": date(2026, 1, 5),
        }])
        self.assertRecordValues(self.history_of(partner), [
            {"change_type": "initial", "previous_status": False, "new_status": "silver",
             "change_date": date(2026, 1, 5)},
        ])

        # Observation 2, Gold: same record; one 'promoted' row Silver -> Gold.
        self.assertEqual(self.observe(5002, "gold", "2026-02-02"), partner)
        self.assertRecordValues(partner, [{
            "current_status": "gold",
            "first_seen_on": date(2026, 1, 5), "last_seen_on": date(2026, 2, 2),
        }])
        self.assertRecordValues(self.history_of(partner), [
            {"change_type": "initial", "previous_status": False, "new_status": "silver",
             "change_date": date(2026, 1, 5)},
            {"change_type": "promoted", "previous_status": "silver", "new_status": "gold",
             "change_date": date(2026, 2, 2)},
        ])

        # Observation 3, Gold again: no transition, so no new row; only
        # last_seen_on moves. first_seen_on never changes.
        self.assertEqual(self.observe(5002, "gold", "2026-03-02"), partner)
        self.assertRecordValues(partner, [{
            "current_status": "gold",
            "first_seen_on": date(2026, 1, 5), "last_seen_on": date(2026, 3, 2),
        }])
        self.assertEqual(len(partner.status_history_ids), 2)
        self.assertEqual(self.Partner.with_context(active_test=False).search_count(
            [("source_id", "=", 5002)]), 1)

    def test_ranking_types_promotions_and_demotions(self):
        partner = self.observe(5003, "ready", "2026-01-05")
        self.observe(5003, "gold", "2026-02-02")    # skips Silver: still one row
        self.observe(5003, "silver", "2026-03-02")
        self.assertEqual(self.history_of(partner).mapped("change_type"),
                         ["initial", "promoted", "demoted"])
        self.assertEqual(self.history_of(partner).mapped("new_status"),
                         ["ready", "gold", "silver"])

    def test_replayed_observation_adds_nothing(self):
        partner = self.observe(5004, "silver", "2026-01-05")
        self.observe(5004, "gold", "2026-02-02")
        before = self.history_of(partner).ids
        self.observe(5004, "gold", "2026-02-02")    # the same unit replayed
        self.assertEqual(self.history_of(partner).ids, before)
        self.assertEqual(partner.last_seen_on, date(2026, 2, 2))

    def test_older_observation_is_ignored(self):
        partner = self.observe(5005, "silver", "2026-01-05")
        self.observe(5005, "gold", "2026-02-02")
        self.observe(5005, "silver", "2026-01-05")  # a late replay of the first run
        self.assertEqual(partner.current_status, "gold")
        self.assertEqual(self.history_of(partner).mapped("change_type"), ["initial", "promoted"])
        self.assertEqual(partner.last_seen_on, date(2026, 2, 2))

    def test_unknown_status_writes_nothing(self):
        with self.assertRaises(ValidationError):
            self.observe(5006, "platinum", "2026-01-05")
        self.assertFalse(self.Partner.with_context(active_test=False).search(
            [("source_id", "=", 5006)]))
        partner = self.observe(5007, "silver", "2026-01-05")
        with self.assertRaises(ValidationError):
            self.observe(5007, "platinum", "2026-02-02", name="Renamed")
        self.assertRecordValues(partner, [{
            "name": "Partner 5007", "current_status": "silver", "last_seen_on": date(2026, 1, 5)}])
        self.assertEqual(len(partner.status_history_ids), 1)

    def test_first_seen_on_cannot_be_rewritten(self):
        partner = self.observe(5008, "gold", "2026-01-05")
        with self.assertRaises(ValidationError):
            partner.write({"first_seen_on": "2025-01-01"})
        partner.write({"first_seen_on": "2026-01-05"})  # same value: allowed
        with self.assertRaises(ValueError):
            self.Partner._record_observation(
                {"source_id": 5008, "first_seen_on": "2025-01-01"}, "2026-02-02")
        self.assertEqual(partner.first_seen_on, date(2026, 1, 5))

    def test_archived_partner_reappears_with_its_history(self):
        partner = self.observe(5009, "silver", "2026-01-05")
        partner.active = False  # what a validated complete snapshot does (Stage 05)
        self.observe(5009, "gold", "2026-04-06")
        self.assertRecordValues(partner, [{
            "active": True, "current_status": "gold",
            "first_seen_on": date(2026, 1, 5), "last_seen_on": date(2026, 4, 6)}])
        self.assertEqual(self.history_of(partner).mapped("change_type"), ["initial", "promoted"])

    def test_country_move_updates_the_same_partner(self):
        partner = self.observe(5010, "ready", "2026-01-05")
        self.observe(5010, "ready", "2026-02-02", country_id=self.egypt.id)
        self.assertEqual(partner.country_id, self.egypt)
        self.assertEqual(len(partner.status_history_ids), 1)

    def test_history_rules_in_database_and_model(self):
        partner = self.observe(5011, "silver", "2026-01-05")
        base = {"partner_id": partner.id, "change_date": "2026-02-02"}
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"), self.env.cr.savepoint():
            self.History.create({**base, "change_type": "initial", "new_status": "gold"})
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"), self.env.cr.savepoint():
            self.History.create({**base, "change_type": "initial", "previous_status": "silver",
                                 "new_status": "gold"})
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"), self.env.cr.savepoint():
            self.History.create({**base, "change_type": "promoted", "previous_status": "gold",
                                 "new_status": "gold"})
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            self.History.create({**base, "change_type": "promoted", "previous_status": "gold",
                                 "new_status": "silver"})
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            self.History.create({**base, "change_date": "2025-12-01", "change_type": "promoted",
                                 "previous_status": "silver", "new_status": "gold"})

    def test_history_rows_cannot_be_changed(self):
        row = self.observe(5012, "gold", "2026-01-05").status_history_ids
        with self.assertRaises(UserError):
            row.write({"new_status": "ready"})

    def test_users_cannot_record_observations(self):
        reader = new_test_user(self.env, login="pm_history_reader", groups=READER)
        with self.assertRaises(AccessError):
            self.Partner.with_user(reader)._record_observation(
                {"source_id": 5013, "name": "Forged", "current_status": "gold",
                 "country_id": self.belgium.id}, "2026-01-05")

    def test_demo_history_is_consistent(self):
        demo_partners = self.Partner.with_context(active_test=False).search([("is_demo", "=", True)])
        if not demo_partners:
            self.skipTest("this database has no demo data")
        for partner in demo_partners:
            rows = self.history_of(partner)
            self.assertEqual(rows[0].change_type, "initial", partner.name)
            self.assertEqual(rows[0].change_date, partner.first_seen_on, partner.name)
            for before, after in zip(rows, rows[1:]):
                self.assertEqual(after.previous_status, before.new_status, partner.name)
            self.assertEqual(rows[-1].new_status, partner.current_status, partner.name)
