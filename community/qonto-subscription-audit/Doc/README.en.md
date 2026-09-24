# 🔍 qonto-subscription-audit — The complete recurring-spend audit

> **Qonto × Anthropic MCP Hackathon submission** · Agent Skill for the Qonto MCP
> 100 % Qonto, 100 % read-only. Every recurring euro, audited: what you pay, what you forgot, what quietly went up, and what just started.

---

## 🎯 Why this matters (usefulness)

Subscriptions pile up, prices creep up silently, trials convert, nobody cancels. Most founders can't name their real annual subscription spend within 50 %. `qonto-subscription-audit` runs the COMPLETE audit over **24–36 months**:

1. **The full inventory** — every recurring charge (cards AND direct debits), monthly/quarterly/**yearly** cadence, with the **TOTAL annualized cost** (the shock number) and a status per line: ✅ active · 👥 duplicate (two tools doing the same job) · 🧟 zombie (always user-confirmed) · 🎣 trial gone paid
2. **The newborns 🌱** — every recent counterparty never seen before is scored. First signal: **Claude's own merchant knowledge** — streaming & software (Netflix, Adobe, Microsoft 365), AI (OpenAI), design & collaboration (Figma, Slack, Notion), **course & creator platforms (Systeme.io, Skool, Kajabi, Podia…)**, **hosting & domain registrars (OVH, PlanetHoster, Gandi, IONOS — domains renew YEARLY, the easiest to miss)** are notorious subscription businesses: a **single first charge** earns the 🌱 tag, no history needed. Then the behavioral signals: typical round amount, label hints (subscription/monthly/plan), a 2nd occurrence ~30 days later → "probable subscription, to confirm". **Early detection**: catch the trial before it becomes rent
3. **Every hike detected** — price plateaus (≥ 2 charges within ±2 %, a jump persisting ≥ 2 cycles), FX and VAT excluded (excl-VAT comparison via supplier invoices), tagged 🟢 ≤ inflation · 🟡 above · 🔴 aggressive · ⚪ variable usage, plus the **cumulated annual overcost** of all hikes
4. **The dashboard + the emails** — a dashboard built **directly in Claude**, exportable as a self-contained HTML file in Qonto colors; an argued renegotiation email (tenure, volume, hike record) and a **monthly digest** (actives, month total, 3-month forecast, hikes) — Gmail drafts when the MCP is present, copy-paste text otherwise, **never sent without you**

Would someone use this on a Monday morning? It's the audit every founder postpones because it means opening 30 months of statements. Here it's one prompt — with the fix one skill away: to cap a subscription with a dedicated virtual card, hand over to `qonto-subscription-guardian`.

## 📋 Prerequisites

| Prerequisite | Detail | Required |
|---|---|---|
| Qonto **production** account | The skill adapts to any organization — `get_organization` first, nothing hardcoded | ✅ |
| Country | **Country-agnostic core**: inventory, statuses and hike detection work on every Qonto country (FR, DE, ES, IT, AT, NL, BE, PT). Only the inflation benchmark is localized — the country's figure when known, euro-area otherwise, reference always stated | ℹ️ detected |
| Qonto MCP connected | Official connector (claude.ai / Claude Desktop), OAuth login | ✅ |
| **≥ 24 months of history** | A YEARLY subscription only shows with 2 occurrences: on a 12-month window, annual renewals fly under the radar. Below that: the skill audits what's visible and honestly states what may be missing | ⭕ recommended |
| Gmail MCP | Detected dynamically: present → monthly digest + negotiation drafts in Gmail; absent → copy-paste text. The core needs Qonto only | ⭕ optional |

## ⚙️ How it works

![How it works](assets/flow.en.png)

1. **Learn from history** (24–36 months of debits, paginated ≤ 50, 3-month windows): counterparty normalization — references, dates and card-processor prefixes (`PAYPAL *`, `SUMUP *`…) stripped, SEPA and card variants of the same supplier merged. Cadence math on `emitted_at`, not `settled_at`
2. **Inventory the recurring charges**: normalized counterparty + cadence 28–32 d / 85–95 d / **350–380 d** + ≥ 3 occurrences (2 for yearly), cards AND direct debits. A dated price series per line, excl-VAT amounts preferred when `list_supplier_invoices` has the invoice → the **total annualized cost**
3. **Statuses + newborns**: ✅ active · 👥 duplicates · 🧟 zombies (a hypothesis, user-confirmed) · 🎣 trials gone paid — plus the **🌱 New** section: nascent subscriptions — notorious merchants recognized **from the very first charge** (no history), round amounts, label hints, 2nd occurrence ~30 d
4. **Hike detection**: a plateau = ≥ 2 stable charges (±2 %); a hike = a plateau jump **persisting ≥ 2 cycles**; outliers, prorated months, FX and VAT excluded; variable usage ⚪ kept apart → the **cumulated annual overcost**, 🟢🟡🔴 tags vs inflation
5. **Dashboard**: markdown tables always; a dashboard rendered **directly in Claude** when the host allows; the same dashboard exportable as a **self-contained HTML file** in the Qonto palette (violet/black/white, light/dark) — total cost, category breakdown, statuses, hikes, 3-month forecast
6. **Emails**: argued negotiation drafts (tenure, volume, dated hikes) for the biggest 🔴/🟡 lines + the monthly digest — Gmail **drafts** with your consent, plain text otherwise

## 🏗 Functional diagram

![Functional diagram](assets/functional.en.png)

**The security model**: this skill performs **zero Qonto writes** — reads only, risk-free by construction. The only outbound artifacts are email **drafts** (negotiation, digest) that you review, edit and send (or not) yourself. The capped virtual card — the one write worth doing after this audit — belongs to `qonto-subscription-guardian`.

## 🧪 Holds up on messy data

- Supplier billed by card AND SEPA under different names? → normalization merges them into one line
- Yearly renewal invisible on short windows? → the scan targets 24–36 months, and below 24 the skill says yearly lines may be missing instead of pretending
- Bill in USD on a EUR account? → flagged as FX-exposed; exchange-rate wobble is never reported as a hike
- Cloud bill that doubled? → ⚪ variable usage: implicit unit price when invoices carry quantities, "not isolable from payment data" said plainly otherwise
- VAT-rate change? → excl-VAT comparison when supplier invoices exist, so a tax change isn't blamed on the supplier
- A one-month-old counterparty? → scored in the 🌱 New section as "probable subscription, to confirm" — never asserted as fact
- Empty account or no recurring charges → stated plainly, no fabricated findings; no Gmail MCP → one line, and the audit continues

## 📤 Output formats (where does the audit land?)

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables: shock number, portfolio sorted by annual cost, New 🌱 section, hikes, variable usage kept separate | **Always** — the baseline |
| **Dashboard in Claude** | Rendered **directly in the conversation** (artifact): annual-cost counter, category breakdown, lines by status ✅👥🧟🎣🌱, hikes with deltas, 3-month forecast | When the host allows it (claude.ai, Claude Desktop, Claude Code) |
| **HTML export** | The **same dashboard** as one self-contained HTML file, Qonto palette (violet #6B4EFF / black #1D1B29 / white, light/dark) — keep it or share it | On request |
| **Emails** | **Gmail drafts** (MCP present + your consent) or copy-paste text: negotiation + monthly digest | Never sent without you |

## 🎬 Demo video

The ≤ 3-minute demo attached to the PR walks through: the problem → the live inventory and statuses → the hikes and the overcost → **the dashboard building itself in Claude with the shock number, and the 🌱 New section catching a fresh trial** → wrap-up. It runs live on a real production account.

## 💡 Roadmap ideas

- Continuous watch: alert on the first charge of a confirmed 🌱 or a new price plateau — the monthly ritual becomes automatic
- Public-price benchmark: compare paid price to the supplier's published pricing (also catches over-paying grandfathered plans)
- Auto-label detected subscriptions in Qonto so the portfolio reads in the app too
- Post-negotiation follow-up: verify the price actually dropped — the price series already exists
- Capped-card bridge: chain into `qonto-subscription-guardian` — the audit finds, the guardian protects

## 🛡 Guardrails

- **Zero Qonto writes** — reads only; the capped card is `qonto-subscription-guardian` territory
- 🧟 is a hypothesis, always user-confirmed; 🌱 is "probable, to confirm", never asserted
- Never accuses a supplier when the data says usage, FX or VAT — doubtful lines go to variable usage with the reason
- Emails are **drafts**: never sent, no recipient added without the user; payment-data estimates ≠ contract audit
- Honest degradation under 24 months of history (yearly lines may be missing — and the skill says so) · IBANs masked (last 4 digits) · pagination ≤ 50 everywhere

---

*Submission docs: `SKILL.md` (the skill itself) · step-by-step guide: `docs/PROCEDURE.en.md` · rich docs in `docs/` (HTML & DOCX, FR/EN).*
