# PRD — Argentier en Autopilote

> **Une page. Une feature.** L'audit qui se déclenche seul, ne dérange l'humain
> qu'au moment de décider (1 tap), et se prouve tout seul ~30 jours après.
> Construit sur **Claude Managed Agents (CMA)**.

**Statut :** proposé · **Owner :** Kevin Mameri · **Cible :** V2 (post-hackathon)
· **Modèle éco :** agent gratuit, 5 % au succès sur les économies **prouvées**.

---

## 1. Problème

Aujourd'hui Argentier est *un outil qu'on lance* (`/audit` dans Claude Code).
Le risque n°1 n'est pas *trouver* des économies — l'engine le fait — c'est le
**gap entre trouver et agir** : dès qu'il faut penser à ouvrir une session, on
perd l'essentiel du funnel. 90 % des TPE n'ont pas de DAF *et* pas le réflexe de
piloter leurs finances. Il faut supprimer l'étape « ouvrir l'app ».

## 2. Solution (le magic moment)

```
J+0   Connexion Qonto (lecture seule), 2 min. Puis PLUS RIEN à faire.
J+2   Push : « 3 leviers → ~1 920 €/an. Ringover facturé 2× : je résilie
      le doublon ? »   [ Approuver ]  [ Refuser ]      ← 1 tap
J+32  Push : « Prouvé : −430 €. La charge a disparu. »
```

L'utilisateur n'a jamais rouvert l'app entre les deux. Argentier se réveille,
lit le compte, calcule (engine.py), benchmarke (Linkup), **se met en pause au
moment de la reco**, notifie, et reprend sur la décision.

## 3. User stories

- **En tant que** dirigeant de TPE, **je veux** qu'Argentier audite mon compte
  tout seul chaque mois **afin de** ne rien avoir à lancer.
- **…je veux** décider chaque action en 1 tap depuis une notif **afin de**
  garder le contrôle sans y passer du temps.
- **…je veux** une preuve chiffrée ~30 j après **afin de** savoir que
  l'économie a bien atterri (et ne payer qu'au succès).
- **…je veux** qu'un refus ne me soit jamais re-proposé.

## 4. Périmètre

**Dans la V1 (MVP) :**
- Deployment **cron mensuel** → audit read-only → engine → benchmark →
  **carte + gate async 1 tap** → écrit le draft → notif.
- Deployment **verify quotidien** (sweep) → toute décision dont la preuve est
  due passe `pending → proven` (ou reste `pending`).
- Gate = **Approuver / Refuser**. Un refus alimente `profile.json`.
- Ledger + profil persistés par client (memory store).

**Hors V1 (refus explicite) :**
- ❌ Envoi automatique de la lettre → on reste sur « PRÊT — À ENVOYER PAR TOI ».
  On monte l'échelle de délégation *après* avoir prouvé l'adoption.
- ❌ Écran de configuration → un autopilote qui demande de la config n'en est pas un.
- ❌ Nouveaux leviers (TVA, FX) → une seule boucle *trouver→décider→prouver*
  complète bat cinq leviers qui s'arrêtent à « trouver ».

## 5. Les 4 règles non négociables (inchangées)

1. **Read-only Qonto** — seuls les tools de lecture sont activés (allowlist).
2. **engine.py calcule, jamais le LLM** — tourne dans le sandbox de session.
3. **Zéro PII vers le web** — Linkup ne reçoit que marchand + catégorie.
4. **Prix = source + date** — sinon 1 retry puis « non vérifié ».

## 6. Métriques

- **North Star :** **€ prouvés / compte / an** (pas « trouvés » — *prouvés*).
- **Activation :** 1re action approuvée **sous 14 jours**.
- **Le KPI qu'on regarde chaque semaine :** taux **carte envoyée → décision reçue**
  (le drop-off *trouver → agir* est tout le business).
- **Garde-fou :** 0 appel à un tool d'écriture Qonto (doit rester à zéro).

## 7. Definition of Done

- [ ] Un compte de test reçoit un audit **sans intervention humaine** (cron).
- [ ] La session **se met en pause** sur la reco et notifie via webhook.
- [ ] Un tap Approuver → draft écrit dans les outputs + ledger `pending`.
- [ ] Un tap Refuser → `profile.json.refus_passes` mis à jour, jamais re-proposé.
- [ ] Le sweep verify fait passer une entrée `pending → proven` avec le delta réel.
- [ ] Aucun tool d'écriture Qonto n'est activé ni appelé (test CI).

## 8. Risques (grille Cagan) & mitigation

| Risque | Question | Mitigation avant scale |
|---|---|---|
| **Valeur** | Approuvent-ils sans rouvrir l'app ? | KPI carte→décision ; Wizard-of-Oz sur 10 comptes réels. |
| **Usabilité** | 1 tap dans une notif suffit-il ? | Prototype la notif avant d'automatiser le cron. |
| **Faisabilité** | Le gate async CMA tient-il (webhook, reconnect, idle race) ? | Patterns CMA documentés → risque faible ; voir spec. |
| **Viabilité** | Le fee au succès survit-il à la falaise « tout coupé » ? | La boucle verify = valeur récurrente → bascule abonnement an-2. |

## 9. Questions ouvertes

- Onboarding : consentement **egress benchmark** (marchand+catégorie) donné une
  fois pour garder la décision à 1 tap — à valider juridiquement.
- Canal de notif V1 : push app vs email (déep-link Approuver/Refuser signé).
- Fréquence d'audit : mensuelle par défaut, configurable plus tard.
