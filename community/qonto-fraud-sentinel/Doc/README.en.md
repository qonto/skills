# 🛡 qonto-fraud-sentinel — The account's bodyguard

> **Qonto × Anthropic MCP Hackathon submission** · Agent Skill for the Qonto MCP
> A 30-second morning scan of the latest transactions against a numbered baseline. One possible write (a card lock), always proposed, never automatic.

---

## 🎯 Why this matters (usefulness)

Fraudulent or abnormal debits usually get discovered too late — on the statement, or never. `qonto-fraud-sentinel` screens the latest transactions against a **numbered baseline** built from the account's real history:

1. **Six anomaly signals** — never-seen beneficiary, amount 3×+ the counterparty's average, duplicate direct debit, unusual hour or channel, bursts of small card debits (the stolen-card testing pattern), first SEPA direct debit from a new creditor
2. **Every alert is explained** — the transaction, why it's unusual with numbers ("€612 vs €148 average over 14 debits = ×4.1"), the recommended action, a severity tag 🔴🟠🟡
3. **A signal is not a fraud** — the skill says "unusual, worth verifying", never "fraud detected". False positives are expected and explained; you mark trusted counterparties in one message
4. **One safe action** — a card lock (`change_card_status`) is **proposed** when a card is implicated, executed only after your explicit confirmation; unlocking and definitive opposition stay in the Qonto app

Would someone use this on a Monday morning? It *is* the Monday morning — 30 seconds, coffee in hand, before the inbox.

## 📋 Prerequisites

| Prerequisite | Detail | Required |
|---|---|---|
| Qonto **production** account | The skill adapts to any organization — `get_organization` first, nothing hardcoded | ✅ |
| Country | **Behavioral, SEPA-universal signals**: identical across all Qonto countries (FR, DE, ES, IT, AT, NL, BE, PT) — only wording adapts | ℹ️ detected |
| Qonto MCP connected | Official connector (claude.ai / Claude Desktop), OAuth login | ✅ |
| ≥ 3 months of history | Below that: **cautious mode announced** — thinner baseline, more false positives, alerts phrased tentatively | ⭕ recommended (3–6 months to calibrate) |
| Gmail MCP | Optional enrichment: a daily digest email draft — detected dynamically, the core runs without it | ⭕ optional |

## ⚙️ How it works

![How it works](assets/flow.en.png)

1. **Calibrate the baseline** (3–6 months, paginated ≤ 50): per normalized counterparty — occurrence count, mean and max amount, cadence, first/last seen, typical operation type and hours. Card transactions are dated on **`emitted_at`** (not `settled_at`: the 1–2 day settlement lag would corrupt duplicate and timing detection)
2. **Scan the window**: since the last scan, or the last 48–72 h on a first run — widen it on demand ("this week", "since the 1st")
3. **Screen the six signals** (reference table below) — trusted counterparties skip "never seen" and "first SEPA" but stay screened for amounts and duplicates
4. **Ranked, explained alerts** 🔴🟠🟡 — and when nothing triggers, the skill says so with the scan window and baseline depth: **a clean "all clear" report is the product, not a failure**
5. **Card lock proposed** (only when a card is implicated + explicit confirmation): `change_card_status` — never automatic
6. **Trust memory**: "*trust MAIF*" → remembered in the conversation/project, no more never-seen alerts for that counterparty

## 🏗 Functional diagram

![Functional diagram](assets/functional.en.png)

**The security model** (not a limitation): solid arrows are risk-free reads; the dashed arrow is a **card lock** — reversible, proposed in reaction to a card alert, executed only after explicit confirmation in the conversation. Unlocking, definitive opposition, SEPA mandate revocation and card replacement stay in the Qonto app, in the account holder's hands. No money moves, under any scenario.

## 🚨 The six reference signals

| Signal | Criterion (numbered baseline) | Recommended action |
|---|---|---|
| **Never-seen beneficiary** | First outgoing occurrence of a counterparty over 3–6 months | Verify — a legitimate new supplier? Mark it trusted |
| **Unusual amount** | ≥ 3× that counterparty's average (or the category's, when new) | Check the matching invoice / contract |
| **Duplicate debit** | Same counterparty, same amount (±1 %), 1–5 days apart | Verify; dispute the duplicate with the creditor or via the app |
| **Unusual hour / channel** | Card payment at an hour never seen for that counterparty; a never-used operation type | Verify; suspicious card → lock proposed |
| **Small-debit burst** | ≥ 3 small debits (bottom decile or < €10) within minutes/hours | Stolen-card testing pattern → lock proposed (`change_card_status`) |
| **First SEPA from a new creditor** | First direct debit from a creditor absent from the baseline (a mandate just got used) | Check the mandate; oppose via the app if unrecognized |

## 🧪 Holds up on messy data

- Under 3 months of history? → cautious mode announced, tentative wording, more false positives — assumed and explained
- A brand-new legitimate supplier? → flagged as "never seen" by design; the skill says so and offers trust-marking, it never cries wolf
- Empty scan window or empty account? → "nothing to scan" with the facts, nothing invented
- Card settlement lag (`emitted_at` vs `settled_at`), noisy transaction labels (references, dates) normalized before matching — all handled
- Multi-account organizations: each account gets its own baseline and its own scan

## 📤 Output formats

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown alert table (transaction · signal · baseline · action · severity) or a numbered "all clear" | **Always** — the baseline |
| **Morning report** | Compact **HTML** file/artifact: ranked alerts, baseline, card status | When the host renders files; automatic fallback to the table |
| **Email digest** | Gmail draft of the daily scan | Only when a Gmail MCP is detected — optional |

## 🎬 Demo video

The ≤ 3-minute demo attached to the PR walks through: the problem → the baseline → the signals in action → **the morning routine, live (a first-SEPA alert, trust-marked in one message)** → wrap-up. It runs live on a real production account.

## 💡 Roadmap ideas

- Scheduled scan (the morning prompt becomes an automated routine)
- User-tunable thresholds (×2, ×5, amount floor) — the baseline stays the smart default
- Per-counterparty 12-month risk score, reusing the baseline engine
- Telegram/Slack alert when the MCP is present — same optional multi-MCP logic as Gmail

## 🛡 Guardrails

- **Never the word "fraud"** — "unusual, worth verifying". A first payment to a new supplier is normal business life, not an incident
- NEVER calls `change_card_status` without explicit confirmation in the current conversation; never presented as done if the call failed
- Honest degradation under 3 months of history · masked IBANs and card numbers (last 4 digits) · pagination ≤ 50 · card timing on `emitted_at`

> **See also**: `qonto-supplier-detective` — historical supplier invoices and money recovery. Sentinel is its security-focused sibling: real-time and daily, not archaeology.

---

*Submission docs: `SKILL.md` (the skill itself) · step-by-step guide: `docs/PROCEDURE.en.md` · rich docs in `docs/` (HTML & DOCX, FR/EN).*
