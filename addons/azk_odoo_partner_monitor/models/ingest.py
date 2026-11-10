import logging

from odoo import api, fields, models
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

    ``observed_on`` is the date recorded on the data (first seen, history,
    references); ``now`` is the time recorded on the validation bookkeeping.
    Both default to the current UTC time.
    """

    _name = "azk_odoo_partner_monitor.ingest"
    _description = "Partner Monitor Ingestion"

    @api.model
    def _ingest_country_list(self, country_list, observed_on, now=None):
        """Record the country list. Only a complete list deactivates missing countries (P-23).

        A country absent from a complete list has no partners on the website,
        so its partners are archived too (docs/architecture.md 5.5). A partner
        that moved to another country is reactivated when that country's
        listing shows it.
        """
        Country = self.env["azk_odoo_partner_monitor.country"]
        seen = Country
        for entry in country_list.countries:
            values = {"source_key": entry.source_key, "name": entry.name}
            if entry.partner_count is not None:
                values["total_partner_count"] = entry.partner_count
            seen |= Country._record_observation(values)
        deactivated = Country
        archived = self.env["azk_odoo_partner_monitor.partner"]
        if country_list.complete:
            # Demo records are never touched by scraped data (D-20).
            deactivated = Country.search([("is_demo", "=", False), ("id", "not in", seen.ids)])
            deactivated.write({"active": False})
            archived = archived.search([("country_id", "in", deactivated.ids), ("is_demo", "=", False)])
            archived.write({"active": False})
        return {
            "countries": len(seen),
            "complete": country_list.complete,
            "deactivated": deactivated.ids,
            "archived": archived.ids,
            "problems": list(country_list.problems),
        }

    @api.model
    def _ingest_country_listing(self, country, pages, observed_on, country_list=None, now=None):
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
          list, independently confirms it: the country is absent from it or
          listed with 0 partners (D-27). Otherwise the result is incomplete and
          every existing record is kept.
        - The outcome is stored on the country (P-18): the expected count read
          on the pages, the partners found, the previous count, and matched or
          mismatch; a mismatch sets to_reprocess_partners, a match clears it.
        """
        now = now or fields.Datetime.now()
        Partner = self.env["azk_odoo_partner_monitor.partner"]
        summary = {
            "country": country.source_key,
            "scope": pages[0].scope if pages else None,
            "expected": None,
            "found": 0,
            "recorded": [],
            "archived": [],
            "unread": [],
            "changed": [],
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
                country._record_validation(False, 0, now)
                return summary
            archived = Partner.search([("country_id", "=", country.id), ("is_demo", "=", False)])
            archived.write({"active": False})
            country._set_listed_count(0)
            country._record_validation(True, 0, now)
            summary.update(expected=0, complete=True, archived=archived.ids)
            return summary
        if any(page.scope != "country" for page in pages):
            country._record_validation(False, 0, now)
            return summary

        cards = {}
        for page in pages:
            for card in page.partners:
                if card.source_id in cards:
                    summary["problems"].append(f"partner {card.source_id} is on two pages")
                cards.setdefault(card.source_id, card)
        recorded = unread = changed = Partner
        for card in cards.values():
            try:
                with self.env.cr.savepoint():
                    partner, never_read, card_changed = self._observe_card(card, country, observed_on, now)
            except (ValidationError, ValueError) as exc:
                summary["errors"].append(f"{card.partner_url}: {exc}")
                _logger.warning("Partner Monitor: partner %s was not recorded: %s", card.partner_url, exc)
                continue
            recorded |= partner
            if never_read:
                unread |= partner
            if card_changed:
                changed |= partner

        expected = pages[0].listed_count
        every_page = ([page.page for page in pages] == list(range(1, len(pages) + 1))
                      and pages[-1].page == pages[-1].last_page)
        complete = (every_page and expected is not None and len(cards) == expected
                    and not summary["rejected"] and not summary["invalid"]
                    and not summary["problems"] and not summary["errors"])
        summary.update(expected=expected, found=len(cards), recorded=recorded.ids,
                       unread=unread.ids, changed=changed.ids, complete=complete)
        country._set_listed_count(expected)
        if complete:
            archived = Partner.search([
                ("country_id", "=", country.id), ("is_demo", "=", False), ("id", "not in", recorded.ids)])
            archived.write({"active": False})
            summary["archived"] = archived.ids
        country._record_validation(complete, len(cards), now)
        return summary

    @api.model
    def _observe_card(self, card, country, observed_on, now):
        """Record one listing card, then apply the details-refresh policy (P-20.3, D-31).

        Returns (partner, never_read, card_changed):
        - never_read: the partner's own page was never read; the worker
          queues it in the same run (first contact, not a mismatch);
        - card_changed: the page was read before and the card's metrics hash
          (retention rate, average and largest project size, reference count;
          PartnerCard.metrics_fingerprint) differs from the last listing read.
          This sets to_reprocess_references, and the reference-validation job
          re-reads the page.
        Only listing cards are compared with listing cards. Reading the partner
        page never changes the stored hash, so a refresh cannot trigger
        another refresh. A first hash (none stored yet) is only recorded.
        """
        partner = self.env["azk_odoo_partner_monitor.partner"]._record_observation(
            card.observation(country.id), observed_on)
        if partner.last_seen_on != fields.Date.to_date(observed_on):
            return partner, False, False  # an older observation was ignored (D-21)
        fingerprint = card.metrics_fingerprint()
        previous = partner.listing_fingerprint
        card_changed = bool(previous) and previous != fingerprint and bool(partner.details_synced_at)
        if previous != fingerprint:
            partner.listing_fingerprint = fingerprint
        if card_changed:
            partner._request_details_refresh(now)
        return partner, not partner.details_synced_at, card_changed

    @api.model
    def _ingest_partner_page(self, partner, page, observed_on, now=None):
        """Record a partner's own page: its values, then its reference snapshot.

        The reference list is complete only when its size equals the expected
        count: the page's "References - N", or, when the page shows no count,
        the count last read on the listing. Only a complete list closes
        references (partner._sync_references). The outcome is stored on the
        partner (P-20): matched only when the list is complete AND the active
        references stored equal the expected count; a mismatch sets
        to_reprocess_references, a match clears it.
        """
        now = now or fields.Datetime.now()
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
        matched = complete and partner.active_reference_count == expected
        partner._record_reference_validation(matched, len(page.references), now)
        return {
            "partner": partner.source_id,
            "expected": expected,
            "found": len(page.references),
            "active": partner.active_reference_count,
            "complete": complete,
            "matched": matched,
            "added": added.ids,
            "removed": removed.ids,
            "problems": list(page.problems),
        }
