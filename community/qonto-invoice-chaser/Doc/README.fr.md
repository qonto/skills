# 📨 qonto-invoice-chaser — Relancer juste, encaisser plus vite

> **Skill #4** · Hackathon Qonto × Anthropic MCP (10-13/07/2026)
> Relancer juste, encaisser plus vite — la relance d'impayés qui vérifie la banque avant d'écrire

---

## 🎯 Le pitch

Une facture B2B française est payée en moyenne avec **plus de 11 jours de retard** — et la relance est la corvée que tout le monde repousse : gênante, répétitive, vite oubliée. `qonto-invoice-chaser` transforme le compte Qonto en chargé de recouvrement qui ne froisse personne :

1. **Détection des impayés** — factures clients en retard (`due_date`), ancienneté calculée, encours total, aging 0-30 / 31-60 / 60+ jours
2. **Croisement avec les encaissements réels** — une facture « unpaid » peut être **déjà payée** (virement hors lien de paiement, jamais marquée) : le skill rapproche montant / contrepartie / référence et **propose** `mark_client_invoice_as_paid` — il ne relance JAMAIS une facture dont l'argent est déjà arrivé
3. **Profil payeur & relance graduée** — bon payeur en retard exceptionnel ≠ retardataire chronique : le ton s'adapte à l'historique. Rappel courtois (~J+7) → relance ferme (~J+21) → mise en demeure (~J+45) avec intérêts de retard et **indemnité forfaitaire de 40 €** (art. L441-10 C. com)
4. **Brouillon Gmail** — si le MCP Gmail est connecté, la relance atterrit en **brouillon** dans Gmail : tu relis, tu envoies. Sinon, texte prêt à copier. Rien ne part jamais tout seul.

## 📋 Prérequis

| Prérequis | Détail | Obligatoire |
|---|---|---|
| Compte Qonto **production** | Exigence du hackathon ; le skill s'adapte à toute organisation (`get_organization` d'abord, zéro donnée en dur) | ✅ |
| Pays | **Kit juridique complet (intérêts + 40 €, art. L441-10) : France.** Autres pays Qonto (DE, ES, IT…) : relances graduées identiques, référence générique à la directive UE 2011/7 — jamais de taux ou de formule juridique inventés | ℹ️ détecté |
| MCP Qonto connecté | Via le connecteur officiel (claude.ai / Claude Desktop), login OAuth | ✅ |
| Factures clients dans Qonto | Le skill lit `list_client_invoices` ; sans facturation Qonto, il n'a rien à relancer et le dit | ✅ |
| MCP Gmail | Optionnel, détecté dynamiquement : présent → brouillons de relance ; absent → texte prêt à copier | ⭕ recommandé |
| Historique de facturation | Nourrit le profil payeur ; sans historique, ton standard + avertissement | ⭕ |

## ⚙️ Fonctionnement global

![Fonctionnement global](assets/flow.fr.png)

1. **Détection des impayés** : `list_client_invoices` (statuts impayés, pagination ≤ 50) → ancienneté par facture, encours total, aging 0-30 / 31-60 / 60+
2. **Croisement encaissements** : chaque facture « unpaid » est confrontée aux transactions créditrices réelles (`list_transactions`) — montant exact ±0,01, contrepartie ≈ nom du client, référence contenant le numéro de facture
3. **Marquage proposé** : correspondance forte → le skill **montre la transaction** et propose `mark_client_invoice_as_paid` ; cas ambigus (paiement partiel, virement groupé) → candidats présentés, jamais de marquage automatique
4. **Profil payeur** : factures réglées, retard moyen, tendance → 🟢 fiable en retard exceptionnel · 🟡 occasionnel · 🔴 chronique — annoncé en une ligne (« 24 factures, toujours réglées, retard moyen 5 j → ton chaleureux »)
5. **Relance graduée** rédigée avec les chiffres exacts (numéro, montant TTC, jours de retard, intérêts calculés) — voir l'échelle ci-dessous
6. **Brouillon Gmail & rapport** : brouillon créé (MCP présent) ou texte à copier, puis rapport encours / aging / DSO / prochaines relances

## 🏗 Schéma fonctionnel

![Schéma fonctionnel](assets/functional.fr.png)

**Le point clé de confiance** : la lecture (trait plein) ne présente aucun risque ; les deux écritures (trait pointillé) sont des actions *proposées* — le marquage « payée » exige la confirmation explicite dans la conversation, et la relance n'existe qu'en **brouillon** que toi seul relis et envoies. Le skill rédige ; toi, tu décides.

## 📨 L'échelle de relance (France, B2B)

| Étape | Quand | Registre | Contenu obligatoire |
|---|---|---|---|
| **Rappel courtois** | ~J+7 | Chaleureux, présume l'oubli | N° de facture, montant TTC, date d'échéance, moyen de paiement indiqué sur la facture |
| **Relance ferme** | ~J+21 | Ferme, factuel | Idem + jours de retard, rappel de la 1ère relance, annonce de l'étape suivante |
| **Mise en demeure** | ~J+45 | Formel, juridique | Idem + intérêts de retard (taux contractuel, sinon BCE + 10 pts, plancher 3× taux légal) calculés au jour près + **indemnité forfaitaire de 40 €** par facture (art. L441-10 & D441-5 C. com) + délai de règlement + recommandation d'envoi en LRAR |

Le ton se décale selon le profil : un 🟢 bon payeur garde le registre le plus chaleureux plus longtemps ; un 🔴 chronique ne l'a jamais — sans jamais devenir agressif. L'objectif : être payé **et** garder le client.

## 📤 Formats de sortie (où atterrit la relance ?)

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown (encours, aging, table d'action par facture) | **Toujours** — c'est la base |
| **Brouillon Gmail** | Email complet (destinataire, objet avec n° de facture, corps personnalisé) dans les brouillons | Si le MCP Gmail est connecté ; sinon repli automatique sur texte à copier |
| **Texte prêt à copier** | Objet + corps, à coller dans n'importe quel client mail | Sans MCP Gmail |
| **Dashboard interactif** | Fichier/artifact **HTML** : barres d'aging, top retardataires, pipeline de relances | Si l'hôte affiche les fichiers ; sinon repli sur les tableaux |

## 🎬 Vidéo de démo

La démo ≤ 3 min jointe à la PR suit le storyboard : problème → scan + croisement (la facture déjà payée détectée) → profil payeur → **le brouillon qui apparaît dans Gmail avec les chiffres exacts** → rapport d'encours. Le script détaillé (textes à dire, checklist tournage, notes de montage) est conservé en interne (hors dépôt).


## 💡 Améliorations possibles (dans les clous du hackathon)

| Idée | Effort | Note |
|---|---|---|
| Lien de paiement dans la relance (`create_payment_link`) | Faible | Le client paie en un clic depuis l'email — les payment links marchent malgré la doc MCP |
| Kits juridiques par pays (DE · ES · IT · AT · NL · BE · PT) | Moyen | Transposition de la directive 2011/7/UE propre à chaque pays |
| Rythme automatique (relance du lundi matin planifiée) | Faible | Le rituel devient un rendez-vous |
| Cycle complet order-to-cash (devis → facture → encaissement) | Moyen | Réutilise l'héritage P4 en amont du chasseur |

## 🛡 Garde-fous

- **Jamais** de marquage « payée » sans montrer la transaction et obtenir la confirmation explicite dans la conversation
- **Jamais** d'envoi d'email de sa propre initiative : brouillons par défaut, envoi direct uniquement sur demande explicite — jamais présenté comme envoyé s'il ne l'est pas
- Sous le seuil de confiance du matching : question plutôt qu'action — relancer un client qui a payé coûte plus cher qu'une question
- Calculs juridiques France uniquement, informatifs, pas un conseil juridique — relecture pro recommandée avant mise en demeure
- Répétitions : client fictif + factures draft + `delete_client_invoice` ; brouillons Gmail de test nettoyés
- IBAN masqués (4 derniers chiffres) ; pagination ≤ 50 partout

---

*Documentation FR (pilotage). Version jury : `README.en.md`. Livrable PR : `SKILL.md`. Procédure pas-à-pas : `docs/PROCEDURE.fr.md`. Docs riches : `docs/doc-qonto-invoice-chaser.fr.html` · `docs/doc-qonto-invoice-chaser.fr.docx`.*
