# 📖 Setup & usage guide — qonto-support-cashdesk

> Step-by-step user guide. French version: `PROCEDURE.fr.md`.

---

## 1️⃣ Setup (once, ~5 min)

### Step 1 — Connect the Qonto MCP to Claude
1. In **claude.ai** (or Claude Desktop): Settings → **Connectors** → *Browse connectors*
2. Search **Qonto** → *Add* → the Qonto sign-in flow opens
3. Log in with your Qonto account (OAuth — your password is **never** shared with Claude)
4. Check: ask Claude "*List my Qonto clients*" → your clients show up

### Step 2 — Install the skill
- **Claude Code / Claude Desktop**: copy the skill folder to `~/.claude/skills/qonto-support-cashdesk/` (the `SKILL.md` file is enough)
- **claude.ai**: attach `SKILL.md` to your project, or paste its content into the project instructions

### Step 3 — Optional connectors (detected automatically)
- **Intercom**: to pull support conversations directly — otherwise paste the conversation into the chat, same verifications
- **Gmail**: to create the customer reply as a **draft** (the skill never sends) — otherwise the reply comes as copy-paste text

> ℹ️ The core works in pure Qonto: no optional connector is required.

## 2️⃣ Typical usage (one billing complaint, ~2 min)

| # | Action | Result |
|---|---|---|
| 1 | Paste the customer conversation (or: "handle the Intercom ticket from [client]") | Claim, identity and amounts extracted |
| 2 | Confirm the proposed client ("yes, that's them") | Match locked — nothing happens before |
| 3 | Read the diagnosis: cited evidence (statuses, dates, credits) | You know exactly what happened |
| 4 | Confirm the proposed fix ("yes, resend" / "yes, create the credit note") | Invoice resent, fresh link, or credit note created in Qonto |
| 5 | Review the reply draft, adjust, send it yourself | The customer gets a factual answer with the fix attached |

## 3️⃣ Prompts to copy-paste

- "**A customer says they never received invoice INV-2026-042. Here's their message: […]**" → verification + resend proposed
- "**This client says their payment link expired: […]**" → the link's real status + a fresh link if needed
- "**A customer claims they were charged twice. Here's the conversation: […]**" → hunt for the two credits, proof or disproof
- "**Handle this support conversation: […]**" → the skill picks the right counter by itself

*(Invented examples — INV-2026-042 is a fictional number.)*

## 4️⃣ Output formats

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Diagnosis + cited evidence + recap table (claim → evidence → action → status) | **Always** — the baseline |
| **Customer reply draft** | Ready-to-review text; **Gmail** draft when that MCP is present (never sent by the skill) | Every conversation handled |
| **Qonto documents** | Invoice resent · payment link · credit note (numbered accounting document) | Case by case, after confirmation |

## 5️⃣ Troubleshooting (known, verified quirks)

| Symptom | Cause | Fix |
|---|---|---|
| `list_transactions` fails | Missing `bank_account_id`/`iban` | The skill calls `get_organization` first — always |
| Client not found by email | Email missing or different on the client record | The skill falls back to normalized name/company and shows you the candidates |
| The customer's payment doesn't show on the date they claim | Card settlement lag (1–2 days) | The skill matches on `emitted_at`, not `settled_at` |
| Doubts about payment links via MCP | The MCP doc says they're unsupported | Verified: `list_payment_links` / `get_payment_link` / `create_payment_link` do work |
| Very large / truncated responses | Missing pagination | `per_page` ≤ 50 everywhere, date windows around the invoice |
| A test invoice lingers in the account | Invoices created via MCP are **real** | Rehearse on a fictional client, draft status, then `delete_client_invoice` / `delete_client` |

## 🔒 Security reminder

The skill **never moves money** and **never sends** anything to the customer. Every write
(invoice resend, link, credit note) requires your explicit confirmation. A credit note is a
**real accounting document**: it is only proposed when the double collection is proven by two
dated credits, cited in front of you. Any refund remains a transfer that **only you** make in
the Qonto app (SCA).
