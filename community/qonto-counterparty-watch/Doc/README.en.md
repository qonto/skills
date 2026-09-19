# 🔭 qonto-counterparty-watch — Know who owes you money… and who's sinking

> **Qonto × Anthropic MCP Hackathon submission** · Agent Skill for the Qonto MCP
> Legal-health radar for clients & suppliers: Qonto exposure × French public registries (SIRENE, BODACC)
> **100 % read-only** — the skill never writes anything, anywhere

---

## 🎯 Why this matters (usefulness)

An unpaid invoice hurts. An unpaid invoice from a client **already in receivership** may be gone forever — and nobody told you. Late payers and failing counterparties are the silent half of the SMB cash problem: the money you earned but will never see. `qonto-counterparty-watch` turns a Qonto account into a counterparty radar:

1. **Exposure per counterparty** — unpaid client invoices (amounts, ageing buckets), supplier commitments, annualized recurring spend: how much each counterparty really weighs
2. **Real payment behavior** — observed payment date vs `due_date` across history: average delay, worst delay, worsening trends
3. **Legal health** (when a Datagouv MCP is present) — SIRENE (deregistrations, cessations) and BODACC (receivership, liquidation, safeguard), with the verification date on every line
4. **A justified 🟢🟡🔴 risk score** — exposure × legal health × payment delay, and cross-signal alerts like: *"client X owes you N € AND just entered receivership → chase TODAY, by registered mail"*

Would someone run this on a Monday morning? That's exactly when you triage who to chase this week.

## 📋 Prerequisites

| Prerequisite | Detail | Required |
|---|---|---|
| Qonto **production** account | The skill adapts to any organization — `get_organization` first, nothing hardcoded | ✅ |
| Country | **Legal health: France** (SIRENE + BODACC). Other Qonto countries (DE, ES, IT…): graceful degradation — the Qonto-pure core (exposure + delays) works everywhere, no registry ever invented | ℹ️ detected |
| Qonto MCP connected | Official connector (claude.ai / Claude Desktop), OAuth login | ✅ |
| Datagouv MCP (data.gouv.fr) | Detected dynamically. Absent → the skill says so and delivers Qonto-only scoring | ⭕ recommended — activates legal health |
| Counterparty SIREN | Extracted from Qonto client records (`tax_identification_number`: a French VAT number embeds the SIREN) or exact legal name. No SIREN → line marked "not verifiable", stated plainly | ⭕ |
| Invoice history | The more paid invoices, the more reliable each client's measured delay | ⭕ |

## ⚙️ How it works

![How it works](assets/flow.en.png)

1. **Counterparty inventory**: clients from `list_clients` + invoices, suppliers from `list_supplier_invoices` + `list_transactions` (12–24 months, paginated ≤ 50). **Name normalization** — bank labels are messy (SEPA noise, references, legal suffixes): the skill merges Qonto client records with transaction counterparties on a normalized key
2. **Exposure per counterparty**: unpaid client invoices at due date (0–30 / 31–60 / 61–90 / 90+ day buckets), supplier invoices to pay, annualized recurrence
3. **Payment behavior**: observed payment date − `due_date` per client → average delay, worst delay, trend (a client sliding from 15 to 45 days is a signal even with zero legal events)
4. **Legal health** (Datagouv MCP present): SIRENE (administrative status) + BODACC (collective procedures) by SIREN. **Honesty is a feature**: every verdict carries its evidence — "✅ verified on BODACC on DD/MM, nothing found" vs "⚠️ not verifiable"; BODACC coverage through data.gouv can be partial, and the skill says so
5. **🟢🟡🔴 score**: exposure × legal health × delay, justified in one line per counterparty
6. **Report & alerts**: sorted risk table, cross-signal priority alerts, coverage note (verified / not verifiable), optional HTML dashboard

## 🏗 Functional diagram

![Functional diagram](assets/functional.en.png)

**The key point**: every arrow is solid — **100 % read-only**. The skill creates nothing, modifies nothing, sends nothing. It crosses two worlds that never talk to each other: your Qonto account (who owes you what) and the French public registries (who is going under). Data flows out; nothing flows in.

## 🧪 Holds up on messy data

- Messy bank labels (SEPA prefixes, payment references, "SARL"/"SAS" suffixes)? → normalized and merged with Qonto client records; the raw label is kept for display
- No SIREN on a client record? → name-only match flagged as lower confidence, or "not verifiable" — never silently skipped
- No Datagouv MCP? → announced once, Qonto-pure scoring delivered (exposure + measured delays are already actionable)
- Registry gap? → "nothing found" is reported as exactly that, with the check date — never inflated to "guaranteed healthy"
- Empty account, no invoices, non-French counterparties → the skill says what it can and can't assess instead of pretending
- Pagination ≤ 50 everywhere; multi-account organizations handled per account

## 📤 Output formats (where does the risk table land?)

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables (sorted risk table, alerts, coverage) | **Always** — the baseline |
| **Interactive dashboard** | **HTML** file/artifact: exposure × health matrix, ageing chart, alert cards | When the host renders files (claude.ai artifacts, Claude Desktop, Claude Code); automatic fallback to tables otherwise |
| **Coverage note** | Verified / not verifiable / registry unavailable counters | Every report — honesty is part of the deliverable |

## 🎬 Demo video

The ≤ 3-minute demo attached to the PR walks through: the problem → the risk table on a real account → **the cross-signal moment** (a real overdue invoice meeting a BODACC procedure) → the dashboard. It runs live on a real production account.

## 💡 Roadmap ideas

- **European registry modules** (Handelsregister DE, Registro Mercantil ES…) — Qonto is pan-European; v1 = France, v2 = one registry module per country
- Dunning-email draft when a Gmail MCP is detected (draft only, never auto-sent) — optional multi-MCP enrichment
- Scan-over-scan diff ("new 🔴 since Monday") — the Monday ritual becomes a delta, not a full report
- Supplier-dependency score (share of spend) — same inventory, highlights single-point-of-failure suppliers

## 🛡 Guardrails

- **100 % read-only** — no Qonto write tool is ever called; nothing to approve, nothing to execute
- Never a legal status without **source + date**; "nothing found" ≠ "guaranteed healthy" when coverage is partial
- Alerts are signals, not legal advice: open procedure → confirm on bodacc.fr and talk to a lawyer/accountant
- Honest degradation: no Datagouv → Qonto-pure scoring, announced; non-French counterparties → exposure + delays only
- IBANs masked (last 4 digits) · pagination ≤ 50 everywhere

---

*Submission docs: `SKILL.md` (the skill itself) · step-by-step guide: `docs/PROCEDURE.en.md` · rich docs in `docs/` (HTML & DOCX, FR/EN).*
