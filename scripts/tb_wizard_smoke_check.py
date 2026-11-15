"""Dynamic Trial Balance wizard smoke check in a real browser (Stage 07).

Uses the DevTools helpers of scripts/ui_smoke_check.py (headless Chrome or
Edge on the machine that runs it) against the local web server. Credentials
come from the environment (PM_UI_LOGIN, PM_UI_PASSWORD) and are never
printed. Optional: PM_UI_URL, PM_UI_BROWSER.

Usage: python scripts/tb_wizard_smoke_check.py OUTPUT_DIR

Steps, each reported as PASS or FAIL:
  1. log in, open the Accounting app, then Reporting > Dynamic Trial Balance
     from the menu: the wizard opens in a dialog with the notice that the
     outputs are not connected yet;
  2. the dialog shows the assessment's fields; Hierarchy Only Parents
     appears only after Hierarchy and Subtotals is ticked, and Account Level
     Up To only after Hierarchy Only Parents is ticked;
  3. a typed account prefix becomes a tag;
  4. Preview shows the "not available yet" message;
  5. no JavaScript error.
"""

import json
import os
import shutil
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ui_smoke_check import BASE, Page, report, results, start_browser  # noqa: E402

APP_XMLID = "accountant.menu_accounting"
REPORTING_XMLID = "account.menu_finance_reports"
MENU_XMLID = "azk_dynamic_trial_balance.menu_dynamic_trial_balance"
EXPECTED_LABELS = [
    "Date From", "Date To", "Posted Entries", "Include Unposted Entries",
    "Hierarchy and Subtotals", "Skip Zero Balance", "Show Amount Currency",
    "Accounts", "Journals",
]


def dialog_facts(page):
    return page.js("""(() => {
        const dialog = document.querySelector('.modal .o_form_view');
        const has = (name) => Boolean(dialog && dialog.querySelector(`div[name=${name}]`));
        return {
            open: Boolean(dialog),
            title: (document.querySelector('.modal .modal-title') || {}).innerText || '',
            // A label with a help text ends with a "?" marker.
            labels: dialog ? [...dialog.querySelectorAll('.o_form_label')]
                .map((n) => n.innerText.trim().replace(/\\s*\\?$/, '')) : [],
            postedTicked: Boolean(dialog && dialog.querySelector('div[name=posted_entries] input:checked')),
            notice: dialog ? ((dialog.querySelector('.alert-warning') || {}).innerText || '') : '',
            onlyParents: has('hierarchy_only_parents'),
            level: has('account_level'),
            buttons: [...document.querySelectorAll('.modal-footer button')].map((n) => n.innerText.trim()),
            tags: dialog ? [...dialog.querySelectorAll('div[name=account_prefix_ids] .o_tag')].map((n) => n.innerText.trim()) : [],
            moduleError: (document.querySelector('.o_module_error') || {}).innerText || '',
        };
    })()""")


def tick(page, field):
    page.js(f"document.querySelector('.modal div[name={field}] input[type=checkbox]').click()")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    output = os.path.abspath(sys.argv[1])
    login, password = os.environ.get("PM_UI_LOGIN"), os.environ.get("PM_UI_PASSWORD")
    if not login or not password:
        sys.exit("BLOCKED: set PM_UI_LOGIN and PM_UI_PASSWORD")
    os.makedirs(output, exist_ok=True)
    profile = tempfile.mkdtemp(prefix="tb_ui_profile_")
    process, ws_url = start_browser(profile)
    page = Page(ws_url)
    try:
        page.call("Runtime.enable")
        page.call("Page.enable")
        page.call("Emulation.setDeviceMetricsOverride", width=1400, height=1000, deviceScaleFactor=1, mobile=False)

        # 1. Log in, open the Accounting app, then the menu item.
        page.goto(f"{BASE}/web/login")
        page.wait("document.querySelector('input[name=login]') !== null", timeout=180)
        page.js(f"""(() => {{
            document.querySelector('input[name=login]').value = {json.dumps(login)};
            document.querySelector('input[name=password]').value = {json.dumps(password)};
            document.querySelector('form.oe_login_form').submit();
        }})()""")
        page.wait("location.pathname.startsWith('/odoo')", timeout=240)
        page.goto(f"{BASE}/odoo")
        app = f".o_app[data-menu-xmlid=\"{APP_XMLID}\"]"
        page.wait(f"document.querySelector('{app}') !== null", timeout=90)
        page.js(f"document.querySelector('{app}').click()")
        reporting = f"[data-menu-xmlid=\"{REPORTING_XMLID}\"]"
        page.wait(f"document.querySelector('{reporting}') !== null", timeout=90)
        page.js(f"document.querySelector('{reporting}').click()")
        item = f"[data-menu-xmlid=\"{MENU_XMLID}\"]"
        page.wait(f"document.querySelector('{item}') !== null", timeout=30)
        menu_text = page.js(f"document.querySelector('{item}').innerText.trim()")
        page.js(f"document.querySelector('{item}').click()")
        page.wait("document.querySelector('.modal .o_form_view') !== null", timeout=60)
        time.sleep(1)
        facts = dialog_facts(page)
        report("no asset or module loading error", not facts["moduleError"], facts["moduleError"][:200])
        report("the menu opens the wizard in a dialog",
               facts["open"] and facts["title"] == "Dynamic Trial Balance",
               f"menu item {menu_text!r}, dialog title {facts['title']!r}")
        report("the dialog says the outputs are not connected yet",
               "not connected yet" in facts["notice"], facts["notice"][:120])

        # 2. Fields, and the options that depend on other options.
        missing = [label for label in EXPECTED_LABELS if label not in facts["labels"]]
        hidden_at_start = not facts["onlyParents"] and not facts["level"]
        report("Posted Entries is ticked in the new form", facts["postedTicked"])
        tick(page, "hierarchy_subtotals")
        page.wait("document.querySelector('.modal div[name=hierarchy_only_parents]') !== null", timeout=30)
        tick(page, "hierarchy_only_parents")
        page.wait("document.querySelector('.modal div[name=account_level]') !== null", timeout=30)
        facts = dialog_facts(page)
        report("the assessment's fields are shown; dependent options appear in order",
               not missing and hidden_at_start and facts["onlyParents"] and facts["level"],
               f"labels {facts['labels']}, missing {missing}, buttons {facts['buttons']}")
        tick(page, "hierarchy_only_parents")
        page.wait("document.querySelector('.modal div[name=account_level]') === null", timeout=30)

        # 3. Type a prefix and create it as a tag.
        page.js("document.querySelector('.modal div[name=account_prefix_ids] input').focus()")
        page.call("Input.insertText", text="10")
        page.wait("[...document.querySelectorAll('.o-autocomplete--dropdown-item')]"
                  ".some((n) => n.innerText.includes('Create'))", timeout=30)
        page.js("[...document.querySelectorAll('.o-autocomplete--dropdown-item')]"
                ".find((n) => n.innerText.includes('Create')).querySelector('a, button, .dropdown-item, span').click()")
        page.wait("document.querySelectorAll('.modal div[name=account_prefix_ids] .o_tag').length === 1", timeout=30)
        facts = dialog_facts(page)
        report("a typed prefix becomes a tag", facts["tags"] == ["10"], f"tags {facts['tags']}")
        page.screenshot(os.path.join(output, "stage07_wizard.png"))

        # 4. Preview: the options are valid, the output is not built yet.
        page.js("document.querySelector('.modal-footer button[name=action_preview]').click()")
        page.wait("[...document.querySelectorAll('.modal .modal-body')]"
                  ".some((n) => n.innerText.includes('not available yet'))", timeout=60)
        message = page.js("[...document.querySelectorAll('.modal .modal-body')]"
                          ".map((n) => n.innerText.trim()).find((t) => t.includes('not available yet'))")
        report("Preview says the output is not available yet", "options are valid" in message, message[:160])
        page.screenshot(os.path.join(output, "stage07_wizard_preview_message.png"))

        errors = [error for error in page.errors if error]
        report("no JavaScript error in the browser", not errors, "; ".join(errors)[:300])
    except Exception as error:  # report the step that failed, then stop
        report("unexpected failure", False, f"{type(error).__name__}: {error}")
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
