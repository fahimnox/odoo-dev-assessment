"""Connects a page source to the parsers. No HTTP code and no database here.

``fetch(url)`` is any callable that returns ``(final_url, html)`` for a page
of the site, after redirects, and RAISES on any failure: a timeout, a
connection error, an HTTP error, an unexpected page. In production it is
services/http_client.py (PartnersHttpClient); the tests use fixture-backed
fakes.

Nothing here turns a failure into an empty result: an exception from
``fetch``, a refused URL or a ParseError propagates to the caller, which must
not ingest anything for that scope.
"""

from . import parsers, urls

MAX_LISTING_PAGES = 60


class NotAllowedError(ValueError):
    """A URL the client must not request (robots.txt rules, other hosts)."""


def _allowed(url):
    reason = urls.fetch_allowed(url)
    if reason:
        raise NotAllowedError(f"{url}: {reason}")
    return url


def read_country_list(fetch):
    final_url, html = fetch(_allowed(urls.COUNTRY_LIST_URL))
    return parsers.parse_country_list(html, final_url)


def read_country_listing(fetch, country_key, max_pages=MAX_LISTING_PAGES):
    """Read every page of one country's listing, following the site's pager.

    Stops after the first page when the page is not this country's listing
    (empty country or unscoped), so a global list is never followed.
    """
    pages, url = [], urls.listing_url(country_key)
    while url:
        final_url, html = fetch(_allowed(url))
        page = parsers.parse_listing_page(html, final_url, country_key)
        pages.append(page)
        if page.scope != "country" or not page.next_url:
            break
        if len(pages) >= max_pages:
            page.problems.append(f"stopped after {max_pages} pages")
            break
        url = page.next_url
    return pages


def read_partner_page(fetch, partner_url):
    final_url, html = fetch(_allowed(partner_url))
    return parsers.parse_partner_page(html, final_url)
