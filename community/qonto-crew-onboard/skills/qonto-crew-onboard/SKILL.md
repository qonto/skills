---
name: qonto-crew-onboard
description: One-sentence financial onboarding (and offboarding) of an employee on Qonto. Reads a per-role policy defined once with the user (card caps, online-only, team), then on "Alex starts Monday as a developer" it invites the member, creates the team if new, and prepares a capped card request that conforms to the policy — plus a Notion welcome page, a day-1 calendar event and a Gmail welcome draft when those MCPs are connected. Offboarding is the mirror image - freeze the cards, generate a recovery checklist, delete nothing. Use for "Alex arrive lundi comme dev", "onboard Sam as an account exec", "prépare l'arrivée de la nouvelle recrue", "Sam is leaving Friday — offboard him", "gèle sa carte".
permissions:
  mcp:
    qonto: [change_card_status, create_card, create_card_request, create_membership, create_team, get_authenticated_membership, get_organization, get_qonto_public_pricing, get_subscription, list_cards, list_memberships, list_requests, list_teams]
  network: []
  env: []
  tools: [Read]
---

# Qonto Crew Onboard

Every new hire triggers the same manual ritual: invite them on Qonto, create their card with the right caps, prepare their first day. This skill turns it into one sentence. Read-heavy, a few explicit writes: every write is individually confirmed, and anything sensitive stays behind the user's own SCA in the Qonto app.

## Prerequisites
1. `get_organization` FIRST → organization, accounts, country. Then `get_authenticated_membership` → the requester's role. **Inviting members and requesting cards require an Admin/Owner role**: if the authenticated membership is weaker, say so honestly and degrade to a read-only preview of what would be done.
2. **Country-agnostic**: memberships, teams and cards work the same on every Qonto country (FR, DE, ES, IT, AT, NL, BE, PT). No fiscal logic here — nothing to degrade.
3. **A per-role policy decided by the user** — card type, monthly cap, online-only or not, team, e.g. "developer → virtual card, €200/month, online-only, team Tech". Defined once in conversation (or pasted from the user's notes). **A role without a policy triggers questions, never a guess.**
4. Optional MCPs detected dynamically: Notion (welcome page), Google Calendar (day-1 event), Gmail (welcome draft). Absent → the skill says so and continues in pure Qonto.

## Workflow

### 1. Snapshot & permissions
`get_organization` → `get_authenticated_membership` (role check, honest warning if not Admin/Owner) → `list_memberships` (paginate `per_page` ≤ 50; count members, verify the email isn't already invited) → `list_teams` → `list_cards`. Detect which optional MCPs are connected and announce the resulting mode.

### 2. Load the policy — never invent it
Ask for (or recall) the per-role policy: card type (virtual/physical), monthly spending cap, per-transaction cap if any, online-only flag, target team. Show it back as a table. **Plan limits**: Qonto plans cap the number of members and the pricing grid is not readable via MCP (`get_subscription` → `403 missing oauth scope` on the claude.ai connector) — so ask the user which plan they're on, compare with the member count from `list_memberships`, and warn *before* inviting if the invitation could exceed the plan or carry a per-seat cost. Never state a price you didn't verify (`get_qonto_public_pricing` can help for public plan info).

### 3. Parse the sentence, then recap everything
"Alex starts Monday as a developer" → first name, role, start date. Ask for what's missing (at minimum the **email address** — required for the invitation, never guessed). Map role → policy. Then show ONE full recap table **before any write**: invitation (email, role granted on Qonto), team (existing or to create), card request (type, caps, online-only), welcome pack items. The user approves the plan as a whole, then each write is still confirmed individually.

### 4. Execute — each write individually confirmed
- `create_membership` → the Qonto invitation email goes out to the new hire. Confirm first; report as "invitation sent, pending acceptance", never as "member active".
- `create_team` only if the policy's team doesn't exist in `list_teams`. Confirm first.
- `create_card_request` → a **card request** matching the policy (holder, card type, caps, online-only). This is deliberately a *request*, not a direct `create_card`: it lands in the Requests section of the Qonto app where an Admin/Owner approves it with their own SCA. Never present the card as active — it is pending approval (`list_requests` can track it).
- Anything the MCP can't do (plan upgrade, definitive permission changes) → say so and point to the app.

### 5. Welcome pack — optional MCPs
Only if the corresponding MCP is connected, each item confirmed before creation:
- **Notion**: a welcome page — first-day info, who's who, the card policy that applies to them, pending items.
- **Google Calendar**: a day-1 event on the start date (title, attendees if emails are known).
- **Gmail**: a welcome **draft** (never sent by the skill — the user reviews and sends).
Absent MCP → one honest line ("no Notion MCP detected — skipping the welcome page") and continue.

### 6. Offboarding — the mirror image
"Sam is leaving Friday" → find Sam in `list_memberships`, find their cards in `list_cards`, then with explicit confirmation `change_card_status` to **freeze** each card. Generate a **recovery checklist**: physical card returned, equipment, app/tool accesses, pending expense claims, forwarding. **The skill never deletes or revokes anything definitive** — membership deactivation and permanent revocations happen in the Qonto app, and the checklist says exactly where. A frozen card is reversible; that's the point.

### 7. Report — output formats
**Always** reply in the conversation with markdown tables:
1. **Onboarding recap** (action · tool · status: ✅ done / 🕐 pending SCA-approval / ⏭ skipped + why).
2. **Card request status** — explicitly "pending approval in the Qonto app".
3. **Welcome pack table** (item · MCP · created/skipped).
4. Offboarding: the recovery checklist as a checkbox list.

**Additionally, when the host renders files** (claude.ai artifacts, Claude Desktop, Claude Code): a one-page **HTML onboarding sheet** (who arrives, when, what was set up, what's pending). If the host cannot render files, the markdown tables are the deliverable.

## Guardrails
- NEVER write without explicit confirmation in the current conversation — full recap first, then each write (`create_membership`, `create_team`, `create_card_request`, `change_card_status`) confirmed one by one. Never present a pending request as done.
- The per-role policy is **decided by the user, never invented**. No policy for the role → ask.
- Plan member limits: the grid isn't readable via MCP (`get_subscription` 403) → ask the plan, count members, warn before inviting.
- Offboarding **never deletes anything**: freeze + checklist only; definitive revocations happen in the Qonto app.
- Admin/Owner required for the writes — check `get_authenticated_membership` first and say honestly what will fail otherwise.
- Emails and personal data: use exactly what the user provides, never guess an address. Paginate everything (`per_page` ≤ 50).
