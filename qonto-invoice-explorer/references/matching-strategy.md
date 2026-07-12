# Matching strategy

Loaded during Phase 3 when `scripts/match.py` needs a semantic hint the pure-code path can't decide. This file defines what a correct match looks like.

## Group by vendor first

Twenty Fiverr invoices in the target period is one email search, not twenty. Group by `clean_counterparty_name` first and fall back to `label` when the enrichment isn't there. Every retrieval channel is set up per vendor group, not per transaction.

## Amount and currency

Qonto stores each transaction in the org's base currency (`amount` / `currency`) and, when the original charge was foreign, in the vendor's billing currency (`local_amount` / `local_currency`). The rule is to match on the currency the vendor bills you in. A US SaaS that charged $99 shows up on a French account as around €87; matching against €99 tolerance misses the invoice, and matching €87 against some unrelated €89 debit false-positives. When the vendor's known currency isn't the org's base, the matcher reads `local_currency` first.

Tolerance is ±0.02 in the vendor's currency for SaaS. For SWIFT payments through correspondent banks, widen to ±1% or more — intermediary fees eat into the round number. Same-vendor SWIFTs with near-identical amounts split across multiple payments should never be matched by amount alone; use the `reference` field.

## Date window

Card charges show `emitted_at` on the day of auth, and the PDF is dated zero to three days earlier. SWIFTs settle three to seven business days after the invoice, so `settled_at` is the anchor there. Default to ±5 business days on `emitted_at` for SaaS card charges, ±15 days on `settled_at` for supplier transfers.

## The `reference` field

On SWIFTs and SEPAs, `tx.reference` holds the transfer memo the user typed at payment time — internal project codes, product codes, "half of X order", or the actual supplier name when the counterparty is a broker. When three near-identical-amount SWIFTs to the same vendor exist, `reference` is often the only signal that disambiguates them. Never drop it from the matcher's input.

## Prefer Invoice over Receipt

Stripe-hosted vendors emit both an Invoice PDF and a Receipt PDF for the same charge. French compta needs the Invoice (SIREN, VAT). Dedup by transaction, keep the Invoice, drop the Receipt. When only a Receipt exists, attach it — better than nothing.

## Vendor keyword

The PDF's extracted vendor string has to share at least one distinctive keyword with the Qonto label, case-insensitive. `VERCEL INC.` matches `Vercel Inc.`; `GOOGLE CLOUD EMEA` matches `Google Cloud EMEA Limited`. But `STRIPE` on a Qonto label matched to a Fiverr invoice PDF isn't a keyword hit — Fiverr paid through Stripe collapses to `STRIPE` on the tx counterparty enrichment. When the label is `STRIPE` and the PDF vendor is anything else, fall back to amount + local_currency + date matching.

## Refuse to guess

When more than one PDF plausibly matches a transaction, or one PDF plausibly matches more than one transaction, the matcher surfaces the candidates with their deltas and waits. Never call `upload_attachment` on an ambiguous pair. Common causes are recurring same-amount SaaS invoices in the same month (rare), a single invoice covering two sub-charges, or the user having forwarded the same email twice.

## Currency sanity check

If `amount / local_amount` doesn't sit within a few percent of the known FX rate, the pair is wrong. USD/EUR ranged 0.85–0.95 across 2025-2026; HKD/EUR around 0.11; CNY/EUR around 0.13. An implied FX that's off by more than five percent means the matcher is looking at the wrong invoice.
