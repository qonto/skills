# 📖 Procédure d'installation et d'utilisation — qonto-oss-navigator

> Guide pas-à-pas utilisateur. Version jury : `PROCEDURE.en.md`.

---

## 1️⃣ Installation (une seule fois, ~5 min)

### Étape 1 — Connecter le MCP Qonto à Claude
1. Dans **claude.ai** (ou Claude Desktop) : Paramètres → **Connecteurs** → *Parcourir les connecteurs*
2. Chercher **Qonto** → *Ajouter* → le flux de connexion Qonto s'ouvre
3. Se connecter avec son compte Qonto (OAuth — le mot de passe n'est **jamais** partagé avec Claude)
4. Vérifier : demander à Claude « *Liste mes comptes Qonto* » → les comptes s'affichent

### Étape 2 — Installer le skill
- **Claude Code / Claude Desktop** : copier le dossier du skill dans `~/.claude/skills/qonto-oss-navigator/` (le fichier `SKILL.md` suffit)
- **claude.ai** : joindre le `SKILL.md` au projet, ou coller son contenu dans les instructions du projet

### Étape 3 — Les deux options recommandées
1. **MCP Shopify** (recommandé) : Paramètres → Connecteurs → **Shopify** → *Ajouter*. C'est ce qui donne les **pays de livraison réels** par commande. Sans lui, le skill travaille en mode Qonto pur et annonce une couverture partielle
2. **Sous-compte « impôts »** : dans l'**app Qonto** : Comptes → **Créer un sous-compte**, nommé avec un mot-clé reconnaissable (« Impôts & TVA », « Taxes », « OSS »…). Le skill le détecte par son nom

> ⚠️ Ces deux étapes sont optionnelles : sans Shopify le skill infère (et le dit), sans sous-compte il calcule tout mais ne propose pas de virement.

## 2️⃣ Usage type (le rituel trimestriel, ~5 min)

| # | Action | Résultat |
|---|---|---|
| 1 | Dire à Claude : « **Où j'en suis sur le seuil des 10 000 € ?** » | Jauge : cumul B2C transfrontalier UE de l'année, franchissement daté ou estimé |
| 2 | Dire : « **Prépare mon brouillon OSS du trimestre** » | Tableau pays par pays : base HT · taux · TVA due · total, date limite et portail de dépôt |
| 3 | Lire le détail (mode Shopify ou Qonto pur, millésime des taux, ligne B2B exclue) | Tu sais exactement d'où vient chaque chiffre — et ce qui reste à vérifier |
| 4 | Confirmer explicitement (« oui, crée la demande ») si tu veux provisionner | Demande de virement créée vers le sous-compte impôts, détail dans la note |
| 5 | Sur le **téléphone** : notification push Qonto → ouvrir → vérifier la note → **approuver (SCA)** | Le trimestre est provisionné ✅ |
| 6 | Déposer la déclaration sur **impots.gouv.fr** (guichet unique OSS) avant la date limite | Le skill a préparé — c'est toi qui déclares |

## 3️⃣ Prompts à copier-coller

- « **Où j'en suis sur le seuil des 10 000 € de ventes UE ?** » → la jauge, avec le mode de calcul annoncé
- « **Quelle TVA appliquer à mes clients allemands / espagnols / italiens ?** » → taux du pays du client (table millésimée)
- « **Prépare mon brouillon OSS du trimestre dernier** » → tableau pays par pays prêt à recopier
- « **Provisionne ma TVA OSS** » → demande de virement (après ta confirmation explicite)
- « **Montre-moi mes ventes B2B intracom** » → les flux exclus de l'OSS (autoliquidation), listés à part

## 4️⃣ Formats de sortie (où atterrit le brouillon ?)

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown (jauge, brouillon pays par pays, flux exclus) | **Toujours** — c'est la base |
| **Dashboard interactif** | Fichier/artifact **HTML** : barre de jauge, tableau par pays, frise des trimestres | Si l'hôte affiche les fichiers (artifacts claude.ai, Claude Desktop, Claude Code) ; sinon repli automatique sur les tableaux |
| **Note de la demande Qonto** | Détail pays par pays joint à la demande, **visible au moment de l'approbation SCA** | À chaque provision créée |

## 5️⃣ Dépannage (erreurs connues et vérifiées)

| Symptôme | Cause | Solution |
|---|---|---|
| `list_transactions` échoue d'entrée | `bank_account_id`/`iban` manquant | Le skill appelle **toujours** `get_organization` d'abord |
| Réponses énormes / tronquées | Pagination trop large | `per_page` ≤ 50 partout, scan par fenêtres |
| `403 missing oauth scope` sur `list_cash_flow_categories` | Hors périmètre du connecteur claude.ai | Normal — le skill utilise les labels à la place |
| `422` à la création de la demande de virement | Champ `credit_account_currency` manquant (non documenté) | Le skill l'envoie systématiquement |
| Refus d'une demande de test impossible | `decline_request` exige `request_type: "multi_transfers"` (au pluriel) | Géré par le skill |
| Outils Shopify introuvables | Les noms utilisent des **tirets** : `list-orders`, `run-analytics-query` | Géré par le skill ; vérifier que le MCP Shopify est bien connecté |
| Jauge plus basse qu'attendu | Mode Qonto pur : les payouts PSP agrègent les commandes et masquent le pays | Couverture annoncée comme partielle (plancher) — connecter Shopify ou fournir un export de commandes |
| Le sous-compte n'est pas détecté | Nom sans mot-clé (taxe/tax/impôt/TVA/OSS) | Renommer le sous-compte dans l'app |

## 🔒 Rappel sécurité

Le skill **ne peut pas** déplacer d'argent ni déposer de déclaration. Il prépare : une jauge, un brouillon,
et au plus une *demande* de virement que **toi seul** peux approuver avec ta 2FA dans l'app Qonto.
Tu peux la refuser en un tap. La table des taux porte son millésime — vérifie-la avant tout dépôt,
et fais valider la déclaration par ton expert-comptable.
