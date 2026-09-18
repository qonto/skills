# 🔎 qonto-grant-scout — The grant hunter your account deserved

> **Qonto × Anthropic MCP Hackathon submission** · Agent Skill for the Qonto MCP
> Your bank account knows what you invest in — public databases know who gets helped for it. This skill introduces them.

---

## 🎯 Why this matters (usefulness)

France runs hundreds of public aid schemes for small businesses — training funds, energy-transition grants, regional investment aid, digital-transformation cheques. Most SMEs claim none of them, because nobody has time to dig. Yet the answer to "what could I claim?" is already written in the bank account. `qonto-grant-scout`:

1. **Profiles the company from the account** — sector (NAF code when present, inferred from the flows otherwise), region, size (incoming volume), age: `get_organization` first, zero forms
2. **Reads the real spending structure** — 12–24 months of flows classified into aid-relevant categories: training, equipment, digital, hiring, export, energy — each one priced in €/year with evidence
3. **Cross-references public aid referentials** — via the Datagouv MCP (optional, detected dynamically): dataset search on data.gouv.fr, **update date checked on every source**
4. **Shortlists honestly** — every lead: what it covers, why this account matches, criteria to confirm, dated source, one concrete next step. Never "you are eligible" — always "worth checking, here's why"

Would someone use this on a Monday morning? "Am I leaving public money on the table?" is a question every founder asks — and never has time to answer.

## 📋 Prerequisites

| Prerequisite | Detail | Required |
|---|---|---|
| Qonto **production** account | The skill adapts to any organization — `get_organization` first, nothing hardcoded | ✅ |
| Country | **Scheme cross-referencing: France only** (aid schemes are national/regional). Other Qonto countries (DE, ES, IT…): spending profile only, generic aid families, no foreign scheme ever invented | ℹ️ detected |
| Qonto MCP connected | Official connector (claude.ai / Claude Desktop), OAuth login | ✅ |
| Datagouv MCP | The data.gouv.fr connector — it unlocks the referential search. Absent: the skill says so and still delivers the profile + generic aid families + official portals | ⭕ recommended — honest degraded mode otherwise |
| ≥ 12 months of history | Below that, spending signals are fragile — the skill says so (🟡 tags) | ⭕ |
| Qonto labels maintained | Improve spending classification (`list_labels`); counterparty-based classification otherwise | ⭕ |

## ⚙️ How it works

![How it works](assets/flow.en.png)

1. **Real profile**: legal form, sector (NAF when present — inferred from flows otherwise, and flagged as such), region, age, size. The profile is shown to the user, who can correct it before any search
2. **Read the flows** (12–24 months, paginated ≤ 50): debits classified into aidable categories — training, equipment/CAPEX, digital, R&D-like, hiring, international, energy. Labels used when available (`list_cash_flow_categories` → 403 on the claude.ai connector; labels are the fallback). Card spending matched by `emitted_at`
3. **Aidable signals**: every significant category becomes a dated, quantified signal — €9,600/year on training, an equipment purchase, growing payroll, foreign clients
4. **Datagouv search**: `search_datasets` across the aid referentials (national aid database, ADEME, France Num, Bpifrance, regional schemes), `get_dataset_info` for **each dataset's update date**, `query_resource_data` to filter by region/sector/family
5. **Cross & shortlist**: signals × schemes, every lead with criteria to confirm + dated source + one next step (training fund, ADEME portal, region's desk, Bpifrance advisor)
6. **Honest report**: shortlist ranked by plausibility, 🟢🟡🔵 tags, and a limits paragraph — what was searched, what wasn't found, which datasets were stale

## 🧪 Holds up on messy data

This is the creative bet of the portfolio — and the one that leans hardest on data nobody controls. So honesty is built in:

- Aid referentials on data.gouv.fr are **heterogeneous and sometimes stale** → every lead carries its source AND the dataset's update date; > ~18 months = degraded tag
- The skill says "**worth checking**", never "you are eligible" — schemes open, close, and change criteria
- Resource not queryable (PDF, malformed CSV)? → the lead becomes a sourced link to the dataset page, stated as such
- Datagouv MCP absent or failing? → spending profile + generic aid families + the right official portals, stated plainly
- Sector missing from `get_organization`? → inferred from the flows, confidence lowered, user can correct
- Empty account, thin history, non-French company → the skill states what it can and cannot do instead of pretending

## 🏗 Functional diagram

![Functional diagram](assets/functional.en.png)

**Zero writes**: the skill touches nothing — no transfer, no invoice, no application filed. And on the data side: only **generic search keywords** (sector, region, aid family) ever reach Datagouv — never an amount, a counterparty name, or an IBAN. The banking data stays between Qonto and Claude.

## 📤 Output formats

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables: profile + signals, sourced and dated aid shortlist, limits | **Always** — the baseline |
| **Grant radar** | **HTML** file/artifact: signals × aid families, leads at the intersections, 🟢🟡🔵 tags | When the host renders files (claude.ai artifacts, Claude Desktop, Claude Code); automatic fallback to tables otherwise |
| **Per-lead brief** | Ready-to-send text block (to the training fund, the accountant, the regional desk): signal, scheme, criteria to confirm, source | On request, for each retained lead |

## 🎬 Demo video

The ≤ 3-minute demo attached to the PR walks through: the problem (aid nobody goes hunting for) → the profile emerging from the flows alone → the dated, sourced Datagouv search → **the crossing** (€9,600/year of training spend spotted → the exact scheme, the link, and what to ask the training fund) → honesty by design. It runs live on a real production account.

## 💡 Roadmap ideas

- Quarterly re-scan: re-cross the profile and alert only on *new* leads
- Aides-territoires enrichment (dedicated API) — fresher than some datasets, same dating discipline
- Pre-filled brief: draft the email to the training fund / regional desk with the account's numbers — still zero writes, the user sends it
- Country modules (DE: KfW · ES: ENISA · IT: Invitalia…) — Qonto is pan-European; v1 = France + country detection

## 🛡 Guardrails

- **Zero writes**; only generic keywords reach Datagouv — never amounts, names, or IBANs
- **Never "you are eligible"** — every lead is dated, sourced, phrased "to verify"; confirmation with the issuing body or the accountant recommended
- Honest degradation: no Datagouv MCP, empty account, undetectable sector, non-FR country → the skill states its limits and never invents a scheme, an amount, or a deadline
- IBANs masked (last 4 digits) · pagination ≤ 50 everywhere

---

*Submission docs: `SKILL.md` (the skill itself) · step-by-step guide: `docs/PROCEDURE.en.md` · rich docs in `docs/` (HTML & DOCX, FR/EN).*
