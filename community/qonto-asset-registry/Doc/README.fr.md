# 🗄 qonto-asset-registry — Le registre du matériel que personne ne tient

> **Hackathon Qonto × Anthropic MCP (10-13/07/2026)** · Agent Skill pour le MCP Qonto
> **100 % lecture** : le registre s'écrit tout seul, ton comptable garde le stylo.

---

## 🎯 Le pitch

Personne ne tient le registre des immobilisations. Et le jour du vol ou du sinistre, l'assureur demande **l'inventaire avec les valeurs d'achat et les justificatifs** — que personne n'a. Pourtant, ton compte Qonto sait déjà tout ce que tu possèdes. `qonto-asset-registry` le lit :

1. **Détection des équipements** dans 24-36 mois d'achats réels (transactions + factures fournisseurs) — informatique, mobilier, machines, véhicules, outillage, téléphonie, reconnus par la culture générale de Claude **dès la première occurrence** (enseignes spécialisées, libellés de factures)
2. **Seuil des 500 € HT** — tolérance fiscale française : en dessous = charge, au-dessus = immobilisation (seuil configurable) ; leasing/LOA détecté et signalé « financé, pas immobilisé ici », jamais compté
3. **Registre des immobilisations** — date, fournisseur, description, montant HT/TTC, **justificatif lié** (pièce jointe de la transaction), statut — avec jauge de complétude des justificatifs
4. **Deux sorties en or** — les **amortissements indicatifs** (durées usuelles, linéaire, valeur nette comptable estimée — à valider par l'expert-comptable) et **l'inventaire assurance** prêt à transmettre, avant d'en avoir besoin

## 📋 Prérequis

| Prérequis | Détail | Obligatoire |
|---|---|---|
| Compte Qonto **production** | Le skill s'adapte à toute organisation (`get_organization` d'abord, zéro donnée en dur) | ✅ |
| Pays | **Mécanique universelle.** Le seuil 500 € HT et les durées d'amortissement sont la pratique **française** ; autres pays Qonto (DE, ES, IT…) → registre et inventaire assurance sans suggestion fiscale, annoncé clairement | ℹ️ détecté |
| MCP Qonto connecté | Connecteur officiel (claude.ai / Claude Desktop), login OAuth | ✅ |
| Historique 24-36 mois | En dessous, le registre est présenté comme partiel, période couverte annoncée | ⭕ |
| Justificatifs joints aux transactions | Plus il y en a, plus l'inventaire est solide ; les manquants sont listés 📎 (renvoi vers `qonto-receipt-hunter`) | ⭕ |

## ⚙️ Fonctionnement global

![Fonctionnement global](assets/flow.fr.png)

1. **Scan des achats** (24-36 mois, débits, pagination ≤ 50, fenêtres de 3 mois) + `list_supplier_invoices` — les libellés de factures fournisseurs sont souvent plus propres que ceux des transactions, rapprochés par montant et date. Achats carte datés par `emitted_at` (le règlement traîne 1-2 jours)
2. **Reconnaissance des équipements** par la culture générale de Claude, **dès la première occurrence** — pas besoin de récurrence pour reconnaître un revendeur informatique ou un fournisseur de mobilier. Marchand généraliste ambigu → ligne « ❓ à confirmer », jamais devinée. Paiements en plusieurs fois rapprochés en un seul actif
3. **Seuil des 500 € HT** (configurable) : charge ou immobilisation ; leasing/LOA (mensualités récurrentes chez un financeur) signalé « 🔁 financé, pas immobilisé ici »
4. **Justificatifs liés** : `list_transaction_attachments` + `get_attachment` par actif ; manquant → 📎 avec renvoi vers `qonto-receipt-hunter` ; jauge de complétude calculée
5. **Amortissements indicatifs** : durées usuelles (tableau ci-dessous), linéaire, valeur nette comptable estimée, date de fin — des usages, pas des écritures comptables
6. **Registre + inventaire assurance** : tableaux dans la conversation, dashboard HTML si l'hôte affiche les fichiers, transmission au cabinet via `qonto-accountant-handoff`

## 🏗 Schéma fonctionnel

![Schéma fonctionnel](assets/functional.fr.png)

**Le point clé** : ce skill est **100 % lecture** — aucun outil d'écriture n'est appelé, jamais. Aucune catégorie modifiée, aucun document envoyé, aucune demande créée. Il lit, il calcule, il présente. La décision comptable (immobiliser, amortir, sortir un actif) reste entièrement chez toi et ton expert-comptable.

## 📅 Durées d'amortissement usuelles (pratique française, indicatif)

| Catégorie | Durée usuelle | Exemples |
|---|---|---|
| Informatique | 3 ans | Ordinateurs, écrans, serveurs, imprimantes |
| Téléphonie | 3 ans | Smartphones, standard, casques pro |
| Outillage | 5 ans | Outillage d'atelier, électroportatif |
| Machines | 5-10 ans | Machines de production, gros équipement |
| Véhicules | 4-5 ans | Voitures, utilitaires, deux-roues |
| Mobilier | 10 ans | Bureaux, sièges, rayonnages |

Chaque ligne du registre porte un statut : ✅ immobilisation · 💰 charge (< seuil) · ❓ à confirmer · 🔁 financé (leasing) · 📎 justificatif manquant. Les cessions et mises au rebut sont **déclarées par l'utilisateur, jamais supposées**.

## 📤 Formats de sortie (où atterrit le registre ?)

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown : registre trié par catégorie/valeur, amortissements, résumé (N actifs · valeur totale · jauge justificatifs) | **Toujours** — c'est la base |
| **Dashboard / export** | Fichier/artifact **HTML autoportant** charte Qonto : registre par catégorie, jauge de complétude des justificatifs, total assuré, frise d'amortissement | Si l'hôte affiche les fichiers ; repli automatique sur les tableaux |
| **Inventaire assurance** | Tableau prêt à transmettre : description, date d'achat, valeur d'achat, référence du justificatif | À la demande, ou après un sinistre |

## 🎬 Vidéo de démo

La démo ≤ 3 min jointe à la PR suit le storyboard : le problème (l'inventaire que l'assureur exige et que personne n'a) → le scan → le registre avec justificatifs liés → le moment « tout est déjà là » → dashboard et inventaire assurance. Le script détaillé de tournage est conservé en interne (hors dépôt).

## 💡 Améliorations possibles (dans les clous du hackathon)

| Idée | Effort | Note |
|---|---|---|
| Modules pays (seuils et durées DE · ES · IT · AT · NL · BE · PT) | Moyen | La mécanique est déjà universelle ; il ne manque que les pratiques locales |
| Détection des cessions par crédit entrant (revente de matériel) proposée à confirmation | Moyen | Toujours confirmé par l'utilisateur, jamais supposé |
| Rapprochement avec un inventaire physique (photos, étiquettes) | Moyen | L'inventaire assurance devient opposable |
| Alerte de fin d'amortissement (renouvellement à budgéter) | Faible | Réutilise les dates de fin déjà calculées |
| Export CSV pour le cabinet comptable | Faible | En complément de `qonto-accountant-handoff` |

## 🛡 Garde-fous

- **100 % lecture** — aucun outil d'écriture appelé, jamais
- Le seuil 500 € HT et les durées d'amortissement sont des **usages indicatifs, pas des écritures comptables** — décision finale à l'expert-comptable, rappelé dans chaque rapport
- Nature ambiguë (marchand généraliste) → « à confirmer », jamais inventée ; cessions/mises au rebut déclarées par l'utilisateur, jamais supposées
- Les montants d'exemple sont inventés et annoncés comme tels · IBAN masqués (4 derniers chiffres) · pagination ≤ 50 partout

---

*Documentation FR (pilotage). Version jury : `README.en.md`. Livrable PR : `SKILL.md`. Procédure pas-à-pas : `docs/PROCEDURE.fr.md`. Docs riches : `docs/doc-qonto-asset-registry.fr.html` · `docs/doc-qonto-asset-registry.fr.docx`.*
