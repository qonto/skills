// ---------------------------------------------------------------------------
// Benchmark web (web app — surface de démo).
//
// Ici, Claude pilote l'outil serveur `web_search_20260209` : il choisit les
// requêtes, lit des sources publiques et renvoie des citations (URL + date).
//
// NB : la recherche Linkup « pour de vrai » (protocole MCP) vit dans le SKILL
// (`mcp__linkup__linkup-search`) — c'est la soumission jugée. Le web app est une
// vitrine et utilise la recherche web hébergée d'Anthropic.
//
// Deux règles respectées :
//   • Zéro PII (règle 3) : on n'envoie QUE le nom du marchand + sa catégorie.
//   • Chaque prix = source + date (règle 4) : sans source datée → « non vérifié ».
//
// Le calcul de l'économie N'EST PAS fait ici : la route/engine soustrait les
// prix. Le LLM ne fournit que de la donnée sourcée.
// ---------------------------------------------------------------------------

import Anthropic from "@anthropic-ai/sdk";
import type { Lang } from "./types";

const MODEL = process.env.ARGENTIER_MODEL || "claude-sonnet-5";
const WEB_SEARCH = { type: "web_search_20260209", name: "web_search", max_uses: 5 };

export interface BenchSource {
  title: string;
  url: string;
  date: string; // page_age brut (« 3 months ago », « April 2025 »…) ou ""
}

export interface BenchAlternative {
  name: string;
  /** Prix mensuel public en € (par utilisateur si SaaS), ou null si non chiffrable. */
  monthlyPrice: number | null;
  unit: string; // « /utilisateur/mois », « /mois »…
  sourceUrl: string;
  sourceDate: string;
}

export interface BenchmarkResult {
  merchant: string;
  verified: boolean;
  summary: string;
  sources: BenchSource[];
  alternatives: BenchAlternative[];
  note?: string;
  /** Qui a fait la recherche : Linkup (réel) ou la recherche web de Claude. */
  provider?: "linkup" | "claude";
}

export function hasAnthropicKey(): boolean {
  return !!process.env.ANTHROPIC_API_KEY;
}

export function hasLinkupKey(): boolean {
  return !!process.env.LINKUP_API_KEY;
}

function yearFrom(text: string): string {
  const m = text.match(/\b(20[12]\d)\b/);
  return m ? m[1] : "";
}

/**
 * Recherche via l'API Linkup (le même fournisseur que le MCP Linkup du skill).
 * On n'envoie que le nom du marchand + la catégorie (règle 3, zéro PII).
 */
async function searchLinkup(
  merchant: string,
  category: string,
  lang: Lang,
): Promise<{ summary: string; sources: BenchSource[] }> {
  const q =
    lang === "fr"
      ? `Quelles sont les 3 meilleures alternatives MOINS CHÈRES à "${merchant}" (catégorie : ${category}) en 2026 ? Pour chaque CONCURRENT (jamais ${merchant} lui-même), donne son nom, son prix mensuel public actuel (par utilisateur si applicable) et l'URL de sa page tarifs.`
      : `What are the 3 best CHEAPER alternatives to "${merchant}" (category: ${category}) in 2026? For each COMPETITOR (never ${merchant} itself), give its name, its current public monthly price (per user if applicable) and its pricing-page URL.`;

  const res = await fetch("https://api.linkup.so/v1/search", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${process.env.LINKUP_API_KEY}`,
      "Content-Type": "application/json",
    },
    // sourcedAnswer = réponse synthétisée (liste de concurrents + prix) + sources.
    // Bien plus exploitable par l'extraction que des snippets bruts (searchResults).
    body: JSON.stringify({ q, depth: "standard", outputType: "sourcedAnswer" }),
  });
  if (!res.ok) throw new Error(`Linkup ${res.status}`);

  const data = (await res.json()) as {
    answer?: string;
    sources?: Array<{ name?: string; url?: string; snippet?: string }>;
  };
  const srcs = (data.sources ?? []).filter((s) => s.url).slice(0, 6);
  const sources: BenchSource[] = srcs.map((s) => ({
    title: s.name ?? s.url!,
    url: s.url!,
    date: yearFrom(s.snippet ?? ""),
  }));
  const summary =
    (data.answer ?? "").trim() ||
    srcs.map((s) => `${s.name ?? ""}: ${(s.snippet ?? "").slice(0, 500)}`).join("\n\n");
  return { summary, sources };
}

const SYSTEM: Record<Lang, string> = {
  fr: `Tu es le module de benchmark d'Argentier. On te donne UNIQUEMENT le nom d'un
outil/service et sa catégorie — jamais de données personnelles, et tu n'en réclames pas.

Ta mission : trouver 2 à 3 alternatives moins chères à usage équivalent, avec leur
PRIX PUBLIC ACTUEL et la date de la source. Utilise la recherche web. Cite tes sources.
Donne des tarifs officiels (pages pricing, comparateurs récents), pas des estimations.
Si tu ne trouves pas de prix sourcé et daté, dis-le clairement — n'invente aucun chiffre.

Réponds en français, de façon concise : pour chaque alternative, son nom, le prix
(en précisant l'unité : /utilisateur/mois, /mois…) et d'où vient l'info.`,
  en: `You are Argentier's benchmark module. You are given ONLY a tool/service name and its
category — never any personal data, and you must not ask for any.

Your task: find 2–3 cheaper alternatives at equal usage, with their CURRENT PUBLIC PRICE
and the source date. Use web search. Cite your sources. Give official pricing (pricing
pages, recent comparison sites), not estimates. If you cannot find a sourced, dated price,
say so clearly — invent no figure.

Answer in English, concisely: for each alternative, its name, the price (state the unit:
/user/month, /month…) and where the information comes from.`,
  de: `Du bist das Benchmark-Modul von Argentier. Du erhältst AUSSCHLIESSLICH den Namen eines
Tools/Dienstes und seine Kategorie — nie personenbezogene Daten, und du forderst auch keine an.

Deine Aufgabe: 2 bis 3 günstigere Alternativen mit gleichwertigem Nutzen finden, mit ihrem
AKTUELLEN ÖFFENTLICHEN PREIS und dem Datum der Quelle. Nutze die Websuche. Zitiere deine Quellen.
Gib offizielle Preise an (Preisseiten, aktuelle Vergleichsportale), keine Schätzungen. Findest
du keinen belegten, datierten Preis, sage es klar — erfinde keine Zahl.

Antworte auf Deutsch, prägnant: für jede Alternative den Namen, den Preis (mit Einheit:
/Nutzer/Monat, /Monat…) und woher die Information stammt.`,
  es: `Eres el módulo de benchmark de Argentier. Se te da ÚNICAMENTE el nombre de una
herramienta/servicio y su categoría — nunca datos personales, y no debes pedirlos.

Tu misión: encontrar de 2 a 3 alternativas más baratas de uso equivalente, con su PRECIO
PÚBLICO ACTUAL y la fecha de la fuente. Usa la búsqueda web. Cita tus fuentes. Da tarifas
oficiales (páginas de precios, comparadores recientes), no estimaciones. Si no encuentras un
precio con fuente y fecha, dilo claramente — no inventes ninguna cifra.

Responde en español, de forma concisa: para cada alternativa, su nombre, el precio (indicando
la unidad: /usuario/mes, /mes…) y de dónde viene la información.`,
  it: `Sei il modulo di benchmark di Argentier. Ti viene fornito SOLO il nome di uno
strumento/servizio e la sua categoria — mai dati personali, e non devi chiederne.

Il tuo compito: trovare 2-3 alternative più economiche a uso equivalente, con il loro PREZZO
PUBBLICO ATTUALE e la data della fonte. Usa la ricerca web. Cita le tue fonti. Fornisci tariffe
ufficiali (pagine dei prezzi, comparatori recenti), non stime. Se non trovi un prezzo con fonte
e data, dillo chiaramente — non inventare alcuna cifra.

Rispondi in italiano, in modo conciso: per ogni alternativa, il nome, il prezzo (indicando
l'unità: /utente/mese, /mese…) e da dove proviene l'informazione.`,
};

const EXTRACT_SCHEMA = {
  type: "object",
  properties: {
    alternatives: {
      type: "array",
      items: {
        type: "object",
        properties: {
          name: { type: "string" },
          monthlyPrice: { type: ["number", "null"] },
          unit: { type: "string" },
          sourceIndex: { type: "integer" },
        },
        required: ["name", "monthlyPrice", "unit", "sourceIndex"],
        additionalProperties: false,
      },
    },
  },
  required: ["alternatives"],
  additionalProperties: false,
} as const;

const NOTE: Record<"noKey" | "webDown" | "noSource", Record<Lang, string>> = {
  noKey: {
    fr: "Non vérifié — clé Anthropic absente (benchmark désactivé).",
    en: "Not verified — Anthropic key missing (benchmark disabled).",
    de: "Nicht verifiziert — Anthropic-Schlüssel fehlt (Benchmark deaktiviert).",
    es: "No verificado — falta la clave de Anthropic (benchmark desactivado).",
    it: "Non verificato — chiave Anthropic assente (benchmark disattivato).",
  },
  webDown: {
    fr: "Non vérifié — recherche web indisponible.",
    en: "Not verified — web search unavailable.",
    de: "Nicht verifiziert — Websuche nicht verfügbar.",
    es: "No verificado — búsqueda web no disponible.",
    it: "Non verificato — ricerca web non disponibile.",
  },
  noSource: {
    fr: "Non vérifié — aucune source datée trouvée. Ne pas afficher de prix.",
    en: "Not verified — no dated source found. Do not display a price.",
    de: "Nicht verifiziert — keine datierte Quelle gefunden. Keinen Preis anzeigen.",
    es: "No verificado — no se encontró ninguna fuente con fecha. No mostrar precio.",
    it: "Non verificato — nessuna fonte datata trovata. Non mostrare il prezzo.",
  },
};

/**
 * Vrai/faux : l'alternative est en réalité le MÊME produit que le marchand
 * (ex. « HeyGen Pro » quand on benchmarke « HeyGen »). On veut des CONCURRENTS,
 * jamais le produit qu'on cherche à remplacer.
 */
function sameBrand(altName: string, merchant: string): boolean {
  const norm = (s: string) => s.toLowerCase().replace(/[^a-z0-9]+/g, "");
  const alt = norm(altName);
  // Marque = premier « mot » significatif du marchand (avant /, ×, +, espace…).
  const brand = norm((merchant.split(/[\s/×·+|(]+/)[0] || merchant));
  if (!alt || brand.length < 3) return false;
  return alt.includes(brand) || brand.includes(alt);
}

export async function benchmark(
  merchant: string,
  category: string,
  currentMonthly: number,
  lang: Lang = "fr",
): Promise<BenchmarkResult> {
  const base: BenchmarkResult = {
    merchant,
    verified: false,
    summary: "",
    sources: [],
    alternatives: [],
  };

  if (!hasAnthropicKey()) {
    return { ...base, note: NOTE.noKey[lang] };
  }

  const client = new Anthropic();

  // --- Passe 1 : recherche des prix ----------------------------------------
  // Linkup (réel) si LINKUP_API_KEY est présent, sinon la recherche web
  // hébergée de Claude. Le provider est renvoyé pour un affichage honnête.
  const provider: "linkup" | "claude" = hasLinkupKey() ? "linkup" : "claude";
  let summary: string;
  let sources: BenchSource[];
  try {
    if (provider === "linkup") {
      ({ summary, sources } = await searchLinkup(merchant, category, lang));
    } else {
      const search = (await client.messages.create({
        model: MODEL,
        max_tokens: 2000,
        tools: [WEB_SEARCH as unknown as Anthropic.Tool],
        system: [{ type: "text", text: SYSTEM[lang] }],
        messages: [
          {
            role: "user",
            content:
              lang === "fr"
                ? `Outil actuel : "${merchant}" (catégorie : ${category}). Coût constaté : environ ${Math.round(
                    currentMonthly,
                  )} €/mois. Trouve des alternatives moins chères à usage équivalent, avec prix public sourcé et daté.`
                : `Current tool: "${merchant}" (category: ${category}). Observed cost: about €${Math.round(
                    currentMonthly,
                  )}/month. Find cheaper alternatives at equal usage, with a sourced, dated public price.`,
          },
        ],
      } as unknown as Anthropic.MessageCreateParamsNonStreaming)) as Anthropic.Message;
      summary = search.content
        .filter((b): b is Anthropic.TextBlock => b.type === "text")
        .map((b) => b.text)
        .join("\n")
        .trim();
      sources = extractSources(search);
    }
  } catch (err) {
    console.error("Benchmark (passe 1) échoué :", err);
    return { ...base, provider, note: NOTE.webDown[lang] };
  }

  if (sources.length === 0) {
    return { ...base, provider, summary, note: NOTE.noSource[lang] };
  }

  // --- Passe 2 : extraction structurée (le prix devient de la donnée) ------
  let alternatives: BenchAlternative[] = [];
  try {
    const sourceList = sources
      .map((s, i) => `[${i}] ${s.title} — ${s.url} (${s.date || "date n.c."})`)
      .join("\n");

    const extract = (await client.messages.create({
      model: MODEL,
      max_tokens: 1500,
      output_config: { effort: "low", format: { type: "json_schema", schema: EXTRACT_SCHEMA } },
      system: [
        {
          type: "text",
          text:
            "Tu extrais des prix depuis un texte de benchmark et une liste de sources numérotées. " +
            "Pour chaque alternative citée, donne le prix mensuel en euros (null si non chiffré), " +
            "l'unité, et l'index [n] de la source qui l'atteste. N'invente aucun prix ni source. " +
            `IMPORTANT : ne retiens QUE des produits CONCURRENTS différents. Exclus totalement « ${merchant} » ` +
            "et ses propres formules/paliers de prix (Free, Pro, Business, annuel…) — on cherche à le remplacer, pas à le lister.",
        },
      ],
      messages: [
        {
          role: "user",
          content: `TEXTE :\n${summary}\n\nSOURCES :\n${sourceList}`,
        },
      ],
    } as unknown as Anthropic.MessageCreateParamsNonStreaming)) as Anthropic.Message;

    const txt = extract.content.find((b) => b.type === "text");
    if (txt && txt.type === "text") {
      const parsed = JSON.parse(txt.text) as {
        alternatives: Array<{ name: string; monthlyPrice: number | null; unit: string; sourceIndex: number }>;
      };
      alternatives = parsed.alternatives
        .filter((a) => !sameBrand(a.name, merchant))
        .map((a) => {
        const src = sources[a.sourceIndex] ?? sources[0];
        return {
          name: a.name,
          monthlyPrice: typeof a.monthlyPrice === "number" ? a.monthlyPrice : null,
          unit: a.unit || "/mois",
          sourceUrl: src?.url ?? "",
          sourceDate: src?.date ?? "",
        };
      });
    }
  } catch (err) {
    console.error("Benchmark (passe 2, extraction) échoué :", err);
    // On garde le résumé sourcé même sans extraction structurée.
  }

  return { merchant, verified: true, summary, sources, alternatives, provider };
}

// --- Extraction des sources (URL + date) depuis les blocs web_search -------
function extractSources(msg: Anthropic.Message): BenchSource[] {
  const byUrl = new Map<string, BenchSource>();

  for (const block of msg.content as unknown as Array<Record<string, unknown>>) {
    // Bloc résultat de recherche serveur
    if (block.type === "web_search_tool_result" && Array.isArray(block.content)) {
      for (const r of block.content as Array<Record<string, unknown>>) {
        const url = typeof r.url === "string" ? r.url : "";
        if (!url) continue;
        byUrl.set(url, {
          url,
          title: typeof r.title === "string" ? r.title : url,
          date: typeof r.page_age === "string" ? r.page_age : "",
        });
      }
    }
    // Citations attachées aux blocs de texte
    if (block.type === "text" && Array.isArray(block.citations)) {
      for (const c of block.citations as Array<Record<string, unknown>>) {
        const url = typeof c.url === "string" ? c.url : "";
        if (!url || byUrl.has(url)) continue;
        byUrl.set(url, {
          url,
          title: typeof c.title === "string" ? c.title : url,
          date: "",
        });
      }
    }
  }

  return [...byUrl.values()].slice(0, 6);
}
