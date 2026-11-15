"""Validation of the Dynamic Trial Balance options.

The wizard turns its fields into one plain, JSON-ready dictionary with
``normalize_options``. The same function is meant to run again wherever
options come back from a client (the report handler of later stages), so
every entry path applies the same rules:

- Date From and Date To are required, and Date From <= Date To;
- the company is one of the user's companies and is active in the company
  switcher (journal items are read through record rules that use the active
  companies);
- the hierarchy options form one of the valid combinations;
- account prefixes are literal code prefixes;
- the journal and the analytic account are readable by the user and usable
  in the company.

The functions take the environment first and translate their messages with
``env._()``, Odoo 18's translation helper for code without ``self``.
The calculation rules themselves are in docs/calculation_contract.md.
"""
from odoo.addons.account.models.account_account import ACCOUNT_CODE_REGEX
from odoo.exceptions import AccessError, ValidationError
from odoo.fields import Date

ACCOUNT_LEVELS = [(str(level), str(level)) for level in range(1, 6)]
# The size of account.account.code.
MAX_PREFIX_LENGTH = 64

BOOLEAN_KEYS = (
    "include_unposted",
    "hierarchy_subtotals",
    "hierarchy_only_parents",
    "skip_zero_balance",
    "show_amount_currency",
)
OPTION_KEYS = frozenset(BOOLEAN_KEYS) | {
    "date_from",
    "date_to",
    "company_id",
    "account_level",
    "account_prefixes",
    "journal_id",
    "analytic_account_id",
}


def clean_prefix(env, value):
    """Return one account-code prefix, trimmed, or raise ValidationError.

    A prefix uses the alphabet of account codes (letters, digits and dots,
    Odoo's ACCOUNT_CODE_REGEX). So "%", "_" and "\\" are refused here: they
    can never start an account code, and they must never act as SQL
    wildcards.
    """
    prefix = value.strip() if isinstance(value, str) else ""
    if not prefix:
        raise ValidationError(env._("An account prefix cannot be empty."))
    if len(prefix) > MAX_PREFIX_LENGTH:
        raise ValidationError(env._(
            "An account prefix can have at most %(max)s characters.",
            max=MAX_PREFIX_LENGTH,
        ))
    if not ACCOUNT_CODE_REGEX.match(prefix):
        raise ValidationError(env._(
            'The account prefix "%(prefix)s" can contain only letters, digits '
            "and dots, like an account code.",
            prefix=prefix,
        ))
    return prefix


def clean_prefixes(env, values):
    """Clean a list of prefixes, keeping the first occurrence of each."""
    if not isinstance(values, (list, tuple)):
        raise ValidationError(env._("The account prefixes must be a list."))
    result = []
    for value in values:
        prefix = clean_prefix(env, value)
        if prefix not in result:
            result.append(prefix)
    return result


def check_combination(env, hierarchy_subtotals, hierarchy_only_parents, account_level,
                      show_amount_currency):
    """Refuse the option combinations the report cannot honour.

    Valid: no hierarchy; Hierarchy and Subtotals; Hierarchy and Subtotals
    with Hierarchy Only Parents and a level from 1 to 5. Include Unposted
    Entries, Skip Zero Balance and the filters combine with all of them.
    Show Amount Currency needs account lines, so it is refused with
    Hierarchy Only Parents.
    """
    if hierarchy_only_parents and not hierarchy_subtotals:
        raise ValidationError(env._("Hierarchy Only Parents needs Hierarchy and Subtotals."))
    if account_level is not None and not hierarchy_only_parents:
        raise ValidationError(env._(
            "Account Level Up To applies only to Hierarchy Only Parents."
        ))
    if hierarchy_only_parents and account_level is None:
        raise ValidationError(env._(
            "Choose an Account Level Up To (1 to 5) for Hierarchy Only Parents."
        ))
    if account_level is not None and account_level not in range(1, 6):
        raise ValidationError(env._("Account Level Up To must be a number from 1 to 5."))
    if hierarchy_only_parents and show_amount_currency:
        raise ValidationError(env._(
            "Show Amount Currency needs account lines, so it cannot be combined "
            "with Hierarchy Only Parents."
        ))


def check_company(env, value):
    """Return the company with id ``value`` if the user may report on it now.

    The user must be allowed to access the company (AccessError otherwise)
    and the company must be active in the company switcher (ValidationError
    otherwise), because journal items are read through record rules that
    use the active companies. The messages do not read the company: its
    record rule hides companies that are not active.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(env._("Choose a company."))
    if not env.su and value not in env.user._get_company_ids():
        raise AccessError(env._("You are not allowed to report on this company."))
    company = env["res.company"].browse(value)
    if company not in env.companies:
        raise ValidationError(env._(
            "The selected company is not active. Select it in the company "
            "switcher, then open the report again."
        ))
    return company


def normalize_options(env, raw):
    """Validate raw option values and return them as a plain dictionary.

    ``raw`` may come from the wizard or from a client, so nothing in it is
    trusted: unknown keys, wrong types, a company the user may not use, and
    records the user cannot read or that belong to another company are all
    refused. Dates come back as ISO strings and records as ids, so the
    result can travel inside the native report options.
    """
    if not isinstance(raw, dict):
        raise ValidationError(env._("The report options are invalid."))
    unknown = set(raw) - OPTION_KEYS
    if unknown:
        raise ValidationError(env._(
            "Unknown report options: %(keys)s",
            keys=", ".join(sorted(str(key) for key in unknown)),
        ))

    date_from = _date(env, raw.get("date_from"), "date_from")
    date_to = _date(env, raw.get("date_to"), "date_to")
    if date_from > date_to:
        raise ValidationError(env._("Date From must be on or before Date To."))

    company = check_company(env, raw.get("company_id"))
    flags = {key: _boolean(env, raw.get(key), key) for key in BOOLEAN_KEYS}
    level = _level(env, raw.get("account_level"))
    check_combination(
        env,
        flags["hierarchy_subtotals"],
        flags["hierarchy_only_parents"],
        level,
        flags["show_amount_currency"],
    )
    journal = _company_record(env, "account.journal", raw.get("journal_id"), company)
    analytic = _company_record(
        env, "account.analytic.account", raw.get("analytic_account_id"), company
    )
    return {
        "date_from": Date.to_string(date_from),
        "date_to": Date.to_string(date_to),
        "company_id": company.id,
        **flags,
        "account_level": level,
        "account_prefixes": clean_prefixes(env, raw.get("account_prefixes") or []),
        "journal_id": journal.id or None,
        "analytic_account_id": analytic.id or None,
    }


def _date(env, value, key):
    if value:
        try:
            return Date.to_date(value)
        except (TypeError, ValueError):
            pass
    label = env._("Date From") if key == "date_from" else env._("Date To")
    if not value:
        raise ValidationError(env._("%(field)s is required.", field=label))
    raise ValidationError(env._("%(field)s is not a valid date.", field=label))


def _boolean(env, value, key):
    if value is None:
        return False
    if not isinstance(value, bool):
        raise ValidationError(env._("The option %(key)s must be true or false.", key=key))
    return value


def _level(env, value):
    if value in (None, False, ""):
        return None
    if isinstance(value, str) and value.isdigit():
        value = int(value)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(env._("Account Level Up To must be a number from 1 to 5."))
    return value


def _company_record(env, model, value, company):
    """Return the record, searched as the user and limited to the company.

    The search applies the user's access rights and record rules, and the
    model's own company rule (_check_company_domain: the company, its parent
    companies, or shared records).
    """
    records = env[model].with_context(active_test=False)
    if value in (None, False):
        return records
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(env._("The selected %(model)s is invalid.", model=records._description))
    record = records.search(
        [("id", "=", value), *records._check_company_domain(company)], limit=1
    )
    if not record:
        raise ValidationError(env._(
            "The selected %(model)s is not available in the report's company.",
            model=records._description,
        ))
    return record
