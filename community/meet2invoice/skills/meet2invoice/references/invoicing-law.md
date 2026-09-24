# Invoicing-Law Reference — meet2invoice

Compliance cheat-sheet the skill consults **before creating a quote or invoice**.
Covers the VAT treatment decision, the mandatory legal mentions, and the
e-invoicing rollout per country. Scoped to Qonto's core markets: 🇫🇷 FR · 🇩🇪 DE ·
🇮🇹 IT · 🇪🇸 ES.

> **Caveat — read this.** This is operational guidance, **not tax advice**, and
> not a substitute for an accountant. Rates and mandatory fields are stable law;
> **e-invoicing rollout dates change** — those below are verified as of
> **2026-07** (sources at the bottom). Qonto itself formats the invoice
> (numbering, VAT breakdown, PDF/e-invoice output), so the skill's job is to feed
> it the **right VAT rate, the right tax IDs, and any required legal mention** —
> not to reformat the document. When a case is ambiguous, **ask the user**; never
> invent a VAT rate or a tax ID.

## Step A — Determine the VAT treatment

Decide this from the **supplier country** (your Qonto org) and the **client
country + status**, before setting `vat_rate`.

| Case | Condition | VAT rate | Mandatory mention on the invoice |
|---|---|---|---|
| **Domestic** | Client in the same country as the org | Standard/reduced local rate | none special |
| **Intra-EU B2B (reverse charge)** | Client is a VAT-registered business in another EU country | **0** | reverse-charge note + **both** VAT IDs (see below) |
| **Intra-EU B2C** | Client is a private individual in another EU country | Supplier's local rate (or OSS rules for goods/digital) | none special |
| **Export (non-EU)** | Client outside the EU | **0** (exempt/out of scope) | "VAT exempt — export of services/goods" |
| **Small business** | Supplier under a small-business scheme (DE §19, etc.) | **0** | scheme note (see per-country) |

**Reverse charge is the high-value case for B2B services** — most cross-border
consulting/agency deals. When it applies:

- set `vat_rate: "0"`,
- put **both** intra-community VAT numbers on the invoice (yours + the client's;
  the client's is mandatory — ask if missing),
- inject the legal mention into `terms_and_conditions`. Acceptable wordings:
  - EN: `Reverse charge — VAT to be accounted for by the recipient (Art. 196 EU VAT Directive 2006/112/EC)`
  - FR: `Autoliquidation — TVA due par le preneur (art. 283-2 du CGI / art. 196 directive TVA)`
  - DE: `Steuerschuldnerschaft des Leistungsempfängers (§ 13b UStG)`
  - IT: `Inversione contabile — art. 7-ter / art. 196 direttiva IVA`

## Step B — Standard VAT rates (as of 2026-07)

| Country | Standard | Common reduced |
|---|---|---|
| 🇩🇪 Germany | **19 %** (`"0.19"`) | 7 % (`"0.07"`) |
| 🇫🇷 France | **20 %** (`"0.2"`) | 10 %, 5.5 %, 2.1 % |
| 🇮🇹 Italy | **22 %** (`"0.22"`) | 10 %, 5 %, 4 % |
| 🇪🇸 Spain | **21 %** (`"0.21"`) | 10 %, 4 % |

Qonto's `vat_rate` is a **decimal string** (`"0.19"` = 19 %), and `unit_price`
is `{ value, currency }`.

## Step C — Mandatory invoice fields, per country

Qonto fills most of these automatically; the skill must ensure the **inputs**
exist (especially tax IDs, which block quote/invoice creation if missing).

### 🇩🇪 Germany — § 14 UStG
Full name + address of both parties · supplier **Steuernummer** *or*
**USt-IdNr.** · invoice date · **sequential invoice number** · quantity + type of
goods/services · **time of supply** (Leistungsdatum) · net amount, VAT rate + VAT
amount broken out · reverse-charge note where applicable.
- **Kleinbetragsrechnung (§ 33 UStDV):** if **gross ≤ €250**, simplified fields
  allowed (supplier name+address, date, quantity/type, gross total with tax rate)
  — **but full fields are still required for reverse charge (§ 13b).**
- **Small business (§ 19 UStG):** no VAT charged; add
  `Kein Ausweis von Umsatzsteuer gemäß § 19 UStG (Kleinunternehmer)`.

### 🇫🇷 France
SIREN/SIRET · intra-community VAT number · invoice number + date · quantity +
description · net, VAT rate, VAT amount · payment terms + **late-payment penalty
rate** and the **€40 fixed recovery indemnity** (mentions légales) ·
auto-entrepreneur non-subject to VAT: `TVA non applicable, art. 293 B du CGI`.

### 🇮🇹 Italy
**Partita IVA** of both parties · **Codice Destinatario** (7-char SdI code) or PEC
— required to route the mandatory electronic invoice through **SdI (FatturaPA)** ·
number + date · description · imponibile, aliquota IVA, imposta.

### 🇪🇸 Spain
NIF/CIF of both parties · number + date · description · base imponible, tipo IVA,
cuota. (Verifactu / e-invoicing rollout ongoing — verify current status.)

## Step D — E-invoicing rollout (verify dates; as of 2026-07)

Structured e-invoices are **EN 16931**-compliant XML (or hybrid PDF+XML). A plain
PDF is increasingly **not** a valid B2B invoice. Qonto produces compliant output;
surface the status to the user, don't try to generate the XML yourself.

| Country | Receive | Issue (B2B domestic) | Formats |
|---|---|---|---|
| 🇩🇪 DE | since **1 Jan 2025** (all) | **1 Jan 2027** (turnover > €800k), **1 Jan 2028** (all) | XRechnung, ZUGFeRD ≥ 2.x |
| 🇫🇷 FR | **1 Sep 2026** (all) | **1 Sep 2026** (large/mid), **1 Sep 2027** (SME/micro); pilot Feb 2026 | Factur-X, UBL, CII via PA/PDP |
| 🇮🇹 IT | **in force** (SdI) | **in force** — mandatory since 2019, extended to flat-rate 2024 | FatturaPA XML via SdI |
| 🇪🇸 ES | rollout ongoing | rollout ongoing (Crea y Crece / Verifactu) | verify |

DE exemptions from the issue mandate: B2C, §19 small business, invoices **≤ €250**,
transport tickets, VAT-exempt sales.

## Step E — How this maps to the Qonto MCP call

- `vat_rate` ← Step A/B decimal string.
- `tax_identification_number` (client) ← **required**; missing → `create_quote`
  fails 422 `"tin_number must have a value"`. Ask / `update_client` then retry.
- `terms_and_conditions` (invoice, ≤ 525 chars) ← carries **both** the legal
  mention (reverse charge / §19 / export) **and** the meet2invoice proof string,
  e.g.:
  `Steuerschuldnerschaft des Leistungsempfängers (§13b UStG) | SHA-256: <hex> | doc never uploaded`
- Sequential numbering, VAT breakdown, and e-invoice format are handled by Qonto.

## Sources (retrieved 2026-07-12)

- Germany B2B e-invoicing timeline: European Commission — <https://ec.europa.eu/digital-building-blocks/sites/spaces/DIGITAL/pages/467108886/eInvoicing+in+Germany> · ecosio — <https://ecosio.com/en/blog/germany-e-invoicing-explained/>
- § 14 UStG / Kleinbetragsrechnung (§ 33 UStDV) / § 13b: IHK Stuttgart — <https://www.ihk.de/stuttgart/fuer-unternehmen/recht-und-steuern/steuerrecht/umsatzsteuer-national/neue-pflichtangaben-fuer-rechnungen-684834>
- France e-invoicing calendar: economie.gouv.fr — <https://www.economie.gouv.fr/tout-savoir-sur-la-facturation-electronique-pour-les-entreprises>
- Italy SdI / FatturaPA: Agenzia delle Entrate (general reference)
