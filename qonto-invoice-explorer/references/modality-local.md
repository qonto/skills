# Local modality

Loaded when the user hands the agent a path — a folder, a zip, or a single file — that contains invoices to attach.

## Ask for the path

The prompt is simply "point me to the folder, zip, or file that contains the receipts for this vendor". Handle a single PDF, a zip (`unzip -o -d /tmp/qonto-inv/<vendor>/ <path>`), or a directory recursed for `*.pdf` (skip `.DS_Store` and the `._*` macOS metadata artefacts). Photos and screenshots are processed only if the user explicitly says "these are receipts" — otherwise the risk of grabbing unrelated images is too high.

## Extraction

`pdftotext -layout <file> -` is the base command. The `-layout` flag preserves column alignment, which most Stripe-hosted invoice regexes rely on. Full extraction patterns are in `pdf-extraction.md`.

## Photo fallback

When the user has a photo of a paper receipt (`.jpg`, `.png`, `.heic`), the fastest path is to ask them to open it in macOS Preview and "Export as PDF". `tesseract image.png -` OCRs directly at around 60% accuracy on receipts — good enough for amount-plus-date matching but not for a fiscal document. `.heic` needs `magick input.heic output.png` first.

iCloud Photos isn't accessible programmatically on a Mac: `icloudpd` fails because Apple blocks app-specific passwords on the Photos API, `Photos.sqlite` needs Full Disk Access permission, and `find` on the `Photos Library.photoslibrary` bundle is TCC-restricted. When the receipt is on the user's iPhone, they have to AirDrop the individual file.

## Dedup and naming

Users hand the agent the same invoice under three filenames sometimes. Dedup by `(vendor, amount, date, invoice_number)`; keep the first found, log the others. Rename each PDF to a canonical form before uploading so Qonto's attachment list stays readable — `<Vendor>-<YYYY-MM-DD>-<AmountCurrency>-<InvoiceNumber>.pdf` works well.

## Multi-invoice PDFs

Occasionally a single PDF holds several invoices on separate pages (a landlord sending a quarterly bundle). Split with `qpdf --split-pages input.pdf out-%d.pdf` and process each page individually. Warn the user this is happening.

## `.xls` and `.xlsx` invoices

Some foreign suppliers send PIs as legacy Excel `.xls` (Composite Document File V2, Office 97-2003). `pdftotext` fails; use `xlrd`. Excel serial dates decode via `datetime(1899,12,30) + timedelta(days=int(v))`. Convert to PDF with `fpdf` before attaching so the accountant gets a readable document; uploading `.xls` directly works (`application/vnd.ms-excel`) but is less clean. Modern `.xlsx` uses `openpyxl` instead of `xlrd`.

```python
from fpdf import FPDF
pdf = FPDF(); pdf.add_page(); pdf.set_font("Courier", size=9)
for row_text in extracted_rows:
    pdf.multi_cell(0, 4, row_text.encode("latin-1","replace").decode("latin-1"))
pdf.output(out_path)
```

## User-provided bundle shapes

Common export shapes from vendor portals: Alibaba ships a zip like `208551.zip` containing `220<n>_<order_id>_receipt.pdf`, matched by `Amount paid\s*(?:EUR|USD)\s*<value>` and `Order number:\s*#?(\d+)`. Fiverr ships `invoices.zip` containing both an `FC<n>.pdf` (Charge) and an `FI<n>.pdf` (Invoice) per order — dedup by transaction. Google Cloud statements come in `google-payments-document-center-download_<ts>.zip` containing `<12-digit-acctID>_YYYYMMDD.pdf`. WhatsApp broker exports follow `<PREFIX>-<CLIENT>-YYYYMMDD-<seq>-<desc>-<amount><CCY>.pdf` — see `modality-messaging.md`. A catch-all `justificatifs.zip` from the user often mixes landlord invoices, notary receipts, and refund PDFs from unrelated vendors; inspect content, never trust filenames.

## Trust content over labels

The user says "all the utility bills are in this thread" and the attachment turns out to be an accidentally-forwarded SaaS receipt. `pdftotext` first. Never trust the folder name, email subject, or the user's description alone.
