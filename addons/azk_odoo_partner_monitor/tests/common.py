from odoo.tests import TransactionCase

READER = "base.group_user,azk_odoo_partner_monitor.group_reader"
MANAGER = "base.group_user,azk_odoo_partner_monitor.group_manager"


class PartnerMonitorCase(TransactionCase):
    """Shared fixtures: the models and two countries observed from the website.

    Test records use positive website ids, like real scraped data. The demo
    records (negative ids, "demo-" country keys) may also exist in the test
    database, so tests never count whole tables.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Country = cls.env["azk_odoo_partner_monitor.country"]
        cls.Partner = cls.env["azk_odoo_partner_monitor.partner"]
        cls.History = cls.env["azk_odoo_partner_monitor.status.history"]
        cls.Reference = cls.env["azk_odoo_partner_monitor.reference"]
        cls.Run = cls.env["azk_odoo_partner_monitor.sync.run"]
        cls.WorkItem = cls.env["azk_odoo_partner_monitor.work.item"]
        cls.SyncError = cls.env["azk_odoo_partner_monitor.sync.error"]
        cls.belgium = cls.Country._record_observation(
            {"source_key": "20", "name": "Belgium", "total_partner_count": 2})
        cls.egypt = cls.Country._record_observation(
            {"source_key": "65", "name": "Egypt", "total_partner_count": 1})

    def observe(self, source_id, status, observed_on, **values):
        """Record one listing observation, as the sync engine will."""
        values.setdefault("name", f"Partner {source_id}")
        values.setdefault("country_id", self.belgium.id)
        return self.Partner._record_observation(
            {"source_id": source_id, "current_status": status, **values}, observed_on)

    @staticmethod
    def history_of(partner):
        """The partner's status history, oldest first."""
        return partner.status_history_ids.sorted(lambda row: (row.change_date, row.id))
