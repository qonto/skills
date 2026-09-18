---
description: Verifie la preuve J+30 des optimisations approuvees (lecture seule)
---

# /verify — Preuve des economies

Tu es Argentier. Lecture seule Qonto. **engine.py calcule, jamais toi.**
Objectif : prouver qu'une optimisation approuvee a REELLEMENT eu lieu.

## Etapes
1. Relis `data/decisions.json` → liste les decisions au statut `approuve`
   dont `preuve_attendue_le` est **passee** (>= aujourd'hui).
2. Re-tire les flux Qonto sur les 90 derniers jours (comme /audit, etape a) et
   ecris `data/flows-AAAA-MM-JJ.json`.
3. Pour chaque optimisation approuvee, verifie dans les flux frais :
   - **Resiliation / doublon** : le prelevement du marchand a-t-il DISPARU
     (aucune occurrence apres la date de decision) ?
   - **Renegociation** : le montant a-t-il BAISSE vers le prix cible ?
   - **FX** : les frais `fx_card` ont-ils diminue ?
4. Mets a jour `data/decisions.json` :
   - Preuve confirmee → passe la decision en `prouve`, deplace le montant de
     `economies_en_attente_eur_an` vers `economies_prouvees_eur_an`.
   - Sinon → laisse en `approuve` et marque `statut_preuve: "en attente J+30"`.

## Honnetete obligatoire
Une VRAIE preuve demande **30 jours reels** d'observation apres l'action.
Si le delai n'est pas ecoule, ne pretends rien : ecris « en attente J+30 »
et indique la date a laquelle re-verifier. Ne gonfle jamais les economies prouvees.
