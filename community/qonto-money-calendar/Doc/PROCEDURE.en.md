# 📖 Setup & usage guide — qonto-money-calendar

> Step-by-step user guide. French version: `PROCEDURE.fr.md`.

---

## 1️⃣ Setup (once, ~5 min)

### Step 1 — Connect the Qonto MCP to Claude
1. In **claude.ai** (or Claude Desktop): Settings → **Connectors** → *Browse connectors*
2. Search **Qonto** → *Add* → the Qonto sign-in flow opens
3. Log in with your Qonto account (OAuth — your password is **never** shared with Claude)
4. Check: ask Claude "*List my Qonto accounts*" → your accounts show up

### Step 2 — Connect the Google Calendar MCP (required for both directions)
1. Same path: Settings → **Connectors** → search **Google Calendar** → *Add* → Google login (OAuth)
2. Check: ask Claude "*What's on my calendar tomorrow?*"

> Without Google Calendar: direction 1 outputs the schedule as a **table in the conversation**,
> and direction 2 (invoicing from the calendar) is **unavailable** — the skill will tell you plainly.

### Step 3 — Install the skill
- **Claude Code / Claude Desktop**: copy the skill folder to `~/.claude/skills/qonto-money-calendar/` (the `SKILL.md` file is enough)
- **claude.ai**: attach `SKILL.md` to your project, or paste its content into the project instructions

### Step 4 — Adopt the tag convention (for direction 2)
When you work for a client, drop an event in your calendar with **the client's name in square brackets** in the title:

| You write in the calendar | The skill counts |
|---|---|
| `[Acme] onsite sprint` | 1 billable day for Acme |
| `[Acme] workshop` spanning 3 days | 3 days |
| `[Acme] 0.5 code review` | half a day |
| `Dentist 3pm` (no brackets) | Nothing — ignored |

That's it. No extra tool, no time-tracker: your calendar **is** the time-tracker.

## 2️⃣ Typical usage

### The Sunday-evening (or first-of-the-month) ritual — direction 1

| # | Action | Result |
|---|---|---|
| 1 | Tell Claude: "**Put my money month in my calendar**" | Reads supplier/client invoices + 24–36 months of recurrences |
| 2 | Read the **recap** (date · title · amount · source 🟢/🟡) | You see exactly what will be created — drop lines if you want |
| 3 | Confirm explicitly ("yes, create them") | Events created: amount in the title, D-3 reminder, anti-duplicate marker |
| 4 | Open Google Calendar | Your money month is visible — rent, suppliers, expected receipts |

### End of month — direction 2

| # | Action | Result |
|---|---|---|
| 1 | Tell Claude: "**Invoice my June**" | Counts the days tagged `[Client]`, shows the list of dates |
| 2 | Check the count (a forgotten tag shows up here) | Days × client table |
| 3 | Confirm the **proposed day rate** (deduced from your past invoices) or give another | The rate is never guessed — always confirmed |
| 4 | Confirm the lines | `create_client_invoice` as a **DRAFT** in Qonto |
| 5 | Review in Qonto → send when you decide | The invoice goes out with your usual numbering and legal mentions |

## 3️⃣ On-demand usage

- "**What's due this week?**" → the next 7 days' schedule, as a table
- "**Add my July deadlines to the calendar**" → direction 1 on a specific window
- "**How many days did I do for [Acme] this quarter?**" → counting without invoicing
- "**Re-run the schedule**" → marked events are updated, never duplicated

## 4️⃣ Output formats

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables: schedule, pre-write recap, day counts, invoice summary | **Always** — the baseline |
| **Google Calendar** | Dated events, amount in the title, D-3 reminder, `[qonto-money-calendar]` marker | When the MCP is present **and** the recap confirmed |
| **Qonto invoice** | `create_client_invoice` draft, Invoicing section | Direction 2, after rate & lines confirmed |

## 5️⃣ Troubleshooting (known, verified quirks)

| Symptom | Cause | Fix |
|---|---|---|
| `list_transactions` fails | Missing `bank_account_id`/`iban` | The skill calls `get_organization` first — always |
| Huge / truncated responses | Pagination too wide | `per_page` ≤ 50 everywhere, 3-month windows |
| Direction 2 "finds nothing" | Days lack `[Client]` brackets in the title | Check the tag convention (setup step 4) |
| Duplicate events after a re-run | Events created outside the skill, without the marker | The skill updates its own marked events; hand-made ones are left alone |
| Tagged client not found in Qonto | Spelling differs from the client record | The skill lists close candidates and asks — it never creates a client on its own |
| Yearly recurrences missing | History < 24 months | Expected — yearly cadences need 24–36 months; the skill says so |
| Test invoice to remove | Rehearsal / demo | Fictional client + draft + `delete_client_invoice` |

## 🔒 Security reminder

The skill **cannot** move money — it schedules and drafts. Calendar events only exist after
a recap **you** confirm. Invoices stay in **draft**: you review, you send. Paying a supplier
remains an action in the Qonto app, protected by your own SCA (2FA). The day rate is deduced
from your history **then confirmed by you** — never guessed.
