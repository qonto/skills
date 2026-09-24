# 🌍 qonto-carbon-ledger — Ton relevé bancaire est un registre carbone qui s'ignore

> **Hackathon Qonto × Anthropic MCP (10-13/07/2026)** · Agent Skill pour le MCP Qonto
> **100 % lecture seule** : le skill estime et explique, il n'écrit rien, ne déplace rien, ne vend rien.

---

## 🎯 Le pitch

Le bilan carbone, les TPE ne le font jamais — pas par désintérêt, mais **faute de données**, de temps et de budget consultant. Or les dépenses bancaires SONT une donnée : chaque euro dépensé a une empreinte. `qonto-carbon-ledger` lit le compte Qonto et en tire :

1. **Empreinte annuelle approchée** — méthode dépenses : les débits classés par postes d'émission × **facteurs monétaires** (kgCO2e/€) type Base Empreinte ADEME, embarqués en statique, **sourcés et millésimés** — incertitude ±50 % affichée sur chaque chiffre
2. **Postes dominants** — les 2-3 postes qui concentrent l'essentiel des émissions, rapprochés des montants réellement dépensés
3. **Tendance** — sur 24-36 mois d'historique, année par année
4. **3 leviers chiffrés** — les actions les plus efficaces au regard des dépenses réelles (le levier n°1 est souvent gratuit), jamais de compensation vendue

C'est un **pré-bilan d'orientation**, pas un bilan réglementaire — et le skill le martèle lui-même.

## 📋 Prérequis

| Prérequis | Détail | Obligatoire |
|---|---|---|
| Compte Qonto **production** | Le skill s'adapte à toute organisation (`get_organization` d'abord, zéro donnée en dur) | ✅ |
| Pays | **Facteurs calibrés France / UE.** Autres pays Qonto (DE, ES, IT…) : méthode identique, facteurs à adapter (mix électrique, niveaux de prix) — annoncé clairement, estimation quand même produite et taguée | ℹ️ détecté |
| MCP Qonto connecté | Via le connecteur officiel (claude.ai / Claude Desktop), login OAuth | ✅ |
| Historique ≥ 6 mois | En dessous : annualisation avec avertissement explicite, jamais d'extrapolation silencieuse. 24-36 mois pour la tendance | ⭕ |
| MCP Datagouv | Optionnel — recoupement des facteurs avec les référentiels ADEME ; sinon facteurs embarqués (sourcés, millésimés) | ⭕ |
| Labels Qonto | Optionnels — améliorent la classification des débits ambigus | ⭕ |

## ⚙️ Fonctionnement global

![Fonctionnement global](assets/flow.fr.png)

1. **Lecture du registre** (24-36 mois, paginé ≤ 50, côté débit) : transactions par compte + labels + factures fournisseurs — la matière première existe déjà, rien à saisir
2. **Périmètre honnête** : la méthode dépenses couvre les achats de biens, services et énergie. Exclus et **annoncés comme exclus** : virements internes, salaires, impôts, TVA, remboursements d'emprunt, dividendes — les flux financiers n'ont pas de facteur d'émission
3. **Classification par postes** : contrepartie normalisée (graphies fusionnées) + labels + factures fournisseurs → énergie (carburant / électricité / gaz séparés quand c'est possible — les facteurs varient ×10), déplacements (avion / train / route), numérique & cloud, achats de biens, services, restauration, assurance & frais bancaires. Les débits ambigus vont dans un poste « non classé » visible, avec sa part annoncée
4. **Conversion HT** : les facteurs monétaires s'appliquent au HT — `vat_amount` quand il existe, sinon ÷ 1,20 (annoncé). Les gros achats ponctuels (≥ ~5 000 €) sont isolés pour ne pas se déguiser en émission récurrente
5. **Facteurs monétaires** embarqués (type Base Empreinte ADEME, millésime 2023-2024) — chaque ligne affichée avec source + millésime ; recoupement Datagouv proposé si le MCP est présent
6. **Rapport** : empreinte ~N tCO2e/an **avec sa fourchette**, répartition par poste, tendance, 3 leviers classés par impact estimé et coût (gratuit / économise / coûte)

## 🏗 Schéma fonctionnel

![Schéma fonctionnel](assets/functional.fr.png)

**Que des traits pleins** : ce skill est 100 % lecture. Aucune écriture, aucune demande de virement, aucun paiement — il n'y a littéralement rien à approuver. Le seul livrable est de l'information : des tableaux et un dashboard.

## 🧮 Facteurs d'émission embarqués (indicatifs, méthode dépenses)

| Poste | Facteur (kgCO2e/€ HT, valeur centrale indicative) |
|---|---|
| Énergie — carburant | ~1,5 |
| Énergie — électricité (mix FR) | ~0,25 |
| Énergie — gaz / chauffage | ~1,9 |
| Déplacements — avion | ~1,2 |
| Déplacements — train (FR) | ~0,05 |
| Déplacements — route, taxi/VTC, fret | ~0,5 |
| Numérique, cloud & SaaS | ~0,3 |
| Achats de biens & équipement | ~0,5 |
| Services & prestations intellectuelles | ~0,15 |
| Restauration & alimentation | ~0,7 |
| Assurance & frais bancaires | ~0,1 |

> Ratios monétaires type Base Empreinte ADEME, millésime 2023-2024, **±50 % et plus** — c'est inhérent à la méthode monétaire (un vol pas cher ≠ peu d'émissions). L'incertitude est imprimée sur chaque chiffre, pas reléguée en note de bas de page.

## 📤 Formats de sortie (où atterrit le bilan ?)

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown : empreinte + fourchette, répartition par poste (avec facteur, source, millésime par ligne), tendance, 3 leviers | **Toujours** — c'est la base |
| **Dashboard interactif** | Fichier/artifact **HTML** : jauge d'empreinte avec bande d'incertitude, barres par poste, tendance, leviers | Si l'hôte affiche les fichiers (artifacts claude.ai, Claude Desktop, Claude Code) ; sinon repli automatique sur les tableaux |

## 🎬 Vidéo de démo

La démo ≤ 3 min jointe à la PR suit le storyboard : le problème (les TPE n'ont « pas de données ») → lecture du compte et classification → l'honnêteté sur l'incertitude → **le moment « ton empreinte en 2 minutes »** → dashboard et leviers. Le script détaillé de tournage est conservé en interne (hors dépôt).

## 💡 Améliorations possibles (dans les clous du hackathon)

| Idée | Effort | Note |
|---|---|---|
| Recoupement Datagouv automatique (référentiels ADEME à jour) | Faible | Multi-MCP optionnel — détecté dynamiquement, sinon facteurs embarqués |
| Facteurs par pays (DE · ES · IT · AT · NL · BE · PT) | Moyen | Même méthode, mix électrique et prix locaux |
| Comparaison sectorielle de l'empreinte | Faible | Croisement naturel avec `qonto-sector-benchmark` |
| Suivi mensuel des leviers (l'empreinte baisse-t-elle vraiment ?) | Moyen | Réutilise la classification, relance sur les mêmes postes |
| Affinage par facture fournisseur ligne à ligne | Moyen | Quand les factures fournisseurs sont riches |

## 🛡 Garde-fous

- **Estimation d'ordre de grandeur, pas un bilan réglementaire** (BEGES / CSRD / GHG Protocol) — rappelé dans chaque rapport ; pour un bilan officiel : prestataire spécialisé
- Chaque facteur affiché avec sa **source et son millésime** ; chaque chiffre avec sa **fourchette** — jamais de fausse précision (« ~9 tCO2e (4,5–13,5) », pas « 9,37 »)
- **Jamais de compensation vendue** ni recommandée
- 100 % lecture seule ; IBAN masqués (4 derniers chiffres) ; pagination ≤ 50 partout
- Pays ≠ FR : méthode identique, facteurs annoncés comme à adapter — jamais de calibration locale prétendue
- Poste « non classé » > ~20 % des dépenses → le skill dit que l'estimation est fragile et propose de labelliser les principales contreparties

---

*Documentation FR (pilotage). Version jury : `README.en.md`. Livrable PR : `SKILL.md`. Procédure pas-à-pas : `docs/PROCEDURE.fr.md`. Docs riches : `docs/doc-qonto-carbon-ledger.fr.html` · `docs/doc-qonto-carbon-ledger.fr.docx`.*
