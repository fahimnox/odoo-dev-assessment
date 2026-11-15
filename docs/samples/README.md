# Sample exports (Stage 09)

Real files produced on 2026-11-15 by `scripts/tb_preview_smoke_check.py` (browser check run 3, final code) on the development database `azk_ee24`, for the installed demo company "AZK Trial Balance Demo (EGP)", period 01/01/2026 to 01/31/2026. The data is the module's demo data only; the files contain no user name, URL or local path (checked with PyMuPDF and by reading the XLSX parts).

| File | Produced by | Options |
|---|---|---|
| `stage09_trial_balance_short.pdf` | the preview's PDF button | Draft Entries, Hierarchy and Subtotals, Skip Zero Balance (one page) |
| `stage09_trial_balance_multipage.pdf` | the preview's PDF button | Draft Entries, Hierarchy and Subtotals, without Skip Zero Balance (three pages, the column header on each) |
| `stage09_trial_balance.xlsx` | the preview's gear menu, "Download Excel" | as the short PDF |
| `stage09_trial_balance_amount_currency.pdf` | the download route `/account_reports`, as the PDF button calls it | posted only, Show Amount Currency, Skip Zero Balance |
| `stage09_trial_balance_amount_currency.xlsx` | the same route, `export_to_xlsx` | as the PDF above |

What to look for:

- Bank (101401) ends at 1,200.00 with posted entries only (the amount-currency files) and at 1,000.00 with drafts (the other files).
- The PDF header states the company, the period and every option; with drafts the title starts with "[DRAFT]".
- The XLSX lists the same options above the table, has codes and names as text, amounts as numbers with a number format, and a frozen header. The amount-currency workbook keeps one row per account and currency, a separate Currency column, and one total per currency.

PNG renders of these PDFs and screenshots of the preview are in [../screenshots/](../screenshots/) (`stage09_*.png`).
