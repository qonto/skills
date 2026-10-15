# 📖 Procédure d'installation et d'utilisation — qonto-chargeback-defender

> Guide pas-à-pas utilisateur. Version jury : `PROCEDURE.en.md`.

---

## 1️⃣ Installation (une seule fois, ~5 min)

### Étape 1 — Connecter le MCP Qonto à Claude
1. Dans **claude.ai** (ou Claude Desktop) : Paramètres → **Connecteurs** → *Parcourir les connecteurs*
2. Chercher **Qonto** → *Ajouter* → le flux de connexion Qonto s'ouvre
3. Se connecter avec son compte Qonto (OAuth — le mot de passe n'est **jamais** partagé avec Claude)
4. Vérifier : demander à Claude « *Liste mes comptes Qonto* » → les comptes s'affichent

### Étape 2 — Installer le skill
- **Claude Code / Claude Desktop** : copier le dossier du skill dans `~/.claude/skills/qonto-chargeback-defender/` (le fichier `SKILL.md` suffit)
- **claude.ai** : joindre le `SKILL.md` au projet, ou coller son contenu dans les instructions du projet

### Étape 3 — Connecter les MCP optionnels (recommandé)
1. **Stripe ou PayPal** : la source autoritaire des litiges — motifs, montants et **deadlines réelles**
2. **Shopify** : commandes, fulfillment, numéros de tracking (la preuve de livraison)
3. **Gmail** : les échanges client (confirmations, réclamations, « bien reçu, merci »)

> ⚠️ Aucun n'est bloquant : sans eux, le skill tourne en **mode Qonto pur** — détection des débits
> de reprise + chronologie + checklist de réponse. Il annonce lui-même ce qu'il a et ce qui lui manque.

## 2️⃣ Usage type (quand un litige tombe, ~10 min)

| # | Action | Résultat |
|---|---|---|
| 1 | Dire à Claude : « **Des litiges de paiement ouverts ?** » | Tableau des litiges triés par urgence : montant, motif, deadline |
| 2 | « **Retrouve le débit correspondant** » | Chronologie : paiement d'origine → payout → reprise → frais |
| 3 | « **Assemble le dossier de défense** » | Checklist de pièces ✅/⚠️, chaque pièce avec sa source, les manquantes avec où les trouver |
| 4 | Confirmer explicitement (« oui, attache le mémo ») | Mémo de synthèse daté attaché au débit de reprise dans Qonto, upload **confirmé** |
| 5 | Copier le brouillon de réponse → **portail Stripe/PayPal** → soumettre **avant la deadline** | La défense est déposée — par toi, et toi seul ✅ |

## 3️⃣ Prompts à copier-coller

- « **Des litiges de paiement ouverts sur mon compte ?** » → détection + tableau d'urgence
- « **Pourquoi Stripe m'a repris 189 € le mois dernier ?** » → reprise identifiée + chronologie *(montant d'exemple inventé)*
- « **Assemble le dossier de défense pour ce litige** » → pièces sourcées + brouillon de réponse
- « **Attache le dossier à la transaction** » → mémo daté joint au débit, confirmé
- « **Quelles pièces me manquent et où les trouver ?** » → checklist des manquantes

## 4️⃣ Formats de sortie

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown : litiges (urgence), chronologie, checklist ✅/⚠️ | **Toujours** — c'est la base |
| **Mémo de défense** | Synthèse datée et sourcée, attachée au débit de reprise dans Qonto | Par litige, avec consentement explicite |
| **Brouillon de réponse** | L'argumentaire structuré comme le formulaire du PSP, prêt à coller | Dès que le motif est connu |

## 5️⃣ Dépannage (erreurs connues et vérifiées)

| Symptôme | Cause | Solution |
|---|---|---|
| `list_transactions` échoue ou réponse vide | `bank_account_id`/`iban` manquant | Le skill appelle toujours `get_organization` d'abord |
| Réponses énormes / tronquées | Pagination trop large | `per_page` ≤ 50 partout, fenêtres de 3 mois |
| Aucun débit de reprise trouvé alors qu'un litige existe | **Stripe compense le litige dans le payout suivant** (pas de ligne séparée) | Le skill signale les payouts anormalement bas et recommande le MCP Stripe |
| Litige rapproché du mauvais paiement | Décalage de règlement carte (1-2 j) | Rapprochement sur `emitted_at`, pas `settled_at` |
| La pièce jointe ne s'affiche pas | Upload non finalisé | Le skill confirme via `list_transaction_attachments` avant d'annoncer le succès ; sinon il réessaie |
| Pas de deadline affichée | Mode Qonto pur (pas de MCP litiges) | Fenêtres types **indicatives** + vérification sur le portail Stripe/PayPal |

## 🔒 Rappel sécurité

Le skill **ne soumet jamais** la défense : il la prépare, et c'est **toi** qui la déposes sur le
portail Stripe/PayPal. Il **ne fabrique jamais** de pièce : le mémo attaché est une synthèse datée
qui **cite** les documents sources — pas un justificatif inventé. Et il n'annonce un upload réussi
qu'après l'avoir **vérifié** sur la transaction.
