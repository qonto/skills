# Qonto Agent Skills — 19 skills for the Qonto MCP

A portfolio of Agent Skills built on the [Qonto MCP](https://qonto.com) for the **Qonto × Anthropic MCP Hackathon** (July 2026). Every skill runs on any Qonto production account: `get_organization` first, nothing hardcoded, graceful degradation on missing data or absent optional MCPs — and **no skill can move money**: the few writes are always confirmed, and transfers only happen after the user's own SCA in the Qonto app.

## The skills

| Skill | What it does | Qonto writes | Optional MCPs |
|---|---|---|---|
| [qonto-tax-pilot](qonto-tax-pilot/) ⭐ | Dated tax schedule (VAT/IS/CFE), 90-day cash projection, monthly provision to a tax sub-account (transfer request + SCA) | transfer request | — |
| [qonto-counterparty-watch](qonto-counterparty-watch/) | Legal health of clients & suppliers (SIRENE/BODACC) crossed with your exposure | none | Datagouv |
| [qonto-vat-return](qonto-vat-return/) | French VAT return (CA3) prepared box by box | none | — |
| [qonto-invoice-chaser](qonto-invoice-chaser/) | Graduated payment reminders that check the bank before writing | paid-marking (proposed) | Gmail |
| [qonto-receipt-hunter](qonto-receipt-hunter/) | Finds missing receipts in Gmail/Drive and attaches originals | attachment upload (confirmed) | Gmail · Google Drive |
| [qonto-monthly-close](qonto-monthly-close/) | The month-end close in 3 minutes, read-only | none | Gmail |
| [qonto-tax-radar](qonto-tax-radar/) | Pre-audit: 8 tax-inspection axes, articles cited | none | — |
| [qonto-subscription-guardian](qonto-subscription-guardian/) | One capped virtual card per chosen subscription (plan quotas checked) | create_card (confirmed, SCA) | — |
| [qonto-subscription-audit](qonto-subscription-audit/) | Full recurring-spend audit: annual cost, zombies, newborns 🌱, price hikes, dashboard | none | Gmail |
| [qonto-shopify-bridge](qonto-shopify-bridge/) | Shopify/Stripe payouts reconciled with real bank credits | none | Shopify · Stripe |
| [qonto-pay-me-now](qonto-pay-me-now/) | Accepted quote → invoice → payment link + tracked QR | invoice draft + payment link | Short.io · Gmail |
| [qonto-meeting-invoice](qonto-meeting-invoice/) | Sales-call transcript → quote sent before the coffee gets cold | quote/invoice draft (confirmed) | Notion / Google Drive |
| [qonto-supplier-detective](qonto-supplier-detective/) | Duplicates, double payments, IBAN-change watch | none | — |
| [qonto-fraud-sentinel](qonto-fraud-sentinel/) | 6 anomaly signals every morning, 30 seconds | card lock (proposed) | Gmail |
| [qonto-grant-scout](qonto-grant-scout/) | Real spending profile crossed with public aid datasets | none | Datagouv |
| [qonto-ceo-cockpit](qonto-ceo-cockpit/) | "My Company" live dashboard: flows, forecast, day-rate sliders | none | — |
| [qonto-board-pack](qonto-board-pack/) | Monthly investor update: figures, narrative, deck, email draft | none | Canva · Gmail |
| [qonto-accountant-handoff](qonto-accountant-handoff/) | The monthly handoff pack for your accountant | none | Google Drive · Gmail |
| [qonto-sector-benchmark](qonto-sector-benchmark/) | Your ratios vs official INSEE sector statistics | none | Datagouv |

## Layout of each skill

```
qonto-<name>/
├── PROMPTS.md             ← example prompts: getting started, going further, chaining
├── skill/
│   ├── qonto-<name>.md    ← the Agent Skill (import this .md, or the .zip)
│   └── qonto-<name>.zip   ← ready to import in claude.ai (contains SKILL.md, as required)
├── Doc/                   ← docs: README + step-by-step guide + rich HTML/DOCX, all in EN & FR
├── assets/                ← diagrams (how-it-works + functional), EN & FR, SVG + PNG
└── video/                 ← demo-qonto-<name>.mp4 — live demo, ≤ 3 minutes
```

**Bonus:** [`how-to-import-a-skill.mp4`](how-to-import-a-skill.mp4) — a 20-second walkthrough of importing any of these skills into claude.ai (Settings → Skills → Import).

## Install

Drop the skill's `.zip` (or its `SKILL.md`) in **claude.ai → Settings → Skills → Import**, open a new conversation with the Qonto connector enabled, and ask — e.g. *"set aside this month's taxes"*. Each `Doc/PROCEDURE.en.md` has the full guide and example prompts.

---

**Author:** Sébastien LA CASA · **Created:** July 11, 2026
*Built for the Qonto × Anthropic MCP Hackathon (July 10–13, 2026).*
