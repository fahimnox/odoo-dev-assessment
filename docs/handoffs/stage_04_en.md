# Stage 04 handoff: partner scraping layers (PARTIAL)

Date: 2026-11-08. Edition: `enterprise-20241208` (port 8071). Status: **PARTIAL**.

- **Done:** the parsing and ingestion layers, tested offline.
- **Missing:** the requests-based page-download module, and a live run through the module.

## What is implemented

- **`services/urls.py`:**
  - `check_country_scope`: the PDF's empty-country rule on the raw link, before canonicalization.
  - `canonical_partner_url`: canonical URL and website id.
  - `listing_url`, `listing_key`, `listing_page_url`: country pages and paging.
  - `reference_key`: reference identity (D-23).
  - `fetch_allowed`: the robots.txt rules (D-25).
- **`services/parsers.py`:** BeautifulSoup parsers that return typed results.
  - `parse_country_list` gives countries, counts, the total and a completeness flag.
  - `parse_listing_page` gives partner cards, rejected and invalid links, the page scope ("country", "empty_country" or "unscoped"), the site's count, and paging.
  - `parse_partner_page` gives the partner's values, the expected reference count and the references.
  - A page of the wrong kind raises `ParseError`.
- **`services/reader.py`:**
  - `read_country_list`, `read_country_listing` and `read_partner_page` pass pages from any `fetch(url)` function to the parsers.
  - They refuse URLs that robots.txt disallows, and follow the site's pager. They stop at the first page that is not this country's listing.
  - Any fetch failure propagates; it is never an empty result.
- **`models/ingest.py`** (`azk_odoo_partner_monitor.ingest`):
  - `_ingest_country_list`, `_ingest_country_listing` and `_ingest_partner_page` call the Stage 03 methods `_record_observation` and `_sync_references`.
  - Removals happen only for complete snapshots (D-27, D-28). Incomplete ones set `to_reprocess_partners` or `to_reprocess_references`, and keep every existing record.
- **Fixtures:** seven live-derived fixtures in `tests/fixtures/`, with their provenance in `tests/fixtures/README.md`.

## What is missing (why Stage 04 is PARTIAL)

1. **The page-download module.**
   - What it is: `services/http_client.py`, planned as class `PartnersHttpClient` with method `get`. It would use requests, with timeouts, limited retries and backoff, a polite delay, and FetchError kinds.
   - Its tests are missing too: mocked HTTP responses, including a successful response and a timeout.
   - Diagnostic: while the response was writing this file, the tool reported, verbatim: "Interrupted: the response that made this tool call was stopped by a safety classifier while the call was running; it may have partially or fully completed." A system notice followed. It said the response had been stopped by a safety classifier, that this was not a tool or API error, and not to produce that content again, even reworded. The file was never created.
2. **Synthetic fixtures.**
   - What they were: hand-written pages for a fake country, starting with `tests/fixtures/synthetic_listing_testland_p1.html`. They were for a complete multi-page country, `country_id` in second position, and login, rate-limit, truncated, unknown-status and duplicate pages.
   - Diagnostic: the response that was writing that first file was stopped the same way, with the same tool message. The file was never created.
3. **The live integration check.** Nothing ran against the live site through the module, because there is no page-download module. This morning's live evidence is the manual curl sample described below.

The user chose to defer both files. Without the page-download module, the reader works only with the test fakes.

## Walkthrough: one partner, from raw URL to stored observation

Partner "BDR GROUP SLU" in Andorra. Test: `test_ingest.py`, `TestIngest.test_walkthrough_raw_url_to_stored_partner`.

1. **The page.** The reader asks for `https://www.odoo.com/partners/country/1`. The site serves `https://www.odoo.com/partners/country/andorra-1` (fixture `live_listing_andorra.html`). The parser checks that this final URL is the listing of country `1`.
2. **The raw link.** The card's link is `/partners/bdr-group-slu-22015187?country_id=1`.
3. **The country check, on the raw link.** `check_country_scope(raw, "1")` finds `country_id=1`, which is the expected country, so the card is accepted.
4. **Canonical identity.** `canonical_partner_url` drops the query string. The result is `https://www.odoo.com/partners/bdr-group-slu-22015187`, with website id `22015187`.
5. **Card values.** Name "BDR GROUP SLU", status Ready, "85 %", "Average Project: 13 users", "Large Project: ~100 users", "17 References".
6. **The stored observation.** `partner._record_observation` creates the partner, because no record has website id 22015187. It stores:
   - `source_id` 22015187 and the canonical `partner_url`;
   - `current_status` ready, the country Andorra, `active` True;
   - `first_seen_on` and `last_seen_on` 2026-11-08;
   - `retention_rate` 85.0, `average_project_size` 13.0, `largest_project_size` 100 and `total_references_count` 17, each with its `_known` flag set to True.
   It also adds one status history row: type initial, no previous status, new status ready, dated 2026-11-08.
7. **The snapshot.** The page holds 2 distinct partners, and its "All Categories" count is 2, on page 1 of 1. So the snapshot is complete:
   - any other active Andorra partner would be archived (`test_complete_snapshot_archives_a_partner_no_longer_listed`);
   - `to_reprocess_partners` stays False.
   Ingesting the same page again, also on a later date, creates no duplicate partner or history row (`test_same_complete_andorra_page_twice_creates_no_duplicates`).

## One rejected URL

- **The page.** For Anguilla (country `5`), the reader asks for `https://www.odoo.com/partners/country/5`. The site serves `https://www.odoo.com/partners/country/anguilla-5` (fixture `live_listing_anguilla_fallback.html`). It shows the notice "There are no matching partners found for the selected country. Displaying results across all countries instead." Then it lists partners from all countries.
- **The rejected link.** One card's link is `/partners/adhoc-990138`. `check_country_scope(raw, "5")` returns **"missing country_id"**: the link carries no country scope. So this partner (adhoc, website id 990138) is not an Anguilla partner, and it is not recorded. All 3 links in the fixture are rejected for the same reason; on the full live page, all 20 were.
- **The country itself.** The notice alone is not proof that the country is empty (D-27):
  - Without a complete country list, the result is incomplete. Existing Anguilla partners stay active, and the country is flagged (`test_anguilla_notice_alone_is_not_enough`).
  - The live country list saved this morning is complete, and Anguilla is absent from it. With that list, the empty result is confirmed: Anguilla's partners are archived, and its count becomes 0 (`test_anguilla_confirmed_empty_by_the_country_list`).
  - An incomplete list, or a list that gives Anguilla a positive count, confirms nothing (`test_anguilla_not_confirmed_by_an_incomplete_list_or_a_listed_count`).

## Real commands and results

**Earlier today, by hand (manual checks, not automated tests):**

- **Live sample:**
  - 9 curl requests with a descriptive user agent, about 4 seconds apart, 08:01 to 08:09 UTC. They covered robots.txt, the default page, the all-countries list, Andorra, Anguilla, Egypt pages 1 and 11, and RoayaTec's and DEVONEERS's pages.
  - All returned HTTP 200; `/country/1` and `/country/5` redirected to their slug URLs. There was no ETag or Last-Modified header.
  - Details in [live_site_notes.md](../live_site_notes.md). The full pages are kept privately in `<kit-root>/runtime/logs/stage04_live/`.
- **Manual parser check:** a one-off script ran the parsers inside the Odoo image on the full saved pages. Results:
  - country list: 170 countries, total 4517, complete;
  - Andorra: 2 of 2;
  - Egypt: 20 partners on page 1 of 11, with a next-page link, and 10 on page 11 of 11;
  - Anguilla: "empty_country", with 20 links rejected for "missing country_id";
  - RoayaTec: 135 of 135 references, identified by link id;
  - DEVONEERS: no references, and retention unknown.

**Automated, after the code was finished:**

- `scripts/dev.sh test azk_odoo_partner_monitor`: **PASS**. "0 failed, 0 error(s) of 91 tests" in a fresh `azk_ee24_test`, exit code 0, 0 warnings in the whole log, 2 min 28 s. It was run again on the committed code, after one test file's Arabic letters were rewritten as `\u` escapes: 91 of 91 again, 0 warnings, 1 min 56 s.
  - That is the 53 Stage 03 tests plus 38 new offline tests:
    - `TestUrlRules`: 8;
    - `TestParsers`: 12;
    - `TestIngest`: 18.
  - The new tests read only the seven live-derived fixtures, through the reader with a fixture-backed `fetch` (`FixtureSite` in `tests/common.py`).
  - The four requested cases:
    - **Andorra:** the same complete page ingested twice creates no duplicate partners or history rows.
    - **RoayaTec:** a seeded active reference absent from the 3-of-135 list stays active, 3 references are added, and the partner is flagged (`to_reprocess_references`).
    - **Anguilla:** the links missing `country_id` are rejected. The country is empty only when the complete country list confirms it; otherwise the result is incomplete and the data is kept.
    - **Egypt:** the reader follows the pager, and a missing page 2 fails the whole read. Reading the last page alone (11 of 11), or pages 1 and 11 with a gap, is incomplete and archives nothing.
- `scripts/dev.sh update azk_odoo_partner_monitor` on `azk_ee24`: PASS, 0 warnings or errors, 1 min 15 s. The development database now has the 18.0.1.2.0 code.
- `df -h /c`: 9.4 GB free.
- **NOT RUN:**
  - the fetcher tests, because there is no fetcher;
  - a live run through the module (country list, one small country and one partner page, then a rollback);
  - a browser check.

## Cases not covered yet

- **Page download:** a successful response, a timeout, HTTP errors, 429 with Retry-After, redirects off the site, the request language, the rate policy.
- **Pages without a live sample:** login pages, rate-limit pages, truncated markup, duplicate cards, and references without a link. The image-id and name fallbacks are tested only on URL strings.
- **Not seen live:** reference lists split over several pages; a complete multi-page country (the Egypt fixtures are trimmed); a partner moving between countries through two listings (D-17); pages in another language.
- **The worker path (Stage 05):** `sync.error` rows, retries, crons, and the end-of-run notification.

## Concepts, with our files

- **A real selector.** On the live site, two menus link to `country_all`: the industry menu and the country menu. My first trimming script picked the wrong one. `_country_menu` in `parsers.py` therefore requires both an "All Countries" item with a count AND country items with counts. That is the only menu matching both, on every page we saw.
- **Raw URL versus canonical identity.** The raw link `/partners/bdr-group-slu-22015187?country_id=1` says where the card was found. The canonical URL `https://www.odoo.com/partners/bdr-group-slu-22015187` and the website id 22015187 say who the partner is. Canonicalization deletes the evidence of where, so `check_country_scope` runs first (`test_the_check_needs_the_raw_link`).
- **Valid empty versus failed parse.**
  - A valid empty result needs positive evidence. For a country: the site's notice, confirmed by a complete country list. For references: a listing that says 0 and a page without a list (DEVONEERS).
  - A failed parse means a required part is missing (`ParseError`). A failed download raises an exception. In both cases nothing is ingested and nothing is removed.
- **Why fixture tests.** They are offline and deterministic: the same saved pages give the same results every run, with no load on the website. They also preserve rare live cases, such as Anguilla's fallback page, that the site may not show again. If the site changes, re-capturing a page and rerunning the tests shows exactly which selector broke.

## Decisions taken in this stage

See [assumptions.md](../assumptions.md):

- **D-23:** a reference's identity is its link id, then its avatar id, then its name.
- **D-24:** an unknown status on a card skips that card, and makes the snapshot incomplete.
- **D-25:** robots.txt is followed.
- **D-26:** the parsers read English labels.
- **D-27:** the empty-country notice needs confirmation from a complete country list.
- **D-28:** the rules for a complete country snapshot.
- **D-29:** the listing card decides when a metric is unknown.

## Changed files

- **New:**
  - `addons/azk_odoo_partner_monitor/services/parsers.py`, `services/reader.py`, `models/ingest.py`;
  - `tests/test_urls.py`, `tests/test_parsers.py`, `tests/test_ingest.py`;
  - `tests/fixtures/` (7 files and a README);
  - `docs/live_site_notes.md`, `docs/handoffs/stage_04_en.md`, `docs/ai/stage_04.md`.
- **Updated:**
  - in the addon: `services/urls.py`, `models/__init__.py`, `tests/__init__.py`, `tests/common.py`, and `__manifest__.py` (18.0.1.2.0);
  - `docs/architecture.md` (5.1, new 5.11), `docs/assumptions.md` (A-19, V-07, D-23 to D-29);
  - `docs/requirements_matrix.md` (17 rows), `docs/test_plan.md` (3.2), `docs/STATE.md`, `docs/ai/README.md`.
- **Outside Git:**
  - `runtime/logs/stage04_live/` (raw pages);
  - `runtime/logs/stage04_*.log`;
  - `azk_ee24` (upgraded) and `azk_ee24_test` (recreated).

## Comprehension questions

1. Why must `check_country_scope` run on the raw link instead of the canonical URL?
2. Why is Anguilla's no-partners notice alone not enough to archive its partners?
3. Egypt's last page says "page 11 of 11". Why does reading it not make the Egypt snapshot complete?

## Next step

Stage 04 stays PARTIAL until the page-download module exists and one bounded live run through the module has been checked. Stage 05 (resumable sync) can build its work units on `services/reader.py` and `models/ingest.py`, but a real sync needs the page-download module.
