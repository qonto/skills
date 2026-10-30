# 📖 Setup & usage guide — qonto-pay-me-now

> Step-by-step user guide. French version: `PROCEDURE.fr.md`.

---

## 1️⃣ Setup (once, ~5 min)

### Step 1 — Connect the Qonto MCP to Claude
1. In **claude.ai** (or Claude Desktop): Settings → **Connectors** → *Browse connectors*
2. Search **Qonto** → *Add* → the Qonto sign-in flow opens
3. Log in with your Qonto account (OAuth — your password is **never** shared with Claude)
4. Check: ask Claude "*List my Qonto quotes*" → your quotes show up

### Step 2 — Install the skill
- **Claude Code / Claude Desktop**: copy the skill folder to `~/.claude/skills/qonto-pay-me-now/` (the `SKILL.md` file is enough)
- **claude.ai**: attach `SKILL.md` to your project, or paste its content into the project instructions

### Step 3 — Activate payment links (recommended)
1. In the **Qonto app**: activate the **Payment links** feature (one-time)
2. Done — if the API refuses `create_payment_link`, the skill says so and continues invoice-only

> 💡 **Optional**: connect the **Short.io** MCP (trackable short link + click stats) and **Gmail** (sending).
> Default: raw Qonto URL and QR encoding that URL, no Short.io calls. Before shortening or reading click stats, explain that Short.io receives and stores the payment URL and tracks payer clicks, then ask for explicit approval in the current conversation. Connection or invoice-send approval is not consent. Approved links use random slugs, no invoice/client identifiers or other Qonto metadata. Keep the raw URL visible; the QR always encodes it. Without approval, clicks are unknown, not "not clicked".

## 2️⃣ Typical usage (the "quote accepted" reflex, ~2 min)

| # | Action | Result |
|---|---|---|
| 1 | Tell Claude: "**Any accepted quotes I haven't invoiced yet?**" | Quotes cross-checked against invoices — only the never-invoiced ones surface |
| 2 | Review the **invoice draft** (lines, amounts, due date) | REAL document — you check before anything is sent |
| 3 | Confirm explicitly ("yes, send it") | Invoice sent + **payment link** created (invoice number in the description) |
| 4 | Share the **raw Qonto link** or its QR; optionally approve Short.io after disclosure | Short link only after approval; QR still uses raw Qonto URL |
| 5 | At D+2: "**Who clicked but didn't pay?**" | Clicks vs cash matrix + a gentle nudge proposed |

## 3️⃣ Copy-paste prompts

- "**My quote [number] just got accepted — invoice it and get me paid**"
- "**Create a payment link for invoice [number]**"
- "**Make me a payment QR code for this printed invoice**"
- "**Who clicked my payment links but didn't pay?**"
- "**Did the client of invoice [number] pay by transfer? Check and mark it paid if so**"

## 4️⃣ Output formats

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables: quote → invoice → link pipeline, follow-up matrix | **Always** — the baseline |
| **The payment link (+ optional short link)** | Raw Qonto URL; Short.io URL only after explicit approval | Every cycle |
| **QR code** | Image file/artifact encoding the raw Qonto URL | When the host renders files; otherwise the raw link is enough |
| **Follow-up report** | Clicks vs cash + proposed nudges (never sent on their own) | On demand / at D+2 |

## 5️⃣ Troubleshooting (known, verified quirks)

| Symptom | Cause | Fix |
|---|---|---|
| Payment-link tool unavailable | Connector does not expose the tool | Follow current official docs and tool schema; continue invoice-only without a direct API workaround |
| Error when creating the payment link | Feature not activated on the account | Qonto app → activate **Payment links** (one-time); meanwhile the skill continues invoice-only |
| `list_transactions` fails | Missing `bank_account_id`/`iban` | `get_organization` first — the skill always does |
| Huge responses / slowness | Pagination too wide | The skill paginates `per_page` ≤ 50 everywhere |
| Test invoice you don't want to keep | MCP invoices are **REAL** | Rehearse on a fictional client, stay in draft, `delete_client_invoice` afterwards |
| No short link, no click stats | Short.io MCP absent | Expected — the raw Qonto link works fine; the skill says so and continues |
| Client paid but the invoice stays "unpaid" | Paid by plain transfer, outside the link | The skill matches it in `list_transactions` and proposes `mark_client_invoice_as_paid` with the transaction as evidence |

## 🔒 Security reminder

The skill **cannot** move your money. A payment link is a way to **receive** a payment from your
client — it has nothing to do with outbound transfers (impossible through the MCP anyway: any transfer
request requires your own SCA in the Qonto app). The only three writes: an invoice (**draft first**, sent only after your explicit go), a payment link
you can deactivate anytime in the app, and a paid-marking on an invoice — always proposed with the
matching transaction as evidence, never automatic.
