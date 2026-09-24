# 📊 qonto-sector-benchmark — « Suis-je normal ? » Enfin une réponse chiffrée

> **Skill #20 · NOUVEAU** · Hackathon Qonto × Anthropic MCP (10-13/07/2026)
> Le bulletin de santé comparé du dirigeant : tes ratios réels (Qonto) face aux statistiques sectorielles officielles (INSEE via MCP Datagouv) · **100 % lecture seule, zéro écriture**

---

## 🎯 Le pitch

« Suis-je normal ? » — la question que tout dirigeant se pose sans jamais avoir la réponse. Tu *sens* que tes charges sont lourdes ou que tes clients paient lentement, mais lourdes **par rapport à quoi** ? `qonto-sector-benchmark` répond en un prompt :

1. **Tes ratios réels** calculés depuis le compte Qonto — part des charges fixes, poids des abonnements logiciels, délai de paiement clients constaté, saisonnalité du CA, trésorerie en jours de charges
2. **La référence sectorielle officielle** — statistiques publiques françaises (INSEE Ésane, délais de paiement) récupérées en direct via le MCP Datagouv, au niveau NAF le plus fin disponible
3. **L'honnêteté statistique comme cœur du skill** — chaque comparaison porte sa **source + millésime + granularité** (« NAF 62.02A, INSEE Ésane, données 2023 ») ; pas de dataset exact → comparaison au niveau supérieur *en le disant* ; jamais de chiffre sectoriel inventé
4. **Toi vs toi il y a un an** — auto-benchmark temporel systématique, qui devient le mode dégradé complet si Datagouv est absent ou si l'entreprise n'est pas française

Résultat type : « tes clients te paient à 38 jours ; la médiane de ton secteur est 51 : tu encaisses **plus vite** que tes pairs » / « tes charges fixes pèsent 61 % vs ~45 % dans ton secteur : voilà où creuser ».

## 📋 Prérequis

| Prérequis | Détail | Obligatoire |
|---|---|---|
| Compte Qonto **production** | Exigence du hackathon ; le skill s'adapte à toute organisation (`get_organization` d'abord), zéro donnée en dur | ✅ |
| Pays | **Comparaison sectorielle : France uniquement** (statistiques INSEE). Autres pays Qonto (DE, ES, IT…) : dégradation propre — ratios internes + auto-benchmark temporel, jamais de mapping sur les données françaises | ℹ️ détecté |
| MCP Qonto connecté | Connecteur officiel (claude.ai / Claude Desktop), login OAuth | ✅ |
| MCP Datagouv | Détecté dynamiquement : présent → références sectorielles en direct ; absent → le skill le dit et bascule en auto-benchmark | ⭕ recommandé |
| Code NAF connu | Lu dans `get_organization` quand exposé ; sinon demandé (il est sur le KBIS) ou déduit de l'activité **et confirmé** avant usage | ⭕ |
| Historique ≥ 12 mois | La saisonnalité exige une année pleine ; l'auto-benchmark ~24 mois. En dessous : le skill calcule ce qui est calculable et taggue le reste indisponible | ⭕ |

## ⚙️ Fonctionnement global

![Fonctionnement global](assets/flow.fr.png)

1. **Identité & secteur** : `get_organization` d'abord — pays, forme juridique, code NAF. NAF absent → demandé ou déduit puis confirmé. Société non française → mode interne annoncé **avant** l'analyse, pas après
2. **Ratios internes** (24 mois, paginé ≤ 50) : charges fixes (récurrences ±10 %, ≥ 3 occurrences), abonnements logiciels (liste affichée, corrigeable), délai de paiement clients (médiane émission → paiement, sur les factures Qonto uniquement — annoncé), saisonnalité (coefficient de variation + mois pic/creux), trésorerie en jours de charges
3. **Références sectorielles** via MCP Datagouv : `search_datasets` (INSEE Ésane, délais de paiement) → `get_dataset_info` (millésime, producteur, granularité vérifiés **avant** usage) → `query_resource_data` filtré sur le NAF
4. **Comparaison honnête** : chaque ligne porte source + millésime + granularité ; classe NAF non publiée → niveau division *en le disant sur la ligne* ; aucun référentiel → valeur interne seule, marquée « pas de référence publique trouvée »
5. **Auto-benchmark** : les 5 mêmes ratios sur la fenêtre 12 mois précédente, flèches de tendance — c'est aussi le mode dégradé complet
6. **Bulletin de santé** : scorecard markdown (toujours) + scorecard HTML si l'hôte affiche les fichiers

## 🏗 Schéma fonctionnel

![Schéma fonctionnel](assets/functional.fr.png)

**Zéro écriture, par conception** : le skill ne fait que lire — le compte Qonto d'un côté, l'open data public de l'autre. Rien à approuver, rien qui puisse bouger. Le seul « risque » est statistique, et il est traité par la règle d'or : source + millésime + granularité sur chaque chiffre, ou pas de chiffre.

## 📐 Les 5 ratios du bulletin

| Ratio | Calcul (données Qonto) | Référence sectorielle |
|---|---|---|
| Part des charges fixes | Débits récurrents (tiers normalisé, montant stable ±10 %, ≥ 3 occurrences) ÷ total des débits, 12 mois | Structure des charges par NAF (INSEE Ésane) |
| Poids des abonnements logiciels | Récurrences dont le tiers matche des patterns SaaS ÷ total des débits — liste affichée, corrigeable | Ordre de grandeur par division NAF quand publié ; sinon valeur interne seule |
| Délai de paiement clients | Médiane émission de facture → paiement constaté (`list_client_invoices` + rapprochement transactions) | Délais de paiement moyens par secteur et taille, quand le dataset existe |
| Saisonnalité du CA | Coefficient de variation des encaissements mensuels sur 24 mois + mois pic/creux | Indices d'activité sectoriels quand disponibles ; sinon auto-benchmark |
| Trésorerie en jours de charges | Solde consolidé ÷ charge moyenne journalière (12 mois) | Surtout temporel (toi vs toi) — peu de référentiel public fiable, et le skill le dit |

## 📤 Formats de sortie (où atterrit le bulletin ?)

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Scorecard markdown : ratio · ta valeur · référence (source · millésime · granularité) · verdict · tendance N-1, puis 2-3 constats narratifs et la liste des sources | **Toujours** — c'est la base |
| **Scorecard interactive** | Fichier/artifact **HTML** : les 5 ratios en jauges face à la fourchette sectorielle, sources en notes de bas de page | Si l'hôte affiche les fichiers (artifacts claude.ai, Claude Desktop, Claude Code) ; sinon repli automatique sur le markdown |

## 🎬 Vidéo de démo

La démo ≤ 3 min jointe à la PR suit le storyboard : la question « am I normal? » → ratios réels calculés → références INSEE sourcées → **la révélation** (les abonnements n'étaient pas le problème ; les délais clients, si) → le bulletin final. Le script détaillé de tournage est conservé en interne (hors dépôt).

## 🧭 Positionnement dans la gamme

Le **bulletin de santé comparé**, rituel trimestriel ou annuel — pas un outil de pilotage quotidien. Pour le jour-le-jour (flux, prévisionnel, dashboard), renvoyer vers `qonto-ceo-cockpit`.

## 💡 Améliorations possibles (dans les clous du hackathon)

| Idée | Effort | Note |
|---|---|---|
| Référentiels par taille d'entreprise (croiser NAF × tranche d'effectif/CA) | Moyen | Ésane publie certaines ventilations par taille — comparaison encore plus juste |
| Modules pays (Destatis DE, INE ES, ISTAT IT…) | Élevé | Même architecture, un connecteur open-data par pays |
| Historique des bulletins : trajectoire sur 4-8 trimestres | Faible | Réutilise l'auto-benchmark, simple mémoire des runs |
| Benchmark « panier de pairs » anonymisé | Élevé | Hors MCP actuel — piste produit Qonto plus que skill |

## 🛡 Garde-fous

- **100 % lecture seule** : aucun outil d'écriture appelé — rien à approuver, rien qui puisse bouger
- **Jamais** de chiffre sectoriel inventé : pas de dataset → la ligne le dit ; granularité dégradée → annoncée sur la ligne ; millésime toujours affiché
- Ratios bancaires ≠ comptabilité : approximation honnête, rappelée dans chaque rapport — les chiffres de l'expert-comptable prévalent
- Secteur confirmé, pas supposé, quand le NAF n'est pas dans les données du compte
- IBAN masqués (4 derniers chiffres) · pagination ≤ 50 partout

---

*Documentation FR (pilotage). Version jury : `README.en.md`. Livrable PR : `SKILL.md`. Procédure pas-à-pas : `docs/PROCEDURE.fr.md`. Docs riches : `docs/doc-qonto-sector-benchmark.fr.html` · `docs/doc-qonto-sector-benchmark.fr.docx`.*
