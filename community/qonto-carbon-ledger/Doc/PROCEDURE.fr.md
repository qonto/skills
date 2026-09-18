# 📖 Procédure d'installation et d'utilisation — qonto-carbon-ledger

> Guide pas-à-pas utilisateur. Version jury : `PROCEDURE.en.md`.

---

## 1️⃣ Installation (une seule fois, ~5 min)

### Étape 1 — Connecter le MCP Qonto à Claude
1. Dans **claude.ai** (ou Claude Desktop) : Paramètres → **Connecteurs** → *Parcourir les connecteurs*
2. Chercher **Qonto** → *Ajouter* → le flux de connexion Qonto s'ouvre
3. Se connecter avec son compte Qonto (OAuth — le mot de passe n'est **jamais** partagé avec Claude)
4. Vérifier : demander à Claude « *Liste mes comptes Qonto* » → les comptes s'affichent

### Étape 2 — Installer le skill
- **Claude Code / Claude Desktop** : copier le dossier du skill dans `~/.claude/skills/qonto-carbon-ledger/` (le fichier `SKILL.md` suffit)
- **claude.ai** : joindre le `SKILL.md` au projet, ou coller son contenu dans les instructions du projet

### Étape 3 — (Optionnel) Connecter le MCP Datagouv
Si le connecteur **Datagouv** est présent, le skill propose de recouper ses facteurs embarqués avec les référentiels ADEME à jour. Sinon, il utilise ses facteurs embarqués (sourcés, millésimés) et le dit — **rien d'autre à installer**.

> 💡 Aucun sous-compte, aucune écriture, aucune approbation : le skill est 100 % lecture seule.

## 2️⃣ Utilisation type (le bilan en 2 minutes)

| # | Action | Résultat |
|---|---|---|
| 1 | Dire à Claude : « **Quelle est l'empreinte carbone de ma boîte ?** » | Lecture de 24-36 mois de débits, classification par postes d'émission |
| 2 | Lire le tableau : empreinte ~N tCO2e/an **avec sa fourchette**, répartition par poste (facteur + source + millésime par ligne) | Tu sais d'où vient chaque tonne — et à quel point c'est incertain |
| 3 | Regarder les **3 leviers** classés par impact estimé et coût (gratuit / économise / coûte) | Tu sais où agir en premier, sur tes montants réels |
| 4 | (Optionnel) Demander le **dashboard HTML** | Jauge d'empreinte + barres par poste + tendance + leviers |

## 3️⃣ Utilisations ponctuelles

- « **Quels postes émettent le plus chez moi ?** » → répartition par poste, dominants en tête
- « **Mon empreinte a-t-elle baissé depuis l'an dernier ?** » → tendance sur 24-36 mois
- « **Et le numérique, ça pèse combien ?** » → zoom sur un poste, avec ses contreparties
- « **C'est fiable, ton chiffre ?** » → le skill explique la méthode monétaire, ses limites et l'incertitude ±50 %
- « **Prépare-moi un pré-bilan pour mon prestataire BEGES** » → export des postes, montants et facteurs — en annonçant que le bilan officiel reste son travail

## 4️⃣ Formats de sortie (où atterrit le bilan ?)

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown : empreinte + fourchette, postes, tendance, leviers | **Toujours** — c'est la base |
| **Dashboard interactif** | Fichier/artifact **HTML** : jauge avec bande d'incertitude, barres par poste, tendance, leviers | Si l'hôte affiche les fichiers (artifacts claude.ai, Claude Desktop, Claude Code) ; sinon repli automatique sur les tableaux |

## 5️⃣ Dépannage (erreurs connues et vérifiées)

| Symptôme | Cause | Solution |
|---|---|---|
| `list_transactions` échoue d'emblée | `bank_account_id`/`iban` manquant | Le skill appelle **toujours** `get_organization` d'abord |
| Réponses énormes / tronquées | Pagination trop large | `per_page` ≤ 50, fenêtres de 3 mois — géré par le skill |
| `403 missing oauth scope` sur `list_cash_flow_categories` | Hors périmètre du connecteur claude.ai | Normal — le skill classe via contreparties + **labels** à la place |
| Beaucoup de débits « non classés » | Contreparties ambiguës, pas de labels | Labelliser les principales contreparties dans Qonto ; au-delà de ~20 % le skill prévient que l'estimation est fragile |
| Empreinte qui semble énorme | Gros achat ponctuel (véhicule, machine) noyé dans le flux | Le skill isole les achats ≥ ~5 000 € — vérifier la ligne « ponctuels » |
| Pays ≠ France | Facteurs calibrés FR/UE | Méthode identique, facteurs annoncés comme à adapter — l'estimation reste produite et taguée |

## 🔒 Rappel sécurité

Le skill est **100 % lecture seule** : aucun outil d'écriture, aucune demande de virement, aucun paiement —
il n'y a rien à approuver. Il ne vend et ne recommande **jamais** de compensation carbone. Ses chiffres sont
des **ordres de grandeur** (±50 % et plus, affiché partout) : pour un bilan réglementaire (BEGES / CSRD),
passe par un prestataire spécialisé — le skill te le rappellera lui-même.
