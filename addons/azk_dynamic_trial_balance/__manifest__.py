{
    "name": "Dynamic Trial Balance",
    "version": "18.0.1.0.0",
    "summary": "Trial balance wizard with account, journal and analytic filters, "
               "hierarchy, and Preview, PDF and XLSX outputs.",
    "category": "Accounting/Accounting",
    "author": "fahimnox",
    "license": "LGPL-3",
    # account: journal items, accounts, account groups and journals
    # (it also brings analytic accounting).
    "depends": ["account"],
    # XLSX export.
    "external_dependencies": {"python": ["XlsxWriter"]},
    "data": [],
    "application": False,
    "installable": True,
}
