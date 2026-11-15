# Prepare the disposable test database for the analytic browser check (Stage 10).
#
#     docker compose run --rm -T -e TB_RO_PASSWORD odoo-ee-20241208 \
#         odoo shell --database=azk_ee24_test --no-http < scripts/tb_analytic_setup.py
#
# On azk_ee24_test only (after the Trial Balance tests installed the module
# with its demo data), and COMMITTED there:
#   - turns on Odoo's Analytic Accounting setting (Accounting > Settings), so
#     the wizard's and the preview's analytic selectors are shown;
#   - sets web.base.url to the temporary server's address (TB_BASE_URL,
#     default http://127.0.0.1:8072), where wkhtmltopdf fetches the PDF styles;
#   - creates or updates a read-only accountant, login tb_readonly, with the
#     password in TB_RO_PASSWORD (never printed), in the demo company only.
import os

assert env.cr.dbname == "azk_ee24_test", f"refusing to run on {env.cr.dbname}: azk_ee24_test only"
password = os.environ.get("TB_RO_PASSWORD")
assert password, "set TB_RO_PASSWORD"
base_url = os.environ.get("TB_BASE_URL", "http://127.0.0.1:8072")

env["res.config.settings"].create({"group_analytic_accounting": True}).execute()
env["ir.config_parameter"].set_param("web.base.url", base_url)
demo = env.ref("azk_dynamic_trial_balance.demo_company")
groups = [env.ref("base.group_user").id, env.ref("account.group_account_readonly").id]
values = {"name": "TB Read-only Accountant", "password": password, "company_id": demo.id,
          "company_ids": [(6, 0, demo.ids)], "groups_id": [(6, 0, groups)]}
user = env["res.users"].with_context(active_test=False).search([("login", "=", "tb_readonly")])
if user:
    user.write(values)
else:
    user = env["res.users"].create({"login": "tb_readonly", **values})
env.cr.commit()
analytic = env.ref("analytic.group_analytic_accounting")
print("TB_SETUP analytic accounting for internal users:", analytic in env.ref("base.group_user").implied_ids)
print("TB_SETUP read-only user:", user.login, "accounting read-only", user.has_group("account.group_account_readonly"),
      "accounting user", user.has_group("account.group_account_invoice"), "analytic", user.has_group(
          "analytic.group_analytic_accounting"), "companies", user.company_ids.mapped("name"))
print("TB_SETUP web.base.url:", env["ir.config_parameter"].get_param("web.base.url"))
