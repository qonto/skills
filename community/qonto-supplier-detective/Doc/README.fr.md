# 🕵️ qonto-supplier-detective — Le détective des factures fournisseurs

> **Skill #13** · Hackathon Qonto × Anthropic MCP (10-13/07/2026)
> **100 % lecture** — « le détective ne touche à rien, il te donne le dossier »

---

## 🎯 Le pitch

En PME, une fraction des paiements fournisseurs sont des erreurs — doublons, payés-deux-fois, trop-versés — et personne ne va jamais les chercher. Sur un compte actif, l'ordre de grandeur se compte vite en **centaines de factures fournisseurs** à passer au crible. Le skill traque 4 anomalies :

1. **Doublons de factures** — même fournisseur + même montant à quelques jours, ou même numéro de facture ; signal natif `has_duplicates` vérifié via `get_supplier_invoice` ; **abonnements écartés par détection de cadence** (même montant chaque mois ≠ doublon !)
2. **Payés-deux-fois** — 1 facture, 2 débits : le signal qui rapporte. Paiements partiels et acomptes reconnus comme légitimes (la somme des débits = le montant facturé, pas 2×)
3. **Écarts facture ↔ paiement** — payé plus que facturé au-delà de l'arrondi ; avoirs et remboursements vérifiés avant de conclure
4. **Vigie IBAN** 🚨 — un fournisseur connu qui change d'IBAN = **alerte sécurité** épinglée en tête de rapport : c'est le pattern n°1 de la fraude au RIB. Consigne systématique : **vérifier par téléphone au numéro connu** — jamais celui de l'email qui annonce le changement

Chaque anomalie sort avec ses preuves : numéro de facture, références des virements, dates, montant récupérable. Rien n'est affirmé — tout est « présomption, à vérifier », avec le dossier pour réclamer.

## 📋 Prérequis

| Prérequis | Détail | Obligatoire |
|---|---|---|
| Compte Qonto **production** | Exigence du hackathon ; le skill s'adapte à toute organisation (`get_organization` d'abord, zéro donnée en dur) | ✅ |
| Pays | **Aucune règle nationale requise** : les détecteurs comparent le compte à lui-même. Fonctionne sur tous les pays Qonto (FR, DE, ES, IT, AT, NL, BE, PT) | ℹ️ détecté |
| MCP Qonto connecté | Via le connecteur officiel (claude.ai / Claude Desktop), login OAuth | ✅ |
| Factures fournisseurs importées dans Qonto | Plus il y en a, plus la surface de détection est grande. Sans elles : passe « transactions seules » (débits jumeaux + vigie IBAN sur virements), annoncée clairement | ⭕ recommandé |
| Historique ≥ 6 mois | En dessous, la détection de cadence des abonnements et le suivi d'IBAN perdent en fiabilité — le skill le dit | ⭕ |

## ⚙️ Fonctionnement global

![Fonctionnement global](assets/flow.fr.png)

1. **Balayage complet** : toutes les factures fournisseurs (paginé ≤ 50 jusqu'au bout — la progression est résumée toutes les ~300 factures) + tous les débits sur 12-24 mois. Noms de fournisseurs **normalisés** (mentions SEPA, suffixes SARL/SAS/GmbH, espaces) pour que « OVH SAS », « OVH.COM » et « VIR SEPA OVH » fusionnent ; numéros de facture nettoyés ; **avoirs et remboursements identifiés d'emblée** — ce sont des pièces à décharge, pas des anomalies
2. **Doublons de factures** : signal natif `has_duplicates` + passe propre (même fournisseur + même montant à 45 jours, ou même numéro). **LE piège de faux positifs : les abonnements** — même montant chaque mois à cadence régulière = récurrence légitime, exclue avant tout signalement
3. **Payés-deux-fois** : une facture rapprochée de 2+ débits, ou deux factures jumelles payées chacune. Les paiements échelonnés sont blanchis d'abord (les débits *totalisent* le montant facturé) ; un vrai payé-deux-fois totalise ≈ 2× la facture
4. **Écarts facture ↔ paiement** : trop-versé présumé au-delà de 0,05 € d'arrondi, après recherche d'un avoir explicatif ; devises étrangères signalées « à vérifier », jamais accusées
5. **Vigie IBAN** 🚨 : l'IBAN de paiement est suivi par fournisseur ; un changement = alerte traitée comme un incident de sécurité, avec la bonne pratique anti-fraude au président : vérification téléphonique au numéro **déjà connu**
6. **Rapport de recouvrement** : anomalies classées par montant récupérable, total à réclamer estimé, cas blanchis affichés (abonnements, échelonnés, remboursements déjà reçus), e-mails de réclamation prêts à envoyer sur demande. **Zéro écriture.**

## 🏗 Schéma fonctionnel

![Schéma fonctionnel](assets/functional.fr.png)

**Le point clé** : tout est en trait plein — de la lecture, rien que de la lecture. Le skill n'appelle **aucun** outil d'écriture Qonto ; il n'a rien à faire approuver, rien à exécuter. Le seul « acte » se passe hors du compte : toi, au téléphone avec ton fournisseur, ou ton e-mail de réclamation. Le détective monte le dossier ; c'est toi qui plaides.

## 🕵️ Les 4 détecteurs — et les pièges qu'ils évitent

| Détecteur | Ce qu'il cherche | Le piège de faux positif écarté |
|---|---|---|
| D1 · Doublons | Même fournisseur + même montant à 45 j, ou même n° de facture ; `has_duplicates` natif | **Abonnements** : même montant chaque mois à cadence régulière = récurrence, pas doublon |
| D2 · Payés-deux-fois | 1 facture ↔ 2+ débits ; 2 jumelles payées chacune | **Paiements partiels / acomptes** : les débits totalisent la facture (≠ 2×) ; remboursement déjà reçu = cas clos |
| D3 · Écarts | Payé > facturé au-delà de l'arrondi (0,05 €) | **Avoirs** expliquant l'écart ; devises étrangères → « à vérifier (change) » |
| D4 · Vigie IBAN 🚨 | Fournisseur connu payé sur IBAN A → soudain IBAN B | **Changement de banque légitime** : l'alerte demande une vérification, elle n'accuse pas — mais toujours **avant le prochain paiement** |

## 🎬 Vidéo de démo

La démo ≤ 3 min jointe à la PR suit le storyboard : problème → balayage (le volume à l'écran) → dossier d'anomalies + alerte IBAN → **le payé-deux-fois chiffré avec son e-mail de réclamation prêt** → wrap-up 100 % lecture. Le script détaillé (textes à dire, checklist tournage, notes de montage) est conservé en interne (hors dépôt).

## 📤 Formats de sortie (où atterrit le dossier ?)

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Rapport markdown : alertes IBAN 🚨 en tête, tableau d'anomalies trié par montant récupérable, total estimé, cas blanchis | **Toujours** — c'est la base |
| **Dossier interactif** | Fichier/artifact **HTML** : tableau des anomalies, cartes de preuves, jauge du récupérable, bandeau alerte IBAN | Si l'hôte affiche les fichiers (artifacts claude.ai, Claude Desktop, Claude Code) ; sinon repli automatique sur le markdown |
| **E-mail de réclamation** | Brouillon prêt à envoyer : n° de facture, les 2 références de virement, dates, montant — IBAN masqués | Sur demande, anomalie par anomalie |

## 💡 Améliorations possibles (dans les clous du hackathon)

| Idée | Effort | Note |
|---|---|---|
| Envoi de la réclamation via un MCP Gmail détecté dynamiquement | Faible | Multi-MCP optionnel — le cœur reste Qonto pur |
| Marquage des factures litigieuses (`change_supplier_invoice_status`) | Moyen | Sortirait du 100 % lecture — à assumer comme option explicite |
| Détection post-résiliation (héritée de P10) : un abonnement qui continue après une résiliation annoncée | Moyen | Réutilise la détection de cadence |
| Audit périodique programmé (trimestriel) avec diff vs le rapport précédent | Faible | La vigie IBAN devient un vrai monitoring |
| Rapprochement multi-devises avec taux du jour | Moyen | Transforme les « à vérifier (change) » en verdicts |

## 🛡 Garde-fous

- **100 % lecture** : aucun outil d'écriture Qonto appelé, jamais — rien à approuver, rien d'exécuté
- Discipline de vocabulaire : « présomption », « à vérifier » — jamais « fraude » ou « erreur » affirmées ; chaque anomalie montre ses preuves
- L'alerte IBAN porte **toujours** la consigne : vérifier par téléphone au numéro connu, jamais via les coordonnées de l'email qui annonce le changement
- Abonnements, échelonnés, acomptes, avoirs et remboursements sont blanchis **avant** tout signalement — une fausse accusation coûte plus cher en confiance qu'un doublon en euros
- IBAN masqués (4 derniers chiffres) ; pagination ≤ 50 partout ; progression résumée sur les gros volumes

---

*Documentation FR (pilotage). Version jury : `README.en.md`. Livrable PR : `SKILL.md`. Procédure pas-à-pas : `docs/PROCEDURE.fr.md`. Docs riches : `docs/doc-qonto-supplier-detective.fr.html` · `docs/doc-qonto-supplier-detective.fr.docx`.*
