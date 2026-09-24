# 📖 Procédure d'installation et d'utilisation — qonto-project-burn

> Guide pas-à-pas utilisateur. Version jury : `PROCEDURE.en.md`.

---

## 1️⃣ Installation (une seule fois, ~5 min)

### Étape 1 — Connecter le MCP Qonto à Claude
1. Dans **claude.ai** (ou Claude Desktop) : Paramètres → **Connecteurs** → *Parcourir les connecteurs*
2. Chercher **Qonto** → *Ajouter* → le flux de connexion Qonto s'ouvre
3. Se connecter avec son compte Qonto (OAuth — le mot de passe n'est **jamais** partagé avec Claude)
4. Vérifier : demander à Claude « *Liste mes comptes Qonto* » → les comptes s'affichent

### Étape 2 — Installer le skill
- **Claude Code / Claude Desktop** : copier le dossier du skill dans `~/.claude/skills/qonto-project-burn/` (le fichier `SKILL.md` suffit)
- **claude.ai** : joindre le `SKILL.md` au projet, ou coller son contenu dans les instructions du projet

### Étape 3 — Connecter Linear ou Jira (optionnel mais recommandé)
1. Paramètres → **Connecteurs** → chercher **Linear** (ou **Jira / Atlassian**) → *Ajouter*
2. C'est tout — le skill **détecte le MCP automatiquement** à l'exécution
3. Sans tracker connecté : **mode dégradé** propre — rapport complet par projet dans la conversation + dashboard HTML

> 💡 Bonus : quelques transactions labellisées par projet dans Qonto (app → transaction → Labels)
> rendent le mapping immédiat. Sans labels, le skill propose un mapping depuis les fournisseurs récurrents.

## 2️⃣ Première utilisation (le mapping, ~3 min)

| # | Action | Résultat |
|---|---|---|
| 1 | Dire à Claude : « **Combien a coûté chaque projet ?** » | Le skill lit les comptes et les labels, propose la table label → projet |
| 2 | Corriger les lignes fausses, **déclarer le budget** de chaque projet | Table de mapping validée, montrée en clair |
| 3 | Coller le bloc de config restitué dans les **instructions du projet Claude** | Le mapping est mémorisé pour toutes les prochaines conversations |
| 4 | Lire le rapport : dépensé, %, rythme, date de dépassement projetée | Tu sais exactement où en est chaque projet ✅ |

## 3️⃣ Utilisation régulière (le rituel du lundi matin, ~2 min)

| # | Action | Résultat |
|---|---|---|
| 1 | « **Où en est le burn des projets ?** » | Tableau par projet ✅/⚠️/🔴, orphelines listées |
| 2 | « **Publie le statut dans Linear** » | Prévisualisation du texte exact du commentaire (+ issue d'alerte si seuil franchi) |
| 3 | Confirmer explicitement (« oui, publie ») | Commentaire posté sur le projet Linear/Jira ; issue « ⚠️ Budget [projet] Z % » créée si seuil franchi |
| 4 | L'équipe voit le statut **dans son outil**, avec les transactions Qonto en justification | La finance vient à l'équipe ✅ |

## 4️⃣ Prompts à copier-coller

- « **Combien a coûté le projet Alpha, au total et ce mois-ci ?** » → burn détaillé, top fournisseurs
- « **Quels projets dépassent 80 % de leur budget ?** » → alertes seuils
- « **À ce rythme, quand est-ce qu'on dépasse ?** » → dates de dépassement projetées
- « **Montre-moi les transactions non attribuées** » → orphelines + options de rangement
- « **Publie le statut de tous les projets dans Linear** » → prévisualisation puis écriture (avec ton accord)

## 5️⃣ Formats de sortie (où atterrit le burn ?)

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown (burn par projet, orphelines, alertes) | **Toujours** — c'est la base |
| **Commentaire Linear/Jira** | « X € / Y € — Z % · dépassement estimé le [date] » sur le projet mappé | MCP tracker détecté + accord explicite |
| **Issue d'alerte Linear/Jira** | « ⚠️ Budget [projet] Z % » + transactions justificatives | Seuil franchi + accord explicite |
| **Dashboard interactif** | Fichier/artifact **HTML** : barres dépensé/budget, rythme, marqueurs | Si l'hôte affiche les fichiers ; repli automatique sur les tableaux |

## 6️⃣ Dépannage (erreurs connues et vérifiées)

| Symptôme | Cause | Solution |
|---|---|---|
| `list_transactions` échoue d'entrée | `bank_account_id`/`iban` manquant | Le skill appelle **toujours** `get_organization` d'abord |
| `403 missing oauth scope` sur `list_cash_flow_categories` | Hors périmètre du connecteur claude.ai | Normal — le mapping se fait sur les **labels** |
| Réponses énormes / tronquées | Pagination absente | `per_page` ≤ 50 partout, fenêtres de 3 mois |
| Le skill ne peut pas labelliser une transaction | Le MCP Qonto n'a **pas d'outil** pour attacher un label | Liste prête à traiter fournie → labelliser dans l'app (une fois) ; ou rangement optionnel via catégorie de cash-flow (confirmé) |
| Un montant compté deux fois | Transaction multi-labels | Comptée **une fois**, premier label du mapping — annoncé dans le rapport |
| Pas d'écriture dans Linear | MCP Linear/Jira absent ou non connecté | Détection dynamique : le skill le dit et passe en mode dégradé (rapport + dashboard) |
| Dépenses carte décalées | `settled_at` en retard de 1-2 j | Le skill rapproche sur `emitted_at` |

## 🔒 Rappel sécurité

Côté Qonto, le skill **ne fait que lire** : aucun virement, aucun paiement, aucune écriture qui touche à l'argent.
La seule écriture notable est un **commentaire ou une issue dans Linear/Jira** — toujours prévisualisée en texte
intégral et publiée **uniquement** après ton accord explicite dans la conversation. Le rangement optionnel des
orphelines (catégorie de cash-flow) est léger, réversible et lui aussi confirmé avant chaque écriture.
