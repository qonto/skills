# 📦 qonto-cash-to-stock — Le réassort sous contrainte de cash

> **Hackathon Qonto × Anthropic MCP (10-13/07/2026)** · Agent Skill pour le MCP Qonto
> Lecture massive, une seule écriture : la demande de virement fournisseur — l'argent ne bouge qu'après ton approbation SCA dans l'app Qonto

---

## 🎯 Le pitch

Le vrai plafond du réassort e-commerce, ce n'est pas la demande — c'est **la trésorerie**. Commander trop, c'est mettre le compte en danger le jour où la TVA tombe ; commander trop peu, c'est la rupture de stock qui coupe les ventes. `qonto-cash-to-stock` répond à LA question : **« combien d'unités puis-je commander sans me mettre en danger, et quand ? »**

1. **Tréso réellement libre** — soldes de tous les comptes − factures fournisseurs à venir − échéances fiscales détectées dans l'historique − coûts fixes récurrents − coussin de sécurité. Le minimum de la courbe, daté.
2. **Vélocité & date de rupture** — Shopify si connecté (ventes/jour et stock par produit) ; sinon estimation depuis les encaissements Qonto + catalogue `list_products`, annoncée comme telle
3. **Les 4 chiffres de la décision** — tréso libre · date de rupture · unités finançables · date limite de commande, chaque chiffre avec un tag de confiance 🟢 vu dans les données · 🟡 estimé · 🔵 dépend de ta réponse
4. **Action sécurisée** — demande de virement fournisseur préparée quand tu décides ; l'argent ne bouge **que** après ton approbation SCA dans l'app Qonto

## 📋 Prérequis

| Prérequis | Détail | Obligatoire |
|---|---|---|
| Compte Qonto **production** | Exigence du hackathon ; le skill s'adapte à toute organisation (`get_organization` d'abord, zéro valeur en dur) | ✅ |
| Pays | Détection des échéances fiscales **depuis l'historique** partout ; affinage calendrier : **France** (même logique que `qonto-tax-pilot`). Autres pays Qonto (DE, ES, IT…) : seuls les prélèvements réellement observés sont projetés — jamais d'échéance inventée | ℹ️ détecté |
| MCP Qonto connecté | Connecteur officiel (claude.ai / Claude Desktop), login OAuth | ✅ |
| MCP Shopify | **Optionnel, détecté dynamiquement** : ventes/jour et stock par produit. Sans lui, mode dégradé propre : vélocité estimée depuis les encaissements + catalogue | ⭕ recommandé |
| Historique ≥ 3-6 mois | En dessous, dégradation honnête (tags 🟡, avertissement) ; 24-36 mois pour voir les cadences fiscales annuelles | ⭕ |
| Activité e-commerce avec fournisseurs | Sinon le skill reste un excellent calculateur de tréso réellement libre | ⭕ |

## ⚙️ Fonctionnement global

![Fonctionnement global](assets/flow.fr.png)

1. **Photo de trésorerie** : `get_organization` d'abord — tous les comptes, soldes, devise, pays
2. **Engagements à venir** : factures fournisseurs dues (`list_supplier_invoices`), échéances fiscales détectées (prélèvements sortants d'abord, DGFIP fusionnée sous toutes ses graphies — la logique de `qonto-tax-pilot` ; s'il est installé, son échéancier est réutilisé), coûts fixes récurrents (loyer, salaires, abonnements) → calendrier daté des sorties sur 90 jours
3. **Tréso réellement libre** : courbe jour par jour = soldes + encaissements prudents − engagements − coussin de sécurité (1 mois de coûts fixes par défaut, ajustable). Le minimum de la courbe, c'est ce que le réassort peut consommer
4. **Vélocité & rupture** : Shopify si connecté (`run-analytics-query` + `get-inventory-levels`) → date de rupture par produit ; sinon estimation encaissements + catalogue, taggée 🟡
5. **La réponse** : N unités finançables (tréso libre ÷ coût unitaire débarqué — demandé s'il est inconnu, jamais deviné) et date limite de commande (rupture − délai fournisseur)
6. **Demande + SCA** : avec ton consentement explicite, `create_multi_transfer_request` avec le calcul complet dans la note → notification push → **ton** approbation 2FA dans l'app → rapport final

## 🏗 Schéma fonctionnel

![Schéma fonctionnel](assets/functional.fr.png)

**Le point clé de sécurité** : le trait plein (lecture) ne présente aucun risque ; le trait pointillé (écriture) exige le consentement explicite donné dans la conversation et ne produit qu'une *demande* — c'est la SCA (2FA) du titulaire du compte, dans l'app Qonto, qui déplace l'argent. Ni Claude ni le MCP ne le peuvent. **C'est le modèle de sécurité, pas une limitation.**

## 🔢 Les 4 chiffres de la décision

| Chiffre | Comment il est obtenu | Tag |
|---|---|---|
| **Tréso libre après échéances** | Minimum de la courbe 90 j : soldes − fournisseurs − impôts détectés − coûts fixes − coussin | 🟢/🟡 |
| **Date de rupture** | Stock ÷ vélocité (Shopify), ou estimation encaissements + catalogue | 🟢 avec Shopify · 🟡 sans |
| **Unités finançables** | Tréso libre à la date de paiement ÷ coût unitaire débarqué | 🔵 dépend du coût confirmé |
| **Date limite de commande** | Date de rupture − délai fournisseur (demandé une fois) | 🔵 |

> **Exemple (chiffres fictifs, à titre d'illustration)** : « Tréso libre après échéances : 8 400 €. Rupture prévue le 28/09. Coût unitaire 6,50 € → **1 290 unités finançables** ; ton fournisseur livre en 3 semaines → **commande avant le 07/09**. » Et si tu dis oui : la demande de virement est créée, à approuver dans Qonto.

## 📤 Formats de sortie

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown (engagements, courbe résumée, 4 chiffres, récap demande) | **Toujours** — c'est la base |
| **Dashboard interactif** | Fichier/artifact **HTML** : courbe de tréso libre, échéances en marqueurs, compte à rebours rupture, jauge d'unités | Si l'hôte affiche les fichiers (artifacts claude.ai, Claude Desktop, Claude Code) ; sinon repli automatique sur les tableaux |
| **Note de la demande Qonto** | Texte joint à la demande de virement, visible à l'approbation SCA : tout le calcul | À chaque demande créée |

## 🎬 Vidéo de démo

La démo ≤ 3 min jointe à la PR suit le storyboard : le dilemme du réassort → engagements & tréso libre → rupture datée & unités finançables → **demande de virement approuvée en SCA, filmée sur téléphone** → dashboard final. Le script détaillé de tournage est conservé en interne (hors dépôt).

## 🔗 Skills complémentaires

- **`qonto-tax-pilot`** — les échéances fiscales viennent de la même logique de détection ; installés ensemble, cash-to-stock réutilise son échéancier au lieu de recalculer
- **`qonto-shopify-bridge`** — réconcilie le *passé* (virements Shopify vs Qonto) ; cash-to-stock décide le *futur* (la prochaine commande)

## 💡 Améliorations possibles (dans les clous du hackathon)

| Idée | Effort | Note |
|---|---|---|
| Multi-fournisseurs : arbitrage d'un budget entre plusieurs commandes | Moyen | Réutilise la courbe de tréso libre |
| Saisonnalité fine (vélocité pondérée par mois, soldes, fêtes) | Moyen | Shopify `run-analytics-query` sur 12 mois |
| Rappel « date limite de commande » dans le calendrier (MCP calendrier détecté dynamiquement) | Faible | Multi-MCP optionnel, dans l'esprit du kickoff |
| Scénarios de paiement fournisseur (acompte 30 % + solde à livraison) | Faible | Deux demandes datées au lieu d'une |

## 🛡 Garde-fous

- **Jamais** de demande de virement sans confirmation explicite dans la conversation en cours ; jamais présentée comme exécutée — elle attend ton approbation SCA
- Estimations ≠ conseil d'achat : la décision de stock reste humaine ; chaque hypothèse est affichée (coût unitaire, délai, coussin)
- Dégradation honnête : sans Shopify, sans catalogue, sans factures fournisseurs ou avec < 3 mois d'historique, le skill dit ce qu'il peut et ne peut pas calculer — il n'invente rien
- Tous les exemples de cette documentation sont **fictifs et annoncés comme tels**
- IBAN masqués (4 derniers chiffres) · pagination ≤ 50 partout · répétitions : `decline_request` après chaque test

---

*Documentation FR (pilotage). Version jury : `README.en.md`. Livrable PR : `SKILL.md`. Procédure pas-à-pas : `docs/PROCEDURE.fr.md`. Docs riches : `docs/doc-qonto-cash-to-stock.fr.html` · `docs/doc-qonto-cash-to-stock.fr.docx`.*
