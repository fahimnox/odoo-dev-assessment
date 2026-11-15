"""Dynamic Trial Balance preview and downloads in a real browser (Stage 09).

Uses the DevTools helpers of scripts/ui_smoke_check.py (headless Chrome or
Edge on the machine that runs it) against the local web server, on the
installed demo company "AZK Trial Balance Demo (EGP)". Credentials come from
the environment (PM_UI_LOGIN, PM_UI_PASSWORD) and are never printed.
Optional: PM_UI_URL, PM_UI_BROWSER.

The downloaded files are read with openpyxl (XLSX) and PyMuPDF (PDF). The
script imports them only for those steps; without them, the file checks
are reported as NOT RUN.

Usage: python scripts/tb_preview_smoke_check.py OUTPUT_DIR

Steps, each reported as PASS, FAIL or NOT RUN:
  1. log in with the demo company active; Accounting > Reporting > Dynamic
     Trial Balance opens the wizard; set January 2026 and Skip Zero Balance;
     Preview opens the standard report view with Bank ending at 1,200.00
     (posted entries only);
  2. Options > Draft Entries recalculates the report: Bank ends at 1,000.00;
  3. searching "bank" keeps Bank and hides Expenses; clearing the search
     shows every line again;
  4. Trial Balance > Hierarchy and Subtotals adds the group rows; folding
     group 10140 hides Bank, unfolding shows it again;
  5. PDF and Download Excel (gear menu) download files; the XLSX rows (codes and the
     nine numbers) equal the engine's result for the same options, read
     over JSON-RPC as the same user; the PDF text holds the Bank row and
     the options; its pages are rendered to PNG;
  6. without Skip Zero Balance the PDF has several pages, each with the
     column header; its pages are rendered to PNG;
  7. an account prefix without accounts shows the no-results message;
  8. the download route (/account_reports, what the PDF and XLSX buttons
     call) refuses tampered options and gives no file without a session;
  9. for eight option sets (posted only, drafts, hierarchy, parents only,
     amount currency, analytic, zero filtering, empty result) the real PDF
     and XLSX from that route are compared with the engine;
 10. no JavaScript error.
"""

import base64
import html
import io
import json
import os
import re
import shutil
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ui_smoke_check import BASE, Page, report, results, start_browser  # noqa: E402

APP_XMLID = "accountant.menu_accounting"
REPORTING_XMLID = "account.menu_finance_reports"
MENU_XMLID = "azk_dynamic_trial_balance.menu_dynamic_trial_balance"
DEMO_COMPANY = "AZK Trial Balance Demo (EGP)"
REPORT = ".o_action.account_report.azk_dynamic_trial_balance"
AMOUNT_KEYS = (
    "initial_debit", "initial_credit", "initial_balance",
    "debit", "credit", "balance",
    "ending_debit", "ending_credit", "ending_balance",
)
AMOUNT_FORMAT = "#,##0.00;-#,##0.00;0.00"
OPTION_SETS = {
    "posted only": {},
    "with drafts": {"drafts": True},
    "hierarchy": {"hierarchy_subtotals": True},
    "parents only": {"hierarchy_subtotals": True, "hierarchy_only_parents": True, "account_level": 2},
    "amount currency": {"show_amount_currency": True, "skip_zero_balance": True},
    "analytic": {"date_from": "2026-03-01", "date_to": "2026-03-31", "analytic": "Sales Department"},
    "zero filtering": {"skip_zero_balance": True},
    "empty result": {"date_from": "2024-01-01", "date_to": "2024-01-31", "skip_zero_balance": True},
}
not_run = []


def skip(name, reason):
    not_run.append(name)
    print(f"NOT RUN {name}: {reason}", flush=True)


def fill(template, **values):
    """Put JSON-encoded values into a JavaScript template (placeholders in capitals)."""
    for key, value in values.items():
        template = template.replace(key, json.dumps(value))
    return template


def click(page, selector):
    """A real mouse click in the middle of the first element matching ``selector``."""
    box = page.js(fill("""(() => {
        const el = document.querySelector(SELECTOR);
        if (!el) return null;
        el.scrollIntoView({block: 'center'});
        const r = el.getBoundingClientRect();
        return {x: r.left + r.width / 2, y: r.top + r.height / 2};
    })()""", SELECTOR=selector))
    if not box:
        raise RuntimeError(f"nothing to click: {selector}")
    for kind in ("mouseMoved", "mousePressed", "mouseReleased"):
        page.call("Input.dispatchMouseEvent", type=kind, x=box["x"], y=box["y"], button="left", clickCount=1)
    time.sleep(0.3)


def click_text(page, selector, text):
    """Click the element matching ``selector`` whose text is exactly ``text``."""
    found = page.js(fill("""(() => {
        document.querySelectorAll('[data-tb-target]').forEach((n) => n.removeAttribute('data-tb-target'));
        const el = [...document.querySelectorAll(SELECTOR)].find((n) => n.innerText.trim() === WANTED);
        if (el) el.setAttribute('data-tb-target', '1');
        return Boolean(el);
    })()""", SELECTOR=selector, WANTED=text))
    if not found:
        raise RuntimeError(f"no {selector} with the text {text!r}")
    click(page, "[data-tb-target='1']")


def press_enter(page):
    for kind in ("keyDown", "keyUp"):
        page.call("Input.dispatchKeyEvent", type=kind, key="Enter", code="Enter",
                  windowsVirtualKeyCode=13, nativeVirtualKeyCode=13)


def set_date(page, field, text):
    selector = f".modal div[name={field}] input"
    page.js(f"(() => {{ const el = document.querySelector('{selector}'); el.focus(); el.select(); }})()")
    page.call("Input.insertText", text=text)
    press_enter(page)
    time.sleep(0.5)
    click(page, ".modal .modal-title")  # closes the date picker
    return page.js(f"document.querySelector('{selector}').value")


LINES_JS = """[...document.querySelectorAll('REPORT tr[data-id=line]')]
    .filter((tr) => !tr.classList.contains('d-none'))
    .map((tr) => ({
        name: ((tr.querySelector('td.line_name') || {}).innerText || '').trim(),
        cells: [...tr.querySelectorAll('td.line_cell')].map((td) => td.innerText.trim()),
        group: tr.classList.contains('o_azk_tb_group'),
    }))""".replace("REPORT", REPORT)


def lines(page):
    return page.js(LINES_JS)


def bank_end_is(text):
    """JS: the visible Bank row ends (End Balance, Balance column) with ``text``."""
    return fill("(() => { const bank = (LINES).find((l) => l.name.startsWith('101401 Bank'));"
                " return Boolean(bank && bank.cells[8] && bank.cells[8].includes(WANTED)); })()",
                WANTED=text).replace("LINES", LINES_JS)


def visible(name):
    return f"({LINES_JS}).some((l) => l.name.startsWith({json.dumps(name)}))"


def close_dropdowns(page):
    click(page, ".o_control_panel .o_breadcrumb")


def download(page, label, folder, extension, target, menu=None, timeout=240):
    """Click the button (or, with ``menu``, the menu item) ``label`` and wait for the downloaded file."""
    before = set(os.listdir(folder))
    if menu:
        click(page, menu)
        items = ".o-dropdown-item, .dropdown-item"
        page.wait(fill(f"[...document.querySelectorAll('{items}')].some((n) => n.innerText.trim() === WANTED)",
                       WANTED=label), timeout=30)
        click_text(page, items, label)
    else:
        click_text(page, "button", label)
    deadline = time.time() + timeout
    while time.time() < deadline:
        names = set(os.listdir(folder))
        new = [name for name in names - before if name.lower().endswith(extension)]
        if new and not any(name.endswith(".crdownload") for name in names):
            path = os.path.join(folder, new[0])
            size = -1
            while size != os.path.getsize(path):  # wait until the file is complete
                size = os.path.getsize(path)
                time.sleep(1)
            final = os.path.join(folder, target)
            if os.path.exists(final):
                os.remove(final)
            os.replace(path, final)
            return final
        time.sleep(1)
    raise TimeoutError(f"no {extension} file downloaded after {timeout} s")


def rpc(page, model, method, args, context):
    """A JSON-RPC call as the logged-in user; raises with the server's message on an error."""
    answer = page.js(fill("""(async () => {
        const response = await fetch('/web/dataset/call_kw', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({jsonrpc: '2.0', method: 'call', params: {
                model: MODEL, method: METHOD, args: ARGS, kwargs: {context: CONTEXT}}}),
        });
        const data = await response.json();
        return data.error ? {error: (data.error.data && data.error.data.message) || data.error.message}
                          : {result: data.result};
    })()""", MODEL=model, METHOD=method, ARGS=args, CONTEXT=context))
    if "error" in answer:
        raise RuntimeError(f"{model}.{method}: {answer['error']}")
    return answer["result"]


def route_download(page, options, generator, anonymous=False):
    """POST /account_reports as the preview's PDF and XLSX buttons do."""
    answer = page.js(fill("""(async () => {
        const form = new FormData();
        form.append('options', JSON.stringify(OPTIONS));
        form.append('file_generator', GENERATOR);
        const response = await fetch('/account_reports', {method: 'POST', body: form, credentials: CREDENTIALS});
        const bytes = new Uint8Array(await response.arrayBuffer());
        let binary = '';
        for (let i = 0; i < bytes.length; i += 8192) {
            binary += String.fromCharCode.apply(null, bytes.subarray(i, i + 8192));
        }
        return {status: response.status, type: response.headers.get('content-type') || '',
                url: response.url, body: btoa(binary)};
    })()""", OPTIONS=options, GENERATOR=generator, CREDENTIALS="omit" if anonymous else "same-origin"))
    answer["body"] = base64.b64decode(answer["body"])
    return answer


def route_error(answer):
    """The server error of a refused download.

    The standard route answers a refused download with HTTP 200 and a JSON
    error body (HTML-escaped), which the browser's download helper shows.
    """
    try:
        error = json.loads(html.unescape(answer["body"].decode("utf-8")))
        return error["data"]["name"], error["data"]["message"]
    except (ValueError, KeyError, TypeError, UnicodeDecodeError):
        return None, None


def check_xlsx(source, result):
    """Compare an XLSX with the engine result: codes, the nine numbers, totals, number types and formats."""
    import openpyxl
    sheet = openpyxl.load_workbook(source).worksheets[0]
    rows = list(sheet.iter_rows())
    header = next(index for index, row in enumerate(rows) if row[0].value == "Code")
    data = [row for row in rows[header + 1:] if any(cell.value is not None for cell in row)]
    per_currency = [row for row in data if str(row[1].value or "").startswith("Total in ")]
    main = [row for row in data if not str(row[1].value or "").startswith("Total in ")]
    expected = [((row["group_code"] if row["type"] == "group" else row["account_code"]) or None,
                 tuple(row[key] for key in AMOUNT_KEYS)) for row in result["lines"]]
    expected.append((None, tuple(result["totals"][key] for key in AMOUNT_KEYS)))
    got = [(row[0].value or None, tuple(cell.value for cell in row[2:11])) for row in main]
    same = got == expected and (sorted(row[11].value for row in per_currency)
                                == sorted(total["amount_currency"] for total in result["currency_totals"]))
    cells = [cell for row in data for cell in row[2:11] if cell.value is not None]
    typed = all(isinstance(cell.value, (int, float)) and cell.number_format == AMOUNT_FORMAT for cell in cells)
    texts = all(isinstance(row[0].value, (str, type(None))) and isinstance(row[1].value, (str, type(None)))
                for row in data)
    return same, typed and texts, len(data), sheet.freeze_panes


def read_pdf(source, png_prefix=None):
    """Text and page count of a PDF (a path or bytes); optionally render each page to PNG."""
    import pymupdf
    document = pymupdf.open(source) if isinstance(source, str) else pymupdf.open(stream=source, filetype="pdf")
    text = "\n".join(page.get_text() for page in document)
    if png_prefix:
        for number, page in enumerate(document, start=1):
            page.get_pixmap(dpi=100).save(f"{png_prefix}_p{number}.png")
    count = document.page_count
    document.close()
    return text, count


def row_text(flat, label):
    """The PDF text after ``label`` up to the next account row or Total."""
    start = flat.find(label)
    if start < 0:
        return ""
    rest = flat[start + len(label):]
    end = re.search(r" \d{6} | Total", rest)
    return rest[:end.start()] if end else rest[:300]


def option_set_checks(page, output, report_id, company_id, analytic_id):
    """Step 9: real PDF and XLSX from the download route for every option set."""
    context = {"allowed_company_ids": [company_id]}
    for name, values in OPTION_SETS.items():
        values = dict(values)
        date_from = values.pop("date_from", "2026-01-01")
        date_to = values.pop("date_to", "2026-01-31")
        drafts = values.pop("drafts", False)
        if values.pop("analytic", None):
            values["analytic_account_id"] = analytic_id
        options = rpc(page, "account.report", "get_options", [[report_id], {
            "date": {"date_from": date_from, "date_to": date_to, "mode": "range", "filter": "custom"},
            "all_entries": drafts, "unfold_all": True, "azk_tb": {"company_id": company_id, **values},
        }], context)
        result = rpc(page, "azk_dynamic_trial_balance.engine", "compute", [{
            "date_from": date_from, "date_to": date_to, "company_id": company_id,
            "include_unposted": drafts, **values,
        }], context)
        slug = name.replace(" ", "_")
        xlsx = route_download(page, options, "export_to_xlsx")
        pdf = route_download(page, options, "export_to_pdf")
        with open(os.path.join(output, "downloads", f"route_{slug}.xlsx"), "wb") as handle:
            handle.write(xlsx["body"])
        with open(os.path.join(output, "downloads", f"route_{slug}.pdf"), "wb") as handle:
            handle.write(pdf["body"])
        files_ok = (xlsx["status"], pdf["status"]) == (200, 200) and xlsx["body"][:2] == b"PK" \
            and pdf["body"][:4] == b"%PDF"
        try:
            same, typed, count, _frozen = check_xlsx(io.BytesIO(xlsx["body"]), result) if files_ok else (
                False, False, 0, None)
            text, pages = read_pdf(pdf["body"]) if files_ok else ("", 0)
        except ImportError:
            skip(f"option set {name!r}", "openpyxl or PyMuPDF is not installed")
            continue
        flat = " ".join(text.split())
        labels = [f"{row['account_code']} {row['account_name']}" for row in result["leaf_rows"]]
        if values.get("hierarchy_only_parents"):
            labels = [row["group_name"] for row in result["lines"]]
        missing = [label for label in labels if label not in flat]
        bank = row_text(flat, "101401 Bank")
        bank_ok = True
        if name == "posted only":
            bank_ok = "1,200.00" in bank
        elif name == "with drafts":
            bank_ok = "1,000.00" in bank and "1,200.00" not in bank
        report(f"option set {name!r}: XLSX equals the engine, PDF holds every row",
               files_ok and same and typed and not missing and "Total" in flat and bank_ok,
               f"{len(result['leaf_rows'])} leaf rows, {count} XLSX rows, {pages} PDF page(s), "
               f"missing in PDF {missing[:3]}, Bank row {bank[:60]!r}")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    output = os.path.abspath(sys.argv[1])
    login, password = os.environ.get("PM_UI_LOGIN"), os.environ.get("PM_UI_PASSWORD")
    if not login or not password:
        sys.exit("BLOCKED: set PM_UI_LOGIN and PM_UI_PASSWORD")
    downloads = os.path.join(output, "downloads")
    os.makedirs(downloads, exist_ok=True)
    profile = tempfile.mkdtemp(prefix="tb_ui_profile_")
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

        # 1. Log in, make the demo company the active one, open the wizard.
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
        company = page.js("(document.querySelector('.modal div[name=company_id] input') || {}).value"
                          " || (document.querySelector('.modal div[name=company_id]') || {}).innerText || ''")
        date_from = set_date(page, "date_from", "01/01/2026")
        date_to = set_date(page, "date_to", "01/31/2026")
        page.js("document.querySelector('.modal div[name=skip_zero_balance] input[type=checkbox]').click()")
        time.sleep(0.5)
        page.screenshot(os.path.join(output, "stage09_wizard.png"))
        page.js("document.querySelector('.modal-footer button[name=action_preview]').click()")
        page.wait(f"document.querySelector('{REPORT} tr[data-id=line]') !== null", timeout=120)
        page.wait(bank_end_is("1,200.00"), timeout=60)
        bank = next(line for line in lines(page) if line["name"].startswith("101401 Bank"))
        report("Preview opens the report: Bank ends at 1,200.00 with posted entries only",
               DEMO_COMPANY in company and (date_from, date_to) == ("01/01/2026", "01/31/2026"),
               f"company {company.strip()!r}, dates {date_from} to {date_to}, Bank cells {bank['cells']}")
        page.screenshot(os.path.join(output, "stage09_preview_posted.png"))

        # 2. Draft Entries: the report is recalculated.
        click(page, "#filter_extra_options button")
        page.wait("document.querySelector('.filter_show_draft_hook') !== null", timeout=30)
        click(page, ".filter_show_draft_hook")
        page.wait(bank_end_is("1,000.00"), timeout=90)
        close_dropdowns(page)
        bank = next(line for line in lines(page) if line["name"].startswith("101401 Bank"))
        report("Draft Entries recalculates the report: Bank ends at 1,000.00", True, f"Bank cells {bank['cells']}")
        page.screenshot(os.path.join(output, "stage09_preview_drafts.png"))

        # 3. Search.
        page.js("document.querySelector('.o_searchview_input').focus()")
        page.call("Input.insertText", text="bank")
        page.wait(f"!{visible('600000 Expenses')} && {visible('101401 Bank')}", timeout=30)
        shown = [line["name"] for line in lines(page)]
        page.screenshot(os.path.join(output, "stage09_preview_search.png"))
        page.js("""(() => { const el = document.querySelector('.o_searchview_input');
            el.value = ''; el.dispatchEvent(new Event('input', {bubbles: true})); })()""")
        page.wait(visible("600000 Expenses"), timeout=30)
        report("search keeps Bank and hides the other rows; clearing it shows them again", True,
               f"rows shown while searching: {shown}")

        # 4. Hierarchy, then fold and unfold a group.
        click(page, ".o_azk_tb_structure_toggle")
        page.wait("document.querySelector('.o_azk_tb_hierarchy') !== null", timeout=30)
        click(page, ".o_azk_tb_hierarchy")
        page.wait(f"document.querySelector('{REPORT} tr.o_azk_tb_group') !== null", timeout=90)
        close_dropdowns(page)
        page.wait(bank_end_is("1,000.00"), timeout=30)
        groups = [line["name"] for line in lines(page) if line["group"]]
        page.screenshot(os.path.join(output, "stage09_preview_hierarchy.png"))
        click_text(page, f"{REPORT} td.line_name", "10140 Bank Accounts")
        page.wait(f"!{visible('101401 Bank')}", timeout=30)
        page.screenshot(os.path.join(output, "stage09_preview_folded.png"))
        click_text(page, f"{REPORT} td.line_name", "10140 Bank Accounts")
        page.wait(visible("101401 Bank"), timeout=30)
        report("Hierarchy and Subtotals adds group rows; folding 10140 hides Bank, unfolding shows it",
               "1 Assets" in groups and "10140 Bank Accounts" in groups, f"groups {groups}")

        # 5. Downloads with the current selection (drafts, hierarchy, skip zero).
        pdf_short = download(page, "PDF", downloads, ".pdf", "stage09_preview_short.pdf")
        # The standard buttons bar shows PDF; "Download Excel" is in the gear menu.
        xlsx = download(page, "Download Excel", downloads, ".xlsx", "stage09_preview.xlsx",
                        menu=".o_control_panel button:has(> i.fa-cog)")
        with open(pdf_short, "rb") as handle:
            pdf_ok = handle.read(4) == b"%PDF"
        with open(xlsx, "rb") as handle:
            xlsx_ok = handle.read(2) == b"PK"
        report("PDF and Download Excel download a PDF and an XLSX file", pdf_ok and xlsx_ok,
               f"{os.path.basename(pdf_short)}, {os.path.basename(xlsx)}")
        context = {"allowed_company_ids": [company_id]}
        result = rpc(page, "azk_dynamic_trial_balance.engine", "compute", [{
            "date_from": "2026-01-01", "date_to": "2026-01-31", "company_id": company_id,
            "include_unposted": True, "skip_zero_balance": True, "hierarchy_subtotals": True,
        }], context)
        try:
            same, typed, count, frozen = check_xlsx(xlsx, result)
            report("the downloaded XLSX equals the engine result (codes, nine numbers, totals)", same,
                   f"{count} rows incl. Total, engine {len(result['lines'])} lines + Total")
            report("XLSX amounts are numbers with a number format, codes and names are text; header frozen",
                   typed and bool(frozen), f"freeze panes at {frozen}")
        except ImportError:
            skip("XLSX content against the engine", "openpyxl is not installed")
        try:
            text, pages = read_pdf(pdf_short, os.path.join(output, "stage09_pdf_short"))
            flat = " ".join(text.split())
            wanted = ["101401 Bank", "1,000.00", DEMO_COMPANY, "Posted and draft", "Initial Balance",
                      "End Balance"]
            missing = [entry for entry in wanted if entry not in flat]
            report("the short PDF holds the Bank row, the company and the options", not missing,
                   f"{pages} page(s), missing {missing}")
        except ImportError:
            skip("PDF text and rendering", "PyMuPDF is not installed")

        # 6. A multipage PDF: every account, without Skip Zero Balance.
        click(page, ".o_azk_tb_structure_toggle")
        page.wait("document.querySelector('.o_azk_tb_skip_zero') !== null", timeout=30)
        rows_before = len(lines(page))
        click(page, ".o_azk_tb_skip_zero")
        page.wait(f"({LINES_JS}).length > {rows_before}", timeout=90)
        close_dropdowns(page)
        pdf_long = download(page, "PDF", downloads, ".pdf", "stage09_preview_multipage.pdf")
        try:
            text, pages = read_pdf(pdf_long, os.path.join(output, "stage09_pdf_multipage"))
            headers = text.count("Initial Balance")
            report("without Skip Zero Balance the PDF has several pages, each with the column header",
                   pages > 1 and headers >= pages, f"{pages} pages, header printed {headers} times")
        except ImportError:
            skip("multipage PDF", "PyMuPDF is not installed")

        # 7. No results: an account prefix that matches no account.
        click(page, ".o_azk_tb_accounts_toggle")
        page.wait("document.querySelector('.o_azk_tb_prefixes') !== null", timeout=30)
        page.js("document.querySelector('.o_azk_tb_prefixes').focus()")
        page.call("Input.insertText", text="8")
        page.js("document.querySelector('.o_azk_tb_prefixes').dispatchEvent(new Event('change', {bubbles: true}))")
        page.wait(f"[...document.querySelectorAll('{REPORT} .alert')]"
                  ".some((n) => n.innerText.includes('No journal items match these options'))", timeout=90)
        close_dropdowns(page)
        message = page.js(f"[...document.querySelectorAll('{REPORT} .alert')].map((n) => n.innerText.trim())"
                          ".find((t) => t.includes('No journal items'))")
        page.screenshot(os.path.join(output, "stage09_preview_empty.png"))
        report("an account prefix without accounts shows the no-results message", True, message[:120])

        # 8. The download route: tampered options, no session.
        report_id = rpc(page, "ir.model.data", "search_read", [[
            ("module", "=", "azk_dynamic_trial_balance"), ("name", "=", "dynamic_trial_balance_report"),
        ], ["res_id"]], context)[0]["res_id"]
        good = rpc(page, "account.report", "get_options", [[report_id], {
            "date": {"date_from": "2026-01-01", "date_to": "2026-01-31", "mode": "range", "filter": "custom"},
            "azk_tb": {"company_id": company_id, "skip_zero_balance": True},
        }], context)
        tampered = route_download(page, {**good, "azk_tb": {**good["azk_tb"], "account_prefixes": ["1%"]}},
                                  "export_to_pdf")
        anonymous = route_download(page, good, "export_to_xlsx", anonymous=True)
        error_name, error_message = route_error(tampered)
        report("the download route refuses tampered options and gives no file without a session",
               tampered["body"][:4] != b"%PDF" and error_name == "odoo.exceptions.ValidationError"
               and anonymous["body"][:2] != b"PK" and "/web/login" in anonymous["url"],
               f"tampered prefix: HTTP {tampered['status']} with {error_name}: {(error_message or '')[:90]!r}; "
               f"no session: HTTP {anonymous['status']} {anonymous['type'].split(';')[0]} "
               f"at {anonymous['url'].replace(BASE, '')[:40]}")

        # 9. Every option set through the real route, against the engine.
        analytic_id = rpc(page, "account.analytic.account", "search_read", [[
            ("name", "=", "Sales Department"), ("company_id", "=", company_id)], ["id"]], context)[0]["id"]
        option_set_checks(page, output, report_id, company_id, analytic_id)

        errors = [error for error in page.errors if error]
        report("no JavaScript error in the browser", not errors, "; ".join(errors)[:300])
    except Exception as error:  # report the step that failed, then stop
        report("unexpected failure", False, f"{type(error).__name__}: {error}")
        try:
            page.screenshot(os.path.join(output, "stage09_failure.png"))
        except Exception:  # noqa: BLE001 - the browser may be gone
            pass
    finally:
        try:
            page.ws.close()
        finally:
            process.kill()
            process.wait(timeout=30)
            shutil.rmtree(profile, ignore_errors=True)
    print(f"{sum(results)} of {len(results)} checks passed, {len(not_run)} not run")
    sys.exit(0 if results and all(results) and not not_run else 1)


if __name__ == "__main__":
    main()
