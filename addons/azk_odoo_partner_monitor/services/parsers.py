"""HTML parsers for the Odoo Partners website: pure functions over saved HTML.

They never fetch a page and never touch the database. Each returns a typed
result with the source URL, the expected counts, the pagination state, the
missing values and completeness indicators, or raises ParseError when the
page is not the expected kind of page. A failed parse is never reported as a
valid empty result.

The selectors were chosen from the live pages read on 2026-11-08
(docs/live_site_notes.md). The labels read in the text ("Average Project",
"Large Project", "References", "Largest", "Average", "Customer Retention" and
the empty-country notice) are the English ones.
"""

import hashlib
import re
from dataclasses import dataclass, field

from bs4 import BeautifulSoup

from . import urls

# Status label shown on the site -> status key of the model (Ready < Silver < Gold).
STATUS_BY_LABEL = {"ready": "ready", "silver": "silver", "gold": "gold"}
# Shown when a country has no partners; the page then lists all countries.
EMPTY_COUNTRY_NOTICE = "no matching partners found for the selected country"

_NUMBER = r"\d[\d,]*(?:\.\d+)?"


class ParseError(ValueError):
    """The page is not the expected kind of page, or lacks a required part."""

    def __init__(self, message, url=None):
        super().__init__(f"{message} [{url}]" if url else message)
        self.url = url


@dataclass(frozen=True)
class Country:
    source_key: str
    name: str
    partner_count: int | None


@dataclass
class CountryList:
    source_url: str
    countries: list
    total_count: int | None  # the "All Countries" count
    complete: bool           # every country has a count, and the counts add up to the total
    problems: list = field(default_factory=list)


@dataclass(frozen=True)
class PartnerCard:
    source_id: int
    name: str
    status: str
    raw_url: str        # the link exactly as the listing shows it
    partner_url: str    # its canonical form
    retention_rate: float | None
    average_project_size: float | None
    largest_project_size: int | None
    total_references_count: int | None

    def observation(self, country_id):
        """Values for partner._record_observation; None means "not shown" (unknown)."""
        return {
            "source_id": self.source_id,
            "name": self.name,
            "partner_url": self.partner_url,
            "current_status": self.status,
            "country_id": country_id,
            "retention_rate": self.retention_rate,
            "average_project_size": self.average_project_size,
            "largest_project_size": self.largest_project_size,
            "total_references_count": self.total_references_count,
        }

    def metrics_fingerprint(self):
        """Hash of the card's metrics, the change-detection key for details refreshes.

        It covers the four values that can make the partner page worth reading
        again: retention rate, average and largest project size, and the
        reference count. None (not shown) is part of the value.
        """
        text = "|".join(repr(value) for value in (
            self.retention_rate, self.average_project_size,
            self.largest_project_size, self.total_references_count))
        return hashlib.sha256(text.encode()).hexdigest()[:32]


@dataclass(frozen=True)
class SkippedLink:
    raw_url: str
    reason: str


@dataclass
class ListingPage:
    source_url: str           # the final URL of the page, after redirects
    country_key: str          # the country this page was read for
    scope: str                # "country", "empty_country" or "unscoped"
    partners: list            # PartnerCard of this country, without duplicates
    rejected: list            # SkippedLink refused by the country-scope rule
    invalid: list             # SkippedLink in scope but unreadable (e.g. unknown status)
    listed_count: int | None  # partners the page says the country has ("All Categories")
    page: int
    last_page: int
    next_url: str | None
    problems: list = field(default_factory=list)


@dataclass(frozen=True)
class Reference:
    source_key: str
    name: str
    key_source: str  # "link", "image" or "name" (see urls.reference_key)


@dataclass
class PartnerPage:
    source_url: str
    source_id: int
    partner_url: str
    name: str
    status: str
    retention_rate: float | None
    average_project_size: float | None
    largest_project_size: int | None
    expected_reference_count: int | None  # "References - N"; None when the page shows no count
    references: list
    problems: list = field(default_factory=list)


def _soup(html):
    return BeautifulSoup(html or "", "html.parser")


def _text(node):
    return " ".join(node.get_text(" ").split()) if node is not None else ""


def _number(pattern, text, cast=float):
    match = re.search(pattern, text or "")
    return cast(match.group(1).replace(",", "")) if match else None


def _reject_login_page(soup, url):
    if soup.select_one('form[action*="/web/login"], input[name="password"]'):
        raise ParseError("a login page instead of a partners page", url)


def _count_and_label(link):
    """The text of a menu item without its count badge, and the count."""
    badge = link.select_one("span.badge")
    count = _number(r"(\d[\d,]*)", _text(badge), int) if badge is not None else None
    label = " ".join("".join(link.find_all(string=True, recursive=False)).split())
    return label, count


def _country_menu(soup):
    """The country menu: the dropdown with an "All Countries" item AND country
    items with partner counts. The industry menu also links to country_all, but
    without counts; the category menu has counts but no "All Countries" item."""
    for menu in soup.select("div.dropdown-menu"):
        if (menu.select('a[href*="country_all"] span.badge')
                and menu.select('a[href^="/partners/country/"] span.badge')):
            return menu
    return None


def parse_country_list(html, source_url):
    soup = _soup(html)
    _reject_login_page(soup, source_url)
    menu = _country_menu(soup)
    if menu is None:
        raise ParseError("no country menu with partner counts", source_url)
    total, countries, problems, seen = None, [], [], set()
    for link in menu.select("a[href]"):
        label, count = _count_and_label(link)
        if "country_all" in link["href"]:
            total = count
            continue
        key = urls.listing_key(link["href"])
        if key is None:
            continue
        source_key = key[0]
        if not label:
            problems.append(f"country {source_key} has no name")
        elif source_key in seen:
            problems.append(f"country {source_key} is listed twice")
        else:
            if count is None:
                problems.append(f"country {source_key} has no partner count")
            seen.add(source_key)
            countries.append(Country(source_key, label, count))
    if not countries:
        problems.append("the country menu lists no country")
    if total is None:
        problems.append("no partner count for all countries")
    else:
        listed = sum(country.partner_count or 0 for country in countries)
        if listed != total:
            problems.append(f"the country counts add up to {listed}, not to the {total} partners of all countries")
    return CountryList(source_url, countries, total, not problems, problems)


def _card_links(soup):
    """Partner cards: links to a partner page that contain the card title (h5)."""
    links = []
    for heading in soup.select("a[href] h5"):
        link = heading.find_parent("a")
        if link is not None and link not in links and urls.is_partner_link(link["href"]):
            links.append(link)
    return links


def _name(heading, url):
    for span in heading.find_all("span", recursive=False):
        if "badge" not in (span.get("class") or []):
            name = _text(span)
            if name:
                return name
    raise ParseError("no partner name", url)


def _status(heading, url):
    badge = heading.select_one("span.badge")
    if badge is None:
        raise ParseError("no status badge", url)
    label = _text(badge)
    status = STATUS_BY_LABEL.get(label.casefold())
    if status is None:
        raise ParseError(f"unknown status {label!r}", url)
    return status


def _first(pattern, texts, cast=float):
    for text in texts:
        value = _number(pattern, text, cast)
        if value is not None:
            return value
    return None


def _parse_card(link, raw_url, partner_url, source_id):
    heading = link.select_one("h5")
    name = _name(heading, raw_url)
    status = _status(heading, raw_url)
    retention = None
    for small in link.select("small"):
        match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*%", _text(small))
        if match:
            retention = float(match.group(1))
            break
    texts = [_text(small) for small in link.select("small.text-muted")]
    average = _first(r"Average Project:\s*(" + _NUMBER + r")\s*users?", texts)
    largest = _first(r"Large Project:\s*~?\s*(\d[\d,]*)\+?\s*users?", texts, int)
    ref_header = link.select_one("div.stat_ref > div")
    references = _number(r"^(\d[\d,]*)\s+References?\b", _text(ref_header), int)
    return PartnerCard(source_id, name, status, raw_url, partner_url,
                       retention, average, largest, references)


def _category_count(soup, country_key):
    """Partners of the page's scope: the "All Categories" item of the category menu,
    accepted only when it points to this country's listing."""
    for menu in soup.select("div.dropdown-menu"):
        if not menu.select('a[href*="/partners/grade/"] span.badge'):
            continue
        for link in menu.select("a[href]"):
            if "/partners/grade/" in link["href"]:
                continue
            key = urls.listing_key(link["href"])
            if key is not None and link.select_one("span.badge") is not None:
                return _count_and_label(link)[1] if key[0] == country_key else None
    return None


def _pagination(soup, source_url, country_key):
    landed = urls.listing_key(source_url)
    current = landed[1] if landed else 1
    pager = soup.select_one("ul.pagination")
    if pager is None:
        return current, current, None
    pages = {}
    for link in pager.select("a.page-link[href]"):
        key = urls.listing_key(link["href"])
        if key is not None and key[0] == country_key:  # links to other scopes are ignored
            pages[key[1]] = link["href"]
    active = pager.select_one("li.active a.page-link")
    if active is not None and _text(active).isdigit():
        current = int(_text(active))
    last = max([current, *pages])
    next_url = None
    if current < last:
        next_url = urls.absolute(pages.get(current + 1) or urls.listing_page_url(source_url, current + 1))
    return current, last, next_url


def parse_listing_page(html, source_url, country_key):
    """Read one page of a country listing.

    Every card link is checked against the expected country BEFORE it is
    canonicalized (urls.check_country_scope). The scope of the page is:
    - "country": the page lists partners of this country;
    - "empty_country": the site says the country has no partners and shows
      all countries instead (a valid empty result);
    - "unscoped": the page is not this country's listing (another country, a
      global list without the notice, ...); nothing on it may be used.
    """
    soup = _soup(html)
    _reject_login_page(soup, source_url)
    country_key = str(country_key)
    links = _card_links(soup)
    notice = any(EMPTY_COUNTRY_NOTICE in _text(alert).casefold() for alert in soup.select('[role="alert"]'))
    if not links and not notice:
        raise ParseError("no partner cards and no empty-country notice", source_url)

    partners, rejected, invalid, problems, seen = [], [], [], [], set()
    for link in links:
        raw_url = link["href"]
        reason = urls.check_country_scope(raw_url, country_key)
        if reason:
            rejected.append(SkippedLink(raw_url, reason))
            continue
        partner_url, source_id = urls.canonical_partner_url(raw_url)
        if source_id in seen:
            problems.append(f"partner {source_id} is listed twice")
            continue
        try:
            card = _parse_card(link, raw_url, partner_url, source_id)
        except ParseError as exc:
            invalid.append(SkippedLink(raw_url, str(exc)))
            continue
        seen.add(source_id)
        partners.append(card)

    landed = urls.listing_key(source_url)
    if notice:
        scope = "empty_country"
        if partners:
            scope = "unscoped"
            problems.append("cards of this country on a page that says it has no partners")
        partners = []
    elif landed is None or landed[0] != country_key:
        scope = "unscoped"
        problems.append(f"the page is not the listing of country {country_key}: {source_url}")
    elif not partners and not invalid:
        scope = "unscoped"
        problems.append(f"no card on the page belongs to country {country_key}")
    else:
        scope = "country"

    if scope == "country":
        listed_count = _category_count(soup, country_key)
        page, last_page, next_url = _pagination(soup, source_url, country_key)
    else:
        listed_count, next_url = None, None
        page = last_page = landed[1] if landed else 1
    return ListingPage(source_url, country_key, scope, partners, rejected, invalid,
                       listed_count, page, last_page, next_url, problems)


def parse_partner_page(html, source_url):
    """Read a partner's own page: its values and its list of references."""
    soup = _soup(html)
    _reject_login_page(soup, source_url)
    heading = soup.select_one("h1#partner_name")
    if heading is None:
        raise ParseError("no partner heading", source_url)
    canonical = soup.select_one('link[rel="canonical"][href]')
    try:
        partner_url, source_id = urls.canonical_partner_url(canonical["href"] if canonical else source_url)
    except urls.UrlError as exc:
        raise ParseError(str(exc), source_url) from exc
    if urls.is_partner_link(source_url) and urls.canonical_partner_url(source_url)[1] != source_id:
        raise ParseError(f"the page is about partner {source_id}, not the one requested", source_url)
    name = _name(heading, source_url)
    status = _status(heading, source_url)  # an unknown status fails the page (D-09)

    size_text = _text(soup.select_one("div.stat_size"))
    largest = _number(r"Largest:\s*~?\s*(\d[\d,]*)\+?\s*users?", size_text, int)
    average = _number(r"Average:\s*(" + _NUMBER + r")\s*users?", size_text)
    retention = _number(r"Customer Retention\s*(" + _NUMBER + r")\s*%", size_text)
    expected = _number(r"References\s*-\s*(\d[\d,]*)", _text(soup.select_one("div.stat_ref > div")), int)

    references, problems, seen = [], [], set()
    title = soup.select_one("h3#references")
    for card in title.find_next_siblings("div", class_="card") if title is not None else []:
        link = card.select_one('a[href*="/customers/"]')
        image = card.select_one('img[src*="/web/image/res.partner/"]')
        if link is None and image is None and not _text(card):
            # A completely empty card holds no reference (seen live on
            # 2026-11-15: 18 cards for "References - 17", one of them empty).
            # Whether the list is complete is still decided by the count.
            continue
        if link is not None:
            ref_name = _text(link.select_one("span") or link)
        elif image is not None:
            ref_name = (image.get("alt") or "").strip()
        else:
            ref_name = _text(card.select_one(".card-body span"))
        if not ref_name:
            problems.append("a reference without a name")
            continue
        key, key_source = urls.reference_key(
            link["href"] if link is not None else None,
            image["src"] if image is not None else None,
            ref_name)
        if key in seen:
            problems.append(f"reference {key} is listed twice")
            continue
        seen.add(key)
        references.append(Reference(key, ref_name, key_source))
    return PartnerPage(source_url, source_id, partner_url, name, status, retention, average,
                       largest, expected, references, problems)
