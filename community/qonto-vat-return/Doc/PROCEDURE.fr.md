# 📖 Procédure d'installation et d'utilisation — qonto-vat-return

> Guide pas-à-pas utilisateur. Version jury : `PROCEDURE.en.md`.

---

## 1️⃣ Installation (une seule fois, ~5 min)

### Étape 1 — Connecter le MCP Qonto à Claude
1. Dans **claude.ai** (ou Claude Desktop) : Paramètres → **Connecteurs** → *Parcourir les connecteurs*
2. Chercher **Qonto** → *Ajouter* → le flux de connexion Qonto s'ouvre
3. Se connecter avec son compte Qonto (OAuth — le mot de passe n'est **jamais** partagé avec Claude)
4. Vérifier : demander à Claude « *Liste mes comptes Qonto* » → les comptes s'affichent

### Étape 2 — Installer le skill
- **Claude Code / Claude Desktop** : copier le dossier du skill dans `~/.claude/skills/qonto-vat-return/` (le fichier `SKILL.md` suffit)
- **claude.ai** : joindre le `SKILL.md` au projet, ou coller son contenu dans les instructions du projet

### Étape 3 — (Recommandé) Vivre sa facturation dans Qonto
Plus les factures clients et fournisseurs existent dans Qonto (module Facturation), plus le tableau CA3 est
précis : ventilation par taux exacte, matching encaissements ↔ factures fiable, `vat_payment_condition` lisible.
Sans factures, le skill travaille depuis les transactions seules et **annonce ses limites** au lieu de deviner.

## 2️⃣ Utilisation mensuelle (avant l'échéance du 15-24, ~5 min)

| # | Action | Résultat |
|---|---|---|
| 1 | Dire à Claude : « **Prépare ma déclaration de TVA de juin** » | Détection régime + périodicité + fait générateur, annoncée en tête |
| 2 | Lire le tableau **case par case** (case → libellé → montant → justification) | Tu sais exactement d'où vient chaque euro de chaque case |
| 3 | Lire les **contrôles de cohérence** ✅/⚠️ (vs mois passés, vs paiements DGFIP, vs relevés) | Les écarts sont expliqués avant que tu recopies |
| 4 | Faire valider par l'**expert-comptable** (surtout autoliquidation / immobilisations / report de crédit) | Sécurité — le skill le recommande dans chaque rapport |
| 5 | Recopier les cases sur **impots.gouv.fr** (montants arrondis à l'euro fournis) | Déclaration déposée — par toi, pas par le skill |

## 3️⃣ Utilisations ponctuelles

- « **Combien de TVA je vais devoir payer ce mois-ci ?** » → position nette (ligne 28 ou crédit 25/27) + détail
- « **Ma TVA collectée de juin, par taux ?** » → bases et taxes 20 / 10 / 5,5 / 2,1 %
- « **Quels débits n'ont pas d'info TVA ce mois-ci ?** » → liste des débits non renseignés (le plancher expliqué)
- « **Compare ma TVA de ce trimestre aux trimestres précédents** » → historique + écarts commentés
- « **Est-ce que j'ai des achats UE à autoliquider ?** » → transactions candidates signalées, à voir avec le comptable

## 4️⃣ Formats de sortie (où atterrit la déclaration ?)

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableau CA3 case par case + tableau des contrôles ✅/⚠️ | **Toujours** — c'est la base |
| **Dashboard interactif** | Fichier/artifact **HTML** : vue « formulaire », ventilation par taux, historique vs paiements DGFIP | Si l'hôte affiche les fichiers (artifacts claude.ai, Claude Desktop, Claude Code) ; sinon repli automatique sur les tableaux |
| **Rien d'autre** | Aucune télétransmission, aucune écriture Qonto | Jamais — c'est le design |

## 5️⃣ Dépannage (erreurs connues et vérifiées)

| Symptôme | Cause | Solution |
|---|---|---|
| « bank_account_id required » sur `list_transactions` | `get_organization` n'a pas été appelé d'abord | Le skill commence toujours par `get_organization` |
| Réponses tronquées / lentes | Pagination trop large | Le skill pagine `per_page` ≤ 50 partout |
| `403 missing oauth scope` sur `list_cash_flow_categories` | Hors périmètre du connecteur claude.ai | Normal — le skill utilise les labels à la place |
| Collectée fausse alors que les factures sont bonnes | TVA sur les **encaissements** non détectée ailleurs — ici le skill lit `vat_payment_condition` | Vérifier que les factures clients portent bien la mention ; sinon le préciser dans le prompt |
| Un paiement reçu n'apparaît dans aucune case | Encaissement sans facture matchée | Normal : listé dans « encaissements non matchés » — à trancher avec le comptable |
| Le skill refuse de produire une CA3 | Régime simplifié (CA12) détecté, ou société non française | Comportement voulu — hors scope annoncé (et rappel : simplifié supprimé au 01/01/2027) |
| Écart avec le montant du comptable | Débits non renseignés (plancher) ou autoliquidation en attente | Lire le compte des non-renseignés et les transactions signalées « à vérifier » |

## 🔒 Rappel sécurité

Le skill **ne déclare rien et ne peut rien déclarer** : aucun outil d'écriture, aucune télétransmission.
Il lit ton compte, calcule, contrôle, et te tend un tableau. C'est **toi** (ou ton expert-comptable) qui
recopies les cases sur impots.gouv.fr. Chaque rapport recommande la validation par l'expert-comptable —
en particulier pour l'autoliquidation, les immobilisations et le report de crédit.
