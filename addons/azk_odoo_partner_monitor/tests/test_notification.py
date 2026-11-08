from odoo.addons.mail.tests.common import MockEmail
from odoo.tests import new_test_user, tagged
from odoo.tools import mute_logger

from ..models.sync_run import NOTIFY_USER_PARAM
from .common import PartnerMonitorCase


@tagged("post_install", "-at_install")
class TestFailureNotification(PartnerMonitorCase, MockEmail):
    """The configured user is notified through Odoo's mail system: a real
    message on the run's chatter, addressed to the user's partner. The mail
    gateway is mocked, so no email leaves the test."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.inbox_user = new_test_user(cls.env, login="pm_inbox_user", groups="base.group_user",
                                       notification_type="inbox", email="inbox.user@example.com")
        cls.email_user = new_test_user(cls.env, login="pm_email_user", groups="base.group_user",
                                       notification_type="email", email="email.user@example.com")
        cls.note = cls.env.ref("mail.mt_note")

    def set_recipient(self, value):
        self.env["ir.config_parameter"].set_param(NOTIFY_USER_PARAM, str(value))

    def make_run(self, state="partial", country_name="Belgium"):
        run = self.Run.create({"trigger": "daily"})
        country = self.Country._record_observation({"source_key": "notify-1", "name": country_name})
        item = self.WorkItem.create({
            "kind": "country_partners", "run_id": run.id, "country_id": country.id,
            "state": "failed", "attempt_count": 5,
            "last_error": "TimeoutError: listing page 2 timed out\nTraceback ..."})
        self.WorkItem.create({"kind": "country_list", "run_id": run.id, "state": "done"})
        self.SyncError.create({"run_id": run.id, "work_item_id": item.id, "country_id": country.id,
                               "error_class": "TimeoutError", "message": "listing page 2 timed out"})
        run.state = state
        return run

    def notifications(self, message):
        return self.env["mail.notification"].search([("mail_message_id", "=", message.id)])

    def test_default_recipient_is_the_administrator(self):
        self.assertEqual(self.env["ir.config_parameter"].get_param(NOTIFY_USER_PARAM),
                         str(self.env.ref("base.user_admin").id))

    def test_note_reaches_an_inbox_user(self):
        self.set_recipient(self.inbox_user.id)
        run = self.make_run()
        with self.mock_mail_gateway():
            message = run._notify_failure()
        self.assertEqual(len(message), 1)
        self.assertRecordValues(message, [{
            "model": run._name, "res_id": run.id, "message_type": "comment",
            "subtype_id": self.note.id, "partner_ids": self.inbox_user.partner_id.ids}])
        self.assertRecordValues(self.notifications(message), [{
            "res_partner_id": self.inbox_user.partner_id.id, "notification_type": "inbox"}])
        self.assertFalse(self._new_mails, "an Inbox user gets no email")
        self.assertIn("1 units done, 1 failed", message.body)
        self.assertIn("Country partners: Belgium: TimeoutError: listing page 2 timed out", message.body)
        self.assertTrue(run.notified_at)
        self.assertEqual(run.message_ids.filtered(lambda m: m.message_type == "comment"), message)

    def test_note_follows_the_email_preference(self):
        self.set_recipient(self.email_user.id)
        run = self.make_run(state="failed")
        with self.mock_mail_gateway():
            message = run._notify_failure()
        self.assertRecordValues(self.notifications(message), [{
            "res_partner_id": self.email_user.partner_id.id, "notification_type": "email"}])
        self.assertTrue(self._new_mails.filtered(
            lambda mail: self.email_user.partner_id in mail.recipient_ids))

    def test_note_is_posted_once_and_only_for_problems(self):
        self.set_recipient(self.inbox_user.id)
        run = self.make_run()
        done_run = self.make_run(state="done")
        with self.mock_mail_gateway():
            first = (run | done_run)._notify_failure()
            second = (run | done_run)._notify_failure()
        self.assertEqual(first.res_id, run.id)
        self.assertFalse(second)
        self.assertFalse(done_run.notified_at)

    def test_invalid_recipient_falls_back_to_the_administrator(self):
        admin = self.env.ref("base.user_admin")
        portal = new_test_user(self.env, login="pm_portal_user", groups="base.group_portal")
        for value in ("999999999", "not-a-user", portal.id):
            with self.subTest(value=value), mute_logger("odoo.addons.azk_odoo_partner_monitor.models.sync_run"):
                self.set_recipient(value)
                self.assertEqual(self.Run._get_failure_recipient(), admin)

    def test_website_text_is_escaped_in_the_note(self):
        self.set_recipient(self.inbox_user.id)
        run = self.make_run(country_name="<script>alert(1)</script>")
        with self.mock_mail_gateway():
            message = run._notify_failure()
        self.assertNotIn("<script>", message.body)
        self.assertIn("&lt;script&gt;", message.body)

    def test_readers_see_the_note_on_the_run(self):
        reader = new_test_user(self.env, login="pm_note_reader",
                               groups="base.group_user,azk_odoo_partner_monitor.group_reader")
        self.set_recipient(self.inbox_user.id)
        run = self.make_run()
        with self.mock_mail_gateway():
            message = run._notify_failure()
        self.assertIn("ended as Partial", message.with_user(reader).read(["body"])[0]["body"])
