# 📖 Setup & usage guide — qonto-rgpd-register

> Step-by-step user guide. French version: `PROCEDURE.fr.md`.

---

## 1️⃣ Setup (once, ~5 min)

### Step 1 — Connect the Qonto MCP to Claude
1. In **claude.ai** (or Claude Desktop): Settings → **Connectors** → *Browse connectors*
2. Search **Qonto** → *Add* → the Qonto sign-in flow opens
3. Log in with your Qonto account (OAuth — your password is **never** shared with Claude)
4. Check: ask Claude "*List my Qonto accounts*" → your accounts show up

### Step 2 — Install the skill
- **Claude Code / Claude Desktop**: copy the skill folder to `~/.claude/skills/qonto-rgpd-register/` (the `SKILL.md` file is enough)
- **claude.ai**: attach `SKILL.md` to your project, or paste its content into the project instructions

### Step 3 — Nothing else to configure
No sub-account, no API key, no extra MCP: the skill is **100% read-only** on the Qonto MCP alone.
Just plan the human hand-off: the register it produces is a **draft**, to be validated by your DPO or lawyer.

## 2️⃣ Typical usage (the big scan, ~5 min)

| # | Action | Result |
|---|---|---|
| 1 | Tell Claude: "**Draft my GDPR register from my spending**" | 12–24 months of debits + supplier invoices scanned, processors detected |
| 2 | Read the summary table (tool · category · purpose · EU/non-EU · flags) | You discover who actually processes your data — usually with surprises |
| 3 | Browse the Article 30 cards (one per activity, "to validate" tags visible) | The register exists — pre-filled, no more blank page |
| 4 | Work the prioritized to-do: DPAs first, non-EU transfers next, ghost tools last | Every flag becomes a concrete action |
| 5 | Hand the HTML document to your DPO/lawyer for validation | Validated register, legal bases and retention set by a human ✅ |

## 3️⃣ Copy-paste prompts

- "**Draft my GDPR register from my spending**" → the full flow: summary + cards + to-do
- "**Which of my vendors process personal data?**" → the summary table alone
- "**Which of my tools send data outside the EU?**" → focus on the 🔴 transfer flags
- "**Which DPAs should I check or sign?**" → the 🟠 to-do, vendor by vendor
- "**Which tools disappeared from my debits in the last 6 months?**" → candidates to retire from the register
- "**Regenerate the register and compare with last time**" → new entrants / retirees since the last scan

## 4️⃣ Output formats (where does the register land?)

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables: summary, one card per activity, prioritized to-do | **Always** — the baseline |
| **Print-ready register** | **HTML** file/artifact: controller header, Article 30 cards, processor annex, to-do | When the host renders files (claude.ai artifacts, Claude Desktop, Claude Code); automatic fallback to tables otherwise |
| **Disclaimer banner** | "Draft register, not legal advice — validate with a DPO or lawyer" | On **every** output, no exception |

## 5️⃣ Troubleshooting (known, verified quirks)

| Symptom | Cause | Fix |
|---|---|---|
| `list_transactions` fails right away | Missing `bank_account_id`/`iban` | The skill **always** calls `get_organization` first |
| Huge / truncated responses | Pagination too wide | `per_page` ≤ 50, 3-month windows — handled by the skill |
| `403 missing oauth scope` on `list_cash_flow_categories` | Outside the claude.ai connector scope | No impact — the skill doesn't need it (labels as fallback if useful) |
| The same tool shows up twice | Multiple spellings of one vendor (`GOOGLE *WORKSPACE` vs `Google Ireland`) | Automatic normalization + merge; report any leftover duplicate |
| A tool you know isn't detected | Paid through a reseller, marketplace or app store — the label masks the vendor | Flagged 🟡 and the skill **asks** which product sits behind the charge |
| Unreadable card label | Card labels are messier than invoices | Cross-checked with `list_supplier_invoices`; otherwise "unidentified — check the invoice" |
| "Last used" date looks off | Card settlement delay (1–2 days) | The skill reads `emitted_at`, not `settled_at` |

## 🔒 Security reminder

The skill is **100% read-only**: four read tools, no write tool. Nothing moves on the account,
no vendor is contacted, nothing is sent anywhere. And the document it produces is a **draft register**,
not legal advice: role qualification, legal bases and retention periods are validated by your DPO
or lawyer — the skill repeats this on every output.
