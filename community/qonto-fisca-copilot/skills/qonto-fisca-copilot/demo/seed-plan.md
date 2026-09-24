# Demo seed plan — sandbox org (fully de-identified)

Goal: seed the Qonto **sandbox** with fabricated transactions so the
`qonto-fisca-copilot` demo triggers **every nudge (N1–N10) + the mileage wow**, on
**public-safe, non-identifying data**.

- Mirror of `demo/demo-transactions.json` (used to test the scripts locally).
- Create via the QA tool (`qa-sandbox.staging.qonto.co`) or its MCP.

## 🔒 De-identification rules (the whole point)

Nothing in the demo may point back to the real account:
- **Org name/slug must be neutral** — use e.g. **NIMBUS SAS**. Never reuse an org whose
  name/slug derives from your real company. Create a fresh org (QA tool → Create
  Organization) with a neutral name, or rename it, before recording.
- **No merchant copied from the real account.** All names below are generic national
  brands (used by everyone) or fictional firms. Restaurants are **real, web-findable
  public places the user has no link to** — needed so the mileage web-lookup works.
- Amounts/dates are fabricated round-ish values.

## Narrative (coherent + de-identified)

**NIMBUS SAS**, a **Paris**-based French SARL. In June it made a **client trip to Lyon**
(lunch + hotel) → the mileage wow. Everything else is ordinary running costs.

> Office city drives the mileage nudge. Set/confirm the sandbox org address = **Paris**.
> Then Lyon = far (wow), Paris = local (dropped).

## The 16 transactions

| # | Label | Amount | VAT | Category | Type | Triggers | Note |
|---|---|---:|---|---|---|---|---|
| 1 | BRASSERIE GEORGES | 95.00 | 8.64 @10% | Food | card | **N2 (km, Lyon)** · N3 · N5 | 🌟 wow — real Lyon brasserie |
| 2 | BOUILLON CHARTIER | 62.00 | 5.64 @10% | Food | card | N3 · N2(Paris→drop) · N5 | local contrast |
| 3 | ANTHROPIC* CLAUDE | 180.00 | — | Tech / Licences | card | **N1 autoliquidation** · N5 | Ireland |
| 4 | VERCEL INC. | 26.26 ($30.07) | — | — | card | N1 · foreign FX · N5 | US, USD |
| 5 | IBIS LYON PART-DIEU | 89.00 | 8.09 @10% | Travel / Lodging | card | **N4 hotel VAT** · N5 | Lyon trip, non-recoverable |
| 6 | TOTALENERGIES | 72.00 | 12.00 @20% | Fuel | card | **N7 fuel VAT** · N5 | |
| 7 | FNAC | 129.00 | 21.50 @20% | IT hardware | card | **N10 <500€** · N5 | immediate deduction |
| 8 | INTERFLORA | 65.00 | 10.83 @20% | Marketing / Gifts | card | **N6 gift ≤73€** · N5 | |
| 9 | URSSAF | 708.00 | 0 | — | direct_debit | no-invoice-expected | not chased |
| 10 | CABINET DUBOIS EXPERTISE | 118.80 | 19.80 @20% | Accounting | card | **N9 honoraires** | has receipt → no N5 (fictional firm) |
| 11 | ORANGE BUSINESS | 29.99 | 5.00 @20% | Telecom | direct_debit | N5 | recurring |
| 12 | Remboursement compte courant associe | 800.00 | — | — | transfer | **N8 CCA** | presumption + interest |
| 13 | LE COMPTOIR DU MARCHE | 48.00 | 4.36 @10% | *(none)* | card | N3 · N5 · uncategorised | tests categorization |
| 14 | AWS EMEA | 54.00 | — | Tech | card | N1 · N5 | reverse-charge |
| 15 | Qonto (fee) | 13.20 | 2.20 @20% | Bank fees | qonto_fee | N9 · no-invoice | has receipt |
| 16 | ACME SAS — Invoice 2026-014 | +2 400.00 | — | Sales | transfer | **inflow (credit)** | fictional client |

## Coverage check (local)

`python3 scripts/scan_triggers.py demo/demo-transactions.json` → **all 10 nudges (N1–N10)
fire**, plus a credit, a foreign-currency line, and an uncategorised line.

## Standalone niches (org-profile driven, not transactions)

Set via the sandbox org metadata / `profile.md`:
- **IS 15% band, CFE creation exemption, JEI window** → make the org's
  `legal_registration_date` recent (< 1 year).
- **CESU** → `employees: 0` → shown as "eligibility uncertain".
- **Home-office redevance, PER, mécénat** → surfaced as reminders.

## Video

Analyze **one month** — crisp, one clear "wow" (the mileage detective reading the city
off the receipt). The skill's value shows on a single month; no year of data needed.
- **Seeding**: creating 130 rows by hand is heavy → prefer the QA **Import Seeds** (bulk)
  or the QA **MCP**. If neither works, seed **June (16 rows) + 2-3 older months** so the
  account still shows visible depth on screen.

## Next

1. Create a neutral sandbox org (**NIMBUS SAS**, Paris) or rename the current one.
2. Confirm the office city = Paris (`get_organization`).
3. Create the 16 rows (QA tool / QA MCP).
4. Get the sandbox **read** MCP endpoint (ask Stefano in `#qonto-mcp-hackathon`).
5. Run the skill end-to-end on the seeded sandbox → record the demo.
