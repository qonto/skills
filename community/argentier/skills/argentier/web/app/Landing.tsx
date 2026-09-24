"use client";

/**
 * Landing — page principale du site (le pitch, façon page marketing).
 * Palette inspirée de qonto.com : fond quasi-noir, texte blanc, accent jaune.
 * Bouton « Voir la démo » → l'app Argentier (MAMFORMA · Qonto).
 */

import React, { useEffect, useState } from "react";
import type { Lang } from "@/lib/types";
import { detectLang, PITCH } from "@/lib/i18n";

// Rend **gras** dans un texte.
function emph(text: string, key: string): React.ReactNode[] {
  return text.split("**").map((seg, i) =>
    i % 2 === 1 ? <strong key={`${key}-${i}`}>{seg}</strong> : <React.Fragment key={`${key}-${i}`}>{seg}</React.Fragment>,
  );
}

const FLAGS: Record<Lang, string> = { fr: "🇫🇷", en: "🇬🇧", de: "🇩🇪", es: "🇪🇸", it: "🇮🇹" };
const L = (lang: Lang, m: Record<Lang, string>) => m[lang] ?? m.en;

export default function Landing({ onDemo }: { onDemo: () => void }) {
  const [lang, setLang] = useState<Lang>("fr");
  const [joined, setJoined] = useState(false);
  const [email, setEmail] = useState("");
  // Gate email au clic « Voir la démo » → stocké dans Cloudflare KV.
  const [gate, setGate] = useState(false);
  const [demoEmail, setDemoEmail] = useState("");
  const [sending, setSending] = useState(false);

  const WAITLIST_URL = "https://argentier-mcp.bonjour-e83.workers.dev/waitlist";
  const storeEmail = async (address: string, source: string) => {
    try {
      await fetch(WAITLIST_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: address.trim().toLowerCase(), lang, source }),
      });
    } catch {
      /* réseau — on ne bloque pas l'utilisateur */
    }
  };
  const submitDemo = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!demoEmail.includes("@")) return;
    setSending(true);
    await storeEmail(demoEmail, "voir-demo");
    setSending(false);
    onDemo();
  };

  useEffect(() => {
    const saved = typeof window !== "undefined" ? window.localStorage.getItem("argentier-lang") : null;
    setLang((["fr", "en", "de", "es", "it"] as Lang[]).includes(saved as Lang) ? (saved as Lang) : detectLang(navigator.language));
  }, []);
  const changeLang = (l: Lang) => {
    setLang(l);
    try {
      window.localStorage.setItem("argentier-lang", l);
    } catch {
      /* noop */
    }
  };

  const p = PITCH[lang];

  return (
    <div className="lp">
      <style>{CSS}</style>

      <header className="lp-nav">
        <span className="lp-brand">
          <Mark /> Argentier
        </span>
        <div className="lp-nav-right">
          <div className="lp-langs" role="group" aria-label="Language">
            {(["fr", "en", "de", "es", "it"] as Lang[]).map((l) => (
              <button
                key={l}
                className={"lp-lang" + (lang === l ? " on" : "")}
                onClick={() => changeLang(l)}
                aria-pressed={lang === l}
                title={l.toUpperCase()}
              >
                {FLAGS[l]}
              </button>
            ))}
          </div>
          <button className="lp-demo-top" onClick={() => setGate(true)}>
            {L(lang, { fr: "Voir la démo", en: "See the demo", de: "Demo ansehen", es: "Ver la demo", it: "Vedi la demo" })} →
          </button>
        </div>
      </header>

      {/* Hero */}
      <section className="lp-hero">
        <span className="lp-eyebrow">
          {L(lang, {
            fr: "L'agent DAF autonome pour ton compte Qonto",
            en: "The autonomous CFO agent for your Qonto account",
            de: "Der autonome CFO-Agent für dein Qonto-Konto",
            es: "El agente director financiero autónomo para tu cuenta Qonto",
            it: "L'agente CFO autonomo per il tuo conto Qonto",
          })}
        </span>
        <h1 className="lp-title">{p.tagline}</h1>
        <p className="lp-sub">
          {L(lang, {
            fr: "Il lit ton compte en lecture seule, trouve l'argent qui fuit, et prouve chaque euro économisé. Tu approuves en 1 tap — il ne bouge jamais d'argent.",
            en: "It reads your account read-only, finds the money leaking out, and proves every euro saved. You approve in 1 tap — it never moves money.",
            de: "Es liest dein Konto nur lesend, findet das versickernde Geld und beweist jeden gesparten Euro. Du gibst mit einem Tap frei — es bewegt nie Geld.",
            es: "Lee tu cuenta en modo solo lectura, encuentra el dinero que se fuga y demuestra cada euro ahorrado. Apruebas en 1 toque — nunca mueve dinero.",
            it: "Legge il tuo conto in sola lettura, trova i soldi che si disperdono e dimostra ogni euro risparmiato. Approvi in 1 tap — non muove mai denaro.",
          })}
        </p>
        <div className="lp-cta">
          <button className="lp-demo" onClick={() => setGate(true)}>
            {L(lang, { fr: "Voir la démo", en: "See the demo", de: "Demo ansehen", es: "Ver la demo", it: "Vedi la demo" })}
          </button>
          <a className="lp-cta-ghost" href="#waitlist">
            {L(lang, {
              fr: "Rejoindre la liste d'attente",
              en: "Join the waitlist",
              de: "Warteliste beitreten",
              es: "Unirse a la lista de espera",
              it: "Iscriviti alla lista d'attesa",
            })}
          </a>
        </div>
        <div className="lp-hook">
          <span className="lp-hook-num">{p.hookNum}</span>
          <span className="lp-hook-cap">{p.hookCap}</span>
        </div>
      </section>

      {/* Pitch */}
      <section className="lp-pitch">
        {p.paras.map((para, i) => (
          <p key={i} className="lp-para">
            {emph(para, `p${i}`)}
          </p>
        ))}
      </section>

      {/* 4 règles */}
      <section className="lp-rules">
        {(
          [
            [L(lang, { fr: "Read-only Qonto", en: "Read-only Qonto", de: "Nur-Lesen Qonto", es: "Qonto solo lectura", it: "Qonto sola lettura" }), L(lang, { fr: "Aucune écriture, aucun mouvement d'argent.", en: "No writes, no money movement.", de: "Keine Schreibvorgänge, keine Geldbewegung.", es: "Sin escrituras, sin movimiento de dinero.", it: "Nessuna scrittura, nessun movimento di denaro." })],
            [L(lang, { fr: "Le moteur calcule", en: "The engine computes", de: "Die Engine rechnet", es: "El motor calcula", it: "Il motore calcola" }), L(lang, { fr: "Chaque euro vient d'un code déterministe, jamais du LLM.", en: "Every euro comes from deterministic code, never the LLM.", de: "Jeder Euro stammt aus deterministischem Code, nie vom LLM.", es: "Cada euro viene de código determinista, nunca del LLM.", it: "Ogni euro viene da codice deterministico, mai dall'LLM." })],
            [L(lang, { fr: "Zéro PII vers le web", en: "Zero PII to the web", de: "Keine PII ins Web", es: "Cero PII a la web", it: "Zero PII sul web" }), L(lang, { fr: "Seuls le marchand + la catégorie sortent.", en: "Only merchant + category leave.", de: "Nur Händler + Kategorie gehen raus.", es: "Solo salen comercio + categoría.", it: "Escono solo esercente + categoria." })],
            [L(lang, { fr: "Prix = source + date", en: "Price = source + date", de: "Preis = Quelle + Datum", es: "Precio = fuente + fecha", it: "Prezzo = fonte + data" }), L(lang, { fr: "Sinon : « non vérifié ».", en: 'Otherwise: "not verified".', de: 'Sonst: „nicht verifiziert".', es: 'Si no: "no verificado".', it: 'Altrimenti: "non verificato".' })],
          ] as const
        ).map(([t, d], i) => (
          <div key={i} className="lp-rule">
            <span className="lp-rule-n">{i + 1}</span>
            <div>
              <p className="lp-rule-t">{t}</p>
              <p className="lp-rule-d">{d}</p>
            </div>
          </div>
        ))}
      </section>

      {/* Waitlist */}
      <section className="lp-wait" id="waitlist">
        <h2 className="lp-wait-title">
          {L(lang, {
            fr: "Branche ton vrai compte Qonto",
            en: "Connect your real Qonto account",
            de: "Verbinde dein echtes Qonto-Konto",
            es: "Conecta tu cuenta Qonto real",
            it: "Collega il tuo vero conto Qonto",
          })}
        </h2>
        {joined ? (
          <p className="lp-wait-done">
            ✓ {L(lang, { fr: "Tu es sur la liste", en: "You're on the list", de: "Du bist auf der Liste", es: "Estás en la lista", it: "Sei nella lista" })}
          </p>
        ) : (
          <>
            <form
              className="lp-wait-form"
              onSubmit={(e) => {
                e.preventDefault();
                if (email.includes("@")) {
                  storeEmail(email, "waitlist");
                  setJoined(true);
                }
              }}
            >
              <input
                className="lp-wait-input"
                type="email"
                required
                placeholder={L(lang, { fr: "ton@email.com", en: "you@email.com", de: "du@email.com", es: "tu@email.com", it: "tua@email.com" })}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                aria-label="email"
              />
              <button className="lp-wait-btn" type="submit">
                {L(lang, {
                  fr: "Rejoindre : connecter Qonto",
                  en: "Join: connect Qonto",
                  de: "Beitreten: Qonto verbinden",
                  es: "Unirse: conectar Qonto",
                  it: "Iscriviti: collega Qonto",
                })}
              </button>
            </form>
            <p className="lp-wait-hint">
              {L(lang, {
                fr: "Pour rejoindre la liste d'attente, connecte ton email.",
                en: "To join the waitlist, connect your email.",
                de: "Um der Warteliste beizutreten, gib deine E-Mail an.",
                es: "Para unirte a la lista de espera, conecta tu email.",
                it: "Per iscriverti alla lista d'attesa, collega la tua email.",
              })}
            </p>
          </>
        )}
        <p className="lp-disclaimer">
          {L(lang, {
            fr: "Données de démonstration — configure Qonto + Anthropic dans .env pour brancher ton vrai compte. Données traitées en Europe, jamais utilisées pour entraîner un modèle. Conseils fiscaux à valider avec ton comptable.",
            en: "Demo data — set up Qonto + Anthropic in .env to connect your real account. Data processed in Europe, never used to train a model. Tax advice to confirm with your accountant.",
            de: "Demo-Daten — Qonto + Anthropic in .env einrichten, um dein echtes Konto zu verbinden. Daten in Europa verarbeitet, nie zum Modelltraining genutzt. Steuertipps mit deinem Buchhalter prüfen.",
            es: "Datos de demostración — configura Qonto + Anthropic en .env para conectar tu cuenta real. Datos tratados en Europa, nunca usados para entrenar un modelo. Consejos fiscales a validar con tu contable.",
            it: "Dati dimostrativi — configura Qonto + Anthropic in .env per collegare il tuo conto reale. Dati trattati in Europa, mai usati per addestrare un modello. Consigli fiscali da validare con il commercialista.",
          })}
        </p>
        <p className="lp-proto">
          {L(lang, {
            fr: "Prototype pour Hackathon Qonto",
            en: "Prototype for Qonto Hackathon",
            de: "Prototyp für den Qonto-Hackathon",
            es: "Prototipo para el Hackathon de Qonto",
            it: "Prototipo per l'Hackathon Qonto",
          })}
        </p>
      </section>

      {/* Gate email — au clic « Voir la démo » (stocké dans Cloudflare KV) */}
      {gate && (
        <div className="lp-gate" role="dialog" aria-modal="true" onClick={() => !sending && setGate(false)}>
          <div className="lp-gate-box" onClick={(e) => e.stopPropagation()}>
            <p className="lp-gate-title">
              {L(lang, { fr: "Accède à la démo", en: "Access the demo", de: "Zur Demo", es: "Accede a la demo", it: "Accedi alla demo" })}
            </p>
            <p className="lp-gate-sub">
              {L(lang, {
                fr: "Laisse ton email pour lancer la démo Argentier.",
                en: "Leave your email to launch the Argentier demo.",
                de: "Gib deine E-Mail an, um die Argentier-Demo zu starten.",
                es: "Deja tu email para iniciar la demo de Argentier.",
                it: "Lascia la tua email per avviare la demo di Argentier.",
              })}
            </p>
            <form className="lp-gate-form" onSubmit={submitDemo}>
              <input
                className="lp-gate-input"
                type="email"
                required
                autoFocus
                placeholder={L(lang, { fr: "ton@email.com", en: "you@email.com", de: "du@email.com", es: "tu@email.com", it: "tua@email.com" })}
                value={demoEmail}
                onChange={(e) => setDemoEmail(e.target.value)}
                aria-label="email"
              />
              <button className="lp-gate-btn" type="submit" disabled={sending}>
                {sending
                  ? "…"
                  : L(lang, { fr: "Voir la démo →", en: "See the demo →", de: "Demo ansehen →", es: "Ver la demo →", it: "Vedi la demo →" })}
              </button>
            </form>
            <button className="lp-gate-cancel" onClick={() => setGate(false)} disabled={sending}>
              {L(lang, { fr: "Annuler", en: "Cancel", de: "Abbrechen", es: "Cancelar", it: "Annulla" })}
            </button>
          </div>
        </div>
      )}

      <footer className="lp-foot">
        <Mark /> Argentier · Qonto × Anthropic MCP Hackathon
      </footer>
    </div>
  );
}

function Mark() {
  return (
    <svg className="lp-mark" viewBox="0 0 32 32" fill="none" aria-hidden="true">
      <path d="M5.5 25.5 L16 5.5 L26.5 25.5" stroke="currentColor" strokeWidth="3" strokeLinejoin="round" strokeLinecap="round" />
      <rect x="12" y="19.5" width="2.3" height="6" rx="0.7" className="lp-mark-bar" />
      <rect x="15.4" y="16.5" width="2.3" height="9" rx="0.7" className="lp-mark-bar" />
      <rect x="18.8" y="13.5" width="2.3" height="12" rx="0.7" className="lp-mark-bar" />
    </svg>
  );
}

// Palette inspirée de qonto.com : noir profond, blanc, accent jaune.
const CSS = `
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');
.lp{--bg:#111110;--ink:#FFFFFF;--ink2:#B4B2AC;--line:rgba(255,255,255,.14);--yellow:#F5D312;
  background:var(--bg);color:var(--ink);font-family:'Inter',system-ui,sans-serif;min-height:100vh;
  -webkit-font-smoothing:antialiased;line-height:1.5;overflow-x:hidden;}
.lp *{box-sizing:border-box;}
.lp-mark{width:26px;height:26px;color:var(--ink);vertical-align:middle;}
.lp-mark-bar{fill:var(--yellow);}
.lp-nav{position:sticky;top:0;z-index:10;display:flex;align-items:center;justify-content:space-between;
  padding:16px clamp(18px,5vw,64px);background:rgba(17,17,16,.82);backdrop-filter:blur(10px);border-bottom:1px solid var(--line);}
.lp-brand{display:inline-flex;align-items:center;gap:9px;font-family:'Space Grotesk';font-weight:600;font-size:18px;}
.lp-nav-right{display:flex;align-items:center;gap:14px;}
.lp-langs{display:inline-flex;gap:2px;}
.lp-lang{border:0;background:none;font-size:15px;padding:3px 4px;cursor:pointer;opacity:.5;border-radius:6px;line-height:1;transition:opacity .1s,background .1s;}
.lp-lang.on,.lp-lang:hover{opacity:1;background:rgba(255,255,255,.08);}
.lp-demo-top{border:1px solid var(--line);background:none;color:var(--ink);border-radius:99px;font-family:inherit;
  font-size:13px;font-weight:600;padding:8px 16px;cursor:pointer;transition:background .12s;}
.lp-demo-top:hover{background:rgba(255,255,255,.08);}

.lp-hero{max-width:920px;margin:0 auto;padding:clamp(48px,10vh,120px) clamp(18px,5vw,32px) 40px;text-align:center;}
.lp-eyebrow{display:inline-block;font-size:12.5px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;
  color:var(--yellow);border:1px solid color-mix(in srgb,var(--yellow) 40%,transparent);border-radius:99px;padding:6px 14px;margin-bottom:26px;}
.lp-title{font-family:'Space Grotesk';font-weight:700;font-size:clamp(34px,7vw,72px);line-height:1.02;letter-spacing:-.03em;margin:0 0 22px;text-wrap:balance;}
.lp-sub{font-size:clamp(16px,2.3vw,21px);color:var(--ink2);max-width:640px;margin:0 auto 34px;text-wrap:pretty;}
.lp-cta{display:flex;gap:14px;justify-content:center;flex-wrap:wrap;margin-bottom:56px;}
.lp-demo{border:0;background:var(--yellow);color:#111110;border-radius:99px;font-family:inherit;font-size:16px;font-weight:700;
  padding:15px 32px;cursor:pointer;box-shadow:0 8px 30px color-mix(in srgb,var(--yellow) 30%,transparent);transition:transform .08s ease;}
.lp-demo:hover{transform:translateY(-2px);}
.lp-cta-ghost{display:inline-flex;align-items:center;border:1px solid var(--line);color:var(--ink);border-radius:99px;
  font-size:16px;font-weight:600;padding:15px 28px;text-decoration:none;transition:background .12s;}
.lp-cta-ghost:hover{background:rgba(255,255,255,.08);}
.lp-hook{display:inline-flex;align-items:baseline;gap:16px;padding-top:40px;border-top:1px solid var(--line);flex-wrap:wrap;justify-content:center;max-width:560px;}
.lp-hook-num{font-family:'Space Grotesk';font-weight:700;font-size:clamp(56px,13vw,110px);line-height:.85;color:var(--yellow);letter-spacing:-.04em;}
.lp-hook-cap{font-family:'Space Grotesk';font-weight:600;font-size:clamp(17px,3vw,24px);color:var(--ink);max-width:300px;text-align:left;}

.lp-pitch{max-width:720px;margin:0 auto;padding:20px clamp(18px,5vw,32px) 60px;}
.lp-para{font-size:clamp(16px,2vw,19px);line-height:1.65;color:var(--ink2);margin:0 0 22px;text-wrap:pretty;}
.lp-para strong{color:var(--ink);font-weight:600;}

.lp-rules{max-width:920px;margin:0 auto;padding:0 clamp(18px,5vw,32px) 70px;display:grid;grid-template-columns:repeat(2,1fr);gap:16px;}
@media(max-width:640px){.lp-rules{grid-template-columns:1fr;}}
.lp-rule{display:flex;gap:14px;align-items:flex-start;border:1px solid var(--line);border-radius:16px;padding:20px;background:rgba(255,255,255,.02);}
.lp-rule-n{flex:none;width:30px;height:30px;border-radius:50%;background:var(--yellow);color:#111110;font-family:'Space Grotesk';
  font-weight:700;display:flex;align-items:center;justify-content:center;font-size:15px;}
.lp-rule-t{font-family:'Space Grotesk';font-weight:600;font-size:16px;margin:0 0 4px;}
.lp-rule-d{font-size:13.5px;color:var(--ink2);margin:0;}

.lp-wait{max-width:720px;margin:0 auto;padding:20px clamp(18px,5vw,32px) 40px;text-align:center;}
.lp-wait-title{font-family:'Space Grotesk';font-weight:700;font-size:clamp(24px,4vw,38px);letter-spacing:-.02em;margin:0 0 26px;}
.lp-wait-btn{border:0;background:var(--yellow);color:#111110;border-radius:99px;font-family:inherit;font-size:clamp(14px,2vw,17px);
  font-weight:700;padding:16px 28px;cursor:pointer;max-width:100%;transition:transform .08s ease,opacity .1s;box-shadow:0 8px 30px color-mix(in srgb,var(--yellow) 26%,transparent);}
.lp-wait-btn:hover:not(:disabled){transform:translateY(-2px);}
.lp-wait-btn:disabled{opacity:.7;cursor:default;background:#2a2a27;color:var(--yellow);box-shadow:none;}
.lp-wait-form{display:flex;gap:10px;max-width:540px;margin:0 auto;flex-wrap:wrap;justify-content:center;}
.lp-wait-input{flex:1;min-width:220px;border:1px solid var(--line);background:rgba(255,255,255,.05);color:var(--ink);
  border-radius:99px;font-family:inherit;font-size:15px;padding:15px 22px;outline:none;transition:border-color .12s;}
.lp-wait-input::placeholder{color:var(--ink2);}
.lp-wait-input:focus{border-color:var(--yellow);}
.lp-wait-hint{font-size:12.5px;color:var(--ink2);margin:12px 0 0;}
.lp-wait-done{font-family:'Space Grotesk';font-weight:700;font-size:clamp(18px,3vw,24px);color:var(--yellow);margin:0;}
.lp-disclaimer{font-size:12px;color:var(--ink2);max-width:560px;margin:22px auto 0;line-height:1.6;}
.lp-proto{font-family:'Space Grotesk';font-weight:600;font-size:13px;color:var(--yellow);margin:14px 0 0;letter-spacing:.02em;}

.lp-foot{border-top:1px solid var(--line);text-align:center;padding:28px;color:var(--ink2);font-size:13px;display:flex;align-items:center;justify-content:center;gap:8px;}
.lp-foot .lp-mark{width:18px;height:18px;color:var(--ink2);}
.lp-gate{position:fixed;inset:0;z-index:50;background:rgba(0,0,0,.7);display:flex;align-items:center;justify-content:center;padding:20px;backdrop-filter:blur(4px);}
.lp-gate-box{background:#1b1b19;border:1px solid var(--line);border-radius:18px;padding:28px;width:100%;max-width:420px;text-align:center;box-shadow:0 24px 70px rgba(0,0,0,.5);}
.lp-gate-title{font-family:'Space Grotesk';font-weight:700;font-size:22px;color:var(--ink);margin:0 0 6px;}
.lp-gate-sub{font-size:13.5px;color:var(--ink2);margin:0 0 18px;}
.lp-gate-form{display:flex;flex-direction:column;gap:10px;}
.lp-gate-input{border:1px solid var(--line);background:rgba(255,255,255,.05);color:var(--ink);border-radius:12px;font-family:inherit;font-size:15px;padding:14px 18px;outline:none;transition:border-color .12s;}
.lp-gate-input::placeholder{color:var(--ink2);}
.lp-gate-input:focus{border-color:var(--yellow);}
.lp-gate-btn{border:0;background:var(--yellow);color:#111110;border-radius:12px;font-family:inherit;font-size:16px;font-weight:700;padding:14px;cursor:pointer;transition:transform .08s ease,opacity .1s;}
.lp-gate-btn:hover:not(:disabled){transform:translateY(-1px);}
.lp-gate-btn:disabled{opacity:.7;cursor:progress;}
.lp-gate-cancel{margin-top:12px;border:0;background:none;color:var(--ink2);font-family:inherit;font-size:13px;cursor:pointer;text-decoration:underline;}
@media(prefers-reduced-motion:reduce){.lp-demo,.lp-wait-btn{transition:none;}}
`;
