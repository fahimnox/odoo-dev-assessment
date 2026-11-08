"""URL rules for the Odoo Partners website.

Pure functions, no Odoo imports, so they can be tested on plain strings.

Raw links and canonical identities are different things:
- A raw link is what a listing page contains, for example
  /partners/roayatec-17207720?country_id=64. Its query string tells which
  country listing it came from.
- The canonical URL, https://www.odoo.com/partners/roayatec-17207720, and the
  website id, 17207720, identify the partner whatever page it was found on.
The empty-country safeguard (PDF p. 5) must therefore check the raw link's
country_id BEFORE the query string is dropped: after canonicalization the
evidence is gone.
"""

import re
from urllib.parse import parse_qs, urljoin, urlsplit

PARTNERS_SCHEME = "https"
PARTNERS_HOST = "www.odoo.com"
SITE = f"{PARTNERS_SCHEME}://{PARTNERS_HOST}"
# The all-countries listing carries the full country menu with partner counts.
COUNTRY_LIST_URL = f"{SITE}/partners?country_all=1"

# One path segment under /partners whose trailing number is the partner's
# website id, e.g. /partners/acme-solutions-12345 or /partners/12345.
# Listing paths such as /partners/country/belgium-20 have two segments and
# never match.
_DETAIL_PATH = re.compile(r"/partners/(?:[^/]*-)?(\d+)")
# A country listing, optionally paginated: /partners/country/egypt-64/page/2,
# or /partners/country/64 before the site redirects to the slug form.
_LISTING_PATH = re.compile(r"/partners/country/(?:[^/]*-)?(\d+)(?:/page/(\d+))?")
# Reference clients link to /customers/<slug>-<id>; their avatar image URL
# carries the same res.partner id.
_CUSTOMER_PATH = re.compile(r"/customers/(?:[^/]*-)?(\d+)")
_AVATAR_PATH = re.compile(r"/web/image/res\.partner/(\d+)/")
# Translated pages live under a language prefix such as /fr_FR or /ar.
_LANG_PREFIX = re.compile(r"^/[a-z]{2,3}(?:_[A-Za-z0-9]{2,4})?(?=/(?:partners|customers)(?:/|$))")

# robots.txt of www.odoo.com (read on 2026-11-08) disallows, for every
# crawler, URLs whose query string has one of these keys, and paths of the
# form */page/*/*. The client never requests such a URL. Links that carry
# country_id are still READ from listing pages; they are never fetched.
ROBOTS_DISALLOWED_QUERY_KEYS = frozenset({
    "country_id", "grade_id", "page", "search", "order", "orderby", "selected_app", "domain",
})
_ROBOTS_DISALLOWED_PATH = re.compile(r"/page/[^/]*/")


class UrlError(ValueError):
    """A link is not the kind of link expected (for example not a partner page)."""


def _strip_language(path):
    return _LANG_PREFIX.sub("", path, count=1)


def absolute(url, base=SITE):
    """Resolve a link found on a page against the site."""
    return urljoin(base + "/", url)


def is_canonical_partner_url(url, source_id):
    """Return True if ``url`` is the canonical link of partner ``source_id``.

    Canonical means exactly https://www.odoo.com/partners/<slug>-<source_id>:
    no query string, no fragment, no trailing separator, and the id in the
    link equals the partner's website id.
    """
    if not url or not source_id:
        return False
    parts = urlsplit(url)
    if parts.scheme != PARTNERS_SCHEME or parts.netloc != PARTNERS_HOST:
        return False
    if url != f"{PARTNERS_SCHEME}://{PARTNERS_HOST}{parts.path}":
        return False  # a query string, a fragment or a bare "?" or "#"
    match = _DETAIL_PATH.fullmatch(parts.path)
    return bool(match) and int(match.group(1)) == source_id


def country_id_of(raw_url):
    """Return (value, None) for the raw link's single country_id, or (None, reason).

    The query is parsed as a whole, so country_id may be in any position.
    A missing, empty, non-numeric or repeated-and-different value is refused.
    """
    query = parse_qs(urlsplit(raw_url).query, keep_blank_values=True)
    values = {value.strip() for value in query.get("country_id", [])}
    if not values:
        return None, "missing country_id"
    if len(values) > 1:
        return None, f"several country_id values {sorted(values)}"
    value = values.pop()
    if not value.isdigit():
        return None, f"invalid country_id {value!r}"
    return value, None


def check_country_scope(raw_url, expected_country_key):
    """Return None if the raw link belongs to the expected country, else the reason.

    This is the PDF's empty-country safeguard. Call it on the raw link, before
    canonical_partner_url() drops the query string.
    """
    value, reason = country_id_of(raw_url)
    if reason:
        return reason
    if value != str(expected_country_key):
        return f"country_id {value} is not the expected country {expected_country_key}"
    return None


def canonical_partner_url(raw_url, base=SITE):
    """Return (canonical URL, website id) of a partner page link.

    Drops the query string and fragment, a language prefix and a trailing
    slash. Raises UrlError for any other kind of link.
    """
    parts = urlsplit(absolute(raw_url, base))
    if parts.scheme not in ("http", "https") or parts.netloc != PARTNERS_HOST:
        raise UrlError(f"not a link to {PARTNERS_HOST}: {raw_url}")
    path = _strip_language(parts.path).rstrip("/")
    match = _DETAIL_PATH.fullmatch(path)
    if not match:
        raise UrlError(f"not a partner page link: {raw_url}")
    return f"{SITE}{path}", int(match.group(1))


def is_partner_link(raw_url):
    try:
        canonical_partner_url(raw_url)
    except UrlError:
        return False
    return True


def listing_url(country_key, page=1):
    """URL of a country listing page; the site redirects /country/<id> to its slug form."""
    url = f"{SITE}/partners/country/{country_key}"
    return f"{url}/page/{page}" if page > 1 else url


def listing_key(url):
    """Return (country key, page number) for a country listing URL, else None."""
    path = _strip_language(urlsplit(absolute(url)).path).rstrip("/")
    match = _LISTING_PATH.fullmatch(path)
    if not match:
        return None
    return match.group(1), int(match.group(2) or 1)


def listing_page_url(listing, page):
    """The URL of another page of the same listing, keeping the site's slug."""
    path = _strip_language(urlsplit(absolute(listing)).path).rstrip("/")
    path = re.sub(r"/page/\d+$", "", path)
    return f"{SITE}{path}/page/{page}" if page > 1 else f"{SITE}{path}"


def normalize_name(name):
    return " ".join((name or "").split()).casefold()


def reference_key(link_url=None, image_url=None, name=None):
    """Return (key, source) identifying a reference client within its partner.

    Preference: the id in its /customers/<slug>-<id> link, then the same id in
    its avatar image URL, then (fallback) its normalized name. Two clients with
    the same name but different ids keep different keys; the name is used only
    when the site shows no id at all.
    """
    if link_url:
        match = _CUSTOMER_PATH.search(urlsplit(absolute(link_url)).path)
        if match:
            return match.group(1), "link"
    if image_url:
        match = _AVATAR_PATH.search(image_url)
        if match:
            return match.group(1), "image"
    normalized = normalize_name(name)
    if not normalized:
        raise UrlError("a reference without an id or a name")
    return f"name:{normalized}", "name"


def fetch_allowed(url):
    """Return None if the client may request ``url``, else the reason.

    Only https://www.odoo.com, never a query key or path that robots.txt
    disallows. The all-countries listing (country_all) is allowed.
    """
    parts = urlsplit(url)
    if parts.scheme != PARTNERS_SCHEME or parts.netloc != PARTNERS_HOST:
        return f"only {SITE} is fetched"
    keys = set(parse_qs(parts.query, keep_blank_values=True))
    blocked = sorted(keys & ROBOTS_DISALLOWED_QUERY_KEYS)
    if blocked:
        return f"robots.txt disallows URLs with {', '.join(blocked)}"
    if _ROBOTS_DISALLOWED_PATH.search(parts.path):
        return "robots.txt disallows */page/*/* paths"
    return None
