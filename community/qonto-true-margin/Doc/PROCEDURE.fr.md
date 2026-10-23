# 📖 Procédure d'installation et d'utilisation — qonto-true-margin

> Guide pas-à-pas utilisateur. Version jury : `PROCEDURE.en.md`.

---

## 1️⃣ Installation (une seule fois, ~5 min)

### Étape 1 — Connecter le MCP Qonto à Claude
1. Dans **claude.ai** (ou Claude Desktop) : Paramètres → **Connecteurs** → *Parcourir les connecteurs*
2. Chercher **Qonto** → *Ajouter* → le flux de connexion Qonto s'ouvre
3. Se connecter avec son compte Qonto (OAuth — le mot de passe n'est **jamais** partagé avec Claude)
4. Vérifier : demander à Claude « *Liste mes comptes Qonto* » → les comptes s'affichent

### Étape 2 — Connecter le MCP Shopify (recommandé)
1. Même chemin : Connecteurs → chercher **Shopify** → *Ajouter* → login OAuth de la boutique
2. Vérifier : « *Liste mes produits Shopify* » → les produits s'affichent
3. Optionnel : ajouter le connecteur **Stripe** pour le détail des fees par paiement

> ⭕ Sans Shopify, le skill fonctionne en **mode dégradé annoncé** : marge réelle par famille de coûts (PSP, change, transport, COGS), sans granularité produit — et il le dit clairement.

### Étape 3 — Installer le skill
- **Claude Code / Claude Desktop** : copier le dossier du skill dans `~/.claude/skills/qonto-true-margin/` (le fichier `SKILL.md` suffit)
- **claude.ai** : joindre le `SKILL.md` au projet, ou coller son contenu dans les instructions du projet

## 2️⃣ Usage type (l'audit de marge mensuel, ~5 min)

| # | Action | Résultat |
|---|---|---|
| 1 | Dire à Claude : « **Quelle est ma vraie marge par produit ?** » | Débits classés (PSP 🟢🟡⚪, change, transport, COGS) + ventes Shopify par produit |
| 2 | Choisir la clé d'allocation (prorata CA ou unités) | Méthode affichée sur chaque tableau — c'est une estimation assumée |
| 3 | Lire le tableau marge dashboard vs marge réelle | Produits à perte en tête, écart chiffré par produit |
| 4 | Demander : « **Propose les nouveaux prix** » | Prix de couverture + prix cible par produit signalé, hypothèses affichées |
| 5 | Valider **ligne à ligne** (« oui pour le produit X ») | `update-product` pour ce produit seul → prix relu dans Shopify → avant/après confirmé |

## 3️⃣ Prompts à copier-coller

- « **Quelle est ma vraie marge par produit, d'après ce qui sort réellement de mon compte Qonto ?** »
- « **Quels produits est-ce que je vends à perte ?** »
- « **Mon dashboard affiche 40 % de marge sur ce produit — c'est vrai ?** »
- « **Répartis mes coûts au prorata des unités plutôt que du CA** »
- « **Propose un prix pour viser 25 % de marge de contribution sur ce produit** »
- « **Applique le nouveau prix du [produit]** » *(la validation reste demandée produit par produit)*

## 4️⃣ Formats de sortie

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown (familles de coûts, marges, propositions, avant/après) | **Toujours** — c'est la base |
| **Dashboard interactif** | Fichier/artifact **HTML** : cascade marge dashboard → réelle, produits à perte, simulateur de prix | Si l'hôte affiche les fichiers (artifacts claude.ai, Claude Desktop, Claude Code) ; sinon repli automatique |
| **Confirmation Shopify** | Relecture `get-product` après chaque `update-product` | À chaque application validée |

## 5️⃣ Dépannage (erreurs connues et vérifiées)

| Symptôme | Cause | Solution |
|---|---|---|
| `list_transactions` échoue d'emblée | `bank_account_id`/`iban` manquant | Le skill appelle toujours `get_organization` en premier |
| Frais PSP introuvables dans les débits | Shopify Payments nette ses fees **dans** le payout — pas de débit séparé | Taux effectif dérivé du brut vs net (MCP Shopify requis) ; sinon affiché « inconnu, pas nul ». Voir aussi `qonto-shopify-bridge` pour le rapprochement payouts↔banque |
| `403 missing oauth scope` sur `list_cash_flow_categories` | Hors périmètre du connecteur claude.ai | Normal — le skill classe par tiers normalisé et labels à la place |
| Réponses énormes / tronquées | Pagination trop large | `per_page` ≤ 50 partout, fenêtres de 3 mois |
| Transport payé par carte introuvable à la date attendue | Décalage `emitted_at` vs `settled_at` (1-2 j) | Le skill rapproche par `emitted_at` |
| L'outil Shopify « update_product » n'existe pas | Graphie : les outils Shopify sont **à tirets** | `update-product`, `get-product`, `run-analytics-query` |
| Le prix ne semble pas appliqué | Mise à jour non confirmée | Le skill relit le produit après chaque `update-product` et n'annonce « fait » qu'après relecture |

## 🔒 Rappel sécurité

Côté **Qonto**, le skill est **100 % lecture** : aucun outil d'écriture bancaire, rien ne peut bouger sur le compte.
L'unique écriture est côté **Shopify** : une mise à jour de prix, produit par produit, **uniquement** après ta validation
explicite de la ligne concernée — un « applique tout » est refusé et re-demandé ligne à ligne. Et chaque marge affichée
rappelle sa méthode d'allocation : c'est une estimation pour décider, pas de la comptabilité.
