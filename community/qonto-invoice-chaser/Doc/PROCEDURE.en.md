# 📖 Setup & usage guide — qonto-invoice-chaser

> Step-by-step user guide. French version: `PROCEDURE.fr.md`.

---

## 1️⃣ Setup (once, ~5 min)

### Step 1 — Connect the Qonto MCP to Claude
1. In **claude.ai** (or Claude Desktop): Settings → **Connectors** → *Browse connectors*
2. Search **Qonto** → *Add* → the Qonto sign-in flow opens
3. Log in with your Qonto account (OAuth — your password is **never** shared with Claude)
4. Check: ask Claude "*List my client invoices*" → your invoices show up

### Step 2 — Install the skill
- **Claude Code / Claude Desktop**: copy the skill folder to `~/.claude/skills/qonto-invoice-chaser/` (the `SKILL.md` file is enough)
- **claude.ai**: attach `SKILL.md` to your project, or paste its content into the project instructions

### Step 3 — Connect the Gmail MCP (recommended)
1. Settings → **Connectors** → search **Gmail** → *Add* → Google OAuth
2. Done — the skill **detects it automatically** and drops its reminders as drafts

> ⚠️ This step is optional: without Gmail, the skill delivers each reminder as ready-to-copy
> text for any email client. The core (detection, cross-check, drafting) runs on Qonto alone.

## 2️⃣ Weekly usage (the Monday-morning ritual, ~3 min)

| # | Action | Result |
|---|---|---|
| 1 | Tell Claude: "**Chase my late invoices**" | Overdue scan + cross-check against real incoming transactions |
| 2 | Review the proposed matches (invoice ↔ transaction) | Already-paid invoices get marked (after your confirmation), not chased |
| 3 | Read the drafted reminders (payer profile + exact numbers shown) | You know who gets chased, in which tone, and why |
| 4 | Open **Gmail → Drafts**: review → tweak if needed → **send** | The reminder goes out, signed by you ✅ |

## 3️⃣ On-demand usage

- "**Who owes me money right now?**" → outstanding, aging, per-invoice action table
- "**Has invoice INV-2026-042 been paid?**" → cross-checked against transactions, sourced answer
- "**Prepare the formal notice for [client]**" → computed interest + €40 indemnity (art. L441-10), as a draft
- "**What's my DSO this quarter?**" → estimate + top late clients

## 4️⃣ Output formats (where does the reminder land?)

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables (outstanding, aging, per-invoice actions) | **Always** — the baseline |
| **Gmail draft** | Complete email (recipient, subject with invoice number, personalized body) | When the Gmail MCP is connected |
| **Copy-ready text** | Subject + body, paste into any email client | Without the Gmail MCP |
| **Interactive dashboard** | **HTML** file/artifact: aging bars, top late clients, pipeline | When the host renders files; fallback to tables otherwise |

## 5️⃣ Troubleshooting (known, verified quirks)

| Symptom | Cause | Fix |
|---|---|---|
| `list_transactions` fails | Missing `bank_account_id` / `iban` (required parameter) | The skill calls `get_organization` first — always |
| Huge responses / slowness | Pagination too wide | `per_page` ≤ 50 + date windows — handled by the skill |
| Invoice paid but still "unpaid" in Qonto | Transfer received outside a payment link, never reconciled | That's the skill's core: cross-check → `mark_client_invoice_as_paid` **proposed**, never silent |
| Partial payment or grouped transfer | One payment ≠ one invoice | Candidates presented with amounts; never auto-marked |
| No draft created | Gmail MCP not connected | Copy-ready text provided; connect Gmail in Connectors (step 3) |
| Reminder without a recipient | Email missing from the client record | Flagged by the skill (`get_client`) → complete the record in Qonto, never a guessed address |
| No legal figures in the notice | Organization outside France | Expected — same graduated reminders, but no invented rates (generic reference to EU Directive 2011/7/EU) |

## 🔒 Security reminder

The skill **sends nothing and marks nothing on its own**. Marking an invoice paid is a *proposal*
backed by the matching transaction — you confirm, or not. Reminders only ever exist as **drafts**
that you alone review and send. A formal notice is a serious document: professional review
(accountant or lawyer) recommended before it goes out, registered mail advised for delivery.
