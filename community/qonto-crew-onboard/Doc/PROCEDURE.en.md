# 📖 Setup & usage guide — qonto-crew-onboard

> Step-by-step user guide. French version: `PROCEDURE.fr.md`.

---

## 1️⃣ Setup (once, ~5 min)

### Step 1 — Connect the Qonto MCP to Claude
1. In **claude.ai** (or Claude Desktop): Settings → **Connectors** → *Browse connectors*
2. Search **Qonto** → *Add* → the Qonto sign-in flow opens
3. Log in with your Qonto account (OAuth — your password is **never** shared with Claude)
4. Check: ask Claude "*List my Qonto members*" → your members show up
5. ⚠️ Log in with an **Admin or Owner** account — inviting members and requesting cards require it

### Step 2 — Install the skill
- **Claude Code / Claude Desktop**: copy the skill folder to `~/.claude/skills/qonto-crew-onboard/` (the `SKILL.md` file is enough)
- **claude.ai**: attach `SKILL.md` to your project, or paste its content into the project instructions

### Step 3 — Define the per-role policy (the heart of the skill)
1. Tell Claude: "**Let's define my onboarding policy**"
2. For each role: card type (virtual/physical), monthly cap, online-only or not, team
3. The skill shows it back as a table — **you** decide, it never invents
4. Tip: paste the policy into your project instructions (or a Notion note) so it's re-read on every arrival

### Step 4 — Connect the welcome-pack MCPs (optional)
- **Notion** (welcome page), **Google Calendar** (day-1 event), **Gmail** (welcome draft)
- Detected dynamically: when absent, the skill says so and continues in pure Qonto

## 2️⃣ On every arrival (~2 min)

| # | Action | Result |
|---|---|---|
| 1 | Tell Claude: "**Alex starts Monday as a developer**" | Role checked, members/teams/cards read, email asked for |
| 2 | Give Alex's email | Full recap: invitation + team + capped card request |
| 3 | Confirm each write ("yes") one by one | Invitation sent · team created if new · card **request** filed |
| 4 | In the **Qonto app**: Requests → approve the card (**SCA**) | The card exists, capped per your policy ✅ |
| 5 | (When MCPs are connected) approve the welcome pack | Notion page + day-1 event + Gmail draft ready |

## 3️⃣ Offboarding (the mirror, ~1 min)

| # | Action | Result |
|---|---|---|
| 1 | Say: "**Sam is leaving Friday**" | Their cards and profile are found |
| 2 | Confirm the freeze | `change_card_status` → cards **frozen** (reversible) |
| 3 | Follow the recovery checklist | Physical card, equipment, accesses, pending expense claims |
| 4 | In the **Qonto app**: deactivate the member | Definitive revocation — **never done by the skill** |

## 4️⃣ Copy-paste prompts

- "**Let's define my onboarding policy: developers get a virtual card, €200/month, online-only, team Tech**"
- "**Alex starts Monday as a developer, email alex@example.com**"
- "**Three interns start on the 1st, ops role**"
- "**Where is Alex's card request?**"
- "**Sam is leaving Friday — prepare the offboarding**"
- "**Freeze Sam's card**"

## 5️⃣ Output formats

| Output | Format | When |
|---|---|---|
| **Conversation reply** | Markdown tables: recap (✅ / 🕐 pending SCA / ⏭ skipped), offboarding checklist | **Always** — the baseline |
| **Onboarding sheet** | One-page **HTML** file/artifact: who, when, what's ready, what's pending | When the host renders files; fallback to tables otherwise |
| **Notion page · Calendar event · Gmail draft** | Welcome pack | When those MCPs are connected |

## 6️⃣ Troubleshooting (known, verified quirks)

| Symptom | Cause | Fix |
|---|---|---|
| `403 missing oauth scope` on `get_subscription` | Outside the claude.ai connector scope — the plan grid isn't readable | Expected — the skill **asks your plan** and counts members before inviting |
| Invitation fails or the write is refused | Connected account isn't Admin/Owner | Reconnect with an Admin/Owner account — the skill checks and announces it upfront |
| "Member already exists" | Email already invited | Caught via `list_memberships` — the skill skips the invitation and says why |
| The card doesn't show up | It's a card **request**, not a card | Qonto app → Requests → approve with SCA |
| Duplicate team | Different casing ("tech" vs "Tech") | The skill matches against `list_teams` before any `create_team` |
| Large org, truncated responses | Pagination | `per_page` ≤ 50 everywhere, handled by the skill |
| No Notion page / event / draft | MCP not connected | Expected — announced by the skill, the Qonto core continues |

## 🔒 Security reminder

The skill **never creates a card directly**: it files a *request*, capped per your policy, that **only you**
(or an Admin/Owner) can approve with SCA in the Qonto app. Every write is confirmed one by one in the
conversation, after a full recap. And offboarding **freezes** — it deletes nothing: definitive revocations
stay in the app, under your control.
