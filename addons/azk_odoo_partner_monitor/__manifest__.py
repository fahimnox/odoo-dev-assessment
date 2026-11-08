{
    "name": "Odoo Partner Monitor",
    "version": "18.0.1.1.0",
    "summary": "Track partners listed on the official Odoo Partners pages: "
               "status history, client references and dashboards.",
    "category": "Tools",
    "author": "fahimnox",
    "license": "LGPL-3",
    # mail: sync runs have a chatter, and failures are posted there for a
    # configurable user (docs/architecture.md 5.7).
    "depends": ["mail"],
    # Scraping uses requests and BeautifulSoup, as the assessment specifies.
    "external_dependencies": {"python": ["requests", "beautifulsoup4"]},
    "data": [
        "security/partner_monitor_security.xml",
        "security/ir.model.access.csv",
        "data/partner_monitor_config.xml",
        "views/country_views.xml",
        "views/partner_views.xml",
        "views/status_history_views.xml",
        "views/reference_views.xml",
        "views/sync_views.xml",
        "views/res_config_settings_views.xml",
        "views/menus.xml",
    ],
    "demo": [
        "demo/partner_monitor_demo.xml",
    ],
    "application": True,
    "installable": True,
}
