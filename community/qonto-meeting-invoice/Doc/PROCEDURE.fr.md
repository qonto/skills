# 📖 Procédure d'installation et d'utilisation — qonto-meeting-invoice

> Guide pas-à-pas utilisateur. Version jury : `PROCEDURE.en.md`.

---

## 1️⃣ Installation (une seule fois, ~5 min)

### Étape 1 — Connecter le MCP Qonto à Claude
1. Dans **claude.ai** (ou Claude Desktop) : Paramètres → **Connecteurs** → *Parcourir les connecteurs*
2. Chercher **Qonto** → *Ajouter* → le flux de connexion Qonto s'ouvre
3. Se connecter avec son compte Qonto (OAuth — le mot de passe n'est **jamais** partagé avec Claude)
4. Vérifier : demander à Claude « *Liste mes produits Qonto* » → le catalogue s'affiche

### Étape 2 — Installer le skill
- **Claude Code / Claude Desktop** : copier le dossier du skill dans `~/.claude/skills/qonto-meeting-invoice/` (le fichier `SKILL.md` suffit)
- **claude.ai** : joindre le `SKILL.md` au projet, ou coller son contenu dans les instructions du projet

### Étape 3 — Vérifier la facturation Qonto (recommandé)
1. Dans l'**app Qonto** : Facturation → Paramètres → numérotation, mentions légales, coordonnées de paiement, logo
2. Renseigner le **catalogue produits** (prestations, prix unitaires, taux de TVA) — c'est lui qui fiabilise le rapprochement
3. C'est tout — le skill s'appuie sur ces paramètres, il ne les réinvente pas

> ⚠️ Sans catalogue produits : le skill fonctionne quand même, mais il te demandera chaque prix
> non dit dans le call au lieu de le retrouver tout seul.

## 2️⃣ Utilisation type (après chaque call de vente, ~3 min)

| # | Action | Résultat |
|---|---|---|
| 1 | Coller le transcript : « **Voici le transcript du call, prépare le devis** » | Extraction des termes négociés, chaque ligne citée |
| 2 | Lire l'extraction et la liste d'ambiguïtés (prix « habituel », condition non dite…) | Tu sais ce qui vient du call et ce qui manque |
| 3 | Répondre aux points listés | Le skill crée le devis **en brouillon** dans Qonto |
| 4 | Vérifier le récap ligne à ligne (client, lignes, TVA, totaux, dates) | Le document est exactement ce qui a été négocié |
| 5 | Confirmer explicitement (« **oui, envoie** ») | Qonto envoie le devis par email au prospect ✅ |

## 3️⃣ Utilisations ponctuelles

- « **Fais le devis du call de ce matin** (note Notion "Call Acme") » → récupération via le MCP Notion s'il est connecté
- « **Le client a dit oui — facture-le directement** » → `create_client_invoice` en brouillon, même récap, même confirmation
- « **C'est un nouveau prospect** » → fiche client créée après relecture des coordonnées
- « **Montre-moi les devis en cours pour ce client** » → `list_quotes`, anti-doublon avant d'en créer un autre

## 4️⃣ Formats de sortie

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown : extraction citée, ambiguïtés, récap ligne à ligne | **Toujours** — c'est la base |
| **Brouillon dans Qonto** | Devis ou facture sur le modèle de facturation de l'organisation | Après la levée des ambiguïtés |
| **Email au prospect** | Envoi natif Qonto (`send_quote` / `send_client_invoice`) | **Seulement** après confirmation explicite |

## 5️⃣ Dépannage (erreurs connues et vérifiées)

| Symptôme | Cause | Solution |
|---|---|---|
| Le devis n'apparaît pas dans Qonto | C'est un **brouillon** — il est dans Facturation → Devis, onglet brouillons | Normal : rien n'est envoyé sans ton accord |
| `422` à la création du devis/de la facture | Champ requis manquant (client, date, taux de TVA par ligne) | Le skill collecte tout **avant** de créer — réponds à la liste d'ambiguïtés |
| Client en double | Fiche créée sans vérifier l'existant | Le skill fait `list_clients` d'abord et te montre le match — signale-lui le doublon sinon |
| Le prix du catalogue contredit le call | Divergence réelle (remise négociée ?) | Le skill la signale et te demande de trancher — jamais de choix silencieux |
| Impossible de supprimer une facture de test | Une facture **finalisée** ne se supprime pas | Ne finalise jamais un test : client fictif + brouillon + `delete_client_invoice` / `delete_quote` |
| « Je ne peux pas lire ta note Notion/Drive » | MCP source non connecté | Normal — colle le transcript directement, le skill continue |
| Grosse réponse / liste tronquée | Pagination oubliée | Le skill pagine `per_page` ≤ 50 partout |

## 🔒 Rappel sécurité

Les devis et factures créés via le MCP sont **réels**. Le skill crée toujours un **brouillon**,
te montre le récap ligne à ligne, et n'envoie **que** sur ton « oui » explicite — l'adresse email
du destinataire est confirmée avant. Ce qui n'a pas été dit dans le call n'entre jamais dans le
document : le skill demande, il n'invente pas. Pour les répétitions : client fictif, puis
`delete_quote` / `delete_client_invoice`.
