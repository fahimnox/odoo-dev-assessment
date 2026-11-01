{
    "name": "Odoo Partner Monitor",
    "version": "18.0.1.0.0",
    "summary": "Track partners listed on the official Odoo Partners pages: "
               "status history, client references and dashboards.",
    "category": "Tools",
    "author": "fahimnox",
    "license": "LGPL-3",
    # mail: chatter notification to a configurable user on scrape failures.
    "depends": ["mail"],
    # Scraping uses requests and BeautifulSoup, as the assessment specifies.
    "external_dependencies": {"python": ["requests", "beautifulsoup4"]},
    "data": [],
    "application": True,
    "installable": True,
}
