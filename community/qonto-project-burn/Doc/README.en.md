# 📊 qonto-project-burn — What project X *actually* cost

> **Qonto × Anthropic MCP Hackathon submission** · Agent Skill for the Qonto MCP
> The finance ↔ product bridge: real burn per project, written where the team lives (Linear/Jira)

---

## 🎯 Why this matters (usefulness)

Teams plan in Linear or Jira; the money lives in Qonto. So **nobody knows what project X actually cost** — the dedicated SaaS, the freelancers, the ads, the hardware. `qonto-project-burn` closes that gap:

1. **Label ↔ project mapping** — a simple config table proposed from your existing Qonto labels, correctable line by line, remembered in the conversation or the Claude project
2. **Real burn per project vs declared budget** — up to 36 months scanned (so *annual* SaaS renewals don't slip through), refunds deducted, unlabelled transactions listed apart — never silently attributed
3. **Projected overrun date** — current monthly run rate → "at this pace, Alpha crosses its budget on Aug 12", with confidence tags 🟢🟡
4. **Status written where the team lives** — with your consent: an "X € / Y € — Z %" comment on the Linear/Jira project, plus an alert issue "⚠️ Budget Alpha 87 %" when a threshold is crossed, backed by the exact Qonto transactions

Qonto side: **read-only**. The one notable write happens in Linear — always previewed first. Would someone use this on a Monday morning? It's the sprint-planning question: *"where is Alpha, really?"* — now with the money in the answer.

## 📋 Prerequisites

| Prerequisite | Detail | Required |
|---|---|---|
| Qonto **production** account | Adapts to any organization — `get_organization` first, nothing hardcoded | ✅ |
| Country | **Universal** — labels + transactions, no tax rules: every Qonto country (FR, DE, ES, IT, AT, NL, BE, PT) | ℹ️ all |
| Qonto MCP connected | Official connector (claude.ai / Claude Desktop), OAuth login | ✅ |
| Qonto labels | A few transactions labelled per project. No labels? The skill proposes a mapping from recurring suppliers (🟡 tags) and explains how to label in the app | ⭕ recommended |
| Linear or Jira/Atlassian MCP | Detected dynamically — otherwise **degraded mode**: full per-project report in the conversation + HTML dashboard | ⭕ optional |
| Declared budgets | Provided by you in the mapping (or read from the Linear project description when formatted) — never invented | ✅ at setup |

## ⚙️ How it works

![How it works](assets/flow.en.png)

1. **Read the account**: `get_organization` first (accounts, currency), then `list_labels` — the label tree becomes the candidate project list. ⚠️ No `list_cash_flow_categories` (403 on the claude.ai connector): the mapping runs on **labels**
2. **Label ↔ project mapping**: label → project → Linear/Jira project (when the MCP is present) → declared budget. Shown, correctable, then handed back as a paste-ready block for the Claude project instructions — remembered, never written to Qonto
3. **Real burn**: `list_transactions` paginated ≤ 50, 24–36 months when history allows (annual cadences), grouped by label, refunds deducted, `emitted_at` for card spend. A multi-label transaction counts **once**
4. **Budget vs run rate**: spent, % consumed, monthly run rate (last 3 months, weighted), projected overrun date. Default thresholds ⚠️ 80 % · 🔴 100 %
5. **Write where the team lives** (explicit consent only): status comment on the Linear/Jira project + alert issue when a threshold is crossed — the exact text shown verbatim **before** posting
6. **Report**: per-project table ✅/⚠️/🔴, orphan list, alerts, HTML dashboard when the host renders files

## 🏗 Functional diagram

![Functional diagram](assets/functional.en.png)

**The security model**: on the Qonto side everything is a read — no transfer, no payment, nothing touches the money. The dashed (write) arrow points at **Linear/Jira**, not at the bank: a comment or an issue, always previewed and confirmed in the conversation. The only optional Qonto-side tidy-up (`modify_transaction_cash_flow_category` to file orphans) is light, reversible and confirmed.

## 🧪 Holds up on messy data

- No labels at all? → mapping proposed from recurring counterparties, everything tagged 🟡, labelling instructions for the app
- Unlabelled (orphan) spend? → listed with count and total, two clean-up paths offered — never silently attributed to a project
- A transaction carrying several labels? → counted once, under the mapping's first matching label, and disclosed
- Annual SaaS renewals? → caught by scanning 24–36 months, not just the current quarter
- No Linear/Jira MCP? → the skill says so and delivers the full report + HTML dashboard in the conversation
- Refunds, card settlement delays (`emitted_at` vs `settled_at`), multi-account orgs — all handled

## 📊 Sample report (invented data)

| Project | Spent | Budget | % | Run rate | Projected overrun | Status |
|---|---|---|---|---|---|---|
| Alpha | €10,440 | €12,000 | 87 % | €1,950/mo | Aug 12 | ⚠️ |
| Kepler | €3,100 | €8,000 | 39 % | €620/mo | — | ✅ |
| Odyssey | €21,500 | €20,000 | 108 % | €1,400/mo | crossed | 🔴 |

*Entirely fictional example — projects, amounts and dates invented for illustration.*

## 📤 Output formats (where does the burn land?)

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables (burn per project, orphans, alerts) | **Always** — the baseline |
| **Linear/Jira comment** | "X € / Y € — Z % · projected overrun on [date] · top 5 lines" on the mapped project | Tracker MCP detected + explicit consent |
| **Linear/Jira alert issue** | "⚠️ Budget [project] Z %" + the Qonto transactions that justify it | Threshold crossed + explicit consent |
| **Interactive dashboard** | **HTML** file/artifact: spent-vs-budget bars, run rate, overrun markers | When the host renders files; automatic fallback to tables |

## 🎬 Demo video

The ≤ 3-minute demo attached to the PR walks through: the problem → the mapping → burn & overrun dates → **opening Linear and finding the "⚠️ Budget Alpha 87 %" issue Claude created, backed by the Qonto transactions** → the dashboard. The finance comes to the team — not the other way around.

## 💡 Roadmap ideas

- Budget per sprint/cycle, not just per project — reuses the mapping, sliced by Linear cycle dates
- Client re-billing: cross with `list_client_invoices` for real per-project margin (burn − invoiced)
- Weekly ritual: the status comment posted every Monday, same write, same consent
- Slack/Notion as alternative status targets — optional multi-MCP, detected dynamically


## 🆚 Not to be confused: `qonto-project-burn` vs `qonto-project-pnl`

| | `qonto-project-burn` (this skill) | `qonto-project-pnl` |
|---|---|---|
| The question | "Are we on budget?" | "Is this project making money?" |
| Scope | **Costs** vs declared budget, projected overrun date | **Revenue AND costs** → margin, burn |
| Destination | Linear / Jira — the product team | Notion — the project docs |
| Alerts | Budget thresholds (80% / 100%) | Late invoice, unusual cost, negative margin |

## 🛡 Guardrails

- NEVER writes to Linear/Jira without showing the exact content and getting explicit confirmation in the current conversation; never presented as done if the call failed
- The label → project attribution is **always shown and correctable** — no silent reassignment
- Budgets are user-declared, spend is Qonto data — the skill invents neither
- `list_cash_flow_categories` → 403 on the claude.ai connector: expected, labels are the fallback
- IBANs masked (last 4 digits) · pagination ≤ 50 everywhere · honest degradation (no labels, short history, no tracker MCP)

## 🔗 Related skills

For the **company-wide** view (runway, all-costs cockpit): `qonto-ceo-cockpit`. This skill is the **project-level** granularity.

---

*Submission docs: `SKILL.md` (the skill itself) · step-by-step guide: `docs/PROCEDURE.en.md` · rich docs in `docs/` (HTML & DOCX, FR/EN).*
