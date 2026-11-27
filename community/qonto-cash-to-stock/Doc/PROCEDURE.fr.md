# 📖 Procédure d'installation et d'utilisation — qonto-cash-to-stock

> Guide pas-à-pas utilisateur. Version jury : `PROCEDURE.en.md`.

---

## 1️⃣ Installation (une seule fois, ~5 min)

### Étape 1 — Connecter le MCP Qonto à Claude
1. Dans **claude.ai** (ou Claude Desktop) : Paramètres → **Connecteurs** → *Parcourir les connecteurs*
2. Chercher **Qonto** → *Ajouter* → le flux de connexion Qonto s'ouvre
3. Se connecter avec son compte Qonto (OAuth — le mot de passe n'est **jamais** partagé avec Claude)
4. Vérifier : demander à Claude « *Liste mes comptes Qonto* » → les comptes s'affichent

### Étape 2 — Installer le skill
- **Claude Code / Claude Desktop** : copier le dossier du skill dans `~/.claude/skills/qonto-cash-to-stock/` (le fichier `SKILL.md` suffit)
- **claude.ai** : joindre le `SKILL.md` au projet, ou coller son contenu dans les instructions du projet

### Étape 3 — Connecter le MCP Shopify (optionnel mais recommandé)
1. Paramètres → **Connecteurs** → chercher **Shopify** → *Ajouter* → connexion à ta boutique
2. Vérifier : demander à Claude « *Quel est mon niveau de stock ?* » → les produits s'affichent

> ℹ️ Sans Shopify, le skill fonctionne en **mode dégradé propre** : vélocité estimée depuis les
> encaissements Qonto + catalogue produits — chaque chiffre dérivé est taggé 🟡 estimé.

## 2️⃣ Usage type (le rituel du réassort, ~3 min)

| # | Action | Résultat |
|---|---|---|
| 1 | Dire à Claude : « **Combien d'unités puis-je commander sans me mettre en danger ?** » | Tréso réellement libre calculée (soldes − fournisseurs − impôts détectés − coûts fixes − coussin) |
| 2 | Lire le calendrier des engagements et la courbe 90 j | Tu vois le point bas daté et ce qui le cause |
| 3 | Lire les **4 chiffres** : tréso libre · date de rupture · unités finançables · date limite de commande | La décision tient sur un écran, chaque chiffre taggé 🟢🟡🔵 |
| 4 | Répondre aux questions du skill si besoin (coût unitaire débarqué, délai fournisseur) | Jamais deviné en silence — demandé une fois |
| 5 | Décider, puis confirmer explicitement (« oui, prépare le virement fournisseur ») | Demande de virement créée, calcul complet dans la note |
| 6 | Sur le **téléphone** : notification push Qonto → ouvrir → vérifier la note → **approuver (SCA)** | Le paiement fournisseur part ✅ — c'est toi qui as le dernier mot |

## 3️⃣ Prompts à copier-coller

- « **Combien d'unités puis-je commander sans mettre le compte en danger, et quand ?** »
- « **Quelle est ma tréso réellement libre après mes échéances des 90 prochains jours ?** »
- « **Quand vais-je être en rupture de stock ?** » (Shopify connecté → par produit)
- « **Et si je coupais la commande en deux ?** » / « **Et si j'attendais après l'échéance de TVA ?** »
- « **OK, prépare la demande de virement fournisseur de [montant] €** » (montant fictif — remplace par le tien)

## 4️⃣ Formats de sortie

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown (engagements, courbe résumée, 4 chiffres, récap demande) | **Toujours** — c'est la base |
| **Dashboard interactif** | Fichier/artifact **HTML** : courbe de tréso libre, échéances en marqueurs, compte à rebours rupture, jauge d'unités | Si l'hôte affiche les fichiers ; sinon repli automatique sur les tableaux |
| **Note de la demande Qonto** | Texte joint à la demande de virement, **visible au moment de l'approbation SCA** | À chaque demande créée |

## 5️⃣ Dépannage (erreurs connues et vérifiées)

| Symptôme | Cause | Solution |
|---|---|---|
| `list_transactions` échoue ou renvoie une erreur de compte | `bank_account_id`/`iban` manquant | Normal — le skill appelle **toujours** `get_organization` d'abord |
| `422` à la création de la demande de virement | Champ `credit_account_currency` manquant (non documenté) | Le skill l'envoie systématiquement |
| Refus d'une demande de test impossible | `decline_request` exige `request_type: "multi_transfers"` (au pluriel) | Géré par le skill |
| « Le skill ne voit pas mes ventes ni mon stock » | MCP Shopify non connecté | Connecter le connecteur Shopify, ou accepter le mode dégradé (estimation 🟡 depuis les encaissements) |
| Réponses très lentes ou tronquées | Pagination trop large | Le skill pagine `per_page` ≤ 50 partout |
| Unités finançables incohérentes | Coût unitaire débarqué mal renseigné | Le skill le demande — vérifier la valeur donnée (transport et douane inclus) |
| Échéance fiscale connue absente du calendrier | Impôt jamais prélevé sur ce compte (historique court) | Le skill ne projette que ce qu'il observe — la signaler à la main dans la conversation |

## 🔒 Rappel sécurité

Le skill **ne peut pas** déplacer d'argent. Il crée une *demande*, que **toi seul** peux approuver
avec ta 2FA dans l'app Qonto. Tu peux la refuser en un tap. Chaque demande contient le calcul
complet dans sa note — tu approuves en connaissance de cause. La décision de commander reste humaine.
