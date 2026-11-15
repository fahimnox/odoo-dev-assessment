"""The Dynamic Trial Balance's analytic selector in a real browser (Stage 10).

For a database where Odoo's Analytic Accounting setting is on (it is off on
azk_ee24; run this on a disposable database served by a temporary server,
docs/test_results.md). Uses the helpers of scripts/tb_preview_smoke_check.py
and scripts/ui_smoke_check.py (headless Chrome or Edge through the DevTools
protocol). Credentials come from the environment (PM_UI_LOGIN,
PM_UI_PASSWORD) and are never printed. Optional: PM_UI_URL, PM_UI_BROWSER.

Usage: python scripts/tb_analytic_smoke_check.py OUTPUT_DIR

Steps on the demo company, March 2026, Skip Zero Balance, each PASS or FAIL:
  1. the wizard shows the Analytic Accounts field; choosing "Sales Department"
     there and clicking Preview opens the report with that analytic account,
     and the visible account rows equal the engine's result;
  2. the preview's analytic dropdown, "All analytic accounts": the report is
     recalculated and equals the engine without the filter;
  3. the same dropdown, "Sales Department" again: recalculated, equal again;
  4. PDF and Download Excel with the filter on: the XLSX equals the engine
     (codes, nine numbers, totals), and the PDF states the analytic account
     and holds every row;
  5. the download route refuses tampered options from this user: another
     company in our options, or in the company list;
  6. no JavaScript error.
"""

import os
import re
import shutil
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tb_preview_smoke_check import (  # noqa: E402
    AMOUNT_KEYS, APP_XMLID, DEMO_COMPANY, MENU_XMLID, REPORT, REPORTING_XMLID, check_xlsx, click, click_text,
    close_dropdowns, download, fill, lines, read_pdf, route_download, route_error, rpc, set_date)
from ui_smoke_check import BASE, Page, report, results, start_browser  # noqa: E402

ANALYTIC = "Sales Department"
DATE_FROM, DATE_TO = "2026-03-01", "2026-03-31"
ITEMS = ".o-dropdown-item, .dropdown-item"


def number(text):
    """The number shown in a preview cell (thousands separators and currency symbols removed)."""
    cleaned = re.sub(r"[^0-9.\-]", "", text or "")
    return float(cleaned) if cleaned not in ("", "-", ".") else 0.0


def differences(page, result):
    """What differs between the visible account rows and the engine's leaf rows (empty: equal)."""
    shown = {line["name"]: line["cells"] for line in lines(page)}
    accounts = [name for name in shown if re.match(r"\d{6} ", name)]
    problems = []
    if len(accounts) != len(result["leaf_rows"]):
        problems.append(f"{len(accounts)} account rows shown, the engine has {len(result['leaf_rows'])}")
    for row in result["leaf_rows"]:
        label = f"{row['account_code']} {row['account_name']}"
        cells = next((cells for name, cells in shown.items() if name.startswith(label)), None)
        if cells is None:
            problems.append(f"{label} not shown")
            continue
        got = tuple(number(text) for text in cells[:9])
        want = tuple(round(row[key], 2) for key in AMOUNT_KEYS)
        if any(abs(a - b) > 0.005 for a, b in zip(got, want)):
            problems.append(f"{label}: shown {got}, engine {want}")
    return problems


def wait_equal(page, result, timeout=90):
    deadline = time.time() + timeout
    problems = differences(page, result)
    while problems and time.time() < deadline:
        time.sleep(1)
        problems = differences(page, result)
    return problems


def choose_analytic(page, label):
    click(page, ".o_azk_tb_analytic_toggle")
    page.wait(fill(f"[...document.querySelectorAll('{ITEMS}')].some((n) => n.innerText.trim() === WANTED)",
                   WANTED=label), timeout=30)
    click_text(page, ITEMS, label)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    output = os.path.abspath(sys.argv[1])
    login, password = os.environ.get("PM_UI_LOGIN"), os.environ.get("PM_UI_PASSWORD")
    if not login or not password:
        sys.exit("BLOCKED: set PM_UI_LOGIN and PM_UI_PASSWORD")
    downloads = os.path.join(output, "downloads")
    os.makedirs(downloads, exist_ok=True)
    profile = tempfile.mkdtemp(prefix="tb_analytic_profile_")
    process, ws_url = start_browser(profile)
    page = Page(ws_url)
    try:
        page.call("Runtime.enable")
        page.call("Page.enable")
        page.call("Emulation.setDeviceMetricsOverride", width=1600, height=1000, deviceScaleFactor=1, mobile=False)
        try:
            page.call("Browser.setDownloadBehavior", behavior="allow", downloadPath=downloads)
        except RuntimeError:
            page.call("Page.setDownloadBehavior", behavior="allow", downloadPath=downloads)

        # Log in, make the demo company the active one, open the wizard.
        page.goto(f"{BASE}/web/login")
        page.wait("document.querySelector('input[name=login]') !== null", timeout=180)
        page.js(fill("""(() => {
            document.querySelector('input[name=login]').value = LOGIN;
            document.querySelector('input[name=password]').value = PASSWORD;
            document.querySelector('form.oe_login_form').submit();
        })()""", LOGIN=login, PASSWORD=password))
        page.wait("location.pathname.startsWith('/odoo')", timeout=240)
        page.goto(f"{BASE}/odoo")
        page.wait("document.querySelector('.o_main_navbar') !== null", timeout=120)
        company_id = page.js(fill("""(() => {
            const session = odoo.loader.modules.get('@web/session').session;
            const company = Object.values(session.user_companies.allowed_companies).find((c) => c.name === NAME);
            return company ? company.id : null;
        })()""", NAME=DEMO_COMPANY))
        if not company_id:
            raise RuntimeError("the demo company is not among the user's companies")
        page.js(f"document.cookie = 'cids={company_id}; path=/'")
        page.goto(f"{BASE}/odoo")
        app = f".o_app[data-menu-xmlid=\"{APP_XMLID}\"]"
        page.wait(f"document.querySelector('{app}') !== null", timeout=120)
        page.js(f"document.querySelector('{app}').click()")
        reporting = f"[data-menu-xmlid=\"{REPORTING_XMLID}\"]"
        page.wait(f"document.querySelector('{reporting}') !== null", timeout=90)
        page.js(f"document.querySelector('{reporting}').click()")
        item = f"[data-menu-xmlid=\"{MENU_XMLID}\"]"
        page.wait(f"document.querySelector('{item}') !== null", timeout=30)
        page.js(f"document.querySelector('{item}').click()")
        page.wait("document.querySelector('.modal .o_form_view') !== null", timeout=60)
        time.sleep(1)
        context = {"allowed_company_ids": [company_id]}
        analytic_id = rpc(page, "account.analytic.account", "search_read", [[
            ("name", "=", ANALYTIC), ("company_id", "=", company_id)], ["id"]], context)[0]["id"]

        def engine(analytic):
            return rpc(page, "azk_dynamic_trial_balance.engine", "compute", [{
                "date_from": DATE_FROM, "date_to": DATE_TO, "company_id": company_id,
                "skip_zero_balance": True, "analytic_account_id": analytic}], context)

        filtered, everything = engine(analytic_id), engine(None)

        # 1. The wizard's Analytic Accounts field, then Preview.
        field = ".modal div[name=analytic_account_id] input"
        has_field = page.js(f"document.querySelector('{field}') !== null")
        set_date(page, "date_from", "03/01/2026")
        set_date(page, "date_to", "03/31/2026")
        page.js("document.querySelector('.modal div[name=skip_zero_balance] input[type=checkbox]').click()")
        page.js(f"(() => {{ const el = document.querySelector('{field}'); el.focus(); el.select(); }})()")
        page.call("Input.insertText", text=ANALYTIC)
        page.wait(fill("[...document.querySelectorAll('.o-autocomplete--dropdown-item')]"
                       ".some((n) => n.innerText.trim() === WANTED)", WANTED=ANALYTIC), timeout=30)
        click_text(page, ".o-autocomplete--dropdown-item", ANALYTIC)
        time.sleep(1)
        chosen = page.js(f"document.querySelector('{field}').value")
        page.screenshot(os.path.join(output, "stage10_analytic_wizard.png"))
        page.js("document.querySelector('.modal-footer button[name=action_preview]').click()")
        page.wait(f"document.querySelector('{REPORT} tr[data-id=line]') !== null", timeout=120)
        problems = wait_equal(page, filtered)
        toggle = page.js("(document.querySelector('.o_azk_tb_analytic_toggle') || {}).innerText || ''").strip()
        page.screenshot(os.path.join(output, "stage10_analytic_preview_filtered.png"))
        report("the wizard's Analytic Accounts field opens the preview filtered; rows equal the engine",
               has_field and chosen == ANALYTIC and toggle == ANALYTIC and not problems,
               f"wizard field {chosen!r}, preview selector {toggle!r}, "
               f"{len(filtered['leaf_rows'])} rows with the filter, {len(everything['leaf_rows'])} without; "
               f"{problems[:3]}")

        # 2. and 3. The preview's analytic dropdown recalculates the report.
        choose_analytic(page, "All analytic accounts")
        problems = wait_equal(page, everything)
        close_dropdowns(page)
        page.screenshot(os.path.join(output, "stage10_analytic_preview_all.png"))
        report("the preview's analytic dropdown, All analytic accounts: recalculated, equal to the engine",
               not problems, f"{problems[:3]}")
        choose_analytic(page, ANALYTIC)
        problems = wait_equal(page, filtered)
        close_dropdowns(page)
        report(f"the preview's analytic dropdown, {ANALYTIC}: recalculated, equal to the engine",
               not problems, f"{problems[:3]}")

        # 4. Downloads with the filter on.
        pdf = download(page, "PDF", downloads, ".pdf", "stage10_analytic.pdf")
        xlsx = download(page, "Download Excel", downloads, ".xlsx", "stage10_analytic.xlsx",
                        menu=".o_control_panel button:has(> i.fa-cog)")
        same, typed, count, frozen = check_xlsx(xlsx, filtered)
        text, pages = read_pdf(pdf, os.path.join(output, "stage10_analytic_pdf"))
        flat = " ".join(text.split())
        labels = [f"{row['account_code']} {row['account_name']}" for row in filtered["leaf_rows"]]
        missing = [label for label in labels if label not in flat]
        report("PDF and XLSX with the analytic filter: the XLSX equals the engine, the PDF states the filter",
               same and typed and bool(frozen) and not missing
               and re.search(rf"Analytic Accounts\s*:\s*{ANALYTIC}", flat) is not None,
               f"{count} XLSX rows incl. Total, {pages} PDF page(s), missing in PDF {missing[:3]}")

        # 5. Tampered download options, as this user: another company in our
        #    options, or in the company list the route turns into the active
        #    companies. Company 1 is the database's main company, which the
        #    read-only accountant of this check may not use.
        report_id = rpc(page, "account.report", "search_read", [[("name", "=", "Dynamic Trial Balance")], ["id"]],
                        context)[0]["id"]
        good = rpc(page, "account.report", "get_options", [[report_id], {
            "date": {"date_from": DATE_FROM, "date_to": DATE_TO, "mode": "range", "filter": "custom"},
            "azk_tb": {"company_id": company_id, "skip_zero_balance": True, "analytic_account_id": analytic_id},
        }], context)
        other = {**good, "azk_tb": {**good["azk_tb"], "company_id": 1}}
        listed = {**good, "companies": [{"id": 1, "name": "main", "currency_id": 1}]}
        answers = {name: route_download(page, options, "export_to_xlsx") for name, options in
                   (("our company option", other), ("the company list", listed))}
        refused = {name: route_error(answer) for name, answer in answers.items()}
        report("tampered download options are refused for this user (another company)",
               company_id != 1 and all(answer["body"][:2] != b"PK" for answer in answers.values())
               and all(name == "odoo.exceptions.AccessError" for name, _message in refused.values()),
               "; ".join(f"{label}: {name}: {(message or '')[:70]!r}" for label, (name, message) in refused.items()))

        errors = [error for error in page.errors if error]
        report("no JavaScript error in the browser", not errors, "; ".join(errors)[:300])
    except Exception as error:  # report the step that failed, then stop
        report("unexpected failure", False, f"{type(error).__name__}: {error}")
        try:
            page.screenshot(os.path.join(output, "stage10_analytic_failure.png"))
        except Exception:  # noqa: BLE001 - the browser may be gone
            pass
    finally:
        try:
            page.ws.close()
        finally:
            process.kill()
            process.wait(timeout=30)
            shutil.rmtree(profile, ignore_errors=True)
    print(f"{sum(results)} of {len(results)} checks passed")
    sys.exit(0 if results and all(results) else 1)


if __name__ == "__main__":
    main()
