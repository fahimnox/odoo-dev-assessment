"""XLSX layout of the Dynamic Trial Balance (Stage 09).

The standard XLSX export writes the amounts as numbers in the General
format (no thousands separator, no fixed decimals), puts no options above
the table, freezes no header, and its "Filters" sheet knows only the
standard options. For this report only,
the sheet is written here from the very same lines (``_get_lines``, so the
same engine result, the same folding and the same search as the preview):

- the company, the period and every option above the table;
- numeric cells written as numbers with a number format, codes and names
  written as text (never as formulas);
- the Amount Currency next to a separate currency-code column, so different
  currencies are never mixed in one cell format;
- header rows frozen, sensible column widths.

Every other report keeps the standard export.
"""
from odoo import _, models

HANDLER = "azk_dynamic_trial_balance.report.handler"
AMOUNT_FORMAT = "#,##0.00;-#,##0.00;0.00"


class AccountReport(models.Model):
    _inherit = "account.report"

    def _is_dynamic_trial_balance(self):
        return self.custom_handler_model_name == HANDLER

    def _inject_report_into_xlsx_sheet(self, options, workbook, sheet):
        if not self._is_dynamic_trial_balance():
            return super()._inject_report_into_xlsx_sheet(options, workbook, sheet)
        return self._write_dynamic_trial_balance_sheet(options, workbook, sheet)

    def _inject_report_options_into_xlsx_sheet(self, options, sheet, y_offset, options_to_print=None):
        if not self._is_dynamic_trial_balance():
            return super()._inject_report_options_into_xlsx_sheet(
                options, sheet, y_offset, options_to_print=options_to_print)
        for label, value in options["azk_tb_display"]["summary"]:
            sheet.write_string(y_offset, 0, label)
            sheet.write_string(y_offset, 1, value)
            y_offset += 1
        return y_offset

    def _write_dynamic_trial_balance_sheet(self, options, workbook, sheet):
        lines = self._filter_out_folded_children(self.with_context(no_format=True)._get_lines(options))
        by_currency = options["azk_tb"]["show_amount_currency"]
        columns = options["columns"]

        title = workbook.add_format({"bold": True, "font_size": 14})
        label = workbook.add_format({"bold": True, "font_color": "#555555"})
        header = workbook.add_format({"bold": True, "align": "center", "valign": "vcenter",
                                      "bottom": 1, "text_wrap": True})
        formats = {}

        def cell_format(kind, level, number):
            key = (kind in ("group", "total", "currency_total"), level if not number else 0, number)
            if key not in formats:
                values = {"bold": key[0]}
                if number:
                    values["num_format"] = AMOUNT_FORMAT
                else:
                    values["indent"] = max(level - 1, 0)
                if kind == "total":
                    values["top"] = 1
                formats[key] = workbook.add_format(values)
            return formats[key]

        row = 0
        sheet.write_string(row, 0, self.name, title)
        row += 2
        for caption, value in options["azk_tb_display"]["summary"]:
            sheet.write_string(row, 0, caption, label)
            sheet.write_string(row, 1, value)
            row += 1
        row += 1

        # Column headers: the column groups, then the column names.
        col = 2
        for group in options["column_headers"][0]:
            span = group.get("colspan", 1) + (1 if by_currency and group is options["column_headers"][0][-1] else 0)
            if span > 1:
                sheet.merge_range(row, col, row, col + span - 1, group.get("name", ""), header)
            else:
                sheet.write_string(row, col, group.get("name", ""), header)
            col += span
        row += 1
        sheet.write_string(row, 0, _("Code"), header)
        sheet.write_string(row, 1, _("Account"), header)
        for index, column in enumerate(columns):
            sheet.write_string(row, 2 + index, column.get("name", ""), header)
        currency_col = 2 + len(columns)
        if by_currency:
            sheet.write_string(row, currency_col, _("Currency"), header)
        row += 1
        sheet.freeze_panes(row, 2)

        for line in lines:
            kind = line.get("azk_tb_kind", "account")
            level = line.get("level") or 1
            name = line.get("azk_tb_name") or line.get("name") or ""
            sheet.write_string(row, 0, line.get("azk_tb_code") or "", cell_format(kind, 1, False))
            sheet.write_string(row, 1, name, cell_format(kind, level, False))
            for index, cell in enumerate(line["columns"]):
                value = cell.get("no_format")
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    sheet.write_number(row, 2 + index, value, cell_format(kind, level, True))
                else:
                    sheet.write_blank(row, 2 + index, None, cell_format(kind, level, True))
            if by_currency and line.get("azk_tb_currency"):
                sheet.write_string(row, currency_col, line["azk_tb_currency"], cell_format(kind, 1, False))
            row += 1

        sheet.set_column(0, 0, 12)
        sheet.set_column(1, 1, 42)
        sheet.set_column(2, 1 + len(columns), 15)
        if by_currency:
            sheet.set_column(currency_col, currency_col, 10)
