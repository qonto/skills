# 📖 Procédure d'installation et d'utilisation — qonto-asset-registry

> Guide pas-à-pas utilisateur. Version jury : `PROCEDURE.en.md`.

---

## 1️⃣ Installation (une seule fois, ~5 min)

### Étape 1 — Connecter le MCP Qonto à Claude
1. Dans **claude.ai** (ou Claude Desktop) : Paramètres → **Connecteurs** → *Parcourir les connecteurs*
2. Chercher **Qonto** → *Ajouter* → le flux de connexion Qonto s'ouvre
3. Se connecter avec son compte Qonto (OAuth — le mot de passe n'est **jamais** partagé avec Claude)
4. Vérifier : demander à Claude « *Liste mes comptes Qonto* » → les comptes s'affichent

### Étape 2 — Installer le skill
- **Claude Code / Claude Desktop** : copier le dossier du skill dans `~/.claude/skills/qonto-asset-registry/` (le fichier `SKILL.md` suffit)
- **claude.ai** : joindre le `SKILL.md` au projet, ou coller son contenu dans les instructions du projet

### Étape 3 — Rien d'autre
Le skill est **100 % lecture** : aucune configuration, aucun sous-compte, aucune permission d'écriture.
Il travaille avec ce que ton compte contient déjà — transactions, factures fournisseurs, pièces jointes.

## 2️⃣ Usage type (le check-up annuel — ou avant de renouveler l'assurance, ~5 min)

| # | Action | Résultat |
|---|---|---|
| 1 | Dire à Claude : « **Quel matériel possède mon entreprise ?** » | Scan 24-36 mois → registre trié par catégorie/valeur, statuts ✅ 💰 ❓ 🔁, colonne 📎 |
| 2 | Passer les lignes « ❓ à confirmer » (marchands généralistes) | Tu confirmes ou reclasses en une phrase — rien n'est deviné |
| 3 | « **Montre les amortissements indicatifs** » | Durée usuelle, dotation annuelle, valeur nette comptable estimée — à valider par l'expert-comptable |
| 4 | « **Génère l'inventaire assurance** » | Tableau prêt à transmettre : description, date, valeur d'achat, justificatif |
| 5 | Pour les 📎 manquants : enchaîner avec `qonto-receipt-hunter` | Les pièces sont récupérées avant d'en avoir besoin |

## 3️⃣ Prompts à copier-coller

- « **Quel matériel possède mon entreprise ? Construis le registre des immobilisations.** »
- « **Utilise un seuil de 800 € au lieu de 500 €.** » (seuil configurable)
- « **Quels équipements n'ont pas de justificatif lié ?** »
- « **Génère l'inventaire assurance, prêt à envoyer à mon assureur.** »
- « **Que vaut encore mon parc informatique aujourd'hui ?** » (valeur nette comptable estimée)
- « **Fais un dashboard HTML du registre.** »
- « **J'ai revendu [tel équipement] : sors-le du registre.** » (les cessions, c'est toi qui les déclares)

## 4️⃣ Formats de sortie (où atterrit le registre ?)

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown : registre, amortissements, résumé (N actifs · valeur totale · jauge justificatifs) | **Toujours** — c'est la base |
| **Dashboard / export** | Fichier/artifact **HTML autoportant** charte Qonto : registre par catégorie, jauge de complétude, total assuré | Si l'hôte affiche les fichiers (artifacts claude.ai, Claude Desktop, Claude Code) ; repli sur les tableaux sinon |
| **Inventaire assurance** | Tableau prêt à transmettre (description, date d'achat, valeur, justificatif) | À la demande — idéalement avant le sinistre |

## 5️⃣ Dépannage (erreurs connues et vérifiées)

| Symptôme | Cause | Solution |
|---|---|---|
| `list_transactions` réclame un compte | L'outil exige `bank_account_id`/`iban` | Le skill appelle `get_organization` d'abord, systématiquement |
| Réponses énormes / scan lent | Pagination insuffisante | `per_page` ≤ 50, fenêtres de 3 mois — géré par le skill |
| Un achat carte introuvable à la date de la facture | Délai de règlement carte (1-2 jours) | Rapprocher par `emitted_at`, pas `settled_at` — géré |
| Le même équipement apparaît 3 fois | Paiement en plusieurs fois | Mensualités rapprochées en **un seul** actif à sa valeur totale |
| Une ligne reste « ❓ à confirmer » | Marchand généraliste, libellé muet | Ouvrir le justificatif (`get_attachment`) ou préciser la nature en une phrase |
| Ligne 📎 justificatif manquant | Pièce jamais jointe à la transaction | Enchaîner avec `qonto-receipt-hunter` pour la récupérer |
| Du matériel en leasing compté dans le total | — | N'arrive pas : mensualités récurrentes chez un financeur → « 🔁 financé, pas immobilisé ici », exclu du total |
| Pas de seuil 500 € proposé | Organisation hors France | Normal — mécanique universelle, mais le seuil et les durées sont la pratique française ; le registre reste complet |

## 🔒 Rappel sécurité

Le skill **n'écrit rien** — c'est sa garantie la plus forte : aucun outil d'écriture n'est appelé,
aucune catégorie modifiée, aucun document envoyé, aucune demande créée. Il lit ton compte,
calcule, et te présente le registre. Le seuil des 500 € et les durées d'amortissement sont des
**usages indicatifs, pas des écritures comptables** : la décision finale appartient à ton
expert-comptable.
