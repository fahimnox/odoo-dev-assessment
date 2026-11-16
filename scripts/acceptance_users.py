"""Create or update the Stage 11 acceptance users. COMMITTED, disposable databases only.

    docker compose run --rm -T -e ACC_PASSWORD -e ACC_DB_CREATED_AFTER odoo-ee-20241208 \
        odoo shell --database=azk_ee24 --no-http < scripts/acceptance_users.py

The password comes from ACC_PASSWORD and is never printed. Users (login: groups):
- acc_pm_reader: Partner Monitor Reader;
- acc_pm_manager: Partner Monitor Manager; notifications handled in Odoo
  (Discuss inbox), so that it can be the configured recipient of sync notes;
- acc_tb_reader: Accounting read-only (account.group_account_readonly), in the
  Trial Balance demo company only;
- acc_no_rights: an internal user without any Partner Monitor or Accounting group.

Guard: the acceptance database has the same name as the development database
(azk_ee24) in another Compose project, so the name cannot tell them apart. The
script refuses to run unless the database was created on or after
ACC_DB_CREATED_AFTER (YYYY-MM-DD; the creation date of base.user_root).
"""
import os
import sys

# `env` is provided by the Odoo shell.
password = os.environ.get("ACC_PASSWORD")
created_after = os.environ.get("ACC_DB_CREATED_AFTER")
created_on = str(env.ref("base.user_root").create_date.date())  # noqa: F821
if not password or not created_after:
    sys.exit("ACC_PASSWORD and ACC_DB_CREATED_AFTER are required")
if created_on < created_after:
    sys.exit(f"refusing to run on {env.cr.dbname}: created on {created_on}, before {created_after}")  # noqa: F821

demo_company = env.ref("azk_dynamic_trial_balance.demo_company", raise_if_not_found=False)  # noqa: F821
main_company = env.ref("base.main_company")  # noqa: F821
internal = env.ref("base.group_user")  # noqa: F821
specs = {
    "acc_pm_reader": ("Acceptance PM Reader", ["azk_odoo_partner_monitor.group_reader"], main_company),
    "acc_pm_manager": ("Acceptance PM Manager", ["azk_odoo_partner_monitor.group_manager"], main_company),
    "acc_tb_reader": ("Acceptance TB Read-only Accountant", ["account.group_account_readonly"],
                      demo_company),
    "acc_no_rights": ("Acceptance No Rights", [], main_company),
}
Users = env["res.users"].with_context(no_reset_password=True)  # noqa: F821
for login, (name, groups, company) in specs.items():
    if company is None:
        print(f"ACC_USERS {login}: skipped, its company is not installed")
        continue
    group_ids = [internal.id] + [env.ref(xmlid).id for xmlid in groups]  # noqa: F821
    values = {
        "name": name, "login": login, "password": password,
        "company_id": company.id, "company_ids": [(6, 0, [company.id])],
        "groups_id": [(6, 0, group_ids)],
        "notification_type": "inbox" if login == "acc_pm_manager" else "email",
    }
    user = Users.search([("login", "=", login)])
    if user:
        user.write(values)
    else:
        user = Users.create(values)
    names = sorted(user.groups_id.filtered(
        lambda g: g.category_id.name in ("Partner Monitor", "Accounting", "User types")).mapped("full_name"))
    print(f"ACC_USERS {login}: id {user.id}, company {user.company_id.name!r}, groups {names}, "
          f"notifications {user.notification_type}")
env.cr.commit()  # noqa: F821
print("ACC_USERS committed")
