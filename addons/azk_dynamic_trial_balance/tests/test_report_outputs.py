"""Preview, PDF and XLSX against the engine, on the installed demo company (Stage 09).

The three outputs come from the report record's lines (``_get_lines``),
which the handler builds from one engine result. These tests compare, for
the same options on the same unchanged data:

- the preview lines (``get_report_information``, what the UI receives),
- the PDF document (``export_to_pdf``; the HTML that wkhtmltopdf prints is
  captured, see ``capture_wkhtmltopdf``),
- the XLSX (``export_to_xlsx``, read back cell by cell with openpyxl),

with the engine result, by fixed column position: the first nine numeric
columns are Initial, Movement and End (Debit, Credit, Balance), the tenth
the Amount Currency. The demo company's January 2026 is the assessment's
example: Bank 1,200 posted only, 1,000 with drafts.
"""
import io

import openpyxl
from lxml import html as lxml_html

from odoo.tests import TransactionCase, tagged

from .common import STUB_PDF, capture_wkhtmltopdf, html_text, pdf_rows

DEMO_COMPANY = "azk_dynamic_trial_balance.demo_company"
REPORT = "azk_dynamic_trial_balance.dynamic_trial_balance_report"
AMOUNT_KEYS = (
    "initial_debit", "initial_credit", "initial_balance",
    "debit", "credit", "balance",
    "ending_debit", "ending_credit", "ending_balance",
)


def line_numbers(line):
    return tuple(column.get("no_format") for column in line["columns"])


def squeeze(value):
    return " ".join(str(value or "").split())


@tagged("post_install", "-at_install")
class TestReportOutputs(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref(DEMO_COMPANY)
        admin = cls.env.ref("base.user_admin")
        cls.env = cls.env(user=admin, context=dict(cls.env.context, allowed_company_ids=cls.company.ids))
        cls.report = cls.env.ref(REPORT)
        Account = cls.env["account.account"].with_company(cls.company)
        cls.bank = Account.search([("code", "=", "101401"), *Account._check_company_domain(cls.company)])
        cls.sales = cls.env["account.analytic.account"].search(
            [("name", "=", "Sales Department"), ("company_id", "=", cls.company.id)])

    def setUp(self):
        super().setUp()
        self.wkhtmltopdf = capture_wkhtmltopdf(self)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def options(self, date_from="2026-01-01", date_to="2026-01-31", drafts=False, **tb):
        return self.report.get_options({
            "date": {"date_from": date_from, "date_to": date_to, "mode": "range", "filter": "custom"},
            "all_entries": drafts,
            "unfold_all": True,
            "azk_tb": {"company_id": self.company.id, **tb},
        })

    def engine(self, options):
        handler = self.env["azk_dynamic_trial_balance.report.handler"]
        return self.env["azk_dynamic_trial_balance.engine"].compute(handler._engine_options(options))

    def preview_lines(self, options):
        return self.report.get_report_information(options)["lines"]

    def print_options(self, options):
        return self.report.get_options({**options, "export_mode": "print"})

    def printed_lines(self, options, formatted=True):
        report = self.report if formatted else self.report.with_context(no_format=True)
        return report._filter_out_folded_children(report._get_lines(self.print_options(options)))

    def pdf_document(self, options):
        """The HTML document that the PDF export prints for ``options``."""
        start = len(self.wkhtmltopdf)
        result = self.report.export_to_pdf(options)
        self.assertEqual(result["file_content"], STUB_PDF)
        self.assertEqual(len(self.wkhtmltopdf), start + 1)
        call = self.wkhtmltopdf[-1]
        # More than five columns: the standard export prints in landscape.
        self.assertTrue(call["landscape"])
        return "".join(call["bodies"])

    def xlsx(self, options):
        content = self.report.export_to_xlsx(options)["file_content"]
        self.assertEqual(content[:2], b"PK")
        return openpyxl.load_workbook(io.BytesIO(content))

    def xlsx_table(self, workbook):
        """Header row index and the data rows (code, name, numbers, currency)."""
        sheet = workbook.worksheets[0]
        rows = list(sheet.iter_rows(values_only=True))
        header = next(index for index, row in enumerate(rows) if row[0] == "Code")
        return header, [row for row in rows[header + 1:] if any(cell is not None for cell in row)]

    def assertPreviewFollowsTheEngine(self, options):
        result = self.engine(options)
        lines = self.preview_lines(options)
        body = [line for line in lines if line.get("azk_tb_kind") in ("group", "account")]
        self.assertEqual(len(body), len(result["lines"]))
        for line, row in zip(body, result["lines"]):
            with self.subTest(line=line["name"]):
                self.assertEqual(line_numbers(line)[:9], tuple(row[key] for key in AMOUNT_KEYS))
                if row["type"] == "account":
                    self.assertTrue(line["name"].startswith(f"{row['account_code']} "))
                    if result["filters"]["show_amount_currency"]:
                        self.assertEqual(line_numbers(line)[9], row["amount_currency"])
                else:
                    self.assertEqual(line["name"], row["group_name"])
        total = next(line for line in lines if line.get("azk_tb_kind") == "total")
        self.assertEqual(line_numbers(total)[:9], tuple(result["totals"][key] for key in AMOUNT_KEYS))
        return result, lines

    def assertXlsxFollowsTheLines(self, options):
        lines = self.printed_lines(options, formatted=False)
        header, rows = self.xlsx_table(self.xlsx(options))
        self.assertEqual(len(rows), len(lines))
        for line, row in zip(lines, rows):
            with self.subTest(line=line["name"]):
                self.assertEqual(row[0] or "", line.get("azk_tb_code") or "")
                numbers = tuple(row[2:2 + len(line["columns"])])
                self.assertEqual(numbers, line_numbers(line))
                for cell in numbers:
                    self.assertTrue(cell is None or isinstance(cell, (int, float)))
        return lines, rows

    def assertPdfFollowsTheLines(self, options):
        """Each PDF row prints exactly the name and the formatted cells of one printed line."""
        lines = self.printed_lines(options)
        document = self.pdf_document(options)
        rows = pdf_rows(document)
        expected = [(squeeze(line["name"]), [squeeze(column.get("name")) for column in line["columns"]])
                    for line in lines]
        self.assertEqual(rows, expected)
        return html_text(document), rows

    # ------------------------------------------------------------------
    # The assessment's example in all three outputs
    # ------------------------------------------------------------------
    def test_bank_in_all_three_outputs(self):
        # Posted only: 1,000 + 500 - 300 = 1,200. With drafts: the draft
        # credit of 200 joins the movement: 1,000 + 500 - 500 = 1,000.
        for drafts, expected in ((False, 1200.0), (True, 1000.0)):
            with self.subTest(drafts=drafts):
                options = self.options(drafts=drafts, skip_zero_balance=True)
                result, lines = self.assertPreviewFollowsTheEngine(options)
                bank_row = next(row for row in result["leaf_rows"] if row["account_id"] == self.bank.id)
                self.assertEqual(bank_row["ending_balance"], expected)
                bank_line = next(line for line in lines if line["name"] == "101401 Bank")
                self.assertEqual(line_numbers(bank_line)[6:9], (expected, 0.0, expected))
                _header, rows = self.xlsx_table(self.xlsx(options))
                bank_cells = next(row for row in rows if row[0] == "101401")
                self.assertEqual(tuple(bank_cells[2:11]), line_numbers(bank_line)[:9])
                _text, pdf = self.assertPdfFollowsTheLines(options)
                bank_pdf = next(cells for name, cells in pdf if name == "101401 Bank")
                amount = f"{expected:,.2f}"
                # End Balance: Debit and Balance print the amount.
                self.assertIn(amount, bank_pdf[6])
                self.assertIn(amount, bank_pdf[8])
                if drafts:
                    self.assertFalse(any("1,200.00" in cell for cell in bank_pdf))

    # ------------------------------------------------------------------
    # Every option set: the outputs follow the engine
    # ------------------------------------------------------------------
    def test_outputs_follow_the_engine_for_each_option_set(self):
        option_sets = {
            "posted only": {},
            "with drafts": {"drafts": True},
            "hierarchy": {"hierarchy_subtotals": True},
            "parents only": {"hierarchy_subtotals": True, "hierarchy_only_parents": True, "account_level": 2},
            "amount currency": {"show_amount_currency": True, "skip_zero_balance": True},
            "analytic": {"date_from": "2026-03-01", "date_to": "2026-03-31",
                         "analytic_account_id": self.sales.id},
            "zero filtering": {"skip_zero_balance": True},
            "empty result": {"date_from": "2024-01-01", "date_to": "2024-01-31", "skip_zero_balance": True},
        }
        for name, values in option_sets.items():
            with self.subTest(options=name):
                options = self.options(**values)
                result, _lines = self.assertPreviewFollowsTheEngine(options)
                self.assertXlsxFollowsTheLines(options)
                text, rows = self.assertPdfFollowsTheLines(options)
                names = [row_name for row_name, _cells in rows]
                for row in result["leaf_rows"]:
                    if not values.get("hierarchy_only_parents"):
                        account = f"{row['account_code']} {row['account_name']}"
                        self.assertTrue(any(row_name.startswith(account) for row_name in names), account)
                self.assertIn("Total", names)
                self.assertIn("Initial Balance", text)

    def test_amount_currency_rows_and_totals(self):
        options = self.options(show_amount_currency=True, skip_zero_balance=True)
        result, lines = self.assertPreviewFollowsTheEngine(options)
        by_name = {line["name"]: line_numbers(line) for line in lines}
        self.assertEqual(by_name["101000 Current Assets (USD)"][9], 60.0)
        self.assertEqual(by_name["101000 Current Assets (EUR)"][9], 50.0)
        # One total per currency, never added together.
        self.assertEqual(by_name["Total in USD"][9], 60.0)
        self.assertEqual(by_name["Total in EUR"][9], 50.0)
        self.assertNotIn(110.0, [numbers[9] for numbers in by_name.values()])
        _header, rows = self.xlsx_table(self.xlsx(options))
        usd = next(row for row in rows if row[0] == "101000" and row[-1] == "USD")
        self.assertEqual((usd[11], usd[12]), (60.0, "USD"))
        text, pdf = self.assertPdfFollowsTheLines(options)
        self.assertIn("Amount Currency", text)
        pdf_by_name = dict(pdf)
        self.assertIn("60.00", pdf_by_name["101000 Current Assets (USD)"][9])
        self.assertIn("60.00", pdf_by_name["Total in USD"][9])
        self.assertIn("50.00", pdf_by_name["Total in EUR"][9])

    # ------------------------------------------------------------------
    # PDF: header, columns, pages
    # ------------------------------------------------------------------
    def test_pdf_states_company_period_options_and_columns(self):
        document = self.pdf_document(self.options(drafts=True, show_amount_currency=True,
                                                  account_prefixes=["10", "6"]))
        text = html_text(document).replace(" :", ":")
        for expected in (self.company.name, "From 01/01/2026 to 01/31/2026", "Posted and draft",
                         "Accounts: 10, 6", "Initial Balance", "End Balance", "Debit", "Credit",
                         "Balance", "Amount Currency", "Movement", "[Draft]"):
            with self.subTest(text=expected):
                self.assertIn(expected, text)

    def test_rounding_unit_is_printed_and_xlsx_keeps_exact_numbers(self):
        # The standard rounding unit only changes how amounts are shown: the
        # PDF must say so, and the XLSX keeps the exact numbers.
        options = self.report.get_options({**self.options(skip_zero_balance=True), "rounding_unit": "thousands"})
        document = self.pdf_document(options)
        self.assertIn("Amounts in Thousands", html_text(document))
        bank_pdf = dict(pdf_rows(document))["101401 Bank"]
        self.assertNotIn("1,200.00", bank_pdf[8])
        _header, rows = self.xlsx_table(self.xlsx(options))
        bank = next(row for row in rows if row[0] == "101401")
        self.assertEqual(bank[10], 1200.0)
        self.assertNotIn("Amounts in Thousands", html_text(self.pdf_document(self.options(skip_zero_balance=True))))

    def test_pdf_table_header_repeats_on_every_page(self):
        # wkhtmltopdf prints a table's <thead> again at the top of every page.
        # So the column groups and names must be in the report table's thead;
        # the real multipage PDF is checked on the running server.
        options = self.options(hierarchy_subtotals=True, show_amount_currency=True)
        tree = lxml_html.fromstring(self.pdf_document(options))
        heads = tree.xpath("//table/thead[@id='table_header']")
        self.assertEqual(len(heads), 1)
        groups, names = heads[0].xpath("./tr")
        self.assertEqual([(squeeze(th.text_content()), th.get("colspan")) for th in groups.xpath("./th")][1:],
                         [("Initial Balance", "3"), (squeeze(options["date"]["string"]), "3"),
                          ("End Balance", "3"), ("Amount Currency", "1")])
        self.assertEqual([squeeze(th.text_content()) for th in names.xpath("./th")][1:],
                         ["Debit", "Credit", "Balance"] * 3 + ["Movement"])
        self.assertEqual(len(tree.xpath("//table/tbody/tr[@name='pdf_export_main_table_body_lines_tr']")),
                         len(self.printed_lines(options)))

    # ------------------------------------------------------------------
    # XLSX: cells, metadata, frozen header
    # ------------------------------------------------------------------
    def test_xlsx_cells_metadata_and_frozen_header(self):
        options = self.options(show_amount_currency=True, skip_zero_balance=True, account_prefixes=["1"])
        workbook = self.xlsx(options)
        sheet = workbook.worksheets[0]
        metadata = {sheet.cell(row, 1).value: sheet.cell(row, 2).value for row in range(3, 20)}
        self.assertEqual(metadata["Company"], self.company.name)
        self.assertEqual(metadata["Period"], "From 01/01/2026 to 01/31/2026")
        self.assertEqual(metadata["Accounts"], "1")
        self.assertTrue(metadata["Show Amount Currency"].startswith("Yes"))
        header, rows = self.xlsx_table(workbook)
        names = [cell.value for cell in sheet[header + 1]]
        self.assertEqual(names[:2], ["Code", "Account"])
        self.assertEqual(names[2:11], ["Debit", "Credit", "Balance"] * 3)
        self.assertEqual(names[11:13], ["Movement", "Currency"])
        self.assertEqual(sheet.freeze_panes, f"C{header + 2}")
        for row in sheet.iter_rows():
            for cell in row:
                self.assertNotEqual(cell.data_type, "f", cell.coordinate)
        for row in sheet.iter_rows(min_row=header + 2):
            for cell in row[2:11]:
                if cell.value is not None:
                    self.assertEqual(cell.number_format, "#,##0.00;-#,##0.00;0.00", cell.coordinate)
        codes = [row[0] for row in rows if row[0]]
        self.assertTrue(all(isinstance(code, str) for code in codes))
        filters = {row[0]: row[1] for row in workbook["Filters"].iter_rows(values_only=True)}
        self.assertEqual(filters["Period"], "From 01/01/2026 to 01/31/2026")

    # ------------------------------------------------------------------
    # Exports follow the preview's search and folding
    # ------------------------------------------------------------------
    def test_exports_follow_the_preview_search(self):
        options = self.options(hierarchy_subtotals=True, skip_zero_balance=True)
        options["filter_search_bar"] = "bank"
        lines, rows = self.assertXlsxFollowsTheLines(options)
        names = [line["name"] for line in lines]
        self.assertIn("101401 Bank", names)
        self.assertNotIn("600000 Expenses", names)
        self.assertEqual([row[0] for row in rows], ["1", "10", "101", "1014", "10140", "101401"])
        text, pdf = self.assertPdfFollowsTheLines(options)
        self.assertEqual([name for name, _cells in pdf], names)
        self.assertIn("Search: bank", text.replace(" :", ":"))

    def test_exports_follow_folded_groups(self):
        options = self.options(hierarchy_subtotals=True, skip_zero_balance=True)
        options.update(unfold_all=False, unfolded_lines=[])
        lines, rows = self.assertXlsxFollowsTheLines(options)
        # Only the top-level groups, "(No Group)" and the total remain.
        self.assertEqual({line.get("level") for line in lines}, {1})
        self.assertIn("1 Assets", [line["name"] for line in lines])
        _text, pdf = self.assertPdfFollowsTheLines(options)
        self.assertEqual(len(pdf), len(lines))

    # ------------------------------------------------------------------
    # Preview: what the UI receives
    # ------------------------------------------------------------------
    def test_preview_columns_filters_and_warnings(self):
        options = self.options(show_amount_currency=True)
        info = self.report.get_report_information(options)
        self.assertEqual(info["custom_display"]["components"]["AccountReportFilters"],
                         "azk_dynamic_trial_balance.TrialBalanceFilters")
        headers = options["column_headers"][0]
        self.assertEqual([(header["name"], header["colspan"]) for header in headers],
                         [("Initial Balance", 3), (options["date"]["string"], 3), ("End Balance", 3),
                          ("Amount Currency", 1)])
        self.assertEqual(options["companies"], [{"name": self.company.name, "id": self.company.id,
                                                 "currency_id": self.company.currency_id.id}])
        empty = self.report.get_report_information(self.options("2024-01-01", "2024-01-31",
                                                                 skip_zero_balance=True))
        self.assertIn("azk_dynamic_trial_balance.tb_warning_no_lines", empty["warnings"])
        filtered = self.report.get_report_information(self.options(account_prefixes=["1"]))
        self.assertIn("azk_dynamic_trial_balance.tb_warning_filtered", filtered["warnings"])
        groups = self.report.get_report_information(self.options(hierarchy_subtotals=True))
        group_lines = [line for line in groups["lines"] if line.get("azk_tb_kind") == "group"]
        self.assertTrue(all(line["id"].startswith(line["parent_id"] + "|")
                            for line in groups["lines"] if line.get("parent_id")))
        self.assertTrue(any(line["unfoldable"] for line in group_lines))

    def test_options_round_trip_from_the_wizard(self):
        wizard = self.env["azk_dynamic_trial_balance.wizard"].create({
            "date_from": "2026-01-01", "date_to": "2026-01-31", "company_id": self.company.id,
            "include_unposted": True, "skip_zero_balance": True,
        })
        action = wizard.action_preview()
        options = self.report.get_options(action["params"]["options"])
        bank_line = next(line for line in self.preview_lines(options) if line["name"] == "101401 Bank")
        self.assertEqual(line_numbers(bank_line)[8], 1000.0)
