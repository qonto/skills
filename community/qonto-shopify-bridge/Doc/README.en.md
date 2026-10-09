# 🌉 qonto-shopify-bridge — What the store claims vs what the bank collects

> **Qonto × Anthropic MCP Hackathon submission** · Agent Skill for the Qonto MCP
> E-commerce payout reconciliation: Shopify/Stripe/PayPal payouts ↔ actual Qonto inflows · **read-only, zero writes**

---

## 🎯 Why this matters (usefulness)

Every Shopify merchant lives with the same blind spot: **gross sales** in the store dashboard, **net payouts** on the bank account — and between the two, fees (Shopify Payments, Stripe, PayPal), refunds, and 2–3 business-day delays. Most merchants never reconcile the two sides; they just trust. This skill checks:

1. **Payout rhythm** — learns each PSP's cadence (Shopify, Stripe, PayPal, SumUp…) and flags every break: a payout that's missing or late
2. **Real fees vs announced** — effective rate computed payout by payout: (gross − net) ÷ gross, compared against your plan's advertised rate (when you provide it — no schedule is ever guessed)
3. **Refunds & chargebacks** — refunded in the store but never reflected on the account (or the reverse): detected and documented
4. **The true margin** — net cash collected per period, after every commission — not the flattering number on the store dashboard

The typical report: "**14 payouts expected, 13 received, 1 late by 4 days; effective fees 2.9% + €0.30, in line with the plan; net collected this month: €X**".

Would someone use this on a Monday morning? That's exactly when last week's payouts should have landed — and when you find out one didn't.

## 📋 Prerequisites

| Prerequisite | Detail | Required |
|---|---|---|
| Qonto **production** account | The skill adapts to any organization — `get_organization` first, nothing hardcoded | ✅ |
| Country | **All Qonto countries** (FR, DE, ES, IT, AT, NL, BE, PT) — payout reconciliation is universal. Multi-currency: reported per currency, never converted silently | ℹ️ detected |
| Qonto MCP connected | Official connector (claude.ai / Claude Desktop), OAuth login | ✅ |
| PSP inflows in the history | Identifiable SHOPIFY / STRIPE / PAYPAL / SUMUP… credits — the raw material of the Qonto-only core | ✅ |
| **Shopify** (or Stripe) MCP connected | Detected dynamically. With it: fine-grained sales ↔ payouts reconciliation. Without it: the skill says so and continues Qonto-only (already useful) | ⭕ recommended |
| ≥ 3 months of PSP history | Below that, cadence detection is announced as low-confidence | ⭕ |

## ⚙️ How it works

![How it works](assets/flow.en.png)

1. **Map the money in**: 12–24 months of credits (paginated ≤ 50), PSP counterparties normalized (SHOPIFY, STRIPE, PAYPAL, SUMUP, ADYEN, MOLLIE…), grouped by provider and by store. Arrival date = `settled_at`
2. **Learn the payout rhythm** (Qonto-only, useful on its own): cadence per PSP (daily on business days, weekly, on-demand), typical delay, typical amount band → an **expected-payout calendar**. Every break becomes an alert. ⚠️ PayPal often works as manual withdrawals — the skill recognizes that pattern instead of raising false "missing payout" alarms
3. **Enrich with the store** (when the Shopify MCP is detected): gross sales, refunds and orders per period (`run-analytics-query`, `list-orders`, `get-order` — Shopify tools, hyphenated names). Multi-store merchants get one reconciliation per store. MCP absent → announced plainly, the skill continues
4. **Reconcile sales ↔ payouts**: a payout groups *n* orders minus fees minus refunds, arriving 2–3 business days later. The skill matches sales windows to received payouts and computes the **effective fee rate**
5. **Detect the gaps**: missing payout (with a **ready-to-send support ticket draft**, all references included — official statement via `list_statements`), unusual delay, fee drift, refund not passed through
6. **Reconciliation report**: tables + net collected + true margin after commissions; HTML dashboard when the host renders files

## 🏗 Functional diagram

![Functional diagram](assets/functional.en.png)

**The key point**: this skill is **pure read** — no write tool on either side, Qonto or Shopify. It reads, matches, documents. The only "action" it produces is text: the support-ticket draft that **you** decide to send. Risk: zero.

## 🧪 Holds up on messy data

- No Shopify MCP? → Qonto-only mode, stated plainly: payout cadence, totals, rhythm breaks — already actionable
- Multiple stores, multiple PSPs? → one lane per store and per provider, consolidated summary on top
- Grouped payouts (n orders → 1 transfer) and 2–3 business-day delays → matched by window + amount proximity, never by naive same-day equality
- PayPal on-demand withdrawals → cadence requalified, no false alarms
- Multi-currency accounts → reported per currency, no silent conversion
- Thin history (< 3 months of PSP inflows) → cadence tagged low-confidence, no invented schedule

## 📤 Output formats

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables (reconciliation, fees, net collected, anomalies) | **Always** — the baseline |
| **Interactive dashboard** | **HTML** file/artifact: payout timeline with gaps highlighted, fee-rate trend, net-per-month bars | When the host renders files (claude.ai artifacts, Claude Desktop, Claude Code); automatic fallback to tables |
| **Support ticket draft** | Ready-to-send text for Shopify/Stripe support, every reference included | Every time a missing payout is detected |

## 🎬 Demo video

The ≤ 3-minute demo attached to the PR walks through: the problem (the store says X, the bank says Y) → payout rhythm in pure Qonto mode → Shopify-enriched reconciliation → **the missing payout caught, support ticket ready** (the "it just works" moment) → the final report with the true margin. It runs live on a real production store and account.

## 💡 Roadmap ideas

- Stripe MCP as a second, symmetric enrichment — same logic, dynamic detection
- Recurring Monday-morning check ("any payout missing from last week?") — the skill is idempotent, just re-run it
- Order-level payout breakdown (payout → exact list of orders) via `get-order`
- Net margin per product, commissions apportioned
- Consolidated multi-PSP view (Shopify + PayPal + SumUp in one report) — the Qonto-only core already does it per PSP

## 🛡 Guardrails

- **Read-only**: no write tool, nothing created or modified — on the Qonto side or the store side
- Never invents a fee schedule: **computed** rates only, sample size shown
- A "missing payout" is a **documented hypothesis**, not an accusation — support has the final word
- Per-currency reporting, no silent conversion · IBANs masked (last 4 digits) · pagination ≤ 50 everywhere
- Honest degradation: no Shopify MCP → Qonto-only announced; thin history → low confidence announced

---

*Submission docs: `SKILL.md` (the skill itself) · step-by-step guide: `docs/PROCEDURE.en.md` · rich docs in `docs/` (HTML & DOCX, FR/EN).*
