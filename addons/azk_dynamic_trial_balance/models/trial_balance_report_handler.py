"""Bridge between the account_reports framework and our calculation engine (Stage 09).

The Preview (the standard report UI), the PDF and the XLSX all come from the
same place: the report record ``azk_dynamic_trial_balance.dynamic_trial_balance_report``
asks this handler for its lines, and the handler asks the engine once per
request. Nothing here computes an amount: it validates the options, lays
out the columns, and turns the engine's rows into report lines.

Options travel in the report options as ``options['azk_tb']`` (our own
choices) plus the standard ``date`` and ``all_entries`` (Draft Entries)
keys. They are validated again on every request, because the preview and
the download route send them back from the browser.
"""
from odoo import _, models
from odoo.exceptions import ValidationError
from odoo.tools.misc import format_date

from .report_options import normalize_options

TB_OPTIONS_KEY = "azk_tb"
# Options that come from the standard date and Draft Entries filters.
STANDARD_KEYS = ("date_from", "date_to", "include_unposted")
# Column group key and column label -> key of the nine numbers in an engine row.
VALUE_KEYS = {
    ("initial", "debit"): "initial_debit",
    ("initial", "credit"): "initial_credit",
    ("initial", "balance"): "initial_balance",
    ("period", "debit"): "debit",
    ("period", "credit"): "credit",
    ("period", "balance"): "balance",
    ("ending", "debit"): "ending_debit",
    ("ending", "credit"): "ending_credit",
    ("ending", "balance"): "ending_balance",
}


class TrialBalanceReportHandler(models.AbstractModel):
    _name = "azk_dynamic_trial_balance.report.handler"
    _inherit = "account.report.custom.handler"
    _description = "Dynamic Trial Balance Report Handler"

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------
    def _get_custom_display_config(self):
        return {
            "css_custom_class": "azk_dynamic_trial_balance",
            "components": {
                "AccountReportFilters": "azk_dynamic_trial_balance.TrialBalanceFilters",
            },
            "pdf_export": {
                "company_information": "azk_dynamic_trial_balance.pdf_company_information",
                "pdf_export_filters": "azk_dynamic_trial_balance.pdf_export_filters",
                "pdf_export_main_table_header": "azk_dynamic_trial_balance.pdf_export_main_table_header",
            },
        }

    # ------------------------------------------------------------------
    # Options
    # ------------------------------------------------------------------
    def _custom_options_initializer(self, report, options, previous_options):
        """Validate our options and lay out the columns.

        Runs on every request (preview, reload after a filter change, PDF and
        XLSX export). An invalid or tampered option set raises before any
        line is computed.
        """
        super()._custom_options_initializer(report, options, previous_options=previous_options)
        engine_options = normalize_options(self.env, self._raw_engine_options(options, previous_options))
        company = self.env["res.company"].browse(engine_options["company_id"])
        options[TB_OPTIONS_KEY] = {
            key: value for key, value in engine_options.items() if key not in STANDARD_KEYS
        }
        # Exactly the report company, whatever the company switcher holds
        # (D-45); the download route also uses this key to set the active
        # companies, and Odoo refuses companies the user may not access.
        options["companies"] = [
            {"name": company.name, "id": company.id, "currency_id": company.currency_id.id}
        ]
        # Group rows show their own numbers, as in the standard Trial Balance.
        options["ignore_totals_below_sections"] = True
        options["azk_tb_display"] = self._display_values(engine_options, company, options)
        options["azk_tb_choices"] = self._filter_choices(company)
        self._set_columns(options, engine_options)

    def _raw_engine_options(self, options, previous_options):
        """Our options from the previous request, with the standard date and
        Draft Entries filters. A first opening without our options reports
        the current company with every choice off."""
        previous = previous_options.get(TB_OPTIONS_KEY) or {}
        if not isinstance(previous, dict):
            raise ValidationError(self.env._("The report options are invalid."))
        raw = dict(previous)
        raw.setdefault("company_id", self.env.company.id)
        raw.update({
            "date_from": options["date"]["date_from"],
            "date_to": options["date"]["date_to"],
            "include_unposted": bool(options.get("all_entries")),
        })
        return raw

    def _engine_options(self, options):
        return {
            **options[TB_OPTIONS_KEY],
            "date_from": options["date"]["date_from"],
            "date_to": options["date"]["date_to"],
            "include_unposted": bool(options.get("all_entries")),
        }

    def _display_values(self, engine_options, company, options):
        """Texts that the PDF and XLSX print about the selection.

        ``summary`` lists (label, value) pairs: the company, the period, and
        every option, so a printed report states exactly what it shows.
        """
        journal = self.env["account.journal"].browse(engine_options["journal_id"] or [])
        analytic = self.env["account.analytic.account"].browse(engine_options["analytic_account_id"] or [])
        date_from = format_date(self.env, engine_options["date_from"])
        date_to = format_date(self.env, engine_options["date_to"])
        yes, no = _("Yes"), _("No")
        level = engine_options["account_level"]
        summary = [
            (_("Company"), company.name),
            (_("Period"), _("From %(date_from)s to %(date_to)s", date_from=date_from, date_to=date_to)),
            (_("Entries"), _("Posted and draft") if engine_options["include_unposted"] else _("Posted only")),
            (_("Hierarchy and Subtotals"), yes if engine_options["hierarchy_subtotals"] else no),
            (_("Hierarchy Only Parents"),
             _("Yes, Account Level Up To %(level)s", level=level) if engine_options["hierarchy_only_parents"] else no),
            (_("Accounts"), ", ".join(engine_options["account_prefixes"]) or _("All")),
            (_("Journals"), journal.display_name or _("All")),
            (_("Analytic Accounts"), analytic.display_name or _("All")),
            (_("Skip Zero Balance"), yes if engine_options["skip_zero_balance"] else no),
            (_("Show Amount Currency"),
             _("Yes: the movement from %(date_from)s to %(date_to)s, in each row's currency",
               date_from=date_from, date_to=date_to) if engine_options["show_amount_currency"] else no),
            (_("Amounts in"), company.currency_id.name),
        ]
        if options.get("filter_search_bar"):
            summary.append((_("Search"), options["filter_search_bar"]))
        return {
            "company_name": company.name,
            "company_id": company.id,
            "currency_name": company.currency_id.name,
            "date_from": date_from,
            "date_to": date_to,
            "journal_name": journal.display_name or "",
            "analytic_account_name": analytic.display_name or "",
            "summary": summary,
        }

    def _filter_choices(self, company):
        """Journals and analytic accounts the user may pick in the preview."""
        Journal = self.env["account.journal"]
        Analytic = self.env["account.analytic.account"]
        journals = Journal.search(Journal._check_company_domain(company))
        analytics = Analytic.search(Analytic._check_company_domain(company), limit=200)
        return {
            "journals": [{"id": journal.id, "name": journal.display_name} for journal in journals],
            "analytic_accounts": [{"id": account.id, "name": account.display_name} for account in analytics],
        }

    def _set_columns(self, options, engine_options):
        """Three column groups (Initial Balance, the period, End Balance) with
        Debit, Credit and Balance each, as the assessment requires, plus an
        Amount Currency column for the period movement when asked."""
        report_columns = {column["expression_label"]: column for column in options["columns"]}
        groups = [
            ("initial", _("Initial Balance")),
            ("period", options["date"]["string"]),
            ("ending", _("End Balance")),
        ]
        headers, columns = [], []
        for group_key, header_name in groups:
            headers.append({"name": header_name, "colspan": 3, "forced_options": {"date": options["date"]}})
            for label in ("debit", "credit", "balance"):
                columns.append({**report_columns[label], "column_group_key": group_key})
        if engine_options["show_amount_currency"]:
            headers.append({"name": _("Amount Currency"), "colspan": 1,
                            "forced_options": {"date": options["date"]}})
            columns.append({**report_columns["amount_currency"], "column_group_key": "currency"})
        options["column_headers"] = [headers]
        options["columns"] = columns
        options["column_groups"] = {
            header_key: {"forced_options": {"date": options["date"]}, "forced_domain": []}
            for header_key in dict.fromkeys(column["column_group_key"] for column in columns)
        }

    # ------------------------------------------------------------------
    # Lines
    # ------------------------------------------------------------------
    def _dynamic_lines_generator(self, report, options, all_column_groups_expression_totals, warnings=None):
        result = self.env["azk_dynamic_trial_balance.engine"].compute(self._engine_options(options))
        lines = self._report_lines(report, options, result)
        if warnings is not None:
            self._add_warnings(options, result, warnings)
        return [(0, line) for line in lines]

    def _report_lines(self, report, options, result):
        company = self.env["res.company"].browse(result["metadata"]["company_id"])
        currencies = self.env["res.currency"].browse(
            {row["currency_id"] for row in result["leaf_rows"] if row["currency_id"]})
        currency_by_id = {currency.id: currency for currency in currencies}
        unfold_all = options.get("unfold_all")
        unfolded_ids = set(options.get("unfolded_lines") or [])
        line_ids = {}
        has_children = {row["parent_id"] for row in result["lines"] if row["parent_id"]}
        lines = []
        for row in result["lines"]:
            parent_line_id = line_ids.get(row["parent_id"])
            if row["type"] == "group":
                line_id = report._get_generic_line_id(
                    "account.group", row["group_id"], markup=None if row["group_id"] else "no_group",
                    parent_line_id=parent_line_id)
                unfoldable = row["id"] in has_children
                code, group_name = row["group_code"] or "", row["group_name"]
                lines.append({
                    "id": line_id,
                    "name": row["group_name"],
                    "level": row["level"],
                    "parent_id": parent_line_id,
                    "unfoldable": unfoldable,
                    "unfolded": unfoldable and (unfold_all or line_id in unfolded_ids) or not unfoldable,
                    "class": "o_azk_tb_group",
                    "columns": self._columns(report, options, row, company, None),
                    "azk_tb_kind": "group",
                    "azk_tb_code": code,
                    # The XLSX writes the code and the name in separate columns.
                    "azk_tb_name": group_name[len(code) + 1:] if code and group_name.startswith(f"{code} ")
                    else group_name,
                })
            else:
                currency = currency_by_id.get(row["currency_id"]) if row["currency_id"] else None
                line_id = report._get_generic_line_id(
                    "account.account", row["account_id"],
                    markup=f"currency_{row['currency_id']}" if currency else None,
                    parent_line_id=parent_line_id)
                name = f"{row['account_code']} {row['account_name']}"
                lines.append({
                    "id": line_id,
                    "name": f"{name} ({currency.name})" if currency else name,
                    "level": row["level"],
                    "parent_id": parent_line_id,
                    "unfoldable": False,
                    "unfolded": False,
                    "columns": self._columns(report, options, row, company, currency),
                    "azk_tb_kind": "account",
                    "azk_tb_code": row["account_code"] or "",
                    "azk_tb_name": row["account_name"] or "",
                    "azk_tb_currency": currency.name if currency else "",
                })
            line_ids[row["id"]] = line_id

        lines.append({
            "id": report._get_generic_line_id(None, None, markup="total"),
            "name": _("Total"),
            "level": 1,
            "class": "total",
            "columns": self._columns(report, options, result["totals"], company, None),
            "azk_tb_kind": "total",
        })
        # One total per transaction currency: different currencies are never
        # added together (contract 8). Their period columns hold the
        # company-currency movement of the rows in that currency.
        for total in result["currency_totals"]:
            currency = self.env["res.currency"].browse(total["currency_id"])
            row = dict.fromkeys(VALUE_KEYS.values())
            row.update(debit=total["debit"], credit=total["credit"], balance=total["balance"],
                       amount_currency=total["amount_currency"])
            lines.append({
                "id": report._get_generic_line_id("res.currency", currency.id, markup="currency_total"),
                "name": _("Total in %(currency)s", currency=currency.name),
                "level": 1,
                "class": "o_azk_tb_currency_total",
                "columns": self._columns(report, options, row, company, currency),
                "azk_tb_kind": "currency_total",
                "azk_tb_currency": currency.name,
            })
        return lines

    def _columns(self, report, options, row, company, currency):
        """One cell per report column, from the engine's numbers only."""
        columns = []
        for column in options["columns"]:
            if column["expression_label"] == "amount_currency":
                value = row.get("amount_currency") if currency else None
                columns.append(report._build_column_dict(value, column, options=options, currency=currency))
            else:
                value = row.get(VALUE_KEYS[(column["column_group_key"], column["expression_label"])])
                columns.append(report._build_column_dict(
                    value, column, options=options, currency=company.currency_id))
        return columns

    def _custom_line_postprocessor(self, report, options, lines):
        """Exports follow the preview's search bar.

        The preview hides the lines whose name does not contain the search
        text, unless they are an ancestor or a descendant of a matching line.
        The PDF and XLSX apply the same rule, so they show what the preview
        shows. The search is a display filter: unlike account prefixes, it
        changes no amount.
        """
        lines = super()._custom_line_postprocessor(report, options, lines)
        query = (options.get("filter_search_bar") or "").strip().lower()
        if options.get("export_mode") != "print" or not query:
            return lines
        matched = [line["id"] for line in lines if query in (line.get("name") or "").lower()]

        def related(line_id):
            return any(line_id == match or line_id.startswith(f"{match}|") or match.startswith(f"{line_id}|")
                       for match in matched)

        return [line for line in lines if related(line["id"])]

    def _add_warnings(self, options, result, warnings):
        """Engine warnings, an empty result, and filtered reports that need not balance."""
        for warning in result["warnings"]:
            warnings[f"azk_dynamic_trial_balance.tb_warning_{warning['code']}"] = {
                "alert_type": "warning", "message": warning["message"],
            }
        if not result["leaf_rows"]:
            warnings["azk_dynamic_trial_balance.tb_warning_no_lines"] = {"alert_type": "info"}
        tb = options[TB_OPTIONS_KEY]
        filtered = tb["account_prefixes"] or tb["journal_id"] or tb["analytic_account_id"]
        if filtered and not result["metadata"]["balanced"]:
            warnings["azk_dynamic_trial_balance.tb_warning_filtered"] = {"alert_type": "info"}
