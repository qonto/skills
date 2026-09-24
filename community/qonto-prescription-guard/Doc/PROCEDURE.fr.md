# 📖 Procédure d'installation et d'utilisation — qonto-prescription-guard

> Guide pas-à-pas utilisateur. Version jury : `PROCEDURE.en.md`.
> ⚖️ Rappel : le skill n'est **pas un avis juridique** — il alerte, un juriste valide.

---

## 1️⃣ Installation (une seule fois, ~5 min)

### Étape 1 — Connecter le MCP Qonto à Claude
1. Dans **claude.ai** (ou Claude Desktop) : Paramètres → **Connecteurs** → *Parcourir les connecteurs*
2. Chercher **Qonto** → *Ajouter* → le flux de connexion Qonto s'ouvre
3. Se connecter avec son compte Qonto (OAuth — le mot de passe n'est **jamais** partagé avec Claude)
4. Vérifier : demander à Claude « *Liste mes comptes Qonto* » → les comptes s'affichent

### Étape 2 — Installer le skill
- **Claude Code / Claude Desktop** : copier le dossier du skill dans `~/.claude/skills/qonto-prescription-guard/` (le fichier `SKILL.md` suffit)
- **claude.ai** : joindre le `SKILL.md` au projet, ou coller son contenu dans les instructions du projet

### Étape 3 — Renseigner les fiches clients (recommandé)
1. Dans l'**app Qonto** : Facturation → Clients → ouvrir chaque fiche
2. Renseigner le **SIREN/SIRET ou le n° de TVA** des clients professionnels
3. C'est tout — le skill qualifiera automatiquement B2B (5 ans) vs B2C (2 ans) ; sans identifiant, il **posera la question** au lieu de deviner

> ℹ️ Aucun sous-compte, aucune autorisation d'écriture à prévoir : le skill est **100 % lecture**.
> Il n'y a littéralement rien à approuver.

## 2️⃣ Utilisation trimestrielle (le rituel, ~5 min)

| # | Action | Résultat |
|---|---|---|
| 1 | Dire à Claude : « **Quelles factures impayées risquent la prescription ?** » | Scan complet, échéancier « agir avant le… » trié urgence × montant |
| 2 | Répondre aux questions B2B/B2C sur les clients ambigus | Délais affinés (5 ans vs 2 ans) — les deux dates affichées tant que c'est ambigu |
| 3 | Déclarer les actes que la banque ne voit pas (reconnaissance écrite, injonction déjà lancée) | Compteurs réinitialisés aux bonnes dates, lignes taguées « déclaré » |
| 4 | Lire les alertes 🔴 et les réinitialisations détectées | Tu sais quoi relancer, quoi confier au commissaire de justice, et avant quand |

## 3️⃣ Utilisations ponctuelles

- « **Cette facture de 2023 est-elle encore récupérable ?** » → analyse de la créance, actes interruptifs cherchés dans les transactions
- « **Combien d'euros deviennent irrécouvrables dans les 12 mois ?** » → totaux à risque par horizon
- « **Ce client m'a fait un petit virement en mars — ça change quoi ?** » → recalcul : paiement partiel = délai probablement réinitialisé
- « **Montre-moi la timeline de mes créances** » → timeline HTML (si l'hôte affiche les fichiers)

## 4️⃣ Formats de sortie

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown : échéancier « agir avant le… », totaux à risque, réinitialisations détectées | **Toujours** — c'est la base |
| **Timeline interactive** | Fichier/artifact **HTML** : une barre par créance, marqueur « aujourd'hui », couleur par urgence | Si l'hôte affiche les fichiers ; sinon repli automatique sur les tableaux |
| **Liste « probablement prescrites »** | Section séparée, jamais mélangée aux créances vivantes | À chaque scan |

## 5️⃣ Dépannage (erreurs connues et vérifiées)

| Symptôme | Cause | Solution |
|---|---|---|
| Erreur sur `list_transactions` | L'outil exige `bank_account_id`/`iban` | Le skill appelle toujours `get_organization` d'abord — normal |
| Réponses énormes / lenteur | Pagination trop large | Le skill pagine `per_page` ≤ 50 et fenêtre l'historique par trimestres |
| Client jamais qualifié B2B | Fiche sans SIREN ni n° de TVA | Répondre à la question du skill, et renseigner la fiche dans l'app pour la prochaine fois |
| Paiement partiel non détecté | Encaissé hors Qonto (autre banque, espèces) | Le déclarer au skill — l'heuristique ne voit que le compte Qonto |
| Facture payée mais listée impayée | Statut non mis à jour dans Qonto | La marquer payée dans l'app ; le skill la signale mais ne modifie rien (100 % lecture) |
| Dates légales absentes du rapport | Organisation hors France | Comportement voulu : ancienneté des créances seulement, jamais de règle inventée |

## 🔒 Rappel sécurité

Le skill **ne peut rien modifier** : aucune écriture MCP, aucun virement, aucun changement de statut —
il lit, calcule et alerte. Ce n'est **pas un avis juridique** : les dates sont des estimations prudentes
fondées sur des règles publiques (art. L110-4 C. com., L218-2 C. conso, 2224 et 2240-2244 C. civ.).
Avant d'engager une action — ou d'abandonner une créance — fais valider par un juriste ou un
commissaire de justice.
