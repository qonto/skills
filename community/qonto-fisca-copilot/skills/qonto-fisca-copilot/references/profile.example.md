# Profile (context) — example

Copy this file to `profile.md` (untracked) and fill it in. The skill combines
**three sources** to know which rules apply:

1. **Auto from Qonto** (`get_organization`) — nothing to fill, it's derived:
   - `country` ← `legal_country` (e.g. FR)
   - `legal_form` ← `legal_form` (e.g. SARL) — gives a **first guess** of the regime:
     SARL/EURL→likely IS+TNS · SASU/SAS→IS+assimilé-salarié · auto-entrepreneur→micro+TNS ·
     EI→micro or IR-réel+TNS. Confirm `regime_fiscal`/`director_regime` when ambiguous.
   - `creation_date` ← `legal_registration_date` (→ ACRE / JEI / CFE windows)
   - `share_capital` ← `legal_share_capital` (→ 10% dividend threshold)

2. **This file** — the facts Qonto does not know:

```yaml
regime_fiscal: IS             # IS (corporate tax) | IR-reel | micro  ← selects the rule pack
director_regime: TNS          # regime_social: TNS (majority manager / auto-entrepreneur / EI) | assimilé-salarié (SASU/SAS president, minority SARL manager)
employees: 0                  # 0 = many "employee benefits" (CESU, meal vouchers…) drop off
vehicle:
  owned: true
  fiscal_cv: 6                 # for the mileage barème
  fuel: petrol                 # petrol | diesel | electric | hybrid
  use: mixed                   # 100%_business | mixed | personal
dependent_children: 0         # → childcare credit, tax parts
married_pacs: true
home: tenant                  # tenant | owner → redevance / pro-rata deduction
existing_contracts: []        # e.g. [madelin_retraite, per, mutuelle_madelin]
training_activity: true       # training body (NDA/Qualiopi) → training VAT exemption
nda_obtained: false           # 3511-SD attestation only possible if true
vat_regime: reel_normal_monthly
```

3. **On-the-fly questions** — if a triggered rule needs a fact absent from the two
   sources above, the skill **asks** for it (e.g. "what's your vehicle's CV?") rather
   than guessing. It asks only the strictly necessary question.

## Why it matters

Each rule's applicability is **computed** from this profile, not hardcoded. Example
switches:
- `employees: 0` → CESU, meal vouchers, holiday vouchers, PPV **disabled** (they
  require employer status — see `rules-fr-is-tns.md`).
- `director_regime: assimilé-salarié` → the social regime changes (no TNS contributions,
  dividends not subject to the 10% threshold…), several rules recompute.
- `training_activity: true` + `nda_obtained: true` → training VAT exemption enabled
  (with its knock-on effect on deductible input VAT).
- `creation_date` < 1 year → ACRE / start-of-activity exemptions / CFE creation windows.

> If `profile.md` is absent, the skill still works: it uses the Qonto auto-fields and
> asks the missing questions along the way.
