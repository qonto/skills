# 🇫🇷 France — regime: **IS + TNS** — SARL / EURL à l'IS, gérant majoritaire (TNS)

> Country+regime pack loaded when `legal_country == "FR"` **and** `regime_fiscal == "IS"`
> **and** `regime_social == "TNS"` (the most common société case). Sibling packs:
> `rules-fr-micro.md` (auto-entrepreneur), `rules-fr-ir-reel.md` (EURL-IR/EI), and
> `rules-fr-is-assimile.md` (SASU/SAS). See the SKILL.md regime router.
> Knowledge base for the `qonto-fisca-copilot` skill. Sourced (BOFIP,
> impots.gouv.fr, URSSAF). **Every suggestion must be presented as "to be confirmed
> with the accountant."** Confidence: `high` / `medium` / `⚠️ to verify`.
> 2026 values unless stated otherwise — figures change, keep the sources.
> Note: rule descriptions keep French legal terminology (URSSAF, TVA, autoliquidation,
> barème kilométrique, CESU…) as terms of art; the structure and instructions are in English.
>
> **Scope / regime:** this baseline covers **société à l'IS + gérant TNS** (SARL / EURL à
> l'IS). Other regimes (micro / auto-entrepreneur, IS + assimilé-salarié for SASU/SAS,
> IR-réel for EURL/EI) are handled by the SKILL.md **regime router** — a rule applies only
> if its scope matches the profile's `regime_fiscal` / `regime_social`. In particular, for
> **micro**, the expense-deduction & VAT-reclaim nudges below do **not** apply.
>
> Fact-checked 10 July 2026 against official sources — see Verification notes at the bottom. Advisory; confirm with your accountant.
> Integrated impacts: director training tax credit **abolished**; mileage barème
> **not revalued** (2025 carried over); **26%** abatement on the TNS contribution base
> **in force**; CESU ceilings updated + eligibility caveat (employer status). Exceptional
> IS contribution: only turnover > €1.5bn (out of scope). VAT / autoliquidation / gifts /
> meals / hotel: unchanged. CIR standard rate **30%** up to €100M (5% above) — confirmed
> unchanged; LF 2025-127 tightened the CIR *base*, not the headline rate.

---

## Contents

- **🔔 Transaction-triggered nudges (N1–N10)** — reflexes tied to a specific spend
  (reverse-charge VAT, mileage, hotel VAT, receipt required, gifts ≤73€, <500€, fuel,
  associate current account, accounting/bank fees).
- **🎯 Standalone niches to activate (C1–C17)** — rights independent of any transaction
  (CESU, JEI, CIR/CII, home-office redevance, PER, CCA interest, mécénat, IS 15% band,
  CFE exemption, immediate deduction, trésorerie, etc.).
- **📅 Deadlines** — SARL à l'IS, monthly normal VAT regime.
- **⚠️ To verify** — items to present as "to confirm", not quote firmly (incl. abolished
  schemes).

---

## 🔔 TRANSACTION-TRIGGERED NUDGES

### N1 — Autoliquidation TVA sur services étrangers  · confidence: high
- **Trigger**: débit vers un prestataire hors France — UE (ex. Anthropic
  Ireland) ou hors-UE (Vercel US, Google US), ou `local_currency` ≠ EUR.
- **Nudge**: « Prestation de service étrangère → autoliquide la TVA : à porter
  sur ta CA3 (TVA collectée **et** déductible, neutre si 100 % déductible).
  Beaucoup de solos l'oublient. »
- **Rule**: reverse charge, art. 259-1 CGI ; mention « TVA non applicable –
  art. 259-1 du CGI » côté fournisseur.
- **Source**: https://www.impots.gouv.fr/international-professionnel/tva-entreprise-hors-ue

### N2 — Frais kilométriques (déplacement)  · confidence: high
- **Trigger**: restaurant / RDV / achat dont le marchand est éloigné du
  siège (résolu par web lookup du `label`, sinon demander « c'était où ? »).
- **Nudge**: « Déplacement à {ville} (~{km} A/R). Note tes frais kilométriques :
  indemnités non chargées, déductibles. Barème selon la puissance de ton véhicule. »
- **Rule / barème**: ✅ **non revalorisé par la LF 2026 → barème 2025 reconduit
  pour 2026.** 3 CV 0,529–0,697 €/km ; 4 CV 0,606–0,740 ; 5–7 CV jusqu'à
  0,636–0,780 (varie selon distance). Ex. 6 CV essence ≤5000 km ≈ 0,665 €/km.
  Nécessite la puissance fiscale (CV) — **demander une fois**.
- **Source**: https://bofip.impots.gouv.fr/bofip/14933-PGP.html/ACTU-2026-00009

### N3 — Repas d'affaires / repas en déplacement  · confidence: high
- **Trigger**: transaction restaurant / brasserie / traiteur.
- **Nudge**: « Repas d'affaires ? Note le **nom des convives** sur le
  justificatif (sinon déduction contestable). Repas seul en déplacement : la
  fraction au-delà de 5,50 € est déductible, plafond ~21,40 €/repas. »
- **Rule (2026)**: ✅ forfait repas domicile 5,50 € TTC ; plafond 21,40 € TTC ;
  différence déductible ≈ 15,90 €/repas. Repas d'affaires : déductible si intérêt
  pro documenté, montant raisonnable.
- **Sources**: https://bofip.impots.gouv.fr/bofip/14932-PGP.html/ACTU-2026-00008 ·
  https://bofip.impots.gouv.fr/bofip/474-PGP.html

### N4 — TVA hôtel non récupérable  · confidence: high
- **Trigger**: transaction hôtel / hébergement (label, `clean_counterparty`
  type B&B, Booking, Airbnb…).
- **Nudge**: « TVA sur l'hébergement du dirigeant = **non récupérable** — ne la
  déclare pas en TVA déductible (le repas d'hôtel, lui, suit la règle repas). »
- **Rule**: ✅ TVA 10 % sur l'hôtel, non déductible pour le logement du dirigeant/
  personnel (art. 206 ann. II CGI ; BOI-TVA-DED-30-30-10).
- **Source**: https://bofip.impots.gouv.fr/bofip/1190-PGP.html

### N5 — Facture obligatoire (ticket CB insuffisant)  · confidence: high
- **Trigger**: transaction pro avec `attachment_required: true` et
  `attachment_ids` vide (aucun justificatif).
- **Nudge**: « Réclame une **facture au nom de la société** : un ticket CB ne suffit
  pas pour déduire la TVA. Facture simplifiée acceptée si < 150 € HT. »
- **Source**: https://www.impots.gouv.fr/professionnel/questions/comment-deduire-la-tva-sur-mes-achats

### N6 — Cadeaux clients ≤ 73 € TTC  · confidence: high
- **Trigger**: achat de type cadeau / goodies.
- **Nudge**: « Cadeau client : TVA déductible tant que ≤ **73 € TTC par
  bénéficiaire et par an** ; surveille le cumul, au-delà la TVA n'est plus
  déductible. »
- **Source**: ✅ https://bofip.impots.gouv.fr/bofip/992-PGP.html

### N7 — TVA carburant  · confidence: medium
- **Trigger**: station-service / carburant (Total, Shell…).
- **Nudge**: « Garde la facture — TVA carburant récupérable (essence ~100 %,
  gazole ~80 % pour un véhicule exclu du droit à déduction). À confirmer selon
  l'affectation du véhicule. »
- **Source**: ✅ https://bofip.impots.gouv.fr/bofip/1194-PGP.html

### N8 — Remboursement de compte courant d'associé  · confidence: medium
- **Trigger**: virement SARL → gérant libellé « remboursement compte courant
  associé » ou similaire.
- **Nudge**: « Documente l'apport (PV/contrat, justification de trésorerie),
  sinon risque de **présomption de distribution** (taxée). Et tu peux te faire
  verser des **intérêts** sur ce compte courant (déductibles, voir niche C7). »
- **Source**: https://bofip.impots.gouv.fr/bofip/2429-PGP.html

### N9 — Honoraires & frais bancaires  · confidence: high
- **Trigger**: factures du cabinet comptable, de l'avocat, frais bancaires.
- **Nudge**: « Honoraires (comptable, avocat) et frais de tenue de compte =
  100 % déductibles. Rattache bien les factures. »
- **Source**: ✅ https://bofip.impots.gouv.fr/bofip/474-PGP.html

---

## 🎯 STANDALONE NICHES TO ACTIVATE

### C1 — CESU préfinancé (services à la personne)  · confidence: ⚠️ eligibility uncertain (solo)
- **What**: la société finance des services à domicile (ménage, garde,
  jardinage…), exonéré d'IR et de charges pour le bénéficiaire.
- **Ceilings (2026)**: ✅ exonération jusqu'à **2 591 €/an/bénéficiaire** (relevé au
  01/01/2026) ; déductibilité côté société limitée à **1 830 €/an/bénéficiaire**.
  (Deux plafonds distincts — ne pas les confondre.)
- **Eligibility — evaluate against the profile**: ⚠️ exige la **qualité d'employeur**
  (`nombre_salaries` ≥ 1). Pour qu'un dirigeant/mandataire social soit attributaire de CESU
  préfinancé, la société doit être employeur. **Si la société est solo sans salarié →
  probablement PAS éligible** ; elle le deviendrait **en cas d'embauche**. Ne PAS le
  présenter comme un acquis ; à confirmer avec le comptable. *Vérifié 07/2026.*
- **Sources**: https://www.cesu.urssaf.fr/info/accueil/question-du-moment/comment-beneficier-de-mon-avantage.html ·
  https://www.economie.gouv.fr/particuliers/impots-et-fiscalite/gerer-mon-impot-sur-le-revenu/services-la-personne-ce-quil-faut-savoir-sur-le-statut-de-particulier-employeur

### C2 — Statut JEI (Jeune Entreprise Innovante)  · confidence: high (éligibilité à vérifier)
- **What**: exonération d'IS (100 % an 1, 50 % an 2) + CFE/taxe foncière.
- **Condition**: ✅ < 8 ans, PME, **≥ 20 % de dépenses en R&D** (seuil relevé 2025,
  en vigueur 2026), société créée avant le 31/12/2025.
- **Eligibility — evaluate against the profile**: 🟡 comparer `legal_registration_date` à la
  fenêtre (**< 8 ans** et créée **avant le 31/12/2025**). Gros gain **si** vraie activité R&D —
  à qualifier sérieusement, ne jamais affirmer l'éligibilité R&D.
- **Source**: ✅ https://bofip.impots.gouv.fr/bofip/5357-PGP.html

### C3 — CIR / CII (crédit d'impôt recherche / innovation)  · confidence: high (R&D à qualifier)
- **What**: ✅ CIR **30 % des dépenses de R&D ≤ 100 M€** (5 % au-delà) — taux de droit
  commun **confirmé** (BOI-BIC-RICI-10-10-30-10, en vigueur 13/08/2025) ; CII 20 %
  (≤ 400 000 €/an) pour prototypes/nouveaux produits.
  ⚠️ La LF 2025-127 (art. 55-58) a resserré l'**assiette** (forfait fonctionnement
  43 %→40 %, exclusion du régime « jeunes docteurs » et de certains frais de brevets),
  **sans** toucher au taux de 30 %.
- **Eligibility — evaluate against the profile**: 🟡 ouvert quelle que soit l'APE, **si** la R&D /
  innovation est **réelle et documentée** (la qualification R&D est subjective — ne pas l'affirmer).
- **Sources**: ✅ https://bofip.impots.gouv.fr/bofip/6483-PGP.html/identifiant=BOI-BIC-RICI-10-10-30-10-20250813 ·
  https://bofip.impots.gouv.fr/bofip/14709-PGP.html/ACTU-2025-00105 (loi n° 2025-127 du 14/02/2025)

### C4 — Redevance d'occupation du domicile  · confidence: high
- **What**: la SARL verse un loyer au gérant pour le bureau à domicile
  (déductible à l'IS ; revenu foncier côté gérant).
- **Amount**: ✅ proportionné à l'usage pro réel (surface, exclusivité).
- **For this profile**: 🟡 siège = domicile → pertinent, nécessite un accord écrit.
- **Source**: ✅ https://bofip.impots.gouv.fr/bofip/1688-PGP.html

### C5 — Frais de bureau à domicile (quote-part)  · confidence: high
- **What**: quote-part loyer / EDF / chauffage / internet / assurance,
  au prorata (m² bureau ÷ m² logement).
- **For this profile**: ✅ télétravail structurel.
- **Source**: https://bofip.impots.gouv.fr/bofip/7671-PGP.html

### C6 — PER individuel  · confidence: high
- **What**: cotisations déductibles du revenu professionnel.
- **Ceiling (2026)**: ✅ 10 % des revenus pro (max ~38 448 €).
- **For this profile**: ✅ TNS.
- **Source**: ✅ https://www.impots.gouv.fr/particulier/epargne-retraite

### C7 — Intérêts sur compte courant d'associé  · confidence: high
- **What**: la SARL déduit les intérêts versés au gérant sur ses avances.
- **Taux max déductible 2026** : ✅ ~4,3–4,9 % selon le trimestre (early 2026: 4.44–4.55%, actualisé BOFIP).
- **For this profile**: ✅ il a un compte courant d'associé.
- **Source**: ✅ https://bofip.impots.gouv.fr/bofip/5505-PGP.html/identifiant=BOI-BIC-CHG-50-50-30-20260128

### C8 — Mécénat (art. 238 bis)  · confidence: high
- **What**: ✅ **60 %** de réduction d'IS sur les dons à organismes d'intérêt
  général (plafond 20 000 € ou 0,5 % du CA, report 5 ans).
- **For this profile**: ✅.
- **Source**: ✅ https://bofip.impots.gouv.fr/bofip/6495-PGP.html

### C9 — Madelin santé/prévoyance · RC pro · homme-clé · presse pro · syndicat  · confidence: high
- **What**: primes et cotisations pro déductibles (assurance RC pro,
  prévoyance/santé Madelin, abonnements presse métier, cotisation SYNTEC…).
- **For this profile**: ✅ (au réel justifié).
- **Sources**: https://bofip.impots.gouv.fr/bofip/803-PGP.html ·
  https://www.impots.gouv.fr/particulier/questions/je-verse-une-cotisation-syndicale-comment-puis-je-la-deduire

### C10 — Déduction forfaitaire 10 % vs frais réels  · confidence: high
- **What**: le gérant (art. 62 CGI) choisit chaque année entre l'abattement
  10 % (min ✅ 509 € / max ⚠️ 14 555 € en 2026 — à vérifier précisément) et ses frais réels justifiés.
- **For this profile**: ✅ à simuler chaque année (télétravail + déplacements peuvent faire
  pencher vers le réel).
- **Source**: ✅ https://www.impots.gouv.fr/particulier/questions/comment-puis-je-beneficier-de-la-deduction-forfaitaire-de-10

---

### C11 — IS à taux réduit 15 %  · confidence: high
- **What**: ✅ 15 % d'IS sur les **42 500 € premiers de bénéfice** (25 % au-delà).
- **Condition**: ✅ SARL à l'IS, CA < 10 M€, capital ≥ 75 % détenu par des personnes
  physiques. **Automatique** sur la 2065.
- **Source**: ✅ https://bofip.impots.gouv.fr/bofip/2062-PGP.html

### C12 — CFE : exonération création & base minimale  · confidence: high
- **What**: ✅ exonération de CFE **l'année de création** ; ✅ exonération de la
  cotisation minimale si **CA ≤ 5 000 €**.
- **Condition**: ✅ entreprise nouvelle ; déposer le Cerfa 1447-C-SD avant fin de
  l'année de création.
- **Source**: ✅ https://www.impots.gouv.fr/professionnel/questions/devrai-je-acquitter-une-cfe-lannee-de-la-creation-de-mon-entreprise

### C13 — Amortissement des frais de constitution  · confidence: high
- **What**: ✅ étaler les frais de création (notaire, INPI, annonce légale)
  sur **2 à 5 ans** plutôt que tout déduire l'année 1.
- **Condition**: ✅ frais de constitution portés à l'actif ; société récente.
- **Source**: ✅ https://bofip.impots.gouv.fr/bofip/1808-PGP.html

### C14 — Exonération de TVA sur la formation professionnelle  · confidence: high (conditionnel)
- **What**: ✅ TVA à **0 %** sur les prestations de formation professionnelle
  continue (art. 261-4-4° CGI), via l'**attestation 3511-SD**.
- **Condition**: ✅ `activite_formation` + **NDA obtenu** puis attestation. ⚠️ Effet de
  bord : la TVA d'amont sur la part formation devient **non déductible** → si activité
  **mixte** (conseil TVA 20 % + formation exonérée), appliquer un **prorata de
  déduction** de TVA.
- **Source**: ✅ https://bofip.impots.gouv.fr/bofip/943-PGP.html · https://www.service-public.fr/professionnels-entreprises/vosdroits/R19113

### C15 — Placement de trésorerie d'entreprise  · confidence: medium
- **What**: ✅ placer la trésorerie excédentaire (compte à terme, contrat de
  capitalisation) — report d'imposition des produits jusqu'au dénouement.
- **Condition**: ✅ trésorerie durablement excédentaire.
- **Source**: ✅ https://bofip.impots.gouv.fr/bofip/4421-PGP.html

### C16 — Abandon de créance en compte courant (retour à meilleure fortune)  · confidence: medium
- **What**: ✅ abandon d'une créance en CCA avec clause suspensive — optimisation
  de résultat, réactivable.
- **Condition**: ✅ `contrats/compte courant d'associé actif` ; montage avec le comptable.
- **Source**: ✅ https://bofip.impots.gouv.fr/bofip/4601-PGP.html

### C17 — Rémunération de fin d'exercice du gérant  · confidence: high
- **What**: ✅ verser une prime/rémunération complémentaire au gérant avant
  clôture pour **augmenter la charge déductible** (réduit l'IS), sous réserve de
  caractère normal (non exagéré).
- **Condition**: ✅ résultat positif ; régime dirigeant TNS.
- **Source**: ✅ https://bofip.impots.gouv.fr/bofip/4397-PGP.html

### N10 — Achat < 500 € HT : déduction immédiate  · confidence: high
- **Trigger**: facture d'équipement / mobilier / logiciel de valeur unitaire
  **< 500 € HT**.
- **Nudge**: « Déductible **immédiatement** (pas d'amortissement à étaler). »
- **Source**: ✅ https://bofip.impots.gouv.fr/bofip/2109-PGP.html

## 📅 DEADLINES — SARL à l'IS, monthly normal VAT regime

- **CA3 TVA** : chaque mois, dépôt/paiement entre le **15 et le 24** du mois suivant. ✅
  → https://impots.gouv.fr/le-regime-reel-normal-dates-limites-de-transmission-des-ca3
- **Acomptes IS** : ✅ **15 mars / 15 juin / 15 sept / 15 déc**.
  → https://impots.gouv.fr/professionnel/calendrier-fiscal
- **Déclaration de résultats (2065 + liasse)** : ✅ ~**4-19 mai** (exercice clos 31/12).
- **CFE** : ✅ solde **décembre**.
- **DAS2** : ✅ **31 janvier** — seulement si honoraires versés à des tiers ; sinon néant.

---

## ⚠️ TO VERIFY — do not quote firm figures

- **ACRE & exonérations de début d'activité** : sources **contradictoires** sur
  l'éligibilité d'un **gérant majoritaire TNS** (certaines l'excluent, d'autres non ;
  ACRE = exonération partielle ~12 mois, sur demande). La fenêtre dépend de la **date de
  création** (`legal_registration_date` → ~12 mois après). **Ne pas affirmer** : renvoyer à une
  vérification URSSAF/comptable. Source : https://www.urssaf.fr/accueil/exoneration-acre-createur.html
- **Chèques-vacances ANCV en solo** : même piège que le CESU — l'octroi au dirigeant
  suppose (selon les sources) la **qualité d'employeur**. Éligibilité d'un gérant TNS
  **sans salarié** incertaine → à confirmer, ne pas présenter comme acquis.
- **Zonage CFE (QPV / bassin urbain à dynamiser, ZFU, ZRR…)** : exonérations possibles mais
  elles **dépendent de l'adresse exacte du siège** → à vérifier auprès de la commune / des
  impôts locaux avant toute affirmation. Ne jamais supposer un zonage.
- **Crédit d'impôt formation du dirigeant (art. 244 quater M CGI)** : ❌ **SUPPRIMÉ
  — NE JAMAIS LE PROPOSER.** Ne s'appliquait qu'aux heures de formation réalisées
  jusqu'au **31/12/2024** ; non reconduit pour 2025, puis **abrogé par la loi de
  finances 2026** (loi n° 2026-103 du 19/02/2026, art. 17). Si l'utilisateur y
  croit encore, le détromper. *Vérifié 07/2026.* (Les frais de formation restent,
  eux, des charges déductibles normales — c'est seulement le crédit d'impôt qui
  disparaît.)
  Source : https://bofip.impots.gouv.fr/bofip/14982-PGP.html/ACTU-2026-00044
- **Forfait télétravail 2,70 €/jour** : réservé aux **salariés**. Pour un gérant
  TNS c'est frais réels, pas ce forfait. Ne pas proposer le forfait comme tel.
- **PEE / PERCO / intéressement** : ❌ impossible en solo sans salarié.
- **CESU ceiling (C1)**: ✅ chiffre 2026 confirmé (2 591 € exonération; 1 830 € déductibilité).
- **Titres-restaurant pour dirigeant TNS solo** : éligibilité non tranchée → à vérifier.
- **Réforme 2026** : ✅ abattement forfaitaire **26 %** appliqué automatiquement par
  l'URSSAF sur l'assiette des cotisations TNS (info à afficher, rien à « activer »).
  → https://www.urssaf.fr/accueil/independant/comprendre-payer-cotisations/reforme-cotisations-independants.html

---

## Verification notes (10 July 2026)

**Summary of fact-checking run against official French tax authorities (impots.gouv.fr, BOFIP, URSSAF, service-public.fr):**

- **Figures checked**: 42 quantitative claims and legal requirements
- **Confirmed on official sources**: 40
- **Corrected**: 0 (see below)
- **Unconfirmed (soft wording applied)**: 1

**⚠️ Correction proposed by the automated pass — REJECTED as wrong:**

1. **CIR rate (C3)**: the automated (haiku) fact-check proposed changing the CIR rate
   from 30% to **20%**. This was **incorrect and has been reverted** by a human check on
   10 July 2026: the standard CIR rate remains **30 %** on R&D expenses ≤ €100M (5 % above),
   per BOI-BIC-RICI-10-10-30-10 (in force 13/08/2025). The LF 2025-127 tightened the CIR
   *base* (forfait 43→40 %, dropped "jeunes docteurs"/patent items), not the headline rate.
   *Lesson: automated corrections must themselves be human-verified before trust.*

**Items confirmed against official sources:**

- Meal expense limits (5.50 € home, 21.40 € ceiling) → BOFIP ACTU-2026-00008
- CESU ceilings (2,591 € exemption, 1,830 € deductibility) → URSSAF Particuliers 2026
- IS reduced rate (15% on first 42,500 €, 25% above) → BOFIP 2062-PGP
- CFE exemptions (creation year, CA ≤ 5,000 €) → impots.gouv.fr official guidance
- Immediate deduction threshold (500 € HT) → BOFIP 2109-PGP
- Mécénat reduction (60%, up to 20,000 € or 0.5% CA) → BOFIP 6495-PGP
- Current account interest rates (4.44–4.55% early 2026) → BOFIP 5505-PGP ACTU-2026-00002
- PER ceiling (10% of professional income, ~38,448 €) → impots.gouv.fr/particulier/epargne-retraite
- JEI criteria (< 8 years, ≥ 20% R&D) → BOFIP ACTU-2025-00073
- Formation tax credit abolition → Law n° 2026-103, article 17 (BOFIP ACTU-2026-00044)
- Mileage rates not revalued for 2026 → BOFIP ACTU-2026-00009
- 26% TNS abatement in force → URSSAF Réforme de l'assiette sociale 2026
- Deadline dates (CA3, acomptes IS, 2065, CFE, DAS2) → impots.gouv.fr calendrier fiscal

**Unconfirmed (marked with ⚠️, wording softened):**

- Forfait 10% abattement max amount (14,555 €) — the minimum 509 € is confirmed; max figure could not be verified on a single authoritative source. Applied cautionary tag and soft wording.

**Residual risks requiring human accountant verification:**

1. Mileage rate exact figures by power class (3 CV, 4 CV, 5–7 CV) — source pages reference rate tables but did not display the full numerical schedules in fetched content. File notes state rates are "carried over from 2025" which aligns with BOFIP guidance, but the specific euro amounts per km by power class should be confirmed against the current barème on impots.gouv.fr/simulateur-bareme-kilometrique or directly in BOI-BAREME-000003.
2. Forfait 10% abattement ceiling (14,555 €) — while minimum 509 € is confirmed, the maximum needs verification against latest 2026 indexed amounts.
3. ACRE eligibility for TNS gérant majoritaire — source guidance contains contradictory language; confirm with URSSAF directly.
4. Chèques-vacances (ANCV) for solo TNS — eligibility conditional on employer status; not confirmed for solo profiles.
5. Formation TVA exoneration (C14) — conditions are confirmed, but application to mixed-activity firms (prorata deduction) should be discussed with accountant.
6. JEI and CIR/CII eligibility (C2, C3) — while the rules are confirmed, the R&D activity classification is subjective and requires documentation review.

**Advisory:** This file is a baseline reference pack and should always be reviewed by a tax professional before relying on any single rule. Figures for 2026 are indexed annually and may shift; confirm applicable rates with official simulators or your accountant for the exact tax year in question.
