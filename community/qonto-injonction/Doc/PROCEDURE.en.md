# 📖 Setup & usage guide — qonto-injonction

> Step-by-step user guide. French version: `PROCEDURE.fr.md`.

---

## 1️⃣ Setup (once, ~5 min)

### Step 1 — Connect the Qonto MCP to Claude
1. In **claude.ai** (or Claude Desktop): Settings → **Connectors** → *Browse connectors*
2. Search **Qonto** → *Add* → the Qonto sign-in flow opens
3. Log in with your Qonto account (OAuth — your password is **never** shared with Claude)
4. Check: ask Claude "*List my unpaid client invoices*" → your invoices show up

### Step 2 — Install the skill
- **Claude Code / Claude Desktop**: copy the skill folder to `~/.claude/skills/qonto-injonction/` (the `SKILL.md` file is enough)
- **claude.ai**: attach `SKILL.md` to your project, or paste its content into the project instructions

### Step 3 — Nothing else to configure
Both public APIs (BODACC, the French company registry) are **keyless and account-free**.
Only condition: the Claude host must be able to reach the web. Otherwise the skill asks you
for the two missing facts (debtor's registered office, any known insolvency) instead of guessing.

> 💡 Before the injunction comes the amicable stage: that's `qonto-invoice-chaser` (graduated
> reminders up to the formal notice). The injunction comes **after** — the skill reminds you if the case looks premature.

## 2️⃣ Typical usage (from "they'll never pay" to a signed file, ~10 min)

| # | Action | Result |
|---|---|---|
| 1 | Tell Claude: "**This invoice will never get paid — prepare the payment-order file**" | The skill targets the invoice and confirms the debtor's identity with you (SIREN confirmed) |
| 2 | Let the non-payment proof run | Incoming transactions scanned since the issue date: nothing matches (or partial payments detected and deducted) |
| 3 | Read the BODACC result | "No collective proceedings as of DD/MM" → injunction OK · Proceeding found → switch to the proof of claim (2-month deadline) |
| 4 | Check the computation (principal, interest, €40) | Detailed table, formula and semester rate shown — **indicative, to be validated** |
| 5 | Collect the dossier | CERFA 12946 pre-filled field by field + exhibits P1–P6 (Qonto receipts retrieved, missing ones listed) |
| 6 | **You**: sign, then file on infogreffe.fr (~€35, PDFs < 2 MB) | What happens next is explained: order → service (6 months) → opposition (1 month) |

## 3️⃣ Copy-paste prompts

- "**Prepare a payment-order file for invoice INV-2026-017**" → complete dossier
- "**Is my debtor in collective proceedings?**" → BODACC check alone
- "**Compute the late-payment interest on this invoice**" → detailed computation (art. L441-10)
- "**Which court has jurisdiction over this client?**" → court identified from the registered office
- "**This client just filed for bankruptcy — what do I do?**" → proof of claim drafted, 2-month deadline stated

## 4️⃣ Output formats

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables: claim computation, CERFA field→value pre-fill, exhibit list ✅/📋, route banner | **Always** — the baseline |
| **Printable dossier** | **HTML** file/artifact: cover sheet, computation, pre-filled form, exhibit list — save as PDF | When the host renders files; automatic fallback to tables otherwise |
| **Exhibits** | Receipts retrieved from Qonto (`get_attachment`) + a "to provide" list | Every dossier |

## 5️⃣ Troubleshooting (known, verified quirks)

| Symptom | Cause | Fix |
|---|---|---|
| `list_transactions` fails right away | Missing `bank_account_id`/`iban` | Expected — the skill always calls `get_organization` first |
| Truncated responses / slowness | Page size too large | The skill paginates `per_page` ≤ 50 everywhere |
| Debtor has no SIREN in Qonto | Incomplete client record | Registry lookup by name + city — **you** confirm the right match (homonyms) |
| BODACC returns nothing for a debtor known to be in trouble | Name search (noisy) instead of SIREN | The skill always searches by SIREN; the check date is displayed |
| Receipt not found via `get_attachment` | Never uploaded to Qonto | Listed as "📋 to provide" in the exhibit list — never invented |
| No web access from the host | Public APIs unreachable | The skill says so and asks you for the two facts (office, known insolvency) |

## 🔒 Security reminder

This skill uses **no write tool at all**: it files nothing, serves nothing, signs nothing.
It assembles a **ready-to-sign** dossier — filing on Infogreffe is you, with your own signature.
Interest amounts are an **indicative computation**: have them validated (lawyer, court bailiff,
or the court clerk) before filing. This is not legal advice.
