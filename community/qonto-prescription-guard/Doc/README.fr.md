# ⏳ qonto-prescription-guard — Chaque facture impayée a une date de mort légale

> **Hackathon Qonto × Anthropic MCP (10-13/07/2026)** · Agent Skill pour le MCP Qonto
> **100 % lecture — zéro écriture.** Le skill analyse et alerte ; il ne touche à rien.
> ⚖️ Ce n'est **pas un avis juridique** : dates prudentes à valider avec un juriste avant d'agir (ou de renoncer).

---

## 🎯 Le pitch

Une facture impayée ne meurt pas quand tu l'oublies — elle meurt quand la **prescription** tombe : **5 ans entre commerçants** (art. L110-4 C. com.), **2 ans contre un consommateur** (art. L218-2 C. conso). Passé ce délai, plus aucune action en justice possible. Et le piège inverse existe aussi : un **paiement partiel** vaut reconnaissance de dette et **réinitialise le compteur** — des créances que tu croyais mortes sont peut-être encore vivantes. `qonto-prescription-guard` met une date de péremption sur chaque créance :

1. **Scan complet** — toutes les factures clients impayées, sur tout l'historique (les vieilles factures sont précisément le sujet)
2. **Qualification B2B/B2C** — SIREN ou n° de TVA sur la fiche client → commerçant probable (5 ans) ; sinon le skill **demande** — jamais de certitude sur la qualification, elle change tout
3. **Actes interruptifs** — paiement partiel repéré dans les transactions → « délai probablement réinitialisé le [date] — à confirmer avec un juriste » ; reconnaissance de dette ou action en justice → déclarées par toi
4. **Échéancier « agir avant le… »** — date limite par créance, temps restant, tri urgence × montant : 🔴 < 6 mois · 🟠 < 12 mois · 🟡 < 2 ans · 🟢 au-delà · ⚫ probablement prescrite

## 📋 Prérequis

| Prérequis | Détail | Obligatoire |
|---|---|---|
| Compte Qonto **production** | Le skill s'adapte à toute organisation (`get_organization` d'abord, zéro donnée en dur) | ✅ |
| Pays | **Règles de prescription : France uniquement.** Autres pays Qonto (DE, ES, IT…) : dégradation propre — rapport d'ancienneté des créances, sans qualification légale, jamais de règle inventée | ℹ️ détecté |
| MCP Qonto connecté | Via le connecteur officiel (claude.ai / Claude Desktop), login OAuth | ✅ |
| Facturation clients dans Qonto | Le skill lit `list_client_invoices` — les factures émises hors Qonto ne sont pas vues | ✅ |
| Fiches clients renseignées | SIREN / n° de TVA sur les fiches → qualification B2B automatique ; sinon le skill pose la question | ⭕ recommandé |
| Rien d'autre | 0 écriture, 0 sous-compte, 0 consentement à donner : il n'y a rien à approuver | — |

## ⚙️ Fonctionnement global

![Fonctionnement global](assets/flow.fr.png)

1. **Inventaire des créances** : `list_client_invoices` en statut impayé, paginé ≤ 50, sur tout l'historique — montant restant dû, date d'émission, date d'échéance, client
2. **Qualification B2B/B2C** par fiche client (heuristique annoncée : SIREN/TVA → commerçant probable ; ambigu → le skill demande et calcule **les deux dates** en attendant, la plus courte en avant)
3. **Règles embarquées en statique** (aucune dépendance externe) : 5 ans L110-4 / 2 ans L218-2, point de départ prudent = date d'émission (art. 2224 C. civ.), interruption = reconnaissance de dette, paiement partiel, action en justice (art. 2240-2244) — et surtout : **une lettre de relance, même recommandée, n'interrompt RIEN** (l'idée reçue n°1)
4. **Actes interruptifs** : paiements partiels détectés dans `list_transactions` (rapprochement tiers/référence/montant, heuristique annoncée comme telle) + actes déclarés par toi (reconnaissance écrite, injonction de payer)
5. **Calcul de la date de mort** : départ + délai, réinitialisé au dernier acte interruptif — temps restant, buckets 🔴🟠🟡🟢⚫
6. **Rapport & passage à l'action** : tableau trié urgence × montant, totaux à risque à 6/12 mois, renvoi vers `qonto-invoice-chaser` (relance amiable) ou vers un commissaire de justice si l'échéance approche

## 🏗 Schéma fonctionnel

![Schéma fonctionnel](assets/functional.fr.png)

**Le point clé** : tout est en trait plein (lecture seule). Ce skill ne crée rien, ne modifie rien, ne demande aucun consentement d'écriture — il n'y a littéralement rien à approuver. Le risque n'est pas dans l'outil, il est dans le calendrier : c'est le temps qui agit, pas le skill.

## ⚖️ Règles de prescription embarquées (France)

| Situation | Délai | Base légale |
|---|---|---|
| Créance entre commerçants (ou née de l'activité commerciale du débiteur) | **5 ans** | art. L110-4 Code de commerce |
| Professionnel contre **consommateur** (particulier, usage non professionnel) | **2 ans** | art. L218-2 Code de la consommation |
| Point de départ | Jour où le créancier a connu les faits — pour une facture, prudemment la **date d'émission** (choix conservateur : ne jamais surestimer le temps restant) | art. 2224 Code civil |
| Interruption → **le délai repart à zéro** | Reconnaissance de dette (un **paiement partiel** vaut reconnaissance tacite), demande en justice, acte d'exécution forcée | art. 2240-2244 Code civil |
| ⚠️ N'interrompt PAS | Relances, emails, mise en demeure même recommandée | jurisprudence constante |

À savoir : après interruption, un **nouveau délai de même durée** court (art. 2231) ; la prescription doit être soulevée par le débiteur, le juge ne l'applique pas d'office (art. 2247) — mais en pratique, traite la date comme la mort de la créance.

## 📤 Formats de sortie

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown : échéancier « agir avant le… », totaux à risque, réinitialisations détectées | **Toujours** — c'est la base |
| **Timeline interactive** | Fichier/artifact **HTML** : une barre par créance (départ → date de mort), marqueur « aujourd'hui », couleur par urgence, largeur par montant | Si l'hôte affiche les fichiers (artifacts claude.ai, Claude Desktop, Claude Code) ; sinon repli automatique sur les tableaux |
| **Liste « probablement prescrites »** | Section séparée du rapport, jamais mélangée aux créances vivantes | À chaque scan |

## 🎬 Vidéo de démo

La démo ≤ 3 min jointe à la PR suit le storyboard : le problème (la mort silencieuse des créances) → le scan et l'échéancier → le moment fort : **un paiement partiel détecté qui ressuscite une facture qu'on croyait morte** → le rapport final et le pipeline avec `qonto-invoice-chaser`. Le script détaillé de tournage est conservé en interne (hors dépôt).

## 🔗 Pipeline avec les autres skills

`qonto-invoice-chaser` relance à l'amiable ; `qonto-prescription-guard` dit **jusqu'à quand** la relance amiable a un sens et quand il faut passer au juridique. Ensemble : **relancer → agir en justice → ne jamais laisser mourir une créance**. Rappel structurant : les relances de `qonto-invoice-chaser` **n'interrompent pas** la prescription — raison de plus pour surveiller les deux.

## 💡 Améliorations possibles (dans les clous du hackathon)

| Idée | Effort | Note |
|---|---|---|
| Rappels calendrier « agir avant le… » (MCP calendrier détecté dynamiquement) | Faible | Multi-MCP optionnel — s'active si présent, sinon le skill le dit et continue |
| Modules pays (DE : 3 ans §195 BGB, ES, IT…) | Moyen | Même moteur, tables de délais par pays |
| Suivi des suspensions (médiation, art. 2238 C. civ.) | Moyen | Déclaratif — affine les dates |
| Brouillon de courrier pour le commissaire de justice | Faible | Sortie texte, toujours 0 écriture MCP |

## 🛡 Garde-fous

- **Pas un avis juridique** — chaque rapport le dit : dates prudentes, à valider avec un juriste/commissaire de justice avant d'agir ou de renoncer
- **Jamais de certitude sur la qualification B2C** : toujours présentée comme une hypothèse à confirmer (un indépendant qui achète pour son activité → retour aux 5 ans)
- Heuristique des actes interruptifs **annoncée comme telle** : « paiement partiel détecté le [date] → délai probablement réinitialisé — à confirmer avec un juriste » ; les paiements hors Qonto et les reconnaissances écrites sont invisibles → le skill demande
- Une créance « probablement prescrite » n'est jamais déclarée définitivement morte (suspensions possibles) — ni définitivement vivante
- France uniquement pour les dates légales ; ailleurs → ancienneté simple, annoncée clairement
- 100 % lecture · IBAN masqués (4 derniers chiffres) · pagination ≤ 50 partout
- Tous les exemples de cette documentation sont **inventés** (numéros au format INV-YYYY-NNN, montants fictifs)

---

*Documentation FR (pilotage). Version jury : `README.en.md`. Livrable PR : `SKILL.md`. Procédure pas-à-pas : `docs/PROCEDURE.fr.md`. Docs riches : `docs/doc-qonto-prescription-guard.fr.html`.*
