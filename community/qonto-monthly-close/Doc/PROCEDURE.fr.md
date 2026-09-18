# 📖 Procédure d'installation et d'utilisation — qonto-monthly-close

> Guide pas-à-pas utilisateur. Version jury : `PROCEDURE.en.md`.

---

## 1️⃣ Installation (une seule fois, ~5 min)

### Étape 1 — Connecter le MCP Qonto à Claude
1. Dans **claude.ai** (ou Claude Desktop) : Paramètres → **Connecteurs** → *Parcourir les connecteurs*
2. Chercher **Qonto** → *Ajouter* → le flux de connexion Qonto s'ouvre
3. Se connecter avec son compte Qonto (OAuth — le mot de passe n'est **jamais** partagé avec Claude)
4. Vérifier : demander à Claude « *Liste mes comptes Qonto* » → les comptes s'affichent

### Étape 2 — Installer le skill
- **Claude Code / Claude Desktop** : copier le dossier du skill dans `~/.claude/skills/qonto-monthly-close/` (le fichier `SKILL.md` suffit)
- **claude.ai** : joindre le `SKILL.md` au projet, ou coller son contenu dans les instructions du projet

### Étape 3 — (Optionnel) Connecter Gmail
1. Paramètres → **Connecteurs** → ajouter **Gmail**
2. Le skill le détectera tout seul et proposera de chercher les reçus manquants dans la boîte mail
3. Sans Gmail : le skill le dit en une ligne et continue — rien d'autre ne change

> ℹ️ Aucun sous-compte, aucune configuration côté Qonto : ce skill est en **lecture seule intégrale**,
> il n'a besoin d'aucun droit d'écriture pour fonctionner.

## 2️⃣ Utilisation mensuelle (le rituel du 1er du mois, ~3 min)

| # | Action | Résultat |
|---|---|---|
| 1 | Dire à Claude : « **Clôture mon mois** » | Le skill cadre le mois (dernier mois complet par défaut) et annonce son plan |
| 2 | Laisser tourner la revue (~2-3 min selon le volume) | Justificatifs, TVA, anomalies, sans-label, impayés, comparaison — en une passe |
| 3 | Lire le **rapport de clôture** : scorecard + tableaux + to-do priorisée | Tu sais exactement quoi régulariser, dans quel ordre, et pourquoi |
| 4 | Dérouler la to-do : chaque ligne pointe vers le skill dédié ou l'action en un tap dans l'app Qonto | Fin de mois pliée en ~10 minutes ✅ |

## 3️⃣ Utilisations ponctuelles

- « **Clôture mon mois de mai** » → revue complète d'un mois précis
- « **Il y a des anomalies sur mon compte le mois dernier ?** » → seulement les 3 détecteurs (dépense inhabituelle, doublon, nouveau bénéficiaire)
- « **Quels justificatifs me manquent, les plus gros d'abord ?** » → la liste priorisée par enjeu
- « **Compare juin à mai** » → top hausses/baisses par poste
- « **C'est quoi ma TVA du mois ?** » → collectée − déductible, avec les réserves

## 4️⃣ Formats de sortie (où atterrit le rapport ?)

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown : scorecard, justificatifs, TVA, anomalies, comparaison, impayés, to-do | **Toujours** — c'est la base |
| **Dashboard de clôture** | Fichier/artifact **HTML** : scorecard, jauge de complétude, tuile TVA, cartes anomalies, checklist | Si l'hôte affiche les fichiers (artifacts claude.ai, Claude Desktop, Claude Code) ; sinon repli automatique sur les tableaux |

## 5️⃣ Dépannage (erreurs connues et vérifiées)

| Symptôme | Cause | Solution |
|---|---|---|
| `list_transactions` échoue d'entrée | `bank_account_id`/`iban` manquant | Normal — le skill appelle toujours `get_organization` d'abord |
| `403 missing oauth scope` sur `list_cash_flow_categories` | Hors périmètre du connecteur claude.ai | Normal — le skill utilise `list_labels` à la place |
| Réponses énormes / lenteur | Pagination trop large | Le skill pagine `per_page` ≤ 50 partout |
| Une dépense carte du 30-31 « manque » dans le mois | Décalage `emitted_at` vs `settled_at` (1-2 j) | Le skill raisonne sur `emitted_at` pour les opérations carte |
| TVA collectée qui semble fausse | Régime TVA sur les encaissements (`on_receipts`) | Le skill le détecte sur les factures et compte les paiements reçus, pas les factures émises |
| Anomalies trop nombreuses / absentes | Historique < 3 mois → baseline trop mince | Le skill l'annonce et modère ses seuils ; ça s'améliore avec l'historique |

## 🔒 Rappel sécurité

Ce skill est en **lecture seule intégrale** : il n'appelle aucun outil d'écriture — rien n'est créé,
modifié, envoyé ni déplacé sur ton compte. Le rapport **propose** ; c'est toi qui agis, directement
dans l'app Qonto ou en enchaînant sur les skills dédiés (`qonto-receipt-hunter`, `qonto-invoice-chaser`,
`qonto-tax-pilot`). Et de toute façon : le MCP Qonto ne peut pas déplacer d'argent — tout virement
exige ta SCA (2FA) dans l'app.
