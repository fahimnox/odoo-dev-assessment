# Odoo Partners website: live sample and selectors (Stage 04)

_Recorded 2026-11-08. This is the evidence behind the parsers in `addons/azk_odoo_partner_monitor/services/parsers.py`. The site can change; the fixtures in `tests/fixtures/` keep the markup as it was on this date._

## The sample (manual, with curl)

The sample was 9 GET requests, about 4 seconds apart, between 08:01 and 08:09 UTC. Every page returned HTTP 200. The full pages are kept privately in `<kit-root>/runtime/logs/stage04_live/`, outside the repository.

- `/robots.txt`: 1627 bytes.
- `/partners`: the default page. It chose the visitor's country (Egypt) from the IP address.
- `/partners?country_all=1`: the all-countries listing.
- `/partners/country/1`: redirected to `/partners/country/andorra-1`. Andorra has 2 partners.
- `/partners/country/5`: redirected to `/partners/country/anguilla-5`. Anguilla has no partners.
- `/partners/country/egypt-64` and `/partners/country/egypt-64/page/11`: the first and last pages of Egypt.
- `/partners/roayatec-17207720` and `/partners/devoneers-32297621`: two partner pages, with 135 and 0 references.

The responses carried no `ETag` or `Last-Modified` header, so conditional requests are not available. Change detection will use content fingerprints (Stage 05).

## robots.txt (as read on 2026-11-08)

For every crawler, the file disallows, among others:

- query strings containing `country_id=`, `grade_id=`, `page=`, `search=`, `order=` or `orderby=`;
- paths of the form `*/page/*/*`.

Consequences for the module (D-25):

- Partner links that carry `?country_id=` are read from the listing pages, but never requested. Partner pages are requested by their canonical URL, without a query string.
- Country pages are requested by path, `/partners/country/<id>` and `.../page/<n>`.
- The country list comes from `/partners?country_all=1`, which no rule disallows.
- `services/urls.py` (`fetch_allowed`) encodes these rules. `services/reader.py` refuses any other URL before calling the page source.

## Page structure and the selectors used

- **Country menu.**
  - Several menus look alike. The industry menu also links to `country_all`, but its items have no counts. The category menu has counts, but no "All Countries" item.
  - So the parser takes the `div.dropdown-menu` that has both an "All Countries" item (`a[href*="country_all"]` with a `span.badge` count, 4517) and country items (`a[href^="/partners/country/"]` with a `span.badge` count).
  - The non-selected countries link to `/partners/country/<id>`; the site redirects that to the slug form.
  - There were 170 countries, and their counts add up to 4517. The parser uses this as a completeness check.
  - Countries without partners are not listed.
- **Category menu** (`#dropdown_grades_selection`). Its "All Categories" item counts the partners in the page's scope (2 for Andorra, 210 for Egypt). This is the expected count for a country snapshot.
- **Partner cards.** A card is a link to a partner page that contains the card title: `a[href] h5`.
  - The link reads `/partners/<slug>-<id>?country_id=<country id>`.
  - Name: the first non-badge `span` in the `h5`. Status: `h5 span.badge` (Gold, Silver or Ready).
  - Retention: a `small` whose text is `90 %`. It is absent for some partners.
  - Project sizes: `small.text-muted` with "Average Project: 23 users" and "Large Project: ~200 users".
  - Reference count: `div.stat_ref > div`, reading "135 References", "1 Reference" or "0 Reference".
  - Each page shows 20 cards.
- **Pager.** `ul.pagination`, with the current page in `li.active`. Links read `/partners/country/egypt-64/page/<n>`, and the last page number is shown (11 for Egypt).
- **Empty country.**
  - The page shows a `div[role="alert"]` reading "There are no matching partners found for the selected country. Displaying results across all countries instead."
  - It then lists global cards whose links have no `country_id`, under a global pager (`/partners/page/<n>`), as the PDF describes.
- **Partner page.**
  - The heading `h1#partner_name` holds the name and the status badge. The id is in `link[rel="canonical"]`.
  - `div.stat_size` reads "Largest: 200+ users", "Average: 23 users" and "Customer Retention 90 %".
  - `div.stat_ref > div` reads "References - 135".
  - The references are the `div.card` siblings after `h3#references`. Each links to `/customers/<slug>-<id>`, and its avatar URL `/web/image/res.partner/<id>/...` carries the same id.
  - RoayaTec's page listed all 135 references, with no paging. DEVONEERS (0 references) has no reference list, no count, and no retention block.

The parsers read the English labels above (D-26).

## Differences from the Odoo 18.0 module used as the working model (A-19)

- The 18.0 Community module shows 40 partners per page; the live site shows 20.
- The live cards show retention, average and largest project size, the reference count, and certified experts. The Community templates show none of these metrics.
- Live references link to `/customers/<slug>-<id>`. In the Community module, references have no link.
- The empty-country behavior is the same: a notice, then results for all countries.

## Manual parser check on the full saved pages (2026-11-08)

This was a one-off script run in the Odoo image, not an automated test. Results:

- **Country list:** 170 countries, total 4517, complete.
- **Andorra:** scope "country", 2 of 2 partners, page 1 of 1.
- **Egypt, page 1:** 20 partners, 210 expected, page 1 of 11, next page `/partners/country/egypt-64/page/2`.
- **Egypt, page 11:** 10 partners, page 11 of 11, no next page. Retention is unknown where the card shows none.
- **Anguilla:** scope "empty_country"; all 20 links rejected for "missing country_id".
- **RoayaTec:** 135 references found of 135 expected, all identified by their `/customers/` link id.
- **DEVONEERS:** no references, retention unknown, average and largest 0.

The automated tests use the trimmed fixtures instead. Their results are in [STATE.md](STATE.md) and the Stage 04 handoff.

## Stage 10: the bounded live check through the module (2026-11-15)

`scripts/pm_live_check.py`, run with `scripts/dev.sh shell azk_ee24_test`, on the disposable test database only. It reads robots.txt directly, then runs the real cron entry point (`worker._cron_process_queue`) with the real client (`services/http_client.py`), parsers and ingestion:

- batch 1: the country list;
- batch 2 (after cancelling every country unit but Andorra's): Andorra's listing, then the first partner page that unit queued.

A hard budget of 8 HTTP requests applies, and everything is rolled back at the end. Results, in order:

- **Run 1 (15:14 UTC): FAIL, nothing stored.** The robots.txt request ended with "Remote end closed connection without response". Seven single diagnostic requests followed, about 5 seconds apart (review finding RF-02). The website closes HTTP/1.1 connections that offer `Accept-Encoding: gzip, deflate`, the `requests` default, after about 15 seconds; `gzip` alone gets HTTP 200 at once. The client now offers gzip only.
- **Run 2 (15:22 UTC): PASS for what ran.**
  - robots.txt: HTTP 200, 1,627 bytes, 56 rules for every crawler, still disallowing `*?*country_id=*`, `*?*grade_id=*`, `*?*page=`, `*?*search=*`, `*?*order=`, `*?*orderby=` and `*/page/*/*`. Both planned URLs were allowed.
  - Requests: `/partners?country_all=1` (HTTP 200, 381,630 bytes, 2.21 s); `/partners/country/1` (HTTP 301 to `/partners/country/andorra-1`, 0.13 s); `/partners/country/andorra-1` (HTTP 200, 322,042 bytes, 0.43 s).
  - Stored: 170 countries, a complete list; Andorra 2 of 2 partners, complete, validation matched: BDR GROUP SLU (22015187, Ready, retention 85 %, 17 references listed) and Process Control Technology Andorra (24934006, Ready, retention 75 %, 3 references listed).
  - Found: the partner pages queued by Andorra's unit were not due in the same batch, and batch 1 reported 0 remaining with 170 units queued (RF-03, fixed).
- **Run 3 (15:25 UTC): PASS.**
  - 4 page requests plus robots.txt. Batch 1 reported 170 remaining. Batch 2 ran Andorra (2 of 2, complete, matched) and BDR GROUP SLU's page (`/partners/bdr-group-slu-22015187`, HTTP 200, 87,050 bytes, 0.23 s): 17 references found of 17 and stored.
  - Found: the unit said "mismatch". One request (with the module's headers, from the host) saved that page privately in `runtime/logs/stage10/` for offline analysis: 18 reference cards, one of them completely empty (RF-04, fixed).
- **Run 4 (16:32 UTC, final code): PASS.**
  - robots.txt HTTP 200, 1,627 bytes, the same 56 rules.
  - Batch 1: 2.69 s, the country list (170 countries, complete), 170 remaining.
  - Batch 2: 6.80 s, Andorra (2 of 2, complete, matched) and BDR GROUP SLU's page: "17 of 17 references, matched, 17 added" (RF-04 fixed).
  - 4 page requests, each allowed by robots.txt: the country list (200, 381,630 bytes, 2.06 s), `/partners/country/1` (301, 0.12 s), Andorra (200, 322,042 bytes, 0.52 s) and BDR GROUP SLU (200, 87,050 bytes, 0.44 s).
  - No error row. Rolled back: no unit of the run left.

Requests to www.odoo.com on 2026-11-15: 23 requests between 15:14 and 16:33 UTC: the four live check runs (1, 4, 5 and 5 requests, robots.txt included), 7 single diagnostic requests to robots.txt (RF-02), and 1 request that saved BDR GROUP SLU's page for offline analysis.
