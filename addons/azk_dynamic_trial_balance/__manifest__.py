{
    "name": "Dynamic Trial Balance",
    "version": "18.0.1.3.0",
    "summary": "Trial balance wizard with account, journal and analytic filters, "
               "hierarchy, and Preview, PDF and XLSX outputs.",
    "category": "Accounting/Accounting",
    "author": "fahimnox",
    "license": "LGPL-3",
    # account_reports (Enterprise): the report framework whose UI, PDF and
    # XLSX exports host the report (our report record and custom handler),
    # and the standard Trial Balance that our conventions follow
    # (docs/calculation_contract.md). In this build it depends on accountant,
    # which brings account and analytic accounting.
    "depends": ["account_reports"],
    # XLSX export.
    "external_dependencies": {"python": ["XlsxWriter"]},
    "data": [
        "security/ir.model.access.csv",
        "security/trial_balance_security.xml",
        "data/trial_balance_report.xml",
        "data/pdf_export_templates.xml",
        "views/trial_balance_wizard_views.xml",
    ],
    "demo": [
        "demo/trial_balance_demo.xml",
    ],
    "assets": {
        # The report UI of account_reports loads in the main backend bundle,
        # so its filter extension must load there too.
        "web.assets_backend": [
            "azk_dynamic_trial_balance/static/src/components/**/*",
        ],
    },
    "application": False,
    "installable": True,
}
