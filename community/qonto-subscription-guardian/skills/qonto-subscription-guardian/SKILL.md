---
name: qonto-subscription-guardian
description: Capped virtual card generation for Qonto subscriptions — an action utility, nothing more. Lightly detects recurring charges (cards AND direct debits, monthly, quarterly AND yearly) over 24–36 months just to list subscription candidates, lets the user pick which ones to protect, then — one at a time, with explicit consent and the user's own SCA — creates a dedicated capped virtual card per chosen subscription (payment_monthly_limit = current price + a small margin) and names it SUB-<Vendor>. Checks the plan's virtual-card allowance before proposing anything. Use for "cap this subscription", "plafonne cet abonnement", "une carte par abonnement", "protect my subscriptions with capped cards", "Adobe surpréleve, bloque-le". For the full recurring-spend audit (annual cost, zombies, duplicates, price increases), use qonto-subscription-audit instead.
permissions:
  mcp:
    qonto: [change_card_status, create_card, create_card_request, get_authenticated_membership, get_organization, get_subscription, list_cards, list_transactions, modify_transaction_cash_flow_category, update_card]
  network: []
  env: []
  tools: [Read]
---

# Qonto Subscription Guardian

One job: give each subscription its own capped virtual card, so no vendor can ever charge more than what the user decided. Dedicated-card protection is a feature Qonto will probably ship natively one day — this skill gives it to the user today. Read-light, one safe write: a card only exists after explicit consent for THAT card AND the user's own SCA confirmation in the Qonto app.

Out of scope (→ `qonto-subscription-audit`): total annualized cost, zombie/duplicate/trial classification, price-increase timelines, email digests. If the user asks for those, point them to that skill and continue with the cards.

## Prerequisites
1. `get_organization` **first** → `bank_account_id` per account (required by `list_transactions`), balances, country. Then `get_authenticated_membership` → membership id (used as `holder_id`/`initiator_id` when a card is created) and role.
2. **Card writes need a role**: direct `create_card` requires Owner/Admin/Manager. Other roles: fall back to `create_card_request` (an admin approves in the app).
3. **Check the plan's virtual-card allowance BEFORE proposing any card**: Qonto plans limit virtual cards — **Basic: 2 included (€2/month each beyond) · Smart/Premium: 50 included (€1/card beyond) · Essential/Business/Enterprise: unlimited** (public grid, qonto.com pricing). The exact plan is NOT readable via MCP (`get_subscription` returns `403 missing oauth scope` on the claude.ai connector): count existing cards with `list_cards`, state the public grid, ask the user which plan they're on, and propose a NUMBER of cards that fits it — never an unconsented batch.
4. **History**: ≥ 24 months recommended so yearly subscriptions (only 2 occurrences past 12 months) are catchable; below that, yearly ones can slip under the radar — the skill says so honestly and audits what it sees.

## Workflow

### 1. Map the account
`list_cards` (paginate `per_page` ≤ 50) → existing cards, `last_digits`, nicknames, and **the card count** (for the plan check). Cards already named `SUB-<Vendor>` are **already-guarded** subscriptions — idempotence: never propose them a second time. Recurring card charges will be matched to the card that pays them.

### 2. Light detection — candidates only (24–36 months)
`list_transactions` per account, paginate `per_page: "50"` in 3-month windows, across **24–36 months** — wide enough to catch **yearly** subscriptions, which need 2 occurrences more than 12 months apart. Match cadence on **`emitted_at`** for card charges — `settled_at` lags 1–2 days and breaks the math.
A **candidate** = same **normalized counterparty** (strip `*`, store/city codes, casing) + regular cadence (monthly 28–32 d · quarterly 85–95 d · **yearly 350–380 d**) + amount stable **±15 %** + ≥ 3 occurrences (2 for yearly). Card charges AND direct debits both count. **Plus**: a first charge from a merchant Claude knows to be a subscription business (SaaS — Netflix, Adobe, Microsoft 365, OpenAI, Figma, Slack; course platforms — Systeme.io, Skool, Kajabi; hosting & domain registrars — OVH, Gandi, IONOS, whose domains renew YEARLY; cloud — AWS, Scaleway) is a candidate immediately — flagged "known subscription vendor · 1st occurrence", no history needed.
Output: ONE markdown table — vendor · price · cadence (M/Q/**Y**) · last charge · paying card · already `SUB-`-guarded or not. **No classification, no annual total, no verdicts** — that's `qonto-subscription-audit`'s job.

### 3. Plan reminder & user choice
Recall the card count and the public grid (Basic 2 / Smart-Premium 50 / higher plans unlimited), ask the user's plan if unknown, and let **the user pick** which subscriptions to protect — proposing a number of cards that fits the announced plan. The skill suggests, the user decides; never a bulk creation.

### 4. Create the capped cards — one at a time
For each chosen subscription, with **explicit confirmation for that specific card**: `create_card` with `card_level: "virtual"`, the account's `bank_account_id`, `organization_id`, `holder_id`/`initiator_id` from `get_authenticated_membership`, and **`payment_monthly_limit` = current price + a small margin** (integer euros, rounded up — ~10 %, or +1–2 € on small amounts). **Yearly subscriptions: size `payment_transaction_limit` to the yearly price instead.**
Be honest about SCA: **each creation is a Strong-Customer-Authentication action — the call blocks until the user confirms the Qonto push notification on their paired device**, and depending on their role it may not be allowed at all (→ `create_card_request`, approved by an admin). NEVER present a card as created before the tool returns it.

### 5. Name it, hand it off
`update_card` to set the nickname `SUB-<Vendor>` (`create_card` has no nickname field), then state the one manual step left: **switch the payment method at the vendor** — `get_card_iframe_url` renders PAN/CVV for that; the URL is a short-lived credential for the user's eyes only, never echo, log or store it.

### 6. Lifecycle & recap
`change_card_status` to `lock` (reversible pause) or `discard` (permanent). Raising a cap later after an accepted price change is done in the Qonto app — card limits are **not editable via MCP**. End with a recap table: cards created, caps, and vendors still to migrate.

## Guardrails
- NEVER create a card or card request without explicit confirmation for that specific card in the current conversation; never present it as done while SCA confirmation is pending.
- Plan check first, always: `list_cards` count + the 2/50/unlimited grid before any proposal; the number of proposed cards fits the user's announced plan.
- **Capping ≠ cancelling**: the contract survives the card. A declined charge can trigger vendor dunning or service suspension — say so BEFORE capping below the current price or locking. Remind notice periods (French B2B contracts often auto-renew).
- Rehearsals on a real account: at most one demo card, clearly named, `change_card_status` → `discard` at the end; never show a full PAN on screen.
- Mask IBANs and card numbers (last 4 digits). Paginate everything (`per_page` ≤ 50). Detected prices are estimates — the vendor's invoice remains the source of truth when sizing a cap.
