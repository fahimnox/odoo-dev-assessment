/** @odoo-module **/

import { registry } from "@web/core/registry";
import { graphView } from "@web/views/graph/graph_view";
import { GraphRenderer } from "@web/views/graph/graph_renderer";

// One color per partner status, the same in every dashboard chart. The
// standard graph view colors datasets by their order of appearance, which
// depends on the filtered data, so Gold could be blue in one chart and red in
// the next.
const STATUS_COLORS = { gold: "#c9a227", silver: "#8e9aa8", ready: "#3d84b8" };

export class PartnerMonitorDashboardGraphRenderer extends GraphRenderer {
    getBarChartData() {
        const data = super.getBarChartData();
        const statusField = this.model.metaData.fields.current_status;
        const colorByLabel = Object.fromEntries(
            (statusField?.selection || []).map(([key, label]) => [label, STATUS_COLORS[key]])
        );
        for (const dataset of data.datasets) {
            const color = colorByLabel[dataset.label];
            if (color) {
                dataset.backgroundColor = color;
            }
        }
        return data;
    }
}

/**
 * The graph view of the dashboard's four charts (js_class in
 * views/dashboard_views.xml): the standard graph view with fixed status
 * colors and without its toolbar, so the ranked order and the measure stay
 * the ones the dashboard computed. "Show them" opens the full views.
 */
registry.category("views").add("azk_pm_dashboard_graph", {
    ...graphView,
    Renderer: PartnerMonitorDashboardGraphRenderer,
    buttonTemplate: "azk_odoo_partner_monitor.DashboardGraphButtons",
});
