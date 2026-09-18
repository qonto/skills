# 📖 Procédure d'installation et d'utilisation — qonto-invoice-chaser

> Guide pas-à-pas utilisateur. Version jury : `PROCEDURE.en.md`.

---

## 1️⃣ Installation (une seule fois, ~5 min)

### Étape 1 — Connecter le MCP Qonto à Claude
1. Dans **claude.ai** (ou Claude Desktop) : Paramètres → **Connecteurs** → *Parcourir les connecteurs*
2. Chercher **Qonto** → *Ajouter* → le flux de connexion Qonto s'ouvre
3. Se connecter avec son compte Qonto (OAuth — le mot de passe n'est **jamais** partagé avec Claude)
4. Vérifier : demander à Claude « *Liste mes factures clients* » → les factures s'affichent

### Étape 2 — Installer le skill
- **Claude Code / Claude Desktop** : copier le dossier du skill dans `~/.claude/skills/qonto-invoice-chaser/` (le fichier `SKILL.md` suffit)
- **claude.ai** : joindre le `SKILL.md` au projet, ou coller son contenu dans les instructions du projet

### Étape 3 — Connecter le MCP Gmail (recommandé)
1. Paramètres → **Connecteurs** → chercher **Gmail** → *Ajouter* → OAuth Google
2. C'est tout — le skill le **détectera automatiquement** et déposera ses relances en brouillons

> ⚠️ Cette étape est optionnelle : sans Gmail, le skill fournit la relance en texte prêt à copier
> dans n'importe quel client mail. Le cœur (détection, croisement, rédaction) marche en Qonto pur.

## 2️⃣ Utilisation hebdomadaire (le rituel du lundi matin, ~3 min)

| # | Action | Résultat |
|---|---|---|
| 1 | Dire à Claude : « **Relance mes impayés** » | Scan des factures en retard + croisement avec les encaissements réels |
| 2 | Vérifier les rapprochements proposés (facture ↔ transaction) | Les factures déjà payées sont marquées (après ta confirmation), pas relancées |
| 3 | Lire les relances rédigées (profil payeur + chiffres exacts affichés) | Tu sais qui est relancé, sur quel ton, et pourquoi |
| 4 | Ouvrir **Gmail → Brouillons** : relire → ajuster si besoin → **envoyer** | La relance part, signée de toi ✅ |

## 3️⃣ Utilisations ponctuelles

- « **Qui me doit de l'argent, là ?** » → encours, aging, table d'action par facture
- « **La facture INV-2026-042 a-t-elle été payée ?** » → croisement avec les transactions, réponse sourcée
- « **Prépare la mise en demeure pour [client]** » → intérêts calculés + indemnité 40 € (art. L441-10), en brouillon
- « **Quel est mon DSO ce trimestre ?** » → estimation + top retardataires

## 4️⃣ Formats de sortie (où atterrit la relance ?)

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown (encours, aging, actions par facture) | **Toujours** — c'est la base |
| **Brouillon Gmail** | Email complet (destinataire, objet avec n° de facture, corps personnalisé) | Si le MCP Gmail est connecté |
| **Texte prêt à copier** | Objet + corps, à coller dans n'importe quel client mail | Sans MCP Gmail |
| **Dashboard interactif** | Fichier/artifact **HTML** : barres d'aging, top retardataires, pipeline | Si l'hôte affiche les fichiers ; repli sur les tableaux sinon |

## 5️⃣ Dépannage (erreurs connues et vérifiées)

| Symptôme | Cause | Solution |
|---|---|---|
| `list_transactions` échoue | `bank_account_id` / `iban` manquant (paramètre exigé) | Le skill appelle `get_organization` d'abord — systématique |
| Réponses énormes / lenteur | Pagination trop large | `per_page` ≤ 50 + fenêtres de dates — géré par le skill |
| Facture payée mais toujours « unpaid » dans Qonto | Virement reçu hors lien de paiement, jamais rapprochée | C'est le cœur du skill : croisement → `mark_client_invoice_as_paid` **proposé**, jamais silencieux |
| Paiement partiel ou virement groupé | Un règlement ≠ une facture | Candidats présentés avec les montants ; jamais de marquage automatique |
| Pas de brouillon créé | MCP Gmail non connecté | Texte prêt à copier fourni ; connecter Gmail dans Connecteurs (étape 3) |
| Relance sans destinataire | Email absent de la fiche client | Le skill le signale (`get_client`) → compléter la fiche dans Qonto, jamais d'adresse devinée |
| Pas de mention légale chiffrée | Organisation hors France | Normal — relances graduées identiques, mais pas de taux inventé (référence générique directive UE 2011/7) |

## 🔒 Rappel sécurité

Le skill **n'envoie rien et ne marque rien tout seul**. Le marquage « payée » est une *proposition*
avec la transaction en preuve — tu confirmes ou pas. La relance n'existe qu'en **brouillon**
que toi seul relis et envoies. La mise en demeure est un document sérieux : relecture
(expert-comptable ou juriste) recommandée avant envoi, et envoi en LRAR conseillé.
