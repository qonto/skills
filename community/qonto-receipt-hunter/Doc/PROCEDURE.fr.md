# 📖 Procédure d'installation et d'utilisation — qonto-receipt-hunter

> Guide pas-à-pas utilisateur. Version jury : `PROCEDURE.en.md`.

---

## 1️⃣ Installation (une seule fois, ~5 min)

### Étape 1 — Connecter le MCP Qonto à Claude
1. Dans **claude.ai** (ou Claude Desktop) : Paramètres → **Connecteurs** → *Parcourir les connecteurs*
2. Chercher **Qonto** → *Ajouter* → le flux de connexion Qonto s'ouvre
3. Se connecter avec son compte Qonto (OAuth — le mot de passe n'est **jamais** partagé avec Claude)
4. Vérifier : demander à Claude « *Liste mes comptes Qonto* » → les comptes s'affichent

### Étape 2 — Installer le skill
- **Claude Code / Claude Desktop** : copier le dossier du skill dans `~/.claude/skills/qonto-receipt-hunter/` (le fichier `SKILL.md` suffit)
- **claude.ai** : joindre le `SKILL.md` au projet, ou coller son contenu dans les instructions du projet

### Étape 3 — Connecter Gmail et Google Drive (recommandé)
1. Paramètres → **Connecteurs** → ajouter **Gmail**, puis **Google Drive** (OAuth Google)
2. C'est ce qui alimente la chasse : sans eux, le skill livre quand même l'inventaire priorisé et la TVA en jeu — il te dira simplement où chercher à la main

> ℹ️ Le skill détecte tout seul les connecteurs présents. Rien à configurer de plus.

## 2️⃣ Utilisation type (la session de chasse, ~5 min)

| # | Action | Résultat |
|---|---|---|
| 1 | Dire à Claude : « **Quelles transactions sans justificatif ?** » | Inventaire priorisé : X pièces manquantes, ~Y € de TVA récupérable en jeu, tags 🔴🟠🟢 |
| 2 | Dire : « **Pars à la chasse** » | Gmail et Drive fouillés (marchand + montant + dates autour de l'achat) ; reçus originaux retrouvés |
| 3 | Vérifier chaque match affiché (transaction ↔ document) et **confirmer un par un** | Pièce rattachée à la transaction, vérifiée, visible dans l'app Qonto ✅ |
| 4 | Lire le rapport final | ✅ rattachées / 📎 à joindre / ❌ introuvables avec une piste chacune + score avant/après |

## 3️⃣ Prompts à copier-coller

- « **Quelles transactions n'ont pas de justificatif ce trimestre ?** » → inventaire priorisé + TVA en jeu
- « **Combien de TVA je risque de perdre ?** » → le chiffrage seul, sans chasse
- « **Retrouve la facture [marchand] dans mes mails** » → chasse ciblée sur une transaction
- « **Pars à la chasse et propose-moi les rattachements** » → session complète (confirmations une par une)
- « **Rapport de complétude du mois** » → score + trous restants + pistes

## 4️⃣ Formats de sortie

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown (inventaire priorisé, TVA en jeu, rapport de chasse) | **Toujours** — c'est la base |
| **Rattachements Qonto** | Pièces jointes réelles sur les transactions, visibles immédiatement dans l'app | À chaque confirmation |
| **Rapport de complétude** | Score avant/après + pistes ; version HTML si l'hôte affiche les fichiers, tableaux sinon | Fin de session |

## 5️⃣ Dépannage (erreurs connues et vérifiées)

| Symptôme | Cause | Solution |
|---|---|---|
| `list_transactions` échoue | `bank_account_id`/`iban` manquant | `get_organization` d'abord — le skill le fait systématiquement |
| Réponses énormes / lenteur | Pagination trop large | `per_page` ≤ 50 partout — géré par le skill |
| Le reçu existe dans Gmail mais la chasse le rate | Recherche calée sur la date de règlement | Le skill cherche autour de **`emitted_at`** (date d'achat réelle — les paiements carte se règlent 1-2 j plus tard) |
| Montant introuvable dans les e-mails | Pourboire, devise étrangère, capture partielle | Tolérance de montant + nouvelle passe marchand seul |
| Pièce jointe d'e-mail non récupérable via le connecteur | Certains connecteurs n'exposent pas le binaire | Le skill donne le lien direct vers l'e-mail → rattachement manuel en un glisser-déposer, annoncé honnêtement |
| L'upload échoue | Flow en 2 temps mal enchaîné | `request_attachment_upload` (ouvre le slot) **puis** `upload_attachment` (pousse le fichier) — géré par le skill |
| Des transactions « polluent » la liste | Pièce non exigée ou encaissement client | `attachment_required: false` et `side: credit` sont exclus d'office du score |

## 🔒 Rappel sécurité

Le skill **ne touche jamais à l'argent** : sa seule écriture ajoute un document à une transaction.
Chaque rattachement est confirmé **individuellement** par toi, sur un match affiché (marchand, montant, date) —
jamais de lot silencieux. Et surtout : **originaux uniquement**. Le skill ne fabrique, ne régénère
et ne « reconstitue » jamais un justificatif — un faux document n'a aucune valeur probante et
t'expose en contrôle fiscal. Sans original : la transaction reste listée, avec une piste pour le retrouver.
