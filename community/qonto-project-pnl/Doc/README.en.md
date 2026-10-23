# 📓 qonto-project-pnl — Your project docs finally tell the economic truth

> **Qonto × Anthropic MCP Hackathon submission** · Agent Skill for the Qonto MCP + Notion connector
> Qonto side: read-only, zero writes · the single write lives in Notion, in a dedicated database, always previewed and confirmed

---

## 🎯 Why this matters (usefulness)

Studios, agencies and indie hackers run their projects in Notion: the docs look great, the specs are current… but **per-project profitability stays a mystery**. The revenue is in the bank, the costs are in the bank — and the doc knows nothing. `qonto-project-pnl` closes the loop:

1. **Real revenue** — cashed money only: paid client invoices matched to incoming bank transactions (matching shown and confirmed), attributed to their project
2. **Attributed costs** — Qonto labels ↔ projects (mapping confirmed once, then remembered), refunds deducted, a 24–36-month scan so *annual* renewals show up
3. **Margin & monthly burn** — per project: margin in € and %, 3-month average burn, confidence tags 🟢🟡
4. **The P&L lives in Notion** — a dedicated "Finance" database, one entry per project, **refreshed on every run** (idempotent: re-run = update, never a duplicate), with alerts ⚠️ overdue invoice · unusual cost · negative margin

Would someone use this on a Monday morning? It answers the Monday-morning question: **which projects deserve your week**.

## 🆚 Don't confuse: `qonto-project-burn` vs `qonto-project-pnl`

| | `qonto-project-burn` | `qonto-project-pnl` (this skill) |
|---|---|---|
| The question | "Are we within budget?" | "Is this project making money?" |
| Scope | **Costs** vs declared budget, projected overrun date | **Revenue AND costs** → margin, burn |
| Destination | Linear / Jira — the product team | Notion — the project documentation |
| Alerts | Budget thresholds (80% / 100%) | Overdue invoice, unusual cost, negative margin |

They complement each other; for the **company-wide** view (runway, all-costs cockpit), see `qonto-ceo-cockpit`.

## 📋 Prerequisites

| Prerequisite | Detail | Required |
|---|---|---|
| Qonto **production** account | The skill adapts to any organization — `get_organization` first, nothing hardcoded | ✅ |
| Country | **Universal** — labels + invoices + transactions, no tax rules: every Qonto country (FR, DE, ES, IT, AT, NL, BE, PT) works identically | ℹ️ detected |
| Qonto MCP connected | Official connector (claude.ai / Claude Desktop), OAuth login | ✅ |
| **Notion** connector | The official connector — required for writing the Finance database. Without it: clean degraded mode (P&L as conversation tables + HTML dashboard) | ⭕ recommended |
| Qonto labels per project | The account's "project" dimension. No labels: mapping proposed from recurring counterparties, everything tagged 🟡 | ⭕ recommended |
| Client invoices in Qonto | For cashed revenue and overdue alerts. Without: fallback to labelled credits (🟡) | ⭕ |

## ⚙️ How it works

![How it works](assets/flow.en.png)

1. **Read the account**: `get_organization` then `list_labels` (paginated ≤ 50) — the label tree is the candidate project list. `list_cash_flow_categories` is never called (403 on the claude.ai connector)
2. **Label ↔ project mapping**: a proposed table (label → project → Notion page → clients), **always shown and confirmed**, then remembered as a paste-ready block — on re-runs, only changes get reconfirmed
3. **Cashed revenue**: paid invoices matched to incoming transactions (amount + date window + normalized counterparty), ambiguous pairs confirmed by the user; an issued-but-unpaid invoice is **never** revenue — past its due date it becomes an ⚠️ alert
4. **Attributed costs + the P&L**: debits grouped by mapped label over 24–36 months (*annual* renewals only show there), refunds deducted, orphans listed separately — then margin (€ and %), monthly burn, quantified alerts
5. **Notion write** (explicit consent only, after a preview): dedicated "Finance — P&L (generated)" database, one entry per project, **updated in place** on re-runs — never a duplicate, never touching the rest of the workspace
6. **Report**: markdown tables in the conversation (always) + an HTML dashboard when the host renders files

## 🏗 Functional diagram

![Functional diagram](assets/functional.en.png)

**The security model**: on the Qonto side the skill is **read-only — zero writes**, risk-free. The dashed arrow (write) lives on the Notion side: it requires explicit consent given in the conversation, touches **only** the dedicated database marked as generated, and never modifies existing Notion content. No money moves, anywhere.

## 🧪 Holds up on messy data

- No labels at all? → mapping proposed from recurring counterparties, everything tagged 🟡, plus how to label in the Qonto app
- No client invoices in Qonto? → revenue falls back to labelled credits (🟡), overdue detection declared unavailable
- Unlabelled debits that look like a project's suppliers? → listed as **orphans**, never silently attributed
- A transaction carrying several labels? → counted once, under the first matching label — and the skill says so
- Renamed a project between runs? → the mapping shows the change; the Notion entry is matched by project name, so confirm the rename instead of creating a twin
- No Notion connector? → the skill says so and delivers the full P&L as tables + HTML dashboard
- Card spend timing (`emitted_at` vs `settled_at`), refunds deducted, pagination ≤ 50 — all handled

## 📓 The "Finance" database in Notion (one entry per project)

| Property | Content | Example (invented) |
|---|---|---|
| Project | Project name (the idempotent update key) | Aurora |
| Cashed revenue | Sum of matched paid invoices | €18,400 |
| Attributed costs | Labelled debits, refunds deducted | €7,150 |
| Margin | € and % | €11,250 · 61% |
| Monthly burn | Average of the last 3 full months | €2,380/month |
| Alerts | ⚠️ plain-language, quantified | ⚠️ 1 overdue invoice (INV-2026-042, 12 days) |
| Period · Updated | Window covered · timestamp of the last run | 2024-08 → 2026-07 · 1 min ago |

## 📤 Output formats (where does the P&L land?)

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables (per-project P&L, alerts, orphans) | **Always** — the baseline |
| **"Finance" database in Notion** | Dedicated database, one entry per project, refreshed on every run | When the Notion connector is present + explicit consent |
| **Interactive dashboard** | **HTML** file/artifact: revenue vs costs bars, margin badge, burn, alert markers | When the host renders files; automatic fallback to tables otherwise |

## 🎬 Demo video

The ≤ 3-minute demo attached to the PR walks through: the profitability mystery → the confirmed mapping → the computed P&L → **the Notion project page showing "updated 1 min ago"** → the idempotent re-run. All figures on screen are invented demo data.

## 💡 Roadmap ideas

- Monthly history per project (a sub-table per entry) — the Finance database gains a time dimension
- Open quotes (`list_quotes`) as a "pipeline" column — signed vs cashed, never conflated
- Hand overdue invoices to `qonto-invoice-chaser` for the follow-up
- Implicit hourly rate (margin ÷ declared time) — time stays user-declared, never invented

## 🛡 Guardrails

- **Zero Qonto writes**; the single write is the dedicated, clearly marked Notion database — after a preview and an explicit "yes", never presented as done if the call failed
- **Idempotent**: re-run = in-place update (key: project name), never a duplicate, never a deletion
- The label → project mapping and the invoice ↔ transaction matching are **always shown and correctable** — no silent attribution
- Revenue is matched cash only; every fallback or estimate carries a 🟡 tag; no invented amounts
- Masked IBANs (last 4 digits) · pagination ≤ 50 everywhere · honest degradation (no labels, no invoices, no Notion, short history)

---

*Submission docs: `SKILL.md` (the skill itself) · step-by-step guide: `docs/PROCEDURE.en.md` · rich docs in `docs/` (HTML & DOCX, FR/EN).*
