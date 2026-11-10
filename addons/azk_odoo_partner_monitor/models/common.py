"""Constants and helpers shared by the Partner Monitor models."""

from datetime import timedelta

from odoo.exceptions import AccessError

READER_GROUP = "azk_odoo_partner_monitor.group_reader"
MANAGER_GROUP = "azk_odoo_partner_monitor.group_manager"

# Partner statuses in rank order: Ready < Silver < Gold (docs/architecture.md 5.3).
STATUS_SELECTION = [("ready", "Ready"), ("silver", "Silver"), ("gold", "Gold")]
STATUS_RANK = {key: rank for rank, (key, _label) in enumerate(STATUS_SELECTION, start=1)}

# Outcome of the last validation of a country's listing or a partner's
# references (docs/resilience.md).
VALIDATION_STATES = [
    ("unchecked", "Not checked yet"),
    ("matched", "Matched"),
    ("mismatch", "Mismatch"),
]

# Retry budget shared by failed work items and by validation re-scrapes:
# at most 5 tries, 15 minutes after the first failure, then doubling, never
# more than 24 hours apart (docs/resilience.md, "Retries").
MAX_ATTEMPTS = 5
RETRY_BASE = timedelta(minutes=15)
RETRY_CAP = timedelta(hours=24)


def retry_delay(attempt):
    """Delay before the next try after ``attempt`` tries (1-based): 15, 30, 60, 120 min, ..."""
    return min(RETRY_BASE * 2 ** max(attempt - 1, 0), RETRY_CAP)


def ensure_manager(env):
    """Raise AccessError unless the current user is a Partner Monitor manager.

    Manager actions change sync data that no access rule lets users write
    directly. They call this check first, then write with a narrow sudo().
    The cron engine runs in superuser mode and passes the check.
    """
    if not env.su and not env.user.has_group(MANAGER_GROUP):
        raise AccessError(env._("Only Partner Monitor managers can do this."))
