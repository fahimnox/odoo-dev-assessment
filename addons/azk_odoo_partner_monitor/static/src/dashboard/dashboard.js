/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { deserializeDateTime, formatDateTime } from "@web/core/l10n/dates";
import { registry } from "@web/core/registry";
import { SelectMenu } from "@web/core/select_menu/select_menu";
import { useService } from "@web/core/utils/hooks";
import { Layout } from "@web/search/layout";
import { View } from "@web/views/view";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";

const DASHBOARD_MODEL = "azk_odoo_partner_monitor.dashboard";
const PARTNER_MODEL = "azk_odoo_partner_monitor.partner";
const RUN_MODEL = "azk_odoo_partner_monitor.sync.run";

function emptyFilters(source) {
    return { statuses: [], country_ids: [], years: [], source: source || false };
}

/**
 * Partner Monitor dashboard (docs/architecture.md 5.8 and 5.13).
 *
 * The component keeps only the filter VALUES. Each change asks the server
 * (get_dashboard_data) for the ranking, the two country cohorts and the
 * domains of the four charts, then remounts the four embedded graph views
 * (standard views defined in XML) with those domains. All text is rendered
 * with t-esc, so website text is always escaped.
 */
export class PartnerMonitorDashboard extends Component {
    static template = "azk_odoo_partner_monitor.Dashboard";
    static components = { Layout, SelectMenu, View };
    static props = { ...standardActionServiceProps };

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.state = useState({ filters: emptyFilters(), data: null, version: 0 });
        onWillStart(() => this.load());
    }

    async load() {
        const data = await this.orm.call(DASHBOARD_MODEL, "get_dashboard_data", [this.state.filters]);
        // Keep the filters the server actually applied (unknown values are dropped there).
        this.state.filters = { ...data.filters, source: data.source };
        this.state.data = data;
        this.state.version++;
    }

    // ------------------------------------------------------------------
    // Filters
    // ------------------------------------------------------------------

    isSelected(key, value) {
        return this.state.filters[key].includes(value);
    }

    toggle(key, value) {
        const current = this.state.filters[key];
        this.state.filters[key] = current.includes(value)
            ? current.filter((item) => item !== value)
            : [...current, value];
        return this.load();
    }

    onCountriesSelected(countryIds) {
        this.state.filters.country_ids = countryIds;
        return this.load();
    }

    setSource(source) {
        this.state.filters = emptyFilters(source);
        return this.load();
    }

    clearFilters() {
        this.state.filters = emptyFilters(this.state.data.source);
        return this.load();
    }

    get countryChoices() {
        return this.state.data.options.countries.map((country) => ({
            value: country.id,
            label: country.name,
        }));
    }

    get hasFilters() {
        const { statuses, country_ids, years } = this.state.filters;
        return Boolean(statuses.length || country_ids.length || years.length);
    }

    // ------------------------------------------------------------------
    // Charts and navigation
    // ------------------------------------------------------------------

    chartProps(cohortKey, viewKey) {
        const data = this.state.data;
        const viewId = data.views[viewKey];
        return {
            resModel: PARTNER_MODEL,
            type: "graph",
            views: [
                [viewId, "graph"],
                [false, "search"],
            ],
            domain: data[cohortKey].domain,
            context: {},
            display: { controlPanel: false },
        };
    }

    openPartners(domain, name) {
        return this.actionService.doAction({
            type: "ir.actions.act_window",
            name,
            res_model: PARTNER_MODEL,
            views: [
                [false, "list"],
                [false, "form"],
            ],
            domain,
            target: "current",
        });
    }

    openCountry(row) {
        const domain = [...this.state.data.domain, ["country_id", "=", row.country_id]];
        return this.openPartners(domain, _t("%s: matching partners", row.country));
    }

    openAllMatching() {
        return this.openPartners(this.state.data.domain, _t("Matching partners"));
    }

    // ------------------------------------------------------------------
    // Sync
    // ------------------------------------------------------------------

    formatDate(value) {
        return value ? formatDateTime(deserializeDateTime(value)) : "";
    }

    stateBadge(state) {
        const classes = {
            running: "text-bg-info",
            done: "text-bg-success",
            partial: "text-bg-warning",
            failed: "text-bg-danger",
        };
        return classes[state] || "text-bg-secondary";
    }

    openRun(runId) {
        return this.actionService.doAction({
            type: "ir.actions.act_window",
            res_model: RUN_MODEL,
            res_id: runId,
            views: [[false, "form"]],
            target: "current",
        });
    }

    openRuns() {
        return this.actionService.doAction("azk_odoo_partner_monitor.sync_run_action");
    }

    openWorkItems(filterName) {
        return this.actionService.doAction("azk_odoo_partner_monitor.work_item_action", {
            additionalContext: { [`search_default_${filterName}`]: 1 },
        });
    }

    async syncNow() {
        // The server only queues the work and wakes the worker (manager check
        // included); the returned notification reloads this dashboard.
        const action = await this.orm.call(RUN_MODEL, "action_sync_now", [[]]);
        return this.actionService.doAction(action);
    }
}

registry.category("actions").add("azk_odoo_partner_monitor.dashboard", PartnerMonitorDashboard);
