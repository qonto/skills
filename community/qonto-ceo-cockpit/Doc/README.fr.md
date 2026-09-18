# 🛩 qonto-ceo-cockpit — « My Société », le cockpit du dirigeant généré à la volée

> **Skill #16** · Hackathon Qonto × Anthropic MCP (10-13/07/2026)
> « My Société » — le cockpit du dirigeant, généré à la volée · **100 % lecture seule, zéro écriture**

---

## 🎯 Le pitch

Ta banque te montre une liste de lignes. Pour *voir* ta boîte — d'où vient l'argent, où il va, où tu seras dans 3 mois — il faut un tableur… ou 3 semaines d'expert-comptable. `qonto-ceo-cockpit` fait ça en un prompt : « **montre-moi ma boîte** » → un dashboard HTML interactif, autoportant, généré depuis les données réelles du compte :

1. **Vue des flux** (type Sankey) — sources de revenus → société → postes de dépenses, rubans proportionnels aux montants, bascule mois/année, tooltips au survol
2. **Cartes mois / année / prévisionnel** par poste + KPI : solde consolidé, résultat du mois, jauge du coffre fiscal (si sous-compte détecté), prévisionnel 3 mois
3. **Prévisionnel 3 mois** — récurrences détectées + factures clients dues (retard habituel intégré) + factures fournisseurs, chaque montant tagué 🟢 réel / 🟡 estimé
4. **Panneau d'hypothèses TJM × jours facturables** — TJM détecté sur les factures, sliders, **recalcul live sans rappeler le MCP** (tout est embarqué dans la page)
5. **Masquage de postes** (œil 👁) — pour présenter le dashboard sans tout montrer, typiquement en rendez-vous banquier

## 📋 Prérequis

| Prérequis | Détail | Obligatoire |
|---|---|---|
| Compte Qonto **production** | Le skill s'adapte à toute organisation (`get_organization` d'abord), zéro donnée en dur | ✅ |
| Pays | **Cœur universel** : flux, cartes, récurrences et prévisionnel marchent dans tous les pays Qonto. Seuls les libellés fiscaux (TVA, IS, URSSAF) sont affinés pour la France ; ailleurs, libellé neutre « Taxes », jamais de règle locale inventée | ℹ️ détecté |
| MCP Qonto connecté | Connecteur officiel (claude.ai / Claude Desktop), login OAuth | ✅ |
| Labels Qonto | Clé de regroupement des postes de dépenses (les catégories cash-flow sont hors périmètre du connecteur — 403) ; sans labels : regroupement par contrepartie | ⭕ recommandé |
| Historique ≥ 6 mois | En dessous : prévisionnel dégradé honnêtement (tags 🟡 + avertissement) | ⭕ |
| Facturation à la journée | Nécessaire au panneau TJM ; sinon le panneau est omis et le skill le dit | ⭕ |

## ⚙️ Fonctionnement global

![Fonctionnement global](assets/flow.fr.png)

1. **Découverte** : `get_organization` (comptes, soldes, pays), détection du sous-compte impôts (jauge du coffre), `list_labels`
2. **Lecture des flux 12 mois** : `list_transactions` paginé ≤ 50 par fenêtres de 3 mois — entrées par source (contrepartie normalisée), sorties par label sinon par contrepartie, virements internes neutralisés, bucket « à catégoriser » explicite (jamais dilué en douce)
3. **Factures & récurrences** : factures clients impayées (retard habituel du client intégré) + factures fournisseurs à venir + détection de récurrences (contrepartie stable, montant ±10 %, cadence M/T/A, ≥3 occurrences) — et **détection du TJM** sur les lignes de factures à l'unité « jour » (médiane)
4. **Prévisionnel 3 mois** mois par mois : récurrences aux dates typiques + flux facturés + base irrégulière (médiane des mois passés), double couche 🟢/🟡 jamais mélangée sans le dire
5. **Hypothèses embarquées** : TJM + jours facturables pré-remplis, données et formules en JSON dans la page → recalcul JS instantané, zéro appel MCP
6. **Cockpit généré** : un seul fichier HTML autoportant (artifact claude.ai / fichier local) — repli automatique en tableaux markdown si l'hôte n'affiche pas les fichiers

## 🏗 Schéma fonctionnel

![Schéma fonctionnel](assets/functional.fr.png)

**Le point clé** : ce skill est **100 % lecture**. Aucun trait pointillé sur le schéma — pas d'écriture, pas de virement, rien à approuver. Le seul livrable est un fichier local que tu peux ouvrir, rafraîchir, ou partager. Et le masquage 👁 est une feature de **présentation** : les données restent dans la page, sur ta machine — rien ne part nulle part. Pour un export réellement expurgé (banquier, associé), le skill régénère le fichier **sans** les postes masqués dans les données.

## 🧭 Les zones du cockpit

| Zone | Contenu | Source | Interactif |
|---|---|---|---|
| Vue des flux | Sources → société → postes, rubans ∝ montants | Transactions 12 mois, labels | Bascule mois/année, survol, clic → carte détail |
| KPI | Solde consolidé · résultat du mois · coffre fiscal · prévisionnel 3 mois | Soldes + flux + sous-compte impôts | Recalculés selon postes masqués |
| Cartes par poste | Mois / année / prévisionnel, badges de cadence, tags 🟢🟡 | Flux + récurrences + factures | Œil 👁 de masquage par carte |
| Panneau hypothèses | TJM × jours facturables (3 mois + reste de l'année) | TJM détecté sur factures | **Sliders, recalcul live sans MCP** |

## 📤 Formats de sortie

| Sortie | Format | Quand |
|---|---|---|
| **Dashboard interactif** | Un seul fichier **HTML autoportant** : CSS/JS inline, zéro dépendance externe (CSP-safe), barres et rubans en CSS/SVG pur, thème clair/sombre, charte violet/noir/blanc | **Le livrable** — dès que l'hôte affiche les fichiers (artifacts claude.ai, Claude Desktop, Claude Code) |
| **Réponse dans la conversation** | Tableaux markdown structurés : KPI, flux mois + année, prévisionnel 3 mois, scénarios TJM chiffrés | Repli automatique si l'hôte n'affiche pas les fichiers |
| **Export « présentation »** | Le même HTML régénéré **sans** les postes sensibles dans les données | À la demande, pour partager |

## 🎬 Vidéo de démo

La démo ≤ 3 min jointe à la PR suit le storyboard : le problème (une banque = une liste de lignes) → « show me my company » → le dashboard qui se construit → **le slider TJM qu'on bouge : +50 € et la projection annuelle bouge en live** → l'œil qui masque un poste pour le banquier → wrap-up gamme. Le script détaillé de tournage est conservé en interne (hors dépôt).

## 💡 Améliorations possibles (dans les clous du hackathon)

| Idée | Effort | Note |
|---|---|---|
| Slot d'intégration gamme : tax-pilot → jauge coffre + échéances, subscription-guardian → carte abonnements | Faible | Déjà prévu dans le SKILL.md (détection dans la conversation, jamais requis) |
| Comparaison N vs N-1 par poste (flèches de tendance) | Faible | L'historique 12 mois est déjà lu |
| Multi-devises (comptes non-EUR consolidés au taux du jour) | Moyen | `get_organization` expose les devises |
| Mode « conseil d'administration » : PDF prêt à imprimer depuis le HTML | Faible | `window.print()` + CSS print, toujours zéro dépendance |
| Sliders supplémentaires : embauche, salaire dirigeant, gros achat | Moyen | Le moteur de recalcul JS est déjà en place (idée v3 de P12) |

## 🛡 Garde-fous

- **Skill 100 % lecture** : aucun outil d'écriture, aucun virement, rien à approuver — et il le dit clairement si on lui demande
- Le masquage 👁 = présentation, pas sécurité : jamais présenté comme un document expurgé ; pour partager, régénération avec exclusion réelle des données
- Prévisionnel et hypothèses = estimations 🟡, pas de la comptabilité — validation expert-comptable recommandée
- IBAN masqués (4 derniers chiffres) · pagination ≤ 50 partout · jamais de catégorie, de règle fiscale ou de chiffre inventés

---

*Documentation FR (pilotage). Version jury : `README.en.md`. Livrable PR : `SKILL.md`. Procédure pas-à-pas : `docs/PROCEDURE.fr.md`. Docs riches : `docs/doc-qonto-ceo-cockpit.fr.html` · `docs/doc-qonto-ceo-cockpit.fr.docx`.*
