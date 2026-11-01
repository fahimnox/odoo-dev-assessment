import io

import xlsxwriter

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestModuleInstalled(TransactionCase):
    """Environment smoke tests: the addon installs, its tests are discovered and
    run, and the XLSX library it depends on works in this runtime."""

    def test_module_is_installed(self):
        module = self.env["ir.module.module"].search(
            [("name", "=", "azk_dynamic_trial_balance")]
        )
        self.assertEqual(module.state, "installed")

    def test_xlsxwriter_writes_a_workbook(self):
        buffer = io.BytesIO()
        workbook = xlsxwriter.Workbook(buffer, {"in_memory": True})
        workbook.add_worksheet("Check").write_number(0, 0, 1500.0)
        workbook.close()
        # An XLSX file is a ZIP container, which starts with "PK".
        self.assertEqual(buffer.getvalue()[:2], b"PK")
