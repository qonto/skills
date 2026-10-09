# 📖 Procédure d'installation et d'utilisation — qonto-rebill

> Guide pas-à-pas utilisateur. Version jury : `PROCEDURE.en.md`.

---

## 1️⃣ Installation (une seule fois, ~5 min)

### Étape 1 — Connecter le MCP Qonto à Claude
1. Dans **claude.ai** (ou Claude Desktop) : Paramètres → **Connecteurs** → *Parcourir les connecteurs*
2. Chercher **Qonto** → *Ajouter* → le flux de connexion Qonto s'ouvre
3. Se connecter avec son compte Qonto (OAuth — le mot de passe n'est **jamais** partagé avec Claude)
4. Vérifier : demander à Claude « *Liste mes comptes Qonto* » → les comptes s'affichent

### Étape 2 — Installer le skill
- **Claude Code / Claude Desktop** : copier le dossier du skill dans `~/.claude/skills/qonto-rebill/` (le fichier `SKILL.md` suffit)
- **claude.ai** : joindre le `SKILL.md` au projet, ou coller son contenu dans les instructions du projet

### Étape 3 — Préparer l'attribution (recommandé)
1. Dans l'**app Qonto** : Paramètres → **Labels** → créer un label par client (même nom que dans la Facturation, ex. « ACME Studio »)
2. Au fil de l'eau : labelliser chaque dépense engagée pour un client (2 secondes au moment du paiement)
3. Vérifier que tes clients existent dans **Facturation → Clients** (la facture a besoin d'un client existant)

> ⚠️ Sans labels, le skill fonctionne quand même : il passe en **attribution interactive**,
> transaction par transaction — plus lent, mais rien n'est perdu. Et il propose de
> labelliser au passage pour que le trimestre suivant soit automatique.

## 2️⃣ Utilisation trimestrielle (le rituel de fin de trimestre, ~5 min)

| # | Action | Résultat |
|---|---|---|
| 1 | Dire à Claude : « **Quels frais ai-je avancés pour mes clients ce trimestre ?** » | Tableau par client : date · tiers · montant · justificatif ✅/⚠️ |
| 2 | Compléter les justificatifs manquants (skill `qonto-receipt-hunter`) | Chaque ligne part avec sa pièce |
| 3 | Répondre à la question fiscale (débours ou refacturation ? majoration ?) | Le skill affiche le tableau comparatif et attend ton choix |
| 4 | Dire : « **Prépare la facture pour [client]** » | Brouillon `create_client_invoice` ligne à ligne, relisible dans Qonto |
| 5 | Relire, puis confirmer explicitement (« oui, envoie ») | Facture envoyée ✅ — jamais avant ta confirmation |

## 3️⃣ Utilisations ponctuelles

- « **Qu'est-ce que j'ai avancé pour [client] depuis janvier ?** » → frais attribués + total, période libre
- « **Y a-t-il des frais que j'ai oublié de refacturer ?** » → scan des périodes passées, frais attribués jamais facturés
- « **Explique-moi débours vs frais refacturés** » → le tableau comparatif, sans rien créer
- « **Prépare la refacturation avec 10 % de frais de gestion** » → majoration au choix (jamais sur un débours)

## 4️⃣ Formats de sortie

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown : frais par client (justificatif ✅/⚠️), facture ligne à ligne, total récupéré | **Toujours** — c'est la base |
| **Brouillon de facture Qonto** | `create_client_invoice` en brouillon, visible dans Facturation | Après ton accord sur le régime |
| **Pack justificatifs** | Liens de téléchargement (durée limitée) à joindre à l'envoi | À chaque facture préparée |
| **Récap HTML** | Cartes par client, jauge justificatifs, montants récupérés | Si l'hôte affiche les fichiers ; sinon repli sur les tableaux |

## 5️⃣ Dépannage (erreurs connues et vérifiées)

| Symptôme | Cause | Solution |
|---|---|---|
| `list_transactions` échoue d'entrée | `bank_account_id`/`iban` manquant | Normal — le skill appelle toujours `get_organization` d'abord |
| Réponses énormes / tronquées | Pagination trop large | Le skill pagine `per_page` ≤ 50 partout |
| Un frais de fin de trimestre manque | Frais carte réglé 1-2 jours plus tard | Le skill regroupe par `emitted_at`, pas `settled_at` |
| `403 missing oauth scope` sur `list_cash_flow_categories` | Hors périmètre du connecteur claude.ai | Normal — le skill travaille avec les labels |
| Client introuvable pour la facture | Absent de Facturation → Clients | Le créer dans l'app (Facturation → Clients), puis relancer le skill |
| Justificatif absent sur une ligne | Pièce jamais attachée à la transaction | Lancer `qonto-receipt-hunter` avant de refacturer |
| Une facture de test traîne | Les factures MCP sont **réelles** | Répétitions : client fictif + brouillon + `delete_client_invoice` |

## 🔒 Rappel sécurité

Le skill ne crée qu'un **brouillon** de facture — rien ne part vers ton client sans ta
confirmation explicite dans la conversation. Le choix fiscal (débours vs refacturation)
t'appartient, avec ton expert-comptable : le skill explique, compare, demande — il ne
décide jamais seul. Et il n'attribue jamais un frais à un client sans ton accord.
