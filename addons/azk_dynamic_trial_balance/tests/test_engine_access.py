import logging

from odoo import Command
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import new_test_user, tagged

from .common import TB_BASE_POSTED, TrialBalanceCase

_logger = logging.getLogger(__name__)
READERS = "base.group_user,account.group_account_readonly"


@tagged("post_install", "-at_install")
class TestEngineAccess(TrialBalanceCase):
    """The engine's guards on TB-BASE: who may run it, what options it accepts,
    the wizard path, and how its query count grows (Stage 08)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._build_tb_base()
        su_env = cls.env(su=True)
        company_ids = [Command.set(cls.company.ids)]
        cls.reader = new_test_user(su_env, login="tb_engine_reader", groups=READERS,
                                   company_id=cls.company.id, company_ids=company_ids)
        cls.other_reader = new_test_user(su_env, login="tb_engine_other_reader", groups=READERS,
                                         company_id=cls.company.id, company_ids=company_ids)
        cls.billing = new_test_user(su_env, login="tb_engine_billing",
                                    groups="base.group_user,account.group_account_invoice",
                                    company_id=cls.company.id, company_ids=company_ids)
        cls.employee = new_test_user(su_env, login="tb_engine_employee", groups="base.group_user",
                                     company_id=cls.company.id, company_ids=company_ids)
        data_2 = cls.setup_other_company(name="AZK TB Other", currency_id=cls.company.currency_id.id)
        cls.company_2 = data_2["company"]
        cls.journal_2 = data_2["default_journal_misc"]
        plan = su_env["account.analytic.plan"].create({"name": "TB Engine Plan"})
        cls.analytic_2 = su_env["account.analytic.account"].create(
            {"name": "TB Other company", "plan_id": plan.id, "company_id": cls.company_2.id})

    def _compute(self, user, **values):
        Engine = self.env["azk_dynamic_trial_balance.engine"].with_user(user)
        Engine = Engine.with_context(allowed_company_ids=self.company.ids)
        return Engine.compute({"date_from": "2026-01-01", "date_to": "2026-01-31",
                               "company_id": self.company.id, **values})

    def test_an_accounting_reader_gets_the_same_numbers(self):
        result = self._compute(self.reader, skip_zero_balance=True)
        self.assertRowsEqual(self.engine_rows(result), TB_BASE_POSTED)

    def test_users_without_accounting_read_access_are_refused(self):
        # A billing user may read some journal items, but not the books as a
        # whole: like the standard Trial Balance, the report needs the
        # accounting read-only group.
        for user in (self.employee, self.billing):
            with self.subTest(user=user.login), self.assertRaises(AccessError):
                self._compute(user)

    def test_tampered_options_are_refused(self):
        tampered = [
            {"domain": [("id", ">", 0)]},
            {"include_unposted": "yes"},
            {"skip_zero_balance": 1},
            {"journal_id": self.journal_2.id},
            {"journal_id": "1"},
            {"analytic_account_id": self.analytic_2.id},
            {"account_prefixes": ["1%"]},
            {"account_prefixes": "1"},
            {"account_level": 3},
            {"hierarchy_only_parents": True, "account_level": 2},
            {"hierarchy_subtotals": True, "hierarchy_only_parents": True, "account_level": 2,
             "show_amount_currency": True},
            {"date_from": "2026-02-01"},
            {"date_to": "not a date"},
            {"company_id": str(self.company.id)},
        ]
        for values in tampered:
            with self.subTest(values=values), self.assertRaises(ValidationError):
                self._compute(self.reader, **values)
        # A company the reader may not access at all.
        with self.assertRaises(AccessError):
            self._compute(self.reader, company_id=self.company_2.id)

    def test_wizard_computes_with_its_owner_access_only(self):
        wizard = self.env["azk_dynamic_trial_balance.wizard"].with_user(self.reader).with_context(
            allowed_company_ids=self.company.ids).create({
                "date_from": "2026-01-01", "date_to": "2026-01-31", "skip_zero_balance": True})
        result = wizard._compute_report()
        self.assertRowsEqual(self.engine_rows(result), TB_BASE_POSTED)
        # Another user cannot run a report from someone else's wizard.
        with self.assertRaises(AccessError):
            wizard.with_user(self.other_reader)._compute_report()
        # Nor open the preview or an export from it (Stage 09).
        for method in ("action_preview", "action_export_pdf", "action_export_xlsx"):
            with self.subTest(button=method), self.assertRaises(AccessError):
                getattr(wizard.with_user(self.other_reader), method)()

    def test_query_count_does_not_grow_with_accounts(self):
        def queries(**options):
            self.env.invalidate_all()
            before = self.env.cr.sql_log_count
            self.engine_report("2026-01-01", "2026-01-31", **options)
            return self.env.cr.sql_log_count - before

        options = [{"skip_zero_balance": True}, {"hierarchy_subtotals": True, "skip_zero_balance": True},
                   {"show_amount_currency": True}]
        small = [queries(**values) for values in options]
        Account = self.env["account.account"]
        for index in range(20):
            account = Account.create({"name": f"TB load {index}", "code": f"TBLOAD{index:02d}",
                                      "account_type": "asset_current"})
            self._entry("2026-01-15", [(account, 10, 0), (self.accounts["bank"], 0, 10)],
                        ref=f"TB load {index}")
        large = [queries(**values) for values in options]
        # 20 more accounts with amounts: rows grow, queries do not.
        for values, before, after in zip(options, small, large):
            _logger.info("engine queries with options %s: %s with 4 accounts with amounts, "
                         "%s with 24", values, before, after)
            with self.subTest(options=values, before=before, after=after):
                self.assertLessEqual(after, before + 2)
        result = self.engine_report("2026-01-01", "2026-01-31", skip_zero_balance=True)
        self.assertEqual(len(result["leaf_rows"]), 24)
