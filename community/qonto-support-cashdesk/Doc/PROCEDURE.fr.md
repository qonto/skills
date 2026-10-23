# 📖 Procédure d'installation et d'utilisation — qonto-support-cashdesk

> Guide pas-à-pas utilisateur. Version jury : `PROCEDURE.en.md`.

---

## 1️⃣ Installation (une seule fois, ~5 min)

### Étape 1 — Connecter le MCP Qonto à Claude
1. Dans **claude.ai** (ou Claude Desktop) : Paramètres → **Connecteurs** → *Parcourir les connecteurs*
2. Chercher **Qonto** → *Ajouter* → le flux de connexion Qonto s'ouvre
3. Se connecter avec son compte Qonto (OAuth — le mot de passe n'est **jamais** partagé avec Claude)
4. Vérifier : demander à Claude « *Liste mes clients Qonto* » → les clients s'affichent

### Étape 2 — Installer le skill
- **Claude Code / Claude Desktop** : copier le dossier du skill dans `~/.claude/skills/qonto-support-cashdesk/` (le fichier `SKILL.md` suffit)
- **claude.ai** : joindre le `SKILL.md` au projet, ou coller son contenu dans les instructions du projet

### Étape 3 — Connecteurs optionnels (détectés automatiquement)
- **Intercom** : pour lire les conversations support directement — sinon tu colles la conversation dans le chat, mêmes vérifications
- **Gmail** : pour créer la réponse client en **brouillon** (le skill n'envoie jamais) — sinon la réponse est fournie en texte à copier-coller

> ℹ️ Le cœur du skill fonctionne en Qonto pur : aucun connecteur optionnel n'est requis.

## 2️⃣ Usage type (une réclamation facturation, ~2 min)

| # | Action | Résultat |
|---|---|---|
| 1 | Coller la conversation client (ou : « traite le ticket Intercom de [client] ») | Demande, identité et montants extraits |
| 2 | Confirmer le client proposé (« oui, c'est bien lui ») | Match verrouillé — aucune action avant |
| 3 | Lire le diagnostic : preuve citée (statuts, dates, crédits) | Tu sais exactement ce qui s'est passé |
| 4 | Confirmer l'action proposée (« oui, renvoie » / « oui, crée l'avoir ») | Facture renvoyée, nouveau lien ou avoir créé dans Qonto |
| 5 | Relire le brouillon de réponse, l'ajuster, l'envoyer toi-même | Le client reçoit une réponse factuelle avec la correction jointe |

## 3️⃣ Prompts à copier-coller

- « **Un client me dit qu'il n'a jamais reçu la facture INV-2026-042. Voici son message : […]** » → vérification + renvoi proposé
- « **Ce client dit que son lien de paiement a expiré : […]** » → statut réel du lien + nouveau lien si besoin
- « **Une cliente affirme avoir été débitée deux fois. Voici la conversation : […]** » → recherche des deux crédits, preuve ou infirmation
- « **Traite cette conversation support : […]** » → le skill identifie le guichet tout seul

*(Exemples inventés — INV-2026-042 est un numéro fictif.)*

## 4️⃣ Formats de sortie

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Diagnostic + preuve citée + tableau récap (demande → preuve → action → statut) | **Toujours** — c'est la base |
| **Brouillon de réponse client** | Texte prêt à relire ; brouillon **Gmail** si le MCP est présent (jamais envoyé par le skill) | À chaque conversation traitée |
| **Documents Qonto** | Facture renvoyée · lien de paiement · avoir (document comptable numéroté) | Selon le cas, après confirmation |

## 5️⃣ Dépannage (erreurs connues et vérifiées)

| Symptôme | Cause | Solution |
|---|---|---|
| `list_transactions` échoue | `bank_account_id`/`iban` manquant | Le skill appelle `get_organization` d'abord — toujours |
| Client introuvable par email | Email absent ou différent sur la fiche client | Le skill bascule sur nom/société normalisés et te montre les candidats |
| Le paiement du client n'apparaît pas à la date qu'il annonce | Délai de règlement carte (1-2 j) | Le skill matche sur `emitted_at`, pas `settled_at` |
| Doute sur les liens de paiement via MCP | La doc MCP les dit non supportés | Vérifié : `list_payment_links` / `get_payment_link` / `create_payment_link` fonctionnent |
| Réponses très longues / tronquées | Pagination oubliée | `per_page` ≤ 50 partout, fenêtres de dates autour de la facture |
| Une facture de test traîne dans le compte | Les factures créées via MCP sont **réelles** | Répéter sur un client fictif, statut draft, puis `delete_client_invoice` / `delete_client` |

## 🔒 Rappel sécurité

Le skill **ne déplace jamais d'argent** et **n'envoie jamais** de message au client. Chaque écriture
(renvoi de facture, lien, avoir) exige ta confirmation explicite. L'avoir est un **document comptable
réel** : il n'est proposé que si le double encaissement est prouvé par deux crédits datés, cités
devant toi. Le remboursement éventuel reste un virement que **toi seul** fais dans l'app Qonto (SCA).
