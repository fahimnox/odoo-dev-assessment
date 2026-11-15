"""Our report extensions leave the standard reports unchanged (Stage 10).

The addon extends ``account.report`` in one place only: the two XLSX writer
methods, which switch to our sheet for our report and call the standard
methods for every other report. Its PDF templates and preview component are
named only by our handler's display configuration. These tests run the
standard Trial Balance and General Ledger with the addon installed and
compare their XLSX, cell by cell, with the one the original Enterprise
methods write, and check that their PDF uses none of our templates.
(The vendor's own TestTrialBalanceReport and annotation export tests are
run with the addon installed too; see docs/test_results.md.)
"""
import io
from unittest.mock import patch

import openpyxl

from odoo.addons.account_reports.models.account_report import AccountReport as StandardReport
from odoo.tests import tagged

from ..models.account_report import AccountReport as OurReport
from .common import TrialBalanceCase, capture_wkhtmltopdf

STANDARD_REPORTS = ("account_reports.trial_balance_report", "account_reports.general_ledger_report")
OUR_REPORT = "azk_dynamic_trial_balance.dynamic_trial_balance_report"


def cells(xlsx):
    """Every sheet's non-empty cells: {sheet: {coordinate: value}}."""
    book = openpyxl.load_workbook(io.BytesIO(xlsx["file_content"]))
    return {sheet.title: {cell.coordinate: cell.value for row in sheet.iter_rows() for cell in row
                          if cell.value is not None}
            for sheet in book.worksheets}


@tagged("post_install", "-at_install")
class TestNativeReportsUnchanged(TrialBalanceCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._build_tb_base()

    def setUp(self):
        super().setUp()
        self.wkhtmltopdf = capture_wkhtmltopdf(self)

    def options(self, report):
        report = report.with_context(allowed_company_ids=self.company.ids)
        return report, report.get_options({
            "date": {"date_from": "2026-01-01", "date_to": "2026-01-31", "mode": "range", "filter": "custom"},
            "unfold_all": True,
        })

    def test_standard_xlsx_exports_are_unchanged(self):
        for xmlid in STANDARD_REPORTS:
            with self.subTest(report=xmlid):
                report, options = self.options(self.env.ref(xmlid))
                self.assertFalse(report._is_dynamic_trial_balance())
                ours = cells(report.export_to_xlsx(options))
                # The same export with our two overrides replaced by the original methods.
                with patch.object(OurReport, "_inject_report_into_xlsx_sheet",
                                  StandardReport._inject_report_into_xlsx_sheet), \
                        patch.object(OurReport, "_inject_report_options_into_xlsx_sheet",
                                     StandardReport._inject_report_options_into_xlsx_sheet):
                    standard = cells(report.export_to_xlsx(options))
                self.assertEqual(ours, standard)
                self.assertTrue(any(standard.values()))

    def test_standard_pdf_uses_none_of_our_templates(self):
        report, options = self.options(self.env.ref("account_reports.trial_balance_report"))
        config = self.env[report._get_custom_handler_model()]._get_custom_display_config()
        self.assertNotIn("azk_dynamic_trial_balance", str(config))
        report.export_to_pdf(options)
        ours_report, our_options = self.options(self.env.ref(OUR_REPORT))
        ours_report.export_to_pdf(our_options)
        standard_html, our_html = (call["bodies"][0] for call in self.wkhtmltopdf)
        self.assertNotIn("o_azk_tb", standard_html)
        self.assertIn("o_azk_tb_filter", our_html)
