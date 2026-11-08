from datetime import date

from psycopg2 import IntegrityError

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from ..services.urls import is_canonical_partner_url
from .common import PartnerMonitorCase

COUNTRY = "azk_odoo_partner_monitor.country"
PARTNER = "azk_odoo_partner_monitor.partner"
HISTORY = "azk_odoo_partner_monitor.status.history"
REFERENCE = "azk_odoo_partner_monitor.reference"

# The four models and their fields exactly as the assessment specifies them
# (PDF pp. 3-4): field name -> (type, related model or None).
PDF_FIELDS = {
    COUNTRY: {
        "name": ("char", None),
        "active": ("boolean", None),
        "total_partner_count": ("integer", None),
        "to_reprocess_partners": ("boolean", None),
    },
    PARTNER: {
        "name": ("char", None),
        "partner_url": ("char", None),
        "current_status": ("selection", None),
        "country_id": ("many2one", COUNTRY),
        "first_seen_on": ("date", None),
        "retention_rate": ("float", None),
        "total_references_count": ("integer", None),
        "largest_project_size": ("integer", None),
        "average_project_size": ("float", None),
        "to_reprocess_references": ("boolean", None),
        "status_history_ids": ("one2many", HISTORY),
        "reference_ids": ("one2many", REFERENCE),
    },
    HISTORY: {
        "partner_id": ("many2one", PARTNER),
        "previous_status": ("selection", None),
        "new_status": ("selection", None),
        "change_date": ("date", None),
        "change_type": ("selection", None),
    },
    REFERENCE: {
        "partner_id": ("many2one", PARTNER),
        "name": ("char", None),
        "is_active": ("boolean", None),
        "added_on": ("date", None),
        "removed_on": ("date", None),
    },
}


def selection_keys(model, name):
    return [key for key, _label in model._fields[name].selection]


@tagged("post_install", "-at_install")
class TestDataModel(PartnerMonitorCase):
    """TP-PM-01 and TP-PM-02: the PDF's models and fields, identities,
    uniqueness and relations."""

    def test_required_models_and_field_types_match_the_pdf(self):
        for model_name, fields_spec in PDF_FIELDS.items():
            model = self.env[model_name]
            for field_name, (field_type, comodel) in fields_spec.items():
                with self.subTest(model=model_name, field=field_name):
                    field = model._fields[field_name]
                    self.assertEqual(field.type, field_type)
                    if comodel:
                        self.assertEqual(field.comodel_name, comodel)
        self.assertTrue(self.Country.default_get(["active"])["active"])
        self.assertEqual(selection_keys(self.Partner, "current_status"), ["ready", "silver", "gold"])
        self.assertEqual(selection_keys(self.History, "previous_status"), ["ready", "silver", "gold"])
        self.assertEqual(selection_keys(self.History, "new_status"), ["ready", "silver", "gold"])
        self.assertEqual(set(selection_keys(self.History, "change_type")),
                         {"initial", "promoted", "demoted"})
        self.assertEqual(self.Partner._fields["status_history_ids"].inverse_name, "partner_id")
        self.assertEqual(self.Partner._fields["reference_ids"].inverse_name, "partner_id")

    def test_country_identity_is_the_website_id(self):
        again = self.Country._record_observation(
            {"source_key": "20", "name": "Belgique", "total_partner_count": 3})
        self.assertEqual(again, self.belgium)
        self.assertRecordValues(self.belgium, [{"name": "Belgique", "total_partner_count": 3}])
        self.belgium.active = False
        self.Country._record_observation({"source_key": "20", "name": "Belgique"})
        self.assertTrue(self.belgium.active)
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"), self.env.cr.savepoint():
            self.Country.create({"name": "Another Belgium", "source_key": "20"})
        with self.assertRaises(ValidationError):
            self.belgium.write({"source_key": "21"})

    def test_partner_identity_is_the_website_id(self):
        partner = self.observe(6001, "gold", "2026-01-05", name="Acme")
        self.assertEqual(self.observe(6001, "gold", "2026-01-05", name="Acme Renamed"), partner)
        self.assertEqual(partner.name, "Acme Renamed")
        # Same name, different website id: a different partner.
        other = self.observe(6002, "gold", "2026-01-05", name="Acme Renamed")
        self.assertNotEqual(other, partner)
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"), self.env.cr.savepoint():
            self.Partner.create({"name": "Copy", "source_id": 6001, "current_status": "gold",
                                 "country_id": self.belgium.id, "first_seen_on": "2026-01-05"})
        with self.assertRaises(ValidationError):
            partner.write({"source_id": 6003})

    def test_demo_and_website_ids_never_collide(self):
        live = {"name": "Live", "current_status": "gold", "country_id": self.belgium.id,
                "first_seen_on": "2026-01-05"}
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"), self.env.cr.savepoint():
            self.Partner.create({**live, "source_id": -6100})                 # negative, not demo
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"), self.env.cr.savepoint():
            self.Partner.create({**live, "source_id": 6100, "is_demo": True})  # demo, positive
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"), self.env.cr.savepoint():
            self.Country.create({"name": "Fake", "source_key": "demo-99"})    # demo key, not demo
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"), self.env.cr.savepoint():
            self.Country.create({"name": "Fake", "source_key": "99", "is_demo": True})

    def test_relations_are_enforced(self):
        partner = self.observe(6201, "silver", "2026-01-05")
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"), self.env.cr.savepoint():
            self.Partner.create({"name": "No country", "source_id": 6202, "current_status": "gold",
                                 "first_seen_on": "2026-01-05"})
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"), self.env.cr.savepoint():
            self.History.create({"new_status": "gold", "change_type": "initial",
                                 "change_date": "2026-01-05"})
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"), self.env.cr.savepoint():
            self.belgium.unlink()  # ondelete='restrict': partners keep their country
        # Deleting a partner (superuser only) removes its own history and references.
        partner._sync_references([{"source_key": "a", "name": "A"}], "2026-01-05", complete=True)
        history_ids, reference_ids = partner.status_history_ids.ids, partner.reference_ids.ids
        partner.unlink()
        self.assertFalse(self.History.browse(history_ids).exists())
        self.assertFalse(self.Reference.browse(reference_ids).exists())

    def test_work_item_target_matches_its_kind(self):
        run = self.Run.create({"trigger": "manual"})
        partner = self.observe(6301, "gold", "2026-01-05")
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"), self.env.cr.savepoint():
            self.WorkItem.create({"kind": "country_partners", "run_id": run.id})
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"), self.env.cr.savepoint():
            self.WorkItem.create({"kind": "partner_details", "run_id": run.id,
                                  "partner_id": partner.id, "country_id": self.belgium.id})
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"), self.env.cr.savepoint():
            self.WorkItem.create({"kind": "country_list", "run_id": run.id,
                                  "country_id": self.belgium.id})

    def test_one_pending_work_item_per_target(self):
        run = self.Run.create({"trigger": "manual"})
        first = self.WorkItem._enqueue("country_partners", run, country=self.belgium)
        self.assertEqual(self.WorkItem._enqueue("country_partners", run, country=self.belgium), first)
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"), self.env.cr.savepoint():
            self.WorkItem.create({"kind": "country_partners", "run_id": run.id,
                                  "country_id": self.belgium.id})
        # Other targets, and finished work for the same target, are allowed.
        self.assertTrue(self.WorkItem._enqueue("country_partners", run, country=self.egypt))
        first.state = "done"
        second = self.WorkItem._enqueue("country_partners", run, country=self.belgium)
        self.assertNotEqual(second, first)

    def test_partner_url_must_be_canonical(self):
        good = "https://www.odoo.com/partners/acme-solutions-6401"
        partner = self.observe(6401, "gold", "2026-01-05", partner_url=good)
        self.assertEqual(partner.partner_url, good)
        for bad in (
            "https://www.odoo.com/partners/acme-solutions-6401?country_id=20",
            "https://www.odoo.com/partners/acme-solutions-6401#top",
            "https://www.odoo.com/partners/acme-solutions-9999",
            "http://www.odoo.com/partners/acme-solutions-6401",
            "https://example.com/partners/acme-solutions-6401",
            "https://www.odoo.com/partners/country/acme-6401",
        ):
            with self.subTest(url=bad), self.assertRaises(ValidationError), self.env.cr.savepoint():
                partner.write({"partner_url": bad})

    def test_canonical_url_rule(self):
        self.assertTrue(is_canonical_partner_url("https://www.odoo.com/partners/acme-12", 12))
        self.assertTrue(is_canonical_partner_url("https://www.odoo.com/partners/12", 12))
        self.assertFalse(is_canonical_partner_url("https://www.odoo.com/partners/acme-12?", 12))
        self.assertFalse(is_canonical_partner_url("https://www.odoo.com/partners/acme-12/", 12))
        self.assertFalse(is_canonical_partner_url("https://www.odoo.com/partners/acme-123", 12))
        self.assertFalse(is_canonical_partner_url("https://www.odoo.com/partners/page/12", 12))
        self.assertFalse(is_canonical_partner_url("", 12))

    def test_unknown_metric_is_not_zero(self):
        partner = self.observe(6501, "ready", "2026-01-05", retention_rate=None,
                               largest_project_size=0, average_project_size=None,
                               total_references_count=0)
        self.assertRecordValues(partner, [{
            "retention_rate": 0.0, "retention_rate_known": False,
            "largest_project_size": 0, "largest_project_size_known": True,
            "average_project_size": 0.0, "average_project_size_known": False,
            "total_references_count": 0, "total_references_count_known": True,
        }])
        self.observe(6501, "ready", "2026-02-02", retention_rate=87.5)
        self.assertRecordValues(partner, [{"retention_rate": 87.5, "retention_rate_known": True}])
        self.observe(6501, "ready", "2026-03-02")  # metric not observed: unchanged
        self.assertRecordValues(partner, [{"retention_rate": 87.5, "retention_rate_known": True}])
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"), self.env.cr.savepoint():
            partner.write({"average_project_size": 12.5})  # a value without the known flag
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"), self.env.cr.savepoint():
            partner.write({"largest_project_size": -1})

    def test_observation_cannot_set_protected_fields(self):
        for field_name in ("first_seen_on", "last_seen_on", "is_demo", "to_reprocess_references", "active"):
            with self.subTest(field=field_name), self.assertRaises(ValueError):
                self.Partner._record_observation(
                    {"source_id": 6601, "current_status": "gold", "country_id": self.belgium.id,
                     "name": "Acme", field_name: date(2020, 1, 1)}, "2026-01-05")
        with self.assertRaises(ValueError):
            self.Country._record_observation({"source_key": "77", "name": "X", "is_demo": True})

    def test_demo_records_are_labeled(self):
        demo_countries = self.Country.with_context(active_test=False).search([("is_demo", "=", True)])
        demo_partners = self.Partner.with_context(active_test=False).search([("is_demo", "=", True)])
        if not demo_partners:
            self.skipTest("this database has no demo data")
        self.assertTrue(all(c.name.startswith("Demo ") and c.source_key.startswith("demo-")
                            for c in demo_countries))
        self.assertTrue(all(p.name.startswith("Demo ") and p.source_id < 0 and not p.partner_url
                            for p in demo_partners))
