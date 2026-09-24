# 🌍 qonto-carbon-ledger — Your bank statement is secretly a carbon ledger

> **Qonto × Anthropic MCP Hackathon submission** · Agent Skill for the Qonto MCP
> **100 % read-only**: the skill estimates and explains — it never writes, never moves money, never sells anything.

---

## 🎯 Why this matters (usefulness)

Small businesses never do a carbon assessment — not because they don't care, but because they have **no data**, no time, and no budget for a consultant. Here's the thing: bank debits ARE data. Every euro spent has a footprint, and `qonto-carbon-ledger` reads it straight from the Qonto account:

1. **Approximate annual footprint** — spend-based method: debits classified into emission categories × **monetary emission factors** (kgCO2e/€, ADEME-style monetary ratios), embedded statically, **sourced and dated** — with the ±50 % uncertainty printed on every figure
2. **Dominant categories** — the 2-3 categories that concentrate most emissions, matched to the amounts actually spent
3. **Trend** — across 24–36 months of history, year over year
4. **Top-3 levers** — the most effective actions given real spending (lever #1 is often free), and never a carbon offset for sale

It's an orientation **pre-assessment**, not a regulatory report — and the skill says so itself, loudly. Would someone run this on a Monday morning? It's the first carbon number most small businesses will ever see — and it costs them two minutes.

## 📋 Prerequisites

| Prerequisite | Detail | Required |
|---|---|---|
| Qonto **production** account | Adapts to any organization — `get_organization` first, nothing hardcoded | ✅ |
| Country | **Factors calibrated for France / EU.** Other Qonto countries (DE, ES, IT…): identical method, factors flagged as needing adaptation (electricity mix, price levels) — stated plainly, estimate still produced and tagged | ℹ️ detected |
| Qonto MCP connected | Official connector (claude.ai / Claude Desktop), OAuth login | ✅ |
| ≥ 6 months of history | Below that: annualization with an explicit warning, never silent extrapolation. 24–36 months for the trend | ⭕ |
| Datagouv MCP | Optional — cross-checks factors against current ADEME datasets; otherwise the embedded (sourced, dated) factors are used | ⭕ |
| Qonto labels | Optional — sharpen the classification of ambiguous debits | ⭕ |

## ⚙️ How it works

![How it works](assets/flow.en.png)

1. **Read the ledger** (24–36 months, paginated ≤ 50, debit side): transactions per account + labels + supplier invoices — the raw material already exists, nothing to type in
2. **Honest scope**: the spend-based method covers purchased goods, services and energy. Excluded and **announced as excluded**: internal transfers, salaries, taxes, VAT payments, loan repayments, dividends — financial flows carry no emission factor
3. **Classify into categories**: normalized counterparties (spellings merged) + labels + supplier invoices → energy (fuel / electricity / gas separated when possible — factors differ ×10), travel (air / rail / road), digital & cloud, purchased goods, services, catering, insurance & bank fees. Ambiguous debits land in a visible "unclassified" bucket with its share disclosed
4. **Convert to excl-VAT**: monetary factors apply to net amounts — `vat_amount` when present, else ÷ 1.20 (disclosed). Large one-off purchases (≥ ~€5,000) are flagged apart so a single investment doesn't masquerade as a recurring emission
5. **Monetary factors**, embedded (ADEME Base Empreinte-style monetary ratios, 2023–2024 vintage) — every line displayed with source + vintage; Datagouv cross-check offered when that MCP is present
6. **Report**: footprint ~N tCO2e/year **with its range**, category breakdown, trend, top-3 levers ranked by estimated impact and cost direction (free / saves money / costs money)

## 🏗 Functional diagram

![Functional diagram](assets/functional.en.png)

**Solid arrows only**: this skill is 100 % read. No write, no transfer request, no payment — there is literally nothing to approve. The only deliverable is information: tables and a dashboard.

## 🧪 Holds up on messy data

- Untagged VAT on debits? → net amounts estimated at ÷ 1.20, with the count of estimated lines disclosed
- Ambiguous counterparties? → visible "unclassified" bucket; above ~20 % of spend the skill says the estimate is weak and suggests labelling the top counterparties
- Short history? → annualized with an explicit warning, never silently extrapolated
- A €20,000 machine bought once? → flagged as a one-off, not blended into the recurring footprint
- Non-French account? → same method, factors flagged as needing local adaptation — no fake calibration
- Empty account? → the skill explains the method and what data it would need, and stops there

## 📤 Output formats (where does the footprint land?)

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables: footprint + range, category breakdown (factor, source, vintage per line), trend, top-3 levers | **Always** — the baseline |
| **Interactive dashboard** | **HTML** file/artifact: footprint gauge with uncertainty band, category bars, trend, levers | When the host renders files (claude.ai artifacts, Claude Desktop, Claude Code); automatic fallback to tables otherwise |

## 🎬 Demo video

The ≤ 3-minute demo attached to the PR walks through: the problem (small businesses "have no data") → reading and classifying the account → the honesty about uncertainty → **the "your footprint in two minutes" moment** → the dashboard and the levers. It runs live on a real production account. The detailed shooting script is kept internal (out of the repo).

## 💡 Roadmap ideas

- Automatic Datagouv cross-check (up-to-date ADEME reference datasets) — optional multi-MCP, detected dynamically
- **Per-country factor packs** (DE · ES · IT · AT · NL · BE · PT) — Qonto is pan-European; same method, local electricity mix and prices
- Sector comparison of the footprint — natural pairing with `qonto-sector-benchmark` (same spirit: your real flows × public reference data)
- Monthly lever tracking — is the footprint actually going down?
- Line-item refinement from rich supplier invoices

## 🛡 Guardrails

- **Order-of-magnitude estimate, not a regulatory carbon report** (BEGES / CSRD / GHG Protocol) — repeated in every report; for an official assessment: a specialized provider
- Every factor shown with its **source and vintage**; every figure with its **range** — no false precision ("~9 tCO2e (4.5–13.5)", never "9.37")
- **Never sells or recommends carbon offsets**
- 100 % read-only · IBANs masked (last 4 digits) · pagination ≤ 50 everywhere

---

*Submission docs: `SKILL.md` (the skill itself) · step-by-step guide: `docs/PROCEDURE.en.md` · rich docs in `docs/` (HTML & DOCX, FR/EN).*
