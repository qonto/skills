# 🛡 qonto-brand-shield — La marque que tu finances est-elle protégée ?

> **Hackathon Qonto × Anthropic MCP (10-13/07/2026)** · Agent Skill pour le MCP Qonto
> **100 % lecture** : le skill mesure et prépare — le dépôt de marque lui-même se fait sur inpi.fr, par toi.

---

## 🎯 Le pitch

Chaque mois, le compte paie des dépenses qui **construisent une marque** : un logo, des noms de domaine, de la publicité, du packaging. Et pendant ce temps, personne ne vérifie si le nom lui-même est protégé. `qonto-brand-shield` fait les deux :

1. **Cumul d'investissement par marque** — designers/logo, domaines, publicité, packaging, impression, détectés dans les dépenses réelles et rattachés à chaque marque : « tu as investi X € sur [Marque] en N mois », chaque rattachement tagué 🟢 prouvé (justificatif, domaine) · 🟡 supposé
2. **Croisement propriété intellectuelle** — la marque est-elle déposée à l'INPI ? Par toi ? Des marques proches existent-elles dans tes classes de Nice ? Le renouvellement des 10 ans approche-t-il ?
3. **Exposition financière** — l'investissement « à découvert » : tout ce qui est déjà dépensé sur un nom que rien ne protège
4. **Dossier de pré-dépôt** — nom, classes de Nice suggérées **depuis l'activité réelle** (produits/services détectés), coût indicatif, prêt pour inpi.fr

**Exemple (chiffres et marque inventés)** : « Tu as dépensé 4 320 € en 8 mois pour la marque *Nordlys* (logo 900 €, domaines 120 €, ads 3 300 €). Elle n'est pas déposée. Une marque proche existe en classe 42 depuis 2021. Dépôt en 2 classes : ~230 €, soit ~5 % de ce que tu as déjà investi à découvert. »

## 📋 Prérequis

| Prérequis | Détail | Obligatoire |
|---|---|---|
| Compte Qonto **production** | Le skill s'adapte à toute organisation (`get_organization` d'abord, zéro valeur en dur) | ✅ |
| Pays | **Registre : INPI = France.** Autres pays Qonto (DE, ES, IT…) : l'exposition financière reste valable partout ; côté registre, piste **EUIPO** — jamais de donnée de registre inventée | ℹ️ détecté |
| MCP Qonto connecté | Connecteur officiel (claude.ai / Claude Desktop), login OAuth | ✅ |
| Accès INPI | L'API data.inpi.fr demande un **compte INPI + une demande d'accès**. Sans lui : mode dégradé assumé — lien de recherche pré-rempli + vérification manuelle guidée en 2 min. **Pas de scraping** | ⭕ optionnel |
| Historique ≥ 12 mois | 24-36 mois recommandés : les cadences annuelles (renouvellements de domaines) ne se voient que sur des années pleines | ⭕ |

## ⚙️ Fonctionnement global

![Fonctionnement global](assets/flow.fr.png)

1. **Inventaire des marques** : `get_organization` (raison sociale, noms commerciaux) + `list_products` (libellés produits/services) + noms de domaine repérés dans les transactions — une société peut porter plusieurs marques, chacune suivie séparément
2. **Scan des dépenses de marque** (12-36 mois, paginé ≤ 50, débits) : design & identité, domaines, publicité, packaging & impression — tiers normalisés (casse, accents, graphies multiples fusionnées)
3. **Rattachement à une marque** : `get_attachment` sur les factures design/domaines/impression pour extraire le nom de marque quand il y figure ; les domaines se rattachent naturellement ; le reste va à la marque principale, tagué 🟡
4. **Vérification INPI** : avec accès API → recherche du nom exact + variantes proches (déposée ? par qui ? classes ? renouvellement ?) ; sans accès → lien data.inpi.fr pré-rempli + checklist 2 min, et le skill n'intègre que ce que tu lui rapportes
5. **Classes de Nice suggérées** depuis l'activité réelle : 1-3 classes proposées (ex. SaaS → 42, vêtements → 25, vente/pub → 35), toujours **à valider**
6. **Rapport** : exposition par marque, alertes marques proches & renouvellement, dossier de pré-dépôt prêt pour inpi.fr

## 🏗 Schéma fonctionnel

![Schéma fonctionnel](assets/functional.fr.png)

**Le point clé** : ce skill est **100 % lecture** — aucune écriture MCP, aucun virement, rien à approuver. Le seul « acte » possible, le dépôt de marque, se fait sur inpi.fr, par toi, après validation humaine (conseil en PI recommandé). Le skill ne présente jamais un fait de registre sans source : résultat d'API ou ta propre vérification manuelle.

## 💼 Postes de dépense détectés

| Poste | Signaux | Exemples de tiers |
|---|---|---|
| Design & identité | Libellés logo / branding / identité / charte graphique / naming | Plateformes freelance, agences, designers indépendants |
| Noms de domaine | Registrars, **cadence annuelle** (cross-réf. `qonto-subscription-audit`) | OVH, Gandi, Namecheap, GoDaddy, IONOS… |
| Publicité | Régies publicitaires | Google Ads, Meta, TikTok, LinkedIn… |
| Packaging & impression | Libellés impression / packaging / étiquettes | Imprimeurs en ligne, fournisseurs packaging |

*Les tiers cités sont des plateformes publiques génériques ; tous les montants d'exemple de cette doc sont inventés.*

## 🏷 Classes de Nice — exemples de suggestion (à valider)

| Activité détectée dans le compte | Classes suggérées |
|---|---|
| SaaS / services logiciels | 42 (+9 si logiciel téléchargeable) |
| Vêtements / print-on-demand | 25 |
| Vente au détail, services publicitaires | 35 |
| Formation / contenus | 41 |

**Coûts INPI indicatifs** : dépôt **190 € la 1re classe + 40 €/classe supplémentaire** (~190-270 € pour 1-3 classes) · renouvellement **tous les 10 ans** (~290 € + 40 €/classe) · à vérifier sur inpi.fr.

## 📤 Formats de sortie

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown (investissement par marque, statut de protection, exposition, alertes) | **Toujours** — c'est la base |
| **One-pager interactif** | Fichier/artifact **HTML** : jauge d'exposition par marque, postes de dépense, statut INPI, dossier | Si l'hôte affiche les fichiers (artifacts claude.ai, Claude Desktop, Claude Code) ; sinon repli sur les tableaux |
| **Dossier de pré-dépôt** | Texte structuré : nom, classes suggérées, coût indicatif, lien inpi.fr | À chaque marque non protégée détectée |

## 🎬 Vidéo de démo

La démo ≤ 3 min jointe à la PR suit le storyboard : problème → cumul d'investissement par marque → vérification INPI (mode manuel guidé montré honnêtement) → **exposition chiffrée + dossier de pré-dépôt**. Le script détaillé de tournage est conservé en interne (hors dépôt).

## 💡 Améliorations possibles (dans les clous du hackathon)

| Idée | Effort | Note |
|---|---|---|
| MCP INPI dédié (API data.inpi.fr intégrée) | Moyen | Supprime l'étape manuelle ; détection dynamique, le cœur marche sans |
| Extension EUIPO / OMPI (marque UE & internationale) | Moyen | Qonto est paneuropéen ; même logique, autres registres |
| Veille des nouveaux dépôts proches | Moyen | Le délai d'opposition INPI est court (2 mois après publication) — alerte utile |
| Croisement automatique `qonto-subscription-audit` | Faible | Les domaines sont déjà des abonnements annuels détectés |
| Échéance de renouvellement poussée dans `qonto-tax-pilot` | Faible | Le renouvellement rejoint l'échéancier des sorties datées |

## 🛡 Garde-fous

- **100 % lecture** : aucun outil d'écriture, jamais — le dépôt reste une décision humaine sur inpi.fr
- La similarité de marques est une **alerte indicative, pas une analyse juridique** : conseil en PI recommandé avant tout dépôt
- Classes de Nice **suggérées, à valider** ; coûts indicatifs — la source de vérité est inpi.fr
- Jamais de fait de registre sans source (API ou ta vérification) ; **pas de scraping** de data.inpi.fr
- Dégradation honnête : historique court, compte vide, société non française (exposition seule + piste EUIPO)
- IBAN masqués (4 derniers chiffres) · pagination ≤ 50 partout

---

*Documentation FR (pilotage). Version jury : `README.en.md`. Livrable PR : `SKILL.md`. Procédure pas-à-pas : `docs/PROCEDURE.fr.md`. Docs riches : `docs/doc-qonto-brand-shield.fr.html`.*
