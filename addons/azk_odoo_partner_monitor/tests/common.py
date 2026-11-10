import os
import re

from bs4 import BeautifulSoup

from odoo.tests import TransactionCase

from ..services import urls

READER = "base.group_user,azk_odoo_partner_monitor.group_reader"
MANAGER = "base.group_user,azk_odoo_partner_monitor.group_manager"

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")

# The saved pages: (final URL the site served after redirects, fixture file).
# All are live-derived (tests/fixtures/README.md).
COUNTRY_LIST = ("https://www.odoo.com/partners?country_all=1", "live_country_list.html")
ANDORRA = ("https://www.odoo.com/partners/country/andorra-1", "live_listing_andorra.html")
ANGUILLA = ("https://www.odoo.com/partners/country/anguilla-5", "live_listing_anguilla_fallback.html")
EGYPT_P1 = ("https://www.odoo.com/partners/country/egypt-64", "live_listing_egypt_page1.html")
EGYPT_P11 = ("https://www.odoo.com/partners/country/egypt-64/page/11", "live_listing_egypt_page11.html")
ROAYATEC = ("https://www.odoo.com/partners/roayatec-17207720", "live_partner_roayatec.html")
DEVONEERS = ("https://www.odoo.com/partners/devoneers-32297621", "live_partner_devoneers.html")

# Every saved page, by the URL the reader asks for. Egypt's pages 2 to 10 and
# all other partner pages are not saved: asking for them fails (LookupError),
# like a failed download.
ALL_PAGES = {
    urls.COUNTRY_LIST_URL: COUNTRY_LIST,
    urls.listing_url("1"): ANDORRA,
    urls.listing_url("5"): ANGUILLA,
    urls.listing_url("64"): EGYPT_P1,
    EGYPT_P11[0]: EGYPT_P11,
    ROAYATEC[0]: ROAYATEC,
    DEVONEERS[0]: DEVONEERS,
}


def fixture(name):
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as handle:
        return handle.read()


# Variants of the saved pages, derived in code for tests (never saved as
# files): each one names what it changes.

def _card(soup, source_id):
    return soup.find("a", href=re.compile(rf"-{source_id}\?"))


def andorra_variant(listed=None, drop_ids=(), statuses=None, new_ids=None):
    """The Andorra listing with a different listed count ("All Categories"),
    cards removed, status labels changed, or partner ids changed."""
    soup = BeautifulSoup(fixture(ANDORRA[1]), "html.parser")
    if listed is not None:
        soup.select_one('#dropdown_grades_selection a[href="/partners/country/andorra-1"] span.badge'
                        ).string = str(listed)
    for source_id in drop_ids:
        _card(soup, source_id).find_parent("div", class_="col-12").decompose()
    for source_id, label in (statuses or {}).items():
        _card(soup, source_id).select_one("h5 span.badge").string = label
    for old_id, new_id in (new_ids or {}).items():
        link = _card(soup, old_id)
        link["href"] = link["href"].replace(f"-{old_id}?", f"-{new_id}?")
    return str(soup)


def country_list_variant(keep=None, drop=()):
    """The country list reduced to the ``keep`` countries, with an "All
    Countries" total that still adds up (a complete list), or without the
    ``drop`` countries and with the original total (an incomplete list)."""
    soup = BeautifulSoup(fixture(COUNTRY_LIST[1]), "html.parser")
    kept_total = 0
    for link in soup.select('a[href^="/partners/country/"]'):
        key = link["href"].rsplit("/", 1)[-1]
        if key in drop or (keep is not None and key not in keep):
            link.decompose()
        else:
            kept_total += int(link.select_one("span.badge").get_text(strip=True))
    if keep is not None:
        soup.select_one('a[href*="country_all"] span.badge').string = str(kept_total)
    return str(soup)


def listing_card_variant(fixture_name, source_id, old_text, new_text):
    """A listing page where one partner's card shows ``new_text`` instead of ``old_text``."""
    soup = BeautifulSoup(fixture(fixture_name), "html.parser")
    small = _card(soup, source_id).find("small", string=re.compile(re.escape(old_text)))
    small.string = small.string.replace(old_text, new_text)
    return str(soup)


class FixtureSite:
    """A ``fetch(url)`` for services/reader.py, backed by the saved fixtures.

    ``pages`` maps a requested URL to (final URL, fixture name); ``html``
    optionally replaces a fixture's text with a variant. A URL without a saved
    page raises LookupError, and ``failures`` makes a URL raise a given
    exception (for example a timeout): like a failed download, never an empty
    page. Every requested URL is recorded in ``requested``.
    """

    def __init__(self, pages, failures=None, html=None):
        self.pages = pages
        self.failures = failures or {}
        self.html = html or {}
        self.requested = []

    def __call__(self, url):
        self.requested.append(url)
        if url in self.failures:
            raise self.failures[url]
        if url not in self.pages:
            raise LookupError(f"no saved page for {url}")
        final_url, name = self.pages[url]
        return final_url, self.html.get(url) or fixture(name)


class PartnerMonitorCase(TransactionCase):
    """Shared fixtures: the models and two countries observed from the website.

    Test records use positive website ids, like real scraped data. The demo
    records (negative ids, "demo-" country keys) may also exist in the test
    database, so tests never count whole tables.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Country = cls.env["azk_odoo_partner_monitor.country"]
        cls.Partner = cls.env["azk_odoo_partner_monitor.partner"]
        cls.History = cls.env["azk_odoo_partner_monitor.status.history"]
        cls.Reference = cls.env["azk_odoo_partner_monitor.reference"]
        cls.Run = cls.env["azk_odoo_partner_monitor.sync.run"]
        cls.WorkItem = cls.env["azk_odoo_partner_monitor.work.item"]
        cls.SyncError = cls.env["azk_odoo_partner_monitor.sync.error"]
        cls.belgium = cls.Country._record_observation(
            {"source_key": "20", "name": "Belgium", "total_partner_count": 2})
        cls.egypt = cls.Country._record_observation(
            {"source_key": "65", "name": "Egypt", "total_partner_count": 1})

    def observe(self, source_id, status, observed_on, **values):
        """Record one listing observation, as the sync engine will."""
        values.setdefault("name", f"Partner {source_id}")
        values.setdefault("country_id", self.belgium.id)
        return self.Partner._record_observation(
            {"source_id": source_id, "current_status": status, **values}, observed_on)

    @staticmethod
    def history_of(partner):
        """The partner's status history, oldest first."""
        return partner.status_history_ids.sorted(lambda row: (row.change_date, row.id))
