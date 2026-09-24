# 🇫🇷 France — regime: **IR réel + TNS** — EURL à l'IR / EI au réel

> Loaded when `regime_fiscal == "IR-réel"` **and** `regime_social == "TNS"`.
> Fact-checked 10 July 2026 against official sources — see Verification notes at the bottom. Advisory; confirm with your accountant.
>
> At the **réel**, actual expenses **are** deductible, so the baseline transaction nudges apply.
> But the business is **à l'IR** (transparent: profit = the entrepreneur's taxable income), so
> the **IS / dividends layer drops**. **Reuse `rules-fr-is-tns.md` for the nudges & TNS niches**;
> this pack overrides the corporate layer.

## ✅ KEEP from `rules-fr-is-tns.md`
- Transaction nudges: **frais km, business meals, <500€ immediate deduction, fuel VAT,
  gifts ≤73€, reverse-charge VAT (autoliquidation), hotel VAT, invoice-required**.
- TNS niches: **26 % social abatement, Madelin, PER (TNS ceiling), CFE, JEI/CIR (réel), mécénat**.
- ⚠️ **Key structural note:** in EURL-IR / EI, expenses are deducted on the **BIC/BNC result**,
  and the **gérant/entrepreneur's own "rémunération" is NOT a deductible charge** (it's a share
  of profit) — unlike à l'IS. Don't treat owner draws as deductible.

## 🔴 DROP (do NOT apply at the IR)
- **IS 15 % reduced band** — there is no IS. → https://bofip.impots.gouv.fr/bofip/2062-PGP.html
- **Dividends & the 10 % threshold** — no dividend mechanism at the IR; profit is taxed
  directly at the entrepreneur's IR rate whether withdrawn or not.

## 🎯 ADD (IR-réel / TNS / EI specifics)

### R1 — 26 % TNS social abatement · confidence: high · ✅ confirmed
- 2026 reform: social base = income minus a **26 % flat abatement** (replaces the old
  cotisation-deduction model). Applies to the EURL-IR gérant / EI (TNS).
- **Source**: https://www.urssaf.fr/accueil/independant/comprendre-payer-cotisations/reforme-cotisations-independants.html

### R2 — Gérant: 10 % forfait vs frais réels · confidence: high · ✅ confirmed
- The gérant can deduct a **10 % forfait** on remuneration **or** itemized real expenses —
  one or the other, chosen annually. Compare each year.
- **Source**: https://www.impots.gouv.fr/particulier/questions/je-suis-gerant-dune-societe-puis-je-beneficier-des-frais-reels

### R3 — CSG-CRDS partly deductible · confidence: ⚠️ reform 2026 — do not quote a firm rate
- Part of the CSG paid on TNS activity income is **deductible** from taxable income.
  ⚠️ **The exact deductible fraction is unsettled for 2026**: the classic activity-income figure is
  CSG déductible **6.8 %** (of 9.2 % CSG; + 2.4 % non-deductible + 0.5 % CRDS), but the **2026 social-base
  reform** (unified assiette, 26 % abatement) changes how CSG-CRDS is computed for TNS. Do **not** assert
  a firm rate — confirm with URSSAF/accountant. (Human check 10 July 2026: the automated pass's "5.1 %"
  could not be confirmed on an official source and has been reverted to this ⚠️ note.)
- **Sources**: https://bofip.impots.gouv.fr/bofip/5658-PGP.html ·
  https://www.urssaf.fr/accueil/independant/comprendre-payer-cotisations/reforme-cotisations-independants.html

### R4 — CVAE · confidence: high · ✅ confirmed
- Register at **€152 500** turnover; **no payment below €500 000**. (Same rule as a société.)
- **Source**: https://bofip.impots.gouv.fr/bofip/839-PGP.html (BOI-CVAE-LIQ-10 updated 2025-11-19)

### R5 — IS option (EURL / EI) · confidence: high · ✅ confirmed
- An EURL-IR (or an EI) can **opt for IS**: **3-month** filing window, **5-year** revocation
  lock then irrevocable. If opted → switch to the **`rules-fr-is-tns.md`** pack (or
  `rules-fr-is-assimile.md` if the manager becomes assimilé).
- **Sources**: https://www.impots.gouv.fr/professionnel/questions/je-cree-une-eurl-de-quels-impots-serai-je-redevable ·
  https://bofip.impots.gouv.fr/bofip/822-PGP.html (BOI-IS-CHAMP-40)

### R6 — EI: automatic asset protection (2022 reform) · confidence: high · ✅ confirmed
- For an **EI**, professional and personal assets are **separated by law** since 15/02/2022 —
  personal property is protected from professional creditors (no EIRL needed).
- **Source**: https://www.impots.gouv.fr/professionnel/questions/quest-ce-que-le-statut-unique-de-lentrepreneur-individuel

### R7 — Micro <-> réel thresholds · confidence: high · ✅ confirmed
- Above **€203 100** (commerce) / **€83 600** (services/BNC) for **2 consecutive years** →
  the micro option is lost (réel becomes mandatory). Below, a switch to micro may be simpler.
  Valid for 2026, 2027, and 2028.
- **Source**: https://entreprendre.service-public.gouv.fr/vosdroits/F23267

## ⚠️ To verify
- Exact **mileage barème** and **PER (TNS) ceiling** for 2026 (see the baseline `rules-fr-is-tns.md`).

## Verification notes (10 July 2026)

**Summary (incl. human Opus pass 10 July 2026):**
- Figures checked: 7 quantitative/legal claims (R1–R7)
- Confirmed on official sources: 6
- Corrected: 0 (see below)
- Unconfirmed / softened: 1 (R3 CSG)

**⚠️ Correction proposed by the automated (haiku) pass — REVERTED:**
- The automated pass changed R3 CSG deductible from 6.8% to "5.1% (total 7.5%)". The human (Opus)
  pass could **not** confirm "5.1%" on any official source, and the 2026 assiette reform makes the
  TNS activity-income figure unsettled → R3 is now marked **⚠️ (no firm rate)**. Neither 6.8% nor 5.1%
  is asserted; the classic 6.8% is noted as the *replacement-income* figure.

**Official sources consulted:**
- https://www.urssaf.fr/accueil/independant/comprendre-payer-cotisations/reforme-cotisations-independants.html (26% abatement, TNS reform)
- https://www.impots.gouv.fr/particulier/questions/je-suis-gerant-dune-societe-puis-je-beneficier-des-frais-reels (gérant 10% forfait)
- https://bofip.impots.gouv.fr/bofip/5658-PGP.html (CSG deductibility for earned income)
- https://bofip.impots.gouv.fr/bofip/839-PGP.html (CVAE thresholds, updated 2025-11-19)
- https://bofip.impots.gouv.fr/bofip/822-PGP.html (IS option terms)
- https://www.impots.gouv.fr/professionnel/questions/quest-ce-que-le-statut-unique-de-lentrepreneur-individuel (EI asset protection since 2022-02-15)
- https://entreprendre.service-public.gouv.fr/vosdroits/F23267 (micro thresholds for 2026–2028)

**Residual risk:**
- The 2026 social contribution reform (26% abatement replacing contribution deductions) is still being implemented. CSG deductibility may be affected by decree changes in April 2026 when the 2025 income declaration campaign opens. Recommend re-verification when Q2 2026 URSSAF/BOFIP guidance is published.
- PER (TNS) ceiling and mileage barème for 2026 remain unchecked; refer to `rules-fr-is-tns.md` for these figures.
