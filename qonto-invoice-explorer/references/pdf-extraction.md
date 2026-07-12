# PDF extraction

Loaded when the agent has a PDF in hand and needs to pull vendor, amount, currency, date, and invoice number out of it. The extraction lives in `scripts/extract_pdf.py` and the patterns below.

## Base command

The whole file assumes `pdftotext -layout <file> -` was run first. The `-layout` flag preserves column alignment, which most Stripe-hosted invoices rely on for the amount column.

## Vendor

The first non-blank line after `Invoice number ...` or `Facture n° ...` is almost always the vendor on Stripe-hosted invoices. French utilities put the vendor in a bordered header at the top of the page. When the layout is ambiguous, the "Bill to" section holds the buyer's identity — anything above it and to the left is the seller.

## Amount and currency

The reliable patterns are `Amount due <n> USD|EUR|GBP`, `Total <n> EUR|€|USD|$`, and the French `Montant TTC <n> €`. Numbers can carry a comma decimal (`70,80`) or a dot decimal; normalize to dot before comparing. When both an amount and a `local_amount` appear in a Stripe-hosted layout, prefer the "amount due" line since it matches what the vendor actually charged.

```python
patterns = [
    r"Amount due\s+([\d,]+\.\d{2})\s+(USD|EUR|GBP)",
    r"Total\s+([\d,]+[.,]\d{2})\s*(EUR|€|USD|\$|GBP|£)?",
    r"(?:€|EUR)\s*([\d,]+[.,]\d{2})\s+(?:due|paid|TTC)",
    r"([\d,]+,\d{2})\s*€",                    # French comma decimal
    r"\$\s*([\d,]+\.\d{2})\s+USD\s+(?:due|paid)",
]
```

## Date

English dates use `Date of issue <Month> <D>, <YYYY>`. French dates use `Facture du <D> <mois> <YYYY>` or the numeric `DD/MM/YYYY`. ISO dates appear on statements. When the PDF is a monthly statement rather than an invoice, use the statement's END date plus two days as the effective charge date — that's the pattern Google Cloud follows.

```python
patterns = [
    r"Date of issue\s+(\w+\s+\d{1,2},?\s+\d{4})",
    r"(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})",
    r"(\d{4})-(\d{2})-(\d{2})",
    r"(\d{2})/(\d{2})/(\d{4})",
]
```

## Invoice number

`Invoice number <ID>`, `Facture n° <ID>`, or `Reçu #<ID>` on Stripe receipts. When present it's the strongest disambiguation signal for two same-amount invoices in the same month.

## Non-PDF sources

Some suppliers, especially foreign B2B ones, send proformas as `.xls` (Office 97-2003 CDF-V2) instead of PDF. `pdftotext` fails; `xlrd` extracts the sheet, and `datetime(1899,12,30) + timedelta(days=int(v))` decodes Excel serial dates. Convert to PDF via `fpdf` before attaching so the accountant gets a readable document. Modern `.xlsx` uses `openpyxl` instead of `xlrd`. See `modality-messaging.md` for the broker-side pattern.

## When extraction is ambiguous

The rule is to surface the ambiguity, not resolve it. If two amounts look plausible for the "total" (e.g. subtotal and total-with-VAT), report both and let the matcher's tolerance decide which one aligns with the Qonto transaction. If the vendor name can't be pulled reliably from the header, fall back to matching by amount + date + a keyword from the Qonto label.
