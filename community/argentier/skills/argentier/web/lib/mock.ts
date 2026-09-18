// ---------------------------------------------------------------------------
// Données mock — servies par /api/analyze quand Qonto/Anthropic ne sont pas
// configurés. Calées sur une analyse réelle, au format AnalyzeResult exact.
// ---------------------------------------------------------------------------

import type { AnalyzeResult } from "./types";

export const MOCK: AnalyzeResult = {
  account: { name: "MAMFORMA", bank: "Qonto", balance: 7646 },
  window: { label: { fr: "20 mai – 19 juin 2026", en: "May 20 – June 19, 2026" } },
  totals: { out: 14114, runRate: 1510 },
  natures: [
    { key: "structurel", label: "Structurel", amount: 8108 },
    { key: "ponctuel", label: "Ponctuel", amount: 2907 },
    { key: "perso", label: "Perso", amount: 1589 },
    { key: "pilotable", label: "Pilotable", amount: 1510 },
  ],
  poles: [
    { label: "Outbound / Sales", amount: 592 },
    { label: "IA & Dev", amount: 327 },
    { label: "Marketing Ads", amount: 313 },
    { label: "Bureau / Telco / Banque", amount: 156 },
    { label: "Infra / Prod", amount: 122 },
  ],
  score: {
    value: 72,
    drivers: [
      { fr: "Doublons fonctionnels (2 LLM) −8", en: "Functional duplicates (2 LLMs) −8" },
      { fr: "Justificatifs TVA manquants −8", en: "Missing VAT receipts −8" },
      { fr: "Part optimisable du run-rate −12", en: "Optimizable share of run-rate −12" },
    ],
  },
  runway: { months: 5.1, note: { fr: "hors exceptionnel", en: "excl. one-offs" } },
  levers: [
    { id: "inst", label: "Instantly", to: "1 seul workspace", saving: 80, risk: "med", active: true, action: "consolidate" },
    { id: "gpt", label: "ChatGPT", to: "Claude seul", saving: 78, risk: "safe", active: true, action: "cancel" },
    { id: "waa", label: "Waalaxy", to: "Apollo + Instantly", saving: 47, risk: "safe", active: true, action: "switch" },
    { id: "fx", label: "Frais FX / ATM", to: "carte Wise / Revolut", saving: 40, risk: "safe", active: true, action: "switch" },
    { id: "nesp", label: "Nespresso abo", to: "achat ponctuel", saving: 39, risk: "safe", active: true, action: "cancel" },
    { id: "figma", label: "Figma", to: "revenir au tarif / renégo", saving: 5, risk: "safe", active: true, action: "renegotiate", monthly: 45, hausse: { pct: 12.5, avantEur: 40, apresEur: 45 } },
    { id: "gw", label: "Google Workspace ×2", to: "1 compte", saving: 27, risk: "safe", active: true, action: "consolidate" },
    { id: "repl", label: "Replit", to: "Claude Code + Cursor", saving: 28, risk: "med", active: true, action: "switch" },
    { id: "hey", label: "HeyGen", to: "pause / annuel", saving: 26, risk: "safe", active: true, action: "downgrade" },
    { id: "loom", label: "Loom", to: "capture native", saving: 21, risk: "safe", active: true, action: "cancel" },
    { id: "uber", label: "Uber One", to: "couper", saving: 6, risk: "safe", active: true, action: "cancel" },
    { id: "make", label: "Make", to: "n8n self-hosted", saving: 9, risk: "med", active: false, action: "switch" },
    { id: "ring", label: "Ringover", to: "renégo forfait", saving: 60, risk: "hard", active: false, action: "renegotiate" },
    { id: "hub", label: "HubSpot", to: "Pipedrive / Folk", saving: 50, risk: "hard", active: false, action: "switch" },
  ],
  flux: [
    {
      kind: "new",
      label: { fr: "HeyGen · nouvel abonnement", en: "HeyGen · new subscription" },
      value: { fr: "26 €/mois", en: "€26/mo" },
      tone: "amber",
    },
    {
      kind: "check",
      label: { fr: "Virement région IDF · à vérifier", en: "IDF region transfer · to review" },
      value: { fr: "234 €", en: "€234" },
      tone: "neutral",
    },
    {
      kind: "dup",
      label: {
        fr: "Doublon : 2 LLM payants (Claude + ChatGPT)",
        en: "Duplicate: 2 paid LLMs (Claude + ChatGPT)",
      },
      value: { fr: "−78 €/mois", en: "−€78/mo" },
      tone: "danger",
    },
    {
      kind: "ghost",
      label: { fr: "CapCut · abo dormant, plus prélevé", en: "CapCut · dormant subscription, no longer charged" },
      value: { fr: "à confirmer", en: "to confirm" },
      tone: "neutral",
    },
  ],
  tvaPerdue: { transactions: 3, baseTtcEur: 360, tvaRecuperableEur: 60 },
  meta: { source: "mock", categorized: "rules", txCount: 0 },
};
