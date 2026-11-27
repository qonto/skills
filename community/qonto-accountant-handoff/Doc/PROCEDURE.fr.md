# 📖 Procédure d'installation et d'utilisation — qonto-accountant-handoff

> Guide pas-à-pas utilisateur. Version jury : `PROCEDURE.en.md`.

---

## 1️⃣ Installation (une seule fois, ~5 min)

### Étape 1 — Connecter le MCP Qonto à Claude
1. Dans **claude.ai** (ou Claude Desktop) : Paramètres → **Connecteurs** → *Parcourir les connecteurs*
2. Chercher **Qonto** → *Ajouter* → le flux de connexion Qonto s'ouvre
3. Se connecter avec son compte Qonto (OAuth — le mot de passe n'est **jamais** partagé avec Claude)
4. Vérifier : demander à Claude « *Liste mes comptes Qonto* » → les comptes s'affichent

### Étape 2 — Installer le skill
- **Claude Code / Claude Desktop** : copier le dossier du skill dans `~/.claude/skills/qonto-accountant-handoff/` (le fichier `SKILL.md` suffit)
- **claude.ai** : joindre le `SKILL.md` au projet, ou coller son contenu dans les instructions du projet

### Étape 3 — Connecter Google Drive et Gmail (optionnel, recommandé)
1. Toujours dans **Connecteurs** : ajouter **Google Drive** puis **Gmail** (OAuth Google)
2. C'est tout — le skill les **détecte automatiquement** à chaque exécution

> ⚠️ Ces deux connecteurs sont **optionnels**. Sans eux, le skill produit le même pack
> en local (dossier structuré markdown + CSV) et tu le transmets comme tu veux.

## 2️⃣ Utilisation mensuelle (le rituel de début de mois, ~5 min)

| # | Action | Résultat |
|---|---|---|
| 1 | Dire à Claude : « **Prépare le pack comptable de juin** » | Relevés + factures + état des justificatifs, tableaux affichés |
| 2 | Lire la **liste des manquants** (date, tiers, montant) | Tu sais exactement quelles pièces chasser — au besoin, lancer **qonto-receipt-hunter** |
| 3 | Relire la **lettre de passation** (points d'attention, questions) et l'amender si besoin | La lettre dit ce que TOI tu veux dire au cabinet |
| 4 | Confirmer le dépôt → arborescence `Comptabilité/AAAA/MM/` sur Drive + **brouillon** Gmail créé | Le pack est classé, l'email est prêt |
| 5 | Dans **Gmail → Brouillons** : relire → **envoyer toi-même** | La passation est partie ✅ — le skill n'envoie jamais |

## 3️⃣ Utilisations ponctuelles

- « **Qu'est-ce qui manque avant d'envoyer mars au cabinet ?** » → état des justificatifs + liste précise des manquants
- « **Prépare le pack du deuxième trimestre** » → même pack, périmètre T2
- « **Reprends la lettre de passation : ajoute la question sur le leasing** » → lettre amendée, pack mis à jour
- « **Où en est la couverture des justificatifs ce mois-ci ?** » → tableau de couverture, sans générer tout le pack

## 4️⃣ Formats de sortie (où atterrit le pack ?)

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown : contenu du pack, couverture, manquants, lettre | **Toujours** — c'est la base |
| **Dossier Google Drive** | `Comptabilité/AAAA/MM/` : lettre, relevés, factures, état des justificatifs | Si le MCP Drive est détecté — dépôt annoncé avant |
| **Brouillon Gmail** | Email récap au cabinet, lettre en corps, lien vers le dossier | Si le MCP Gmail est détecté — **jamais envoyé par le skill** |
| **Pack local** | Dossier structuré markdown + CSV, décrit fichier par fichier | Sans Drive/Gmail |

## 5️⃣ Dépannage (erreurs connues et vérifiées)

| Symptôme | Cause | Solution |
|---|---|---|
| `list_transactions` échoue d'entrée | `bank_account_id`/`iban` obligatoire | Le skill appelle **toujours** `get_organization` d'abord |
| Réponses énormes / lenteur | Pagination absente | Le skill pagine partout avec `per_page` ≤ 50 |
| Pas de relevé pour le mois demandé | Le mois n'est pas clos (ou compte ouvert en cours de mois) | Attendre la clôture du mois — en attendant, pack partiel annoncé comme tel |
| Transactions de bord de mois en trop / manquantes | Délais carte : `emitted_at` vs `settled_at` (1-2 j d'écart) | Le skill affiche les deux dates et signale les cas limites |
| `403 missing oauth scope` sur `list_cash_flow_categories` | Hors périmètre du connecteur claude.ai | Normal — le skill utilise les labels à la place |
| Pas de dépôt Drive / pas de brouillon Gmail | MCP non connecté | Normal — pack local produit ; connecter les connecteurs (étape 3) si tu veux l'automatisation |
| Lien de téléchargement d'une pièce expiré | Les URLs de pièces jointes sont temporaires | Relancer la demande — le skill récupère les liens au moment du dépôt, pas avant |

## 🔒 Rappel sécurité

Côté Qonto, le skill est en **lecture seule** — aucun outil d'écriture n'est utilisé, rien à approuver.
Les deux seules écritures sont chez toi : un dossier sur **ton** Google Drive (annoncé avant), et un
**brouillon** dans **ta** boîte Gmail. C'est toujours toi qui cliques sur envoyer. Et le skill ne fait
pas la compta : il prépare la matière, ton comptable reste le pro.
