# 📖 Procédure d'installation et d'utilisation — qonto-infra-margin

> Guide pas-à-pas utilisateur. Version jury : `PROCEDURE.en.md`.

---

## 1️⃣ Installation (une seule fois, ~5 min)

### Étape 1 — Connecter le MCP Qonto à Claude
1. Dans **claude.ai** (ou Claude Desktop) : Paramètres → **Connecteurs** → *Parcourir les connecteurs*
2. Chercher **Qonto** → *Ajouter* → le flux de connexion Qonto s'ouvre
3. Se connecter avec son compte Qonto (OAuth — le mot de passe n'est **jamais** partagé avec Claude)
4. Vérifier : demander à Claude « *Liste mes comptes Qonto* » → les comptes s'affichent

### Étape 2 — Connecter les MCP produit (recommandé, pour le €/utilisateur)
1. Même chemin : Connecteurs → ajouter **Vercel** puis **Supabase** (login OAuth chez chaque éditeur)
2. Optionnel : **Sentry** (contexte volume d'erreurs)
3. Vérifier : « *Liste mes projets Vercel* » et « *Liste mes projets Supabase* » → les projets s'affichent

> ⭕ Sans ces MCP, le skill fonctionne en **mode dégradé annoncé** : classification des débits infra,
> total par mois, tendance — déjà utile. Il te dira quoi connecter pour aller plus loin.

### Étape 3 — Installer le skill
- **Claude Code / Claude Desktop** : copier le dossier du skill dans `~/.claude/skills/qonto-infra-margin/` (le fichier `SKILL.md` suffit)
- **claude.ai** : joindre le `SKILL.md` au projet, ou coller son contenu dans les instructions du projet

## 2️⃣ Usage type (l'audit mensuel, ~5 min)

| # | Action | Résultat |
|---|---|---|
| 1 | Dire à Claude : « **Combien me coûte mon infra, et par utilisateur ?** » | Scan des débits 12-24 mois, P&L infra fournisseur × mois |
| 2 | Le skill détecte les MCP Vercel/Supabase et propose la télémétrie | Projets et déploiements réels tirés de Vercel |
| 3 | **Confirmer la table qui compte tes utilisateurs** (ex. `auth.users`) | Un seul `SELECT count(*)` en lecture seule est lancé |
| 4 | Lire le tableau unit economics | €/utilisateur, €/projet (prorata affiché), dérive de marge |
| 5 | Regarder la liste des « saignées » | Side-projects facturés sans déploiement depuis 90 j, avec preuves |

## 3️⃣ Prompts à copier-coller

- « **Combien me coûte mon infra par utilisateur ?** » → l'analyse complète
- « **Isole mes dépenses d'infra des 12 derniers mois** » → le P&L infra seul (marche sans MCP produit)
- « **Combien je dépense en API IA, et ça évolue comment ?** » → focus famille IA + tendance
- « **Quels side-projects me coûtent de l'argent pour rien ?** » → les saignées, avec preuves
- « **Ma marge brute dérive ?** » → infra en % des encaissements, mois par mois (proxy annoncé)

## 4️⃣ Formats de sortie (où atterrit l'analyse ?)

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown : P&L infra, unit economics, saignées | **Toujours** — c'est la base |
| **Dashboard interactif** | Fichier/artifact **HTML** : barres par famille, jauge €/user, courbe de dérive, spotlight saignées | Si l'hôte affiche les fichiers (artifacts claude.ai, Claude Desktop, Claude Code) ; sinon repli automatique |
| **Mode dégradé** | Mêmes tableaux sans €/user ni allocation par projet — annoncé | Sans MCP Vercel/Supabase |

## 5️⃣ Dépannage (erreurs connues et vérifiées)

| Symptôme | Cause | Solution |
|---|---|---|
| `list_transactions` échoue d'emblée | `bank_account_id`/`iban` manquant | Normal — le skill appelle toujours `get_organization` d'abord |
| Réponses énormes / tronquées | Pagination trop large | Le skill pagine `per_page` ≤ 50, par fenêtres de 3 mois |
| Les totaux ≠ le dashboard Vercel/AWS | Facturation USD, débit en EUR (change inclus) | Attendu — la vérité du skill, c'est le débit du compte ; l'écart est expliqué |
| Facture fournisseur introuvable face au débit carte | Rapprochement sur la mauvaise date | Rapprocher par `emitted_at`, pas `settled_at` (1-2 j d'écart) |
| `execute_sql` échoue ou table inconnue | La table « users » varie selon l'app | Le skill propose `auth.users` par défaut et **demande confirmation** — indique ta table/filtre |
| Un coût annuel pris pour un one-off | Historique trop court | Étendre le scan à 24-36 mois (les cadences annuelles ne se voient que là) |
| `403 missing oauth scope` sur `list_cash_flow_categories` | Hors périmètre du connecteur claude.ai | Normal — le skill n'en a pas besoin (labels en repli si utile) |

## 🔒 Rappel sécurité

Le skill est **100 % lecture, des deux côtés**. Côté Qonto : aucun outil d'écriture, jamais — rien à approuver,
rien d'exécuté. Côté produit : `execute_sql` est limité à des `SELECT count` unitaires en lecture seule,
sur une table que **toi seul** confirmes avant exécution. Aucune métrique produit n'est inventée :
pas de comptage mesuré → pas de €/utilisateur, et le skill le dit.
