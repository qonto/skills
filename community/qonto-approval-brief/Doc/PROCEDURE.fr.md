# 📖 Procédure d'installation et d'utilisation — qonto-approval-brief

> Guide pas-à-pas utilisateur. Version jury : `PROCEDURE.en.md`.

---

## 1️⃣ Installation (une seule fois, ~5 min)

### Étape 1 — Connecter le MCP Qonto à Claude
1. Dans **claude.ai** (ou Claude Desktop) : Paramètres → **Connecteurs** → *Parcourir les connecteurs*
2. Chercher **Qonto** → *Ajouter* → le flux de connexion Qonto s'ouvre
3. Se connecter avec son compte Qonto (OAuth — le mot de passe n'est **jamais** partagé avec Claude)
4. Vérifier : demander à Claude « *Liste mes demandes en attente* » → les demandes s'affichent (ou « aucune », c'est bon signe)

### Étape 2 — Installer le skill
- **Claude Code / Claude Desktop** : copier le dossier du skill dans `~/.claude/skills/qonto-approval-brief/` (le fichier `SKILL.md` suffit)
- **claude.ai** : joindre le `SKILL.md` au projet, ou coller son contenu dans les instructions du projet

### Étape 3 — Vérifier son rôle (important)
Le compte connecté doit pouvoir **voir les demandes de l'équipe** (Owner, Admin ou Manager avec revue des demandes).
Sinon `list_requests` revient vide — et le skill te dira que c'est un problème de visibilité, pas une absence de demandes.

> ℹ️ Optionnel : connecter les MCP **Gmail** (contexte : devis, échanges) et **Slack** (digest).
> Le skill les détecte tout seul — sans eux, le cœur fonctionne en Qonto pur.

## 2️⃣ Usage type (le rituel des demandes, ~2 min)

| # | Action | Résultat |
|---|---|---|
| 1 | Dire à Claude : « **Fais-moi le brief de mes demandes en attente** » | Un brief par demande : ✅ recommandé / 🔶 à vérifier, preuves citées |
| 2 | Lire les briefs 🔶 (IBAN jamais vu, montant inhabituel, doublon possible…) | Tu sais exactement quoi vérifier, et auprès de qui |
| 3 | Pour refuser : « **Refuse la demande X : [motif]** » puis confirmer | Refus motivé envoyé — le demandeur voit le motif dans Qonto |
| 4 | Pour approuver : ouvrir l'**app Qonto** → Demandes → approuver avec ta **2FA** | L'argent ne bouge que là — le skill ne peut pas approuver ✅ |

## 3️⃣ Utilisations ponctuelles

- « **Je peux approuver la demande de [prénom] ?** » → brief instantané de cette demande, preuves citées
- « **On a déjà payé ce bénéficiaire ?** » → historique du tiers : N paiements, montants, cadence
- « **Cet IBAN, on le connaît ?** » → déjà vu (daté) ou jamais vu (signal, pas accusation)
- « **Poste le digest des demandes sur Slack** » → résumé des briefs sur le canal choisi (si MCP Slack connecté)

## 4️⃣ Formats de sortie (où atterrissent les briefs ?)

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableau des briefs + brief détaillé par demande 🔶 + prochaine étape explicite | **Toujours** — c'est la base |
| **Tableau de bord des briefs** | Fichier/artifact **HTML** : une carte par demande, verdict et preuves | Si l'hôte affiche les fichiers ; repli automatique sur les tableaux |
| **Motif de refus** | Texte joint au refus, visible par le demandeur dans Qonto | À chaque refus (confirmé) |
| **Digest Slack** | Résumé posté sur le canal choisi | Si le MCP Slack est connecté (optionnel) |

## 5️⃣ Dépannage (erreurs connues et vérifiées)

| Symptôme | Cause | Solution |
|---|---|---|
| Claude « refuse » d'approuver une demande | **Par conception** : `approve_request` n'est jamais utilisé par ce skill | Approuver dans l'app Qonto avec ta 2FA — c'est le modèle de sécurité |
| Échec du refus d'une demande groupée | `decline_request` exige `request_type: "multi_transfers"` (au **pluriel**) | Géré par le skill |
| Erreur sur `list_transactions` | `bank_account_id`/`iban` obligatoire | Le skill appelle `get_organization` d'abord, systématiquement |
| `list_requests` revient vide | Aucune demande en attente **ou** rôle sans revue des demandes | Le skill dit lequel des deux ; vérifier son rôle dans Qonto si besoin |
| Réponses énormes / tronquées | Pagination absente | Le skill pagine partout avec `per_page` ≤ 50 |
| Pas de contexte email dans les briefs | MCP Gmail non connecté | Optionnel — le skill le dit une fois et continue en Qonto pur |
| « IBAN jamais vu » sur un fournisseur légitime | Nouveau fournisseur = normal, une fois | C'est un **signal, pas une accusation** : vérifier avec le demandeur, la fois suivante il sera « connu » |

## 🔒 Rappel sécurité

Le skill **ne peut pas** approuver ni déplacer d'argent : `approve_request` n'est jamais appelé.
Sa seule écriture est le **refus motivé** (`decline_request`), toujours confirmé par toi dans la conversation.
Les approbations se font dans l'app Qonto, avec **ta** 2FA — chaque brief cite ses preuves, tu décides en connaissance de cause.
