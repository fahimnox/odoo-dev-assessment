"""Partner Monitor dashboard smoke check in a real browser (Stage 06, TP-PM-20).

Drives headless Chrome or Edge through the DevTools protocol against the local
web server and saves screenshots. It needs a Chromium-based browser and the
Python package websocket-client on the machine that runs it.

Credentials come from the environment (PM_UI_LOGIN, PM_UI_PASSWORD) and are
never printed. Optional: PM_UI_URL (default http://127.0.0.1:8071),
PM_UI_BROWSER (path to chrome.exe or msedge.exe).

Usage: python scripts/ui_smoke_check.py OUTPUT_DIR [--sync]
  --sync  also click "Sync Now" (a manager action that queues a real run) and
          wait until the dashboard shows the run waiting for a page source.

Steps, each reported as PASS or FAIL:
  1. log in; open the home menu; open the Partner Monitor app: the dashboard
     must be the first screen, with four rendered charts;
  2. select Gold and the year 2025; the Top 5 table is read;
  3. open the first country of the Top 5: the partner list must hold as many
     records as the dashboard shows for that country;
  4. (--sync) Sync Now, then the waiting state.
JavaScript errors reported by the browser are listed at the end.
"""

import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

import websocket

BASE = os.environ.get("PM_UI_URL", "http://127.0.0.1:8071").rstrip("/")
PORT = 9333
BROWSERS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "/usr/bin/google-chrome", "/usr/bin/chromium",
]
APP_XMLID = "azk_odoo_partner_monitor.menu_root"
results = []


def report(name, passed, detail=""):
    results.append(passed)
    print(f"{'PASS' if passed else 'FAIL'} {name}{': ' + detail if detail else ''}", flush=True)


class Page:
    """A tiny DevTools-protocol client: one page, synchronous calls."""

    def __init__(self, ws_url):
        self.ws = websocket.create_connection(ws_url, timeout=30, suppress_origin=True)
        self.next_id = 0
        self.errors = []

    def call(self, method, **params):
        self.next_id += 1
        self.ws.send(json.dumps({"id": self.next_id, "method": method, "params": params}))
        while True:
            message = json.loads(self.ws.recv())
            if message.get("id") == self.next_id:
                if "error" in message:
                    raise RuntimeError(f"{method}: {message['error']}")
                return message.get("result", {})
            self.collect(message)

    def collect(self, event):
        if event.get("method") == "Runtime.exceptionThrown":
            details = event["params"]["exceptionDetails"]
            self.errors.append(details.get("exception", {}).get("description") or details.get("text"))
        elif event.get("method") == "Runtime.consoleAPICalled" and event["params"]["type"] == "error":
            self.errors.append(" ".join(str(arg.get("value", arg.get("description", "")))
                                        for arg in event["params"]["args"]))

    def js(self, expression):
        result = self.call("Runtime.evaluate", expression=expression, awaitPromise=True, returnByValue=True)
        if "exceptionDetails" in result:
            raise RuntimeError(result["exceptionDetails"].get("text"))
        return result["result"].get("value")

    def wait(self, expression, timeout=60):
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                if self.js(expression):
                    return True
            except (RuntimeError, websocket.WebSocketTimeoutException):
                pass  # the page is navigating or still busy: ask again
            time.sleep(0.5)
        raise TimeoutError(f"still false after {timeout} s: {expression}")

    def goto(self, url):
        self.call("Page.navigate", url=url)
        time.sleep(1)

    def screenshot(self, path):
        data = self.call("Page.captureScreenshot", format="png")["data"]
        with open(path, "wb") as handle:
            handle.write(base64.b64decode(data))
        print(f"     screenshot {os.path.basename(path)}", flush=True)


def start_browser(profile):
    browser = os.environ.get("PM_UI_BROWSER") or next((path for path in BROWSERS if os.path.exists(path)), None)
    if not browser:
        sys.exit("BLOCKED: no Chrome or Edge found (set PM_UI_BROWSER)")
    process = subprocess.Popen([
        browser, "--headless=new", f"--remote-debugging-port={PORT}", f"--user-data-dir={profile}",
        "--no-first-run", "--no-default-browser-check", "--disable-extensions", "--lang=en-US",
        f"--remote-allow-origins=http://127.0.0.1:{PORT}", "about:blank",
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    deadline = time.time() + 30
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/list", timeout=2) as response:
                targets = json.load(response)
            page = next(target for target in targets if target["type"] == "page")
            return process, page["webSocketDebuggerUrl"]
        except (OSError, StopIteration, ValueError):
            time.sleep(0.5)
    process.kill()
    sys.exit("BLOCKED: the browser did not open its DevTools port")


def dashboard_facts(page):
    return page.js("""(() => {
        const text = (selector) => [...document.querySelectorAll(selector)].map((n) => n.innerText.trim());
        return {
            title: (document.querySelector('.o_breadcrumb .active') || document.querySelector('.o_breadcrumb') || {}).innerText,
            banner: text('[data-pm=demo-banner]').join(' '),
            waiting: text('[data-pm=waiting]').join(' '),
            sync: text('[data-pm=sync]').join(' '),
            summary: text('[data-pm=summary]').join(' '),
            notes: text('[data-pm=overlap], [data-pm=few], [data-pm=empty]').join(' '),
            top: text('[data-pm=cohort-top] tbody tr'),
            bottom: text('[data-pm=cohort-bottom] tbody tr'),
            topBuckets: text('[data-pm=buckets-top]').join(' '),
            canvases: document.querySelectorAll('.o_pm_dashboard .o_pm_chart canvas').length,
            syncButton: Boolean(document.querySelector('[data-pm=sync-now]')),
            // The standard graph toolbar ("Measures") must not show: the
            // charts use the dashboard graph view (js_class).
            toolbar: [...document.querySelectorAll('.o_pm_chart')].some((n) => /Measures/.test(n.innerText)),
            // Odoo's module loader prints asset errors into the page.
            moduleError: (document.querySelector('.o_module_error') || {}).innerText || '',
        };
    })()""")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    output = os.path.abspath(sys.argv[1])
    with_sync = "--sync" in sys.argv[2:]
    login, password = os.environ.get("PM_UI_LOGIN"), os.environ.get("PM_UI_PASSWORD")
    if not login or not password:
        sys.exit("BLOCKED: set PM_UI_LOGIN and PM_UI_PASSWORD")
    os.makedirs(output, exist_ok=True)
    profile = tempfile.mkdtemp(prefix="pm_ui_profile_")
    process, ws_url = start_browser(profile)
    page = Page(ws_url)
    try:
        page.call("Runtime.enable")
        page.call("Page.enable")
        page.call("Emulation.setDeviceMetricsOverride", width=1500, height=2300, deviceScaleFactor=1, mobile=False)

        # 1. Log in, then open the app from the home menu.
        page.goto(f"{BASE}/web/login")
        page.wait("document.querySelector('input[name=login]') !== null", timeout=180)
        page.js(f"""(() => {{
            document.querySelector('input[name=login]').value = {json.dumps(login)};
            document.querySelector('input[name=password]').value = {json.dumps(password)};
            document.querySelector('form.oe_login_form').submit();
        }})()""")
        page.wait("location.pathname.startsWith('/odoo')", timeout=240)
        page.goto(f"{BASE}/odoo")
        page.wait(f"document.querySelector('.o_app[data-menu-xmlid=\"{APP_XMLID}\"]') !== null", timeout=90)
        page.js(f"document.querySelector('.o_app[data-menu-xmlid=\"{APP_XMLID}\"]').click()")
        page.wait("document.querySelectorAll('.o_pm_dashboard .o_pm_chart canvas').length === 4", timeout=90)
        time.sleep(2)  # let the charts finish their animation
        facts = dashboard_facts(page)
        report("no asset or module loading error", not facts["moduleError"], facts["moduleError"][:200])
        report("the app opens on the dashboard", facts["title"].strip().startswith("Dashboard"),
               f"breadcrumb {facts['title']!r}, {facts['canvases']} charts")
        report("the charts use the dashboard graph view (no toolbar)", not facts["toolbar"])
        report("demo data is labeled", "Demo data" in facts["banner"], facts["banner"][:90])
        print(f"     sync panel: {facts['sync']!r}")
        print(f"     summary: {facts['summary']!r} {facts['notes']!r}")
        print(f"     top 5: {facts['top']}")
        print(f"     bottom 5: {facts['bottom']}")
        print(f"     top 5 project sizes: {facts['topBuckets']!r}")
        page.screenshot(os.path.join(output, "stage06_dashboard_demo.png"))

        # 2. Gold and 2025.
        version = page.js("document.querySelector('[data-pm=summary]').innerText")
        page.js("document.querySelector('[data-pm=status-gold]').click()")
        page.wait(f"document.querySelector('[data-pm=summary]').innerText !== {json.dumps(version)}")
        version = page.js("document.querySelector('[data-pm=summary]').innerText")
        page.wait("document.querySelector('[data-pm=year-2025]') !== null")
        page.js("document.querySelector('[data-pm=year-2025]').click()")
        page.wait(f"document.querySelector('[data-pm=summary]').innerText !== {json.dumps(version)}")
        page.wait("document.querySelectorAll('.o_pm_dashboard .o_pm_chart canvas').length === 4", timeout=60)
        time.sleep(2)
        facts = dashboard_facts(page)
        selected = page.js("[...document.querySelectorAll('[data-pm^=status-].btn-primary, [data-pm^=year-].btn-primary')]"
                           ".map((n) => n.innerText.trim())")
        report("Gold and 2025 are applied to all four charts", facts["canvases"] == 4 and selected == ["Gold", "2025"],
               f"selected {selected}, {facts['summary']!r}")
        print(f"     top 5: {facts['top']}")
        print(f"     bottom 5: {facts['bottom']}")
        print(f"     notes: {facts['notes']!r}")
        page.screenshot(os.path.join(output, "stage06_dashboard_gold_2025.png"))

        # 3. Open the first country of the Top 5 and count its partners.
        first = page.js("""(() => {
            const link = document.querySelector('[data-pm=cohort-top] tbody tr a');
            const cells = link.closest('tr').querySelectorAll('td');
            return {country: link.innerText.trim(), shown: Number(cells[2].innerText.trim())};
        })()""")
        page.js("document.querySelector('[data-pm=cohort-top] tbody tr a').click()")
        page.wait("document.querySelector('.o_list_view .o_data_row') !== null", timeout=60)
        time.sleep(1)
        listed = page.js("""(() => ({
            rows: document.querySelectorAll('.o_list_view .o_data_row').length,
            pager: (document.querySelector('.o_pager_counter') || {}).innerText,
            title: (document.querySelector('.o_breadcrumb .active') || {}).innerText,
        }))()""")
        report("the country's partner list matches the dashboard count", listed["rows"] == first["shown"],
               f"{first['country']}: dashboard {first['shown']}, list {listed['rows']} rows, "
               f"pager {listed['pager']!r}, title {listed['title']!r}")
        page.call("Emulation.setDeviceMetricsOverride", width=1500, height=900, deviceScaleFactor=1, mobile=False)
        page.screenshot(os.path.join(output, "stage06_country_partners.png"))
        page.call("Emulation.setDeviceMetricsOverride", width=1500, height=2300, deviceScaleFactor=1, mobile=False)

        # 4. Sync Now (manager), then the waiting state.
        if with_sync:
            page.js("history.back()")
            page.wait("document.querySelector('[data-pm=sync-now]') !== null", timeout=60)
            page.js("document.querySelector('[data-pm=sync-now]').click()")
            page.wait("[...document.querySelectorAll('.o_notification')].some((n) => /queued/.test(n.innerText))",
                      timeout=60)
            notice = page.js("[...document.querySelectorAll('.o_notification')].map((n) => n.innerText).join(' ')")
            report("Sync Now queues a run", "queued" in notice, notice.strip()[:80])
            deadline = time.time() + 240
            waiting = ""
            while time.time() < deadline and not waiting:
                time.sleep(10)
                page.js("location.reload()")
                time.sleep(3)
                page.wait("document.querySelector('.o_pm_dashboard') !== null", timeout=90)
                waiting = page.js("(document.querySelector('[data-pm=waiting]') || {}).innerText || ''")
            report("the dashboard shows the run waiting for a page source", bool(waiting), waiting.strip()[:120])
            page.wait("document.querySelectorAll('.o_pm_dashboard .o_pm_chart canvas').length === 4", timeout=60)
            time.sleep(2)
            print(f"     sync panel: {dashboard_facts(page)['sync']!r}")
            page.call("Emulation.setDeviceMetricsOverride", width=1500, height=900, deviceScaleFactor=1, mobile=False)
            page.screenshot(os.path.join(output, "stage06_sync_waiting.png"))
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
