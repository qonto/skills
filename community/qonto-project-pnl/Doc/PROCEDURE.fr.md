# 📖 Procédure d'installation et d'utilisation — qonto-project-pnl

> Guide pas-à-pas utilisateur. Version jury : `PROCEDURE.en.md`.

---

## 1️⃣ Installation (une seule fois, ~5 min)

### Étape 1 — Connecter le MCP Qonto à Claude
1. Dans **claude.ai** (ou Claude Desktop) : Paramètres → **Connecteurs** → *Parcourir les connecteurs*
2. Chercher **Qonto** → *Ajouter* → le flux de connexion Qonto s'ouvre
3. Se connecter avec son compte Qonto (OAuth — le mot de passe n'est **jamais** partagé avec Claude)
4. Vérifier : demander à Claude « *Liste mes comptes Qonto* » → les comptes s'affichent

### Étape 2 — Connecter le connecteur Notion (recommandé)
1. Même endroit : Paramètres → **Connecteurs** → chercher **Notion** → *Ajouter* (OAuth)
2. Autoriser l'accès au workspace (ou à une section dédiée — le skill n'écrira que dans **sa** base)
3. Vérifier : « *Liste mes pages Notion récentes* » → des pages s'affichent

> ⭕ Sans Notion : le skill fonctionne quand même — P&L en tableaux dans la conversation + dashboard HTML.

### Étape 3 — Installer le skill
- **Claude Code / Claude Desktop** : copier le dossier du skill dans `~/.claude/skills/qonto-project-pnl/` (le fichier `SKILL.md` suffit)
- **claude.ai** : joindre le `SKILL.md` au projet, ou coller son contenu dans les instructions du projet

### Étape 4 — Labelliser ses transactions par projet (recommandé)
Dans l'app Qonto : créer un **label par projet** et l'appliquer aux transactions concernées.
Sans labels, le skill propose un mapping depuis les tiers récurrents (tout en 🟡) — mais les labels restent la voie royale.

## 2️⃣ Utilisation mensuelle (le rituel, ~3 min)

| # | Action | Résultat |
|---|---|---|
| 1 | Dire à Claude : « **Construis le P&L par projet et mets à jour ma base Finance dans Notion** » | Lecture du compte, mapping label → projet proposé |
| 2 | Vérifier / corriger le mapping, confirmer (mémorisé pour les prochaines fois) | Revenus encaissés + coûts attribués calculés |
| 3 | Lire le P&L (marge, burn, alertes ⚠️) et l'aperçu de l'écriture Notion, dire « oui » | Base « Finance » créée ou **mise à jour en place** — jamais de doublon |
| 4 | Ouvrir sa page projet dans **Notion** | L'entrée P&L affiche « mise à jour il y a 1 min » ✅ |

## 3️⃣ Utilisations ponctuelles

- « **Quelle est la marge réelle du projet Aurora ?** » *(nom inventé — utilise les tiens)* → P&L du projet, encaissé vs coûts
- « **Quel projet perd de l'argent ?** » → classement par marge, alertes 🔴
- « **Montre-moi le mapping labels → projets avant de calculer** » → tableau de mapping seul, corrigeable
- « **Quel est mon burn mensuel par projet ?** » → burn 3 mois glissants, par projet
- « **Fais le P&L sans toucher à Notion** » → mode tableaux + dashboard HTML uniquement

## 4️⃣ Formats de sortie (où atterrit le P&L ?)

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown (P&L par projet, alertes, orphelins) | **Toujours** — c'est la base |
| **Base « Finance » dans Notion** | Base dédiée « Finance — P&L (générée) », une entrée par projet, mise à jour à chaque exécution | Si le connecteur Notion est présent + consentement explicite |
| **Dashboard interactif** | Fichier/artifact **HTML** : barres revenus vs coûts, marge, burn, alertes | Si l'hôte affiche les fichiers ; repli automatique sur les tableaux |

## 5️⃣ Dépannage (erreurs connues et vérifiées)

| Symptôme | Cause | Solution |
|---|---|---|
| Erreur sur `list_transactions` dès le départ | `bank_account_id`/`iban` obligatoire | Le skill appelle **toujours** `get_organization` d'abord |
| `403 missing oauth scope` sur `list_cash_flow_categories` | Hors périmètre du connecteur claude.ai | Normal — le skill travaille avec les **labels**, jamais avec cet outil |
| Réponses énormes ou tronquées | Pagination absente | Le skill pagine `per_page` ≤ 50 partout |
| Aucun projet détecté | Pas de labels Qonto | Mapping proposé depuis les tiers récurrents (🟡) ; labelliser dans l'app pour la suite |
| La base Finance n'apparaît pas dans Notion | Connecteur Notion absent ou non autorisé | Paramètres → Connecteurs → Notion ; en attendant, mode dégradé (tableaux + dashboard) |
| Risque d'entrée en double dans Notion | Projet renommé entre deux exécutions | Le skill rapproche par **nom de projet** : confirmer le renommage dans le mapping au lieu de créer un jumeau |
| Revenus à zéro alors que des factures existent | Factures non payées, ou paiements non rapprochés | Le skill ne compte que l'**encaissé** ; vérifier les statuts et confirmer le matching proposé |
| Un coût annuel manque (licence, domaine…) | Historique scanné trop court | Le skill couvre 24-36 mois quand l'historique le permet — les cadences annuelles ne se voient que là |

## 🔒 Rappel sécurité

Côté Qonto, le skill est en **lecture seule** : zéro écriture, aucun argent ne bouge, nulle part.
Côté Notion, il n'écrit que dans **sa** base dédiée, marquée comme générée, après un aperçu
et ton « oui » explicite — jamais dans tes pages existantes. Relancer le skill met la base
à jour, sans doublon ni suppression.
