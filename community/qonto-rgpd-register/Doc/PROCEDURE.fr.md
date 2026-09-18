# 📖 Procédure d'installation et d'utilisation — qonto-rgpd-register

> Guide pas-à-pas utilisateur. Version jury : `PROCEDURE.en.md`.

---

## 1️⃣ Installation (une seule fois, ~5 min)

### Étape 1 — Connecter le MCP Qonto à Claude
1. Dans **claude.ai** (ou Claude Desktop) : Paramètres → **Connecteurs** → *Parcourir les connecteurs*
2. Chercher **Qonto** → *Ajouter* → le flux de connexion Qonto s'ouvre
3. Se connecter avec son compte Qonto (OAuth — le mot de passe n'est **jamais** partagé avec Claude)
4. Vérifier : demander à Claude « *Liste mes comptes Qonto* » → les comptes s'affichent

### Étape 2 — Installer le skill
- **Claude Code / Claude Desktop** : copier le dossier du skill dans `~/.claude/skills/qonto-rgpd-register/` (le fichier `SKILL.md` suffit)
- **claude.ai** : joindre le `SKILL.md` au projet, ou coller son contenu dans les instructions du projet

### Étape 3 — Rien d'autre à configurer
Pas de sous-compte, pas de clé API, pas de MCP supplémentaire : le skill est **100 % lecture** sur le seul MCP Qonto.
Prévois juste le bon relais humain : le registre produit est un **projet**, à faire valider par ton DPO ou ton juriste.

## 2️⃣ Usage type (le grand scan, ~5 min)

| # | Action | Résultat |
|---|---|---|
| 1 | Dire à Claude : « **Génère mon registre RGPD depuis mes dépenses** » | Scan 12-24 mois de débits + factures fournisseurs, sous-traitants détectés |
| 2 | Lire le tableau de synthèse (outil · catégorie · finalité · UE/hors-UE · drapeaux) | Tu découvres qui traite réellement tes données — souvent des surprises |
| 3 | Parcourir les fiches art. 30 (une par traitement, tags « à valider » visibles) | Le registre existe — pré-rempli, plus une page blanche |
| 4 | Traiter la to-do priorisée : DPA d'abord, transferts hors UE ensuite, outils fantômes enfin | Chaque drapeau devient une action concrète |
| 5 | Transmettre le document HTML au DPO/juriste pour validation | Registre validé, bases légales et durées fixées par un humain ✅ |

## 3️⃣ Prompts à copier-coller

- « **Génère mon registre RGPD depuis mes dépenses** » → le flux complet, synthèse + fiches + to-do
- « **Quels sous-traitants traitent des données personnelles chez moi ?** » → le tableau de synthèse seul
- « **Lesquels de mes outils envoient des données hors UE ?** » → focus drapeaux 🔴 transferts
- « **Quels DPA dois-je vérifier ou signer ?** » → la to-do 🟠, fournisseur par fournisseur
- « **Quels outils ont disparu de mes débits depuis 6 mois ?** » → les candidats à sortir du registre
- « **Regénère le registre et compare avec la dernière fois** » → entrants / sortants depuis le dernier scan

## 4️⃣ Formats de sortie (où atterrit le registre ?)

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown : synthèse, fiche par traitement, to-do priorisée | **Toujours** — c'est la base |
| **Registre imprimable** | Fichier/artifact **HTML** : en-tête responsable, fiches art. 30, annexe sous-traitants, to-do | Si l'hôte affiche les fichiers (artifacts claude.ai, Claude Desktop, Claude Code) ; sinon repli automatique sur les tableaux |
| **Bandeau disclaimer** | « Projet de registre, pas un avis juridique — à valider (DPO/juriste) » | Sur **chaque** sortie, sans exception |

## 5️⃣ Dépannage (erreurs connues et vérifiées)

| Symptôme | Cause | Solution |
|---|---|---|
| `list_transactions` échoue d'entrée | `bank_account_id`/`iban` manquant | Le skill appelle **toujours** `get_organization` d'abord |
| Réponses énormes / tronquées | Pagination trop large | `per_page` ≤ 50, fenêtres de 3 mois — géré par le skill |
| `403 missing oauth scope` sur `list_cash_flow_categories` | Hors périmètre du connecteur claude.ai | Sans impact — le skill n'en a pas besoin (labels en repli si utile) |
| Le même outil apparaît en double | Graphies multiples du même fournisseur (`GOOGLE *WORKSPACE` vs `Google Ireland`) | Normalisation + fusion automatiques ; signale un doublon restant |
| Un outil connu n'est pas détecté | Payé via revendeur, marketplace ou app store — le libellé masque l'éditeur | Le skill le signale 🟡 et **demande** quel produit se cache derrière |
| Libellé carte incompréhensible | Libellés carte plus sales que les factures | Croisement avec `list_supplier_invoices` ; sinon « non identifié — vérifier la facture » |
| Date « dernière utilisation » décalée | Délai de règlement carte (1-2 j) | Le skill lit `emitted_at`, pas `settled_at` |

## 🔒 Rappel sécurité

Le skill est **100 % lecture** : quatre outils de lecture, aucun outil d'écriture. Rien ne bouge sur le compte,
aucun fournisseur n'est contacté, rien n'est envoyé. Et le document produit est un **projet de registre**,
pas un avis juridique : la qualification des rôles, les bases légales et les durées de conservation
sont validées par ton DPO ou ton juriste — le skill le rappelle sur chaque sortie.
