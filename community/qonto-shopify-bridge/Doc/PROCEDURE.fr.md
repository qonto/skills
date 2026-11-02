# 📖 Procédure d'installation et d'utilisation — qonto-shopify-bridge

> Guide pas-à-pas utilisateur. Version jury : `PROCEDURE.en.md`.

---

## 1️⃣ Installation (une seule fois, ~5 min)

### Étape 1 — Connecter le MCP Qonto à Claude
1. Dans **claude.ai** (ou Claude Desktop) : Paramètres → **Connecteurs** → *Parcourir les connecteurs*
2. Chercher **Qonto** → *Ajouter* → le flux de connexion Qonto s'ouvre
3. Se connecter avec son compte Qonto (OAuth — le mot de passe n'est **jamais** partagé avec Claude)
4. Vérifier : demander à Claude « *Liste mes comptes Qonto* » → les comptes s'affichent

### Étape 2 — Connecter le MCP Shopify (recommandé)
1. Même chemin : Connecteurs → chercher **Shopify** → *Ajouter* → login OAuth de la boutique
2. Vérifier : « *Montre-moi mes 3 dernières commandes Shopify* » → les commandes s'affichent
3. Plusieurs boutiques ? Le skill réconcilie boutique par boutique

> ⭕ Cette étape est **optionnelle** : sans MCP Shopify, le skill fonctionne en mode Qonto pur
> (cadence des payouts, totaux, ruptures de rythme) — et te le dit clairement.

### Étape 3 — Installer le skill
- **Claude Code / Claude Desktop** : copier le dossier du skill dans `~/.claude/skills/qonto-shopify-bridge/` (le fichier `SKILL.md` suffit)
- **claude.ai** : joindre le `SKILL.md` au projet, ou coller son contenu dans les instructions du projet

## 2️⃣ Utilisation hebdomadaire (le rituel du lundi matin, ~2 min)

| # | Action | Résultat |
|---|---|---|
| 1 | Dire à Claude : « **Tous mes payouts Shopify sont-ils arrivés la semaine dernière ?** » | Timeline des payouts attendus vs reçus, par PSP |
| 2 | Lire le tableau de réconciliation | « 14 attendus, 13 reçus, 1 en retard de 4 jours » — tu sais où tu en es |
| 3 | S'il manque un payout : lire le **brouillon de ticket support** généré | Date, montant attendu, commandes concernées, référence du relevé — prêt à envoyer |
| 4 | Envoyer le ticket **toi-même** au support Shopify/Stripe | Le skill ne fait que préparer le texte — c'est toi qui agis |

## 3️⃣ Utilisations ponctuelles

- « **Combien Stripe me prend vraiment ?** » → taux effectif calculé payout par payout, comparé au tarif de ton plan (si tu l'indiques)
- « **Quel est mon net encaissé du mois, après commissions ?** » → la vraie marge, pas le brut du dashboard
- « **Rapproche mes ventes Shopify de mon compte sur mars** » → réconciliation complète du mois
- « **Mes remboursements ont-ils bien été répercutés ?** » → contrôle remboursements/chargebacks des deux côtés

## 4️⃣ Formats de sortie

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown (réconciliation, frais, net encaissé, anomalies) | **Toujours** — c'est la base |
| **Dashboard interactif** | Fichier/artifact **HTML** : timeline des payouts (trous en évidence), tendance du taux de frais, barres net/mois | Si l'hôte affiche les fichiers (artifacts claude.ai, Claude Desktop, Claude Code) ; sinon repli sur les tableaux |
| **Brouillon de ticket support** | Texte prêt à envoyer, toutes références incluses | À chaque payout manquant détecté |

## 5️⃣ Dépannage (erreurs connues et vérifiées)

| Symptôme | Cause | Solution |
|---|---|---|
| `list_transactions` échoue d'entrée | `bank_account_id`/`iban` manquant | Le skill appelle **toujours** `get_organization` d'abord |
| Réponses énormes / tronquées | Pagination trop large | `per_page` ≤ 50 partout — géré par le skill |
| `403 missing oauth scope` sur `list_cash_flow_categories` | Hors périmètre du connecteur claude.ai | Normal — le skill se base sur les contreparties et les labels |
| Outils Shopify introuvables | MCP Shopify non connecté, ou graphie confondue : les outils Shopify s'écrivent **avec des tirets** (`get-order`, `list-orders`, `run-analytics-query`) | Connecter le MCP Shopify ; sinon le skill continue en Qonto pur |
| Faux « payout manquant » sur PayPal | Retraits manuels (à la demande), pas de cadence fixe | Le skill reconnaît ce pattern et requalifie la cadence |
| Payout introuvable à la date annoncée par Shopify | Délai bancaire J+2/J+3 ; la date Qonto est `settled_at` | Le skill matche par fenêtre de dates + proximité de montant, pas au jour près |
| Montants qui ne collent jamais | Payouts groupés : *n* commandes − frais − remboursements = 1 versement | C'est le fonctionnement normal — le skill reconstitue le groupe |

## 🔒 Rappel sécurité

Le skill est en **lecture pure** : aucun outil d'écriture, ni côté Qonto ni côté Shopify.
Il ne crée rien, ne modifie rien, ne peut toucher à aucun argent. La seule chose qu'il produit,
c'est de l'information — et un brouillon de ticket que **toi seul** décides d'envoyer.
