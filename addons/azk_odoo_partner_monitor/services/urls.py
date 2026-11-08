"""URL rules for the Odoo Partners website.

Pure functions, no Odoo imports, so they can be tested on plain strings.
Stage 03 needs only the canonical-form check used by the partner model.
Stage 04 adds the country-scope check (the PDF's "?country_id=" rule) and the
conversion of raw listing links into canonical URLs.
"""

import re
from urllib.parse import urlsplit

PARTNERS_SCHEME = "https"
PARTNERS_HOST = "www.odoo.com"

# One path segment under /partners whose trailing number is the partner's
# website id, e.g. /partners/acme-solutions-12345 or /partners/12345.
# Listing paths such as /partners/country/belgium-20 have two segments and
# never match.
_DETAIL_PATH = re.compile(r"/partners/(?:[^/]*-)?(\d+)")


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
