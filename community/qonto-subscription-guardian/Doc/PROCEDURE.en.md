# 📖 Setup & usage guide — qonto-subscription-guardian

> Step-by-step user guide. French version: `PROCEDURE.fr.md`.
> For the full recurring-spend audit (annual cost, duplicates, price increases…): the **`qonto-subscription-audit`** skill.

---

## 1️⃣ Setup (once, ~5 min)

### Step 1 — Connect the Qonto MCP to Claude
1. In **claude.ai** (or Claude Desktop): Settings → **Connectors** → *Browse connectors*
2. Search **Qonto** → *Add* → the Qonto sign-in flow opens
3. Log in with your Qonto account (OAuth — your password is **never** shared with Claude)
4. Check: ask Claude "*List my Qonto accounts*" → your accounts show up

### Step 2 — Install the skill
- **Claude Code / Claude Desktop**: copy the skill folder to `~/.claude/skills/qonto-subscription-guardian/` (the `SKILL.md` file is enough)
- **claude.ai**: attach `SKILL.md` to your project, or paste its content into the project instructions

> ℹ️ Creating cards directly requires an **Owner/Admin/Manager** role on Qonto.
> With any other role: the skill falls back to `create_card_request` (an admin approves in the app) — and detection itself works for everyone.

## 2️⃣ Typical usage: list, pick, cap (~5 min)

| # | Action | Result |
|---|---|---|
| 1 | Tell Claude: "**List my subscriptions**" | Light detection across **24–36 months** (wide enough for **yearly** ones): candidate table — vendor, price, cadence M/Q/Y, paying card, already guarded or not |
| 2 | Read the plan reminder | `list_cards` count + the grid: **Basic 2 included · Smart/Premium 50 · Essential/Business/Enterprise unlimited** — the skill asks for your plan and proposes a number of cards that fits |
| 3 | Pick the subscriptions to protect | You alone decide — never a bulk run, existing `SUB-` cards are never proposed twice |
| 4 | Confirm card #1 explicitly | Virtual `create_card`, monthly cap = current price + a small margin (yearly: per-transaction cap) |
| 5 | On your **phone**: Qonto push notification → **confirm (SCA)** | The `SUB-<Vendor>` card exists, capped ✅ — repeat steps 4-5 for each chosen subscription, **one SCA every time** |
| 6 | Switch the payment method **at each vendor** (manual step) | `get_card_iframe_url` renders the card number — for your eyes only |

## 3️⃣ On-demand usage

- "**Cap Adobe**" → a single card, same path: explicit confirmation + SCA
- "**Which SUB- cards already exist?**" → list of already-protected subscriptions (idempotence)
- "**Lock the SUB-X card**" → `change_card_status` lock (reversible) — with a warning about vendor-side consequences first
- "**Audit my subscriptions**" (annual cost, duplicates, increases…) → that's the **`qonto-subscription-audit`** skill, not this one

## 4️⃣ Output formats

| Output | Format | When |
|---|---|---|
| **Candidate list** | Markdown table: vendor · price · cadence M/Q/Y · paying card · already guarded | After light detection |
| **Created-cards recap** | Markdown table: card · cap · vendor · still to switch | End of session |

## 5️⃣ Troubleshooting (known, verified quirks)

| Symptom | Cause | Fix |
|---|---|---|
| `403 missing oauth scope` on `get_subscription` | Qonto's own subscription (plan, card quotas) isn't readable through the claude.ai connector | Expected — the skill states the public grid and asks for your plan |
| Worried the plan's card quota will block you | Qonto plans limit virtual cards: **Basic = 2 included (€2/month beyond) · Smart/Premium = 50 included (€1/card beyond) · Essential/Business/Enterprise = unlimited** | The skill counts existing cards (`list_cards`), recalls this grid and proposes a **number of cards that fits the plan you announce** — never a bulk run |
| `list_transactions` fails right away | Missing `bank_account_id`/`iban` | The skill **always** calls `get_organization` first |
| Card creation "hangs" | That's **SCA**: the call blocks until the push notification is confirmed on the paired device | Confirm on your phone — or decline; nothing is created without you |
| Card creation rejected (role) | Direct `create_card` requires Owner/Admin/Manager | Automatic fallback to `create_card_request` (an admin approves in the app) |
| The new card has no name | `create_card` has no nickname field | The skill chains `update_card` → `SUB-<Vendor>` right after |
| Can't change a card limit via MCP | `update_card` only handles the nickname (options are physical-card only) | Adjust the cap in the Qonto app — the skill says so plainly |
| A known subscription isn't listed | Cadence broken by `settled_at` (1–2 day card lag), amount too variable, or a **yearly one with less than 24 months of history** | The skill matches on `emitted_at`, tolerates ±15 % and scans 24–36 months; below 24 months it warns that yearly subscriptions can slip under the radar |

## 🔒 Security reminder

The skill **cannot** spend your money. Creating a card is an **SCA** action: the call stays blocked until
**you alone** confirm the push notification on your paired Qonto device — and you can decline in one tap,
for every single card. The created card is **capped** at the amount you approved: that's exactly its point.
Capping is not cancelling — the vendor contract continues until you terminate it.
