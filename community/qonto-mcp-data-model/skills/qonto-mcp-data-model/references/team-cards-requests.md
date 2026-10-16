# Team, cards, requests, subscription

## Membership — `get_authenticated_membership`, `list_memberships`, `create_membership`

A person with access to the organization. `get_authenticated_membership` = the token owner ("me").

```jsonc
// get_authenticated_membership (full view)
{
  "membership": {
    "id": "22222222-…-uuid",
    "first_name": "Jane", "last_name": "Doe",
    "email": "jane@acme.example",
    "phone_number": "+33600000000",
    "role": "owner",                 // owner | admin | manager | employee | reporting
    "status": "active",
    "kyc_status": "accepted",        // identity-verification state
    "locale": "fr",
    "position": null,
    "team_id": "dddd4444-…-uuid"
  }
}

// list_memberships entries are slimmer: id, first_name, last_name, role, status, team_id
```

- `role` enum (5 values): `owner`, `admin`, `manager`, `reporting`, `employee`.
- ⚠️ `status` has **no documented enum** upstream (example: `active`; live values like `invited` may exist) — treat as an open string.
- Spanish orgs only: extra fields `residence_country`, `birthdate`, `nationality`, `birth_country`, `ubo` (Ultimate Beneficial Owner flag).

`create_membership(email, first_name, last_name, role, team_id)` invites by email:
- roles limited to **`employee` | `reporting`** (owners/admins are promoted elsewhere);
- ⚠️ `team_id` is marked optional in the spec but the upstream **rejects calls without it** — always pass one (resolve via `list_teams`).

## Team — `list_teams`, `create_team`

Minimal shape: `{"id": uuid, "name": "Équipe commerciale"}`. Used as `team_id` on memberships and for manager-scoped visibility.

## Card — `list_cards`, `create_card`, `update_card`, `change_card_status`, `get_card_iframe_url`

Cards belong to a `holder_id` (membership) and a `bank_account_id`. The `card_level` picks the variant **and** the required-field set:

| `card_level` | Physical? | Budget model |
|---|---|---|
| `standard`, `plus`, `metal` | yes (stays `pending` until PIN set in webapp) | daily/monthly/per-transaction limits + ATM limits |
| `virtual`, `virtual_partner` | no | recurring monthly budget |
| `flash` | no | one-shot `payment_lifespan_limit` + `pre_expires_at` |
| `advertising` | no | daily/monthly payment limits |

Observed read shape (truncated to the meaningful fields):

```jsonc
{
  "id": "eeee5555-…-uuid",
  "organization_id": "…", "bank_account_id": "…",
  "holder_id": "22222222-…-uuid",              // membership
  "embossed_name": "JANE DOE",
  "nickname": "Ops card",
  "card_level": "standard", "card_type": "debit",   // card_type: debit | prepaid
  "card_design": "standard.recycled.plastic.2023",
  "status": "shipped_lost",                    // full enum below
  "last_digits": "4321", "mask_pan": "512345******4321",
  "exp_month": "8", "exp_year": "2023",
  "pin_set": true,
  // spend controls
  "payment_daily_limit": 1000, "payment_monthly_limit": 1000, "payment_transaction_limit": 1000,
  "payment_daily_spent": 0,    "payment_monthly_spent": 0,
  "payment_lifespan_limit": null, "payment_lifespan_spent": 0,   // flash cards
  "atm_option": true, "atm_daily_limit": 100, "atm_monthly_limit": 100,
  "atm_daily_spent": 0, "atm_monthly_spent": 0,
  "nfc_option": true, "online_option": true, "foreign_option": true,
  "active_days": [1,2,3,4,5,6,7],              // ISO 8601 weekdays, 1 = Monday
  "categories": [],                            // MCC restriction tags; [] = all allowed (Team plan+)
  "appearance": {"theme": "light", "assets": {"front_large": "https://…png", "…": "…"}},
  // shipping / lifecycle flags
  "shipped_at": "2020-08-31T00:00:00Z", "discard_on": null, "pre_expires_at": null,
  "renewal": false, "renewed": false, "eligible_for_renewal": false,
  "created_at": "2020-08-26T07:37:56.687623Z", "updated_at": "2025-05-14T20:05:37.232037Z",
  "last_activity_at": "2020-08-26T07:37:56.687623Z"
}
```

### `status` enum (13 documented values)

| Status | Meaning |
|---|---|
| `pending` | awaiting PIN set or issuing completion |
| `live` | active, usable |
| `paused` | unusable until un-paused (check `has_only_user_liftable_locks`: `false` = locked for non-user reasons, e.g. org suspended) |
| `pin_blocked` | too many wrong PIN attempts — ⚠️ still usable for card-not-present payments |
| `lost` / `stolen` | reported by holder — terminal |
| `shipped_lost` | lost during shipping |
| `expired` / `pre_expired` | expired / flash card reached validity end |
| `discarded` | permanently discarded |
| `onhold` | issuing on hold pending KYC/KYB |
| `order_canceled` | order canceled |
| `abusive` | reported as abusive |

- `last_activity_at` = last use **attempt** (successful or failed), excludes settings changes.
- `renewed`/`renewal`, `upsold`/`upsell` + `discard_on` (= upsold_at + 30 days), `parent_card_summary {id, last_digits}` track renewal/upsell chains.
- ⚠️ `is_qcp` (seen in live captures) is **not documented upstream** — treat as internal.
- Category restriction tags: `transport`, `restaurant_and_bar`, `food_and_grocery`, `it_and_electronics`, `utility`, `tax`, `legal_and_accounting`, `atm`, `office_supply`, `hardware_and_equipment`, `finance`.
- `create_card` is an **SCA action**: in production the call blocks until the user confirms the push notification on their paired device. `type_of_print` (`print`/`embossed`) is `plus`-only.
- `get_card_iframe_url(id, accept_language: en|it|es|de|fr|pt)` returns a **one-shot short-lived URL** whose target renders number/expiry/CVV (never as JSON). Treat it like a password; deliver only to the requesting user.
- `change_card_status(id, <action>: true)` — exactly one of `lock` (reversible), `unlock` (owners/admins only), `lost` / `stolen` / `discard` (**permanent**).
- `update_card(id, …)` — exactly one of `nickname` OR `options`; `options` requires all four flags together (`atm_option`, `nfc_option`, `online_option`, `foreign_option`) and works on physical tiers only (virtual/flash/advertising reject it). Limits are not updatable through MCP.

## Request — `list_requests`, `create_card_request`, `create_multi_transfer_request`, `approve_request`, `decline_request`

Expense-management approval workflow.

- `request_type`: `flash_card` | `virtual_card` | `transfer` | `multi_transfer`.
- `status`: `pending` → `approved` | `declined` (by approver) | `canceled` (by requester).
- Visibility is **role-scoped**: employees see their own, managers their team's, admins/owners everything.
- ⚠️ **Plan-gated**: on a Solo-lineup plan, `list_requests` returns HTTP **403 Forbidden** — requests need a Business or Enterprise plan. Handle 403 as "not available on this plan".
- `create_card_request`: exactly one of `flash` (one-shot budget) or `virtual` (monthly budget) for the authenticated membership; owners can bypass via `create_card`.
- `create_multi_transfer_request(note, transfers[1..400], debit_iban?, scheduled_date?)` bundles SEPA transfers into one pending approval batch. Per-transfer objects carry beneficiary name/IBAN, amount, currency, reference. **Nothing executes until a reviewer approves with their own SCA.**
- ⚠️ **MCP behavior of `approve_request`**: it does **not** approve anything. It returns an `approval_url` deeplink that opens the request in the Qonto app, where the user reviews and approves with their own SCA. `decline_request(request_type, id, declined_note)` does decline directly (`declined_note` required). Both take the **plural** `request_type` (`flash_cards` / `virtual_cards` / `transfers` / `multi_transfers`).

### Request object shape

Common fields: `id`, `request_type` (discriminator), `status`, `initiator_id` (requester), `approver_id` (null until reviewed), `note`, `declined_note?`, `created_at`, `processed_at?` (null while pending).

Per-type fields (⚠️ amounts here are **decimal strings**, unlike transactions):

| `request_type` | Extra fields |
|---|---|
| `flash_card` | `payment_lifespan_limit` ("250.00"), `pre_expires_at`, `currency` |
| `virtual_card` | `payment_monthly_limit`, `currency`, `card_level` (`virtual` \| `virtual_partner`), `card_design` |
| `transfer` | `creditor_name` (no IBAN in the list shape), `reference`, `amount`, `currency`, `scheduled_date`, `recurrence` (e.g. `monthly`), `last_recurrence_date?`, `attachment_ids[]` |
| `multi_transfer` | `total_transfers_amount` (+`_currency`), `total_transfers_count`, `scheduled_date` — no per-beneficiary detail in the list shape |

### Approval semantics (upstream)

- Approving without SCA enabled returns **428** `{code: "sca_required"}` — the user must have SCA active on their Qonto account.
- 422 business failures include `insufficient_funds` and `kyc_not_accepted`.
- Optional `debit_iban` on approve selects the account to debit (transfers) or link (cards); defaults to the main account.
- Approving transitions `pending` → `approved` and returns the full request object.

## Subscription & pricing — `get_subscription`, `get_qonto_public_pricing`

The org's own Qonto plan — check it before using plan-gated features:

```jsonc
{
  "plan": {
    "code": "solo_basic_2024",
    "lineup": "solo",                    // solo | teams (larger orgs)
    "name": "Basic",
    "monthly_price": {"amount": "11.00", "currency": "EUR"},   // ⚠️ key is `amount`, not `value`
    "recurrence": "monthly",
    "status": "active",
    "trial_ends_at": null
  }
}
```

`get_qonto_public_pricing(plan?, include_addons?)` returns `{fetched_at, markdown, source}` — a **markdown snapshot of qonto.com/pricing** (plan names, prices, features, addons), not structured data. Plans: Basic, Smart, Premium (solo lineup); Essential, Business, Enterprise (teams lineup). Use it for "what plan has feature X", not for programmatic price math.
