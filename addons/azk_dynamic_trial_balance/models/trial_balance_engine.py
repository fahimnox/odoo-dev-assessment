"""Dynamic Trial Balance calculation engine (Stage 08).

One server-side service computes the report from the normalized options and
returns one plain result. Every output (Preview, PDF and XLSX, Stage 09)
renders that result and computes no numbers of its own. The rules are in
docs/calculation_contract.md; "contract N" below refers to its sections.

Everything runs as the calling user. The amounts come from three grouped
queries on account.move.line (movement, opening, carry-forward) through
``_read_group``, which checks access rights and applies every record rule,
so journal items the user may not read never reach a total. There is no
sudo() and no SQL. The number of queries does not depend on the number of
accounts.
"""
from collections import defaultdict

from odoo import api, fields, models
from odoo.exceptions import AccessError
from odoo.osv import expression

from .report_options import normalize_options

# The nine numbers of every row and of the totals (contract 6).
AMOUNT_KEYS = (
    "initial_debit", "initial_credit", "initial_balance",
    "debit", "credit", "balance",
    "ending_debit", "ending_credit", "ending_balance",
)
NO_GROUP_ID = "group-none"


def like_prefix_pattern(prefix):
    """Return an '=like' pattern that matches ``prefix`` literally at the start.

    Prefixes are validated to the account-code alphabet first (D-44), so they
    hold no wildcard; escaping them anyway keeps "_" and "%" literal even if
    a future caller skips that validation.
    """
    escaped = prefix.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return escaped + "%"


class TrialBalanceEngine(models.AbstractModel):
    _name = "azk_dynamic_trial_balance.engine"
    _description = "Dynamic Trial Balance calculation"

    @api.model
    def compute(self, options):
        """Validate raw ``options`` and return the report as plain data.

        ``options`` may come from the wizard or from a client, so they are
        validated again here (``normalize_options``): an unknown key, a
        wrong type, a company the user may not use, or a journal or analytic
        account outside that company is refused before any query runs.

        The result is a dictionary of plain values:

        - ``filters``: the normalized options, with display names;
        - ``lines``: the rows in display order (group rows and account
          rows, as the hierarchy options ask);
        - ``leaf_rows``: every shown account row (one per account, or per
          account and transaction currency), whatever the hierarchy options;
        - ``hierarchy_rows``: the group rows, in display order;
        - ``totals``: the nine numbers summed over ``leaf_rows`` only;
        - ``currency_totals``: one total per transaction currency (Show
          Amount Currency only);
        - ``warnings`` and ``metadata``.
        """
        if not (self.env.su or self.env.user.has_group("account.group_account_readonly")):
            raise AccessError(self.env._(
                "The Dynamic Trial Balance needs read access to accounting."
            ))
        opts = normalize_options(self.env, options)
        company = self.env["res.company"].browse(opts["company_id"])
        # Account codes and groups are company-dependent: read them in the
        # report company (V-06). check_company already made it active.
        return self.with_company(company)._compute(opts)

    # ------------------------------------------------------------------
    # Steps
    # ------------------------------------------------------------------
    def _compute(self, opts):
        company = self.env.company
        currency = company.currency_id
        date_from = fields.Date.to_date(opts["date_from"])
        date_to = fields.Date.to_date(opts["date_to"])
        fy_start = company.compute_fiscalyear_dates(date_from)["date_from"]
        by_currency = opts["show_amount_currency"]

        accounts = self._accounts_in_scope(opts)
        scope = self._scope_domain(opts)
        # A prefix selects account rows (contract 7). Restricting the items
        # to those accounts gives the same rows with less work; the
        # carry-forward below deliberately ignores it (D-15).
        account_filter = [("account_id", "in", accounts.ids)] if opts["account_prefixes"] else []

        sums = defaultdict(lambda: {"opening": 0.0, "debit": 0.0, "credit": 0.0, "amount_currency": 0.0})
        self._add_movement(sums, scope, account_filter, date_from, date_to, by_currency)
        self._add_opening(sums, scope, account_filter, date_from, fy_start, by_currency)
        warnings = []
        earnings, carry_forward = self._add_carry_forward(
            sums, scope, accounts, opts, fy_start, by_currency, warnings)
        if not opts["skip_zero_balance"]:
            self._add_accounts_without_items(sums, accounts, by_currency)

        leaf_rows = self._leaf_rows(sums, by_currency)
        if opts["skip_zero_balance"]:
            leaf_rows = [row for row in leaf_rows if not self._is_zero_row(row)]
        leaf_rows.sort(key=lambda row: (row["account_code"] or "", row["currency_name"] or "", row["account_id"]))

        if opts["hierarchy_subtotals"]:
            lines, hierarchy_rows = self._hierarchy(leaf_rows, opts, warnings)
        else:
            lines, hierarchy_rows = list(leaf_rows), []

        totals = self._sum_amounts(leaf_rows)
        return {
            "filters": self._filters(opts),
            "lines": lines,
            "leaf_rows": leaf_rows,
            "hierarchy_rows": hierarchy_rows,
            "totals": totals,
            "currency_totals": self._currency_totals(leaf_rows) if by_currency else [],
            "warnings": warnings,
            "metadata": {
                "company_id": company.id,
                "company_name": company.name,
                "currency_id": currency.id,
                "currency_name": currency.name,
                "date_from": opts["date_from"],
                "date_to": opts["date_to"],
                "fiscal_year_start": fields.Date.to_string(fy_start),
                "earnings_account_id": earnings.id or None,
                "carry_forward": carry_forward,
                "balanced": all(
                    currency.is_zero(totals[debit] - totals[credit])
                    for debit, credit in (("initial_debit", "initial_credit"), ("debit", "credit"),
                                          ("ending_debit", "ending_credit"))
                ),
                "leaf_count": len(leaf_rows),
            },
        }

    def _chart_accounts(self, domain=()):
        """Accounts of the report company's chart matching ``domain``, searched as the user.

        Ordered by id on purpose. The default order of account.account in
        this build ("code, placeholder_code") joins each account to its first
        company among the user's own companies. A branch shares the accounts
        of its root company, and Odoo 18 lets a user access a branch without
        its root: for that user the join drops every shared account, so a
        search with the default order finds none of them, although the
        record rules let the user count and read them (Stage 10,
        docs/review_findings.md, RF-06). Rows are sorted by code later.
        """
        Account = self.env["account.account"]
        return Account.search([*Account._check_company_domain(self.env.company), *domain], order="id")

    def _accounts_in_scope(self, opts):
        """The company's accounts whose code starts with a prefix (all if none).

        Only the report company's chart is searched, so accounts of other
        companies never match a prefix. Deprecated accounts are included
        here; they are listed only when they have amounts (D-12).
        """
        domain = []
        if opts["account_prefixes"]:
            domain = expression.OR([
                [("code", "=like", like_prefix_pattern(prefix))] for prefix in opts["account_prefixes"]
            ])
        return self._chart_accounts(domain)

    def _scope_domain(self, opts):
        """The journal items in scope, for opening, carry-forward and movement alike (contract 4)."""
        domain = [
            ("company_id", "=", self.env.company.id),
            ("display_type", "not in", ("line_section", "line_note")),
            # Posted always; drafts on request; cancelled never (the
            # standard report's own condition).
            ("parent_state", "!=", "cancel") if opts["include_unposted"] else ("parent_state", "=", "posted"),
        ]
        if opts["journal_id"]:
            domain.append(("journal_id", "=", opts["journal_id"]))
        if opts["analytic_account_id"]:
            # Whole-item selection (contract 9): the analytic mixin turns
            # this into an overlap test on the distribution's account ids,
            # composite keys included, so each item counts once, in full.
            domain.append(("analytic_distribution", "in", [opts["analytic_account_id"]]))
        return domain

    def _groupby(self, by_currency):
        return ["account_id", "currency_id"] if by_currency else ["account_id"]

    def _key(self, account, currency, by_currency):
        return (account.id, currency.id if by_currency else None)

    def _add_movement(self, sums, scope, account_filter, date_from, date_to, by_currency):
        """Gross debit and credit of the period, both dates included (contract 5)."""
        domain = expression.AND([scope, account_filter, [("date", ">=", date_from), ("date", "<=", date_to)]])
        aggregates = ["debit:sum", "credit:sum"] + (["amount_currency:sum"] if by_currency else [])
        for group in self.env["account.move.line"]._read_group(domain, self._groupby(by_currency), aggregates):
            if by_currency:
                account, row_currency, debit, credit, amount_currency = group
            else:
                (account, debit, credit), row_currency, amount_currency = group, None, 0.0
            values = sums[self._key(account, row_currency, by_currency)]
            values["debit"] += debit
            values["credit"] += credit
            values["amount_currency"] += amount_currency

    def _add_opening(self, sums, scope, account_filter, date_from, fy_start, by_currency):
        """Opening balances (contract 5).

        Balance-sheet accounts: everything before Date From. Income and
        expense accounts: only from the fiscal-year start, so nothing when
        Date From is that start. This is the standard report's condition.
        """
        domain = expression.AND([
            scope, account_filter, [("date", "<", date_from)],
            ["|", ("date", ">=", fy_start), ("account_id.include_initial_balance", "=", True)],
        ])
        for group in self.env["account.move.line"]._read_group(domain, self._groupby(by_currency), ["balance:sum"]):
            if by_currency:
                account, row_currency, balance = group
            else:
                (account, balance), row_currency = group, None
            sums[self._key(account, row_currency, by_currency)]["opening"] += balance

    def _add_carry_forward(self, sums, scope, accounts, opts, fy_start, by_currency, warnings):
        """Earlier years' income and expense, shown on Current Year Earnings (contract 5).

        A presentation, as in the standard report: no journal entry is
        created. It sums every income and expense account in scope, whatever
        the prefixes, and is shown only when the earnings account itself is
        in the report (D-15).
        """
        earnings = self._chart_accounts([("account_type", "=", "equity_unaffected")])[:1]
        if earnings and opts["account_prefixes"] and earnings not in accounts:
            return earnings, None
        domain = expression.AND([
            scope, [("date", "<", fy_start), ("account_id.include_initial_balance", "=", False)],
        ])
        [(balance,)] = self.env["account.move.line"]._read_group(domain, [], ["balance:sum"])
        currency = self.env.company.currency_id
        carry_forward = currency.round(balance or 0.0)
        if currency.is_zero(carry_forward):
            return earnings, 0.0
        if not earnings:
            warnings.append({
                "code": "no_earnings_account",
                "message": self.env._(
                    "The company has no Current Year Earnings account, so the result of earlier "
                    "fiscal years (%(amount)s) is not shown.",
                    amount=carry_forward,
                ),
            })
            return earnings, carry_forward
        sums[self._key(earnings, currency, by_currency)]["opening"] += carry_forward
        return earnings, carry_forward

    def _add_accounts_without_items(self, sums, accounts, by_currency):
        """Without Skip Zero Balance, every non-deprecated account is listed (D-12)."""
        listed = {account_id for account_id, _currency in sums}
        company_currency = self.env.company.currency_id
        for account in accounts:
            if account.id not in listed and not account.deprecated:
                key = self._key(account, account.currency_id or company_currency, by_currency)
                sums[key].update(opening=0.0)  # creates the all-zero row

    def _accounts_by_id(self, account_ids):
        """Map ids to records that share one prefetch set.

        Records browsed one by one would each compute ``code`` and
        ``group_id`` (company-dependent, not stored) in their own query;
        iterating one recordset computes them for all accounts at once.
        """
        return {account.id: account for account in self.env["account.account"].browse(list(account_ids))}

    def _leaf_rows(self, sums, by_currency):
        """Turn the sums into account rows with their nine numbers (contract 6)."""
        Currency = self.env["res.currency"]
        accounts = self._accounts_by_id({account_id for account_id, _currency in sums})
        rows = []
        for (account_id, currency_id), values in sums.items():
            account = accounts[account_id]
            row_currency = Currency.browse(currency_id) if currency_id else Currency
            row = {
                "id": f"account-{account_id}" + (f"-{currency_id}" if currency_id else ""),
                "type": "account",
                "level": 1,
                "parent_id": None,
                "account_id": account_id,
                "account_code": account.code,
                "account_name": account.name,
                "group_id": None,
                "currency_id": currency_id,
                "currency_name": row_currency.name or None,
                "currency_symbol": row_currency.symbol or None,
                "amount_currency": row_currency.round(values["amount_currency"]) if by_currency else None,
            }
            row.update(self._amounts(values["opening"], values["debit"], values["credit"]))
            if by_currency and row_currency.is_zero(row["amount_currency"]):
                row["amount_currency"] = 0.0
            rows.append(row)
        return rows

    def _amounts(self, opening, debit, credit):
        """The nine numbers: opening and ending show the net side, movement is gross."""
        currency = self.env.company.currency_id

        def clean(amount):
            amount = currency.round(amount)
            return 0.0 if currency.is_zero(amount) else amount

        opening, debit, credit = clean(opening), clean(debit), clean(credit)
        balance = clean(debit - credit)
        ending = clean(opening + balance)
        # Written out rather than max(), which can return -0.0.
        return {
            "initial_debit": opening if opening > 0 else 0.0,
            "initial_credit": -opening if opening < 0 else 0.0,
            "initial_balance": opening,
            "debit": debit,
            "credit": credit,
            "balance": balance,
            "ending_debit": ending if ending > 0 else 0.0,
            "ending_credit": -ending if ending < 0 else 0.0,
            "ending_balance": ending,
        }

    def _is_zero_row(self, row):
        """Skip Zero Balance hides a row only when nothing at all happened on it (D-48).

        Gross debit and credit count as activity, so an account whose debit
        and credit movements cancel out stays visible.
        """
        currency = self.env.company.currency_id
        if any(not currency.is_zero(row[key])
               for key in ("initial_balance", "debit", "credit", "ending_balance")):
            return False
        return not row["amount_currency"]

    def _sum_amounts(self, rows):
        currency = self.env.company.currency_id
        totals = dict.fromkeys(AMOUNT_KEYS, 0.0)
        for row in rows:
            for key in AMOUNT_KEYS:
                totals[key] += row[key]
        return {key: currency.round(value) + 0.0 for key, value in totals.items()}

    def _currency_totals(self, leaf_rows):
        """One total per transaction currency; currencies are never added together (contract 8)."""
        Currency = self.env["res.currency"]
        per_currency = defaultdict(lambda: {"amount_currency": 0.0, "debit": 0.0, "credit": 0.0, "balance": 0.0})
        for row in leaf_rows:
            values = per_currency[row["currency_id"]]
            values["amount_currency"] += row["amount_currency"]
            for key in ("debit", "credit", "balance"):
                values[key] += row[key]
        company_currency = self.env.company.currency_id
        result = []
        for currency_id, values in per_currency.items():
            row_currency = Currency.browse(currency_id)
            result.append({
                "currency_id": currency_id,
                "currency_name": row_currency.name,
                "currency_symbol": row_currency.symbol,
                "amount_currency": row_currency.round(values["amount_currency"]) + 0.0,
                "debit": company_currency.round(values["debit"]) + 0.0,
                "credit": company_currency.round(values["credit"]) + 0.0,
                "balance": company_currency.round(values["balance"]) + 0.0,
            })
        return sorted(result, key=lambda values: values["currency_name"])

    def _hierarchy(self, leaf_rows, opts, warnings):
        """Group rows from the account-group tree (contract 10).

        Each shown account row is added once to each of its ancestor
        groups; accounts without a group go to "(No Group)". Group rows sum
        the displayed debit and credit of their account rows separately, as
        the standard hierarchy does. Totals never use group rows. With
        Hierarchy Only Parents, only group rows of the chosen level or
        higher are listed, and each still holds every account below it.
        """
        currency = self.env.company.currency_id
        accounts = self._accounts_by_id({row["account_id"] for row in leaf_rows})
        nodes = {}

        def node(group):
            node_id = f"group-{group.id}" if group else NO_GROUP_ID
            if node_id not in nodes:
                nodes[node_id] = {
                    "row": {
                        "id": node_id,
                        "type": "group",
                        "level": 1,
                        "parent_id": None,
                        "group_id": group.id or None,
                        "group_code": group.code_prefix_start or None,
                        "group_name": group.display_name if group else self.env._("(No Group)"),
                        "amount_currency": None,
                        **dict.fromkeys(AMOUNT_KEYS, 0.0),
                    },
                    "sort_key": group.code_prefix_start or "",
                    "children": [],
                    "is_group": bool(group),
                }
            return nodes[node_id]

        for row in leaf_rows:
            group = accounts[row["account_id"]].group_id
            chain = []
            while group:
                chain.append(group)
                group = group.parent_id
            chain = chain or [self.env["account.group"]]
            for depth, group in enumerate(reversed(chain), start=1):
                group_node = node(group)
                group_node["row"]["level"] = depth
                for key in AMOUNT_KEYS:
                    group_node["row"][key] += row[key]
            for child, parent in zip(chain, chain[1:]):
                child_node, parent_node = node(child), node(parent)
                if child_node["row"]["parent_id"] is None:
                    child_node["row"]["parent_id"] = parent_node["row"]["id"]
                    parent_node["children"].append(("group", child_node))
            leaf_parent = node(chain[0])
            row["group_id"] = chain[0].id or None
            row["parent_id"] = leaf_parent["row"]["id"]
            row["level"] = leaf_parent["row"]["level"] + 1
            leaf_parent["children"].append(("account", row))

        for group_node in nodes.values():
            for key in AMOUNT_KEYS:
                group_node["row"][key] = currency.round(group_node["row"][key]) + 0.0

        if leaf_rows and NO_GROUP_ID in nodes and len(nodes) == 1:
            warnings.append({
                "code": "no_account_groups",
                "message": self.env._(
                    "No account of this report belongs to an account group, so every account is "
                    "shown under (No Group)."
                ),
            })

        max_level = opts["account_level"] if opts["hierarchy_only_parents"] else None
        lines, hierarchy_rows = [], []

        def child_sort_key(child):
            kind, item = child
            if kind == "group":
                return (item["sort_key"], 0, item["row"]["id"])
            return (item["account_code"] or "", 1, item["currency_name"] or "", item["account_id"])

        def emit(group_node):
            hierarchy_rows.append(group_node["row"])
            lines.append(group_node["row"])
            for kind, item in sorted(group_node["children"], key=child_sort_key):
                if kind == "group":
                    if max_level is None or item["row"]["level"] <= max_level:
                        emit(item)
                elif max_level is None:
                    lines.append(item)

        roots = sorted((n for n in nodes.values() if n["is_group"] and n["row"]["parent_id"] is None),
                       key=lambda n: (n["sort_key"], n["row"]["id"]))
        if NO_GROUP_ID in nodes:
            roots.append(nodes[NO_GROUP_ID])
        for root in roots:
            emit(root)
        return lines, hierarchy_rows

    def _filters(self, opts):
        """The normalized options, with the names an output prints."""
        journal = self.env["account.journal"].browse(opts["journal_id"] or [])
        analytic = self.env["account.analytic.account"].browse(opts["analytic_account_id"] or [])
        return {
            **opts,
            "company_name": self.env.company.name,
            "journal_name": journal.display_name or None,
            "analytic_account_name": analytic.display_name or None,
        }
