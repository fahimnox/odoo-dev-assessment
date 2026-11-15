"""Who may open and download the Dynamic Trial Balance, and with which options (Stage 09).

An accounting reader can preview and export; users without accounting read
access cannot; tampered options are refused on the preview and on every
export path, including the company list that the download route
(``/account_reports``) turns into the active companies. Another user's
wizard is covered in ``test_engine_access.py``. The download route itself
is exercised over HTTP on the running server
(scripts/tb_preview_smoke_check.py): an ``HttpCase`` here would make Odoo
build every asset bundle before the tests (about 13 minutes on this host).
"""
import io

import openpyxl

from odoo import Command
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import new_test_user, tagged

from .common import STUB_PDF, TB_BASE_POSTED, TrialBalanceCase, capture_wkhtmltopdf, pdf_rows

REPORT = "azk_dynamic_trial_balance.dynamic_trial_balance_report"
READERS = "base.group_user,account.group_account_readonly"


@tagged("post_install", "-at_install")
class TestReportAccess(TrialBalanceCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._build_tb_base()
        su_env = cls.env(su=True)
        company_ids = [Command.set(cls.company.ids)]
        cls.reader = new_test_user(su_env, login="tb_report_reader", groups=READERS,
                                   company_id=cls.company.id, company_ids=company_ids)
        cls.billing = new_test_user(su_env, login="tb_report_billing",
                                    groups="base.group_user,account.group_account_invoice",
                                    company_id=cls.company.id, company_ids=company_ids)
        cls.employee = new_test_user(su_env, login="tb_report_employee", groups="base.group_user",
                                     company_id=cls.company.id, company_ids=company_ids)
        data_2 = cls.setup_other_company(name="AZK TB Report Other", currency_id=cls.company.currency_id.id)
        cls.company_2 = data_2["company"]
        cls.journal_2 = data_2["default_journal_misc"]
        cls.report = cls.env.ref(REPORT)

    def setUp(self):
        super().setUp()
        self.wkhtmltopdf = capture_wkhtmltopdf(self)

    def _report(self, user, companies=None):
        return self.report.with_user(user).with_context(allowed_company_ids=(companies or self.company).ids)

    def _options(self, user, **tb):
        return self._report(user).get_options({
            "date": {"date_from": "2026-01-01", "date_to": "2026-01-31", "mode": "range", "filter": "custom"},
            "unfold_all": True,
            "azk_tb": {"company_id": self.company.id, "skip_zero_balance": True, **tb},
        })

    def test_an_accounting_reader_previews_and_exports(self):
        report = self._report(self.reader)
        options = self._options(self.reader)
        lines = report.get_report_information(options)["lines"]
        bank = next(line for line in lines if line["name"] == "101401 Bank")
        self.assertEqual([column["no_format"] for column in bank["columns"]],
                         [float(value) for value in TB_BASE_POSTED["bank"]])
        pdf = report.dispatch_report_action(options, "export_to_pdf")
        self.assertEqual(pdf["file_content"], STUB_PDF)
        printed = dict(pdf_rows("".join(self.wkhtmltopdf[-1]["bodies"])))
        self.assertIn("1,200.00", printed["101401 Bank"][8])
        xlsx = report.dispatch_report_action(options, "export_to_xlsx")
        sheet = openpyxl.load_workbook(io.BytesIO(xlsx["file_content"])).worksheets[0]
        bank_row = next(row for row in sheet.iter_rows(values_only=True) if row[0] == "101401")
        self.assertEqual(bank_row[10], 1200.0)

    def test_users_without_accounting_read_access_get_nothing(self):
        for user in (self.employee, self.billing):
            with self.subTest(user=user.login), self.assertRaises(AccessError):
                report = self._report(user)
                options = report.get_options({"azk_tb": {"company_id": self.company.id}})
                report.get_report_information(options)

    def test_tampered_options_are_refused_on_every_path(self):
        good = self._options(self.reader)
        report = self._report(self.reader)
        tampered = {
            "another company's journal": {**good["azk_tb"], "journal_id": self.journal_2.id},
            "an unknown key": {**good["azk_tb"], "domain": [("id", ">", 0)]},
            "a wrongly typed value": {**good["azk_tb"], "skip_zero_balance": "yes"},
            "a non-code prefix": {**good["azk_tb"], "account_prefixes": ["1%"]},
            "not a dictionary": "all",
        }
        for name, value in tampered.items():
            options = {**good, "azk_tb": value}
            for path in ("get_options", "export_to_pdf", "export_to_xlsx"):
                with self.subTest(tampering=name, path=path), self.assertRaises(ValidationError):
                    if path == "get_options":
                        report.get_options(options)
                    else:
                        report.dispatch_report_action(options, path)
        # A company the reader may not access: refused, whatever the options say.
        with self.assertRaises(AccessError):
            report.get_options({**good, "azk_tb": {**good["azk_tb"], "company_id": self.company_2.id}})
        with self.assertRaises(AccessError):
            self._report(self.reader, self.company_2).dispatch_report_action(good, "export_to_pdf")
        # The download route makes the companies of the options the active
        # companies (get_report_company_ids): another company there is refused.
        company_2 = {"id": self.company_2.id, "name": self.company_2.name,
                     "currency_id": self.company_2.currency_id.id}
        for companies in ([company_2], [company_2, *good["companies"]]):
            options = {**good, "companies": companies}
            active = self.env["account.report"].get_report_company_ids(options)
            for path in ("export_to_pdf", "export_to_xlsx"):
                with self.subTest(companies=active, path=path), self.assertRaises(AccessError):
                    self.report.with_user(self.reader).with_context(
                        allowed_company_ids=active).dispatch_report_action(options, path)
        self.assertEqual(self.wkhtmltopdf, [])
        # Options of another report.
        other = self.env.ref("account_reports.trial_balance_report")
        with self.assertRaises(UserError):
            report.dispatch_report_action({**good, "report_id": other.id}, "export_to_pdf")
