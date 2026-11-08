import dataclasses
from datetime import date

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged

from ..services import parsers, reader, urls
from .common import (ANDORRA, ANGUILLA, COUNTRY_LIST, DEVONEERS, EGYPT_P1, EGYPT_P11, ROAYATEC,
                     FixtureSite, fixture)

DAY = date(2026, 11, 8)


@tagged("post_install", "-at_install")
class TestIngest(TransactionCase):
    """Saved pages -> services/reader.py (fixture-backed fetch) -> parsers ->
    the ingestion model -> the Stage 03 observation methods."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Ingest = cls.env["azk_odoo_partner_monitor.ingest"]
        cls.Country = cls.env["azk_odoo_partner_monitor.country"]
        cls.Partner = cls.env["azk_odoo_partner_monitor.partner"].with_context(active_test=False)
        cls.country_list = reader.read_country_list(FixtureSite({urls.COUNTRY_LIST_URL: COUNTRY_LIST}))
        cls.Ingest._ingest_country_list(cls.country_list, DAY)
        cls.andorra = cls.Country.search([("source_key", "=", "1")])
        cls.egypt = cls.Country.search([("source_key", "=", "64")])
        # Anguilla had partners when an earlier scrape stored it; today's list no longer has it.
        cls.anguilla = cls.Country._record_observation(
            {"source_key": "5", "name": "Anguilla", "total_partner_count": 1})

    def existing_partner(self, country, source_id):
        """A partner stored by an earlier scrape, not on today's pages."""
        return self.Partner._record_observation(
            {"source_id": source_id, "name": f"Earlier partner {source_id}", "current_status": "ready",
             "country_id": country.id}, "2026-10-01")

    def read_andorra(self):
        return reader.read_country_listing(FixtureSite({urls.listing_url("1"): ANDORRA}), "1")

    # ---------------------------------------------------------------- countries

    def test_country_list_records_every_country(self):
        self.assertEqual(self.Country.search_count([("is_demo", "=", False), ("source_key", "!=", "5")]), 170)
        self.assertRecordValues(self.andorra, [{"name": "Andorra", "total_partner_count": 2, "active": True}])
        self.assertRecordValues(self.egypt, [{"name": "Egypt", "total_partner_count": 210, "active": True}])

    def test_complete_country_list_deactivates_a_missing_country(self):
        demo_before = self.Country.with_context(active_test=False).search([("is_demo", "=", True)]).read(["active"])
        summary = self.Ingest._ingest_country_list(self.country_list, DAY)
        self.assertTrue(summary["complete"])
        self.assertEqual(summary["deactivated"], self.anguilla.ids)
        self.assertFalse(self.anguilla.active)
        self.assertEqual(self.Country.with_context(active_test=False).search(
            [("is_demo", "=", True)]).read(["active"]), demo_before)

    def test_incomplete_country_list_deactivates_nothing(self):
        incomplete = dataclasses.replace(self.country_list, complete=False)
        summary = self.Ingest._ingest_country_list(incomplete, DAY)
        self.assertEqual(summary["deactivated"], [])
        self.assertTrue(self.anguilla.active)

    # ---------------------------------------------------------------- Andorra

    def test_walkthrough_raw_url_to_stored_partner(self):
        pages = self.read_andorra()
        card = pages[0].partners[0]
        # 1. The raw link from the listing, with its country scope.
        self.assertEqual(card.raw_url, "/partners/bdr-group-slu-22015187?country_id=1")
        self.assertIsNone(urls.check_country_scope(card.raw_url, "1"))
        # 2. Its canonical form and website id.
        self.assertEqual((card.partner_url, card.source_id),
                         ("https://www.odoo.com/partners/bdr-group-slu-22015187", 22015187))
        # 3. The stored observation.
        summary = self.Ingest._ingest_country_listing(self.andorra, pages, DAY)
        self.assertTrue(summary["complete"])
        partner = self.Partner.search([("source_id", "=", 22015187)])
        self.assertRecordValues(partner, [{
            "name": "BDR GROUP SLU", "partner_url": "https://www.odoo.com/partners/bdr-group-slu-22015187",
            "current_status": "ready", "country_id": self.andorra.id, "active": True,
            "first_seen_on": DAY, "last_seen_on": DAY,
            "retention_rate": 85.0, "retention_rate_known": True,
            "average_project_size": 13.0, "average_project_size_known": True,
            "largest_project_size": 100, "largest_project_size_known": True,
            "total_references_count": 17, "total_references_count_known": True,
            "to_reprocess_references": False, "is_demo": False,
        }])
        self.assertRecordValues(partner.status_history_ids, [{
            "change_type": "initial", "previous_status": False, "new_status": "ready", "change_date": DAY}])

    def test_same_complete_andorra_page_twice_creates_no_duplicates(self):
        first = self.Ingest._ingest_country_listing(self.andorra, self.read_andorra(), DAY)
        partners = self.Partner.search([("country_id", "=", self.andorra.id)])
        second = self.Ingest._ingest_country_listing(self.andorra, self.read_andorra(), DAY)
        third = self.Ingest._ingest_country_listing(self.andorra, self.read_andorra(), date(2026, 11, 9))
        self.assertTrue(first["complete"] and second["complete"] and third["complete"])
        self.assertEqual(self.Partner.search([("country_id", "=", self.andorra.id)]), partners)
        self.assertEqual(sorted(partners.mapped("source_id")), [22015187, 24934006])
        self.assertEqual(len(partners.status_history_ids), 2)  # one initial row each
        self.assertEqual(set(partners.mapped("first_seen_on")), {DAY})
        self.assertEqual(set(partners.mapped("last_seen_on")), {date(2026, 11, 9)})
        self.assertFalse(self.andorra.to_reprocess_partners)
        self.assertEqual(third["archived"], [])

    def test_complete_snapshot_archives_a_partner_no_longer_listed(self):
        gone = self.existing_partner(self.andorra, 990001)
        summary = self.Ingest._ingest_country_listing(self.andorra, self.read_andorra(), DAY)
        self.assertEqual(summary["archived"], gone.ids)
        self.assertFalse(gone.active)
        self.assertEqual(len(gone.status_history_ids), 1)  # archiving adds no history row

    def test_timeout_is_a_failed_read_not_an_empty_list(self):
        kept = self.existing_partner(self.andorra, 990002)
        site = FixtureSite({}, failures={urls.listing_url("1"): TimeoutError("read timed out")})
        with self.assertRaises(TimeoutError):
            reader.read_country_listing(site, "1")
        # Nothing was read, so nothing is ingested: the stored data stays as it was.
        self.assertTrue(kept.active)
        self.assertFalse(self.Partner.search([("source_id", "in", [22015187, 24934006])]))
        self.assertFalse(self.andorra.to_reprocess_partners)

    # ---------------------------------------------------------------- Anguilla

    def read_anguilla(self):
        site = FixtureSite({urls.listing_url("5"): ANGUILLA})
        pages = reader.read_country_listing(site, "5")
        self.assertEqual(site.requested, [urls.listing_url("5")])  # the global pager is not followed
        return pages

    def test_anguilla_notice_alone_is_not_enough(self):
        kept = self.existing_partner(self.anguilla, 990003)
        pages = self.read_anguilla()
        self.assertEqual(pages[0].scope, "empty_country")
        self.assertEqual([link.reason for link in pages[0].rejected], ["missing country_id"] * 3)
        summary = self.Ingest._ingest_country_listing(self.anguilla, pages, DAY)
        self.assertFalse(summary["complete"])
        self.assertIn("the no-partners notice is not confirmed by a complete country list", summary["problems"])
        self.assertTrue(kept.active)
        self.assertTrue(self.anguilla.to_reprocess_partners)
        self.assertEqual(self.anguilla.total_partner_count, 1)
        # None of the global partners shown on the page was recorded.
        self.assertFalse(self.Partner.search([("source_id", "in", [990138, 4155, 732280])]))

    def test_anguilla_confirmed_empty_by_the_country_list(self):
        gone = self.existing_partner(self.anguilla, 990004)
        summary = self.Ingest._ingest_country_listing(self.anguilla, self.read_anguilla(), DAY,
                                                      country_list=self.country_list)
        self.assertTrue(summary["complete"])
        self.assertEqual(summary["archived"], gone.ids)
        self.assertFalse(gone.active)
        self.assertEqual(self.anguilla.total_partner_count, 0)
        self.assertFalse(self.anguilla.to_reprocess_partners)

    def test_anguilla_not_confirmed_by_an_incomplete_list_or_a_listed_count(self):
        kept = self.existing_partner(self.anguilla, 990005)
        incomplete = dataclasses.replace(self.country_list, complete=False)
        listed = dataclasses.replace(
            self.country_list, countries=[*self.country_list.countries, parsers.Country("5", "Anguilla", 3)])
        for country_list in (incomplete, listed):
            with self.subTest(complete=country_list.complete):
                summary = self.Ingest._ingest_country_listing(self.anguilla, self.read_anguilla(), DAY,
                                                              country_list=country_list)
                self.assertFalse(summary["complete"])
                self.assertTrue(kept.active)

    # ---------------------------------------------------------------- Egypt

    def test_egypt_pagination_is_followed_and_a_missing_page_fails_the_read(self):
        site = FixtureSite({urls.listing_url("64"): EGYPT_P1, EGYPT_P11[0]: EGYPT_P11})
        with self.assertRaises(LookupError):
            reader.read_country_listing(site, "64")
        self.assertEqual(site.requested, [urls.listing_url("64"),
                                          "https://www.odoo.com/partners/country/egypt-64/page/2"])
        self.assertFalse(self.Partner.search([("country_id", "=", self.egypt.id)]))

    def test_egypt_last_page_alone_is_not_a_complete_snapshot(self):
        kept = self.existing_partner(self.egypt, 990006)
        last = parsers.parse_listing_page(fixture(EGYPT_P11[1]), EGYPT_P11[0], "64")
        self.assertEqual((last.page, last.last_page, last.next_url), (11, 11, None))
        summary = self.Ingest._ingest_country_listing(self.egypt, [last], DAY)
        self.assertEqual((summary["complete"], summary["expected"], summary["found"]), (False, 210, 7))
        self.assertEqual(summary["archived"], [])
        self.assertTrue(kept.active)
        self.assertTrue(self.egypt.to_reprocess_partners)
        sharp = self.Partner.search([("source_id", "=", 5912889)])
        self.assertRecordValues(sharp, [{"retention_rate": 0.0, "retention_rate_known": False,
                                         "average_project_size": 55.0, "average_project_size_known": True}])

    def test_egypt_first_and_last_pages_with_a_gap_are_incomplete(self):
        kept = self.existing_partner(self.egypt, 990007)
        pages = [parsers.parse_listing_page(fixture(name), url, "64") for url, name in (EGYPT_P1, EGYPT_P11)]
        summary = self.Ingest._ingest_country_listing(self.egypt, pages, DAY)
        self.assertEqual((summary["complete"], summary["found"]), (False, 10))
        self.assertTrue(kept.active)
        self.assertTrue(self.egypt.to_reprocess_partners)

    def test_page_of_another_country_changes_nothing(self):
        kept = self.existing_partner(self.egypt, 990008)
        site = FixtureSite({urls.listing_url("64"): ANDORRA})  # a wrong page for Egypt
        pages = reader.read_country_listing(site, "64")
        summary = self.Ingest._ingest_country_listing(self.egypt, pages, DAY)
        self.assertEqual((summary["scope"], summary["complete"], summary["recorded"]), ("unscoped", False, []))
        self.assertFalse(self.Partner.search([("source_id", "in", [22015187, 24934006])]))
        self.assertTrue(kept.active)
        self.assertTrue(self.egypt.to_reprocess_partners)

    def test_unknown_status_card_is_not_recorded_as_ready(self):
        html = fixture(EGYPT_P1[1]).replace('bg_gold">Gold</span>', 'bg_gold">Platinum</span>', 1)
        site = FixtureSite({urls.listing_url("64"): EGYPT_P1}, html={urls.listing_url("64"): html})
        page = parsers.parse_listing_page(site(urls.listing_url("64"))[1], EGYPT_P1[0], "64")
        summary = self.Ingest._ingest_country_listing(self.egypt, [page], DAY)
        self.assertFalse(summary["complete"])
        self.assertEqual(len(summary["invalid"]), 1)
        self.assertFalse(self.Partner.search([("source_id", "=", 17207720)]))
        self.assertEqual(len(summary["recorded"]), 2)

    # ---------------------------------------------------------------- partner pages

    def roayatec(self):
        page1 = parsers.parse_listing_page(fixture(EGYPT_P1[1]), EGYPT_P1[0], "64")
        self.Ingest._ingest_country_listing(self.egypt, [page1], DAY)
        return self.Partner.search([("source_id", "=", 17207720)])

    def test_roayatec_incomplete_reference_list_keeps_existing_references(self):
        partner = self.roayatec()
        seeded, _removed = partner._sync_references(
            [{"source_key": "999001", "name": "Client seen in an earlier scrape"}], "2026-11-01", complete=False)
        page = reader.read_partner_page(FixtureSite({ROAYATEC[0]: ROAYATEC}), partner.partner_url)
        summary = self.Ingest._ingest_partner_page(partner, page, DAY)
        self.assertEqual((summary["complete"], summary["expected"], summary["found"]), (False, 135, 3))
        self.assertEqual((len(summary["added"]), summary["removed"]), (3, []))
        self.assertRecordValues(seeded, [{"is_active": True, "removed_on": False}])
        self.assertTrue(partner.to_reprocess_references)
        self.assertEqual(len(partner.reference_ids.filtered("is_active")), 4)
        self.assertEqual(sorted(partner.reference_ids.mapped("source_key")),
                         ["22148381", "31670917", "4189486", "999001"])

    def test_partner_without_references_is_a_valid_empty_list(self):
        last = parsers.parse_listing_page(fixture(EGYPT_P11[1]), EGYPT_P11[0], "64")
        self.Ingest._ingest_country_listing(self.egypt, [last], DAY)
        partner = self.Partner.search([("source_id", "=", 32297621)])
        self.assertRecordValues(partner, [{"total_references_count": 0, "total_references_count_known": True}])
        old, _removed = partner._sync_references(
            [{"source_key": "999002", "name": "Client seen in an earlier scrape"}], "2026-11-01", complete=False)
        page = reader.read_partner_page(FixtureSite({DEVONEERS[0]: DEVONEERS}), partner.partner_url)
        summary = self.Ingest._ingest_partner_page(partner, page, DAY)
        # The page shows no reference list; the listing's known 0 makes the empty list complete.
        self.assertEqual((summary["complete"], summary["expected"], summary["removed"]), (True, 0, old.ids))
        self.assertRecordValues(old, [{"is_active": False, "removed_on": DAY}])
        self.assertFalse(partner.to_reprocess_references)
        self.assertRecordValues(partner, [{"retention_rate_known": False}])

    def test_page_of_another_partner_is_refused(self):
        partner = self.roayatec()
        other = self.existing_partner(self.egypt, 990009)
        page = parsers.parse_partner_page(fixture(ROAYATEC[1]), ROAYATEC[0])
        with self.assertRaises(ValidationError):
            self.Ingest._ingest_partner_page(other, page, DAY)
        self.assertFalse(other.reference_ids)
        self.assertFalse(partner.reference_ids)
