# 📖 Procédure d'installation et d'utilisation — qonto-ceo-cockpit

> Guide pas-à-pas utilisateur. Version jury : `PROCEDURE.en.md`.

---

## 1️⃣ Installation (une seule fois, ~5 min)

### Étape 1 — Connecter le MCP Qonto à Claude
1. Dans **claude.ai** (ou Claude Desktop) : Paramètres → **Connecteurs** → *Parcourir les connecteurs*
2. Chercher **Qonto** → *Ajouter* → le flux de connexion Qonto s'ouvre
3. Se connecter avec son compte Qonto (OAuth — le mot de passe n'est **jamais** partagé avec Claude)
4. Vérifier : demander à Claude « *Liste mes comptes Qonto* » → les comptes s'affichent

### Étape 2 — Installer le skill
- **Claude Code / Claude Desktop** : copier le dossier du skill dans `~/.claude/skills/qonto-ceo-cockpit/` (le fichier `SKILL.md` suffit)
- **claude.ai** : joindre le `SKILL.md` au projet, ou coller son contenu dans les instructions du projet

### Étape 3 — Poser quelques labels Qonto (recommandé)
1. Dans l'**app Qonto** : Transactions → sélectionner → **Labels** (« Abonnements », « Prestataires », « Déplacements »…)
2. Les labels deviennent les postes de dépenses du cockpit — plus il y en a, plus la vue des flux est parlante
3. Sans labels : le skill regroupe par contrepartie et propose un bucket « à catégoriser » explicite

> ℹ️ Pas besoin de tout labelliser : le cockpit affiche le nombre de transactions non catégorisées et ne les dilue jamais en douce.

## 2️⃣ Utilisation type (le lundi matin, ~2 min)

| # | Action | Résultat |
|---|---|---|
| 1 | Dire à Claude : « **Montre-moi ma boîte** » | Lecture 12 mois + factures + labels, dashboard HTML généré |
| 2 | Ouvrir le dashboard (artifact ou fichier) | Flux, KPI, cartes par poste, prévisionnel 3 mois |
| 3 | Bouger les sliders TJM × jours facturables | La projection 3 mois et l'atterrissage annuel se recalculent **en live, sans rappeler le MCP** |
| 4 | Cliquer l'œil 👁 sur les postes sensibles | Le poste disparaît de la vue, les totaux se recalculent, un chip permet de le réafficher |
| 5 | (Optionnel) « **Régénère sans les postes masqués** » | Export « présentation » : les données masquées ne sont plus DANS le fichier |

## 3️⃣ Prompts à copier-coller

- « **Montre-moi ma boîte** » → le cockpit complet
- « **Show me my company** » → pareil, en anglais
- « **D'où vient mon argent et où va-t-il cette année ?** » → vue des flux, bascule année
- « **Et si je passais mon TJM à 550 € ?** » → réponse chiffrée + rappel que le slider fait ça en live
- « **Prépare la version pour mon banquier, sans le poste X** » → régénération avec exclusion réelle
- « **Rafraîchis le cockpit** » → relecture des données, nouveau fichier

## 4️⃣ Formats de sortie

| Sortie | Format | Quand |
|---|---|---|
| **Dashboard interactif** | Un seul fichier **HTML autoportant** : CSS/JS inline, zéro dépendance externe, barres/rubans en CSS+SVG pur, thème clair/sombre | **Le livrable** — si l'hôte affiche les fichiers (artifacts claude.ai, Claude Desktop, Claude Code) |
| **Réponse dans la conversation** | Tableaux markdown : KPI, flux mois + année, prévisionnel 3 mois, scénarios TJM chiffrés | Repli automatique sinon |
| **Export « présentation »** | Le même HTML régénéré sans les postes sensibles dans les données | À la demande |

## 5️⃣ Dépannage (erreurs connues et vérifiées)

| Symptôme | Cause | Solution |
|---|---|---|
| `list_transactions` échoue d'entrée | `bank_account_id`/`iban` manquant | Normal — le skill appelle toujours `get_organization` d'abord |
| `403 missing oauth scope` sur `list_cash_flow_categories` | Hors périmètre du connecteur claude.ai | Prévu — le skill utilise les **labels** comme clé de regroupement |
| Réponses énormes / tronquées | Pagination trop large | Le skill pagine `per_page` ≤ 50, par fenêtres de 3 mois |
| Pas de panneau TJM | Aucune ligne de facture à l'unité « jour » | Normal (pas d'activité au temps passé) — le skill le dit et omet le panneau |
| Jauge du coffre absente | Pas de sous-compte au nom taxe/tax/impôt/TVA | Créer/renommer le sous-compte dans l'app, ou ignorer — tout le reste fonctionne |
| Le dashboard semble vide sur un poste | Transactions non labellisées | Bucket « à catégoriser » affiché avec son compte — labelliser dans l'app puis « Rafraîchis le cockpit » |
| Un montant paraît doublé | Virement interne compté comme flux | Le skill neutralise les virements entre comptes de l'organisation — signaler le cas s'il en reste un |

## 🔒 Rappel sécurité

Le skill est **100 % lecture** : aucun virement, aucun paiement, rien à approuver.
Le dashboard est un fichier **local** — les données ne quittent pas ta machine, aucun code externe ne se charge.
Le masquage 👁 est une commodité de **présentation** : les données restent dans la source du fichier.
Pour partager, demande la régénération « présentation » — là, les postes masqués sont réellement exclus.
