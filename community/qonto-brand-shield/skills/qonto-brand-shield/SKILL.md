---
name: qonto-brand-shield
description: Brand protection radar for Qonto accounts. Detects brand-building spend in real transactions (designers & logo work, domain names, advertising, packaging, print), totals it per brand ("you invested €X in brand [Name]"), then cross-checks intellectual property — is the brand registered at INPI, by you, do close marks exist in your suggested Nice classes, is the 10-year renewal near? Outputs the financial exposure (unprotected investment) and a pre-filing dossier ready for inpi.fr. Use for "is my brand protected?", "ma marque est-elle déposée ?", "combien j'ai investi dans ma marque ?", "how much did I spend building my brand?", "should I file a trademark?", "prépare mon dossier INPI".
permissions:
  mcp:
    qonto: [get_attachment, get_organization, list_cash_flow_categories, list_products, list_supplier_invoices, list_transaction_attachments, list_transactions]
  network: []
  env: []
  tools: [Read]
---

# Qonto Brand Shield

You keep paying to build a brand — is anyone protecting it? 100 % read-only: the skill measures the investment and prepares the filing dossier; the trademark filing itself happens on inpi.fr, by the user.

## Prerequisites
1. `get_organization` FIRST → legal name, trade names, country, and the `bank_account_id`/`iban` values that `list_transactions` requires.
2. **Country-aware**: the registry cross-check targets **INPI (France)**. For other Qonto countries (DE, ES, IT, AT, NL, BE, PT…), the spend analysis and financial exposure stay fully valid; for the registry side, point to **EUIPO** (euipo.europa.eu) as the lead — never invent registry data.
3. **INPI access is optional**: the data.inpi.fr API requires an INPI account plus an approved access request. Without it, degrade honestly (step 4) — **no scraping, ever**.

## Workflow

### 1. Identify the brand(s)
- `get_organization` → legal name + trade names (a trade name is often the brand).
- `list_products` → product/service labels: brand line names AND the raw material for Nice-class suggestion (step 5).
- Collect additional brand candidates from transaction labels and invoice attachments (step 3): domain names, product lines. One company can carry several brands — keep them separate.

### 2. Scan brand-building spend (12–36 months)
`list_transactions` per account, `per_page: "50"`, 3-month windows, `side: debit`. Prefer **24–36 months**: yearly cadences (domain renewals) only become visible across full years. Add `list_supplier_invoices` for clean supplier names and amounts. Buckets:
- **Design & identity**: freelance/design platforms and agencies; labels containing logo / branding / identité / charte graphique / naming.
- **Domain names**: registrars (OVH, Gandi, Namecheap, GoDaddy, IONOS…), yearly cadence — domains are annual subscriptions: cross-reference with **qonto-subscription-audit** when installed.
- **Advertising**: ad platforms (Google Ads, Meta, TikTok, LinkedIn…) — campaigns build the name's value.
- **Packaging & print**: printers and packaging suppliers; labels containing impression / packaging / étiquettes / stickers.
Normalize counterparties (case, accents; the same vendor under several spellings = ONE counterparty).

### 3. Attach each expense to a brand
- `list_transaction_attachments` then `get_attachment` on design/domain/print invoices: extract the brand name when it appears ("logo for X", the domain "x.com", a packaging proof).
- Domain names map naturally to a brand.
- Unattributable spend goes to the organization's main brand, tagged 🟡 assumed (vs 🟢 evidenced by a document or domain).
- Output per brand: total invested, breakdown per bucket, period covered, monthly run-rate.

### 4. IP cross-check (INPI — France)
- **With INPI API access** (extra MCP or user-provided credentials): search the exact name + close variants; report — registered? live? owner matches the organization? which Nice classes? filing date and **10-year renewal window** (alert when < 12 months away; indicative renewal cost ~€290 + €40/class — verify on inpi.fr).
- **Without API access (the default)**: provide the pre-filled search link — `https://data.inpi.fr/search?q=<brand>` (Marques tab) — plus a 2-minute manual checklist: exact name registered/live? owner = your company? classes? renewal date? Ask the user to paste back what they see; integrate registry facts **only** from that answer. Never scrape data.inpi.fr, never guess registry results — unverified lines stay marked "unverified".
- **Close marks**: similar names in the user's suggested classes are an **indicative alert, not a legal opinion** — recommend an IP professional (conseil en PI) before filing.

### 5. Suggest Nice classes from real activity
Map the products/services actually detected (`list_products` labels, transaction activity) to **1–3 Nice classes** — e.g. SaaS/software services → 42 (+9 for downloadable software), clothing/print-on-demand → 25, retail & advertising services → 35, education/content → 41. Always presented as **suggestions to validate** (IP professional or INPI's own class-helper), never as legal advice.

### 6. Report — output formats
**Always** reply in the conversation with markdown tables:
1. **Investment per brand** (bucket × amount × period × confidence 🟢🟡).
2. **Protection status** (registered? by whom? classes? renewal date?) — each line sourced (API result or the user's manual check) or marked "unverified".
3. **Exposure line**: "€X invested over N months on [Brand] — not registered" + close-mark and renewal alerts.
4. **Pre-filing dossier**: brand name, suggested Nice classes (to validate), indicative cost (**€190 first class + €40 per extra class**, ~€190–270 for 1–3 classes — verify on inpi.fr), and the inpi.fr link to start the filing.

**Additionally, when the host renders files** (claude.ai artifacts, Claude Desktop, Claude Code): an HTML one-pager — exposure gauge per brand, spend buckets, protection status, dossier. If the host cannot render files, say nothing about it: the markdown tables are the deliverable.

## Guardrails
- **Read-only**: this skill uses no write tool, ever. The filing is a human decision, made on inpi.fr.
- Trademark similarity = indicative alert, **not** a legal analysis; recommend an IP professional before filing or opposing.
- Nice classes are suggestions to validate; costs are indicative — the source of truth is inpi.fr.
- Never present registry facts without a source (API result or the user's own manual check). No scraping.
- Non-French organizations: exposure analysis valid everywhere; registry checks → EUIPO mentioned as the lead.
- Mask IBANs (last 4 digits). Paginate everything (`per_page` ≤ 50). Degrade honestly when history < 12 months (annual domain cadences need 24–36).
