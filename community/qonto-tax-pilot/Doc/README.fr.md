# 🧭 qonto-tax-pilot — Prédire le fisc, puis mettre l'argent à l'abri

> **Skill #1 · candidat principal** · Hackathon Qonto × Anthropic MCP (10-13/07/2026)
> **Validé de bout en bout sur un compte de production réel** : provision calculée → demande MCP → approbation SCA dans l'app → virement réellement exécuté

---

## 🎯 Le pitch

La première cause de mort des TPE, ce n'est pas le manque de chiffre d'affaires — c'est **la TVA déjà dépensée**. `qonto-tax-pilot` transforme le compte Qonto en copilote fiscal :

1. **Échéancier fiscal chiffré** — quand tombe chaque impôt et combien (TVA, acomptes & solde IS, CFE, PFU dividendes), estimé depuis l'historique réel, chaque ligne avec un tag de confiance 🟢 vu dans l'historique · 🟡 estimé · 🔵 conditionnel
2. **Projection de trésorerie 90 jours** par compte — point bas daté, franchissements de seuils, simulations « et si »
3. **Provision mensuelle** — TVA nette du mois (**sur encaissements** si c'est le régime détecté !) + IS/12 + CFE/12
4. **Action sécurisée** — demande de virement vers le sous-compte impôts ; l'argent ne bouge **que** après l'approbation SCA de l'utilisateur dans l'app Qonto

## 📋 Prérequis

| Prérequis | Détail | Obligatoire |
|---|---|---|
| Compte Qonto **production** | Exigence du hackathon ; le skill s'adapte à toute organisation (`get_organization` d'abord) | ✅ |
| Pays | **Calendrier fiscal complet : France.** Autres pays Qonto (DE, ES, IT…) : dégradation propre — projection + provision TVA génériques, jamais d'échéance inventée | ℹ️ détecté |
| MCP Qonto connecté | Via le connecteur officiel (claude.ai / Claude Desktop), login OAuth | ✅ |
| Sous-compte « impôts » | Créé une fois dans l'app Qonto (Comptes → Créer un sous-compte) — le MCP ne sait pas le créer. Le skill le détecte par son nom (taxe/tax/impôt/TVA) | ⭕ recommandé — sinon le skill calcule sans agir |
| Historique ≥ 6 mois | En dessous, le skill dégrade honnêtement (tags 🟡, avertissement) | ⭕ |
| Société française à l'IS | Hypothèse par défaut ; le skill adapte son discours sinon | ⭕ |

## ⚙️ Fonctionnement global

![Fonctionnement global](assets/flow.fr.png)

1. **Analyse de l'historique** (24-36 mois, paginé ≤ 50, **au moins les 2 exercices précédents**) : les cadences fiscales (acomptes IS trimestriels, CFE de décembre, rythme de TVA) ne se voient que sur des années pleines, et la comparaison N-1/N-2 nourrit la projection. **Détection automatique du régime ET de la périodicité de TVA** — CA3 mensuelle ou trimestrielle (trimestrielle si TVA annuelle < 4 000 €), simplifié (2 acomptes/an + CA12), et TVA sur les débits vs **sur les encaissements** (`vat_payment_condition` des factures). ⚠️ Le régime simplifié est **supprimé au 01/01/2027** (LF 2025) : le skill prévient les utilisateurs en CA12 de la bascule vers la CA3
2. **Échéancier fiscal** daté et chiffré (tableau de référence ci-dessous)
3. **Projection 90 jours** : solde + récurrences + factures clients (retard historique par client intégré) + factures fournisseurs + échéances fiscales
4. **Provision du mois** : TVA collectée (sur les paiements reçus si `on_receipts`) − TVA déductible (somme des `vat_amount`, annoncée comme plancher si des débits sont non renseignés) + IS/12 + CFE/12
5. **Demande de virement** (uniquement avec consentement explicite) : `create_multi_transfer_request` avec le détail du calcul dans la note — visible au moment de l'approbation
6. **Approbation SCA** dans l'app Qonto → l'argent bouge → rapport final

## 🏗 Schéma fonctionnel

![Schéma fonctionnel](assets/functional.fr.png)

**Le point clé de sécurité** : le trait plein (lecture) ne présente aucun risque ; le trait pointillé (écriture) exige le consentement explicitement donné dans la conversation, et ne produit qu'une *demande* — c'est la SCA (2FA) du titulaire du compte, dans l'app Qonto, qui déplace l'argent. Ni Claude ni le MCP ne le peuvent. **C'est le modèle de sécurité, pas une limitation.**

## 📅 Échéancier fiscal de référence (société à l'IS, clôture 31/12)

| Échéance | Impôt | Estimation du montant |
|---|---|---|
| Mensuelle ou trimestrielle ~15-24 (réel normal ; trimestrielle si TVA annuelle < 4 000 €) | TVA CA3 | Médiane des paiements récents ; affiné par collectée−déductible |
| Juillet 55 % + décembre 40 % (simplifié — **supprimé au 01/01/2027**, LF 2025) | Acomptes TVA | Dernière CA12 / historique |
| 15/03 · 15/06 · 15/09 · 15/12 | Acomptes IS (2571) | Acomptes passés, sinon IS N-1 ÷ 4 ; **aucun si IS N-1 < 3 000 €** |
| 15/05 | Solde IS (2572) | IS N-1 estimé − acomptes |
| 15/06 (si ≥ 3 000 €) + 15/12 | CFE | Paiement de l'an dernier |
| Le 15 du mois suivant la distribution | Dividendes — **le skill demande qui est l'actionnaire** | Personne physique → PFU 30 % (2777) à provisionner · **Holding (régime mère-fille)** → pas de PFU, exonération 95 %, quote-part 5 % imposée chez la holding — quasi rien à provisionner ici. Jamais supposé, toujours demandé |

## 🎬 Vidéo de démo

La démo ≤ 3 min jointe à la PR suit le storyboard : problème → échéancier & projection → provision → **approbation SCA filmée sur iPhone** → dashboard. Le script détaillé de tournage est conservé en interne (hors dépôt).

## 📤 Formats de sortie (où atterrit l'échéancier ?)

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown (échéancier, provision, alertes) | **Toujours** — c'est la base |
| **Dashboard interactif** | Fichier/artifact **HTML** : courbe 90 j, échéancier ✅/⚠️, jauge du coffre | Si l'hôte affiche les fichiers (artifacts claude.ai, Claude Desktop, Claude Code) ; sinon repli automatique sur les tableaux |
| **Note de la demande Qonto** | Texte joint à la demande de virement, visible à l'approbation SCA | À chaque provision créée |

## 🔔 UX de validation (les canaux, dans l'ordre de la démo)

| Canal | Fourni par | Contenu |
|---|---|---|
| Notification push (mobile) | Natif Qonto | « Demande de virement en attente » → détail → approuver (SCA) / refuser |
| Section « Demandes » (app + web) | Natif Qonto | Demandes en attente, avec notre note de calcul complète |
| Dashboard HTML | Le skill | Échéancier + courbe 90 j + état du coffre |
| Conversation Claude | Le skill | Tableau de provision + « demande créée, approuve dans l'app » |

## ✅ Éprouvé sur compte réel

- Flux complet validé de bout en bout sur un compte de production : calcul de la provision → demande de virement MCP → approbation SCA → argent réellement déplacé sur le sous-compte, solde vérifié
- Virement interne **auto-catégorisé « Impôts et taxes »**, justificatif facultatif natif
- Pièges API vérifiés : `credit_account_currency` obligatoire (422 sinon) · `decline_request` exige `request_type: "multi_transfers"` (pluriel) · pas d'outil MCP de création de sous-compte

## 💡 Améliorations possibles (dans les clous du hackathon)

| Idée | Effort | Note |
|---|---|---|
| URSSAF/TNS pour les EURL (dirigeant TNS) | Moyen | Élargit la cible au-delà des SASU à l'IS |
| Multi-MCP optionnel : rappel d'échéance dans Google Calendar | Faible | Détection dynamique — s'ajoute si le MCP est présent |
| Mode « atterrissage annuel » : projection IS de l'année en cours | Moyen | Réutilise le moteur de récurrences |
| Export du rapport en artifact interactif (sliders what-if) | Faible | Déjà maquetté (P12 dashboard) |

## ⚡ Optimisation de détection (optimisation terrain)

Les impôts français (TVA, acomptes IS, CFE) sont prélevés par **prélèvement SEPA** → le skill cherche d'abord dans les **prélèvements sortants** (`operation_type: direct_debit`) avant de matcher les noms — beaucoup moins de bruit que de scanner tous les débits. Et la DGFIP apparaît sous plusieurs graphies (« DGFIP », « DIRECTION GENERALE DES FINANCES PUBLIQUES », « Direction Générale des Finances Publiques ») : normalisées et fusionnées en un seul tiers.

## 🛡 Garde-fous

- **Jamais** de demande de virement sans confirmation explicite dans la conversation en cours ; jamais présentée comme exécutée
- Estimations ≠ déclarations : recommander la validation par l'expert-comptable
- Dégradation honnête si historique < 6 mois ; IBAN masqués (4 derniers chiffres) ; pagination ≤ 50 partout
- Répétitions : `decline_request` après chaque test

---

*Documentation FR (pilotage). Version jury : `README.en.md`. Livrable PR : `SKILL.md`. Procédure pas-à-pas : `docs/PROCEDURE.fr.md`. Docs riches : `docs/doc-qonto-tax-pilot.fr.html` · `docs/doc-qonto-tax-pilot.fr.docx`.*
