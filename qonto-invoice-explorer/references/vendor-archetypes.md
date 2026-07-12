# Vendor archetypes — taxonomy + retrieval recipes

Rather than a fixed list of vendors (which becomes stale and business-specific), this file classifies vendors into **archetypes** that share invoice-delivery patterns. When you encounter a new vendor, identify its archetype first, then apply the corresponding recipe.

## The 8 archetypes

| # | Archetype | Modality (default → fallback) | Signal |
|---|---|---|---|
| A1 | **Stripe-hosted SaaS** | email → browser | Sender is `invoice+statements@<vendor>.com` OR `invoice+statements+acct_<hash>@stripe.com`. PDF filename `Invoice-XXXXXXXX-NNNN.pdf`. Currency often USD. |
| A2 | **Non-Stripe direct-email SaaS** | email → browser | Sender is vendor-specific (e.g. `billing@vendor.com`). PDF attached to email. |
| A3 | **Dashboard-only SaaS** | browser | No emailed PDF, invoice list only accessible after login on `<vendor>.com/settings/billing`. Common for enterprise-tier SaaS. |
| A4 | **Foreign-currency B2B SWIFT** | messaging + local | Overseas suppliers or freelance partners paid by wire. PIs sent via WhatsApp/LinkedIn DM. Filename convention set by the sender. USD or another non-base currency. |
| A5 | **Domestic utility / paper-first vendor** | local (user forwards) | Landlord, tax notary, utility company. Monthly PDF sent via email or postal. User has it locally or in a specific mail thread. |
| A6 | **Payment aggregator (PayPal / Stripe direct)** | local + email fallback | Charge appears as `PAYPAL *MERCHANT` or `STRIPE *SOMETHING`. Underlying vendor's invoice needs to be traced via the aggregator's dashboard OR user's PayPal/Stripe export. |
| A7 | **Marketplace / commerce platform** | browser (export CSV) → per-bill browser | Shopify, Amazon Marketplace, etsy: invoice list is a CSV export from admin panel; per-bill PDFs behind cookie auth on the same domain. |
| A8 | **Qonto-native-covered vendor** | qonto_native | Vendor appears in Qonto's Invoice Collector / Amazon Business / receipts@ forwarding catalog. Best path is to instruct the user to enable that native integration once. |

## Recipe per archetype

### A1 — Stripe-hosted SaaS

**Detection**: Search all user mailboxes with `any_email=invoice+statements`. Every hit is either A1 or A2. If sender ends with `@mail.stripe.com` or contains `+acct_`, it's A1.

**Retrieval**:
1. Unipile `from=invoice+statements@<vendor>.com` (or `+acct_<hash>@stripe.com`)
2. Download PDF attachment; check first 4 bytes = `%PDF`
3. Parse with the Stripe-hosted regex family (see `pdf-extraction.md`)

**Currency**: often USD. Match on `local_amount` + `local_currency='USD'`.

**Prefer Invoice over Receipt**: Stripe emits both `Invoice-*.pdf` and `Receipt-*.pdf` per charge — dedup by tx, keep Invoice.

**Trap**: the `+acct_<hash>@stripe.com` sender is OPAQUE — the acct_id doesn't reveal the vendor. Identify vendor from PDF content (header "Bill to" section usually names the actual merchant).

### A2 — Non-Stripe direct-email SaaS

**Detection**: Sender is a vendor-specific domain, not Stripe-relayed. Common patterns:
- `billing@<vendor>.com`
- `invoice@<vendor>.com`
- `payments-noreply@<vendor>.com`
- `feedback@<vendor>.com` (Slack does this)

**Retrieval**:
1. Unipile `from=<guess>` (list of guessed sender addresses per known vendor)
2. If nothing found, try `any_email=<vendor>.com` + `has_attachments=true`
3. Extract PDF

**Traps**:
- Some vendors mix vendor emails with invoice PDFs in the SAME sender. `payments-noreply@google.com` handles both Workspace AND Cloud invoices. Distinguish via PDF content.
- Some vendors send zip files instead of PDF (Google Cloud statements come in a `google-payments-document-center-download_*.zip`).

### A3 — Dashboard-only SaaS

**Detection**: No emailed PDF; vendor sends "Invoice XYZ is available in your dashboard" security-notice style emails. Common for Vercel, Netlify, Cloudflare paid tiers, some enterprise SaaS.

**Retrieval**:
1. User must be logged into the vendor's dashboard in Chrome
2. Use Claude for Chrome MCP: navigate to `<vendor>.com/<team>/~/settings/invoices` (or similar)
3. `read_page` to enumerate `<a href="...invoices/inv_...">` links
4. For each invoice detail page, look for a `Download` link. **The Stripe-hosted PDF trick** works on many of these:
   - Pattern: `https://pay.stripe.com/invoice/{acct_...}/{live_...}/pdf?s=ap`
   - This URL is **public** — no cookie, no auth, no Referer needed
   - Extract with regex on the detail page HTML: `/https:\/\/pay\.stripe\.com\/invoice\/[^"'\s]+\/pdf[^"'\s]*/`
   - Then `curl -sL "<url>" -o out.pdf` from any machine
5. For non-Stripe-hosted vendors, use in-page `fetch(href, {credentials:'include'})` to download with the session cookie

**Currency**: often USD. Same matching rule as A1.

**Trap**: some vendors have MULTIPLE teams/workspaces per user account. Enumerate them via the vendor's API or account-switcher, and confirm with the user which one is the target org's.

### A4 — Foreign-currency B2B SWIFT

**Detection**: Qonto tx `operation_type == "transfer"` or `"swift"`, counterparty label contains a foreign city or bank name, amount in a non-base currency (USD, CNY, HKD, INR, etc.). Chinese factories are the canonical example — same pattern applies to any overseas B2B supplier or freelance partner paid by wire.

**Retrieval**:
1. Typically comes via WhatsApp or WeChat, sometimes email. Unipile WhatsApp works IF the account was connected before the PIs were sent.
2. **WhatsApp history is not backfilled by Unipile** — see gotcha #8. Options:
   - Ask the supplier to resend the PI via email
   - Ask the user to export the WhatsApp chat from phone (includes attachments)
   - Ask the user to AirDrop specific files from phone
3. PIs often come as `.xls` (Office 97-2003 CDF-V2) or `.xlsx`, not PDF. Extract via `xlrd` (for `.xls`) or `openpyxl` (for `.xlsx`), then convert to PDF via `fpdf` for Qonto attachment. See `modality-messaging.md` + `modality-local.md`.

**Currency**: use `local_amount` + `local_currency`. Widen date tolerance to ±15 days (SWIFT settlement lag) and amount tolerance to ±1% (correspondent bank fees).

**Trap**: brokers often reuse PI filenames when resending. The internal `Ref. no.` field (inside the xls/PDF) is the source of truth, not the filename.

### A5 — Domestic utility / paper-first vendor

**Detection**: Tx label = utility company or landlord (EDF, Orange, SFR, notary, rental company), reference is often blank or contains contract number. Usually monthly recurring.

**Retrieval**: user has the PDF locally (email attachment they forwarded to themselves, or downloaded from utility portal). Ask them for the folder path or specific file.

**Trap**: users MIS-LABEL these folders. Someone forwarding "electricity bills" to themselves may accidentally include unrelated Canva subscription invoices in the same thread. Always `pdftotext` first before trusting the folder name.

### A6 — Payment aggregator (PayPal / Stripe direct charges from users)

**Detection**: Tx label starts with `PAYPAL *` or `STRIPE *` (with the actual merchant name after the asterisk).

**Retrieval**:
- The underlying merchant's invoice is where you have to look. Extract the merchant name from the label (`PAYPAL *MERCHANT_NAME` → search for MERCHANT_NAME's invoice).
- If no invoice email exists, the aggregator's dashboard (paypal.com, dashboard.stripe.com if it's your own Stripe account) has the transaction detail — sometimes with a merchant-side receipt link.

**Trap**: PayPal debits often pair with a same-day credit (refund pattern). When you see a PayPal debit, always search for a paired credit ±1 day; if found, it's a cancelled order — the refund PDF is what you attach.

### A7 — Marketplace / commerce platform

**Detection**: Shopify subscription (`SHOPIFY *<BILL_ID>`), Amazon Marketplace pro fees, etsy platform fees, etc.

**Retrieval**:
1. Ask the user to export the CSV from the platform's billing admin (e.g. Shopify: `charges_export.csv`).
2. The CSV has bill numbers + amounts but NOT per-bill PDF URLs — the PDFs live at `admin.<platform>.com/store/<slug>/billing/receipt/<bill_id>` behind cookie auth.
3. Use browser modality to iterate the bill IDs and download each PDF.

**Trap**: platform CSV exports are sometimes just tx summaries without downloadable PDFs. Confirm with the user before promising bulk retrieval.

### A8 — Qonto-native-covered vendor

**Detection**: Vendor is in Qonto's supported integration catalog (Amazon Business, plus the Invoice Collector auto-match for ~200 known merchants).

**Retrieval**: **DO NOT re-implement**. Instruct the user to enable the native integration once (one-click in Qonto UI). Then either:
- Wait for the integration to backfill (Amazon Business syncs ~24h after activation)
- Skip these vendors in this session; they'll get auto-matched separately

See `modality-qonto-native.md`.

## How to classify a new vendor (heuristic)

Run through this list in order — first match wins:

1. **Tx label starts with `STRIPE *`** or amount-matches a `invoice+statements+acct_@stripe.com` email → **A1**
2. **Tx label starts with `PAYPAL *`** → **A6**
3. **Tx label is a known marketplace platform** (Shopify, Amazon Marketplace, Etsy) → **A7**
4. **Counterparty is foreign (non-org-country), foreign bank, foreign currency** → **A4**
5. **Vendor appears in Qonto's integration catalog** (check `qonto.com/features/factures-fournisseurs-comptabilite` OR the Qonto app's Integrations page) → **A8**
6. **Vendor has a searchable emailed PDF** (Unipile `any_email=<vendor>.com has_attachments=true` returns hits) → **A2**
7. **Vendor has a dashboard** at `<vendor>.com` → **A3**
8. **Otherwise** → **A5** (ask user for local file) or **manual_ask** (specific ask to supplier/user)

## Grow the map as you go

Each org has its own vendor mix. Nothing to hardcode here; the skill's job is to teach the agent the classification rules, and the agent builds its own sender-to-vendor map at runtime by decoding what it finds in the target org's mailboxes. A future run on the same org can reuse the map by reading whatever the agent wrote to `/tmp/qonto-inv/senders.json` on the previous run.
