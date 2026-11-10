"""Server side of the Partner Monitor dashboard (docs/architecture.md 5.8 and 5.13).

The client action (static/src/dashboard/) sends filter VALUES, never a domain.
This model validates them, builds the one shared domain, ranks the countries
with grouped ORM queries as the calling user, and returns the cohorts, the
domains of the four embedded graph views, the summary numbers and the sync
state. The graph views then read the same records through the same domains,
so a chart and its summary cannot disagree.
"""

from odoo import api, fields, models

from .common import (MANAGER_GROUP, PROJECT_SIZE_BUCKETS, STATUS_SELECTION, ensure_reader)

COHORT_SIZE = 5
# Shown from the highest status down: Gold, Silver, Ready.
STATUS_CHOICES = list(reversed(STATUS_SELECTION))
STATUS_KEYS = [key for key, _label in STATUS_CHOICES]
GRAPH_VIEWS = {
    "top_status": "azk_odoo_partner_monitor.partner_view_graph_dashboard_top",
    "bottom_status": "azk_odoo_partner_monitor.partner_view_graph_dashboard_bottom",
    "top_size": "azk_odoo_partner_monitor.partner_view_graph_dashboard_top_size",
    "bottom_size": "azk_odoo_partner_monitor.partner_view_graph_dashboard_bottom_size",
}


class PartnerMonitorDashboard(models.AbstractModel):
    _name = "azk_odoo_partner_monitor.dashboard"
    _description = "Partner Monitor Dashboard"

    # ------------------------------------------------------------------
    # Public entry point (called by the client action)
    # ------------------------------------------------------------------

    @api.model
    def get_dashboard_data(self, filters=None):
        """Everything the dashboard shows, computed for the calling user.

        ``filters`` may hold ``statuses`` ('gold', 'silver', 'ready'),
        ``country_ids``, ``years`` (years first seen) and ``source``
        ('website' or 'demo'). Unknown keys and invalid values are dropped;
        empty means all. Ranking (decision D-06):
        - active partners of active countries, after all three filters;
        - only countries with at least one matching partner take part;
        - Top 5: most partners first; Bottom 5: fewest first; ties by
          country name, then id (the country model's order, as in the
          graph views);
        - with fewer than 10 ranked countries the two cohorts can overlap.
        """
        ensure_reader(self.env)
        filters = filters if isinstance(filters, dict) else {}
        source, sources = self._data_source(filters.get("source"))
        options = self._filter_options(source)
        applied = self._clean_filters(filters, options)
        domain = self._filtered_domain(source, applied)

        Partner = self.env["azk_odoo_partner_monitor.partner"]
        top_counts = Partner._read_group(domain, ["country_id"], ["__count"], order="__count desc, country_id")
        bottom_counts = Partner._read_group(domain, ["country_id"], ["__count"], order="__count asc, country_id")
        by_status = {(country.id, status): count for country, status, count in Partner._read_group(
            domain, ["country_id", "current_status"], ["__count"])}
        ranked = len(top_counts)
        total = sum(count for _country, count in top_counts)
        return {
            "source": source,
            "sources": sources,
            "options": options,
            "filters": applied,
            "domain": [list(term) for term in domain],
            "total": total,
            "ranked_countries": ranked,
            "empty": total == 0,
            "overlap": 0 < ranked < 2 * COHORT_SIZE,
            "few": 0 < ranked < COHORT_SIZE,
            "top": self._cohort(top_counts[:COHORT_SIZE], domain, by_status),
            "bottom": self._cohort(bottom_counts[:COHORT_SIZE], domain, by_status),
            "views": {key: self.env.ref(xmlid).id for key, xmlid in GRAPH_VIEWS.items()},
            "buckets": [{"key": key, "label": label} for key, label in PROJECT_SIZE_BUCKETS],
            "statuses": [{"key": key, "label": label} for key, label in STATUS_CHOICES],
            "sync": self._sync_state(),
            "is_manager": self.env.user.has_group(MANAGER_GROUP),
        }

    # ------------------------------------------------------------------
    # Filters and domain
    # ------------------------------------------------------------------

    @api.model
    def _population_domain(self, source):
        """Active partners of active countries, of one data source."""
        return [("active", "=", True), ("country_id.active", "=", True),
                ("is_demo", "=", source == "demo")]

    @api.model
    def _data_source(self, requested):
        """Website data unless asked otherwise, or unless only demo data exists.

        Demo records are never mixed with website data: the dashboard shows
        one source at a time and says which.
        """
        Partner = self.env["azk_odoo_partner_monitor.partner"]
        sources = {name: Partner.search_count(self._population_domain(name)) for name in ("website", "demo")}
        if requested in sources:
            return requested, sources
        return ("website" if sources["website"] or not sources["demo"] else "demo"), sources

    @api.model
    def _filter_options(self, source):
        """The values the filters offer: countries and years present in this source."""
        Partner = self.env["azk_odoo_partner_monitor.partner"]
        population = self._population_domain(source)
        countries = Partner._read_group(population, ["country_id"], order="country_id")
        years = Partner._read_group(population, ["first_seen_year"], order="first_seen_year desc")
        return {
            "statuses": STATUS_KEYS,
            "countries": [{"id": country.id, "name": country.name} for (country,) in countries],
            "years": [year for (year,) in years if year],
        }

    @api.model
    def _clean_filters(self, filters, options):
        """Keep only known values, in a stable order; anything else is dropped."""

        def wanted(key, cast):
            values = filters.get(key) or []
            if not isinstance(values, (list, tuple)):
                return set()
            result = set()
            for value in values:
                try:
                    result.add(cast(value))
                except (TypeError, ValueError):
                    continue
            return result

        statuses = wanted("statuses", str)
        country_ids = wanted("country_ids", int)
        years = wanted("years", int)
        return {
            "statuses": [key for key in options["statuses"] if key in statuses],
            "country_ids": [country["id"] for country in options["countries"] if country["id"] in country_ids],
            "years": [year for year in options["years"] if year in years],
        }

    @api.model
    def _filtered_domain(self, source, applied):
        domain = self._population_domain(source)
        if applied["statuses"]:
            domain.append(("current_status", "in", applied["statuses"]))
        if applied["country_ids"]:
            domain.append(("country_id", "in", applied["country_ids"]))
        if applied["years"]:
            domain.append(("first_seen_year", "in", applied["years"]))
        return domain

    # ------------------------------------------------------------------
    # Cohorts and sync state
    # ------------------------------------------------------------------

    @api.model
    def _cohort(self, counts, domain, by_status):
        """One cohort: its ranked rows, its chart domain and its project-size distribution."""
        Partner = self.env["azk_odoo_partner_monitor.partner"]
        country_ids = [country.id for country, _count in counts]
        cohort_domain = domain + [("country_id", "in", country_ids)]
        buckets = dict(Partner._read_group(cohort_domain, ["project_size_bucket"], ["__count"])) \
            if country_ids else {}
        rows = []
        for rank, (country, count) in enumerate(counts, start=1):
            row = {"rank": rank, "country_id": country.id, "country": country.name, "total": count}
            row.update({status: by_status.get((country.id, status), 0) for status in STATUS_KEYS})
            rows.append(row)
        return {
            "rows": rows,
            "country_ids": country_ids,
            "domain": [list(term) if isinstance(term, tuple) else term for term in cohort_domain],
            "total": sum(row["total"] for row in rows),
            "buckets": [{"key": key, "label": label, "count": buckets.get(key, 0)}
                        for key, label in PROJECT_SIZE_BUCKETS],
        }

    @api.model
    def _sync_state(self):
        """The real state of the sync: last run, last success, waiting, and (for managers) the queue."""
        Run = self.env["azk_odoo_partner_monitor.sync.run"]
        states = dict(Run._fields["state"]._description_selection(self.env))
        last = Run.search([], limit=1)
        success = Run.search([("state", "=", "done")], order="finished_at desc, id desc", limit=1)
        waiting = Run.search([("state", "=", "running"), ("waiting_reason", "!=", False)], limit=1)
        state = {
            "last_run": {
                "id": last.id,
                "name": last.display_name,
                "state": last.state,
                "state_label": states.get(last.state, ""),
                "started_at": fields.Datetime.to_string(last.started_at),
                "finished_at": fields.Datetime.to_string(last.finished_at) if last.finished_at else False,
            } if last else False,
            "last_success_at": fields.Datetime.to_string(success.finished_at) if success.finished_at else False,
            "waiting_reason": waiting.waiting_reason or "",
            "waiting_run_id": waiting.id or False,
            "queue": False,
        }
        if self.env.user.has_group(MANAGER_GROUP):
            WorkItem = self.env["azk_odoo_partner_monitor.work.item"]
            counts = dict(WorkItem._read_group([("state", "in", ("pending", "failed"))], ["state"], ["__count"]))
            state["queue"] = {
                "pending": counts.get("pending", 0),
                "retrying": WorkItem.search_count([("state", "=", "pending"), ("attempt_count", ">", 0)]),
                "failed": counts.get("failed", 0),
                "flagged_countries": self.env["azk_odoo_partner_monitor.country"].search_count(
                    [("to_reprocess_partners", "=", True), ("is_demo", "=", False)]),
                "flagged_partners": self.env["azk_odoo_partner_monitor.partner"].search_count(
                    [("to_reprocess_references", "=", True), ("is_demo", "=", False)]),
            }
        return state
