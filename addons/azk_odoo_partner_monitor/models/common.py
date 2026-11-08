"""Constants and helpers shared by the Partner Monitor models."""

from odoo.exceptions import AccessError

READER_GROUP = "azk_odoo_partner_monitor.group_reader"
MANAGER_GROUP = "azk_odoo_partner_monitor.group_manager"

# Partner statuses in rank order: Ready < Silver < Gold (docs/architecture.md 5.3).
STATUS_SELECTION = [("ready", "Ready"), ("silver", "Silver"), ("gold", "Gold")]
STATUS_RANK = {key: rank for rank, (key, _label) in enumerate(STATUS_SELECTION, start=1)}


def ensure_manager(env):
    """Raise AccessError unless the current user is a Partner Monitor manager.

    Manager actions change sync data that no access rule lets users write
    directly. They call this check first, then write with a narrow sudo().
    The cron engine runs in superuser mode and passes the check.
    """
    if not env.su and not env.user.has_group(MANAGER_GROUP):
        raise AccessError(env._("Only Partner Monitor managers can do this."))
