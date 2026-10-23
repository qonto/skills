# 📖 Setup & usage guide — qonto-chargeback-defender

> Step-by-step user guide. French version: `PROCEDURE.fr.md`.

---

## 1️⃣ Setup (once, ~5 min)

### Step 1 — Connect the Qonto MCP to Claude
1. In **claude.ai** (or Claude Desktop): Settings → **Connectors** → *Browse connectors*
2. Search **Qonto** → *Add* → the Qonto sign-in flow opens
3. Log in with your Qonto account (OAuth — your password is **never** shared with Claude)
4. Check: ask Claude "*List my Qonto accounts*" → your accounts show up

### Step 2 — Install the skill
- **Claude Code / Claude Desktop**: copy the skill folder to `~/.claude/skills/qonto-chargeback-defender/` (the `SKILL.md` file is enough)
- **claude.ai**: attach `SKILL.md` to your project, or paste its content into the project instructions

### Step 3 — Connect the optional MCPs (recommended)
1. **Stripe or PayPal**: the authoritative source for disputes — reasons, amounts and **real deadlines**
2. **Shopify**: orders, fulfillment, tracking numbers (the proof of delivery)
3. **Gmail**: customer threads (confirmations, complaints, "got it, thanks")

> ⚠️ None of them is blocking: without them the skill runs in **Qonto-only mode** — clawback
> detection + money trail + response checklist. It announces by itself what it has and what it lacks.

## 2️⃣ Typical usage (when a dispute lands, ~10 min)

| # | Action | Result |
|---|---|---|
| 1 | Tell Claude: "**Any open payment disputes?**" | Urgency-sorted dispute table: amount, reason, deadline |
| 2 | "**Find the matching debit**" | Money trail: original payment → payout → clawback → fee |
| 3 | "**Build the defense file**" | Evidence checklist ✅/⚠️, every piece with its source, missing ones with where to find them |
| 4 | Confirm explicitly ("yes, attach the memo") | Dated synthesis memo attached to the clawback transaction in Qonto, upload **confirmed** |
| 5 | Copy the response draft → **Stripe/PayPal portal** → submit **before the deadline** | The defense is filed — by you, and only you ✅ |

## 3️⃣ Copy-paste prompts

- "**Any open payment disputes on my account?**" → detection + urgency table
- "**Why did Stripe take back €189 last month?**" → clawback identified + money trail *(example amount, invented)*
- "**Build the defense file for this dispute**" → sourced evidence + response draft
- "**Attach the file to the transaction**" → dated memo attached to the debit, confirmed
- "**Which pieces am I missing and where do I find them?**" → missing-evidence checklist

## 4️⃣ Output formats

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables: disputes (urgency), money trail, checklist ✅/⚠️ | **Always** — the baseline |
| **Defense memo** | Dated, sourced synthesis attached to the clawback transaction in Qonto | Per dispute, explicit consent only |
| **Response draft** | The argument structured like the PSP's response form, ready to paste | As soon as the reason is known |

## 5️⃣ Troubleshooting (known, verified quirks)

| Symptom | Cause | Fix |
|---|---|---|
| `list_transactions` fails or comes back empty | Missing `bank_account_id`/`iban` | The skill always calls `get_organization` first |
| Huge / truncated responses | Pagination too wide | `per_page` ≤ 50 everywhere, 3-month windows |
| No clawback debit found although a dispute exists | **Stripe nets the dispute inside the next payout** (no separate line) | The skill flags unusually low payouts and recommends the Stripe MCP |
| Dispute matched to the wrong payment | Card settlement drift (1–2 days) | Matching on `emitted_at`, not `settled_at` |
| Attachment doesn't show up | Upload not finalized | The skill confirms via `list_transaction_attachments` before reporting success; otherwise it retries |
| No deadline shown | Qonto-only mode (no dispute MCP) | Typical windows given as **indicative** + check on the Stripe/PayPal portal |

## 🔒 Security reminder

The skill **never submits** the defense: it prepares it, and **you** file it on the Stripe/PayPal
portal. It **never fabricates** evidence: the attached memo is a dated synthesis that **cites** the
source documents — not an invented receipt. And it only reports an upload as done after
**verifying** it on the transaction.
