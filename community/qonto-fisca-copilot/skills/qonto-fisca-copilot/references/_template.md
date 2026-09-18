# Template — adding a country to `qonto-fisca-copilot`

The skill detects the organization's country via `get_organization` → `legal_country`
(e.g. `FR`, `DE`, `IT`, `ES`) and loads `references/rules-<cc>-<regime>.md` (lowercase country
code). To cover a new Qonto market, create that file following the structure of
`rules-fr-is-tns.md`.

## Golden rules

- **Source every figure** (national tax authority + a reputable firm), with the **year**
  it applies to. Never an unsourced amount.
- **Confidence level** per item: `high` / `medium` / `⚠️ to verify`.
- Adapt to the **local legal form** and the **director's status** (SARL/gérant TNS in
  FR; GmbH/Geschäftsführer in DE; SRL/amministratore in IT; SL/administrador in ES…) —
  a niche's eligibility depends heavily on it.
- Everything stays **advisory**: "to be confirmed with a local accountant."

## Expected structure (reuse the sections of `rules-fr-is-tns.md`)

```
# <legal form>, <director status> (<country>) — tax rules catalogue

## 🔔 TRANSACTION-TRIGGERED NUDGES
### N1 — Reverse-charge VAT on foreign services        ← UNIVERSAL (EU)
### N2 — Mileage (local barème)
### N3 — Business meal / travel
### N4 — Accommodation VAT
### N5 — Invoice required to deduct VAT                 ← UNIVERSAL (EU)
### N6 — Client gifts (local threshold)
### N7 — Fuel VAT
### N8 — Associate current account / contributions
### N9 — Accounting fees & bank fees

## 🎯 STANDALONE NICHES TO ACTIVATE       ← 100% country-specific
## 📅 DEADLINES                            ← local filing calendar
## ⚠️ TO VERIFY
```

## What is (almost) universal in the EU — reuse fast

- **N1 — VAT reverse-charge** on intra-EU / non-EU B2B services: harmonized by the EU
  VAT directive. The mechanism is the same everywhere; only the national return and
  the wording change.
- **N5 — mandatory invoice** to deduct VAT: common EU principle.
- **N2/N3 — travel and meal expenses**: the concept exists everywhere, but the barèmes
  and ceilings are national → re-source them.

## What is 100% national — research fully

- All the **niches** (there is no exact CESU/JEI/redevance-domicile equivalent elsewhere),
  the **rates and ceilings**, the **mileage barèmes**, the **filing calendar**, the
  **legal forms** and the **director's social regime**.

> Never ship a partial `rules-<cc>-<regime>.md` presented as complete. An unsourced country =
> the skill limits itself to the universal nudges and says so to the user.
