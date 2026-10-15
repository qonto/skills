# 📖 Procédure d'installation et d'utilisation — qonto-pay-me-now

> Guide pas-à-pas utilisateur. Version jury : `PROCEDURE.en.md`.

---

## 1️⃣ Installation (une seule fois, ~5 min)

### Étape 1 — Connecter le MCP Qonto à Claude
1. Dans **claude.ai** (ou Claude Desktop) : Paramètres → **Connecteurs** → *Parcourir les connecteurs*
2. Chercher **Qonto** → *Ajouter* → le flux de connexion Qonto s'ouvre
3. Se connecter avec son compte Qonto (OAuth — le mot de passe n'est **jamais** partagé avec Claude)
4. Vérifier : demander à Claude « *Liste mes devis Qonto* » → les devis s'affichent

### Étape 2 — Installer le skill
- **Claude Code / Claude Desktop** : copier le dossier du skill dans `~/.claude/skills/qonto-pay-me-now/` (le fichier `SKILL.md` suffit)
- **claude.ai** : joindre le `SKILL.md` au projet, ou coller son contenu dans les instructions du projet

### Étape 3 — Activer les payment links (recommandé)
1. Dans l'**app Qonto** : activer la fonctionnalité **Liens de paiement** (activation unique)
2. C'est tout — si l'API refuse `create_payment_link`, le skill l'explique et continue avec la facture seule

> 💡 **Optionnel** : connecter les MCP **Short.io** (lien court trackable + stats de clics) et **Gmail** (envoi).
> Le skill les détecte tout seul ; sans eux, le lien Qonto brut et le texte à copier suffisent.

## 2️⃣ Utilisation type (le réflexe « devis accepté », ~2 min)

| # | Action | Résultat |
|---|---|---|
| 1 | Dire à Claude : « **Des devis acceptés pas encore facturés ?** » | Devis croisés avec les factures — seuls les jamais facturés remontent |
| 2 | Relire le **brouillon de facture** (lignes, montants, échéance) | Document RÉEL — tu vérifies avant tout envoi |
| 3 | Confirmer explicitement (« oui, envoie ») | Facture envoyée + **payment link** créé (numéro de facture dans la description) |
| 4 | Partager le **lien court** (ou le QR code pour l'imprimé) | Le client paie par carte ou virement, en un clic |
| 5 | À J+2 : « **Qui a cliqué sans payer ?** » | Matrice clics vs encaissements + relance douce proposée |

## 3️⃣ Prompts à copier-coller

- « **Mon devis [numéro] vient d'être accepté — facture-le et fais-moi payer** »
- « **Crée un payment link pour la facture [numéro]** »
- « **Fais-moi un QR code de paiement pour cette facture imprimée** »
- « **Qui a cliqué sur mes liens de paiement sans payer ?** »
- « **Le client de la facture [numéro] a payé par virement ? Vérifie et marque-la payée si oui** »

## 4️⃣ Formats de sortie

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown : pipeline devis → facture → lien, matrice de suivi | **Toujours** — c'est la base |
| **Le payment link (+ lien court)** | URL Qonto + URL courte Short.io, prêtes à partager | À chaque cycle |
| **QR code** | Fichier/artifact image encodant le lien | Si l'hôte affiche les fichiers ; sinon les liens suffisent |
| **Rapport de suivi** | Clics vs encaissements + relances proposées (jamais envoyées seules) | Sur demande / à J+2 |

## 5️⃣ Dépannage (erreurs connues et vérifiées)

| Symptôme | Cause | Solution |
|---|---|---|
| « La doc MCP dit que les payment links ne sont pas supportés » | Doc en retard sur l'API | **Vérifié le 03/07 : `create_payment_link` fonctionne** — le skill l'appelle directement, sans se fier à la doc |
| Erreur à la création du payment link | Fonctionnalité pas activée sur le compte | App Qonto → activer les **Liens de paiement** (une fois) ; en attendant le skill continue avec la facture seule |
| `list_transactions` échoue | `bank_account_id`/`iban` manquant | `get_organization` d'abord — le skill le fait systématiquement |
| Grosses réponses / lenteurs | Pagination trop large | Le skill pagine `per_page` ≤ 50 partout |
| Facture de test à ne pas garder | Les factures MCP sont **RÉELLES** | Répéter sur un client fictif, rester en brouillon, `delete_client_invoice` ensuite |
| Pas de lien court ni de stats | MCP Short.io absent | Normal — le lien Qonto brut marche très bien ; le skill le dit et continue |
| Le client a payé mais la facture reste « unpaid » | Paiement par virement classique, hors lien | Le skill rapproche via `list_transactions` et propose `mark_client_invoice_as_paid` avec la transaction en preuve |

## 🔒 Rappel sécurité

Le skill **ne peut pas** déplacer ton argent. Un payment link est un moyen de **recevoir** un paiement
de ton client — rien à voir avec un virement sortant (impossible via MCP de toute façon : toute demande
de virement exige ta SCA dans l'app Qonto). Les trois seules écritures : une facture (**brouillon d'abord**, envoi seulement après ton OK explicite),
un lien de paiement que tu peux désactiver à tout moment dans l'app, et le marquage « payée » d'une
facture — toujours proposé avec la transaction en preuve, jamais automatique.
