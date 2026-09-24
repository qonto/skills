# Argentier

Agent d'optimisation bancaire et fiscale pour TPE, freelances et EI, branché sur Qonto.
**Ton vrai run-rate, pas ton relevé.**

Argentier lit le compte **en lecture seule**, sépare les 4 natures de flux
(pilotable / structurel / ponctuel / perso), chiffre ce qui est récupérable et le
rend actionnable en un écran : hero « tu peux récupérer X €/an », score de santé,
runway, simulateur de leviers, fil d'anomalies.

## Architecture (le principe non négociable)

> **Le LLM classe, `engine.ts` calcule.** Claude étiquette chaque marchand
> (nature, pôle, action, ratio d'économie). Tout montant en euros est calculé par
> le moteur déterministe. Le LLM ne multiplie jamais.

```
Qonto (lecture seule)  ─▶  categorize.ts (Claude : étiquettes)  ─▶  engine.ts (€)  ─▶  /api/analyze  ─▶  front
        lib/qonto.ts            lib/categorize.ts                    lib/engine.ts      app/api/analyze     app/Argentier.tsx
```

| Fichier | Rôle |
|---|---|
| `lib/types.ts` | Le contrat d'API (fait foi entre front et back). |
| `lib/qonto.ts` | Client Qonto REST v2 — **GET uniquement**, normalisation. |
| `lib/categorize.ts` | Catégorisation Claude (`claude-sonnet-5`) + fallback règles. |
| `lib/engine.ts` | Moteur déterministe : natures, run-rate, pôles, score, runway, leviers, anomalies. |
| `lib/letters.ts` | Lettres de résiliation / renégociation via Claude + gabarit de secours. |
| `lib/export.ts` | Export du plan en CSV (Excel FR). |
| `lib/mock.ts` | Données de démo (fallback sans clés). |
| `app/api/analyze/route.ts` | Orchestration OBSERVE → CATÉGORISE → CALCULE. |
| `app/api/letter/route.ts` | Prépare un courrier prêt à envoyer pour un levier. |
| `app/Argentier.tsx` | Le front d'entrée (hero, ledger, simulateur, anomalies, lettres). |
| `app/rapport/page.tsx` | Rapport imprimable (→ PDF via impression). |

## Démarrer

```bash
npm install
cp env.example .env.local    # optionnel : renseigner les clés
npm run dev                  # http://localhost:3000
```

**Sans clés**, l'app tourne en mode démo (données mock) — démontrable en pitch.
**Avec les clés** (`.env.local`), elle analyse le vrai compte :

```env
ANTHROPIC_API_KEY=sk-ant-...     # sans : catégorisation par règles (mots-clés)
QONTO_LOGIN=...                  # Qonto → Paramètres → Intégrations → API
QONTO_SECRET_KEY=...
QONTO_IBAN=FR76...               # compte à analyser
```

Vérifs :

```bash
npm run typecheck
npm run build
```

## Ce qu'Argentier NE fait pas

- Aucune action bancaire : pas de paiement, pas de résiliation automatique.
  Il conseille et prépare ; **c'est toi qui agis** (PRD §3, §5.8).
- Aucune donnée utilisée pour entraîner un modèle. Traitement en Europe.
- Conseils fiscaux = pistes à valider avec un comptable.

## Roadmap (extrait PRD §13)

- **M0 (démo)** — front + `/api/analyze` branché Qonto, données réelles, sans persistance. ✅
- **M1 (MVP)** — export CSV + lettres de résiliation/renégociation + rapport PDF ✅ · auth (magic link), persistance Postgres, freemium ⏳
- **M2** — multi-banque (Bridge/Powens), benchmarking anonymisé, suivi des économies réalisées, pricing à la performance.

### Couche « passage à l'action » (M1, livrée)

- **Export du plan** — bouton *Exporter le plan (CSV)* → téléchargement Excel-compatible (BOM UTF-8).
- **Rapport imprimable** — `/rapport` → *Imprimer / Enregistrer en PDF*.
- **Lettres prêtes à envoyer** — l'icône ✎ sur chaque levier ouvre un courrier rédigé par Claude
  (résiliation / renégociation / consolidation selon l'action), éditable, avec bouton *Copier*.
  Argentier prépare, **tu envoies** : aucun envoi automatique, `[crochets]` à compléter.

## Modèle Claude

La catégorisation utilise `claude-sonnet-5` (configurable via `ARGENTIER_MODEL`),
conformément au PRD §6. Structured outputs (`output_config.format`) garantissent un
JSON valide ; le LLM ne renvoie que des étiquettes, jamais des euros.
