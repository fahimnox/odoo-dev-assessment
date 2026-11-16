"""Access checks over HTTP as non-admin and unauthorized users (Stage 11 acceptance).

Each user logs in to the running web server with its own session and calls the
same endpoints the web client calls: JSON-RPC (/web/dataset/call_kw) and the
report download route (/account_reports), which the preview's PDF and XLSX
buttons use. Python standard library only.

Users come from scripts/acceptance_users.py; their shared password is read
from ACC_PASSWORD and never printed. The administrator (PM_UI_LOGIN,
PM_UI_PASSWORD) only creates the wizard that another user then tries to read.
Optional: ACC_URL (default http://127.0.0.1:8071), ACC_DB (default azk_ee24).

Usage: python scripts/acceptance_access_check.py
Every check prints PASS or FAIL; the exit code is 1 if one failed.
"""
import http.cookiejar
import html
import json
import os
import sys
import urllib.parse
import urllib.request

BASE = os.environ.get("ACC_URL", "http://127.0.0.1:8071").rstrip("/")
DB = os.environ.get("ACC_DB", "azk_ee24")
PASSWORD = os.environ.get("ACC_PASSWORD")
ADMIN = (os.environ.get("PM_UI_LOGIN"), os.environ.get("PM_UI_PASSWORD"))
results = []


def report(name, ok, detail=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}: {name}" + (f" -- {detail}" if detail else ""), flush=True)


class Session:
    """One logged-in browser-like session (cookie jar)."""

    def __init__(self, login=None, password=None):
        self.login = login or "anonymous"
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        self.uid = None
        if login:
            answer = self.rpc("/web/session/authenticate", {"db": DB, "login": login, "password": password})
            if "error" in answer:
                raise RuntimeError(f"login {login}: {answer['error']}")
            self.uid = answer["result"]["uid"]

    def rpc(self, path, params):
        body = json.dumps({"jsonrpc": "2.0", "method": "call", "params": params, "id": 1}).encode()
        request = urllib.request.Request(BASE + path, data=body, headers={"Content-Type": "application/json"})
        with self.opener.open(request, timeout=300) as response:
            data = json.loads(response.read())
        if "error" in data:
            error = data["error"].get("data", {})
            return {"error": (error.get("name", "?"), error.get("message", data["error"].get("message", "")))}
        return {"result": data["result"]}

    def call(self, model, method, args, kwargs=None, context=None):
        kwargs = dict(kwargs or {})
        if context:
            kwargs["context"] = context
        return self.rpc(f"/web/dataset/call_kw/{model}/{method}",
                        {"model": model, "method": method, "args": args, "kwargs": kwargs})

    def download(self, options, generator):
        """POST /account_reports as the preview's buttons do: (status, content type, final URL, body)."""
        data = urllib.parse.urlencode({"options": json.dumps(options), "file_generator": generator}).encode()
        with self.opener.open(urllib.request.Request(BASE + "/account_reports", data=data), timeout=300) as response:
            return response.status, response.headers.get("Content-Type", ""), response.url, response.read()


def refused(answer):
    return "error" in answer and answer["error"][0] in (
        "odoo.exceptions.AccessError", "odoo.exceptions.UserError", "odoo.exceptions.ValidationError")


def describe(answer):
    if "error" in answer:
        return f"{answer['error'][0].rsplit('.', 1)[-1]}: {answer['error'][1][:110]!r}"
    return f"allowed ({str(answer['result'])[:80]})"


def route_error(body):
    """The standard route answers a refused download with a JSON error body (HTML-escaped)."""
    try:
        error = json.loads(html.unescape(body.decode("utf-8")))
        return error["data"]["name"].rsplit(".", 1)[-1], error["data"]["message"][:110]
    except (ValueError, KeyError, TypeError, UnicodeDecodeError):
        return None, None


def main():
    if not PASSWORD or not all(ADMIN):
        sys.exit("ACC_PASSWORD, PM_UI_LOGIN and PM_UI_PASSWORD are required")
    reader, manager = Session("acc_pm_reader", PASSWORD), Session("acc_pm_manager", PASSWORD)
    tb_reader, nobody = Session("acc_tb_reader", PASSWORD), Session("acc_no_rights", PASSWORD)
    admin = Session(*ADMIN)
    print(f"server {BASE}, database {DB}; logged in: acc_pm_reader, acc_pm_manager, acc_tb_reader, "
          "acc_no_rights and the administrator", flush=True)

    # ---- Partner Monitor --------------------------------------------------
    dashboard = "azk_odoo_partner_monitor.dashboard"
    partner = "azk_odoo_partner_monitor.partner"
    answer = reader.call(dashboard, "get_dashboard_data", [], {"filters": {}})
    ok = "result" in answer and len(answer["result"].get("charts", answer["result"])) > 0
    report("PM reader: the dashboard data is served", ok, describe(answer))
    rows = reader.call(partner, "search_read", [[]], {"fields": ["name", "is_demo"], "limit": 1})
    report("PM reader: partner records can be read", "result" in rows and len(rows["result"]) == 1,
           describe(rows))
    partner_id = rows["result"][0]["id"] if "result" in rows and rows["result"] else 0
    answer = reader.call(partner, "write", [[partner_id], {"name": "changed by a reader"}])
    report("PM reader: writing a partner is refused", refused(answer), describe(answer))
    answer = reader.call("azk_odoo_partner_monitor.sync.run", "action_sync_now", [[]])
    report("PM reader: the manager action Sync Now is refused", refused(answer), describe(answer))
    for user in (nobody, tb_reader):
        answer = user.call(dashboard, "get_dashboard_data", [], {"filters": {}})
        report(f"PM, {user.login} (no Partner Monitor group): the dashboard data is refused",
               refused(answer), describe(answer))
        answer = user.call(partner, "search_read", [[]], {"fields": ["name"], "limit": 1})
        report(f"PM, {user.login}: partner records are refused", refused(answer), describe(answer))
        menus = user.call("ir.ui.menu", "load_menus", [False])
        names = [menu.get("name") for menu in menus.get("result", {}).values()
                 if isinstance(menu, dict)] if "result" in menus else []
        report(f"PM, {user.login}: no Partner Monitor menu", "result" in menus and "Partner Monitor" not in names,
               f"{len(names)} menus visible")
    answer = manager.call("azk_odoo_partner_monitor.sync.run", "action_sync_now", [[]])
    ok = "result" in answer and answer["result"].get("tag") == "display_notification"
    report("PM manager: Sync Now is allowed (it only queues; downloads are paused)", ok,
           describe(answer) if not ok else answer["result"]["params"].get("message", "")[:110])

    # ---- Dynamic Trial Balance ----------------------------------------------
    ids = admin.call("ir.model.data", "search_read", [[
        ("module", "=", "azk_dynamic_trial_balance"), ("name", "in", ("dynamic_trial_balance_report", "demo_company")),
    ], ["name", "res_id"]])["result"]
    ids = {row["name"]: row["res_id"] for row in ids}
    report_id, demo_company = ids["dynamic_trial_balance_report"], ids["demo_company"]
    main_company = admin.call("res.users", "read", [[admin.uid], ["company_id"]])["result"][0]["company_id"][0]
    context = {"allowed_company_ids": [demo_company]}
    period = {"date": {"date_from": "2026-01-01", "date_to": "2026-01-31", "mode": "range", "filter": "custom"}}
    answer = tb_reader.call("account.report", "get_options",
                            [[report_id], {**period, "azk_tb": {"company_id": demo_company}}], {}, context)
    report("TB read-only accountant: the report options are served", "result" in answer, describe(answer)[:80])
    options = answer.get("result", {})
    engine = tb_reader.call("azk_dynamic_trial_balance.engine", "compute", [{
        "date_from": "2026-01-01", "date_to": "2026-01-31", "company_id": demo_company}], {}, context)
    bank = [row for row in engine.get("result", {}).get("leaf_rows", [])
            if (row.get("account_name") or "") == "Bank"]
    report("TB read-only accountant: the engine computes as the user (golden fixture: Bank ends at 1,200.00)",
           bool(bank) and abs(bank[0].get("ending_balance", 0) - 1200.0) < 0.005,
           f"Bank row: {bank[0] if bank else describe(engine)}"[:160])
    if options:
        status, kind, _url, body = tb_reader.download(options, "export_to_pdf")
        report("TB read-only accountant: PDF download", body[:4] == b"%PDF", f"HTTP {status} {kind.split(';')[0]}, "
               f"{len(body)} bytes")
        status, kind, _url, body = tb_reader.download(options, "export_to_xlsx")
        report("TB read-only accountant: XLSX download", body[:2] == b"PK", f"HTTP {status} {kind.split(';')[0]}, "
               f"{len(body)} bytes")
        for label, tampered in (
                ("another company (not allowed for this user)",
                 {**options, "azk_tb": {**options["azk_tb"], "company_id": main_company}}),
                ("a wildcard account prefix", {**options, "azk_tb": {**options["azk_tb"], "account_prefixes": ["1%"]}}),
        ):
            status, kind, _url, body = tb_reader.download(tampered, "export_to_pdf")
            name, message = route_error(body)
            report(f"TB read-only accountant: tampered download refused, {label}",
                   body[:4] != b"%PDF" and name in ("AccessError", "UserError", "ValidationError"),
                   f"HTTP {status}, {name}: {message!r}")
        # Options of the users' own company, made by the administrator: the
        # refusal then comes from the missing Accounting rights, not from the company.
        main_options = admin.call("account.report", "get_options", [[report_id], {
            **period, "azk_tb": {"company_id": main_company}}], {}, {"allowed_company_ids": [main_company]})
        for user in (nobody, reader):
            status, kind, _url, body = user.download(main_options.get("result", {}), "export_to_xlsx")
            name, message = route_error(body)
            report(f"TB, {user.login} (no Accounting group): the download is refused",
                   body[:2] != b"PK" and name is not None, f"HTTP {status}, {name}: {message!r}")
        status, kind, url, body = Session().download(options, "export_to_xlsx")
        report("TB, no session: no file, redirected to the login page",
               body[:2] != b"PK" and "/web/login" in url, f"HTTP {status} at {url.replace(BASE, '')[:40]}")
    wizard = "azk_dynamic_trial_balance.wizard"
    values = {"company_id": demo_company, "date_from": "2026-01-01", "date_to": "2026-01-31"}
    own = tb_reader.call(wizard, "create", [values], {}, context)
    report("TB read-only accountant: creating its own wizard is allowed", "result" in own, describe(own))
    admins = admin.call(wizard, "create", [values], {}, context)
    answer = tb_reader.call(wizard, "read", [[admins.get("result", 0)], ["date_from"]], {}, context)
    report("TB read-only accountant: another user's wizard cannot be read", refused(answer), describe(answer))
    answer = nobody.call(wizard, "create", [{**values, "company_id": main_company}])
    report("TB, acc_no_rights: creating a wizard is refused", refused(answer), describe(answer))
    answer = nobody.call("azk_dynamic_trial_balance.engine", "compute", [{
        "date_from": "2026-01-01", "date_to": "2026-01-31", "company_id": main_company}])
    report("TB, acc_no_rights: the engine is refused", refused(answer), describe(answer))

    print(f"{sum(results)} of {len(results)} checks passed", flush=True)
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
