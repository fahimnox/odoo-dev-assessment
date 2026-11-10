from odoo import SUPERUSER_ID, api, fields
from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger

from ..services import urls
from .common import ANDORRA, FixtureSite

WORKER_LOG = "odoo.addons.azk_odoo_partner_monitor.models.worker"
# Website ids no real country uses. Each page answers with the Andorra cards,
# whose links name country 1, so nothing on it belongs to these countries:
# the units finish without storing any partner.
RACE_KEYS = ("900001", "900002", "900003")


@tagged("post_install", "-at_install")
class TestWorkerConcurrency(TransactionCase):
    """TP-PM-14 with real concurrency: separate database connections, as two
    cron workers or two servers would use.

    Other connections cannot see the test transaction, so the units are
    committed by a separate cursor and deleted again after each test.
    """

    def setUp(self):
        super().setUp()
        with self.registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            run = env["azk_odoo_partner_monitor.sync.run"].with_context(
                mail_create_nolog=True, mail_create_nosubscribe=True).create({"trigger": "manual"})
            countries = env["azk_odoo_partner_monitor.country"].create(
                [{"source_key": key, "name": f"Concurrency test {key}"} for key in RACE_KEYS])
            units = env["azk_odoo_partner_monitor.work.item"].create(
                [{"kind": "country_partners", "run_id": run.id, "country_id": country.id}
                 for country in countries])
            self.run_id, self.country_ids, self.unit_ids = run.id, countries.ids, units.ids
        self.addCleanup(self.delete_committed_data)
        self.site = FixtureSite({urls.listing_url(key): (urls.listing_url(key), ANDORRA[1])
                                 for key in RACE_KEYS})
        self.now = fields.Datetime.now()

    def delete_committed_data(self):
        with self.registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            env["azk_odoo_partner_monitor.sync.run"].browse(self.run_id).unlink()  # cascades to its units
            env["azk_odoo_partner_monitor.country"].with_context(active_test=False).browse(
                self.country_ids).unlink()

    @staticmethod
    def worker(cr):
        return api.Environment(cr, SUPERUSER_ID, {})["azk_odoo_partner_monitor.worker"]

    def unit_states(self):
        with self.registry.cursor() as cr:
            units = api.Environment(cr, SUPERUSER_ID, {})["azk_odoo_partner_monitor.work.item"]
            return units.browse(self.unit_ids).read(["state", "attempt_count"])

    def test_two_workers_never_get_the_same_unit(self):
        first, second, third = self.unit_ids
        with self.registry.cursor() as cr_a, self.registry.cursor() as cr_b, mute_logger(WORKER_LOG):
            a, b = self.worker(cr_a), self.worker(cr_b)
            unit_a = a._claim_next(self.now)
            unit_b = b._claim_next(self.now)  # A's unit is locked: B skips it
            self.assertEqual((unit_a.id, unit_b.id), (first, second))
            self.assertTrue(a._run_unit(unit_a, self.site, self.now))
            self.assertTrue(b._run_unit(unit_b, self.site, self.now))
            self.assertEqual(a._claim_next(self.now).id, third)
            self.assertFalse(b._claim_next(self.now))  # what is left is locked by A
            self.assertTrue(a._run_unit(a.env["azk_odoo_partner_monitor.work.item"].browse(third),
                                        self.site, self.now))
            cr_a.commit()  # A's batch is durable
            # B's transaction began before A's commit. PostgreSQL refuses to lock
            # a unit that A changed since then; B stops instead of redoing it.
            self.assertFalse(b._claim_next(self.now))
            cr_b.commit()
        self.assertEqual(sorted(self.site.requested), sorted(urls.listing_url(key) for key in RACE_KEYS))
        self.assertEqual(self.unit_states(), [
            {"id": unit_id, "state": "done", "attempt_count": 0} for unit_id in self.unit_ids])

    def test_a_crashed_worker_releases_its_unit(self):
        with self.registry.cursor() as cr_a:
            claimed = self.worker(cr_a)._claim_next(self.now)
            with self.registry.cursor() as cr_b:
                self.assertNotEqual(self.worker(cr_b)._claim_next(self.now).id, claimed.id)
                cr_b.rollback()
            # A ends without a commit, as a killed process does: PostgreSQL
            # rolls its transaction back and drops its row locks.
            cr_a.rollback()
        with self.registry.cursor() as cr_c:
            self.assertEqual(self.worker(cr_c)._claim_next(self.now).id, claimed.id)
            cr_c.rollback()
        self.assertEqual({state["state"] for state in self.unit_states()}, {"pending"})
