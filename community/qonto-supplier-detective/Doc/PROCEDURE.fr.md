# 📖 Procédure d'installation et d'utilisation — qonto-supplier-detective

> Guide pas-à-pas utilisateur. Version jury : `PROCEDURE.en.md`.

---

## 1️⃣ Installation (une seule fois, ~5 min)

### Étape 1 — Connecter le MCP Qonto à Claude
1. Dans **claude.ai** (ou Claude Desktop) : Paramètres → **Connecteurs** → *Parcourir les connecteurs*
2. Chercher **Qonto** → *Ajouter* → le flux de connexion Qonto s'ouvre
3. Se connecter avec son compte Qonto (OAuth — le mot de passe n'est **jamais** partagé avec Claude)
4. Vérifier : demander à Claude « *Liste mes comptes Qonto* » → les comptes s'affichent

### Étape 2 — Installer le skill
- **Claude Code / Claude Desktop** : copier le dossier du skill dans `~/.claude/skills/qonto-supplier-detective/` (le fichier `SKILL.md` suffit)
- **claude.ai** : joindre le `SKILL.md` au projet, ou coller son contenu dans les instructions du projet

### Étape 3 — Maximiser la surface de détection (recommandé)
1. Dans l'**app Qonto** : importer/centraliser les **factures fournisseurs** (section Achats) — plus il y en a, plus le détective voit
2. C'est tout : le skill est **100 % lecture**, il n'y a rien d'autre à configurer ni à autoriser

> ℹ️ Sans factures fournisseurs importées : le skill fait une passe « transactions seules »
> (débits jumeaux + vigie IBAN sur les virements) et l'annonce clairement.

## 2️⃣ Utilisation trimestrielle (l'audit, ~10 min)

| # | Action | Résultat |
|---|---|---|
| 1 | Dire à Claude : « **Lance l'audit fournisseurs** » | Balayage complet paginé (progression résumée toutes les ~300 factures), normalisation des noms, abonnements et avoirs écartés |
| 2 | Lire les **alertes IBAN 🚨** en tête de rapport | Pour chaque changement : appeler le fournisseur **au numéro connu** avant le prochain paiement |
| 3 | Parcourir le tableau d'anomalies (montant récupérable, preuves, confiance 🟢🟡) | Tu sais quoi réclamer, à qui, avec quelles références exactes |
| 4 | Dire : « **Prépare l'e-mail de réclamation pour l'anomalie n°1** » | Brouillon prêt à envoyer : n° de facture, les 2 références de virement, dates, montant |

## 3️⃣ Utilisations ponctuelles

- « **Est-ce que j'ai payé quelque chose deux fois ce trimestre ?** » → passe D2 ciblée sur la période
- « **Un fournisseur a-t-il changé d'IBAN récemment ?** » → vigie IBAN seule, avec note de couverture
- « **Vérifie les factures de [fournisseur]** » → mini-audit ciblé sur un tiers
- « **C'est un abonnement, pas un doublon** » → le skill écarte la ligne et met à jour le total
- « **Compare la facture n°X avec ce que j'ai réellement payé** » → passe D3 sur une facture précise

## 4️⃣ Formats de sortie (où atterrit le dossier ?)

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Rapport markdown : alertes IBAN 🚨 en tête, anomalies triées par montant récupérable, total estimé, cas blanchis | **Toujours** — c'est la base |
| **Dossier interactif** | Fichier/artifact **HTML** : tableau des anomalies, cartes de preuves, jauge du récupérable | Si l'hôte affiche les fichiers (artifacts claude.ai, Claude Desktop, Claude Code) ; sinon repli automatique sur le markdown |
| **E-mail de réclamation** | Brouillon prêt à envoyer, IBAN masqués | Sur demande, anomalie par anomalie |

## 5️⃣ Dépannage (erreurs connues et vérifiées)

| Symptôme | Cause | Solution |
|---|---|---|
| `list_transactions` réclame un compte | `bank_account_id`/`iban` obligatoires | Le skill appelle `get_organization` d'abord — toujours |
| Réponses énormes / audit qui traîne | Pagination trop large | `per_page` ≤ 50 partout, fenêtres de 3 mois sur les transactions |
| Impossible de filtrer les factures par statut | Filtres de statut non exposés côté MCP | Le skill filtre côté client sur `status` |
| Un abonnement ressort en doublon | Historique trop court pour voir la cadence | Dis-le (« c'est un abonnement ») → écarté ; ≥ 6 mois d'historique recommandé |
| Paiement carte introuvable au rapprochement | `settled_at` décalé de 1-2 jours | Le skill rapproche par `emitted_at` |
| Pas d'alerte IBAN alors qu'un changement a eu lieu | IBAN non exposé pour ce fournisseur (paiement carte, prélèvement) | Note de couverture dans le rapport — vérifier le bénéficiaire dans l'app Qonto |

## 🔒 Rappel sécurité

Le skill est **100 % lecture** : il n'appelle aucun outil d'écriture Qonto, ne modifie rien, ne paie rien.
Il monte le dossier ; **toi seul** agis. Et la règle d'or face à un changement d'IBAN — c'est la bonne
pratique anti-fraude au virement : **appelle ton fournisseur au numéro que tu connais déjà** (ancien
contrat, site officiel), jamais au numéro ni à l'adresse de l'email qui annonce le changement.
Dans le doute, ne paie pas.
