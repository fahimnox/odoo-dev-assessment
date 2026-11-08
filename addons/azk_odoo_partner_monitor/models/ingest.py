import logging

from odoo import api, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PartnerMonitorIngest(models.AbstractModel):
    """Database ingestion: parsed pages -> the Stage 03 observation methods.

    No HTTP and no HTML here; the input is the typed results of
    services/parsers.py. Removals are applied only for a complete snapshot of
    exactly the scope that was read. An incomplete, unscoped or failed read
    keeps every existing record (docs/architecture.md 5.5). Called by the
    sync engine in superuser mode, like every write to the scraped data
    (D-18). Each method returns a plain summary for logs and work items.
    """

    _name = "azk_odoo_partner_monitor.ingest"
    _description = "Partner Monitor Ingestion"

    @api.model
    def _ingest_country_list(self, country_list, observed_on):
        """Record the country list. Only a complete list deactivates missing countries (P-23)."""
        Country = self.env["azk_odoo_partner_monitor.country"]
        seen = Country
        for entry in country_list.countries:
            values = {"source_key": entry.source_key, "name": entry.name}
            if entry.partner_count is not None:
                values["total_partner_count"] = entry.partner_count
            seen |= Country._record_observation(values)
        deactivated = Country
        if country_list.complete:
            # Demo records are never touched by scraped data (D-20).
            deactivated = Country.search([("is_demo", "=", False), ("id", "not in", seen.ids)])
            deactivated.write({"active": False})
        return {
            "countries": len(seen),
            "complete": country_list.complete,
            "deactivated": deactivated.ids,
            "problems": list(country_list.problems),
        }

    @api.model
    def _ingest_country_listing(self, country, pages, observed_on, country_list=None):
        """Record one country's listing snapshot: every page read for it, in order.

        - Each partner card goes through partner._record_observation, in its
          own savepoint, so one bad card does not stop the others.
        - The snapshot is complete only if every page from 1 to the last was
          read, every card was in scope and readable, nothing was listed twice,
          and the number of distinct partners equals the count the site shows
          for the country on the same pages.
        - Only a complete snapshot archives the country's partners that are no
          longer listed. "unscoped" changes nothing.
        - "empty_country" (the page shows the site's no-partners notice) is a
          valid empty snapshot only when ``country_list``, a complete country
          list read in the same run, independently confirms it: the country is
          absent from it or listed with 0 partners (D-27). Otherwise the result
          is incomplete and every existing record is kept.
        - to_reprocess_partners is set when the snapshot is incomplete (P-18)
          and cleared by a complete one.
        """
        Partner = self.env["azk_odoo_partner_monitor.partner"]
        summary = {
            "country": country.source_key,
            "scope": pages[0].scope if pages else None,
            "expected": None,
            "found": 0,
            "recorded": [],
            "archived": [],
            "rejected": [(link.raw_url, link.reason) for page in pages for link in page.rejected],
            "invalid": [(link.raw_url, link.reason) for page in pages for link in page.invalid],
            "problems": [problem for page in pages for problem in page.problems],
            "errors": [],
            "complete": False,
        }
        if not pages:
            summary["errors"].append("no page was read")
            return summary
        if pages[0].scope == "empty_country":
            listed = {entry.source_key: entry.partner_count for entry in country_list.countries} \
                if country_list is not None else {}
            confirmed = (country_list is not None and country_list.complete
                         and not listed.get(country.source_key))
            if not confirmed:
                summary["problems"].append(
                    "the no-partners notice is not confirmed by a complete country list")
                country.write({"to_reprocess_partners": True})
                return summary
            archived = Partner.search([("country_id", "=", country.id), ("is_demo", "=", False)])
            archived.write({"active": False})
            country.write({"total_partner_count": 0, "to_reprocess_partners": False})
            summary.update(expected=0, complete=True, archived=archived.ids)
            return summary
        if any(page.scope != "country" for page in pages):
            country.write({"to_reprocess_partners": True})
            return summary

        cards = {}
        for page in pages:
            for card in page.partners:
                if card.source_id in cards:
                    summary["problems"].append(f"partner {card.source_id} is on two pages")
                cards.setdefault(card.source_id, card)
        recorded = Partner
        for card in cards.values():
            try:
                with self.env.cr.savepoint():
                    recorded |= Partner._record_observation(card.observation(country.id), observed_on)
            except (ValidationError, ValueError) as exc:
                summary["errors"].append(f"{card.partner_url}: {exc}")
                _logger.warning("Partner Monitor: partner %s was not recorded: %s", card.partner_url, exc)

        expected = pages[0].listed_count
        every_page = ([page.page for page in pages] == list(range(1, len(pages) + 1))
                      and pages[-1].page == pages[-1].last_page)
        complete = (every_page and expected is not None and len(cards) == expected
                    and not summary["rejected"] and not summary["invalid"]
                    and not summary["problems"] and not summary["errors"])
        summary.update(expected=expected, found=len(cards), recorded=recorded.ids, complete=complete)
        if expected is not None and expected != country.total_partner_count:
            country.write({"total_partner_count": expected})
        if complete:
            archived = Partner.search([
                ("country_id", "=", country.id), ("is_demo", "=", False), ("id", "not in", recorded.ids)])
            archived.write({"active": False})
            summary["archived"] = archived.ids
        country.write({"to_reprocess_partners": not complete})
        return summary

    @api.model
    def _ingest_partner_page(self, partner, page, observed_on):
        """Record a partner's own page: its values, then its reference snapshot.

        The reference list is complete only when its size equals the expected
        count: the page's "References - N", or, when the page shows no count,
        the count last read on the listing. Only a complete list closes
        references (partner._sync_references); to_reprocess_references is set
        when the list is incomplete (P-20) and cleared by a complete one.
        """
        if page.source_id != partner.source_id:
            raise ValidationError(self.env._(
                "The page of partner %(page)s cannot update partner %(partner)s.",
                page=page.source_id, partner=partner.source_id))
        values = {
            "source_id": partner.source_id,
            "name": page.name,
            "current_status": page.status,
            "partner_url": page.partner_url,
        }
        # The listing card is where a missing value becomes "unknown"; the
        # partner page only adds the values it shows.
        for name in ("retention_rate", "average_project_size", "largest_project_size"):
            if getattr(page, name) is not None:
                values[name] = getattr(page, name)
        if page.expected_reference_count is not None:
            values["total_references_count"] = page.expected_reference_count
        partner._record_observation(values, observed_on)

        expected = page.expected_reference_count
        if expected is None and partner.total_references_count_known:
            expected = partner.total_references_count
        complete = expected is not None and len(page.references) == expected and not page.problems
        added, removed = partner._sync_references(
            [{"source_key": ref.source_key, "name": ref.name} for ref in page.references],
            observed_on, complete)
        partner.write({"to_reprocess_references": not complete})
        return {
            "partner": partner.source_id,
            "expected": expected,
            "found": len(page.references),
            "complete": complete,
            "added": added.ids,
            "removed": removed.ids,
            "problems": list(page.problems),
        }
