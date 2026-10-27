# Product

<!-- impeccable:product-schema 1 -->

## Platform

Desktop application (PyQt6), Windows and macOS. Not web: native Qt widgets styled with QSS.

## Users

The treasurer of the BDE ODIN student association (IUT d'Annecy), entering the association's money movements through the year and preparing the financial report presented at the general assembly (AG). The report is signed by the outgoing and incoming president and treasurer, so a successor treasurer also reads and takes over the data.

## Product Purpose

Keep the association's treasury in one place (bank current account, savings account, cash boxes, SumUp) and produce, without manual spreadsheet work, the AG financial report in the exact layout the association already uses (`Bilan financier.xlsx`).

## Operating Context

- Entries are typed in batches from bank statements, cash sheets and receipts: date, label, amount, category, optional third party and invoice reference.
- The financial year is not the calendar year (the 2026 report covers April 2025 to March 2026).
- The deliverable is an Excel workbook: one ledger per account (Débit / Crédit, monthly subtotals and balances) and a one-page summary with signature boxes, printed for the AG.

## Capabilities and Constraints

- Accounts with an opening balance; income, expense and internal transfer operations; categories with one level of sub-categories (shown as « dont … » lines).
- Amounts stored in cents; the database lives in the user's data folder and v1 databases are migrated automatically.
- Two switchable themes: Cyberpunk (default) and Classique.
- French interface and code comments.

## Brand Commitments

- The Cyberpunk theme reuses the owner's portfolio identity (D:\Code\Website_International): VS Code « Cyberpunk 2077 » palette, Cyberpunk / Oxanium / Blender Pro fonts, cut corners, scanline grid. It must stay switchable.
- The Classique theme is a sober light theme following standard UX rules.
- The Excel export follows the association's existing workbook layout.

## Evidence on Hand

- `Bilan financier.xlsx` (owner's Downloads): the reference layout for the export.
- Portfolio fonts copied into `resources/fonts/`.

## Product Principles

1. The AG report is the product: every screen exists to make that report correct.
2. Errors are explained where they happen, with the fix, never as a blocking pop-up.
3. Destructive actions are confirmed and name what will be lost.
4. Brand lives in details; controls stay standard and predictable.
