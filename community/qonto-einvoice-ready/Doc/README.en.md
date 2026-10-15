# 📥 qonto-einvoice-ready — Ready for France's September 2026 e-invoicing mandate?

> **Qonto × Anthropic MCP Hackathon submission** · Agent Skill for the Qonto MCP
> The readiness audit for the French e-invoicing reform: measures the gap, then closes it — one confirmed record at a time.

---

## 🎯 Why this matters (usefulness)

On **September 1st, 2026**, every French VAT-registered company must be able to **receive** electronic invoices (issuing: 2026 for large companies and mid-caps, 2027 for SMEs). The trap isn't the date — it's the **client file**. No SIREN, no intra-EU VAT number, no structured address = no valid Factur-X, ever. That's exactly the messy data sitting in most Qonto accounts today. `qonto-einvoice-ready` turns the account into a readiness check-up:

1. **Readiness score** — client file complete for Factur-X (SIREN/SIRET, intra-EU VAT, structured address), quality of issued invoices, timeline known, e-reporting exposure — transparent formula, before/after
2. **The timeline that applies to YOU** — company size fetched from the public registry (large / mid-cap / SME) or asked, never guessed → "receiving mandatory in N weeks; issuing mandatory for you in 2026 or 2027"
3. **E-reporting exposure** — foreign and consumer (B2C) clients spotted in the records AND in the real money flows: outside e-invoicing, but subject to transaction-data transmission
4. **Live fix** — SIRENs recovered from the **public French company registry API** (data.gouv, no key), intra-EU VAT derived from the SIREN, line-by-line preview → `update_client` **only after your confirmation**, never in bulk

Would someone run this on a Monday morning? With a legal deadline counting down for every French business, this is the Monday-morning question of 2026.

## 📋 Prerequisites

| Prerequisite | Detail | Required |
|---|---|---|
| Qonto **production** account | The skill adapts to any organization — `get_organization` first, nothing hardcoded | ✅ |
| Country | **French reform.** Other Qonto countries (DE, ES, IT…): graceful degradation — generic client-file completeness audit, never an invented deadline | ℹ️ detected |
| Qonto MCP connected | Official connector (claude.ai / Claude Desktop), OAuth login | ✅ |
| Client records in Qonto | The raw material of the audit; with none, the skill explains the reform reference and stops there | ⭕ |
| Public registry API reachable | No key, no account; if down, the audit still runs — only the live fix degrades (announced) | ⭕ |
| Company size | Fetched from the registry (`categorie_entreprise`) or asked — sets your issuing date (2026 or 2027) | ℹ️ detected |

## ⚙️ How it works

![How it works](assets/flow.en.png)

1. **Company snapshot**: `get_organization` (always first), country, identity; size fetched from the public registry or asked → applicable timeline, countdown to 2026-09-01
2. **Client-file audit**: every B2B record scored on the 3 identifiers Factur-X requires — SIREN/SIRET (also the key to the central directory), intra-EU VAT number, structured address (one blob in a single field doesn't count). Individuals flagged as B2C
3. **Invoice quality**: over the last 12 months, what share is attached to a complete client record and would pass as Factur-X today? Blockers are named precisely
4. **E-reporting exposure**: foreign + B2C clients, cross-checked against real flows (`list_transactions`) → "X% of your income falls under e-reporting, on the same calendar as your issuing obligation"
5. **Live fix**: registry query by name (+ zip when available); homonyms → the skill **always asks**; intra-EU VAT derived from the SIREN and **labeled as derived**; line-by-line preview (client · field · current → proposed · source) → confirmation → `update_client`, field by field
6. **Score & action plan**: readiness before/after, what got fixed, what stays on your side — above all the **choice of an accredited platform (PDP), which belongs to you** (the skill lists criteria, never picks)

## 🏗 Functional diagram

![Functional diagram](assets/functional.en.png)

**The security model**: solid arrows are risk-free reads; the dashed arrow is `update_client` — it **never touches money**, only client records, and writes only after the full preview and your explicit confirmation in the conversation. No silent bulk updates, ever; every write is reported as succeeded or failed, honestly.

## 🧪 Holds up on messy data

- No clients at all? → the skill explains the reform reference and the timeline, proposes nothing to fix
- Client named differently from its legal name? → registry search by name + zip; no match → the skill asks for the SIREN or skips
- Homonyms in the registry? → candidates shown (name, city, SIREN), user picks — never auto-matched
- Addresses dumped as one text blob? → counted as incomplete, flagged for restructuring
- Non-French organization? → the French calendar is off the table; generic completeness audit instead, stated plainly
- Registry API down? → the audit and score still run; only the enrichment degrades, announced

## 📤 Output formats

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables: detailed score, incomplete records, timeline, e-reporting exposure | **Always** — the baseline |
| **Fix preview** | One table: client · field · current → proposed · source, pending confirmation | Every proposed fix |
| **Readiness report** | **HTML** file/artifact: before/after gauge, countdown, action plan | When the host renders files (claude.ai artifacts, Claude Desktop, Claude Code); automatic fallback to tables |

## 🎬 Demo video

The ≤ 3-minute demo attached to the PR walks through: the 2026-09-01 wall → audit and score → the live fix (public registry → preview → confirmation) → the after-score and action plan. It runs live on a real production account. The detailed shooting script is kept internal (out of the repo).

## 💡 Roadmap ideas

- Recurring check-up ("re-scan my client file monthly") — the score decays with every new incomplete client
- Intra-EU VAT number validation via the public VIES service — same "public API, no key" pattern
- Supplier-side audit (purchase records) — reuses the scoring engine as-is
- Country modules (DE XRechnung · IT SdI · ES Verifactu…) — Qonto is pan-European; v1 = France + country detection
- Pairs naturally with `qonto-vat-return` (the data this reform feeds) and `qonto-meeting-invoice` (clean invoices from day one)

## 🛡 Guardrails

- **An audit, not legal or tax advice** — stated in every report; edge cases → the company's accountant
- The **PDP choice belongs to the user**: criteria provided, decision never made for them
- Registry homonyms → confirmation, always; derived VAT numbers labeled as derived
- `update_client`: full preview + explicit confirmation, field by field, **never a silent bulk update**; failures reported, never presented as done
- All report examples are invented and say so; pagination ≤ 50 everywhere
- Empty account, non-FR country, registry down → graceful degradation, never invented data or deadlines

---

*Submission docs: `SKILL.md` (the skill itself) · step-by-step guide: `docs/PROCEDURE.en.md` · rich docs in `docs/` (HTML & DOCX, FR/EN).*
