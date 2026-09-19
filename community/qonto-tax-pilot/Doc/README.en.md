# 🧭 qonto-tax-pilot — Predict the taxman, then move the money out of harm's way

> **Qonto × Anthropic MCP Hackathon submission** · Agent Skill for the Qonto MCP
> Battle-tested end-to-end on a real production account: computed provision → transfer request via MCP → SCA approval in the Qonto app → money actually moved.

---

## 🎯 Why this matters (usefulness)

The number-one cash killer for small businesses isn't revenue — it's **VAT money that was already spent** when the tax notice arrives. `qonto-tax-pilot` turns a Qonto account into a tax copilot:

1. **Dated, amount-estimated tax schedule** — when each tax is due and how much (VAT, corporate tax instalments & balance, CFE, dividend flat tax), estimated from the account's real history, every line tagged 🟢 seen in history · 🟡 estimated · 🔵 conditional
2. **90-day cash projection** per account — dated low point, threshold crossings, what-if simulations
3. **Monthly provision** — net VAT (computed **on receipts** when that's the detected regime) + IS/12 + CFE/12
4. **One safe action** — a transfer request to the tax sub-account; money moves **only** after the user's own SCA approval in the Qonto app

Would someone use this on a Monday morning? This is literally a first-of-the-month ritual.

## 📋 Prerequisites

| Prerequisite | Detail | Required |
|---|---|---|
| Qonto **production** account | The skill adapts to any organization — `get_organization` first, nothing hardcoded | ✅ |
| Country | **Full tax calendar: France.** Other Qonto countries (DE, ES, IT…): graceful degradation — generic projection + VAT provisioning, never invented deadlines | ℹ️ detected |
| Qonto MCP connected | Official connector (claude.ai / Claude Desktop), OAuth login | ✅ |
| A "tax" sub-account | Created once in the Qonto app (the MCP has no account-creation tool). Detected by name (tax/taxe/impôt/TVA) | ⭕ recommended — otherwise the skill computes and explains, without acting |
| ≥ 6 months of history | Below that, the skill degrades honestly (🟡 tags + warning) | ⭕ |
| French company at IS | Default assumption; wording adapts otherwise | ⭕ |

## ⚙️ How it works

![How it works](assets/flow.en.png)

1. **Learn from history** (24–36 months, paginated ≤ 50, **covering at least the two previous fiscal years**): tax cadences (quarterly corporate-tax instalments, December CFE, VAT rhythm) only become visible across full years, and year-over-year comparison feeds the projection. **Automatic detection of the VAT regime AND filing frequency** — monthly or quarterly CA3 (quarterly when annual VAT < €4,000), simplified regime (two instalments + CA12), and accrual vs **cash-basis VAT** (`vat_payment_condition: "on_receipts"` means VAT follows client *payments*, not issued invoices). ⚠️ The simplified regime is **abolished on 2027-01-01** (2025 Finance Act): the skill warns CA12 users about the switch to CA3
2. **Tax schedule**, dated and amount-estimated (reference table in SKILL.md)
3. **90-day projection**: balance + recurrences + unpaid client invoices (adjusted by each client's historical payment delay) + supplier invoices + the tax schedule
4. **This month's provision**: collected VAT (matched to incoming payments when cash-basis) − deductible VAT (summed `vat_amount`, announced as a floor when debits are untagged) + IS/12 + CFE/12
5. **Transfer request** (explicit user consent only): `create_multi_transfer_request`, full calculation embedded in the request note — visible at approval time
6. **SCA approval** in the Qonto app → money moves → final report

## 🏗 Functional diagram

![Functional diagram](assets/functional.en.png)

**The security model** (not a limitation): solid arrows are risk-free reads; the dashed arrow requires explicit consent given in the conversation and only produces a *request*. The account holder's own SCA (2FA) in the Qonto app is what moves money. Neither Claude nor the MCP can.

## 🧪 Holds up on messy data

- No transactions? → schedule from public rules, everything tagged 🟡, no action proposed
- Untagged VAT on debits? → deductible estimate announced as a floor, count of unknowns disclosed
- No tax sub-account? → computations shown + one-time setup instructions
- Multi-account orgs, credit-card settlement delays (`emitted_at` vs `settled_at`), refunds reducing collected VAT — all handled
- Non-French or non-IS company → the skill says what it can and can't estimate instead of pretending

## 📤 Output formats (where does the schedule land?)

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables (schedule, provision, alerts) | **Always** — the baseline |
| **Interactive dashboard** | **HTML** file/artifact: 90-day curve, schedule ✅/⚠️, vault gauge | When the host renders files (claude.ai artifacts, Claude Desktop, Claude Code); automatic fallback to tables otherwise |
| **Qonto request note** | Text attached to the transfer request, visible at SCA approval time | Every time a provision is created |

## 🎬 Demo video

The ≤ 3-minute demo attached to the PR walks through: the problem → tax schedule & projection → the provision → **the SCA approval filmed on a phone** → the final dashboard. It runs live on a real production account.

## 💡 Roadmap ideas

- URSSAF/social contributions for TNS managers (EURL) — widens the audience beyond IS companies
- **European country modules** (DE · ES · IT · AT · NL · BE · PT) — Qonto is pan-European; v1 = France + country detection, v2 = one tax-calendar module per country
- Optional multi-MCP enrichment: tax deadlines pushed to the user's calendar when a calendar MCP is detected
- Full-year corporate-tax landing estimate
- Interactive what-if artifact (sliders for client delays / purchases)

## 🛡 Guardrails

- NEVER creates a transfer request without explicit confirmation in the current conversation; never presented as executed — it is pending the user's SCA approval
- Estimates ≠ filings: accountant validation recommended in every report
- Honest degradation under 6 months of history · IBANs masked (last 4 digits) · pagination ≤ 50 everywhere

---

*Submission docs: `SKILL.md` (the skill itself) · step-by-step guide: `docs/PROCEDURE.en.md` · rich docs in `docs/` (HTML & DOCX, FR/EN).*
