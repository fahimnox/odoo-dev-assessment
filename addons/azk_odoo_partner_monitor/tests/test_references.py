from datetime import date

from psycopg2 import IntegrityError

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import PartnerMonitorCase

ACME = {"source_key": "acme", "name": "Acme Corp"}
GLOBEX = {"source_key": "globex", "name": "Globex"}


@tagged("post_install", "-at_install")
class TestReferences(PartnerMonitorCase):
    """Invariant 4 of Stage 03: reference removal is reversible and keeps its
    history (decision D-10: one record per listing interval)."""

    def setUp(self):
        super().setUp()
        self.partner = self.observe(7001, "gold", "2026-01-05")

    def references(self, key):
        return self.partner.reference_ids.filtered(lambda r: r.source_key == key).sorted("id")

    def test_new_references_are_active(self):
        added, removed = self.partner._sync_references([ACME, GLOBEX], "2026-01-05", complete=True)
        self.assertEqual(len(added), 2)
        self.assertFalse(removed)
        self.assertRecordValues(added.sorted("source_key"), [
            {"source_key": "acme", "name": "Acme Corp", "is_active": True,
             "added_on": date(2026, 1, 5), "removed_on": False},
            {"source_key": "globex", "name": "Globex", "is_active": True,
             "added_on": date(2026, 1, 5), "removed_on": False},
        ])

    def test_complete_snapshot_closes_missing_reference(self):
        self.partner._sync_references([ACME, GLOBEX], "2026-01-05", complete=True)
        added, removed = self.partner._sync_references([ACME], "2026-02-02", complete=True)
        self.assertFalse(added)
        self.assertRecordValues(removed, [{"source_key": "globex", "is_active": False,
                                           "removed_on": date(2026, 2, 2)}])
        self.assertRecordValues(self.references("acme"), [{"is_active": True, "removed_on": False}])
        # Regression: the closure is in the database at once, so the
        # one-active-per-key index sees it (the ORM would otherwise delay it).
        self.env.cr.execute("SELECT is_active FROM azk_odoo_partner_monitor_reference WHERE id = %s",
                            [removed.id])
        self.assertIs(self.env.cr.fetchone()[0], False)

    def test_partial_snapshot_never_removes(self):
        self.partner._sync_references([ACME, GLOBEX], "2026-01-05", complete=True)
        added, removed = self.partner._sync_references([ACME], "2026-02-02", complete=False)
        self.assertFalse(added)
        self.assertFalse(removed)
        self.assertTrue(all(self.partner.reference_ids.mapped("is_active")))

    def test_returning_reference_opens_a_new_interval(self):
        self.partner._sync_references([ACME, GLOBEX], "2026-01-05", complete=True)
        self.partner._sync_references([ACME], "2026-02-02", complete=True)
        self.partner._sync_references([ACME, GLOBEX], "2026-03-02", complete=True)
        self.assertRecordValues(self.references("globex"), [
            {"is_active": False, "added_on": date(2026, 1, 5), "removed_on": date(2026, 2, 2)},
            {"is_active": True, "added_on": date(2026, 3, 2), "removed_on": False},
        ])
        self.assertEqual(len(self.references("acme")), 1)

    def test_same_snapshot_twice_changes_nothing(self):
        self.partner._sync_references([ACME, GLOBEX], "2026-01-05", complete=True)
        before = self.partner.reference_ids.read(["source_key", "is_active", "added_on", "removed_on"])
        added, removed = self.partner._sync_references([ACME, GLOBEX], "2026-01-05", complete=True)
        self.assertFalse(added or removed)
        self.assertEqual(
            self.partner.reference_ids.read(["source_key", "is_active", "added_on", "removed_on"]), before)

    def test_snapshot_duplicates_and_renames(self):
        added, _removed = self.partner._sync_references(
            [ACME, {"source_key": "acme", "name": "Acme Corp"}], "2026-01-05", complete=True)
        self.assertEqual(len(added), 1)
        self.partner._sync_references([{"source_key": "acme", "name": "Acme Corporation"}],
                                      "2026-02-02", complete=True)
        self.assertRecordValues(self.references("acme"), [
            {"name": "Acme Corporation", "is_active": True, "added_on": date(2026, 1, 5)}])
        with self.assertRaises(ValidationError):
            self.partner._sync_references([{"source_key": "", "name": "No key"}], "2026-02-02", True)

    def test_reference_rules_in_database(self):
        base = {"partner_id": self.partner.id, "name": "Initech", "added_on": "2026-01-05"}
        self.Reference.create({**base, "source_key": "initech"})
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"), self.env.cr.savepoint():
            self.Reference.create({**base, "source_key": "initech"})  # second active record
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"), self.env.cr.savepoint():
            self.Reference.create({**base, "source_key": "x", "removed_on": "2026-02-02"})
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"), self.env.cr.savepoint():
            self.Reference.create({**base, "source_key": "y", "is_active": False})
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"), self.env.cr.savepoint():
            self.Reference.create({**base, "source_key": "z", "is_active": False,
                                   "removed_on": "2025-12-01"})
