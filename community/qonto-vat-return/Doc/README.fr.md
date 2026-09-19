# 🧾 qonto-vat-return — Ta CA3 case par case, prête à recopier

> **Skill #3** · Hackathon Qonto × Anthropic MCP (10-13/07/2026)
> Déclaration de TVA CA3 (formulaire 3310-CA3) préparée depuis les données Qonto réelles · **0 écriture — lecture seule intégrale**
> ⚠️ **Aide à la préparation, PAS une déclaration** : le skill ne télédéclare rien, validation expert-comptable recommandée

---

## 🎯 Le pitch

Chaque mois, la même corvée : reconstituer la TVA collectée et la TVA déductible, puis reporter les bons montants dans les bonnes cases sur impots.gouv.fr — en espérant ne pas se tromper de ligne. `qonto-vat-return` fait le travail de préparation depuis le compte Qonto :

1. **TVA collectée par taux** — bases et taxes 20 / 10 / 5,5 / 2,1 % → cases 08, 09, 9B, 11, ligne 16 ; **sur les débits ou sur les encaissements selon le fait générateur détecté** (`vat_payment_condition: "on_receipts"` → la collecte suit les paiements *reçus* du mois, matchés aux factures)
2. **TVA déductible** — somme des `vat_amount` des débits + factures fournisseurs (dédupliquées), immobilisations (case 19) séparées si détectables, le reste en case 20 — **annoncée comme plancher** avec le compte des débits non renseignés
3. **TVA nette** — ligne 28 à payer ou lignes 25/27 crédit à reporter, calcul au centime + arrondi à l'euro du formulaire
4. **Contrôles de cohérence** — vs mois précédents, vs paiements DGFIP passés, vs relevés de compte — chaque écart signalé ⚠️ avant que tu recopies quoi que ce soit

Le tout dans **un tableau « case du formulaire → montant → justification »** prêt à recopier sur impots.gouv.fr.

## 📋 Prérequis

| Prérequis | Détail | Obligatoire |
|---|---|---|
| Compte Qonto **production** | Exigence du hackathon ; le skill s'adapte à toute organisation (`get_organization` d'abord, zéro valeur en dur) | ✅ |
| Pays | **La CA3 est un formulaire français.** Autres pays Qonto (DE, ES, IT…) : dégradation propre — synthèse TVA collectée/déductible générique, jamais de mapping vers des cases françaises | ℹ️ détecté |
| MCP Qonto connecté | Via le connecteur officiel (claude.ai / Claude Desktop), login OAuth | ✅ |
| Régime réel (CA3) | Le réel simplifié (CA12 + acomptes) est **hors scope** — le skill le détecte, le dit, et rappelle que ce régime est **supprimé au 01/01/2027** (art. 38 LF 2025) | ℹ️ détecté |
| Factures dans Qonto | Plus les factures clients/fournisseurs vivent dans Qonto, plus le tableau est précis ; sinon le skill travaille depuis les transactions et annonce ses limites | ⭕ recommandé |
| Historique ≥ 6 mois | Nourrit la détection de périodicité et les contrôles de cohérence ; en dessous, dégradation honnête | ⭕ |

## ⚙️ Fonctionnement global

![Fonctionnement global](assets/flow.fr.png)

1. **Cadrage — détecté, jamais demandé** : périodicité depuis l'historique DGFIP (débits mensuels → CA3 mensuelle ; trimestriels → CA3 trimestrielle, permise si TVA annuelle < 4 000 €) ; réel simplifié → hors scope, annoncé, avec le rappel de sa suppression au 01/01/2027 ; **fait générateur** lu sur les factures clients (`vat_payment_condition`) — débits ou encaissements, géré facture par facture si le portefeuille est mixte
2. **TVA collectée par taux** : sur les débits → factures émises de la période ; **sur les encaissements → transactions entrantes matchées aux factures clients** (montant + contrepartie + référence), ventilation TVA des factures matchées ; avoirs déduits ; encaissements sans facture → listés à part, jamais taxés ni ignorés en silence
3. **TVA déductible** : `vat_amount` des débits + `total_tax_amount` des factures fournisseurs, dédupliqués ; immobilisations (case 19) si détectables, sinon tout en case 20 avec explication ; report de crédit (case 22) depuis la déclaration précédente — **total annoncé comme plancher** ; **autoliquidation (achats UE / imports) : contreparties étrangères détectées → signalées « à vérifier avec l'expert-comptable », jamais calculées en silence**
4. **Position nette** : ligne 23 (total déductible) → ligne 28 TVA nette à payer, ou lignes 25/27 crédit à reporter (ligne 26 remboursement : mentionnée, choix de l'utilisateur avec son comptable) ; calcul au centime + arrondi à l'euro du formulaire
5. **Contrôles de cohérence** : nette vs médiane des paiements DGFIP passés (⚠️ si écart > 30 %, expliqué) ; bases et mix de taux vs mois précédents ; transactions vs totaux des relevés (`list_statements`) ; encaissements non matchés listés
6. **Rapport** : tableau CA3 case par case avec justifications, tableau des contrôles ✅/⚠️, rappel d'échéance (entre le 15 et le 24 du mois suivant) — + dashboard HTML si l'hôte affiche les fichiers

## 🏗 Schéma fonctionnel

![Schéma fonctionnel](assets/functional.fr.png)

**Le point clé** : ce skill est en **lecture seule intégrale** — aucun outil d'écriture, aucun trait pointillé dans le schéma. Il ne peut ni télédéclarer, ni payer, ni modifier quoi que ce soit. La seule action qui suit est la tienne : recopier les cases sur impots.gouv.fr (idéalement après validation par ton expert-comptable).

## 🧾 Les cases de la CA3 couvertes

| Case / ligne | Libellé officiel | Comment le skill la remplit |
|---|---|---|
| 01 | Ventes, prestations de services (base HT) | Somme des bases taxées de la période (débits ou encaissements selon le fait générateur) |
| 08 · 09 · 9B · 11 | Base et taxe par taux 20 / 5,5 / 10 / 2,1 % | Ventilation TVA des factures (émises ou matchées aux paiements reçus), avoirs déduits |
| 16 | Total TVA brute due | Somme des taxes par taux |
| 03 · 17 · A4/I | Acquisitions intracom · imports (autoliquidation) | **Jamais calculées** — transactions candidates signalées « à vérifier avec l'expert-comptable » |
| 19 | TVA déductible — immobilisations | Seulement si détectable (label, description fournisseur, achat d'équipement) ; sinon expliqué |
| 20 | TVA déductible — autres biens et services | `vat_amount` des débits + factures fournisseurs, dédupliqués — **plancher annoncé** |
| 22 | Report de crédit antérieur | Depuis la CA3 précédente (fournie ou inférée 🟡, à confirmer) |
| 23 | Total TVA déductible | 19 + 20 + 21 + 22 |
| 25 · 27 (· 26) | Crédit de TVA · crédit à reporter (· remboursement) | Si déductible > collectée ; le remboursement reste un choix utilisateur/comptable |
| 28 · 32 | TVA nette due · total à payer | Si collectée > déductible — au centime + arrondi à l'euro du formulaire |

## 🎬 Vidéo de démo

La démo ≤ 3 min jointe à la PR suit le storyboard : la corvée mensuelle → détection du régime (encaissements !) → le tableau case par case → **le montant qui tombe au centime sur le calcul manuel du comptable** → contrôles de cohérence + dashboard. Le script détaillé de tournage est conservé en interne (hors dépôt).

## 📤 Formats de sortie (où atterrit la déclaration ?)

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableau CA3 case par case (case → libellé → montant → justification) + tableau des contrôles ✅/⚠️ | **Toujours** — c'est la base |
| **Dashboard interactif** | Fichier/artifact **HTML** : vue « formulaire », ventilation par taux, historique vs paiements DGFIP | Si l'hôte affiche les fichiers (artifacts claude.ai, Claude Desktop, Claude Code) ; sinon repli automatique sur les tableaux |
| **Rien d'autre** | Aucune télétransmission, aucune écriture Qonto | Jamais — c'est le design |

## 💡 Améliorations possibles (dans les clous du hackathon)

| Idée | Effort | Note |
|---|---|---|
| Pré-contrôle des pièces : `list_transaction_attachments` sur les débits déduits, justificatifs manquants signalés | Faible | Renforce le dossier en cas de contrôle |
| Chaînage avec `qonto-tax-pilot` (skill #1) : la CA3 préparée alimente la provision du coffre fiscal | Faible | Les deux skills partagent la même détection du fait générateur |
| Multi-MCP optionnel : brouillon d'email à l'expert-comptable (Gmail détecté dynamiquement) | Faible | Le cœur reste 100 % Qonto |
| Modules TVA par pays (DE USt-VA, ES modelo 303, IT LIPE…) | Moyen | Qonto est paneuropéen ; même moteur, autre mapping de cases |

## ⚡ Optimisation de détection (optimisation terrain)

La TVA est prélevée par **prélèvement SEPA** → l'historique DGFIP se cherche d'abord dans les **prélèvements sortants**, puis en fusionnant les graphies multiples de la DGFIP (majuscules, casse mixte, sigle) en un seul tiers.

## 🛡 Garde-fous

- **Aide à la préparation, PAS une déclaration** : aucun outil d'écriture, aucune télétransmission — le skill ne peut rien déposer, c'est toi (ou ton comptable) qui recopies
- **Validation expert-comptable recommandée dans chaque rapport** — surtout autoliquidation, immobilisations et report de crédit
- Jamais d'invention : pas de cases françaises pour une société étrangère, pas de taux deviné sur un débit non renseigné, pas d'autoliquidation calculée en silence
- Déductible = **plancher annoncé** avec le compte des débits non renseignés ; encaissements non matchés listés
- IBAN masqués (4 derniers chiffres) ; pagination ≤ 50 partout

---

*Documentation FR (pilotage). Version jury : `README.en.md`. Livrable PR : `SKILL.md`. Procédure pas-à-pas : `docs/PROCEDURE.fr.md`. Docs riches : `docs/doc-qonto-vat-return.fr.html` · `docs/doc-qonto-vat-return.fr.docx`.*
