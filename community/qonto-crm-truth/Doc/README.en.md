# 🤝 qonto-crm-truth — The CRM that stops lying

> **Qonto × Anthropic MCP Hackathon submission** · Agent Skill for the Qonto MCP
> The bank as the source of truth: won deals never cashed, real revenue, A/B/C payer scores — written back into the CRM, always behind confirmation.

---

## 🎯 Why this matters (usefulness)

In every CRM, a deal marked "Closed Won" looks like revenue. Until the money hits the account, **it's fiction** — and sales teams prioritize on numbers the bank never confirmed. `qonto-crm-truth` reconciles CRM records (HubSpot **or** Airtable) with the Qonto account:

1. **Won-but-never-cashed deals** — every won deal with no matching euro on the account, listed with amount and age
2. **Real revenue, LTV & observed delays** — cash actually collected (not declared), cash LTV, the observed average payment delay ("pays at day +X"), the last payment date
3. **A/B/C payer reliability score** — computed from bank data, formula disclosed, never a guessed score (fewer than 2 paid invoices → unrated)
4. **Write-back into the CRM** — HubSpot custom properties or Airtable columns, after a CRM-record ↔ Qonto-client matching that is **always shown and confirmed**, never silent

Would someone use this on a Monday morning? It's the sales pipeline review — except this time the numbers are the bank's.

## 📋 Prerequisites

| Prerequisite | Detail | Required |
|---|---|---|
| Qonto **production** account | Adapts to any organization — `get_organization` first, nothing hardcoded | ✅ |
| Country | **Universal** — no local tax rule involved: works identically for all Qonto countries (FR, DE, ES, IT, AT, NL, BE, PT) | ℹ️ detected |
| Qonto MCP connected | Official connector (claude.ai / Claude Desktop), OAuth login | ✅ |
| HubSpot **or** Airtable MCP | The CRM — required for writes. Without it: degraded mode, a "Qonto clients, scored" report in the conversation (already useful) | ⭕ required for writes |
| Client invoices in Qonto | Anchor payment delays and matching. Without them: counterparty-level analysis of credits, stated as such | ⭕ recommended |
| ≥ 6 months of history | Below that, honest degradation (unrated scores + warning) | ⭕ |

## ⚙️ How it works

![How it works](assets/flow.en.png)

1. **Bank truth first** (24 months, paginated ≤ 50): credits per account, Qonto clients, client invoices with statuses — every payment tied to its client; multiple spellings of the same client normalized and merged (case, accents, legal suffixes); refunds deducted
2. **Per-client metrics**: real cash revenue, cash LTV, observed payment delay (median and mean of day +X), last payment date, A/B/C payer score — **from the bank, never from the CRM**
3. **Read the CRM** (detected dynamically): won deals, amounts, company records — HubSpot, or Airtable (`search_bases` → `get_table_schema` → read). No CRM? The skill says so and delivers the scored report in the conversation
4. **Assisted matching** — THE guardrail: CRM-record ↔ Qonto-client pairs proposed on normalized name / email / VAT number, the mapping table **always shown and confirmed** before anything else; ambiguous pairs become questions, the skill never picks alone
5. **Fiction vs reality**: won deals never cashed, top CRM account vs top real payer, chronic late payers — every gap quantified; unpaid invoices found here are ready for `qonto-invoice-chaser`
6. **Write into the CRM** (only after a field-by-field preview + explicit go): `create_field` then `update_records_for_table` on Airtable, custom properties on HubSpot — skill-dedicated fields, CRM-native fields never overwritten

## 🏗 Functional diagram

![Functional diagram](assets/functional.en.png)

**The security model**: on the Qonto side the skill is **pure read** — zero bank writes, nothing to approve, nothing at risk. The only writes target the CRM, behind two locks: the confirmed matching (never silent) and the exact preview of what will be written, explicitly approved in the conversation.

## 🅰️ The payer score (disclosed formula, never a black box)

| Score | Definition |
|---|---|
| **A** | Median settlement within 5 days of the due date, nothing currently overdue |
| **B** | Always pays, but late — median lateness ≤ 30 days past due |
| **C** | Median lateness > 30 days, or an invoice unpaid > 60 days, or a won deal never cashed |
| **—** | Fewer than 2 paid invoices → **unrated** (never a guessed score) |

⚠️ The score describes **payment behavior observed on this account** — not general creditworthiness; restated in every report.

## 🧪 Holds up on messy data

- Same client under five spellings ("ACME STUDIO", "Acme Studio SARL"…) → normalized, merged, shown as one
- CRM company with no Qonto counterpart (or vice versa) → listed as unmatched, excluded from writes, never force-matched
- Deals without amounts → flagged as unquantified instead of guessed
- Fewer than 2 paid invoices → unrated, with the reason
- Partial payments and instalments cumulated per invoice; refunds deducted from revenue
- No CRM connected → the skill says so and still delivers the scored-clients report
- Empty account → nothing invented; the skill states what it cannot compute

## 📤 Output formats (where does the truth land?)

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables: scored clients, won-not-cashed deals, mapping table, write-back summary | **Always** — the baseline |
| **CRM write-back** | HubSpot custom properties / Airtable columns (dedicated fields) | After confirmed matching + explicit go |
| **HTML one-pager** | CRM ranking vs bank ranking side by side, score distribution | When the host renders files; automatic fallback to tables otherwise |

## 🎬 Demo video

The ≤ 3-minute demo attached to the PR walks through: the CRM lie → bank truth & confirmed matching → scores and gaps → **the write-back after confirmation** → degraded mode without a CRM. All demo records are invented.

## 💡 Roadmap ideas

- Chase won-but-never-cashed deals automatically via `qonto-invoice-chaser` — one skill discovers, the other acts
- Payer score surfaced at quote time (`list_quotes`): warn before signing a C payer
- Score history (dated column) to spot clients drifting from A to C
- More CRMs (Notion, Salesforce…) through the same dynamic detection — read, match, confirm, write

## 🛡 Guardrails

- **Zero Qonto writes** — pure read on the bank side; the only writes target the CRM
- NEVER writes to the CRM without (a) a confirmed mapping table and (b) an explicit go on an exact preview; never presented as done if it failed or was partial
- Assisted matching, **never silent**: ambiguous pairs are asked, not decided
- Honest degradation: unrated under 2 paid invoices · counterparty-level without invoices · conversation report without a CRM
- IBANs masked (last 4 digits) · pagination ≤ 50 everywhere · rehearse writes on a duplicated Airtable base or test properties (CRM writes are real)

---

*Submission docs: `SKILL.md` (the skill itself) · step-by-step guide: `docs/PROCEDURE.en.md` · rich docs in `docs/` (HTML & DOCX, FR/EN).*
