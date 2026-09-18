# 📖 Setup & usage guide — qonto-meeting-invoice

> Step-by-step user guide. French version: `PROCEDURE.fr.md`.

---

## 1️⃣ Setup (once, ~5 min)

### Step 1 — Connect the Qonto MCP to Claude
1. In **claude.ai** (or Claude Desktop): Settings → **Connectors** → *Browse connectors*
2. Search **Qonto** → *Add* → the Qonto sign-in flow opens
3. Log in with your Qonto account (OAuth — your password is **never** shared with Claude)
4. Check: ask Claude "*List my Qonto products*" → your catalog shows up

### Step 2 — Install the skill
- **Claude Code / Claude Desktop**: copy the skill folder to `~/.claude/skills/qonto-meeting-invoice/` (the `SKILL.md` file is enough)
- **claude.ai**: attach `SKILL.md` to your project, or paste its content into the project instructions

### Step 3 — Check your Qonto invoicing setup (recommended)
1. In the **Qonto app**: Invoicing → Settings → numbering, legal mentions, payment details, logo
2. Fill in the **product catalog** (services, unit prices, VAT rates) — that's what makes the matching reliable
3. Done — the skill builds on these settings, it never reinvents them

> ⚠️ Without a product catalog: the skill still works, but it will ask you for every price
> not stated on the call instead of finding it on its own.

## 2️⃣ Typical usage (after each sales call, ~3 min)

| # | Action | Result |
|---|---|---|
| 1 | Paste the transcript: "**Here's the call transcript, draft the quote**" | Negotiated terms extracted, every line quoted |
| 2 | Read the extraction and the ambiguity list ("the usual rate", unstated terms…) | You know what came from the call and what's missing |
| 3 | Answer the listed points | The skill creates the quote **as a draft** in Qonto |
| 4 | Check the line-by-line recap (client, items, VAT, totals, dates) | The document is exactly what was negotiated |
| 5 | Confirm explicitly ("**yes, send it**") | Qonto emails the quote to the prospect ✅ |

## 3️⃣ On-demand usage

- "**Draft the quote from this morning's call** (Notion note 'Acme call')" → fetched via the Notion MCP when connected
- "**The client said yes — invoice them directly**" → `create_client_invoice` as a draft, same recap, same confirmation
- "**It's a new prospect**" → client record created after the details are read back
- "**Show me open quotes for this client**" → `list_quotes`, duplicate check before creating another

## 4️⃣ Output formats

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables: quoted extraction, ambiguities, line-by-line recap | **Always** — the baseline |
| **Draft in Qonto** | Quote or invoice on the organization's own invoicing template | After ambiguities are settled |
| **Email to the prospect** | Native Qonto sending (`send_quote` / `send_client_invoice`) | **Only** after explicit confirmation |

## 5️⃣ Troubleshooting (known, verified quirks)

| Symptom | Cause | Fix |
|---|---|---|
| The quote doesn't show in Qonto | It's a **draft** — look in Invoicing → Quotes, drafts tab | Expected: nothing is sent without your go |
| `422` when creating the quote/invoice | A required field is missing (client, date, per-line VAT rate) | The skill collects everything **before** creating — answer the ambiguity list |
| Duplicate client | Record created without checking existing ones | The skill runs `list_clients` first and shows the match — flag the duplicate otherwise |
| Catalog price contradicts the call | Real divergence (negotiated discount?) | The skill flags it and asks you to settle it — never a silent choice |
| Can't delete a test invoice | A **finalized** invoice cannot be deleted | Never finalize a test: fictitious client + draft + `delete_client_invoice` / `delete_quote` |
| "I can't read your Notion/Drive note" | Source MCP not connected | Expected — paste the transcript directly, the skill continues |
| Huge response / truncated list | Pagination skipped | The skill paginates `per_page` ≤ 50 everywhere |

## 🔒 Security reminder

Quotes and invoices created through the MCP are **real**. The skill always creates a **draft**,
shows you the line-by-line recap, and sends **only** on your explicit "yes" — the recipient's
email address is confirmed first. What wasn't said on the call never enters the document: the
skill asks, it doesn't invent. For rehearsals: fictitious client, then
`delete_quote` / `delete_client_invoice`.
