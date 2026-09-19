# 📖 Procédure d'installation et d'utilisation — qonto-counterparty-watch

> Guide pas-à-pas utilisateur. Version jury : `PROCEDURE.en.md`.

---

## 1️⃣ Installation (une seule fois, ~5 min)

### Étape 1 — Connecter le MCP Qonto à Claude
1. Dans **claude.ai** (ou Claude Desktop) : Paramètres → **Connecteurs** → *Parcourir les connecteurs*
2. Chercher **Qonto** → *Ajouter* → le flux de connexion Qonto s'ouvre
3. Se connecter avec son compte Qonto (OAuth — le mot de passe n'est **jamais** partagé avec Claude)
4. Vérifier : demander à Claude « *Liste mes comptes Qonto* » → les comptes s'affichent

### Étape 2 — Connecter le MCP Datagouv (recommandé)
1. Même chemin : Connecteurs → chercher **Datagouv** (data.gouv.fr) → *Ajouter*
2. C'est lui qui active la **santé légale** (SIRENE + BODACC)
3. Sans lui : le skill le dit et livre le scoring Qonto pur (encours + retards) — déjà actionnable

### Étape 3 — Installer le skill
- **Claude Code / Claude Desktop** : copier le dossier du skill dans `~/.claude/skills/qonto-counterparty-watch/` (le fichier `SKILL.md` suffit)
- **claude.ai** : joindre le `SKILL.md` au projet, ou coller son contenu dans les instructions du projet

> 💡 Bonus fiabilité : renseigner le **numéro de TVA** (`tax_identification_number`) sur les fiches clients Qonto —
> le skill en extrait le SIREN et la vérification légale devient certaine au lieu d'un match par nom.

## 2️⃣ Utilisation hebdomadaire (le rituel du lundi matin, ~3 min)

| # | Action | Résultat |
|---|---|---|
| 1 | Dire à Claude : « **Classe mes clients et fournisseurs par risque** » | Inventaire des tiers + tableau de risque trié 🟢🟡🔴 |
| 2 | Lire les alertes prioritaires (croisement encours × BODACC) | Tu sais qui relancer **cette semaine**, et pourquoi |
| 3 | Vérifier la note de couverture (vérifiés / non vérifiables) | Tu sais ce qui a vraiment été contrôlé, et quand |
| 4 | Cas 🔴 avec procédure : confirmer sur bodacc.fr → relance en recommandé, déclaration de créance si besoin | La facture a une chance d'être sauvée ✅ |

## 3️⃣ Utilisations ponctuelles

- « **Mon client X est-il en redressement ?** » → vérification SIRENE + BODACC datée, avec l'encours en face
- « **Qui me doit de l'argent et depuis combien de temps ?** » → impayés par tranches d'ancienneté (0-30 / 31-60 / 61-90 / 90+)
- « **Quels clients paient de plus en plus tard ?** » → tendances de retard par client (réel vs `due_date`)
- « **De quels fournisseurs suis-je le plus dépendant ?** » → dépense annualisée + santé légale de chacun

## 4️⃣ Formats de sortie (où atterrit le tableau de risque ?)

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown (risque trié, alertes, couverture) | **Toujours** — c'est la base |
| **Dashboard interactif** | Fichier/artifact **HTML** : matrice encours × santé, ancienneté, cartes d'alerte | Si l'hôte affiche les fichiers (artifacts claude.ai, Claude Desktop, Claude Code) ; sinon repli automatique sur les tableaux |
| **Note de couverture** | Compteurs vérifiés / non vérifiables / registre indisponible | À chaque rapport |

## 5️⃣ Dépannage (erreurs connues et vérifiées)

| Symptôme | Cause | Solution |
|---|---|---|
| `list_transactions` échoue d'entrée | `bank_account_id`/`iban` manquant | Normal — le skill appelle **toujours** `get_organization` d'abord |
| Réponses énormes / tronquées | Pagination trop large | Le skill pagine `per_page` ≤ 50 partout |
| Un même tiers apparaît en double | Libellé bancaire ≠ nom de la fiche client (mentions SEPA, suffixes) | La normalisation fusionne ; sinon, aligner le nom de la fiche client Qonto |
| Tiers « non vérifiable » | Pas de SIREN (fiche client sans n° TVA) ou pas de correspondance registre | Renseigner le n° de TVA sur la fiche client Qonto → SIREN extrait |
| Santé légale absente du rapport | MCP Datagouv non connecté | Le skill l'annonce et continue en Qonto pur ; connecter Datagouv (étape 2) |
| Procédure connue mais introuvable | Couverture BODACC via data.gouv partielle | Le skill l'assume : « rien trouvé » ≠ « garanti sain » ; confirmer sur bodacc.fr |

## 🔒 Rappel sécurité

Le skill est **100 % lecture** : il n'appelle aucun outil d'écriture Qonto, ne crée rien, n'envoie rien.
Il n'y a rien à approuver — le pire qu'il puisse faire est de te dire une vérité désagréable sur un client.
Les alertes légales sont des **signaux**, pas un conseil juridique : pour une procédure ouverte, confirme
sur bodacc.fr et parles-en à ton avocat ou expert-comptable avant d'agir.
