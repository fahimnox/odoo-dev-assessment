{
    "name": "Dynamic Trial Balance",
    "version": "18.0.1.1.0",
    "summary": "Trial balance wizard with account, journal and analytic filters, "
               "hierarchy, and Preview, PDF and XLSX outputs.",
    "category": "Accounting/Accounting",
    "author": "fahimnox",
    "license": "LGPL-3",
    # account_reports (Enterprise): the report framework whose UI and
    # exporters will host the report, and the standard Trial Balance that
    # our conventions follow (docs/calculation_contract.md). In this build it
    # depends on accountant, which brings account and analytic accounting.
    "depends": ["account_reports"],
    # XLSX export.
    "external_dependencies": {"python": ["XlsxWriter"]},
    "data": [
        "security/ir.model.access.csv",
        "security/trial_balance_security.xml",
        "views/trial_balance_wizard_views.xml",
    ],
    "application": False,
    "installable": True,
}
