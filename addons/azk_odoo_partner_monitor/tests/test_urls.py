from odoo.tests import BaseCase, tagged

from ..services import urls


@tagged("post_install", "-at_install")
class TestUrlRules(BaseCase):
    """The empty-country safeguard and URL identities (TP-PM-08), on plain strings."""

    def test_country_id_is_checked_in_any_position(self):
        for raw in ("/partners/acme-12?country_id=64",
                    "/partners/acme-12?grade_id=1&country_id=64",
                    "https://www.odoo.com/partners/acme-12?country_id=64#top"):
            with self.subTest(raw=raw):
                self.assertIsNone(urls.check_country_scope(raw, "64"))

    def test_missing_wrong_empty_or_repeated_country_id_is_rejected(self):
        cases = {
            "/partners/acme-12": "missing country_id",
            "/partners/acme-12?grade_id=1": "missing country_id",
            "/partners/acme-12?country_id=1": "country_id 1 is not the expected country 64",
            "/partners/acme-12?country_id=": "invalid country_id ''",
            "/partners/acme-12?country_id=64&country_id=1": "several country_id values ['1', '64']",
        }
        for raw, reason in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(urls.check_country_scope(raw, "64"), reason)

    def test_the_check_needs_the_raw_link(self):
        raw = "/partners/acme-12?country_id=64"
        canonical, _source_id = urls.canonical_partner_url(raw)
        self.assertIsNone(urls.check_country_scope(raw, "64"))
        # After canonicalization the evidence is gone: check first, then canonicalize.
        self.assertEqual(urls.check_country_scope(canonical, "64"), "missing country_id")

    def test_canonical_partner_url(self):
        expected = ("https://www.odoo.com/partners/acme-solutions-12", 12)
        for raw in ("/partners/acme-solutions-12?country_id=64",
                    "https://www.odoo.com/partners/acme-solutions-12",
                    "http://www.odoo.com/partners/acme-solutions-12/",
                    "/fr_FR/partners/acme-solutions-12?grade_id=2"):
            with self.subTest(raw=raw):
                self.assertEqual(urls.canonical_partner_url(raw), expected)
        # A real slug with Arabic letters (escaped here to keep the file ASCII).
        url, source_id = urls.canonical_partner_url(
            "/partners/the-egyptian-developers-\u0627\u0644\u0645\u0637\u0648\u0631\u0648\u0646-19980114")
        self.assertEqual(source_id, 19980114)
        self.assertTrue(urls.is_canonical_partner_url(url, source_id))
        self.assertTrue(urls.is_canonical_partner_url(*expected))

    def test_other_links_are_not_partner_pages(self):
        for raw in ("/partners/country/egypt-64", "/partners/grade/1", "/partners/page/2",
                    "/customers/2h-group-4189486", "https://example.com/partners/acme-12", "/partners"):
            with self.subTest(raw=raw), self.assertRaises(urls.UrlError):
                urls.canonical_partner_url(raw)

    def test_listing_urls(self):
        self.assertEqual(urls.listing_url("64"), "https://www.odoo.com/partners/country/64")
        self.assertEqual(urls.listing_url("64", 2), "https://www.odoo.com/partners/country/64/page/2")
        self.assertEqual(urls.listing_key("/partners/country/egypt-64/page/11"), ("64", 11))
        self.assertEqual(urls.listing_key("https://www.odoo.com/partners/country/1"), ("1", 1))
        self.assertIsNone(urls.listing_key("/partners/page/2"))
        self.assertIsNone(urls.listing_key("/partners/grade/1/country/egypt-64"))
        self.assertEqual(urls.listing_page_url("https://www.odoo.com/partners/country/egypt-64/page/3", 4),
                         "https://www.odoo.com/partners/country/egypt-64/page/4")

    def test_reference_keys_prefer_site_ids(self):
        image = "https://odoocdn.com/web/image/res.partner/4189486/avatar_128/2H%20Group?unique=1"
        self.assertEqual(urls.reference_key("/customers/2h-group-4189486", image, "2H Group"), ("4189486", "link"))
        self.assertEqual(urls.reference_key(None, image, "2H Group"), ("4189486", "image"))
        self.assertEqual(urls.reference_key(None, None, "  2H   Group "), ("name:2h group", "name"))
        # Same name, different ids: two different references, never merged.
        self.assertNotEqual(urls.reference_key("/customers/acme-1", None, "Acme"),
                            urls.reference_key("/customers/acme-2", None, "Acme"))
        with self.assertRaises(urls.UrlError):
            urls.reference_key(None, None, " ")

    def test_robots_rules(self):
        for url in ("https://www.odoo.com/partners?country_all=1",
                    "https://www.odoo.com/partners/country/64",
                    "https://www.odoo.com/partners/country/egypt-64/page/2",
                    "https://www.odoo.com/partners/roayatec-17207720"):
            with self.subTest(url=url):
                self.assertIsNone(urls.fetch_allowed(url))
        for url in ("https://www.odoo.com/partners/roayatec-17207720?country_id=64",
                    "https://www.odoo.com/partners?grade_id=1",
                    "https://www.odoo.com/partners?page=2",
                    "https://www.odoo.com/partners/page/2/x",
                    "http://www.odoo.com/partners",
                    "https://example.com/partners"):
            with self.subTest(url=url):
                self.assertIsNotNone(urls.fetch_allowed(url))
