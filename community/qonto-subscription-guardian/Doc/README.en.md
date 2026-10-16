# 🛡 qonto-subscription-guardian — One capped card per subscription

> **Qonto × Anthropic MCP Hackathon submission** · Agent Skill for the Qonto MCP
> A pure action utility: lists your recurring charges, lets you pick, then gives each chosen subscription its own capped virtual card — one at a time, behind your own SCA.
> For the full recurring-spend audit (annual cost, zombies, duplicates, price increases): **`qonto-subscription-audit`**

---

## 🎯 Why this matters (usefulness)

Every subscription charges whatever it wants on YOUR main card. This skill does one thing, well: **generate capped virtual cards, one per subscription — nothing more.**

1. **Light detection** — recurring charges across **24–36 months** of history (wide enough to catch **yearly** subscriptions, which need 2 occurrences more than 12 months apart): normalized counterparty, **monthly, quarterly or yearly** cadence, amount stable ±15 %. A simple candidate list, no verdicts
2. **You pick** — the skill counts your existing cards (`list_cards`), recalls your plan's grid and proposes a **number of cards that fits it** — never a bulk run
3. **One capped card PER chosen subscription** — virtual `create_card` + `payment_monthly_limit` = current price + a small margin (yearly: `payment_transaction_limit`), **one at a time, explicit consent + SCA every time**
4. **Nickname `SUB-<Vendor>`** via `update_card` — and existing `SUB-` cards are recognized, never proposed twice (idempotence)

**The honest pitch**: dedicated-card protection is a feature Qonto will probably ship natively one day — this skill gives it to you today.

## 📋 Prerequisites

| Prerequisite | Detail | Required |
|---|---|---|
| Qonto **production** account | The skill adapts to any organization — `get_organization` first, nothing hardcoded | ✅ |
| Qonto MCP connected | Official connector (claude.ai / Claude Desktop), OAuth login | ✅ |
| Owner/Admin/Manager role | To create cards directly; other roles fall back to `create_card_request` (approved by an admin) | ⭕ for the action — detection works for everyone |
| Plan virtual-card allowance | **Basic: 2 included (€2/month beyond) · Smart/Premium: 50 included (€1/card beyond) · Essential/Business/Enterprise: unlimited**. The exact plan isn't readable via MCP (`get_subscription` → 403): the skill counts existing cards, states this public grid and asks for your plan | ℹ️ checked before any proposal |
| **≥ 24 months of history recommended** | To catch **yearly** subscriptions; below that, yearly ones can slip under the radar — stated honestly | ⭕ |

## ⚙️ How it works

![How it works](assets/flow.en.png)

1. **Map the account**: `get_organization` first, then existing cards via `list_cards` — `SUB-` cards already in place are recognized (never proposed twice), and the count feeds the plan check
2. **Light detection** (24–36 months, paginated ≤ 50, 3-month windows): normalized counterparty + cadence 28–32 d / 85–95 d / **350–380 d (yearly)** + amount ±15 % + ≥ 3 occurrences (2 for yearly). Card charges AND direct debits. Matched on `emitted_at` — `settled_at` lags 1–2 days and breaks cadence math. Output: one candidate table — vendor, price, cadence M/Q/**Y**, paying card, already guarded or not
3. **Plan reminder**: the public 2/50/unlimited grid + the card count — the skill proposes a number of cards that fits the plan you announce
4. **You pick** the subscriptions to protect, one by one
5. **One capped card per subscription**: virtual `create_card`, monthly cap = price + margin (yearly: per-transaction cap); **each creation is an SCA action** — the call blocks until you confirm the Qonto push notification; nickname `SUB-<Vendor>` set right after via `update_card`
6. **Switch**: change the payment method at each protected vendor (`get_card_iframe_url`, for your eyes only); final recap of the created cards

## 🏗 Functional diagram

![Functional diagram](assets/functional.en.png)

**The security model** (not a limitation): solid arrows are risk-free reads; the dashed arrow requires explicit consent in the conversation AND the user's SCA — `create_card` **blocks until the push notification is confirmed on the user's paired Qonto device**, for EACH card. Depending on the role, direct creation may not be allowed at all: the skill then falls back to `create_card_request` and says so plainly. Neither Claude nor the MCP can spend a euro.

## 🧪 Holds up on messy data

- Merchant names full of noise (`ADOBE *CC PARIS`, `GOOGLE*CLOUD IE`)? → normalized before matching, so one vendor = one line
- Amount wobbles (VAT rounding, FX, seat changes)? → ±15 % stability band
- Card settlement delays? → cadence matched on `emitted_at`, not `settled_at`
- Short history? → the skill lists what it sees and states that yearly subscriptions may be invisible below 24 months
- Empty account, no recurring charges? → says so, proposes nothing, invents nothing
- Restricted role or plan card quotas? → honest fallback: detection for everyone, `create_card_request` when direct creation isn't allowed; plan allowances (Basic 2 · Smart/Premium 50 · higher plans unlimited) aren't readable via the connector — the skill counts cards, states the grid, and sizes its proposal to your plan

## 🔁 A SUB- card's lifecycle

| Step | Tool | Note |
|---|---|---|
| Capped creation | `create_card` (virtual, cap = price + margin) | Explicit consent + SCA, one card at a time |
| Naming | `update_card` → `SUB-<Vendor>` | `create_card` has no nickname field |
| Switch at the vendor | `get_card_iframe_url` (PAN/CVV) | Manual step — short-lived URL, for your eyes only |
| Reversible pause | `change_card_status` → `lock` | Warns first: a declined charge can suspend the service |
| Permanent removal | `change_card_status` → `discard` | The contract survives — capping ≠ cancelling |
| Adjusting a cap | Qonto app only | Card limits are **not editable via MCP** — stated plainly |

## 📤 Output formats

| Output | Format | When |
|---|---|---|
| **Candidate list** | Markdown table: vendor · price · cadence M/Q/Y · paying card · already guarded | After light detection |
| **Created-cards recap** | Markdown table: card · cap · vendor · still to switch | End of session |

## 🎬 Demo video

The ≤ 3-minute demo attached to the PR walks through: the problem → the candidate list + the plan grid → the user's pick → **THE capped card created live, SCA confirmation filmed on a phone, the card visible in the app with its cap** → "every subscription now has its own box" + wrap-up. It runs live on a real production account.

## 💡 Roadmap ideas

- Auto-categorize protected subscriptions in Qonto (`modify_transaction_cash_flow_category`) so SUB- lines read in the app too
- Public price benchmark per tool (web search) to size the cap at the fair price
- Multi-currency subscriptions (USD/GBP) — amount normalization before the stability check

## 🛡 Guardrails

- NEVER creates a card (or card request) without explicit confirmation for THAT card in the current conversation; never presented as done while SCA confirmation is pending
- Plan check first, always: `list_cards` count + the 2/50/unlimited grid before any proposal — a number of cards that fits, never a bulk run
- **Capping ≠ cancelling**: the contract survives the card — a declined charge can trigger vendor dunning or service suspension, stated BEFORE acting
- Card numbers and IBANs masked (last 4 digits) · pagination ≤ 50 everywhere
- `get_card_iframe_url` output is a short-lived credential for the user's eyes only — never echoed, logged or stored

---

*Submission docs: `SKILL.md` (the skill itself) · step-by-step guide: `docs/PROCEDURE.en.md` · rich docs in `docs/` (HTML & DOCX, FR/EN).*
