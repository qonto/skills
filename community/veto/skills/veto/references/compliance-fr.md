# French invoicing compliance for 2026

Why this skill validates what it validates. Sources: CGI art. 242 nonies A,
289 & 1737; Code de commerce L441-9/L441-10/D441-5; Loi de finances 2024
art. 91 (e-invoicing reform); service-public.gouv.fr; impots.gouv.fr.

## 2026 e-invoicing timeline

| Date | Obligation | Who |
|---|---|---|
| 1 Sept 2026 | RECEIVE e-invoices | ALL French VAT-registered businesses |
| 1 Sept 2026 | ISSUE e-invoices | Large enterprises + ETI |
| 1 Sept 2027 | ISSUE e-invoices | SMEs, TPE, micro-entrepreneurs |

Qonto is a Plateforme Agréée. Veto performs preflight checks on the customer
and invoice data available through the Qonto MCP. Generation, routing and
regulatory transmission remain the responsibility of Qonto and the applicable
e-invoicing infrastructure.

## Four mandatory mentions

1. **Client SIREN** — for French B2B buyers, 9 digits (SIRET 14 accepted).
   It does not apply to an individual/B2C buyer or a non-French buyer. Maps to Qonto client
   field `tax_identification_number`. Veto blocks a missing identifier because
   the recipient record is incomplete for French B2B invoice preparation. It
   does not claim network reachability until the routing directory confirms it.
2. **Delivery address** when different from billing (goods only) — Qonto
   client field `delivery_address`.
3. **Operation category** — goods (LB) / services (PS) / mixed (LBPS).
   Set at ORGANIZATION level in Qonto (`transaction_type`:
   goods / services / goods_and_services) — check org settings in-app.
4. **"Option TVA sur les débits"** when the seller opted for it — Qonto
   org-level field `vat_payment_condition` (`compensated_for_sales`).

Note: mentions 3 and 4 live on the Qonto ORGANIZATION profile, not on the
invoice payload. Advise the user to verify them once in Qonto settings.

## French VAT rates

| Rate | Use |
|---|---|
| 20% | Standard |
| 10% | Reduced (restauration, transport, works on housing…) |
| 5.5% | Reduced (food, books, energy renovation…) |
| 2.1% | Super-reduced (press, reimbursable medicines…) |
| 0% + exemption code | Franchise en base, exports, intra-EU with valid VAT number |

Franchise en base (auto-entrepreneurs): exact mandatory wording
"TVA non applicable, art. 293 B du CGI".

The Qonto API accepts ANY decimal vat_rate — it does not validate against
French legal rates. The skill must.

## Required B2B late-payment terms

- Late-payment penalty terms must state the contractual rate or a valid
  formula such as the applicable ECB refinancing rate + 10 points. The
  underlying reference rates change; verify the rate applicable to the
  invoice period before calculating an amount. The deterministic script
  therefore requires the annual rate as an explicit input.
- Fixed recovery indemnity: €40 per late invoice (B2B only, not VAT-able).
- Escompte conditions (or "Pas d'escompte pour paiement anticipé").

## Invoice numbering

Chronological, continuous, no gaps, unique per organization. Never delete
or renumber an issued invoice — corrections go through a credit note
(avoir) referencing the original. Qonto handles numbering when
auto-numbering is enabled; do not override it manually.

## Penalties for non-compliance

- €15 per missing mention, capped at 25% of the invoice (CGI art. 1737).
- E-invoicing: €15 per non-compliant invoice, capped €15,000/year.
- Missing invoice (amende fiscale): up to €75,000 (€375,000 for companies).
