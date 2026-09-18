# 📖 Procédure d'installation et d'utilisation — qonto-subscription-audit

> Guide pas-à-pas utilisateur. Version jury : `PROCEDURE.en.md`.

---

## 1️⃣ Installation (une seule fois, ~5 min)

### Étape 1 — Connecter le MCP Qonto à Claude
1. Dans **claude.ai** (ou Claude Desktop) : Paramètres → **Connecteurs** → *Parcourir les connecteurs*
2. Chercher **Qonto** → *Ajouter* → le flux de connexion Qonto s'ouvre
3. Se connecter avec son compte Qonto (OAuth — le mot de passe n'est **jamais** partagé avec Claude)
4. Vérifier : demander à Claude « *Liste mes comptes Qonto* » → les comptes s'affichent

### Étape 2 — Installer le skill
- **Claude Code / Claude Desktop** : copier le dossier du skill dans `~/.claude/skills/qonto-subscription-audit/` (le fichier `SKILL.md` suffit)
- **claude.ai** : joindre le `SKILL.md` au projet, ou coller son contenu dans les instructions du projet

### Étape 3 — Connecter le MCP Gmail (optionnel)
1. Paramètres → **Connecteurs** → chercher **Gmail** → *Ajouter*
2. Avec Gmail : les emails de négo ET le digest mensuel arrivent en **brouillons** dans ta boîte (jamais envoyés)
3. Sans Gmail : le skill fournit le texte à copier-coller — tout le reste marche pareil

## 2️⃣ Utilisation type (l'audit mensuel, ~5 min)

| # | Action | Résultat |
|---|---|---|
| 1 | Dire à Claude : « **Audite mes abonnements** » | Scan 24-36 mois : inventaire complet, cadences (mensuel/trimestriel/annuel), **coût annuel total** |
| 2 | Lire les statuts (✅👥🧟🎣) et la section **🌱 Nouveaux** | Tu sais qui te prélève quoi, ce qui fait doublon, ce qui dort — et ce qui vient de commencer |
| 3 | Confirmer ou infirmer les zombies 🧟 et les nouveaux 🌱 proposés | Le skill ne décrète jamais — c'est toi qui confirmes l'usage |
| 4 | Lire le tableau des hausses et le **surcoût annuel cumulé** | Tu sais ce que l'inflation silencieuse te coûte par an, hors change/TVA/usage |
| 5 | Dire : « **Montre-moi le dashboard** » | Dashboard construit directement dans Claude ; « exporte-le en HTML » → fichier autoportant charte Qonto |
| 6 | Dire : « **Écris l'email de négo pour [fournisseur]** » puis confirmer | Brouillon Gmail (ou texte) : ancienneté, volume, historique des hausses → **relire, ajuster, envoyer toi-même** ✅ |

> 💡 Pour **protéger un abonnement par carte plafonnée** (plafond mensuel, prélèvements au-delà refusés) : c'est le skill **`qonto-subscription-guardian`** — l'audit trouve, le guardian protège.

## 3️⃣ Utilisations ponctuelles

- « **Combien je paie d'abonnements par an ?** » → le chiffre choc + portefeuille trié par coût annuel
- « **Qu'est-ce que je paie encore sans l'utiliser ?** » → candidats 🧟 + essais 🎣, à confirmer
- « **Ce prélèvement de 19 € chez [marchand], c'est un abonnement ?** » → analyse 🌱 : indices et verdict « probable / peu probable, à confirmer »
- « **Qui a augmenté ses prix cette année ?** » → hausses datées (ancien → nouveau, %, tag 🟢🟡🔴)
- « **Mon prix unitaire cloud a-t-il augmenté, ou juste ma conso ?** » → prix implicite si isolable, sinon dit franchement
- « **Prépare mon digest abonnements du mois** » → brouillon d'email : actifs, total du mois, prévisionnel 3 mois, hausses, nouveaux 🌱 (si MCP mail)

## 4️⃣ Formats de sortie (où atterrit l'audit ?)

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown : chiffre choc, portefeuille par statut, section Nouveaux 🌱, hausses, usage variable à part | **Toujours** — c'est la base |
| **Dashboard dans Claude** | Rendu directement dans la conversation (artifact) : coût annuel, répartition par catégorie, statuts ✅👥🧟🎣🌱, hausses avec deltas, prévisionnel 3 mois | Quand l'hôte le permet |
| **Export HTML** | Le même dashboard en fichier autoportant, charte Qonto (violet #6B4EFF / noir #1D1B29 / blanc, clair/sombre) | Sur demande — à garder ou partager |
| **Emails** | Brouillon Gmail (MCP présent + ton accord) ou texte à copier : négo + digest mensuel | **Jamais envoyés** sans toi |

## 5️⃣ Dépannage (erreurs connues et vérifiées)

| Symptôme | Cause | Solution |
|---|---|---|
| « `list_transactions` échoue » au démarrage | `bank_account_id`/`iban` manquant | Normal — le skill appelle `get_organization` d'abord, toujours |
| Réponses énormes / tronquées | Pagination trop large | Le skill pagine `per_page` ≤ 50, fenêtres de 3 mois |
| `403 missing oauth scope` sur `list_cash_flow_categories` | Hors périmètre du connecteur claude.ai | Normal — le skill se base sur les contreparties et labels |
| Un abonnement annuel connu n'apparaît pas | Historique scanné < 24 mois : une seule occurrence visible | Le skill le dit honnêtement ; relancer avec plus d'historique si le compte en a |
| Un fournisseur apparaît en double | Variantes carte/SEPA non fusionnées (libellé exotique) | Signale-le : « fusionne X et Y » — la normalisation apprend |
| Cadence détectée fausse sur les paiements carte | Rapprochement fait sur `settled_at` (décalage 1-2 j) | Le skill utilise `emitted_at` pour les cadences |
| « Hausse » sur un abonnement en USD | Variation de change, pas de prix | Le skill marque la série comme exposée au change et ne conclut pas |
| Un 🌱 signalé n'est pas un abonnement | Détection précoce = probabiliste (< 3 occurrences) | Réponds « non » : la ligne est écartée — 🌱 est une hypothèse, jamais un verdict |
| Pas de brouillon Gmail créé | MCP Gmail absent ou non autorisé | Le skill le dit et fournit le texte à copier — rien n'est perdu |
| Pas de dashboard affiché | L'hôte ne rend pas les artifacts/fichiers | Les tableaux markdown restent le livrable complet |

## 🔒 Rappel sécurité

Le skill est **100 % lecture** sur Qonto : aucune écriture, aucun virement, aucune carte créée —
pour la carte plafonnée, c'est le skill `qonto-subscription-guardian`, avec ton consentement et ta SCA.
Les emails (négo, digest) sont des **brouillons** — c'est toi qui relis, modifies et envoies (ou pas).
Aucun destinataire n'est ajouté sans toi. Les IBAN sont masqués dans tous les rapports.
