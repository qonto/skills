# 📖 Procédure d'installation et d'utilisation — qonto-subscription-guardian

> Guide pas-à-pas utilisateur. Version jury : `PROCEDURE.en.md`.
> Pour l'audit complet des récurrences (coût annuel, doublons, hausses…) : skill **`qonto-subscription-audit`**.

---

## 1️⃣ Installation (une seule fois, ~5 min)

### Étape 1 — Connecter le MCP Qonto à Claude
1. Dans **claude.ai** (ou Claude Desktop) : Paramètres → **Connecteurs** → *Parcourir les connecteurs*
2. Chercher **Qonto** → *Ajouter* → le flux de connexion Qonto s'ouvre
3. Se connecter avec son compte Qonto (OAuth — le mot de passe n'est **jamais** partagé avec Claude)
4. Vérifier : demander à Claude « *Liste mes comptes Qonto* » → les comptes s'affichent

### Étape 2 — Installer le skill
- **Claude Code / Claude Desktop** : copier le dossier du skill dans `~/.claude/skills/qonto-subscription-guardian/` (le fichier `SKILL.md` suffit)
- **claude.ai** : joindre le `SKILL.md` au projet, ou coller son contenu dans les instructions du projet

> ℹ️ Pour créer des cartes directement, il faut un rôle **Owner/Admin/Manager** sur Qonto.
> Avec un autre rôle : le skill bascule sur `create_card_request` (un admin approuve dans l'app) — et la détection, elle, marche pour tout le monde.

## 2️⃣ Usage type : lister, choisir, plafonner (~5 min)

| # | Action | Résultat |
|---|---|---|
| 1 | Dire à Claude : « **Liste mes abonnements** » | Détection légère sur **24-36 mois** (assez pour les **annuels**) : tableau des candidats — fournisseur, prix, cadence M/T/A, carte payeuse, déjà protégé ou non |
| 2 | Lire le rappel du plan | Comptage `list_cards` + grille : **Basic 2 incluses · Smart/Premium 50 · Essential/Business/Enterprise illimité** — le skill te demande ton plan et propose un nombre de cartes adapté |
| 3 | Choisir les abonnements à protéger | Toi seul décides — jamais de rafale, les cartes `SUB-` existantes ne sont pas reproposées |
| 4 | Confirmer la carte n°1 explicitement | `create_card` virtuelle, plafond mensuel = prix actuel + petite marge (annuel : plafond par transaction) |
| 5 | Sur l'**iPhone** : notification push Qonto → **confirmer (SCA)** | La carte `SUB-<Fournisseur>` existe, plafonnée ✅ — répéter les étapes 4-5 pour chaque abonnement choisi, **une SCA à chaque fois** |
| 6 | Changer le moyen de paiement **chez chaque fournisseur** (étape manuelle) | `get_card_iframe_url` affiche le numéro de carte, pour tes yeux uniquement |

## 3️⃣ Utilisations ponctuelles

- « **Plafonne Adobe** » → une seule carte, même parcours : confirmation explicite + SCA
- « **Quelles cartes SUB- existent déjà ?** » → liste des abonnements déjà protégés (idempotence)
- « **Verrouille la carte SUB-X** » → `change_card_status` lock (réversible) — prévient d'abord des conséquences côté fournisseur
- « **Audite mes abonnements** » (coût annuel, doublons, hausses…) → c'est le skill **`qonto-subscription-audit`**, pas celui-ci

## 4️⃣ Formats de sortie

| Sortie | Format | Quand |
|---|---|---|
| **Liste des candidats** | Tableau markdown : fournisseur · prix · cadence M/T/A · carte payeuse · déjà protégé | Après la détection légère |
| **Récap des cartes créées** | Tableau markdown : carte · plafond · fournisseur · reste à basculer | En fin de session |

## 5️⃣ Dépannage (erreurs connues et vérifiées)

| Symptôme | Cause | Solution |
|---|---|---|
| `403 missing oauth scope` sur `get_subscription` | L'abonnement Qonto lui-même (plan, quotas de cartes) n'est pas lisible via le connecteur claude.ai | Normal — le skill donne la grille publique et te demande ton plan |
| Peur d'être bloqué par le quota de cartes du plan | Les plans Qonto limitent les cartes virtuelles : **Basic = 2 incluses (2 €/mois au-delà) · Smart/Premium = 50 incluses (1 €/carte au-delà) · Essential/Business/Enterprise = illimité** | Le skill compte les cartes existantes (`list_cards`), rappelle cette grille et propose un **nombre de cartes adapté au plan que tu annonces** — jamais de rafale |
| `list_transactions` échoue d'entrée | `bank_account_id`/`iban` manquant | Le skill appelle **toujours** `get_organization` d'abord |
| La création de carte « ne répond pas » | C'est la **SCA** : l'appel bloque tant que la notification push n'est pas confirmée sur l'appareil appairé | Confirmer sur le téléphone — ou refuser, rien n'est créé sans toi |
| Création de carte refusée (rôle) | `create_card` direct exige Owner/Admin/Manager | Repli automatique sur `create_card_request` (un admin approuve dans l'app) |
| La carte créée n'a pas de nom | `create_card` n'a pas de champ nickname | Le skill enchaîne `update_card` → `SUB-<Fournisseur>` juste après |
| Impossible de modifier un plafond via MCP | `update_card` ne gère que le nickname (les options sont réservées aux cartes physiques) | Ajuster le plafond dans l'app Qonto — le skill le dit tel quel |
| Un abonnement connu n'est pas listé | Cadence cassée par `settled_at` (décalage carte 1-2 j), montant trop variable, ou **annuel avec moins de 24 mois d'historique** | Le skill rapproche sur `emitted_at`, tolère ±15 % et balaie 24-36 mois ; en dessous de 24 mois, il prévient que les annuels peuvent passer sous le radar |

## 🔒 Rappel sécurité

Le skill **ne peut pas** dépenser ton argent. Créer une carte est une action **SCA** : l'appel reste bloqué
tant que **toi seul** n'as pas confirmé la notification push sur ton appareil Qonto appairé — et tu peux refuser
en un tap, pour chaque carte. La carte créée est **plafonnée** au montant que tu as validé : c'est précisément sa raison d'être.
Plafonner n'est pas résilier — le contrat avec le fournisseur continue tant que tu ne le résilies pas.
