# 📖 Procédure d'installation et d'utilisation — qonto-einvoice-ready

> Guide pas-à-pas utilisateur. Version jury : `PROCEDURE.en.md`.

---

## 1️⃣ Installation (une seule fois, ~5 min)

### Étape 1 — Connecter le MCP Qonto à Claude
1. Dans **claude.ai** (ou Claude Desktop) : Paramètres → **Connecteurs** → *Parcourir les connecteurs*
2. Chercher **Qonto** → *Ajouter* → le flux de connexion Qonto s'ouvre
3. Se connecter avec son compte Qonto (OAuth — le mot de passe n'est **jamais** partagé avec Claude)
4. Vérifier : demander à Claude « *Liste mes clients Qonto* » → les fiches s'affichent

### Étape 2 — Installer le skill
- **Claude Code / Claude Desktop** : copier le dossier du skill dans `~/.claude/skills/qonto-einvoice-ready/` (le fichier `SKILL.md` suffit)
- **claude.ai** : joindre le `SKILL.md` au projet, ou coller son contenu dans les instructions du projet

### Étape 3 — Rien d'autre à configurer
- L'API du registre public (`recherche-entreprises.api.gouv.fr`) est **publique, sans clé ni compte**
- Optionnel : connaître la taille de son entreprise (GE / ETI / PME) — le skill la retrouve en général au registre, sinon il la demande

## 2️⃣ Usage type : l'audit + la correction (~5 min)

| # | Action | Résultat |
|---|---|---|
| 1 | Dire à Claude : « **Suis-je prêt pour la facturation électronique ?** » | Score de readiness + calendrier applicable + fiches incomplètes listées |
| 2 | Lire l'audit (fiche par fiche : SIREN, TVA intracom, adresse) | Tu sais exactement ce qui bloquerait un Factur-X |
| 3 | Dire : « **Complète mes fiches clients** » | Le skill interroge le registre public et affiche un **aperçu ligne par ligne** |
| 4 | Vérifier l'aperçu (homonymes → le skill demande), puis confirmer (« oui, mets à jour ») | `update_client` champ par champ, résultat annoncé |
| 5 | Relire le score | Readiness avant/après + plan d'action pour le reste |

## 3️⃣ Utilisations ponctuelles

- « **Quel calendrier e-invoicing s'applique à mon entreprise ?** » → réception 01/09/2026 + ta date d'émission (2026 ou 2027)
- « **Quels clients bloqueraient un Factur-X aujourd'hui ?** » → liste des fiches incomplètes, champ par champ
- « **Suis-je concerné par l'e-reporting ?** » → clients étrangers + B2C repérés dans les fiches et les flux
- « **Retrouve le SIREN de ce client** » → recherche au registre public, aperçu, confirmation

## 4️⃣ Formats de sortie

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown : score, fiches incomplètes, calendrier, exposition e-reporting | **Toujours** — c'est la base |
| **Aperçu de correction** | Tableau fiche · champ · actuel → proposé · source, soumis à confirmation | À chaque correction proposée |
| **Rapport de readiness** | Fichier/artifact **HTML** : jauge avant/après, compte à rebours, plan d'action | Si l'hôte affiche les fichiers (artifacts claude.ai, Claude Desktop, Claude Code) ; sinon repli sur les tableaux |

## 5️⃣ Dépannage (erreurs connues et vérifiées)

| Symptôme | Cause | Solution |
|---|---|---|
| Erreur sur `list_transactions` | `bank_account_id`/`iban` manquant | Normal — le skill appelle `get_organization` d'abord, toujours |
| Réponses tronquées / lenteur | Pagination trop large | Le skill pagine `per_page` ≤ 50 partout |
| Client introuvable au registre | Nom commercial ≠ raison sociale | Donner le SIREN au skill, ou affiner avec le code postal ; sinon la fiche est passée |
| Plusieurs entreprises homonymes | Noms fréquents au registre | Le skill affiche les candidats (nom, ville, SIREN) et **demande** — jamais d'auto-match |
| N° de TVA marqué « dérivé » | Calculé depuis le SIREN (clé FR + 2 chiffres) | Normal — à faire confirmer par le client concerné |
| Registre public indisponible | API data.gouv en maintenance / hors ligne | L'audit et le score tournent quand même ; seule la correction en live attend |
| La mise à jour ne s'applique pas | Confirmation non donnée dans la conversation | Voulu : aucun `update_client` sans « oui » explicite après l'aperçu |
| Pays de l'organisation ≠ FR | Réforme française uniquement | Le skill bascule en audit générique de complétude (annoncé clairement) |

## 🔒 Rappel sécurité

La seule écriture du skill est `update_client` : elle **ne touche jamais à l'argent**, seulement aux
fiches clients. Chaque modification est montrée en aperçu (valeur actuelle → proposée, avec sa source)
et n'est écrite qu'après **ta** confirmation explicite — champ par champ, jamais en masse. Et le choix
de ta plateforme agréée (PDP) t'appartient : le skill informe, il ne décide pas.
