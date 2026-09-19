# 📖 Setup & usage guide — qonto-vat-return

> Step-by-step user guide. French version: `PROCEDURE.fr.md`.

---

## 1️⃣ Setup (once, ~5 min)

### Step 1 — Connect the Qonto MCP to Claude
1. In **claude.ai** (or Claude Desktop): Settings → **Connectors** → *Browse connectors*
2. Search **Qonto** → *Add* → the Qonto sign-in flow opens
3. Log in with your Qonto account (OAuth — your password is **never** shared with Claude)
4. Check: ask Claude "*List my Qonto accounts*" → your accounts show up

### Step 2 — Install the skill
- **Claude Code / Claude Desktop**: copy the skill folder to `~/.claude/skills/qonto-vat-return/` (the `SKILL.md` file is enough)
- **claude.ai**: attach `SKILL.md` to your project, or paste its content into the project instructions

### Step 3 — (Recommended) Keep your invoicing in Qonto
The more client and supplier invoices live in Qonto (Invoicing module), the sharper the CA3 table:
exact per-rate breakdown, reliable receipt-to-invoice matching, readable `vat_payment_condition`.
Without invoices, the skill works from transactions alone and **states its limits** instead of guessing.

## 2️⃣ Monthly usage (before the 15th–24th deadline, ~5 min)

| # | Action | Result |
|---|---|---|
| 1 | Tell Claude: "**Prepare my VAT return for June**" | Regime + filing frequency + chargeability detected, stated up front |
| 2 | Read the **box-by-box table** (box → label → amount → justification) | You know exactly where every euro of every box comes from |
| 3 | Read the **consistency checks** ✅/⚠️ (vs past months, vs DGFIP payments, vs statements) | Discrepancies are explained before you copy anything |
| 4 | Have your **accountant validate** (especially reverse charge / fixed assets / prior credit) | Safety — the skill recommends it in every report |
| 5 | Copy the boxes into the **tax portal** (whole-euro rounded amounts provided) | Return filed — by you, not by the skill |

## 3️⃣ On-demand usage

- "**How much VAT will I owe this month?**" → net position (line 28 or credit 25/27) + breakdown
- "**My collected VAT for June, per rate?**" → bases and tax at 20 / 10 / 5.5 / 2.1%
- "**Which debits have no VAT info this month?**" → the untagged-debits list (the floor, explained)
- "**Compare this quarter's VAT to previous quarters**" → history + commented deviations
- "**Any EU purchases I should reverse-charge?**" → candidate transactions flagged, for the accountant

## 4️⃣ Output formats (where does the return land?)

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Box-by-box CA3 table + checks table ✅/⚠️ | **Always** — the baseline |
| **Interactive dashboard** | **HTML** file/artifact: form-like view, per-rate split, history vs DGFIP payments | When the host renders files (claude.ai artifacts, Claude Desktop, Claude Code); automatic fallback to tables otherwise |
| **Nothing else** | No transmission, no Qonto write | Never — by design |

## 5️⃣ Troubleshooting (known, verified quirks)

| Symptom | Cause | Fix |
|---|---|---|
| "bank_account_id required" on `list_transactions` | `get_organization` wasn't called first | The skill always starts with `get_organization` |
| Truncated / slow responses | Page size too large | The skill paginates `per_page` ≤ 50 everywhere |
| `403 missing oauth scope` on `list_cash_flow_categories` | Outside the claude.ai connector scope | Expected — the skill uses labels instead |
| Collected VAT wrong although the invoices are right | Cash-basis VAT missed elsewhere — here the skill reads `vat_payment_condition` | Check the client invoices carry the mention; otherwise state it in the prompt |
| An incoming payment appears in no box | Receipt with no matched invoice | Expected: listed under "unmatched receipts" — decide with your accountant |
| The skill declines to produce a CA3 | Simplified regime (CA12) detected, or non-French company | Intended — out of scope, stated (with the 2027-01-01 abolition reminder) |
| Gap vs the accountant's figure | Untagged debits (floor) or pending reverse charge | Read the untagged count and the transactions flagged "to verify" |

## 🔒 Security reminder

The skill **files nothing and cannot file anything**: no write tool, no transmission.
It reads your account, computes, cross-checks, and hands you a table. **You** (or your accountant)
copy the boxes into the tax portal. Every report recommends accountant validation — especially
for reverse charge, fixed assets and the prior credit.
