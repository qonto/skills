# 🧾 qonto-support-cashdesk — Le guichet facturation du support client

> **Hackathon Qonto × Anthropic MCP (10-13/07/2026)** · Agent Skill pour le MCP Qonto
> Le client dit « vous m'avez facturé deux fois » — le skill le **prouve** (ou pas) dans les transactions, puis répond avec l'action jointe.

---

## 🎯 Le pitch

« Je n'ai pas reçu ma facture », « le lien de paiement a expiré », « vous m'avez facturé deux fois » — ces trois conversations support mobilisent le dirigeant alors que **la réponse est déjà dans Qonto**. `qonto-support-cashdesk` transforme le compte en guichet facturation :

1. **Conversation lue** — depuis Intercom si le MCP est connecté, sinon collée dans le chat : demande, indices d'identité et montants cités sont extraits
2. **Client matché, jamais deviné** — `list_clients` par email puis nom/société ; le ou les candidats sont montrés et **confirmés par toi** avant toute action
3. **Réalité vérifiée** — factures (statuts, dates), état réel du lien de paiement (ouvert, expiré, payé), encaissements dans les transactions : chaque conclusion cite sa preuve
4. **Action jointe** — renvoi de la facture (`send_client_invoice`), nouveau lien (`create_payment_link`), ou **avoir** (`create_credit_note`) si le double encaissement est **prouvé par deux crédits datés** — chaque écriture confirmée, la réponse au client fournie en brouillon à relire

## 📋 Prérequis

| Prérequis | Détail | Obligatoire |
|---|---|---|
| Compte Qonto **production** | Le skill s'adapte à toute organisation (`get_organization` d'abord, zéro donnée en dur) | ✅ |
| Pays | **Universel** — clients, factures, liens de paiement et transactions existent dans tous les pays Qonto (FR, DE, ES, IT…) ; aucune règle fiscale locale | ℹ️ tous pays |
| MCP Qonto connecté | Connecteur officiel (claude.ai / Claude Desktop), login OAuth | ✅ |
| Module Facturation Qonto utilisé | Les factures clients et liens de paiement doivent être émis via Qonto pour être vérifiables | ✅ |
| MCP Intercom | Pour lire les conversations support directement | ⭕ optionnel — sinon conversation collée dans le chat |
| MCP Gmail | Pour créer la réponse en **brouillon** (jamais envoyée par le skill) | ⭕ optionnel — sinon texte à copier-coller |

## ⚙️ Fonctionnement global

![Fonctionnement global](assets/flow.fr.png)

1. **Lecture de la conversation** : depuis Intercom si présent, sinon collée — le skill extrait le type de demande (facture non reçue / lien expiré / doublon), les indices d'identité (email, nom, société) et les références citées (numéro de facture, montant)
2. **Matching du client** : `list_clients` par email d'abord (le plus fiable), puis nom/société normalisés — candidats montrés et confirmés, deux homonymes → les deux sont listés, aucun match → dit franchement
3. **Vérification des faits** : `list_client_invoices` (statuts, montants, dates, email destinataire), `list_payment_links` + `get_payment_link` (ouvert / expiré / payé), `list_transactions` en crédits autour des dates de la facture (`emitted_at` pour les délais carte)
4. **Diagnostic prouvé** : facture jamais reçue, lien expiré, ou double encaissement — **deux crédits cités date + montant** ; un seul crédit trouvé → pas d'avoir, rapport factuel de ce qui existe
5. **Action jointe** (chacune confirmée) : renvoi de facture, nouveau lien de paiement, ou avoir si le doublon est prouvé — l'avoir documente la correction, **le remboursement reste un virement que tu fais dans l'app Qonto (SCA)**
6. **Réponse au client** : brouillon factuel à relire — excuses uniquement si l'erreur est avérée, correction citée (numéro d'avoir, nouveau lien) ; brouillon Gmail si le MCP est présent, sinon à copier-coller

## 🏗 Schéma fonctionnel

![Schéma fonctionnel](assets/functional.fr.png)

**Le point clé** : les lectures (traits pleins) sont sans risque ; les écritures (pointillés) — renvoi, lien, avoir — exigent chacune une confirmation explicite dans la conversation. L'avoir est un **document comptable réel** : il n'est proposé que preuve à l'appui, jamais en « geste commercial » décidé par le skill. Et le skill n'envoie **jamais** la réponse au client lui-même : brouillon seulement.

## 🧾 Les trois guichets

| Le client dit | Le skill vérifie | Issue honnête |
|---|---|---|
| « Je n'ai pas reçu ma facture » | La facture existe ? Statut ? Email destinataire correct sur la fiche client ? | Facture trouvée → renvoi proposé (email corrigé avant si besoin) · pas de facture → rien à renvoyer, dit tel quel |
| « Le lien de paiement a expiré » | Statut réel du lien (`get_payment_link`) : ouvert, expiré, payé | Expiré → nouveau lien proposé · déjà **payé** → signalé, pas de nouveau lien |
| « Vous m'avez facturé deux fois » | Deux crédits pour la même facture : même montant, dates proches — **les deux cités** | Doublon **prouvé** → avoir proposé · **un seul crédit → pas d'avoir**, rapport de ce qui a été trouvé |

Exemple (inventé) : facture INV-2026-042 de 480 €, deux crédits de 480 € encaissés à un jour d'écart → doublon prouvé, avoir de 480 € proposé avec les deux dates citées dans la réponse.

## 🎬 Vidéo de démo

La démo ≤ 3 min jointe à la PR suit le storyboard : les trois messages support → matching confirmé → la preuve du doublon dans les transactions → **l'avoir + la réponse d'excuse en une passe** → les deux autres guichets en accéléré. Le script détaillé (textes à dire, checklist tournage) est dans **`_SCRIPT-VIDEO.md`** — fichier interne, **exclu de la PR**.

## 📤 Formats de sortie

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Diagnostic + preuve citée + tableau récap (demande → preuve → action → statut) | **Toujours** — c'est la base |
| **Brouillon de réponse client** | Texte prêt à relire ; brouillon **Gmail** si le MCP est présent (jamais envoyé par le skill) | À chaque conversation traitée |
| **Documents Qonto** | Facture renvoyée par Qonto · lien de paiement · avoir (document comptable numéroté) | Selon le cas, après confirmation |

## 💡 Améliorations possibles (dans les clous du hackathon)

| Idée | Effort | Note |
|---|---|---|
| Détection **proactive** des doublons d'encaissement (scan périodique) | Moyen | Le pendant ventes de `qonto-supplier-detective` |
| Historique des litiges par client (récidives, délais moyens) | Faible | Réutilise le matching client |
| Réponse dans la langue du client (détectée dans la conversation) | Faible | Qonto est paneuropéen |
| Remboursement guidé : préparation de la demande de virement (approbation SCA dans l'app) | Moyen | Même modèle de sécurité que `qonto-tax-pilot` |

## 🛡 Garde-fous

- **Jamais** d'action sur un client non confirmé ; jamais une écriture présentée comme faite si elle est en attente ou a échoué
- **Avoir = preuve + confirmation** : deux crédits datés cités, confirmation explicite dans la conversation en cours — sinon pas d'avoir, quoi qu'insiste le client
- Le skill n'envoie jamais la réponse au client : brouillon à relire, c'est toi qui envoies
- Le remboursement est un virement fait par toi dans l'app Qonto (SCA) — le skill ne déplace jamais d'argent et le dit
- Doublons côté **achats** (un fournisseur t'a prélevé deux fois) → c'est `qonto-supplier-detective`
- IBAN masqués (4 derniers chiffres) · pagination ≤ 50 partout · répétitions sur **client fictif** (factures MCP = réelles → draft puis delete)

---

*Documentation FR (pilotage). Version jury : `README.en.md`. Livrable PR : `SKILL.md`. Procédure pas-à-pas : `docs/PROCEDURE.fr.md`. Docs riches : `docs/doc-qonto-support-cashdesk.fr.html` · `docs/doc-qonto-support-cashdesk.fr.docx`.*
