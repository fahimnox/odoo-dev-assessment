"""Partner Monitor demonstration in a real browser (Stage 11 acceptance).

Uses the DevTools helpers of scripts/ui_smoke_check.py (headless Chrome or
Edge) against the running web server, after scripts/acceptance_pm_demo.py:
the database then holds the demo data, a LIVE sample (Andorra and its
partners) and a run that ended partial after a SIMULATED outage, then
recovered. Credentials come from the environment and are never printed:
PM_UI_LOGIN and PM_UI_PASSWORD (the administrator), ACC_PASSWORD
(acc_pm_manager, the configured recipient). Optional: PM_UI_URL, PM_UI_BROWSER.

Usage: python scripts/acceptance_pm_ui_check.py OUTPUT_DIR

Steps, each reported as PASS or FAIL:
  1. administrator: the app opens on the dashboard with the WEBSITE data
     source selected and four charts; the Country filter set to Andorra keeps
     four charts; switching to DEMO data shows the demo banner and four charts;
  2. the live partner BDR GROUP SLU: the Status History and References tabs
     list the stored rows;
  3. the run of the live sample: its chatter holds the note about the partial run;
  4. acc_pm_manager (the configured recipient): the Discuss inbox shows that note;
  5. no JavaScript error.
A step that stops early (for example on a missing element) is reported as FAIL.
"""
import json
import os
import shutil
import sys
import tempfile
import time

import websocket

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tb_preview_smoke_check import rpc  # noqa: E402
from ui_smoke_check import APP_XMLID, BASE, Page, dashboard_facts, report, results, start_browser  # noqa: E402

CHARTS = "document.querySelectorAll('.o_pm_dashboard .o_pm_chart canvas').length === 4"
MESSAGES = "[...document.querySelectorAll('.o-mail-Message')].map((n) => n.innerText.replace(/\\s+/g, ' ').trim())"


def navigate(page, url, ready, timeout=240):
    """Open ``url`` and wait until the JS expression ``ready`` is true.

    Right after a server start, the first web client page builds the asset
    bundles and the browser can be too busy to answer a DevTools call within
    its 30 s; that is not a failure, so the wait decides (found in Stage 11).
    """
    try:
        page.call("Page.navigate", url=url)
    except websocket.WebSocketTimeoutException:
        pass
    time.sleep(1)
    page.wait(ready, timeout=timeout)


def login(page, login_name, password):
    navigate(page, f"{BASE}/web/session/logout", "document.readyState === 'complete'")
    navigate(page, f"{BASE}/web/login", "document.querySelector('input[name=login]') !== null", timeout=180)
    page.js(f"""(() => {{
        document.querySelector('input[name=login]').value = {json.dumps(login_name)};
        document.querySelector('input[name=password]').value = {json.dumps(password)};
        document.querySelector('form.oe_login_form').submit();
    }})()""")
    # Logged in once the web client has loaded (its menu bar is shown).
    page.wait("location.pathname.startsWith('/odoo') && document.querySelector('.o_main_navbar') !== null",
              timeout=300)


def click_and_wait_summary(page, expression):
    before = page.js("(document.querySelector('[data-pm=summary]') || {}).innerText || ''")
    page.js(expression)
    page.wait(f"((document.querySelector('[data-pm=summary]') || {{}}).innerText || '') !== {json.dumps(before)}",
              timeout=60)
    page.wait(CHARTS, timeout=60)
    time.sleep(2)  # let the charts finish their animation


def open_tab(page, name):
    page.js(f"document.querySelector('.o_notebook a.nav-link[name={name}]').click()")
    time.sleep(1.5)
    return page.js("""(() => {
        const pane = document.querySelector('.o_notebook .tab-pane.active');
        return [...pane.querySelectorAll('.o_data_row')].map((r) => r.innerText.replace(/\\s+/g, ' ').trim());
    })()""")


def dashboard_steps(page, output, admin):
    """1. The dashboard: website data by default, Andorra, then demo data."""
    login(page, *admin)
    navigate(page, f"{BASE}/odoo", f"document.querySelector('.o_app[data-menu-xmlid=\"{APP_XMLID}\"]') !== null")
    page.js(f"document.querySelector('.o_app[data-menu-xmlid=\"{APP_XMLID}\"]').click()")
    page.wait(CHARTS, timeout=90)
    time.sleep(2)
    sources = page.js("""[...document.querySelectorAll('[data-pm^=source-]')].map((n) => ({
        text: n.innerText.trim(), selected: n.classList.contains('btn-primary')}))""")
    facts = dashboard_facts(page)
    selected = [source["text"] for source in sources if source["selected"]]
    report("the dashboard opens on the website data (the live sample), four charts",
           bool(selected) and selected[0].startswith("Website data") and facts["canvases"] == 4
           and not facts["moduleError"],
           f"sources {[source['text'] for source in sources]}, selected {selected}, summary {facts['summary']!r}")
    page.screenshot(os.path.join(output, "stage11_dashboard_website.png"))
    click_and_wait_summary(page, "document.querySelector('[data-pm=source-demo]').click()")
    facts = dashboard_facts(page)
    report("the demo data source is separate and labeled", facts["canvases"] == 4 and "Demo data" in facts["banner"],
           f"banner {facts['banner'][:80]!r}; summary {facts['summary']!r}")
    page.screenshot(os.path.join(output, "stage11_dashboard_demo.png"))
    # The Country filter, on the demo data: the website sample has one country
    # only, so a filter on it would change nothing there.
    page.js("document.querySelector('.o_pm_country_filter .o_select_menu_toggler').click()")
    page.wait("document.querySelector('.o_select_menu_item_label') !== null", timeout=30)
    country = page.js("document.querySelector('.o_select_menu_item_label').innerText.trim()")
    click_and_wait_summary(page, """document.querySelector('.o_select_menu_item_label')
        .closest('.dropdown-item, .o_select_menu_item').click()""")
    page.js("document.body.click()")
    time.sleep(1)
    facts = dashboard_facts(page)
    cleared = page.js("document.querySelector('[data-pm=clear]') !== null")
    report("the Country filter applies to the four charts", facts["canvases"] == 4 and cleared
           and all(country in row for row in facts["top"]),
           f"country {country!r}; summary {facts['summary']!r}; top 5 {facts['top']}")
    page.screenshot(os.path.join(output, "stage11_dashboard_demo_country.png"))


def partner_step(page, output):
    """2. The live partner: status history and references."""
    partners = rpc(page, "azk_odoo_partner_monitor.partner", "search_read", [
        [("name", "ilike", "BDR GROUP"), ("is_demo", "=", False)],
        ["name", "total_references_count", "active_reference_count"]], {})
    if not partners:
        report("the live partner shows its status history and references", False, "no live BDR GROUP partner")
        return
    partner = partners[0]
    page.call("Emulation.setDeviceMetricsOverride", width=1500, height=1100, deviceScaleFactor=1, mobile=False)
    navigate(page, f"{BASE}/odoo/action-azk_odoo_partner_monitor.partner_action/{partner['id']}",
             "document.querySelector('.o_form_view .o_notebook') !== null")
    history = open_tab(page, "status_history")
    page.screenshot(os.path.join(output, "stage11_live_partner_history.png"))
    references = open_tab(page, "references")
    page.screenshot(os.path.join(output, "stage11_live_partner_references.png"))
    report("the live partner shows its status history and references",
           len(history) >= 1 and len(references) == partner["active_reference_count"],
           f"{partner['name']}: {len(history)} history rows {history[:1]}; {len(references)} reference rows "
           f"(stored active {partner['active_reference_count']}, listed {partner['total_references_count']})")


def chatter_step(page, output):
    """3. The run's chatter."""
    runs = rpc(page, "azk_odoo_partner_monitor.sync.run", "search_read", [
        [("notified_at", "!=", False)], ["display_name", "state"]], {})
    if not runs:
        report("the run's chatter holds the note about the partial run", False, "no notified run")
        return
    run = runs[-1]
    navigate(page, f"{BASE}/odoo/action-azk_odoo_partner_monitor.sync_run_action/{run['id']}",
             "document.querySelector('.o-mail-Message') !== null")
    time.sleep(1.5)
    note = next((text for text in page.js(MESSAGES) if "ended as" in text), "")
    page.screenshot(os.path.join(output, "stage11_run_chatter.png"))
    report("the run's chatter holds the note about the partial run", bool(note),
           f"run {run['display_name']} ({run['state']}): {note[:200]!r}")


def inbox_step(page, output, password):
    """4. The configured recipient's Discuss inbox."""
    login(page, "acc_pm_manager", password)
    try:
        navigate(page, f"{BASE}/odoo/discuss",
                 "[...document.querySelectorAll('.o-mail-Message')].some((n) => /ended as/.test(n.innerText))",
                 timeout=90)
        inbox = [text for text in page.js(MESSAGES) if "ended as" in text]
    except TimeoutError:
        inbox = []
    page.screenshot(os.path.join(output, "stage11_recipient_inbox.png"))
    report("the configured recipient (acc_pm_manager) finds the note in the Discuss inbox", bool(inbox),
           (inbox[0] if inbox else "no message with 'ended as'")[:200])


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    output = os.path.abspath(sys.argv[1])
    admin = (os.environ.get("PM_UI_LOGIN"), os.environ.get("PM_UI_PASSWORD"))
    recipient_password = os.environ.get("ACC_PASSWORD")
    if not all(admin) or not recipient_password:
        sys.exit("BLOCKED: set PM_UI_LOGIN, PM_UI_PASSWORD and ACC_PASSWORD")
    os.makedirs(output, exist_ok=True)
    profile = tempfile.mkdtemp(prefix="pm_acc_profile_")
    process, ws_url = start_browser(profile)
    page = Page(ws_url)
    try:
        page.call("Runtime.enable")
        page.call("Page.enable")
        page.call("Emulation.setDeviceMetricsOverride", width=1500, height=2300, deviceScaleFactor=1, mobile=False)
        for name, step in (("dashboard", lambda: dashboard_steps(page, output, admin)),
                           ("live partner", lambda: partner_step(page, output)),
                           ("run chatter", lambda: chatter_step(page, output)),
                           ("recipient inbox", lambda: inbox_step(page, output, recipient_password))):
            try:
                step()
            except Exception as error:  # noqa: BLE001 - report the step as failed and go on
                report(f"{name}: the step ran to its end", False, f"{type(error).__name__}: {error}"[:300])
        errors = [error for error in page.errors if error]
        report("no JavaScript error in the browser", not errors, "; ".join(errors)[:300])
    finally:
        try:
            page.ws.close()
        finally:
            process.kill()
            process.wait(timeout=30)
            shutil.rmtree(profile, ignore_errors=True)
    print(f"{sum(results)} of {len(results)} checks passed")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
