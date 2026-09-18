# 📖 Procédure d'installation et d'utilisation — qonto-tax-radar

> Guide pas-à-pas utilisateur. Version jury : `PROCEDURE.en.md`.

---

## 1️⃣ Installation (une seule fois, ~5 min)

### Étape 1 — Connecter le MCP Qonto à Claude
1. Dans **claude.ai** (ou Claude Desktop) : Paramètres → **Connecteurs** → *Parcourir les connecteurs*
2. Chercher **Qonto** → *Ajouter* → le flux de connexion Qonto s'ouvre
3. Se connecter avec son compte Qonto (OAuth — le mot de passe n'est **jamais** partagé avec Claude)
4. Vérifier : demander à Claude « *Liste mes comptes Qonto* » → les comptes s'affichent

### Étape 2 — Installer le skill
- **Claude Code / Claude Desktop** : copier le dossier du skill dans `~/.claude/skills/qonto-tax-radar/` (le fichier `SKILL.md` suffit)
- **claude.ai** : joindre le `SKILL.md` au projet, ou coller son contenu dans les instructions du projet

### Étape 3 — Rien d'autre
Pas de sous-compte à créer, pas d'autorisation d'écriture à donner : le skill est en **lecture seule intégrale**.
Bonus (optionnel) : plus tes justificatifs sont attachés dans Qonto, plus l'axe 4 (TVA vs justificatifs) sera vert.

## 2️⃣ Utilisation type (le rituel trimestriel, ~5 min)

| # | Action | Résultat |
|---|---|---|
| 1 | Dire à Claude : « **Lance mon pré-contrôle fiscal** » | Les 8 axes annoncés, 12 mois de transactions scannés |
| 2 | Lire le rapport : bandeau global, tableau 8 axes 🟢🟡🔴 | Tu sais où tu es exposé et pour combien |
| 3 | Ouvrir le détail des signalements | Chaque point = transaction + article cité + action corrective |
| 4 | Suivre le plan de régularisation (justificatifs, requalifications) **avec ton expert-comptable** | Le dossier se nettoie |
| 5 | Relancer le skill le mois suivant | La note s'améliore — c'est la boucle vertueuse |

## 3️⃣ Prompts à copier-coller

- « **Lance mon pré-contrôle fiscal** » → rapport complet 8 axes
- « **Suis-je prêt pour un contrôle fiscal ?** » → même rapport, angle préparation
- « **Concentre-toi sur la TVA : qu'est-ce que je déduis sans justificatif ?** » → axe 4 seul, détail par transaction
- « **Passe en revue mes restaurants et cadeaux de l'année** » → axes 1-2 seuls
- « **Refais le pré-contrôle et compare avec le dernier rapport** » → re-run comparatif
- « **Génère l'avis de pré-contrôle en HTML** » → rapport riche si l'hôte affiche les fichiers

## 4️⃣ Formats de sortie (où atterrit le rapport ?)

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Bandeau global + tableau 8 axes + détail + plan de régularisation (markdown) | **Toujours** — c'est la base |
| **« Avis de pré-contrôle » interactif** | Fichier/artifact **HTML** : note globale, jauges par axe, checklist | Si l'hôte affiche les fichiers ; sinon repli automatique sur le markdown |
| **Re-run comparatif** | Même rapport, avec l'évolution de la note | À chaque relance |

## 5️⃣ Dépannage (erreurs connues et vérifiées)

| Symptôme | Cause | Solution |
|---|---|---|
| `list_transactions` échoue au premier appel | `bank_account_id`/`iban` manquant | Normal — le skill appelle **toujours** `get_organization` d'abord |
| `403 missing oauth scope` sur `list_cash_flow_categories` | Hors périmètre du connecteur claude.ai | Attendu — le skill utilise `list_labels` à la place |
| Réponses énormes / tronquées | Pagination trop large | Le skill pagine `per_page` ≤ 50, par fenêtres trimestrielles |
| Un achat du dimanche apparaît en semaine | Délai de règlement carte (`settled_at` +1-2 j) | Le skill lit les motifs carte sur `emitted_at` |
| « Beaucoup de faux positifs » | Le skill manque de contexte par construction | C'est annoncé dans le rapport : chaque point est « à documenter », pas une faute — trier avec l'expert-comptable |
| Société non française | Les articles cités sont français | Le skill bascule sur les axes universels et le dit — il n'invente jamais de règle locale |

## 🔒 Rappel sécurité

Le skill est en **lecture seule intégrale** : aucun outil d'écriture n'est jamais appelé. Il ne peut ni modifier
une transaction, ni poser un label, ni déplacer un centime. Et côté analyse : c'est une **simulation
pédagogique** — pas un avis fiscal, pas une position de l'administration. Les régularisations se décident
**avec ton expert-comptable**.
