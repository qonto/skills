# ⚖️ qonto-injonction — Quand la relance ne suffit plus, le dossier de justice prêt à signer

> **Hackathon Qonto × Anthropic MCP (10-13/07/2026)** · Agent Skill pour le MCP Qonto
> **Zéro écriture, par conception** : le skill s'arrête au dossier prêt à signer — aucun acte juridique n'est jamais exécuté par le skill. C'est une feature.

---

## 🎯 Le pitch

Les relances ont échoué (voir `qonto-invoice-chaser`), la mise en demeure est restée lettre morte. L'étape suivante — l'**injonction de payer** — est simple sur le papier (~35 € de frais de greffe, sans avocat) mais presque personne n'ose : formulaire CERFA intimidant, intérêts à calculer, tribunal à identifier, pièces à numéroter. `qonto-injonction` fait tout ça depuis le compte Qonto :

1. **Vérification BODACC d'abord** (API publique, sans clé) — si le débiteur est en procédure collective, PAS d'injonction : le skill réoriente vers la **déclaration de créance** (délai 2 mois) et la rédige
2. **Créance chiffrée au jour près** — principal (acomptes déduits), **intérêts de retard** (taux BCE + 10 points, plancher 3× le taux légal — art. L441-10 C. com.), **indemnité forfaitaire de 40 €** (art. D441-5), formule affichée
3. **CERFA 12946 pré-rempli champ par champ** + **bordereau de pièces numéroté** (facture, relances, mise en demeure — récupérées des justificatifs Qonto) + **tribunal compétent** identifié depuis le siège du débiteur
4. **Mode d'emploi Infogreffe** — dépôt dématérialisé, ~35 €, pièces en PDF < 2 Mo, et la suite (ordonnance → signification → opposition 1 mois)

## 📋 Prérequis

| Prérequis | Détail | Obligatoire |
|---|---|---|
| Compte Qonto **production** | Le skill s'adapte à toute organisation (`get_organization` d'abord, zéro donnée en dur) | ✅ |
| Pays | **Procédure CERFA : France.** Autres pays Qonto (DE, ES, IT…) : dossier factuel complet (non-paiement prouvé, intérêts directive UE 2011/7, pièces) mais **sans formulaire** — jamais de forme ni de taux étranger inventé | ℹ️ détecté |
| MCP Qonto connecté | Connecteur officiel (claude.ai / Claude Desktop), login OAuth | ✅ |
| Accès web (APIs publiques, sans clé) | BODACC + recherche-entreprises.api.gouv.fr. Sans accès web : le skill demande les 2 infos manquantes au lieu de deviner | ⭕ recommandé |
| Relance amiable déjà faite | Mise en demeure envoyée (LRAR) — sinon le skill conseille de passer d'abord par `qonto-invoice-chaser` | ⭕ conseillé |
| SIREN du débiteur | Dans la fiche client Qonto ; sinon recherché par nom + ville et **confirmé par toi** (homonymes) | ⭕ |

## ⚙️ Fonctionnement global

![Fonctionnement global](assets/flow.fr.png)

1. **Cibler la facture** : facture impayée choisie avec toi (`list_client_invoices`, `get_client_invoice`), identité du débiteur (`get_client`) — SIREN confirmé, jamais supposé
2. **Prouver le non-paiement** : scan des crédits (`list_transactions` depuis l'émission) — aucun encaissement ne matche ; les paiements partiels sont détectés et **déduits du principal** ; facture contestée → avertissement (l'injonction fera opposition)
3. **Vérification BODACC** : SIREN cherché dans les annonces de procédures collectives. Procédure ouverte → **STOP injonction**, bascule en déclaration de créance (2 mois à compter de la publication BODACC, art. L622-24)
4. **Tribunal compétent** : siège social du débiteur via recherche-entreprises.api.gouv.fr → greffe du tribunal de commerce compétent (art. 1406 CPC) ; état administratif de la société vérifié au passage
5. **Chiffrer la créance** : principal − acomptes + intérêts (taux contractuel, sinon BCE + 10 pts, plancher 3× le taux légal, taux du semestre affiché) + 40 € par facture — chaque euro justifié, calcul détaillé
6. **Dossier prêt à signer** : CERFA 12946 pré-rempli champ par champ, bordereau P1-P6 (justificatifs récupérés via `get_attachment`, pièces manquantes listées « à fournir »), mode d'emploi Infogreffe

## 🏗 Schéma fonctionnel

![Schéma fonctionnel](assets/functional.fr.png)

**Le point clé** : ce skill est **100 % lecture**. Il lit Qonto et deux APIs publiques sans clé, calcule, assemble — et s'arrête. Aucun outil d'écriture n'est utilisé : rien n'est déposé, rien n'est signifié, rien n'est signé. Le dépôt sur Infogreffe, c'est toi, avec ta signature. **Aucun acte juridique n'est jamais exécuté par une IA — par conception.**

## ⚖️ Les deux routes (le skill choisit la bonne)

| Situation du débiteur | Route | Ce que le skill produit | Délai clé |
|---|---|---|---|
| **In bonis** (rien au BODACC) | Injonction de payer (art. 1405 s. CPC) | CERFA 12946 pré-rempli + bordereau + calcul + guide Infogreffe (~35 €) | Prescription 5 ans (art. L110-4) — voir `qonto-prescription-guard` |
| **Procédure collective** (sauvegarde, RJ, LJ) | Déclaration de créance (art. L622-24) | Relevé de créance rédigé : principal, intérêts arrêtés au jugement, pièces, adresse du mandataire si publiée | **2 mois** après publication BODACC |
| Société radiée / introuvable | Ni l'une ni l'autre | Constat + conseil de consulter un professionnel | — |

## 💶 Le calcul des intérêts (indicatif, à faire valider)

| Poste | Règle | Exemple (inventé) : facture INV-2026-017, 4 800 € TTC, 92 j de retard |
|---|---|---|
| Principal | Total TTC − acomptes prouvés | 4 800,00 € |
| Intérêts | Taux contractuel, sinon **BCE + 10 pts** (plancher 3× taux légal), du lendemain de l'échéance au dépôt, /365 | 4 800 × 12,15 % × 92/365 ≈ **147,00 €** (taux illustratif) |
| Indemnité | **40 €** par facture (art. D441-5) | 40,00 € |
| **Total réclamé** | | **≈ 4 987,00 €** |

## 📤 Formats de sortie

| Sortie | Format | Quand |
|---|---|---|
| **Réponse dans la conversation** | Tableaux markdown : créance chiffrée, pré-remplissage CERFA champ→valeur, bordereau ✅/📋, bandeau de route (injonction / déclaration de créance) | **Toujours** — c'est la base |
| **Dossier imprimable** | Fichier/artifact **HTML** : page de garde, calcul, CERFA pré-rempli, bordereau — à enregistrer en PDF | Si l'hôte affiche les fichiers ; sinon repli automatique sur les tableaux |
| **Pièces du bordereau** | Justificatifs Qonto récupérés (`get_attachment`) + liste « à fournir » pour le reste | À chaque dossier |

## 🎬 Vidéo de démo

La démo ≤ 3 min jointe à la PR suit le storyboard : problème → preuve du non-paiement + vérification BODACC → calcul des intérêts + tribunal → **le dossier complet prêt à signer** → dépôt Infogreffe. Le script détaillé (textes à dire, checklist tournage) est dans **`_SCRIPT-VIDEO.md`** — fichier interne, **exclu de la PR**.

## 💡 Améliorations possibles (dans les clous du hackathon)

| Idée | Effort | Note |
|---|---|---|
| Injonction de payer européenne (formulaire A, règlement 1896/2006) | Moyen | Pour les débiteurs dans un autre État membre — même moteur de calcul |
| Suivi post-dépôt : rappel de la signification (6 mois) et de l'opposition (1 mois) | Faible | Réutilise l'horloge de `qonto-prescription-guard` |
| Multi-factures : une requête par débiteur regroupant N factures | Faible | Le bordereau et le calcul savent déjà empiler |
| Brouillon d'email au greffe / au commissaire de justice si un MCP email est présent | Faible | Multi-MCP optionnel, détecté dynamiquement |

## 🛡 Garde-fous

- **Pas un avis juridique** — rappelé sur chaque dossier ; intérêts = calcul indicatif à faire valider (avocat, commissaire de justice, greffe)
- **Zéro écriture** : jamais présenté comme déposé, signifié ou obtenu — le skill s'arrête au dossier prêt à signer
- Débiteur en procédure collective → jamais d'injonction proposée ; réorientation systématique vers la déclaration de créance
- Créance contestée ou proche de la prescription → signalé, jamais tu
- Procédure France uniquement ; ailleurs, dossier factuel sans formulaire
- IBAN masqués (4 derniers chiffres) · pagination ≤ 50 · exemples inventés (INV-YYYY-NNN)

---

*Documentation FR (pilotage). Version jury : `README.en.md`. Livrable PR : `SKILL.md`. Procédure pas-à-pas : `docs/PROCEDURE.fr.md`. Docs riches : `docs/doc-qonto-injonction.fr.html` · `docs/doc-qonto-injonction.fr.docx`.*
