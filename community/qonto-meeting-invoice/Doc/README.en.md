# 📞 qonto-meeting-invoice — From call to quote, before the meeting ends

> **Qonto × Anthropic MCP Hackathon submission** · Agent Skill for the Qonto MCP
> Call-to-invoice is a known dream — this skill's bet is making it **trustworthy**: extract-don't-invent, draft-first, send only after explicit confirmation.

---

## 🎯 Why this matters (usefulness)

A great sales call, everyone's excited… and the quote goes out three days later. By then the momentum is gone and the prospect has seen two competitors. `qonto-meeting-invoice` cuts that delay to minutes:

1. **Transcript in** — a file, a Notion/Drive note (when that MCP is connected), or text pasted straight into the chat: the skill depends on **no** third-party MCP
2. **Careful extraction** — deliverables, quantities, prices, discounts, payment terms, deadlines: **only what was actually said**. Missing price, VAT or due date → a question to the user, never a guess. Every extracted term quotes its transcript line
3. **Matched against real Qonto data** — product catalog (`list_products`: prices, VAT rates), client records (`list_clients` — creation proposed for new prospects, with confirmation), existing quotes (`list_quotes`, duplicate check)
4. **Draft, then send** — `create_quote` (or `create_client_invoice` on request) as a **draft**, line-by-line recap, and sending **only** after an explicit "yes, send it". The prospect gets the quote while the coffee is still warm

Would someone use this on a Monday morning? Every sales call that ends with "I'll send you a quote" is this skill's Monday morning.

## 📋 Prerequisites

| Prerequisite | Detail | Required |
|---|---|---|
| Qonto **production** account | The skill adapts to any organization — `get_organization` first, nothing hardcoded | ✅ |
| Country | Quote/invoice creation: **all Qonto countries**. Legal mentions come from the country's Qonto invoicing settings; VAT rates are never assumed (catalog or confirmation) — no "default 20 %" | ℹ️ detected |
| Qonto MCP connected | Official connector (claude.ai / Claude Desktop), OAuth login | ✅ |
| Qonto invoicing configured | Numbering, legal mentions, payment details — set once in the Qonto app; the skill builds on them, it never reinvents them | ✅ |
| A call transcript | File, Notion/Google Drive note, or text pasted into the conversation | ✅ |
| Qonto product catalog | Services with prices and VAT rates (`list_products`) — without it, the skill builds lines from the call and asks for what's missing | ⭕ recommended |
| Notion / Google Drive MCP | Transcript source, detected dynamically — when absent, the skill says so and asks for a paste | ⭕ optional |

## ⚙️ How it works

![How it works](assets/flow.en.png)

1. **Ingest the transcript**: file, Notion/Drive note (optional MCP, detected dynamically) or pasted text — messy transcripts (filler words, several speakers, mixed languages) are the normal case
2. **Extract the negotiated terms**: deliverables, quantities, unit prices, discounts, payment terms, deadline/validity — every term backed by its transcript quote; what wasn't said does **not** enter the document
3. **Match against Qonto**: product catalog (canonical title, price, VAT — divergences flagged: "the call says €850/day, your catalog says €900"), existing client found or creation proposed with details read back, duplicate check on recent quotes
4. **Surface ambiguities**: one single list, BEFORE any write — "the usual rate", an unstated payment term, an uncertain VAT treatment. The user settles each point
5. **Draft**: `create_quote` (default) or `create_client_invoice` (on request) — never sent at this stage. Line-by-line recap: client, items (title · qty · unit price · VAT · total), totals, dates, terms
6. **Send after confirmation**: `send_quote` / `send_client_invoice` on an explicit "yes", email address confirmed. Otherwise the document stays a draft in Qonto

## 🏗 Functional diagram

![Functional diagram](assets/functional.en.png)

**The key safety point**: documents created via MCP are **real**. Solid arrows (reads: catalog, clients, quotes) are risk-free; the dashed arrow (write) only produces a **draft** — and sending to the prospect requires explicit confirmation in the conversation, after the line-by-line recap. Nothing leaves without the user's go.

## 🧪 Holds up on messy data

- Rambling transcript, several speakers, mixed languages? → extraction quotes its evidence line by line, so the user can verify every term
- A price mentioned as "the usual"? → matched against the catalog and confirmed, never guessed
- No product catalog? → lines built from the call, missing prices asked one by one
- New prospect with half an address? → `create_client` proposed with known fields read back, missing ones asked
- No payment term stated on the call? → asked, or the organization's Qonto default offered — explicitly, never silently
- Non-French organization? → same workflow; VAT and legal mentions follow that country's Qonto settings, nothing French is assumed

## 📤 Output formats

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables: quoted extraction, ambiguity list, line-by-line recap | **Always** — the baseline |
| **Draft in Qonto** | Quote or invoice on the organization's own invoicing template (native numbering & legal mentions) | After ambiguities are settled |
| **Email to the prospect** | Native Qonto sending (`send_quote` / `send_client_invoice`) | **Only** after explicit confirmation |

## 🎬 Demo video

The ≤ 3-minute demo attached to the PR walks through: the problem (the quote that ships three days late) → pasted transcript & quoted extraction → catalog/client matching & the ambiguity list → **the complete quote appearing in Qonto ~90 seconds after the meeting ends, then the send** → the guardrails. It runs live on a real production account.

## 💡 Roadmap ideas

- Automatic deposit ("30 % upfront") via `create_payment_link` attached to the send — official MCP tool, same confirmation logic
- Follow-up on unsigned quotes after N days (status via `list_quotes`)
- Direct audio transcription (audio file → text) when the host supports it
- A/B quotes: two variants (with/without an option) from the same call, compared side by side
- Prospect-language detection → quote wording in their language (Qonto handles the templates)

## 🛡 Guardrails

- Documents created via MCP are **real**: draft first, always; NEVER sent without explicit confirmation in the current conversation; never presented as sent while it is a draft
- Nothing invented: a price, VAT rate, quantity or due date missing from the call → a question. No default VAT
- `create_client` only after details are read back; `list_clients` first (duplicate check)
- Rehearsals: fictitious client + `delete_quote` / `delete_client_invoice` (drafts only — a finalized invoice cannot be deleted, which is exactly why draft-first)
- Pagination ≤ 50 everywhere · personal data masked when echoing client records
- The skill drafts business documents, not legal or tax advice — Qonto settings and the accountant remain the reference

---

*Submission docs: `SKILL.md` (the skill itself) · step-by-step guide: `docs/PROCEDURE.en.md` · rich docs in `docs/` (HTML & DOCX, FR/EN).*
