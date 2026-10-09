# ⚖️ qonto-injonction — When reminders stop working, a court file ready to sign

> **Qonto × Anthropic MCP Hackathon submission** · Agent Skill for the Qonto MCP
> **Zero writes, by design**: the skill stops at a ready-to-sign dossier — no legal act is ever executed by the skill. That's a feature.

---

## 🎯 Why this matters (usefulness)

Reminders failed (see `qonto-invoice-chaser`), the formal notice went unanswered. The next step — the French **payment-order procedure** (*injonction de payer*) — is cheap (~€35 court fee) and lawyer-free on paper, yet almost nobody dares: an intimidating CERFA form, interest to compute, the right court to find, exhibits to number. Most founders just write the invoice off. `qonto-injonction` builds the whole file from the Qonto account:

1. **BODACC check first** (public API, no key) — if the debtor is in collective proceedings, an injunction is the wrong move: the skill reorients to a **proof of claim** (2-month deadline) and drafts it
2. **The claim, computed to the day** — principal (payments on account deducted), **late-payment interest** (ECB refi + 10 points, floor 3× the French legal rate — art. L441-10), the **€40 recovery indemnity**, formula shown
3. **CERFA 12946 pre-filled field by field** + a **numbered exhibit list** (invoice, reminders, formal notice — pulled from Qonto receipts) + the **competent commercial court** identified from the debtor's registered office
4. **Infogreffe filing guide** — online filing, ~€35, exhibits as PDF < 2 MB, and what happens next (order → service → 1-month opposition window)

Would someone use this on a Monday morning? It's the Monday you finally stop waiting for that invoice — the dossier is done before your coffee is.

## 📋 Prerequisites

| Prerequisite | Detail | Required |
|---|---|---|
| Qonto **production** account | Adapts to any organization — `get_organization` first, nothing hardcoded | ✅ |
| Country | **CERFA procedure: France.** Other Qonto countries (DE, ES, IT…): full factual dossier (proven non-payment, generic EU Late Payment Directive interest, exhibits) but **no form** — foreign forms or rates are never invented | ℹ️ detected |
| Qonto MCP connected | Official connector (claude.ai / Claude Desktop), OAuth login | ✅ |
| Web access (public APIs, no key) | BODACC + the French company registry (`recherche-entreprises.api.gouv.fr`). Without web access the skill asks for the two missing facts instead of guessing | ⭕ recommended |
| Amicable stage done | Formal notice already sent (registered mail) — otherwise the skill points to `qonto-invoice-chaser` first | ⭕ advised |
| Debtor's SIREN | From the Qonto client record; otherwise looked up by name + city and **confirmed by the user** (homonyms) | ⭕ |

## ⚙️ How it works

![How it works](assets/flow.en.png)

1. **Target the invoice**: unpaid invoice picked with the user (`list_client_invoices`, `get_client_invoice`), debtor identity (`get_client`) — SIREN confirmed, never assumed
2. **Prove non-payment**: credit-side transaction scan since the issue date — no incoming payment matches; partial payments are detected and **deducted from the principal**; disputed invoice → warning (an injunction would just meet opposition)
3. **BODACC check**: the debtor's SIREN searched in collective-proceedings announcements. Open proceeding → **injunction stops here**, the skill switches to the proof of claim (2 months from the BODACC publication)
4. **Competent court**: debtor's registered office via the public registry API → the commercial court with jurisdiction; the company's administrative status is verified on the way
5. **Compute the claim**: principal − payments on account + interest (contract rate, else ECB + 10 pts, floor 3× the legal rate, semester rate stated) + €40 per invoice — every euro justified
6. **Ready-to-sign dossier**: CERFA 12946 pre-filled field by field, exhibits P1–P6 (receipts retrieved via `get_attachment`, missing pieces listed as "to provide"), Infogreffe filing guide

## 🏗 Functional diagram

![Functional diagram](assets/functional.en.png)

**The key point**: this skill is **100% read-only**. It reads Qonto and two keyless public APIs, computes, assembles — and stops. No write tool is used: nothing is filed, nothing is served, nothing is signed. Filing on Infogreffe is the user, with their own signature. **No legal act is ever executed by an AI — by design.**

## 🧪 Holds up on messy data

- Invoice actually paid (transfer never reconciled)? → the transaction scan catches it, the skill stops and proposes reconciliation instead of a lawsuit
- Partial payments, several invoices for one debtor? → deducted, itemized, stackable in one claim
- No SIREN on the client record? → registry lookup by name + city, user confirms the match — homonyms never guessed
- Debtor in liquidation? → no injunction, a proof of claim instead, with its 2-month clock stated
- Receipts missing from Qonto? → listed as "to provide", never invented
- No web access, non-French debtor, empty account → the skill says exactly what it can and can't build

## ⚖️ Two routes, picked automatically

| Debtor's situation | Route | What the skill produces | Key deadline |
|---|---|---|---|
| **Solvent** (nothing in BODACC) | Payment order (injonction de payer) | Pre-filled CERFA 12946 + exhibit list + claim computation + Infogreffe guide (~€35) | 5-year limitation (art. L110-4) — see `qonto-prescription-guard` |
| **Collective proceedings** | Proof of claim (art. L622-24) | Drafted claim statement: principal, interest stopped at the judgment, exhibits, receiver's address when published | **2 months** after BODACC publication |
| Company struck off / unreachable | Neither | Factual finding + advice to consult a professional | — |

## 📤 Output formats

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables: claim computation, CERFA field→value pre-fill, exhibit list ✅/📋, route banner (injunction / proof of claim) | **Always** — the baseline |
| **Printable dossier** | **HTML** file/artifact: cover sheet, computation, pre-filled form, exhibit list — save as PDF | When the host renders files (claude.ai artifacts, Claude Desktop, Claude Code); automatic fallback to tables otherwise |
| **Exhibits** | Qonto receipts retrieved (`get_attachment`) + a "to provide" list for the rest | Every dossier |

## 🎬 Demo video

The ≤ 3-minute demo attached to the PR walks through: the problem → proven non-payment + the BODACC check → interest computation + the right court → **the complete dossier, ready to sign** → filing on Infogreffe. All figures shown are invented examples.

## 💡 Roadmap ideas

- **European order for payment** (form A, Regulation 1896/2006) — for debtors in another member state, same computation engine
- Post-filing follow-up: service deadline (6 months) and opposition window (1 month) reminders — reuses the `qonto-prescription-guard` clock
- Multi-invoice claims: one request per debtor stacking N invoices
- Optional email MCP enrichment: draft to the court clerk or the bailiff when an email MCP is detected

## 🛡 Guardrails

- **Not legal advice** — stated on every dossier; interest amounts are indicative computations to be validated (lawyer, bailiff, or the court clerk)
- **Zero writes**: never presented as filed, served, or granted — the skill stops at the ready-to-sign dossier
- Debtor in collective proceedings → the injunction is never suggested; systematic reorientation to the proof of claim
- Disputed claims and limitation risks are flagged, never silenced
- France-only procedure; elsewhere, a factual dossier without a form
- IBANs masked (last 4 digits) · pagination ≤ 50 · examples invented (INV-YYYY-NNN)

---

*Submission docs: `SKILL.md` (the skill itself) · step-by-step guide: `docs/PROCEDURE.en.md` · rich docs in `docs/` (HTML & DOCX, FR/EN).*
