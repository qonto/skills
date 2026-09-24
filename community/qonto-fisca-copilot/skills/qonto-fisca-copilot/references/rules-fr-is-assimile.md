# 🇫🇷 France — regime: **IS + assimilé-salarié** — SASU / SAS (président)

> Loaded when `regime_fiscal == "IS"` **and** `regime_social == "assimilé-salarié"`.
> Fact-checked 10 July 2026 against official sources — see Verification notes at the bottom. Advisory — end every suggestion with "confirm with your accountant".
>
> **Reuse `rules-fr-is-tns.md` for the company-level rules** — a SASU/SAS is à l'IS, so its
> **transaction nudges (N1–N10)** and **IS niches** (15 % band, JEI, CIR/CII, CFE, mécénat,
> home-office redevance, immediate deduction, etc.) are **identical**. This pack only
> **overrides the SOCIAL / rémunération block**, where the président (assimilé-salarié)
> differs sharply from a gérant TNS.

## ✅ KEEP from `rules-fr-is-tns.md`
- All transaction nudges **N1–N10** (reverse-charge VAT, hotel VAT, meals, mileage, <500€,
  gifts ≤73€, fuel, invoice-required, associate current account, honoraires) — deducted at
  the **company** level.
- IS niches: **IS 15 % band**, **JEI**, **CIR/CII**, **CFE**, **mécénat**, redevance domicile.

## 🔴 DROP (do NOT apply to an assimilé-salarié)
- **Madelin** — TNS-only. A président assimilé uses salaried-style cover (mutuelle/prévoyance
  collective), not a Madelin contract.
- **26 % TNS abatement** on the social base — the président pays **salaried** contributions,
  not TNS ones. → https://www.urssaf.fr/accueil/independant/comprendre-payer-cotisations/reforme-cotisations-independants.html
- **The dividend "10 % of capital" threshold** — that is a **SARL-gérant-majoritaire-TNS**
  rule; it does **not** apply to SASU/SAS. Use A3 instead.

## 🎯 ADD (assimilé-specific)

### A1 — ACRE for the president · confidence: high
- ✅ **25 % exoneration of social contributions in the first 12 months**, income-capped
  (~€36,045–€48,060 degressive band, 2026 — PASS = €48,060). Unlike a gérant majoritaire TNS, the SASU/SAS
  president **is** eligible.
- **Source**: https://www.urssaf.fr/accueil/exoneration-acre-createur.html

### A2 — Social regime: assimilé-salarié · confidence: medium (rate ⚠️)
- ⚠️ **Contributions on gross salary (~42–45 % combined employee + employer)**,
  AGIRC-ARRCO complementary pension, **no unemployment insurance**. ⚠️ **No single flat 2026 rate —
  use the URSSAF simulator.** Heavier than TNS on salary, but full salaried cover.
- **Source**: https://mon-entreprise.urssaf.fr/documentation/dirigeant/assimil%C3%A9-salari%C3%A9

### A3 — Dividends: 40 % allowance, NO 10 % threshold · confidence: high
- ✅ **SASU/SAS dividends get the 40 % abattement** (if barème option) + ✅ **18.6 % CSG-CRDS** (as of 2026), and are
  **not** subject to the 10 %-of-capital social-charge threshold (the key advantage vs SARL-TNS).
- **Source**: https://bofip.impots.gouv.fr/bofip/2218-PGP.html

### A4 — PER (assimilé) · confidence: ⚠️ ceiling depends on the reference year
- ✅ **Deductible up to 10 % of professional income, capped at 8× PASS** (a floor of 10 % of
  PASS applies for low income), 3-year carry-over.
- ⚠️ **Exact max depends on the reference PASS — do NOT quote one firm figure**: 10 % × 8 × PASS 2026
  (€48,060) = **€38,448**; on PASS 2025 (€47,100) = **€37,680**. The applicable year depends on the
  contribution/declaration timing → confirm with the accountant. (Human check 10 July 2026:
  the earlier "€41,136" was an old PASS value and wrong; the automated pass's flat "€37,680" is only
  correct for the 2025 PASS.)
- **Sources**: https://bofip.impots.gouv.fr/bofip/1124-PGP.html/identifiant=BOI-IR-BASE-20-50-20-20260217 ·
  https://www.impots.gouv.fr/particulier/epargne-retraite

### A5 — Salary vs dividends arbitrage · confidence: high
- ✅ **Salary is deductible from the IS result** (but ⚠️ ~42–45 % social); ✅ **dividends bear no social
  charges** (only PFU/IR + 40 % allowance) but ✅ **aren't deductible**. Model both — it's the central
  SASU optimization.
- **Source**: https://bofip.impots.gouv.fr/bofip/2065-PGP.html

## Verification notes (10 July 2026)

**Figures checked: 8** — includes a second human (Opus) pass on 10 July 2026.
- ✅ **Confirmed on official sources: 6**
  - ACRE exoneration rate (25%) and income thresholds (€36,045–€48,060, PASS 2026 = €48,060)
  - Dividend 40% allowance
  - CSG-CRDS rate on dividends (18.6% as of 2026)
  - PER deductibility mechanism (10% of professional income, capped at 8× PASS)
  - Salary deductibility from IS
  - Dividends not subject to social charges
  
- ⚠️ **To verify with accountant: 2**
  - Exact assimilé-salarié combined social contribution rate for 2026 (URSSAF confirms 42–45% but varies by situation; use simulator for precise figure)
  - **PER ceiling exact amount** — depends on the reference PASS (€38,448 on 2026 PASS vs €37,680 on 2025 PASS); do not quote a single figure.

- ✗→ **Corrected by the human pass: 1**
  - The automated (haiku) pass had "fixed" the PER ceiling to a flat **€37,680**; the human (Opus) pass
    found that is only the 2025-PASS value and softened it to a ⚠️ range (€37,680–€38,448). The original
    "€41,136" was an old (2022) PASS value and wrong.

**Residual risk:**
- ACRE eligibility and rate evolution in 2026 are subject to regulatory updates; confirm latest URSSAF guidance.
- Assimilé-salarié social contribution rates vary by specific contribution type; use official URSSAF simulator (mon-entreprise.urssaf.fr) for individual modeling.
- PER ceiling depends on the reference year and prior-year professional income — confirm the exact applicable amount with the accountant.
