from lxml import etree

from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import new_test_user, tagged

from ..models.sync_run import NOTIFY_USER_PARAM
from .common import MANAGER, READER, PartnerMonitorCase


@tagged("post_install", "-at_install")
class TestSecurity(PartnerMonitorCase):
    """TP-PM-05: readers read, managers operate the sync, nobody edits scraped
    data, audit events or sync checkpoints directly."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.reader = new_test_user(cls.env, login="pm_reader", groups=READER)
        cls.manager = new_test_user(cls.env, login="pm_manager", groups=MANAGER)
        cls.employee = new_test_user(cls.env, login="pm_employee", groups="base.group_user")
        cls.sysadmin = new_test_user(cls.env, login="pm_sysadmin", groups="base.group_user,base.group_system")
        cls.company_b = cls.env["res.company"].create({"name": "Partner Monitor Company B"})
        cls.reader_b = new_test_user(cls.env, login="pm_reader_b", groups=READER,
                                     company_id=cls.company_b.id,
                                     company_ids=[Command.set(cls.company_b.ids)])
        cls.partner = cls.Partner._record_observation(
            {"source_id": 8001, "name": "Acme", "current_status": "gold",
             "country_id": cls.belgium.id}, "2026-01-05")
        cls.partner._sync_references([{"source_key": "acme", "name": "Acme Client"}],
                                     "2026-01-05", complete=True)
        cls.sync_run = cls.Run.create({"trigger": "daily", "state": "partial"})
        cls.failed_item = cls.WorkItem.create({
            "kind": "country_partners", "run_id": cls.sync_run.id, "country_id": cls.belgium.id,
            "state": "failed", "attempt_count": 5, "last_error": "TimeoutError"})
        cls.error = cls.SyncError.create({
            "run_id": cls.sync_run.id, "work_item_id": cls.failed_item.id,
            "error_class": "TimeoutError", "message": "listing page timed out"})

    def business_records(self):
        return [self.belgium, self.partner, self.partner.status_history_ids,
                self.partner.reference_ids, self.sync_run]

    def test_reader_reads_business_data_and_runs(self):
        for records in self.business_records():
            with self.subTest(model=records._name):
                as_reader = records.with_user(self.reader)
                self.assertEqual(as_reader.search([("id", "in", records.ids)]), as_reader)
                as_reader.read(["display_name"])

    def test_reader_cannot_write_create_or_delete(self):
        for records in self.business_records():
            with self.subTest(model=records._name):
                as_reader = records.with_user(self.reader)
                for operation in ("write", "create", "unlink"):
                    with self.assertRaises(AccessError):
                        as_reader.check_access(operation)
                with self.assertRaises(AccessError):
                    as_reader.unlink()
        with self.assertRaises(AccessError):
            self.partner.with_user(self.reader).write({"current_status": "ready"})
        with self.assertRaises(AccessError):
            self.History.with_user(self.reader).create({
                "partner_id": self.partner.id, "previous_status": "gold", "new_status": "silver",
                "change_type": "demoted", "change_date": "2026-02-02"})
        with self.assertRaises(AccessError):
            self.partner.reference_ids.with_user(self.reader).write({"is_active": False})

    def test_reader_cannot_see_work_items_or_errors(self):
        with self.assertRaises(AccessError):
            self.WorkItem.with_user(self.reader).search([])
        with self.assertRaises(AccessError):
            self.SyncError.with_user(self.reader).search([])
        with self.assertRaises(AccessError):
            self.sync_run.with_user(self.reader).read(["work_item_ids"])

    def test_reader_cannot_run_manager_actions(self):
        with self.assertRaises(AccessError):
            self.Run.with_user(self.reader).action_sync_now()
        with self.assertRaises(AccessError):
            self.belgium.with_user(self.reader).action_mark_for_rescrape()
        with self.assertRaises(AccessError):
            self.partner.with_user(self.reader).action_mark_for_rescrape()
        with self.assertRaises(AccessError):
            self.failed_item.with_user(self.reader).action_retry()
        self.assertFalse(self.belgium.to_reprocess_partners)
        self.assertEqual(self.failed_item.state, "failed")

    def test_manager_operates_the_sync(self):
        self.WorkItem.search([("kind", "=", "country_list"), ("state", "=", "pending")]).state = "cancelled"
        runs_before = self.Run.search([])
        self.Run.with_user(self.manager).action_sync_now()
        new_run = self.Run.search([]) - runs_before
        self.assertRecordValues(new_run, [{"trigger": "manual", "state": "running"}])
        self.assertRecordValues(new_run.work_item_ids, [{"kind": "country_list", "state": "pending"}])
        # A second click while the first sync is queued queues nothing more.
        self.Run.with_user(self.manager).action_sync_now()
        self.assertEqual(self.Run.search([]) - runs_before, new_run)

        self.failed_item.with_user(self.manager).action_retry()
        self.assertRecordValues(self.failed_item, [{"state": "pending", "attempt_count": 0}])
        # Regression: the retry is in the database at once, so the
        # one-pending-per-target index sees it before anything else is queued.
        self.env.cr.execute("SELECT state FROM azk_odoo_partner_monitor_work_item WHERE id = %s",
                            [self.failed_item.id])
        self.assertEqual(self.env.cr.fetchone()[0], "pending")

        self.belgium.with_user(self.manager).action_mark_for_rescrape()
        self.partner.with_user(self.manager).action_mark_for_rescrape()
        self.assertTrue(self.belgium.to_reprocess_partners)
        self.assertTrue(self.partner.to_reprocess_references)

    def test_retry_skips_work_that_is_queued_again(self):
        queued = self.WorkItem.create({"kind": "country_partners", "run_id": self.sync_run.id,
                                       "country_id": self.belgium.id})
        self.failed_item.with_user(self.manager).action_retry()
        self.assertEqual(self.failed_item.state, "failed")
        self.assertEqual(queued.state, "pending")

    def test_manager_cannot_edit_data_events_or_checkpoints(self):
        with self.assertRaises(AccessError):
            self.partner.with_user(self.manager).write({"current_status": "ready"})
        with self.assertRaises(AccessError):
            self.History.with_user(self.manager).create({
                "partner_id": self.partner.id, "previous_status": "gold", "new_status": "silver",
                "change_type": "demoted", "change_date": "2026-02-02"})
        with self.assertRaises(AccessError):
            self.failed_item.with_user(self.manager).write({"state": "done"})
        with self.assertRaises(AccessError):
            self.Run.with_user(self.manager).create({"trigger": "manual"})
        with self.assertRaises(AccessError):
            self.error.with_user(self.manager).unlink()
        # Managers do read the sync records.
        self.assertEqual(self.failed_item.with_user(self.manager).read(["state"])[0]["state"], "failed")
        self.assertEqual(self.sync_run.with_user(self.manager).error_count, 1)

    def test_user_without_partner_monitor_group_sees_nothing(self):
        for model in (self.Country, self.Partner, self.History, self.Reference, self.Run):
            with self.subTest(model=model._name), self.assertRaises(AccessError):
                model.with_user(self.employee).search([])

    def test_data_is_shared_across_companies(self):
        """Scraped data has no company: a reader of another company sees the same records."""
        records = self.Partner.search([("source_id", "=", 8001)])
        self.assertEqual(self.Partner.with_user(self.reader_b).search([("source_id", "=", 8001)]).ids,
                         records.ids)
        self.assertNotIn("company_id", self.Partner._fields)
        self.assertFalse(self.env["ir.rule"].search([("model_id.model", "like", "azk_odoo_partner_monitor.")]))

    def test_settings_are_for_system_administrators(self):
        with self.assertRaises(AccessError):
            self.env["res.config.settings"].with_user(self.manager).create({})
        settings = self.env["res.config.settings"].with_user(self.sysadmin).create(
            {"partner_monitor_notify_user_id": self.manager.id})
        settings.set_values()
        self.assertEqual(self.env["ir.config_parameter"].get_param(NOTIFY_USER_PARAM), str(self.manager.id))

    def test_menus_follow_the_groups(self):
        Menu = self.env["ir.ui.menu"]
        menus = {xmlid: self.env.ref(f"azk_odoo_partner_monitor.{xmlid}").id for xmlid in (
            "menu_root", "menu_partners", "menu_sync_runs", "menu_work_items", "menu_settings")}

        def visible(user):
            ids = Menu.with_user(user)._visible_menu_ids()
            return {xmlid for xmlid, menu_id in menus.items() if menu_id in ids}

        self.assertEqual(visible(self.reader), {"menu_root", "menu_partners", "menu_sync_runs"})
        self.assertEqual(visible(self.manager),
                         {"menu_root", "menu_partners", "menu_sync_runs", "menu_work_items"})
        self.assertFalse(visible(self.employee))

    def test_views_load_for_each_role(self):
        """Every view renders for readers, without manager-only fields."""
        for model in (self.Country, self.Partner, self.History, self.Reference, self.Run):
            with self.subTest(model=model._name):
                views = model.with_user(self.reader).get_views(
                    [(False, "list"), (False, "form"), (False, "search")])
                self.assertEqual(set(views["views"]), {"list", "form", "search"})
        form = self.Run.with_user(self.reader).get_views([(False, "form")])["views"]["form"]["arch"]
        names = {node.get("name") for node in etree.fromstring(form).iter("field")}
        self.assertNotIn("error_ids", names)
        self.assertNotIn("work_item_ids", names)
        for model in (self.WorkItem, self.SyncError):
            with self.subTest(model=model._name):
                views = model.with_user(self.manager).get_views([(False, "list"), (False, "form")])
                self.assertEqual(set(views["views"]), {"list", "form"})
