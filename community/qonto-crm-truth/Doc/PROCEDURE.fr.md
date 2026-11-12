# 📖 Procédure d'installation et d'utilisation — qonto-crm-truth

> Guide pas-à-pas utilisateur. Version jury : `PROCEDURE.en.md`.

---

## 1️⃣ Installation (une seule fois, ~5 min)

### Étape 1 — Connecter le MCP Qonto à Claude
1. Dans **claude.ai** (ou Claude Desktop) : Paramètres → **Connecteurs** → *Parcourir les connecteurs*
2. Chercher **Qonto** → *Ajouter* → le flux de connexion Qonto s'ouvre
3. Se connecter avec son compte Qonto (OAuth — le mot de passe n'est **jamais** partagé avec Claude)
4. Vérifier : demander à Claude « *Liste mes comptes Qonto* » → les comptes s'affichent

### Étape 2 — Connecter le CRM (HubSpot ou Airtable)
1. Même chemin : Paramètres → **Connecteurs** → chercher **HubSpot** ou **Airtable** → *Ajouter* (OAuth)
2. Vérifier : « *Liste mes bases Airtable* » (ou « *mes sociétés HubSpot* ») → le CRM répond
3. **Sans CRM connecté** : le skill fonctionne quand même, en mode rapport (clients Qonto scorés dans la conversation) — il ne propose simplement pas d'écriture

### Étape 3 — Installer le skill
- **Claude Code / Claude Desktop** : copier le dossier du skill dans `~/.claude/skills/qonto-crm-truth/` (le fichier `SKILL.md` suffit)
- **claude.ai** : joindre le `SKILL.md` au projet, ou coller son contenu dans les instructions du projet

## 2️⃣ Usage type (la revue de pipeline, ~5 min)

| # | Action | Résultat |
|---|---|---|
| 1 | Dire à Claude : « **Quels deals gagnés n'ont jamais été encaissés ?** » | Lecture banque (24 mois) + lecture CRM |
| 2 | **Vérifier le tableau de correspondance** fiche CRM ↔ client Qonto (🟢 exact · 🟡 probable · 🔴 ambigu) et le confirmer / corriger | Le matching est verrouillé — jamais silencieux |
| 3 | Lire le rapport : deals « won » non encaissés, CA réel, LTV, délais constatés, scores A/B/C | Tu sais qui paie vraiment, et quand |
| 4 | Dire « **oui, écris-le dans le CRM** » après l'aperçu champ par champ | Colonnes Airtable / propriétés HubSpot remplies ✅ |
| 5 | Ouvrir le CRM : trier par « Score payeur » | Les commerciaux priorisent les clients qui paient |

## 3️⃣ Utilisations ponctuelles

- « **Mon top client CRM est-il vraiment mon top payeur ?** » → classement CRM vs classement banque
- « **Score mes clients Qonto** » (sans CRM) → rapport scoré dans la conversation
- « **Quel est le délai de paiement moyen de [client] ?** » → J+X constaté, médiane et moyenne
- « **Quels clients se dégradent ?** » → derniers encaissements anciens, retards qui s'allongent
- Enchaîner : « **Relance les impayés trouvés** » → passe la main à `qonto-invoice-chaser`

## 4️⃣ Formats de sortie (où atterrit la vérité ?)

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown : clients scorés, deals non encaissés, correspondances, bilan d'écriture | **Toujours** — c'est la base |
| **Écriture CRM** | Propriétés custom HubSpot / colonnes Airtable — champs dédiés au skill, jamais les champs natifs | Après matching confirmé + go explicite |
| **One-pager HTML** | Classement CRM vs banque, distribution des scores | Si l'hôte affiche les fichiers ; sinon repli sur les tableaux |

## 5️⃣ Dépannage (erreurs connues et vérifiées)

| Symptôme | Cause | Solution |
|---|---|---|
| `list_transactions` échoue d'entrée | `bank_account_id`/`iban` manquant | Normal — le skill appelle `get_organization` d'abord |
| Réponses énormes / tronquées | Pagination trop large | Le skill pagine `per_page` ≤ 50 partout |
| Filtre Airtable qui ne matche rien (champ *select*) | IDs de choix requis, pas les libellés | Le skill appelle `get_table_schema` avant de filtrer |
| `create_field` refusé sur Airtable | Droits insuffisants sur la base (creator requis) | Donner les droits, ou laisser le skill proposer des colonnes existantes |
| Le même client apparaît en double | Graphies multiples (casse, accents, SARL/SAS…) | Normalisées et fusionnées — visible dans le tableau de correspondance |
| Une fiche CRM reste « non matchée » | Aucune clé fiable (nom/email/SIREN) | Le skill demande — il n'écrit jamais sur un match non confirmé |
| Pas de CRM détecté | HubSpot/Airtable non connecté | Mode dégradé annoncé : rapport scoré dans la conversation |

## 🔒 Rappel sécurité

Côté **Qonto**, le skill ne fait que **lire** — zéro écriture bancaire, il ne peut pas toucher à l'argent.
Les seules écritures visent le **CRM**, et uniquement après deux verrous : le tableau de correspondance
que **tu** confirmes, puis l'aperçu exact de chaque valeur que **tu** approuves. Les scores décrivent le
comportement de paiement observé sur ce compte — pas une solvabilité générale.
