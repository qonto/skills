# 🇫🇷 France — Micro / auto-entrepreneur — tax rules

> Country+regime file loaded when `regime_fiscal == "micro"` (auto-entrepreneur, micro-EI,
> micro-EURL). Fact-checked 10 July 2026 against official sources — see Verification notes
> at the bottom. Advisory; confirm with your accountant. Rule descriptions keep French legal
> terms; structure is English.
>
> ⚠️ **Flat-abatement regime.** In micro, deemed expenses are a fixed % of turnover — the
> founder **cannot** deduct actual costs. So the baseline (`rules-fr-is-tns.md`) expense &
> VAT-reclaim nudges **do NOT apply**. Use the packs below instead.

## Contents

- **🔴 Do NOT propose** — inapplicable to micro (say so plainly).
- **🔔 Micro nudges** — the few that DO apply (VAT reverse-charge, thresholds, e-invoicing).
- **🎯 Micro items to activate** — VFL, ACRE, CFE relief.
- **📅 Thresholds & figures (2026)**.
- **⚠️ To verify**.

---

## 🔴 DO NOT PROPOSE (inapplicable to micro)

Say plainly: *"You're on the micro regime — your expenses are already covered by the
{71/50/34}% abatement, so per-expense deductions don't apply."*

- **Frais réels of any kind** — mileage (km), business meals, equipment <500€, fuel,
  home office, supplies. The abattement replaces them; **0 % actual deduction**.
  → https://entreprendre.service-public.gouv.fr/vosdroits/F23267
- **Amortissement** (depreciation of equipment/vehicles) — not allowed.
- **Deficit** — no loss carry-forward/offset.
- **VAT reclaim / recoverable VAT** — under franchise en base, no input VAT is deductible
  and no VAT is charged (mention *"TVA non applicable, art. 293 B du CGI"*).
  → https://bofip.impots.gouv.fr/bofip/1079-PGP.html
- **IS-only niches** — 15 % IS band, JEI (IS exemption), CIR/CII, dividends 10 % threshold,
  redevance domicile as a company charge — a micro is not an IS company.

## 🔔 MICRO NUDGES (the ones that DO apply)

### M1 — 🔥 Reverse-charge VAT on foreign services — **applies EVEN under franchise en base**
- **Trigger**: paying a foreign service provider (Anthropic Ireland, Vercel US, AWS, Google…).
- **Nudge**: *"Even VAT-exempt (franchise en base), you MUST self-liquidate (autoliquidation)
  the VAT on services bought from abroad — **any amount** for intra-EU/foreign services —
  get an intra-community VAT number and declare it (CA3). Most auto-entrepreneurs miss this."*
- Goods from the EU: reverse-charge only above **€10 000/yr**.
- **Sources**: https://www.impots.gouv.fr/professionnel/prestations-entre-assujettis ·
  https://www.impots.gouv.fr/professionnel/questions/je-suis-micro-entrepreneur-ou-la-tete-dune-micro-entreprise-ai-je-des

### M2 — Approaching the micro CA ceiling
- **Trigger**: cumulative turnover nearing the ceiling.
- **Nudge**: *"Watch the micro ceiling — 2 consecutive years over and you switch to régime
  réel automatically."* Ceilings 2026: ✅ **€203 100** (vente/commerce/hébergement),
  ✅ **€83 600** (services BIC / BNC).
- **Source**: https://www.autoentrepreneur.urssaf.fr/portail/accueil/sinformer-sur-le-statut/toutes-les-actualites/2026--modification-des-seuils-de.html

### M3 — Approaching the franchise-en-base VAT threshold
- **Nudge**: *"Cross the franchise threshold and you must charge VAT — immediately if you
  pass the higher limit mid-year."* 2026: ✅ goods **€85 000** (majoré €93 500); ✅ services
  **€37 500** (majoré €41 250).
- **Source**: https://entreprendre.service-public.gouv.fr/vosdroits/F21746

### M4 — E-invoicing 2026 applies even to franchise
- **Nudge**: *"Even VAT-exempt, the 2026 e-invoicing reform applies — you must receive (then
  issue) electronic invoices."*
- **Source**: https://www.impots.gouv.fr/professionnel/questions/franchise-en-base-micro-entrepreneur-ou-auto-entrepreneur-suis-je-concerne

## 🎯 MICRO ITEMS TO ACTIVATE

### MC1 — Versement forfaitaire libératoire (VFL) — confidence: high
- Optional: pay income tax as a flat % of turnover instead of the barème: ✅ **1 %** (commerce),
  ✅ **1,7 %** (BIC services), ✅ **2,2 %** (BNC). Worth it if your marginal IR rate is higher.
- **Condition**: household RFR must not exceed ✅ **€29 579 per share** (quotient familial)
  in year N-2. For a couple: €59 158; couple +1 child: €73 948; couple +2 children: €88 737 (2026).
- **Source**: https://entreprendre.service-public.gouv.fr/vosdroits/F23267

### MC2 — ACRE (start of activity)
- Partial exemption of micro-social contributions in the first period. Check eligibility
  and the 2026 rules. → https://www.urssaf.fr/accueil/exoneration-acre-createur.html

### MC3 — CFE relief
- ✅ **Exempt the creation year**; and ✅ exempt from the **minimum CFE if CA ≤ €5 000/yr**
  (measured on reference year N-2).
- **Source**: https://entreprendre.service-public.gouv.fr/vosdroits/F23999

### MC4 — Know your abattement
- Deemed expenses = ✅ **71 %** (vente/commerce), ✅ **50 %** (services BIC), ✅ **34 %** (BNC),
  ✅ minimum €305. That IS your deduction — nothing to itemize.
- **Source**: https://entreprendre.service-public.gouv.fr/vosdroits/F23267

## 📅 THRESHOLDS & FIGURES (2026)

- **Micro ceilings**: ✅ €203 100 (commerce) · ✅ €83 600 (services/BNC) · ✅ €15 000 (meublé tourisme — classified only; unclassified excluded from micro as of 1 Jan 2026).
- **Franchise TVA**: ✅ goods €85 000 / €93 500 · ✅ services €37 500 / €41 250.
- **Abattements**: ✅ 71 % / 50 % / 34 % (min €305).
- **VFL**: ✅ 1 % / 1,7 % / 2,2 % of turnover.
- **Micro-social contributions** (on **turnover**, not profit):
  - ✅ Commerce: 12.3 % (13.3 % if opting for VFL)
  - ✅ BIC services: 21.2 % (22.9 % with VFL)
  - ✅ BNC services (liberal): 25.6 % (27.8 % with VFL)

## ⚠️ TO VERIFY

- ✅ Exact **micro-social rates** per activity for 2026 — CONFIRMED (12.3% / 21.2% / 25.6%).
- ✅ **VFL household RFR ceiling** for 2026 — CONFIRMED (€29 579 per share).
- Any **minimum-turnover / affiliation** rule for auto-entrepreneur status.
- ✅ Franchise-TVA thresholds (€85k/€93.5k goods; €37.5k/€41.25k services) confirmed in force post-2025 reform.

---

## Verification notes (10 July 2026)

**Figures checked**: 21 quantitative claims verified against official French tax sources
(impots.gouv.fr, urssaf.fr, entreprendre.service-public.gouv.fr).

**Confirmed on authoritative sources**: 18 figures
- Micro ceilings (€203 100, €83 600, €15 000)
- Abattement rates (71%, 50%, 34%) and minimum (€305)
- VFL rates (1%, 1.7%, 2.2%)
- Franchise TVA thresholds (all four figures)
- VFL household RFR ceilings (€29 579 per share + couples/children scale)
- Micro-social contribution rates (12.3%, 21.2%, 25.6% + VFL variants 13.3%, 22.9%, 27.8%)
- CFE exemptions (creation year, €5 000/yr minimum threshold)

**Corrected figures**: 1
- Micro-social contributions: Original text said "~22% commerce · ~25.6% services · ~26.1% BNC" 
  → Corrected to: Commerce 12.3% (13.3% with VFL), BIC services 21.2% (22.9% with VFL), 
  BNC services 25.6% (27.8% with VFL). Source: https://entreprendre.service-public.gouv.fr/vosdroits/F36232

**Unconfirmed claims**: 2
- "Any minimum-turnover / affiliation rule for auto-entrepreneur status" — no specific 
  contradiction found; may need accountant review.
- Specific article reference "art. 293 B du CGI" for VAT non-applicability — cited correctly 
  but not independently verified in this fact-check.

**Residual risk**: 
- VFL RFR ceiling figures are for 2026 option (based on 2024 RFR). Verify with your accountant 
  that 2024 RFR figures are current in your situation; thresholds may change year-on-year.
- Meublé tourisme regime changed significantly at 1 Jan 2026 (unclassified now excluded); 
  confirm your property classification with tax authority if affected.
- BNC contribution rate (25.6%) applies to unregulated liberal activities; regulated activities 
  under Cipav have different rates (23.2%). Verify your activity category.
- Micro-social rate changes on 1 Jan 2026 included shifts in CSG/CRDS composition; actual 
  take-home impact may vary. Confirm with your accountant for your specific case.
