/** @odoo-module */

// Filters of the Dynamic Trial Balance preview (Stage 09).
//
// The standard filter bar of account_reports keeps its date filter, Draft
// Entries and Unfold All options and its search bar. This extension adds the
// wizard's own options: the hierarchy, Only Parents and its level, Skip Zero
// Balance, Show Amount Currency, account prefixes, one journal and one
// analytic account. Each change reloads the report, so the server validates
// the options again and the engine recalculates.

import { _t } from "@web/core/l10n/translation";
import { WarningDialog } from "@web/core/errors/error_dialogs";
import { AccountReport } from "@account_reports/components/account_report/account_report";
import { AccountReportFilters } from "@account_reports/components/account_report/filters/filters";

// The alphabet of account codes, as checked on the server (D-44).
const PREFIX_PATTERN = /^[A-Za-z0-9.]{1,64}$/;

export class TrialBalanceFilters extends AccountReportFilters {
    static template = "azk_dynamic_trial_balance.TrialBalanceFilters";

    get tbOptions() {
        return this.controller.options.azk_tb;
    }

    get tbChoices() {
        return this.controller.options.azk_tb_choices || { journals: [], analytic_accounts: [] };
    }

    get tbPrefixesText() {
        return this.tbOptions.account_prefixes.join(", ");
    }

    get tbJournalName() {
        const journal = this.tbChoices.journals.find((choice) => choice.id === this.tbOptions.journal_id);
        return journal ? journal.name : _t("All journals");
    }

    get tbAnalyticName() {
        const account = this.tbChoices.analytic_accounts.find(
            (choice) => choice.id === this.tbOptions.analytic_account_id
        );
        return account ? account.name : _t("All analytic accounts");
    }

    // Apply ``values`` to our options, keeping the combinations the server
    // accepts (D-43, D-46), then reload the report.
    async setTbOptions(values) {
        const next = { ...this.tbOptions, ...values };
        if (!next.hierarchy_subtotals) {
            next.hierarchy_only_parents = false;
        }
        if (values.show_amount_currency) {
            next.hierarchy_only_parents = false;
        }
        if (next.hierarchy_only_parents) {
            next.show_amount_currency = false;
            next.account_level = next.account_level || 1;
        } else {
            next.account_level = null;
        }
        await this.controller.updateOption("azk_tb", next);
        await this.applyFilters("azk_tb");
    }

    toggleTb(key) {
        return this.setTbOptions({ [key]: !this.tbOptions[key] });
    }

    async setPrefixes(ev) {
        const prefixes = [...new Set(ev.target.value.split(/[\s,;]+/).filter(Boolean))];
        const invalid = prefixes.find((prefix) => !PREFIX_PATTERN.test(prefix));
        if (invalid) {
            this.dialog.add(WarningDialog, {
                title: _t("Invalid account prefix"),
                message: _t(
                    'The account prefix "%s" can contain only letters, digits and dots, like an account code.',
                    invalid
                ),
            });
            ev.target.value = this.tbPrefixesText;
            return;
        }
        await this.setTbOptions({ account_prefixes: prefixes });
    }
}

AccountReport.registerCustomComponent(TrialBalanceFilters);
