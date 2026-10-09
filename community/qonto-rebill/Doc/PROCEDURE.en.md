# 📖 Setup & usage guide — qonto-rebill

> Step-by-step user guide. French version: `PROCEDURE.fr.md`.

---

## 1️⃣ Setup (once, ~5 min)

### Step 1 — Connect the Qonto MCP to Claude
1. In **claude.ai** (or Claude Desktop): Settings → **Connectors** → *Browse connectors*
2. Search **Qonto** → *Add* → the Qonto sign-in flow opens
3. Log in with your Qonto account (OAuth — your password is **never** shared with Claude)
4. Check: ask Claude "*List my Qonto accounts*" → your accounts show up

### Step 2 — Install the skill
- **Claude Code / Claude Desktop**: copy the skill folder to `~/.claude/skills/qonto-rebill/` (the `SKILL.md` file is enough)
- **claude.ai**: attach `SKILL.md` to your project, or paste its content into the project instructions

### Step 3 — Prepare the attribution (recommended)
1. In the **Qonto app**: Settings → **Labels** → create one label per client (same name as in Invoicing, e.g. "ACME Studio")
2. As you go: label every expense paid for a client (two seconds at payment time)
3. Make sure your clients exist in **Invoicing → Clients** (the invoice needs an existing client)

> ⚠️ No labels? The skill still works: it switches to **interactive attribution**,
> one transaction at a time — slower, nothing lost. And it offers to label accepted
> expenses on the way, so next quarter runs itself.

## 2️⃣ Quarterly usage (the end-of-quarter ritual, ~5 min)

| # | Action | Result |
|---|---|---|
| 1 | Tell Claude: "**Which expenses did I advance for my clients this quarter?**" | Per-client table: date · counterparty · amount · receipt ✅/⚠️ |
| 2 | Fill the receipt gaps (skill `qonto-receipt-hunter`) | Every line ships with its document |
| 3 | Answer the VAT question (disbursement or rebill? handling fee?) | The skill shows the comparison table and waits for your choice |
| 4 | Say: "**Prepare the invoice for [client]**" | Line-by-line `create_client_invoice` draft, reviewable in Qonto |
| 5 | Review, then confirm explicitly ("yes, send it") | Invoice sent ✅ — never before your confirmation |

## 3️⃣ On-demand usage

- "**What did I advance for [client] since January?**" → attributed expenses + total, any period
- "**Did I forget to rebill anything?**" → scan of past periods, attributed expenses never invoiced
- "**Explain disbursement vs rebilled expense**" → the comparison table, nothing created
- "**Prepare the rebill with a 10% handling fee**" → markup is your choice (never on a disbursement)

## 4️⃣ Output formats

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables: expenses per client (receipt ✅/⚠️), invoice line by line, recovered total | **Always** — the baseline |
| **Draft invoice in Qonto** | `create_client_invoice` as a draft, visible in the Invoicing section | After the regime is agreed |
| **Receipt pack** | Download links (time-limited) to forward with the invoice | Every prepared invoice |
| **HTML recap** | Per-client cards, receipts gauge, recovered amounts | When the host renders files; fallback to tables otherwise |

## 5️⃣ Troubleshooting (known, verified quirks)

| Symptom | Cause | Fix |
|---|---|---|
| `list_transactions` fails immediately | Missing `bank_account_id`/`iban` | Expected — the skill always calls `get_organization` first |
| Huge / truncated responses | Page size too large | The skill paginates `per_page` ≤ 50 everywhere |
| An end-of-quarter expense is missing | Card expense settled 1-2 days later | The skill groups by `emitted_at`, not `settled_at` |
| `403 missing oauth scope` on `list_cash_flow_categories` | Outside the claude.ai connector scope | Expected — the skill works with labels |
| Client not found for the invoice | Missing from Invoicing → Clients | Create it in the app (Invoicing → Clients), then re-run the skill |
| Receipt missing on a line | Document never attached to the transaction | Run `qonto-receipt-hunter` before rebilling |
| A test invoice lingers | MCP-created invoices are **real** | Rehearsals: fictitious client + draft + `delete_client_invoice` |

## 🔒 Security reminder

The skill only creates a **draft** invoice — nothing reaches your client without your
explicit confirmation in the conversation. The VAT choice (disbursement vs rebill) is
yours, with your accountant: the skill explains, compares, asks — it never decides on
its own. And it never attributes an expense to a client without your agreement.
