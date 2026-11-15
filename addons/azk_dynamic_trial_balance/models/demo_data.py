"""Installable demo data of the Dynamic Trial Balance (Stage 09).

The assessment asks for demo or test data with posted and unposted journal
entries, entries in other currencies and with analytic accounts, and a chart
of accounts deep enough to test the hierarchy. ``demo/trial_balance_demo.xml``
calls ``_create_demo_data`` when the module is installed with demo data:
Odoo loads demo files as noupdate data and runs their functions at install
only, never on an upgrade. The function creates everything in a dedicated
company and does nothing when that company already exists, so neither an
upgrade nor a second call duplicates the records. A database that got the
module before this demo data existed can receive it by calling
``_create_demo_data`` once from an Odoo shell.

While modules are still loading, the creation waits for ``_register_hook``,
which Odoo calls once every module of the registry is loaded. Loading a
chart of accounts earlier logs "Incorrect usage of try_loading without a
fully loaded registry": modules loaded after this one could not adapt the
new company's chart. The account module defers its own first chart the
same way (``ir.module.module._register_hook``).

The company, "AZK Trial Balance Demo (EGP)", uses Odoo's generic chart, the
Egyptian pound and a calendar fiscal year. Its January 2026 report is the
assessment's example: Bank ends at 1,200 with posted entries only and at
1,000 with drafts.
"""
from odoo import Command, api, models

DEMO_COMPANY_XMLID = "azk_dynamic_trial_balance.demo_company"
DEMO_COMPANY_NAME = "AZK Trial Balance Demo (EGP)"

# Account groups (prefix, name), named as in the TB-H test fixture. Bank
# 101401 sits five levels deep: 1 > 10 > 101 > 1014 > 10140. Liabilities (2...)
# and Current Year Earnings (999999) have no group.
DEMO_GROUPS = [
    ("1", "Assets"),
    ("10", "Current Assets"),
    ("101", "Cash and Receivables"),
    ("1014", "Bank and Cash"),
    ("10140", "Bank Accounts"),
    ("12", "Receivables and Prepaid Expenses"),
    ("3", "Equity"),
    ("4", "Income"),
    ("6", "Expenses"),
    ("60", "Operating Expenses"),
]


class TrialBalanceDemo(models.AbstractModel):
    _name = "azk_dynamic_trial_balance.demo"
    _description = "Dynamic Trial Balance demo data"

    @api.model
    def _create_demo_data(self):
        """Create the demo company and its entries once.

        Returns True if it created them now, False if they exist already or
        if the creation waits for the end of the module loading.
        """
        if self.env.ref(DEMO_COMPANY_XMLID, raise_if_not_found=False):
            return False
        if not self.env.registry.loaded:
            self.env.registry._azk_tb_create_demo_data = True
            return False
        Currency = self.env["res.currency"].with_context(active_test=False)
        egp, usd, eur = (Currency.search([("name", "=", code)], limit=1) for code in ("EGP", "USD", "EUR"))
        (egp | usd | eur).write({"active": True})

        # Without a country, loading the generic chart would make its fiscal
        # country (the United States) the company's country. With a country,
        # outside tests and module loading (for example the one-time call from
        # an Odoo shell), Odoo installs that country's localization, which
        # commits the transaction, and queues the country's own chart for the
        # new company. This function loads the generic chart itself, so it sets
        # the flag that Odoo sets while it loads a chart (chart_template_load),
        # which turns that automatic install off; the flag is then dropped.
        company = self.env["res.company"].with_context(chart_template_load=True).create({
            "name": DEMO_COMPANY_NAME, "currency_id": egp.id, "country_id": self.env.ref("base.eg").id,
        }).with_env(self.env)
        self.env["ir.model.data"]._update_xmlids([
            {"xml_id": DEMO_COMPANY_XMLID, "record": company, "noupdate": True},
        ])
        users = self.env.ref("base.user_admin")
        demo_user = self.env.ref("base.user_demo", raise_if_not_found=False)
        if demo_user:
            users |= demo_user
        users.write({"company_ids": [Command.link(company.id)]})
        self.env["account.chart.template"].try_loading("generic_coa", company=company, install_demo=False)
        # The chart may set its own currency; the demo company reports in EGP.
        company.currency_id = egp

        # Exchange rates of this company: 1 USD = 50 EGP, 1 EUR = 55 EGP.
        self.env["res.currency.rate"].create([
            {"name": "2025-01-01", "currency_id": usd.id, "company_id": company.id, "rate": 1 / 50},
            {"name": "2025-01-01", "currency_id": eur.id, "company_id": company.id, "rate": 1 / 55},
        ])
        for prefix, name in DEMO_GROUPS:
            self.env["account.group"].create({"name": name, "code_prefix_start": prefix, "company_id": company.id})

        accounts = self._demo_accounts(company)
        journals = self._demo_journals(company)
        analytic = self._demo_analytic_accounts(company)
        self._demo_entries(company, accounts, journals, analytic, usd, eur)
        return True

    def _register_hook(self):
        super()._register_hook()
        if getattr(self.env.registry, "_azk_tb_create_demo_data", False):
            del self.env.registry._azk_tb_create_demo_data
            self._create_demo_data()

    def _demo_accounts(self, company):
        Account = self.env["account.account"].with_company(company)
        domain = Account._check_company_domain(company)
        codes = {"bank": "101401", "current_assets": "101000", "prepaid": "128000", "capital": "301000",
                 "revenue": "400000", "expense": "600000"}
        return {name: Account.search([("code", "=", code), *domain], limit=1) for name, code in codes.items()}

    def _demo_journals(self, company):
        Journal = self.env["account.journal"]
        domain = Journal._check_company_domain(company)
        return {
            "misc": Journal.search([*domain, ("type", "=", "general")], limit=1),
            "bank": Journal.search([*domain, ("type", "=", "bank")], limit=1),
        }

    def _demo_analytic_accounts(self, company):
        Plan = self.env["account.analytic.plan"]
        departments = Plan.create({"name": "Demo Departments"})
        projects = Plan.create({"name": "Demo Projects"})
        Analytic = self.env["account.analytic.account"]
        return {
            "sales": Analytic.create({"name": "Sales Department", "plan_id": departments.id,
                                      "company_id": company.id}),
            "admin": Analytic.create({"name": "Administration", "plan_id": departments.id,
                                      "company_id": company.id}),
            "nile": Analytic.create({"name": "Project Nile", "plan_id": projects.id, "company_id": company.id}),
        }

    def _demo_entries(self, company, a, journals, analytic, usd, eur):
        def entry(date, ref, lines, state="posted", journal="misc"):
            move = self.env["account.move"].with_company(company).create({
                "move_type": "entry",
                "date": date,
                "ref": ref,
                "journal_id": journals[journal].id,
                "line_ids": [
                    Command.create({"account_id": account.id, "name": ref, "debit": debit, "credit": credit,
                                    **(extra[0] if extra else {})})
                    for account, debit, credit, *extra in lines
                ],
            })
            if state in ("posted", "cancel"):
                move.action_post()
            if state == "cancel":
                move.button_cancel()
            return move

        def foreign(currency, amount):
            return {"currency_id": currency.id, "amount_currency": amount}

        # The assessment's example (Stage 07 base fixture), plus 2025 revenue.
        entry("2025-06-30", "TB Demo: 2025 sale on credit", [(a["current_assets"], 700, 0), (a["revenue"], 0, 700)])
        entry("2025-12-31", "TB Demo: opening capital", [(a["bank"], 1000, 0), (a["capital"], 0, 1000)])
        entry("2026-01-10", "TB Demo: office supplies", [(a["expense"], 300, 0), (a["bank"], 0, 300)])
        entry("2026-01-20", "TB Demo: customer receipt", [(a["bank"], 500, 0), (a["revenue"], 0, 500)],
              journal="bank")
        entry("2026-01-25", "TB Demo: consultant fee (draft)", [(a["expense"], 200, 0), (a["bank"], 0, 200)],
              state="draft")
        entry("2026-01-26", "TB Demo: duplicate bill (cancelled)", [(a["expense"], 400, 0), (a["bank"], 0, 400)],
              state="cancel")
        entry("2026-02-01", "TB Demo: February bank fee", [(a["expense"], 50, 0), (a["bank"], 0, 50)])

        # Foreign currencies on Current Assets, against Prepaid Expenses in EGP.
        x, y = a["current_assets"], a["prepaid"]
        entry("2025-12-20", "TB Demo: USD deposit", [(x, 1000, 0, foreign(usd, 20)), (y, 0, 1000)])
        entry("2025-12-22", "TB Demo: EUR refund", [(y, 1650, 0), (x, 0, 1650, foreign(eur, -30))])
        entry("2026-01-05", "TB Demo: USD deposit", [(x, 5000, 0, foreign(usd, 100)), (y, 0, 5000)])
        entry("2026-01-12", "TB Demo: USD refund", [(y, 2000, 0), (x, 0, 2000, foreign(usd, -40))])
        entry("2026-01-18", "TB Demo: EUR deposit", [(x, 3850, 0, foreign(eur, 70)), (y, 0, 3850)])
        entry("2026-01-25", "TB Demo: EUR refund", [(y, 1100, 0), (x, 0, 1100, foreign(eur, -20))])
        entry("2026-01-28", "TB Demo: USD deposit (draft)", [(x, 500, 0, foreign(usd, 10)), (y, 0, 500)],
              state="draft")

        # Analytic distributions: 60/40 across two departments, and a key
        # spanning two plans (a department and a project).
        sales, admin, nile = analytic["sales"], analytic["admin"], analytic["nile"]
        entry("2026-03-10", "TB Demo: shared marketing cost", [
            (a["expense"], 1000, 0, {"analytic_distribution": {str(sales.id): 60, str(admin.id): 40}}),
            (a["bank"], 0, 1000),
        ])
        entry("2026-03-12", "TB Demo: Nile project sales cost", [
            (a["expense"], 200, 0, {"analytic_distribution": {f"{sales.id},{nile.id}": 100}}),
            (a["bank"], 0, 200),
        ])
