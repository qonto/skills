// ---------------------------------------------------------------------------
// Catégorisation des marchands via Claude (PRD §5.2).
//
// RÈGLE : le LLM CLASSE (nature, pôle, action, risque, ratio d'économie).
// Il ne calcule JAMAIS un montant en euros — c'est engine.ts qui multiplie.
//
// Sans ANTHROPIC_API_KEY, on retombe sur un classifieur déterministe par
// mots-clés (categorizeByRules) : l'app reste démontrable hors-ligne.
// ---------------------------------------------------------------------------

import Anthropic from "@anthropic-ai/sdk";
import type { MerchantVerdict, Nature, Pole, Risk, LeverAction } from "./types";

const MODEL = process.env.ARGENTIER_MODEL || "claude-sonnet-5";

const NATURES: Nature[] = ["pilotable", "structurel", "ponctuel", "perso"];
const POLES: Pole[] = [
  "IA & Dev",
  "Outbound / Sales",
  "Infra / Prod",
  "Marketing Ads",
  "Bureau / Telco / Banque",
  "Perso",
  "Sous-traitance",
  "Certif",
  "Voyage",
  "Autre",
];
const ACTIONS: LeverAction[] = [
  "keep",
  "cancel",
  "downgrade",
  "switch",
  "consolidate",
  "renegotiate",
];

export interface MerchantInput {
  name: string;
  occurrences: number;
  monthlyEstimate: number; // indicatif, aide le LLM à juger — pas recalculé par lui
  isRecurring: boolean;
}

const SYSTEM = `Tu es le moteur de catégorisation d'Argentier, un agent d'optimisation
financière pour TPE et entreprises individuelles françaises clientes de Qonto.

Pour chaque marchand fourni, tu renvoies une classification. Tu ne calcules AUCUN
montant en euros : un moteur déterministe s'en charge. Tu fournis seulement des
étiquettes et, pour les outils pilotables optimisables, un ratio d'économie.

Les 4 natures de flux :
- "pilotable" : abonnements SaaS, outils, télécom, frais bancaires. C'est là qu'on optimise.
- "structurel" : prélèvements du dirigeant, sous-traitants, salaires, charges sociales,
  certifications, assurances pro. On pilote mais on ne coupe pas.
- "ponctuel" : voyages, gros achats isolés, échéances fiscales. Exclu du run-rate récurrent.
- "perso" : dépenses personnelles (courses, resto perso, streaming perso) sur un compte EI.

Pour un marchand pilotable, propose une "action" seulement si une optimisation crédible existe :
- "consolidate" : doublon fonctionnel (2 outils qui font la même chose) → savingRatio ~0.5.
- "downgrade" : plan surdimensionné → savingRatio ~0.3.
- "switch" : alternative moins chère à usage égal → savingRatio selon l'écart (0.2 à 0.6).
- "cancel" : outil dormant ou superflu → savingRatio 1.0.
- "renegotiate" : contrat renégociable (télécom, banque) → savingRatio ~0.2.
- "keep" : rien à optimiser, alternative = "", savingRatio = 0.
Le risque : "safe" (sans perte de capacité), "med" (à valider), "hard" (projet, changement lourd).
Ne propose jamais de couper un outil manifestement critique (banque, assurance obligatoire).`;

const SCHEMA = {
  type: "object",
  properties: {
    verdicts: {
      type: "array",
      items: {
        type: "object",
        properties: {
          name: { type: "string" },
          nature: { type: "string", enum: NATURES },
          pole: { type: "string", enum: POLES },
          isSubscription: { type: "boolean" },
          action: { type: "string", enum: ACTIONS },
          alternative: { type: "string" },
          savingRatio: { type: "number" },
          risk: { type: "string", enum: ["safe", "med", "hard"] },
        },
        required: [
          "name",
          "nature",
          "pole",
          "isSubscription",
          "action",
          "alternative",
          "savingRatio",
          "risk",
        ],
        additionalProperties: false,
      },
    },
  },
  required: ["verdicts"],
  additionalProperties: false,
} as const;

export function hasAnthropicKey(): boolean {
  return !!process.env.ANTHROPIC_API_KEY;
}

/** Classifieur LLM. Renvoie un verdict par marchand fourni. */
export async function categorizeWithClaude(
  merchants: MerchantInput[],
): Promise<MerchantVerdict[]> {
  const client = new Anthropic();

  const userPayload = merchants.map((m) => ({
    name: m.name,
    occurrences: m.occurrences,
    montant_mensuel_indicatif_eur: Math.round(m.monthlyEstimate),
    recurrent: m.isRecurring,
  }));

  // Structured outputs (output_config.format) : le champ peut ne pas être typé
  // selon la version du SDK — on cast les params, la réponse reste un Message.
  const params = {
    model: MODEL,
    max_tokens: 8000,
    output_config: {
      effort: "low",
      format: { type: "json_schema", schema: SCHEMA },
    },
    system: [{ type: "text", text: SYSTEM, cache_control: { type: "ephemeral" } }],
    messages: [
      {
        role: "user",
        content:
          "Classe chacun de ces marchands. Renvoie un verdict par marchand, même ordre.\n\n" +
          JSON.stringify(userPayload, null, 2),
      },
    ],
  };

  const response = (await client.messages.create(
    params as unknown as Anthropic.MessageCreateParamsNonStreaming,
  )) as Anthropic.Message;

  const text = response.content.find((b) => b.type === "text");
  if (!text || text.type !== "text") throw new Error("Réponse Claude vide");
  const parsed = JSON.parse(text.text) as { verdicts: MerchantVerdict[] };
  return sanitize(parsed.verdicts, merchants);
}

/** Garantit un verdict par marchand attendu (le LLM peut en oublier). */
function sanitize(verdicts: MerchantVerdict[], expected: MerchantInput[]): MerchantVerdict[] {
  const byName = new Map(verdicts.map((v) => [v.name.toLowerCase(), v]));
  return expected.map(
    (m) => byName.get(m.name.toLowerCase()) ?? ruleVerdict(m),
  );
}

// --- Fallback déterministe (pas de clé Anthropic) --------------------------
const PERSO = [
  "carrefour", "monoprix", "leclerc", "franprix", "auchan", "lidl", "intermarche",
  "grand frais", "boulangerie", "mcdonald", "starbucks", "uber eats", "deliveroo",
  "netflix", "spotify", "disney", "nespresso", "pharmacie", "zara", "h&m", "sephora",
];
const PILOTABLE = [
  "hubspot", "apollo", "ringover", "google workspace", "gsuite", "notion", "slack",
  "aws", "github", "gitlab", "stripe", "ovh", "scaleway", "figma", "zoom", "openai",
  "anthropic", "claude", "chatgpt", "vercel", "make", "zapier", "airtable", "instantly",
  "waalaxy", "loom", "replit", "skool", "webflow", "heygen", "capcut", "mailjet",
  "free mobile", "bouygues", "uber one", "mailchimp", "canva",
];
const STRUCTUREL = ["hiscox", "urssaf", "impot", "salaire", "sous-trait", "certif", "inkrea", "assur"];
const VOYAGE = ["sofitel", "air france", "booking", "sncf", "hotel", "uber", "airbnb"];

const POLE_HINTS: Array<[RegExp, Pole]> = [
  [/hubspot|apollo|instantly|waalaxy|pipedrive|salesforce|mailjet|mailchimp/, "Outbound / Sales"],
  [/openai|anthropic|claude|chatgpt|replit|github|gitlab|cursor|make|zapier/, "IA & Dev"],
  [/meta|google ads|facebook|tiktok ads/, "Marketing Ads"],
  [/aws|ovh|scaleway|vercel|cloudflare/, "Infra / Prod"],
  [/ringover|free mobile|bouygues|orange|sfr|qonto|google workspace/, "Bureau / Telco / Banque"],
];

function classifyRule(name: string): { nature: Nature; pole: Pole } {
  const n = name.toLowerCase();
  if (STRUCTUREL.some((k) => n.includes(k))) return { nature: "structurel", pole: "Certif" };
  if (VOYAGE.some((k) => n.includes(k))) return { nature: "ponctuel", pole: "Voyage" };
  if (PERSO.some((k) => n.includes(k))) return { nature: "perso", pole: "Perso" };
  if (PILOTABLE.some((k) => n.includes(k))) {
    const hit = POLE_HINTS.find(([re]) => re.test(n));
    return { nature: "pilotable", pole: hit ? hit[1] : "IA & Dev" };
  }
  return { nature: "ponctuel", pole: "Autre" };
}

function ruleVerdict(m: MerchantInput): MerchantVerdict {
  const { nature, pole } = classifyRule(m.name);
  let action: LeverAction = "keep";
  let alternative = "";
  let savingRatio = 0;
  let risk: Risk = "safe";
  if (nature === "pilotable" && m.isRecurring) {
    action = "renegotiate";
    alternative = "revoir le plan / le tarif";
    savingRatio = 0.2;
    risk = "med";
  }
  return {
    name: m.name,
    nature,
    pole,
    isSubscription: m.isRecurring && nature === "pilotable",
    action,
    alternative,
    savingRatio,
    risk,
  };
}

export function categorizeByRules(merchants: MerchantInput[]): MerchantVerdict[] {
  return merchants.map(ruleVerdict);
}

// ---------------------------------------------------------------------------
// Classification EI PRO / PERSO / A-CLARIFIER — MIROIR EXACT de engine.py.
//
// Règle #2 du projet : engine.py fait foi. Le périmètre « TVA perdue » ne
// compte QUE les dépenses classées PRO (whitelist PRO_KEYWORDS, jamais
// A-CLARIFIER ni « perso »). On réplique ici la même liste de mots-clés et la
// même fonction classify() pour que engine.ts produise le MÊME résultat
// qu'engine.py sur les mêmes transactions.
// ---------------------------------------------------------------------------
export const PRO_KEYWORDS = [
  "hubspot", "apollo", "ringover", "google workspace", "google gsuite",
  "notion", "slack", "aws", "amazon web services", "github", "gitlab",
  "linkedin", "stripe", "ovh", "scaleway", "figma", "zoom", "microsoft",
  "adobe", "openai", "anthropic", "vercel", "cloudflare", "sentry",
  "calendly", "typeform", "mailchimp", "mailjet", "sendgrid", "twilio",
  "make", "make.com", "zapier", "airtable", "pipedrive", "salesforce",
  "intercom", "canva", "webflow", "instantly", "waalaxy", "loom", "replit",
  "skool", "hiscox",
];

export const PERSO_KEYWORDS = [
  "zara", "h&m", "uniqlo", "restaurant", "uber eats", "deliveroo",
  "just eat", "carrefour", "monoprix", "leclerc", "franprix", "auchan",
  "lidl", "intermarche", "boulangerie", "mcdonald", "starbucks", "fnac",
  "decathlon", "sephora", "ikea", "netflix", "spotify", "disney+",
  "pharmacie", "nespresso", "barber", "action",
];

export type EiClass = "PRO" | "PERSO" | "A-CLARIFIER";

/**
 * Miroir de engine.py:classify() — PRO l'emporte sur PERSO, défaut A-CLARIFIER.
 * Source de vérité partagée pour le périmètre de la TVA perdue (règle #2).
 */
export function classifyEI(name: string): EiClass {
  const n = name.toLowerCase().replace(/\s+/g, " ").trim();
  if (PRO_KEYWORDS.some((k) => n.includes(k))) return "PRO";
  if (PERSO_KEYWORDS.some((k) => n.includes(k))) return "PERSO";
  return "A-CLARIFIER";
}
