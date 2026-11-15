import re

from bs4 import BeautifulSoup

from odoo.tests import BaseCase, tagged

from ..services import parsers
from .common import ANDORRA, ANGUILLA, COUNTRY_LIST, DEVONEERS, EGYPT_P1, EGYPT_P11, ROAYATEC, fixture


def parse_listing(page, country_key):
    url, name = page
    return parsers.parse_listing_page(fixture(name), url, country_key)


@tagged("post_install", "-at_install")
class TestParsers(BaseCase):
    """TP-PM-06 and TP-PM-08 on the seven live-derived fixtures (no network, no database)."""

    def test_country_list(self):
        result = parsers.parse_country_list(fixture(COUNTRY_LIST[1]), COUNTRY_LIST[0])
        by_key = {country.source_key: country for country in result.countries}
        self.assertEqual(len(result.countries), 170)
        self.assertEqual(result.total_count, 4517)
        self.assertTrue(result.complete)
        self.assertEqual(result.problems, [])
        self.assertEqual(by_key["1"], parsers.Country("1", "Andorra", 2))
        self.assertEqual(by_key["64"], parsers.Country("64", "Egypt", 210))
        self.assertNotIn("5", by_key)  # Anguilla: no partners, so not listed

    def test_country_counts_must_add_up(self):
        html = fixture(COUNTRY_LIST[1])
        # A variant of the live list without its Andorra item (2 partners).
        variant = re.sub(r'<a [^>]*href="/partners/country/1">.*?</a>', "", html, count=1, flags=re.S)
        self.assertNotEqual(variant, html)
        result = parsers.parse_country_list(variant, COUNTRY_LIST[0])
        self.assertEqual(len(result.countries), 169)
        self.assertFalse(result.complete)
        self.assertIn("the country counts add up to 4515, not to the 4517 partners of all countries",
                      result.problems)

    def test_andorra_listing(self):
        page = parse_listing(ANDORRA, "1")
        self.assertEqual((page.scope, page.page, page.last_page, page.next_url, page.listed_count),
                         ("country", 1, 1, None, 2))
        self.assertEqual((page.rejected, page.invalid, page.problems), ([], [], []))
        self.assertEqual(page.partners[0], parsers.PartnerCard(
            source_id=22015187, name="BDR GROUP SLU", status="ready",
            raw_url="/partners/bdr-group-slu-22015187?country_id=1",
            partner_url="https://www.odoo.com/partners/bdr-group-slu-22015187",
            retention_rate=85.0, average_project_size=13.0, largest_project_size=100,
            total_references_count=17))
        self.assertEqual(page.partners[1].source_id, 24934006)

    def test_egypt_first_page_pagination(self):
        page = parse_listing(EGYPT_P1, "64")
        self.assertEqual((page.scope, page.page, page.last_page, page.listed_count), ("country", 1, 11, 210))
        self.assertEqual(page.next_url, "https://www.odoo.com/partners/country/egypt-64/page/2")
        self.assertEqual(len(page.partners), 3)  # the fixture keeps 3 of the 20 cards
        roayatec = page.partners[0]
        self.assertEqual((roayatec.source_id, roayatec.status, roayatec.retention_rate,
                          roayatec.average_project_size, roayatec.largest_project_size,
                          roayatec.total_references_count),
                         (17207720, "gold", 90.0, 23.0, 200, 135))

    def test_egypt_last_page_and_missing_values(self):
        page = parse_listing(EGYPT_P11, "64")
        self.assertEqual((page.scope, page.page, page.last_page, page.next_url), ("country", 11, 11, None))
        self.assertEqual(len(page.partners), 7)
        by_id = {card.source_id: card for card in page.partners}
        sharp = by_id[5912889]  # "Sharp 4 IT": the card shows no retention rate
        self.assertIsNone(sharp.retention_rate)
        self.assertEqual((sharp.average_project_size, sharp.largest_project_size,
                          sharp.total_references_count), (55.0, 100, 1))
        binntechs = by_id[26747451]  # the card shows 0 users and 0 references: known zeros
        self.assertEqual((binntechs.retention_rate, binntechs.average_project_size,
                          binntechs.largest_project_size, binntechs.total_references_count),
                         (None, 0.0, 0, 0))

    def test_anguilla_fallback_links_are_rejected(self):
        page = parse_listing(ANGUILLA, "5")
        self.assertEqual(page.scope, "empty_country")
        self.assertEqual(page.partners, [])
        self.assertEqual([link.reason for link in page.rejected], ["missing country_id"] * 3)
        self.assertEqual(page.rejected[0].raw_url, "/partners/adhoc-990138")
        self.assertEqual((page.listed_count, page.next_url), (None, None))

    def test_page_of_another_country_is_unscoped(self):
        # The Andorra page served for a request about Egypt (e.g. a wrong redirect).
        page = parse_listing(ANDORRA, "64")
        self.assertEqual(page.scope, "unscoped")
        self.assertEqual(page.partners, [])
        self.assertEqual([link.reason for link in page.rejected],
                         ["country_id 1 is not the expected country 64"] * 2)

    def test_unknown_status_is_not_ready(self):
        # A variant of the live page where RoayaTec's badge reads "Platinum".
        html = fixture(EGYPT_P1[1]).replace('bg_gold">Gold</span>', 'bg_gold">Platinum</span>', 1)
        page = parsers.parse_listing_page(html, EGYPT_P1[0], "64")
        self.assertEqual([link.raw_url for link in page.invalid], ["/partners/roayatec-17207720?country_id=64"])
        self.assertIn("unknown status 'Platinum'", page.invalid[0].reason)
        self.assertNotIn(17207720, [card.source_id for card in page.partners])
        self.assertEqual(len(page.partners), 2)

    def test_roayatec_page_and_reference_identities(self):
        page = parsers.parse_partner_page(fixture(ROAYATEC[1]), ROAYATEC[0])
        self.assertEqual((page.source_id, page.name, page.status, page.retention_rate,
                          page.average_project_size, page.largest_project_size),
                         (17207720, "RoayaTec", "gold", 90.0, 23.0, 200))
        self.assertEqual(page.expected_reference_count, 135)
        self.assertEqual([(ref.source_key, ref.name, ref.key_source) for ref in page.references], [
            ("4189486", "2H Group", "link"),
            ("22148381", "AL Fouad Pharmacies", "link"),
            ("31670917", "AROSCENT FOR FRAGRANCE S.A.E", "link"),
        ])

    def test_an_empty_card_is_not_a_reference(self):
        # Regression (Stage 10 live check): BDR GROUP SLU's live page had 18
        # cards for "References - 17", one of them completely empty. Read as
        # "a reference without a name", it made a full list look incomplete.
        soup = BeautifulSoup(fixture(ROAYATEC[1]), "html.parser")
        title = soup.select_one("h3#references")
        title.insert_after(BeautifulSoup('<div class="card mt-3 border-0">\n</div>', "html.parser"))
        page = parsers.parse_partner_page(str(soup), ROAYATEC[0])
        self.assertEqual((len(page.references), page.problems), (3, []))
        # A card with content but no name is still a problem.
        title.insert_after(BeautifulSoup('<div class="card"><div class="card-body"><p>?</p></div></div>',
                                         "html.parser"))
        page = parsers.parse_partner_page(str(soup), ROAYATEC[0])
        self.assertEqual(page.problems, ["a reference without a name"])

    def test_partner_page_without_references(self):
        page = parsers.parse_partner_page(fixture(DEVONEERS[1]), DEVONEERS[0])
        self.assertEqual((page.source_id, page.status, page.retention_rate, page.average_project_size,
                          page.largest_project_size, page.expected_reference_count, page.references),
                         (32297621, "ready", None, 0.0, 0, None, []))

    def test_wrong_page_types_are_parse_errors(self):
        with self.assertRaises(parsers.ParseError):
            parsers.parse_listing_page(fixture(ROAYATEC[1]), "https://www.odoo.com/partners/country/egypt-64", "64")
        with self.assertRaises(parsers.ParseError):
            parsers.parse_partner_page(fixture(ANDORRA[1]), ROAYATEC[0])
        with self.assertRaises(parsers.ParseError):
            parsers.parse_country_list(fixture(ROAYATEC[1]), COUNTRY_LIST[0])
        for parse in (lambda: parsers.parse_country_list("", COUNTRY_LIST[0]),
                      lambda: parsers.parse_listing_page("", ANDORRA[0], "1"),
                      lambda: parsers.parse_partner_page("", ROAYATEC[0])):
            with self.assertRaises(parsers.ParseError):
                parse()

    def test_partner_page_requested_for_another_partner(self):
        with self.assertRaises(parsers.ParseError):
            parsers.parse_partner_page(fixture(ROAYATEC[1]), "https://www.odoo.com/partners/other-partner-55")
