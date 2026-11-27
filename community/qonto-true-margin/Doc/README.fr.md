# ⚖️ qonto-true-margin — Le pricing par les coûts bancaires réels

> Hackathon Qonto × Anthropic MCP (10-13/07/2026)
> La marge « théorique » du dashboard e-commerce est une fiction ; **le compte bancaire connaît la vraie**. Zéro écriture côté Qonto — l'unique écriture est côté Shopify (prix), ligne à ligne, sur validation explicite.

---

## 🎯 Le pitch

Le dashboard e-commerce affiche une « marge » construite sur des coûts théoriques. Ce qui sort **vraiment** du compte — frais PSP réellement débités, frais de change EUR/USD, transport facturé, achats fournisseurs — raconte une autre histoire. `qonto-true-margin` reconstruit la vérité et la transforme en décision de prix :

1. **Coûts réels classés depuis les débits Qonto** — frais PSP constatés (ou « inconnus, pas nuls » quand ils sont nettés dans les payouts), change, transporteurs, COGS fournisseurs (`list_supplier_invoices`) — chaque famille taguée 🟢 observé · 🟡 dérivé · ⚪ inconnu
2. **Marge de contribution réelle par produit** — ventes Shopify par produit − coûts réels alloués **au prorata (heuristique annoncée** : CA ou unités, au choix, méthode affichée sur chaque tableau)
3. **Produits vendus à perte identifiés** — triés en premier, écart vs la marge « théorique » du dashboard affiché noir sur blanc
4. **Nouveaux prix proposés puis appliqués** — prix de couverture + prix cible ; application dans Shopify (`update-product`) **uniquement après validation explicite ligne à ligne** — jamais en lot

## 📋 Prérequis

| Prérequis | Détail | Obligatoire |
|---|---|---|
| Compte Qonto **production** | Le skill s'adapte à toute organisation (`get_organization` d'abord, zéro valeur en dur) | ✅ |
| Pays | **Universel** — l'analyse marche à l'identique pour tous les pays Qonto (FR, DE, ES, IT, AT, NL, BE, PT). La vérité, c'est le débit du compte ; multi-devises rapporté par devise, jamais converti en silence | ℹ️ détecté |
| MCP Qonto connecté | Connecteur officiel (claude.ai / Claude Desktop), login OAuth | ✅ |
| MCP Shopify connecté | Ventes par produit + application des prix. Sans lui : **mode dégradé annoncé** — marge globale par famille de coûts, sans granularité produit | ⭕ recommandé |
| MCP Stripe connecté | Détail des fees par paiement | ⭕ optionnel |
| Historique ≥ 3 mois | En dessous : tags de confiance dégradés + avertissement honnête | ⭕ |

## ⚙️ Fonctionnement global

![Fonctionnement global](assets/flow.fr.png)

1. **Coûts réels du compte** : 12-24 mois de débits Qonto (paginé ≤ 50), classés par famille — frais PSP (⚠️ Shopify Payments nette ses fees **dans** le payout : pas de débit séparé → taux effectif dérivé du brut vs net quand Shopify est connecté, sinon « inconnu, pas nul »), change (devise locale ≠ devise du compte), transport (Colissimo, Chronopost, Mondial Relay, DHL, UPS… ; paiements carte rapprochés par `emitted_at`), COGS fournisseurs (`list_supplier_invoices` + prélèvements récurrents). Le reste = coûts fixes, exclus de la marge de contribution, listés à part
2. **Ventes par produit** (si MCP Shopify) : CA, unités, remboursements par produit sur la même fenêtre, prix actuels
3. **Allocation heuristique** : prorata CA (défaut) ou prorata unités (mieux quand le transport pèse) — méthode choisie par l'utilisateur et **affichée sur chaque tableau**. Les factures fournisseurs nommant un produit sont rattachées en direct, l'allocation ne couvre que le reste
4. **Marge réelle par produit** : CA net − COGS − PSP − change − transport, en € et en % — produits à perte en tête de tableau
5. **Nouveaux prix** : prix de couverture + prix cible pour la marge visée (demandée, jamais supposée). Une suggestion chiffrée, **pas une stratégie de pricing** — l'élasticité n'est pas modélisée, et le skill le dit à chaque proposition
6. **Application validée** : tableau ligne à ligne (produit · prix actuel · prix proposé · marge avant/après) → l'utilisateur confirme **chaque ligne** → `update-product` par produit confirmé → relecture Shopify pour confirmer avant de dire « fait »

## 🏗 Schéma fonctionnel

![Schéma fonctionnel](assets/functional.fr.png)

**Le point clé de sécurité** : côté Qonto, le skill est **100 % lecture** — aucun outil d'écriture bancaire, rien ne peut bouger sur le compte. L'unique écriture est côté **Shopify** (mise à jour de prix), et elle exige la validation explicite de chaque produit dans la conversation. Un « applique tout » global est refusé et re-demandé ligne à ligne.

## 🆚 Différenciation vs `qonto-shopify-bridge`

| | `qonto-shopify-bridge` | `qonto-true-margin` |
|---|---|---|
| Nature | **Constat comptable du passé** | **Décision de prix pour l'avenir** |
| Question | « Shopify m'a-t-il vraiment payé ? » | « Ce produit me rapporte-t-il vraiment ? » |
| Cœur | Rapproche payouts ↔ banque, constate les fees effectifs | **Consomme** ces coûts constatés → marge réelle par produit → nouveaux prix |
| Écriture | Aucune (100 % lecture) | Aucune côté Qonto ; prix Shopify sur validation ligne à ligne |

**Input partagé, output opposé** : lance le bridge quand un payout cloche ; lance true-margin quand un prix doit changer. Voir aussi `qonto-shopify-bridge` pour la réconciliation.

## 📊 Exemple de restitution (données inventées)

| Produit | Prix | Marge dashboard | Marge réelle | Verdict |
|---|---|---|---|---|
| Mug émaillé | 24,90 € | 38 % | **−4 %** | 🔴 vendu à perte (transport réel) |
| Tote bag | 19,90 € | 45 % | 22 % | 🟠 fees + change sous-estimés |
| Poster A2 | 34,90 € | 42 % | **11 %** | 🟠 prix recommandé : 39,90 € |

*Tous les chiffres de ce tableau sont inventés pour l'exemple — le skill n'affiche que ceux calculés sur le compte de l'utilisateur, avec la méthode d'allocation en légende.*

## 📤 Formats de sortie

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown (familles de coûts, marges par produit, propositions de prix, avant/après) | **Toujours** — c'est la base |
| **Dashboard interactif** | Fichier/artifact **HTML** : cascade marge dashboard → marge réelle, liste des produits à perte, simulateur de prix | Si l'hôte affiche les fichiers (artifacts claude.ai, Claude Desktop, Claude Code) ; sinon repli automatique sur les tableaux |
| **Confirmation Shopify** | Relecture `get-product` après chaque `update-product` — le prix affiché est le prix relu, pas le prix demandé | À chaque application validée |

## 🎬 Vidéo de démo

La démo ≤ 3 min jointe à la PR suit le storyboard : la marge dashboard qui ment → les coûts réels lus dans les débits → **la révélation** (le produit star vendu à perte) → le nouveau prix validé ligne à ligne et appliqué dans Shopify → le dashboard final. Le script détaillé (textes à dire, checklist tournage, sous-titres EN) est dans **`_SCRIPT-VIDEO.md`** — fichier interne, **exclu de la PR**.

## 💡 Améliorations possibles (dans les clous du hackathon)

| Idée | Effort | Note |
|---|---|---|
| Allocation transport au poids/commande (données Shopify) | Moyen | Remplace le prorata pour la famille transport |
| Détail des fees par charge via le MCP Stripe | Faible | Déjà prévu en optionnel — précision du 🟡 vers le 🟢 |
| Suivi mensuel de la dérive de marge réelle | Faible | Réutilise la classification ; alerte quand un produit passe sous le seuil |
| Scénarios de prix comparés (2-3 hypothèses de marge cible) | Faible | Dans le simulateur HTML |

## 🛡 Garde-fous

- **Jamais** de prix appliqué sans validation explicite du produit concerné dans la conversation en cours ; jamais annoncé « fait » sans relecture Shopify
- L'allocation est une **estimation assumée** — méthode (prorata CA ou unités) affichée sur chaque tableau ; marge réelle = estimation, pas de la comptabilité
- Suggestion ≠ stratégie de pricing : élasticité non modélisée — dit honnêtement à chaque proposition
- **Zéro outil d'écriture Qonto** ; fees PSP invisibles (nettés) → « inconnu, pas nul », jamais un taux annoncé présenté comme constaté
- Dégradation honnête sans Shopify (marge par famille seulement) ; IBAN masqués ; pagination ≤ 50 ; multi-devises par devise

---

*Documentation FR (pilotage). Version jury : `README.en.md`. Livrable PR : `SKILL.md`. Procédure pas-à-pas : `docs/PROCEDURE.fr.md`. Docs riches : `docs/doc-qonto-true-margin.fr.html` · `docs/doc-qonto-true-margin.fr.docx`.*
