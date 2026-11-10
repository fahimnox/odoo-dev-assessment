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


def ensure_reader(env):
    """Raise AccessError unless the current user may read Partner Monitor data.

    Used by RPC entry points that aggregate data themselves (the dashboard),
    on top of the read access rules the ORM applies.
    """
    if not env.su and not env.user.has_group(READER_GROUP):
        raise AccessError(env._("Only Partner Monitor readers can see this dashboard."))


# Project-size buckets of the average project size (decision D-05): half-open
# intervals, so 4.99 is below 5, 5 starts the second bucket, and 25 belongs to
# the last bucket only. An unknown average has its own bucket. The keys start
# with their position: grouped queries (and so the graph views) order a
# selection by its stored key, and this keeps the intervals in order.
PROJECT_SIZE_BUCKETS = [
    ("1_below_5", "Below 5"),
    ("2_5_to_11", "5 to below 11"),
    ("3_11_to_25", "11 to below 25"),
    ("4_25_plus", "25 and above"),
    ("5_unknown", "Unknown"),
]


def project_size_bucket(average, known):
    """The bucket key of an average project size (None or not known: "5_unknown")."""
    if not known or average is None:
        return "5_unknown"
    if average < 5:
        return "1_below_5"
    if average < 11:
        return "2_5_to_11"
    if average < 25:
        return "3_11_to_25"
    return "4_25_plus"


def ensure_manager(env):
    """Raise AccessError unless the current user is a Partner Monitor manager.

    Manager actions change sync data that no access rule lets users write
    directly. They call this check first, then write with a narrow sudo().
    The cron engine runs in superuser mode and passes the check.
    """
    if not env.su and not env.user.has_group(MANAGER_GROUP):
        raise AccessError(env._("Only Partner Monitor managers can do this."))
