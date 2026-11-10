import os
from datetime import datetime

from odoo.exceptions import AccessError
from odoo.tests import new_test_user, tagged

from ..models.common import PROJECT_SIZE_BUCKETS, project_size_bucket
from .common import MANAGER, READER, PartnerMonitorCase

STATUSES = ("gold", "silver", "ready")


@tagged("post_install", "-at_install")
class TestDashboard(PartnerMonitorCase):
    """TP-PM-18 and TP-PM-19: the dashboard's server side (models/dashboard.py).

    The tests build their own website data (positive ids), so they do not
    depend on the demo data, which the dashboard keeps in a separate source.
    Expected ranking of the website data below, with no filter:
    Andes 4, Baltic 4, Caspian 3, Delta 2, Euphrates 1. Fjord is in an
    inactive country, Ganges has no partner, and Delta's Gold partner is
    archived.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Dashboard = cls.env["azk_odoo_partner_monitor.dashboard"]
        cls.reader = new_test_user(cls.env, login="pm_dashboard_reader", groups=READER)
        cls.manager = new_test_user(cls.env, login="pm_dashboard_manager", groups=MANAGER)
        cls.employee = new_test_user(cls.env, login="pm_dashboard_employee", groups="base.group_user")
        cls.next_id = 7000
        cls.countries = {}
        for key, name in (("a", "Andes"), ("b", "Baltic"), ("c", "Caspian"), ("d", "Delta"),
                          ("e", "Euphrates"), ("f", "Fjord"), ("g", "Ganges")):
            cls.countries[key] = cls.Country._record_observation({"source_key": f"77{key}", "name": name})
        cls.add("a", "gold", 2025, 2)
        cls.add("a", "silver", 2024)
        cls.add("a", "ready", 2026)
        cls.add("b", "gold", 2025)
        cls.add("b", "silver", 2025, 2)
        cls.add("b", "ready", 2024)
        cls.add("c", "gold", 2024)
        cls.add("c", "ready", 2025, 2)
        cls.add("d", "silver", 2026)
        cls.add("d", "ready", 2026)
        cls.add("d", "gold", 2025).write({"active": False})  # archived: never counted
        cls.add("e", "gold", 2025)
        cls.add("f", "gold", 2025, 3)
        cls.countries["f"].write({"active": False})  # inactive country: never counted

    @classmethod
    def add(cls, key, status, year, count=1, average=12.0):
        partners = cls.Partner
        for _index in range(count):
            cls.next_id += 1
            partners |= cls.Partner._record_observation({
                "source_id": cls.next_id, "name": f"Website partner {cls.next_id}",
                "current_status": status, "country_id": cls.countries[key].id,
                "average_project_size": average}, f"{year}-03-02")
        return partners

    def data(self, user=None, **filters):
        dashboard = self.Dashboard.with_user(user) if user else self.Dashboard
        return dashboard.get_dashboard_data({"source": "website", **filters})

    def ids(self, *keys):
        return [self.countries[key].id for key in keys]

    @staticmethod
    def ranking(cohort):
        return [(row["country"], row["total"]) for row in cohort["rows"]]

    # ---------------------------------------------------------------- ranking

    def test_ranking_without_filters_and_tie_order(self):
        data = self.data()
        self.assertEqual(self.ranking(data["top"]),
                         [("Andes", 4), ("Baltic", 4), ("Caspian", 3), ("Delta", 2), ("Euphrates", 1)])
        self.assertEqual(self.ranking(data["bottom"]),
                         [("Euphrates", 1), ("Delta", 2), ("Caspian", 3), ("Andes", 4), ("Baltic", 4)])
        self.assertEqual((data["total"], data["ranked_countries"]), (14, 5))
        self.assertEqual((data["few"], data["overlap"], data["empty"]), (False, True, False))
        # Andes and Baltic tie at 4: the country name decides, as in the graph
        # views, which keep the grouped query's country order for equal totals.
        groups = self.Partner.read_group(data["top"]["domain"], [], ["country_id"])
        self.assertEqual([group["country_id"][1] for group in groups][:2], ["Andes", "Baltic"])

    def test_filters_apply_before_ranking(self):
        gold = self.data(statuses=["gold"])
        self.assertEqual(self.ranking(gold["top"]),
                         [("Andes", 2), ("Baltic", 1), ("Caspian", 1), ("Euphrates", 1)])
        self.assertEqual(self.ranking(gold["bottom"]),
                         [("Baltic", 1), ("Caspian", 1), ("Euphrates", 1), ("Andes", 2)])
        self.assertTrue(gold["few"])
        gold_2025 = self.data(statuses=["gold"], years=[2025])
        self.assertEqual(self.ranking(gold_2025["top"]), [("Andes", 2), ("Baltic", 1), ("Euphrates", 1)])
        year_2026 = self.data(years=[2026])
        self.assertEqual(self.ranking(year_2026["top"]), [("Delta", 2), ("Andes", 1)])
        one_country = self.data(country_ids=self.ids("b"))
        self.assertEqual(self.ranking(one_country["top"]), [("Baltic", 4)])
        gold_silver = self.data(statuses=["gold", "silver"])
        self.assertEqual(self.ranking(gold_silver["top"]),
                         [("Andes", 3), ("Baltic", 3), ("Caspian", 1), ("Delta", 1), ("Euphrates", 1)])
        self.assertEqual(gold_silver["filters"], {"statuses": ["gold", "silver"], "country_ids": [], "years": []})

    def test_zero_match_countries_take_no_part(self):
        data = self.data(statuses=["ready"])
        names = {row["country"] for row in data["top"]["rows"] + data["bottom"]["rows"]}
        self.assertEqual(names, {"Andes", "Baltic", "Caspian", "Delta"})  # Euphrates has no Ready partner
        self.assertNotIn("Ganges", {country["name"] for country in data["options"]["countries"]})
        self.assertNotIn("Fjord", {country["name"] for country in data["options"]["countries"]})

    def test_empty_result_is_labelled(self):
        data = self.data(statuses=["gold"], country_ids=self.ids("d"))  # Delta's Gold partner is archived
        self.assertTrue(data["empty"])
        self.assertEqual((data["total"], data["top"]["rows"], data["bottom"]["rows"]), (0, [], []))
        self.assertFalse(data["overlap"] or data["few"])

    # ---------------------------------------------------------------- chart totals

    def test_chart_totals_equal_the_filtered_records(self):
        """Each chart reads the same records the summary counts (TP-PM-18)."""
        for filters in ({}, {"statuses": ["gold"]}, {"years": [2025, 2026]},
                        {"statuses": ["silver", "ready"], "country_ids": self.ids("a", "b", "c")}):
            data = self.data(user=self.reader, **filters)
            for key in ("top", "bottom"):
                with self.subTest(filters=filters, cohort=key):
                    cohort = data[key]
                    domain = cohort["domain"]
                    Partner = self.Partner.with_user(self.reader)
                    # The same call the graph view makes for the status chart ...
                    status_groups = Partner.web_read_group(domain, [], ["country_id", "current_status"], lazy=False)
                    chart_total = sum(group["__count"] for group in status_groups["groups"])
                    # ... and for the project-size chart.
                    size_groups = Partner.web_read_group(domain, [], ["project_size_bucket", "country_id"], lazy=False)
                    size_total = sum(group["__count"] for group in size_groups["groups"])
                    records = Partner.search(domain)
                    self.assertEqual(chart_total, len(records))
                    self.assertEqual(size_total, len(records))
                    self.assertEqual(cohort["total"], len(records))
                    self.assertEqual(sum(bucket["count"] for bucket in cohort["buckets"]), len(records))
                    self.assertEqual(set(records.country_id.ids), set(cohort["country_ids"]))
                    for row in cohort["rows"]:
                        mine = records.filtered(lambda partner, row=row: partner.country_id.id == row["country_id"])
                        self.assertEqual(row["total"], len(mine))
                        self.assertEqual([row[status] for status in STATUSES],
                                         [len(mine.filtered(lambda p, s=status: p.current_status == s))
                                          for status in STATUSES])
                    # The same filters, built independently from the field values.
                    expected = self.Partner.search([
                        ("is_demo", "=", False), ("country_id", "in", cohort["country_ids"]),
                        ("country_id.active", "=", True),
                        *([("current_status", "in", filters["statuses"])] if "statuses" in filters else []),
                        *([("country_id", "in", filters["country_ids"])] if "country_ids" in filters else []),
                        *([("first_seen_on", ">=", f"{min(filters['years'])}-01-01"),
                           ("first_seen_on", "<=", f"{max(filters['years'])}-12-31")]
                          if "years" in filters else []),
                    ])
                    self.assertEqual(records, expected.with_user(self.reader))

    def test_same_cohorts_feed_both_charts_of_a_side(self):
        data = self.data()
        for key in ("top", "bottom"):
            cohort = data[key]
            self.assertEqual(cohort["domain"][-1], ["country_id", "in", cohort["country_ids"]])
            self.assertEqual(cohort["domain"][:-1], data["domain"])
        self.assertEqual(data["top"]["country_ids"], self.ids("a", "b", "c", "d", "e"))

    def test_project_size_buckets(self):
        expected = [(None, False, "5_unknown"), (12.0, False, "5_unknown"), (0.0, True, "1_below_5"),
                    (4.99, True, "1_below_5"), (5.0, True, "2_5_to_11"), (10.99, True, "2_5_to_11"),
                    (11.0, True, "3_11_to_25"), (24.99, True, "3_11_to_25"), (25.0, True, "4_25_plus"),
                    (1000.0, True, "4_25_plus")]
        for average, known, bucket in expected:
            with self.subTest(average=average, known=known):
                self.assertEqual(project_size_bucket(average, known), bucket)
        # The stored field follows the observed value and its known flag.
        partner = self.add("e", "ready", 2026, average=4.99)
        self.assertEqual(partner.project_size_bucket, "1_below_5")
        self.Partner._record_observation({"source_id": partner.source_id, "average_project_size": 25.0},
                                         "2026-11-02")
        self.assertEqual(partner.project_size_bucket, "4_25_plus")
        self.Partner._record_observation({"source_id": partner.source_id, "average_project_size": None},
                                         "2026-11-03")
        self.assertEqual(partner.project_size_bucket, "5_unknown")
        self.assertEqual(partner.first_seen_year, 2026)
        labels = [label for _key, label in PROJECT_SIZE_BUCKETS]
        self.assertEqual(labels, ["Below 5", "5 to below 11", "11 to below 25", "25 and above", "Unknown"])
        self.assertEqual([bucket["label"] for bucket in self.data()["top"]["buckets"]], labels)

    # ---------------------------------------------------------------- inputs and access

    def test_filter_values_are_validated(self):
        data = self.Dashboard.get_dashboard_data({
            "source": "website",
            "domain": [["id", ">", 0]],  # not a filter: ignored
            "statuses": "gold",  # not a list: ignored
            "country_ids": ["1 OR 1=1", None, self.countries["f"].id, self.countries["a"].id],
            "years": ["x", 1999, 2025],
        })
        self.assertEqual(data["filters"], {"statuses": [], "country_ids": self.ids("a"), "years": [2025]})
        self.assertEqual(self.ranking(data["top"]), [("Andes", 2)])
        self.assertEqual(self.Dashboard.get_dashboard_data("not a dict")["filters"],
                         {"statuses": [], "country_ids": [], "years": []})

    def test_access_is_enforced_on_the_server(self):
        with self.assertRaises(AccessError):
            self.Dashboard.with_user(self.employee).get_dashboard_data({})
        reader = self.data(user=self.reader)
        self.assertEqual((reader["is_manager"], reader["sync"]["queue"]), (False, False))
        manager = self.data(user=self.manager)
        self.assertTrue(manager["is_manager"])
        self.assertEqual(set(manager["sync"]["queue"]),
                         {"pending", "retrying", "failed", "flagged_countries", "flagged_partners"})
        # The charts read partners as the user: a user without the group cannot.
        with self.assertRaises(AccessError):
            self.Partner.with_user(self.employee).web_read_group(reader["top"]["domain"], [], ["country_id"])
        # The manual sync stays a manager action, checked on the server.
        with self.assertRaises(AccessError):
            self.Run.with_user(self.reader).action_sync_now()

    def test_demo_and_website_data_are_never_mixed(self):
        data = self.data()
        self.assertEqual(data["source"], "website")
        countries = self.Country.browse(data["top"]["country_ids"] + data["bottom"]["country_ids"])
        self.assertFalse(any(countries.mapped("is_demo")))
        self.assertEqual(self.Dashboard.get_dashboard_data({})["source"], "website")  # website data exists
        if data["sources"]["demo"]:
            demo = self.Dashboard.get_dashboard_data({"source": "demo"})
            countries = self.Country.browse(demo["top"]["country_ids"] + demo["bottom"]["country_ids"])
            self.assertTrue(all(countries.mapped("is_demo")))

    # ---------------------------------------------------------------- sync state

    def test_sync_state_shows_waiting_last_success_and_queue(self):
        done = self.Run.create({"trigger": "daily", "state": "done",
                                "started_at": datetime(2026, 11, 9, 2, 0), "finished_at": datetime(2026, 11, 9, 2, 30)})
        waiting = self.Run.create({"trigger": "daily", "started_at": datetime(2026, 11, 10, 2, 0),
                                   "waiting_reason": "no page source is available"})
        self.WorkItem.create([
            {"kind": "country_partners", "run_id": waiting.id, "country_id": self.countries["a"].id},
            {"kind": "country_partners", "run_id": waiting.id, "country_id": self.countries["b"].id,
             "attempt_count": 2},
            {"kind": "country_partners", "run_id": done.id, "country_id": self.countries["c"].id,
             "state": "failed", "attempt_count": 5},
        ])
        sync = self.data(user=self.manager)["sync"]
        self.assertEqual(sync["last_run"]["id"], waiting.id)
        self.assertEqual((sync["last_run"]["state"], sync["last_run"]["state_label"]), ("running", "Running"))
        self.assertEqual(sync["last_success_at"], "2026-11-09 02:30:00")
        self.assertEqual((sync["waiting_reason"], sync["waiting_run_id"]),
                         ("no page source is available", waiting.id))
        self.assertEqual({key: sync["queue"][key] for key in ("pending", "retrying", "failed")},
                         {"pending": 2, "retrying": 1, "failed": 1})
        reader_sync = self.data(user=self.reader)["sync"]
        self.assertEqual(reader_sync["waiting_reason"], "no page source is available")
        self.assertFalse(reader_sync["queue"])

    # ---------------------------------------------------------------- views and menus

    def test_dashboard_is_the_entry_point(self):
        root = self.env.ref("azk_odoo_partner_monitor.menu_root")
        first = root.child_id.sorted("sequence")[0]
        self.assertEqual(first, self.env.ref("azk_odoo_partner_monitor.menu_dashboard"))
        action = self.env.ref("azk_odoo_partner_monitor.dashboard_action")
        self.assertEqual((first.action, action.tag), (action, "azk_odoo_partner_monitor.dashboard"))
        visible = self.env["ir.ui.menu"].with_user(self.reader)._visible_menu_ids()
        self.assertIn(first.id, visible)
        self.assertNotIn(first.id, self.env["ir.ui.menu"].with_user(self.employee)._visible_menu_ids())

    def test_graph_and_pivot_views_load_for_readers(self):
        data = self.data(user=self.reader)
        Partner = self.Partner.with_user(self.reader)
        for key, view_id in data["views"].items():
            with self.subTest(view=key):
                arch = Partner.get_views([(view_id, "graph")])["views"]["graph"]["arch"]
                self.assertIn("<graph", arch)
        self.assertIn('order="desc"', Partner.get_views([(data["views"]["top_status"], "graph")])
                      ["views"]["graph"]["arch"])
        for model, modes in ((self.Partner, ("pivot", "graph")), (self.History, ("pivot", "graph")),
                             (self.Reference, ("pivot",))):
            with self.subTest(model=model._name):
                views = model.with_user(self.reader).get_views([(False, mode) for mode in modes])
                self.assertEqual(set(views["views"]), set(modes))

    def test_template_escapes_website_text(self):
        """The client template prints every value with t-esc, never as markup."""
        path = os.path.join(os.path.dirname(__file__), "..", "static", "src", "dashboard", "dashboard.xml")
        with open(path, encoding="utf-8") as handle:
            template = handle.read()
        self.assertNotIn("t-raw", template)
        self.assertNotIn("t-out", template)
        self.assertIn('t-esc="row.country"', template)


@tagged("post_install", "-at_install")
class TestDashboardDemoData(PartnerMonitorCase):
    """The demo data behind the handoff walkthrough (D-20): more than ten
    countries, clearly labeled, with the ranking the walkthrough describes."""

    def setUp(self):
        super().setUp()
        if not self.Partner.with_context(active_test=False).search_count([("is_demo", "=", True)]):
            self.skipTest("this database has no demo data")
        self.Dashboard = self.env["azk_odoo_partner_monitor.dashboard"]

    def ranking(self, cohort):
        return [(row["country"].removeprefix("Demo Country "), row["total"]) for row in cohort["rows"]]

    def test_demo_data_ranking(self):
        data = self.Dashboard.get_dashboard_data({"source": "demo"})
        self.assertEqual(data["source"], "demo")
        self.assertEqual((data["ranked_countries"], data["total"]), (12, 47))
        self.assertFalse(data["overlap"])
        self.assertEqual(self.ranking(data["top"]),
                         [("Epsilon", 8), ("Zeta", 7), ("Eta", 6), ("Alpha", 5), ("Iota", 5)])
        self.assertEqual(self.ranking(data["bottom"]),
                         [("Beta", 1), ("Gamma", 1), ("Nu", 1), ("Mu", 2), ("Kappa", 3)])
        demo_countries = self.Country.with_context(active_test=False).search([("is_demo", "=", True)])
        self.assertGreater(len(demo_countries), 10)
        partners = self.Partner.with_context(active_test=False).search([("is_demo", "=", True)])
        self.assertEqual(set(partners.mapped("current_status")), {"gold", "silver", "ready"})
        self.assertGreater(len(set(partners.mapped("first_seen_year"))), 2)
        self.assertEqual(set(partners.mapped("project_size_bucket")), {key for key, _label in PROJECT_SIZE_BUCKETS})
        self.assertTrue(partners.filtered(lambda partner: not partner.active))

    def test_walkthrough_gold_2025(self):
        """Handoff walkthrough: Gold and 2025, then open Epsilon and count its partners."""
        data = self.Dashboard.get_dashboard_data({"source": "demo", "statuses": ["gold"], "years": [2025]})
        self.assertEqual(self.ranking(data["top"]),
                         [("Epsilon", 3), ("Zeta", 2), ("Alpha", 1), ("Gamma", 1), ("Iota", 1)])
        self.assertEqual(self.ranking(data["bottom"]),
                         [("Alpha", 1), ("Gamma", 1), ("Iota", 1), ("Kappa", 1), ("Zeta", 2)])
        self.assertTrue(data["overlap"])
        epsilon = data["top"]["rows"][0]
        partners = self.Partner.search(data["domain"] + [("country_id", "=", epsilon["country_id"])])
        self.assertEqual(len(partners), 3)
        self.assertEqual(set(partners.mapped("current_status")), {"gold"})
        self.assertEqual(set(partners.mapped("first_seen_year")), {2025})
