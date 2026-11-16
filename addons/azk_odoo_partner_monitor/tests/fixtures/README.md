# Test fixtures

All seven files here are **live-derived**: trimmed copies of public pages of https://www.odoo.com read on 2026-11-08 (UTC). Tests derive a few variants in code from these files (for example a badge renamed to an unknown status); those variants are marked in the tests. The synthetic cases planned in Stage 04 (login page, rate limit, cut-off and unusable pages) were written in Stage 10 as answers built in code, not as files: see `tests/test_http_client.py`.

## How they were made

- The full pages were saved with curl during a small manual sample: 9 requests including robots.txt, between 08:01 and 08:09 UTC, about 4 seconds apart. The full pages are kept privately, outside the repository.
- A script kept only the elements the parsers read. Scripts, styles, navigation, addresses and other page parts were removed. For partner pages, each reference's description was replaced by "(description trimmed)".
- BeautifulSoup re-serialized the kept elements: entities such as `&nbsp;` became the equivalent characters, and attributes are sorted. The markup is otherwise unchanged.
- Each file starts with a comment giving its source URL and fetch time (the server's Date header).

## Files

- `live_country_list.html`
  - Source: `/partners?country_all=1`, 08:02:48.
  - Kept: the country menu, with all 170 countries and the "All Countries" count (4517).
  - Used for: country discovery and the counts check.
- `live_listing_andorra.html`
  - Source: `/partners/country/1`, redirected to `/partners/country/andorra-1`, 08:02:53.
  - Kept: the category menu, the country menu cut to 3 items, and both partner cards.
  - Used for: a complete one-page country.
- `live_listing_egypt_page1.html`
  - Source: `/partners/country/egypt-64`, 08:08:44.
  - Kept: the menus, 3 of the 20 cards, and the pager (page 1 of 11).
  - Used for: pagination and card values.
- `live_listing_egypt_page11.html`
  - Source: `/partners/country/egypt-64/page/11`, 08:03:02.
  - Kept: the menus, 7 of the 10 cards, and the pager (page 11 of 11).
  - Used for: the last page, a missing retention rate, and zero values.
- `live_listing_anguilla_fallback.html`
  - Source: `/partners/country/5`, redirected to `/partners/country/anguilla-5`, 08:02:58.
  - Kept: the no-partners notice, 3 of the 20 global cards (links without `country_id`), and the global pager.
  - Used for: the empty-country safeguard.
- `live_partner_roayatec.html`
  - Source: `/partners/roayatec-17207720`, 08:03:06.
  - Kept: the heading, the statistics, and 3 of the 135 references.
  - Used for: partner values, reference identities, and an incomplete reference list.
- `live_partner_devoneers.html`
  - Source: `/partners/devoneers-32297621`, 08:04:26.
  - Kept: the heading and the statistics. The page has no reference list.
  - Used for: a partner without references, and a missing retention rate.

The trimming is visible in the results: the Egypt fixtures hold fewer cards than the 210 partners their pages announce, and the RoayaTec fixture holds 3 of 135 references. Tests use this on purpose, for incomplete snapshots.
