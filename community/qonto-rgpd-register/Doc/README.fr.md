# 🗂 qonto-rgpd-register — Ton compte bancaire connaît tes sous-traitants mieux que toi

> **Hackathon Qonto × Anthropic MCP (10-13/07/2026)** · Agent Skill pour le MCP Qonto
> **Zéro écriture, par conception** : le skill lit les dépenses, classe, rédige — et s'arrête là.
> Partout le même bandeau : **projet de registre, pas un avis juridique — à valider (DPO/juriste)**.

---

## 🎯 Le pitch

Le registre des activités de traitement (art. 30 RGPD), c'est le document que **90 % des TPE n'ont pas** — et le premier que la CNIL demande. Or la liste des sous-traitants qui traitent tes données personnelles est déjà écrite quelque part : **dans tes débits**. `qonto-rgpd-register` la lit :

1. **Détection des sous-traitants** — les outils SaaS qui traitent des données personnelles (CRM, emailing, analytics, IA, cloud, paie, support), reconnus par la culture générale de Claude **dès la première occurrence** dans les débits — pas besoin de récurrence
2. **Classification par traitement** — finalité, catégories de données typiques, personnes concernées, siège et hébergement UE / hors-UE — chaque attribut marqué **« à valider »**
3. **Projet de registre art. 30 au format CNIL** — une fiche par traitement (finalité, base légale à choisir, données, destinataires, sous-traitants, durées à fixer, transferts, mesures de sécurité), en-tête responsable de traitement rempli depuis `get_organization`
4. **Drapeaux actionnables** — 🔴 transfert hors UE → clauses contractuelles types à vérifier · 🟠 DPA à retrouver ou signer · 🟡 outil disparu des débits depuis 6 mois → à sortir du registre ?

Même matière première que `qonto-subscription-audit`, lecture opposée : lui chiffre le **coût** de tes abonnements, celui-ci en tire l'**obligation légale**.

## 📋 Prérequis

| Prérequis | Détail | Obligatoire |
|---|---|---|
| Compte Qonto **production** | Exigence du hackathon ; le skill s'adapte à toute organisation (`get_organization` d'abord, zéro donnée en dur) | ✅ |
| Pays | **RGPD = toute l'UE — skill pan-européen.** Tous les pays Qonto (FR, DE, ES, IT, AT, NL, BE, PT) sont couverts : en France, format et références **CNIL** ; ailleurs, même registre, références à l'autorité locale (BfDI/LfDI, AEPD, Garante, DSB, AP, APD/GBA, CNPD) | ℹ️ détecté |
| MCP Qonto connecté | Via le connecteur officiel (claude.ai / Claude Desktop), login OAuth | ✅ |
| Historique de dépenses | 12-24 mois idéalement ; compte mince → le skill dit ce qu'il n'a pas pu détecter et livre quand même le squelette du registre | ⭕ |
| DPO ou juriste pour valider | Le skill produit un **projet** : qualification juridique, bases légales et durées de conservation restent des décisions humaines | ✅ à la fin |

## ⚙️ Fonctionnement global

![Fonctionnement global](assets/flow.fr.png)

1. **Identité du responsable de traitement** : `get_organization` → raison sociale, forme, adresse, pays = l'en-tête obligatoire du registre. Au passage, rappel honnête : l'exemption « moins de 250 salariés » de l'art. 30(5) est plus étroite qu'on croit — un traitement **non occasionnel** (paie, CRM, prospection) suffit à rendre le registre obligatoire
2. **Scan des dépenses** (12-24 mois, `side: debit`, pagination ≤ 50, fenêtres de 3 mois) + `list_supplier_invoices` (noms plus propres que les libellés carte). Graphies normalisées et fusionnées : `GOOGLE *WORKSPACE`, `GOOGLE IRELAND LTD`, `Google Cloud EMEA` = un seul fournisseur. Date de dernière apparition suivie (`emitted_at` pour les cartes) pour le drapeau fraîcheur
3. **Classification** : pour chaque SaaS reconnu — traite-t-il des données personnelles pour ton compte ? Catégorie (CRM, emailing, analytics, IA, cloud, paie, support, e-commerce/paiement), données typiques, siège et hébergement UE/hors-UE — **tout marqué « à valider »**. Les hors-périmètre (frais bancaires, déplacements, matériel) sont listés en annexe, rien ne disparaît en silence
4. **Fiches de traitement** : regroupement par **finalité, pas par fournisseur** (prospection & clients, communication marketing, mesure d'audience, support, RH & paie, comptabilité, hébergement IT). `list_memberships` : plusieurs membres actifs → le skill propose le bloc RH même sans outil de paie visible dans les débits
5. **Drapeaux** : 🔴 fournisseur ou hébergement hors UE → mécanisme de transfert à vérifier (adéquation, CCT, annexes du DPA) · 🟠 DPA à retrouver ou signer, fournisseur par fournisseur · 🟡 disparu des débits ≥ 6 mois → encore utilisé ? à sortir du registre (et demander la suppression des données) · 🟡 revendeur/marketplace qui masque l'éditeur réel → le skill **demande**, ne devine jamais
6. **Livraison** : tableau de synthèse + fiche par traitement + to-do priorisée en markdown ; document HTML imprimable si l'hôte affiche les fichiers. Partout : **projet de registre, pas un avis juridique**

## 🏗 Schéma fonctionnel

![Schéma fonctionnel](assets/functional.fr.png)

**Zéro écriture, par conception** : quatre outils de lecture, aucun outil d'écriture. Le skill ne modifie rien sur le compte, ne contacte aucun fournisseur, n'envoie rien. Il transforme une donnée que tu as déjà (tes débits) en un document que tu n'as pas (ton registre) — et la validation reste humaine.

## 🗂 Catégories de sous-traitants reconnues

> Exemples **illustratifs** (culture générale de Claude), pas issus d'un compte réel.

| Catégorie | Exemples d'outils reconnus | Données typiquement traitées | Point d'attention fréquent |
|---|---|---|---|
| CRM & prospection | HubSpot, Pipedrive, Salesforce | Identité, coordonnées, historique commercial | Siège US → mécanisme de transfert à vérifier |
| Emailing & marketing | Mailchimp, Brevo, Mailjet | Emails, comportement d'ouverture, segments | Consentement & base légale à documenter |
| Analytics | Google Analytics, Matomo, Plausible | Identifiants en ligne, navigation | Hors-UE vs auto-hébergé : régimes très différents |
| IA | OpenAI, Anthropic, Mistral | Contenu des prompts (parfois des données clients !) | Vérifier l'option « pas d'entraînement sur vos données » |
| Cloud & hébergement | AWS, Google Cloud, OVHcloud, Scaleway | Toutes les données hébergées | Région d'hébergement UE disponible ? activée ? |
| Paie & RH | PayFit, Silae, Lucca | Données salariés (sensibles : NIR, salaires) | Fiche RH obligatoire, durées légales spécifiques |
| Support client | Zendesk, Intercom, Crisp | Identité, échanges, métadonnées | Conversations = données personnelles, souvent oublié |
| E-commerce & paiement | Shopify, Stripe | Clients finaux, transactions | Rôle contrôleur/sous-traitant **ambigu** → à valider |

## 🚩 Les drapeaux

| Drapeau | Déclencheur | Action proposée |
|---|---|---|
| 🔴 Transfert hors UE | Siège ou hébergement hors UE détecté | Vérifier adéquation / clauses contractuelles types / annexes du DPA |
| 🟠 DPA à vérifier | Sous-traitant sans DPA connu signé | Retrouver la page DPA de l'éditeur, signer ou archiver |
| 🟡 Outil fantôme | Plus aucun débit depuis ≥ 6 mois | Confirmer l'abandon → sortir du registre + demande de suppression des données |
| 🟡 Éditeur masqué | Revendeur, marketplace, app store dans le libellé | Le skill demande quel produit se cache derrière — jamais de devinette |

## 📤 Formats de sortie (où atterrit le registre ?)

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown : synthèse sous-traitants, fiche par traitement, to-do priorisée | **Toujours** — c'est la base |
| **Registre imprimable** | Fichier/artifact **HTML** : en-tête responsable, fiches art. 30, annexe sous-traitants, to-do | Si l'hôte affiche les fichiers (artifacts claude.ai, Claude Desktop, Claude Code) ; sinon repli automatique sur les tableaux |
| **Bandeau disclaimer** | « Projet de registre, pas un avis juridique — à valider (DPO/juriste) » | Sur **chaque** sortie, sans exception |

## 🎬 Vidéo de démo

La démo ≤ 3 min jointe à la PR suit le storyboard : problème (le document que personne n'a) → scan des débits → classification & fiches → **le registre art. 30 complet généré depuis un relevé bancaire** → to-do DPA/transferts. Le script détaillé (textes à dire, checklist tournage) est dans **`_SCRIPT-VIDEO.md`** — fichier interne, **exclu de la PR**.

## 💡 Améliorations possibles (dans les clous du hackathon)

| Idée | Effort | Note |
|---|---|---|
| Multi-MCP optionnel : scan Gmail/Drive pour retrouver les DPA déjà signés | Moyen | Détection dynamique — s'active si le MCP est présent, sinon le skill le dit et continue |
| Diff de registre : relancer le skill 6 mois plus tard → nouveaux entrants / sortants | Faible | Réutilise la date de dernière apparition |
| Modèles de courrier « demande de DPA » et « demande de suppression » prêts à envoyer | Faible | Toujours zéro écriture — texte à copier |
| Annexe AIPD : signaler les traitements susceptibles d'exiger une analyse d'impact | Moyen | Toujours en « à valider », jamais de qualification définitive |

## ⚡ Optimisation terrain

La reconnaissance vient de la **culture générale de Claude**, pas d'une base de données : un SaaS est identifié dès sa **première occurrence** (siège, rôle de sous-traitant, données typiques), là où une heuristique de récurrence raterait l'outil payé à l'année. Et les factures fournisseurs (`list_supplier_invoices`) donnent des raisons sociales plus propres que les libellés carte — le skill croise les deux.

## 🛡 Garde-fous

- **Jamais de qualification juridique définitive** (sous-traitant vs responsable vs responsabilité conjointe, base légale, durées) — chaque fiche porte « à valider », les champs à décider restent des placeholders visibles
- Jamais de fait inventé sur un fournisseur : siège ou hébergement inconnu → dit inconnu, avec « vérifier la facture / la page DPA » comme étape suivante
- Un projet de registre ≠ la conformité RGPD : c'est une pièce obligatoire, pas tout le programme — validation DPO/juriste recommandée dans chaque rapport
- 100 % lecture, zéro écriture · IBAN masqués (4 derniers chiffres) · pagination ≤ 50 partout · tous les exemples des docs sont inventés

---

*Documentation FR (pilotage). Version jury : `README.en.md`. Livrable PR : `SKILL.md`. Procédure pas-à-pas : `docs/PROCEDURE.fr.md`. Docs riches : `docs/doc-qonto-rgpd-register.fr.html` · `docs/doc-qonto-rgpd-register.fr.docx`.*
