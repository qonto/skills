# 📖 Procédure d'installation et d'utilisation — qonto-money-calendar

> Guide pas-à-pas utilisateur. Version jury : `PROCEDURE.en.md`.

---

## 1️⃣ Installation (une seule fois, ~5 min)

### Étape 1 — Connecter le MCP Qonto à Claude
1. Dans **claude.ai** (ou Claude Desktop) : Paramètres → **Connecteurs** → *Parcourir les connecteurs*
2. Chercher **Qonto** → *Ajouter* → le flux de connexion Qonto s'ouvre
3. Se connecter avec son compte Qonto (OAuth — le mot de passe n'est **jamais** partagé avec Claude)
4. Vérifier : demander à Claude « *Liste mes comptes Qonto* » → les comptes s'affichent

### Étape 2 — Connecter le MCP Google Calendar (requis pour les 2 sens)
1. Même chemin : Paramètres → **Connecteurs** → chercher **Google Calendar** → *Ajouter* → login Google (OAuth)
2. Vérifier : demander à Claude « *Qu'est-ce que j'ai dans mon agenda demain ?* »

> Sans Google Calendar : le sens 1 sort l'échéancier en **tableau dans la conversation**,
> et le sens 2 (facturation depuis l'agenda) est **indisponible** — le skill te le dira clairement.

### Étape 3 — Installer le skill
- **Claude Code / Claude Desktop** : copier le dossier du skill dans `~/.claude/skills/qonto-money-calendar/` (le fichier `SKILL.md` suffit)
- **claude.ai** : joindre le `SKILL.md` au projet, ou coller son contenu dans les instructions du projet

### Étape 4 — Adopter la convention de tag (pour le sens 2)
Quand tu travailles pour un client, pose un événement dans ton agenda avec **le nom du client entre crochets** dans le titre :

| Tu écris dans l'agenda | Le skill compte |
|---|---|
| `[Acme] sprint sur site` | 1 jour facturable pour Acme |
| `[Acme] atelier` posé sur 3 jours | 3 jours |
| `[Acme] 0.5 revue de code` | 0,5 jour |
| `Dentiste 15h` (pas de crochets) | Rien — ignoré |

C'est tout. Pas d'outil de plus, pas de time-tracker : ton agenda **est** le time-tracker.

## 2️⃣ Usage type

### Le rituel du dimanche soir (ou du 1er du mois) — sens 1

| # | Action | Résultat |
|---|---|---|
| 1 | Dire à Claude : « **Mets mon mois financier dans mon agenda** » | Lecture des factures fournisseurs/clients + récurrences sur 24-36 mois |
| 2 | Lire le **récapitulatif** (date · titre · montant · source 🟢/🟡) | Tu vois exactement ce qui va être créé — tu peux retirer des lignes |
| 3 | Confirmer explicitement (« oui, crée-les ») | Événements créés : montant dans le titre, rappel J-3, marqueur anti-doublons |
| 4 | Ouvrir Google Calendar | Ton mois financier est visible — loyer, fournisseurs, encaissements attendus |

### La fin de mois — sens 2

| # | Action | Résultat |
|---|---|---|
| 1 | Dire à Claude : « **Facture mon mois de juin** » | Comptage des jours tagués `[Client]`, liste des dates affichée |
| 2 | Vérifier le comptage (un oubli de tag se voit ici) | Tableau jours × client |
| 3 | Confirmer le **TJM proposé** (déduit de tes factures passées) ou en donner un autre | Le TJM n'est jamais deviné — toujours confirmé |
| 4 | Confirmer les lignes | `create_client_invoice` en **brouillon** dans Qonto |
| 5 | Relire dans Qonto → envoyer quand tu décides | La facture part avec ta numérotation et tes mentions habituelles |

## 3️⃣ Utilisations ponctuelles

- « **Qu'est-ce qui tombe cette semaine ?** » → l'échéancier des 7 prochains jours, en tableau
- « **Ajoute mes échéances de juillet à l'agenda** » → sens 1 sur une période précise
- « **Combien de jours j'ai fait chez [Acme] ce trimestre ?** » → comptage sans facturation
- « **Rejoue l'échéancier** » → les événements marqués sont mis à jour, jamais dupliqués

## 4️⃣ Formats de sortie

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown : échéancier, récap avant écriture, comptage, résumé de facture | **Toujours** — c'est la base |
| **Google Calendar** | Événements datés, montant dans le titre, rappel J-3, marqueur `[qonto-money-calendar]` | Si le MCP est présent **et** le récap confirmé |
| **Facture Qonto** | Brouillon `create_client_invoice`, section Facturation | Sens 2, après confirmation TJM + lignes |

## 5️⃣ Dépannage (erreurs connues et vérifiées)

| Symptôme | Cause | Solution |
|---|---|---|
| `list_transactions` échoue | `bank_account_id`/`iban` manquant | Le skill appelle `get_organization` d'abord — toujours |
| Réponses énormes / tronquées | Pagination trop large | `per_page` ≤ 50 partout, fenêtres de 3 mois |
| Le sens 2 « ne trouve rien » | Jours sans crochets `[Client]` dans le titre | Vérifier la convention de tag (étape 4 de l'installation) |
| Événements en double après relance | Événements créés hors skill, sans marqueur | Le skill met à jour ses événements marqués ; ceux créés à la main sont laissés intacts |
| Client tagué introuvable dans Qonto | Orthographe différente de la fiche client | Le skill propose les candidats proches et demande — il ne crée jamais un client tout seul |
| Récurrences annuelles absentes | Historique < 24 mois | Normal — les cadences annuelles exigent 24-36 mois ; le skill le signale |
| Facture de test à supprimer | Répétition / démo | Client fictif + brouillon + `delete_client_invoice` |

## 🔒 Rappel sécurité

Le skill **ne peut pas** déplacer d'argent — il planifie et prépare. Les événements d'agenda
n'existent qu'après un récapitulatif que **tu** confirmes. Les factures restent en **brouillon** :
c'est toi qui relis et qui envoies. Payer un fournisseur reste une action dans l'app Qonto,
protégée par ta SCA (2FA). Le TJM est déduit de ton historique **puis confirmé par toi** — jamais deviné.
