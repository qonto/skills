# 📖 Procédure d'installation et d'utilisation — qonto-injonction

> Guide pas-à-pas utilisateur. Version jury : `PROCEDURE.en.md`.

---

## 1️⃣ Installation (une seule fois, ~5 min)

### Étape 1 — Connecter le MCP Qonto à Claude
1. Dans **claude.ai** (ou Claude Desktop) : Paramètres → **Connecteurs** → *Parcourir les connecteurs*
2. Chercher **Qonto** → *Ajouter* → le flux de connexion Qonto s'ouvre
3. Se connecter avec son compte Qonto (OAuth — le mot de passe n'est **jamais** partagé avec Claude)
4. Vérifier : demander à Claude « *Liste mes factures clients impayées* » → les factures s'affichent

### Étape 2 — Installer le skill
- **Claude Code / Claude Desktop** : copier le dossier du skill dans `~/.claude/skills/qonto-injonction/` (le fichier `SKILL.md` suffit)
- **claude.ai** : joindre le `SKILL.md` au projet, ou coller son contenu dans les instructions du projet

### Étape 3 — Rien d'autre à configurer
Les deux APIs publiques (BODACC, recherche-entreprises.api.gouv.fr) sont **sans clé et sans compte**.
Seule condition : que l'hôte Claude puisse accéder au web. Sinon, le skill demande les deux infos
manquantes (siège du débiteur, procédure collective connue) au lieu de deviner.

> 💡 Avant l'injonction, la relance amiable : c'est le rôle de `qonto-invoice-chaser` (relances graduées
> jusqu'à la mise en demeure). L'injonction vient **après** — le skill te le rappelle si le dossier semble prématuré.

## 2️⃣ Usage type (du constat d'échec au dossier signé, ~10 min)

| # | Action | Résultat |
|---|---|---|
| 1 | Dire à Claude : « **Cette facture ne sera jamais payée, prépare l'injonction de payer** » | Le skill cible la facture, vérifie l'identité du débiteur (SIREN confirmé avec toi) |
| 2 | Laisser tourner la preuve du non-paiement | Scan des encaissements depuis l'émission : rien ne matche (ou acomptes détectés et déduits) |
| 3 | Lire le résultat BODACC | « Aucune procédure collective au JJ/MM » → injonction OK · Procédure trouvée → bascule en déclaration de créance (délai 2 mois) |
| 4 | Vérifier le calcul (principal, intérêts, 40 €) | Tableau détaillé, formule et taux du semestre affichés — **calcul indicatif à faire valider** |
| 5 | Récupérer le dossier | CERFA 12946 pré-rempli champ par champ + bordereau P1-P6 (justificatifs Qonto récupérés, manquants listés) |
| 6 | **Toi** : signer, puis déposer sur infogreffe.fr (~35 €, PDF < 2 Mo) | La suite est expliquée : ordonnance → signification (6 mois) → opposition (1 mois) |

## 3️⃣ Prompts à copier-coller

- « **Prépare une injonction de payer pour la facture INV-2026-017** » → dossier complet
- « **Mon débiteur est-il en procédure collective ?** » → vérification BODACC seule
- « **Calcule les intérêts de retard sur cette facture** » → calcul détaillé (art. L441-10)
- « **Quel tribunal est compétent pour ce client ?** » → greffe identifié depuis le siège
- « **Ce client a déposé le bilan, qu'est-ce que je fais ?** » → déclaration de créance rédigée, délai 2 mois rappelé

## 4️⃣ Formats de sortie

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown : créance chiffrée, pré-remplissage CERFA champ→valeur, bordereau ✅/📋, bandeau de route | **Toujours** — c'est la base |
| **Dossier imprimable** | Fichier/artifact **HTML** : page de garde, calcul, CERFA pré-rempli, bordereau — à enregistrer en PDF | Si l'hôte affiche les fichiers ; sinon repli automatique sur les tableaux |
| **Pièces du bordereau** | Justificatifs récupérés depuis Qonto (`get_attachment`) + liste « à fournir » | À chaque dossier |

## 5️⃣ Dépannage (erreurs connues et vérifiées)

| Symptôme | Cause | Solution |
|---|---|---|
| `list_transactions` échoue d'entrée | `bank_account_id`/`iban` manquant | Normal — le skill appelle toujours `get_organization` d'abord |
| Réponses tronquées / lenteur | Pagination trop large | Le skill pagine `per_page` ≤ 50 partout |
| Le débiteur n'a pas de SIREN dans Qonto | Fiche client incomplète | Recherche par nom + ville sur l'API registre — **toi** confirmes le bon match (homonymes) |
| BODACC ne renvoie rien pour un débiteur pourtant en difficulté | Recherche par nom (bruit) au lieu du SIREN | Le skill cherche toujours par SIREN ; la date de la vérification est affichée |
| Justificatif introuvable via `get_attachment` | Pièce jamais uploadée dans Qonto | Listée « 📋 à fournir » dans le bordereau — jamais inventée |
| Pas d'accès web depuis l'hôte | APIs publiques injoignables | Le skill le dit et te demande les 2 infos (siège, procédure connue) |

## 🔒 Rappel sécurité

Ce skill n'utilise **aucun outil d'écriture** : il ne dépose rien, ne signifie rien, ne signe rien.
Il assemble un dossier **prêt à signer** — le dépôt sur Infogreffe, c'est toi, avec ta signature.
Les montants d'intérêts sont un **calcul indicatif** : fais-les valider (avocat, commissaire de
justice ou greffe) avant le dépôt. Ce n'est pas un avis juridique.
