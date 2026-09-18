# 📖 Setup & usage guide — qonto-approval-brief

> Step-by-step user guide. French version: `PROCEDURE.fr.md`.

---

## 1️⃣ Setup (once, ~5 min)

### Step 1 — Connect the Qonto MCP to Claude
1. In **claude.ai** (or Claude Desktop): Settings → **Connectors** → *Browse connectors*
2. Search **Qonto** → *Add* → the Qonto sign-in flow opens
3. Log in with your Qonto account (OAuth — your password is **never** shared with Claude)
4. Check: ask Claude "*List my pending requests*" → your requests show up (or "none", which is good news)

### Step 2 — Install the skill
- **Claude Code / Claude Desktop**: copy the skill folder to `~/.claude/skills/qonto-approval-brief/` (the `SKILL.md` file is enough)
- **claude.ai**: attach `SKILL.md` to your project, or paste its content into the project instructions

### Step 3 — Check your role (important)
The connected account must be able to **see team requests** (Owner, Admin, or Manager with request review).
Otherwise `list_requests` comes back empty — and the skill will tell you it's a visibility issue, not an absence of requests.

> ℹ️ Optional: connect the **Gmail** MCP (context: quotes, threads) and **Slack** MCP (digest).
> The skill detects them on its own — without them, the core runs on Qonto data alone.

## 2️⃣ Typical usage (the request ritual, ~2 min)

| # | Action | Result |
|---|---|---|
| 1 | Tell Claude: "**Brief me on my pending requests**" | One brief per request: ✅ recommended / 🔶 verify, evidence cited |
| 2 | Read the 🔶 briefs (never-seen IBAN, unusual amount, possible duplicate…) | You know exactly what to check, and with whom |
| 3 | To decline: "**Decline request X: [reason]**" then confirm | Motivated decline sent — the requester sees the reason in Qonto |
| 4 | To approve: open the **Qonto app** → Requests → approve with your **2FA** | Money only moves there — the skill cannot approve ✅ |

## 3️⃣ On-demand usage

- "**Can I approve [name]'s request?**" → an instant brief for that request, evidence cited
- "**Have we paid this beneficiary before?**" → counterparty history: N payments, amounts, cadence
- "**Do we know this IBAN?**" → seen before (dated) or never seen (a signal, not an accusation)
- "**Post the request digest to Slack**" → brief summary on the channel of your choice (when the Slack MCP is connected)

## 4️⃣ Output formats (where do the briefs land?)

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Brief table + one expanded brief per 🔶 request + the explicit next step | **Always** — the baseline |
| **Brief board** | **HTML** file/artifact: one card per request, verdict and evidence | When the host renders files; automatic fallback to tables otherwise |
| **Decline reason** | Text attached to the decline, visible to the requester in Qonto | Every decline (confirmed) |
| **Slack digest** | Summary posted to the channel of your choice | When a Slack MCP is connected (optional) |

## 5️⃣ Troubleshooting (known, verified quirks)

| Symptom | Cause | Fix |
|---|---|---|
| Claude "refuses" to approve a request | **By design**: this skill never uses `approve_request` | Approve in the Qonto app with your 2FA — that's the security model |
| Declining a multi-transfer request fails | `decline_request` requires `request_type: "multi_transfers"` (**plural**) | Handled by the skill |
| Error on `list_transactions` | `bank_account_id`/`iban` is required | The skill always calls `get_organization` first |
| `list_requests` comes back empty | No pending requests **or** a role without request review | The skill says which of the two; check your role in Qonto if needed |
| Huge / truncated responses | Missing pagination | The skill paginates everywhere with `per_page` ≤ 50 |
| No email context in the briefs | Gmail MCP not connected | Optional — the skill says so once and continues on Qonto data alone |
| "Never-seen IBAN" on a legitimate supplier | A new supplier is normal, exactly once | It's a **signal, not an accusation**: check with the requester; next time it's "known" |

## 🔒 Security reminder

The skill **cannot** approve or move money: `approve_request` is never called.
Its only write is the **motivated decline** (`decline_request`), always confirmed by you in the conversation.
Approvals happen in the Qonto app, with **your** 2FA — every brief cites its evidence, so you decide with complete information.
