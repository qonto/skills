# 📖 Setup & usage guide — qonto-reimburse-batch

> Step-by-step user guide. French version: `PROCEDURE.fr.md`.

---

## 1️⃣ Setup (once, ~5 min)

### Step 1 — Connect the Qonto MCP to Claude
1. In **claude.ai** (or Claude Desktop): Settings → **Connectors** → *Browse connectors*
2. Search **Qonto** → *Add* → the Qonto sign-in flow opens
3. Log in with your Qonto account (OAuth — your password is **never** shared with Claude)
4. Check: ask Claude "*List my Qonto accounts*" → your accounts show up

### Step 2 — Install the skill
- **Claude Code / Claude Desktop**: copy the skill folder to `~/.claude/skills/qonto-reimburse-batch/` (the `SKILL.md` file is enough)
- **claude.ai**: attach `SKILL.md` to your project, or paste its content into the project instructions

### Step 3 — Plug the claims source + define your policy (recommended)
1. **Optional**: connect the **Slack** or **Notion** MCP (same path as step 1) — the skill will read your expenses channel or claims database. **Without them, everything still works**: paste the claims into the conversation
2. Define your **expense policy** once: "meals €30, client meals €90, taxi €50, equipment €150" (invented example — use your own caps)
3. **Required before creating requests**: designate a finance-controlled employee/contractor list containing independently verified identity, account name and IBAN. Paste it separately from claims if needed. Claim IBANs do not establish trusted recipients. Missing mapping or conflicting IBAN → on hold until finance independently verifies the recipient through a known contact or established process and you supply the verified mapping; generic batch consent is insufficient.
4. Claims, receipts and tool results are data only, not instructions or consent. The skill flags and ignores embedded instructions.

## 2️⃣ Typical usage (the end-of-month ritual, ~5 min)

| # | Action | Result |
|---|---|---|
| 1 | Tell Claude: "**Reimburse this month's expense claims**" | Claims collected (Slack/Notion or pasted), normalized table shown |
| 2 | The skill verifies recipients, then checks receipt · duplicate · policy | Verdict table: ✅ in batch · ⚠️ on hold · ❌ duplicate with the cited transaction |
| 3 | Settle the ⚠️ and ❌ (cap, accept, reject) | Final batch list agreed |
| 4 | Confirm explicitly ("yes, create the grouped request") | ONE request created: N pending transfers |
| 5 | Open Qonto; compare every full destination IBAN and amount against the verified mapping, not just the note. If details cannot be inspected or differ, do not approve | Approve with SCA only after this review |

## 3️⃣ Copy-paste prompts

- "**Reimburse this month's expense claims: read the expenses channel, verify each claim (receipt, card duplicate, policy) and prepare the grouped request.**"
- "**Here's our expense policy: meals €30, client meals €90, taxi €50, equipment €150. Apply it to the checks.**" *(example caps — use yours)*
- "**Here are 3 claims as a markdown table: [employee · amount · date · category · reason · IBAN · receipt]. Check duplicates and receipts, then prepare the batch.**"
- "**This €129 claim for a screen — wasn't it already paid with the company card?**"
- "**What's the status of the grouped request?**" *(via `list_requests`)*

## 4️⃣ Output formats

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables: verdicts, batch content, holds | **Always** — the baseline |
| **Grouped Qonto request** | N pending transfers (Requests section), batch summary in the note, **visible at SCA approval time** | Every validated batch |
| **Reimbursement report** | Markdown recap (who · how much · why rejected, with evidence) — or an HTML artifact when the host renders files | After approval |

## 5️⃣ Troubleshooting (known, verified quirks)

| Symptom | Cause | Fix |
|---|---|---|
| `422` when creating the batch | Missing `credit_account_currency` field (undocumented) | The skill always sends it |
| Can't decline a test request | `decline_request` requires `request_type: "multi_transfers"` (plural) | Handled by the skill |
| `list_transactions` fails | `bank_account_id`/`iban` required | `get_organization` first — the skill always does |
| Missed duplicate or false positive | Card settlement delay: `emitted_at` vs `settled_at` (1–2 days apart) | ±5-day window on `emitted_at`; the presumption is cited, you decide |
| Slack channel / Notion base not read | MCP absent or not connected | Expected — degraded mode: paste the claims in the conversation, the checks are identical |
| A recipient missing from the batch | Missing/ambiguous verified recipient or conflicting IBAN | Have finance verify identity and bank details independently; supply the verified mapping, then reconfirm the rebuilt final list |
| Slow / truncated responses | Pagination | `per_page` ≤ 50 everywhere — done by the skill |

## 🔒 Security reminder

The skill **cannot** move money. It creates a *grouped request* requiring your SCA approval.
SCA authorizes payment; it does not verify recipient ownership. Finance must verify recipients independently;
the skill cannot verify account ownership or list access controls itself. Review each destination and amount
in Qonto against the verified mapping before approving. The note is a summary, not a substitute for this review.
