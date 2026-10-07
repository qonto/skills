# Stage A: scope

Steps 1 to 6. Pass `workspace_id` on every `well_*` call once step 1 has pinned it. The Well app address used below is `https://app.wellapp.ai`.

## 1. Pin the workspace

Call `well_list_workspaces()`.

- Auth error → the Well server is not signed in yet. Tell the user to sign in (in Claude Code: run `/mcp`, pick the Well server, sign in), then retry once they say they did.
- `success: false` with a non-auth error → retry once; on a second failure, do not invent a workspace. Say so and give `https://app.wellapp.ai` to open Well directly.
- Zero workspaces → the account has no workspace yet. Say so, point the user to Well to finish signing up, and stop.
- `session.pinned_workspace_id` set, and THIS conversation established it (its own picker click or typed choice earlier), and the user is not asking to switch → use it. A pin this conversation never made is another conversation's leftover: ignore it, never mention it, and resolve as if unset.

Resolve without asking when you can:

- **Exactly one workspace** → use it. Say which one in one line; do not ask and do not call `well_switch_workspace`.
- **Several workspaces and a hint** (a `workspace_id`, a name, or the company behind it, including the Qonto organization name from step 0) → match exactly on `workspace_id`; otherwise case-insensitively on `workspace_name`, `identity.registered_name`, `identity.trade_name`, or, for a country hint, on `identity.country`. Exactly one match → use it, say which one, and lock it with `well_switch_workspace({ workspace_id })`. Zero or several matches → the picker below; never pick the closest name.
- **A hint naming several entities** ("FR and US") → run the pack once per entity, one after the other, each with its own pages. Nothing is merged across two entities: no shared row, no combined total.

**Several workspaces and no usable hint** → call `well_show_workspace_picker({ reply })`. Write `reply` as the sentence the click sends in the user's name, in their language, with `{picked}` where the workspace name belongs. Write your one line for the user first, then call `well_wait_for_selection({ kind: "workspace", timeout_s: 60 })`:

- `selected` or `already_set` → the click already pinned it. Say one short line naming the workspace, then continue on `selection.workspace_id` with no `well_switch_workspace` call.
- `no_selection_yet` → call it again at once, at most five calls in one turn. After the fifth, end the turn on one line asking the user to pick on the card.

In a host that draws no card, list each workspace on one line (name, country, base currency) and ask which one, then end the turn. Never default to the primary workspace on the user's behalf.

When the user answers in their own words, map the name to its `workspace_id` from the earlier result, never a guessed id, and call `well_switch_workspace`. A decline ("not now") → say nothing was pinned and stop.

**A demo workspace** (`kind: "demo"` on its row) holds sample data. Say so in one line, and that the figures are not the user's. Offer to run on their own workspace instead.

Keep for later steps: `workspace_id`, `workspace_name`, `identity` (registered and trade name, country, base currency), and `has_bank_transactions` (`true` only when a connector the workspace banks with has already delivered a transaction; `null` when it could not be read, never a zero).

## 2. Confirm the base currency

Take `identity.base_currency` from step 1 when it is there. Otherwise read `well_get_schema({ root: "workspaces" })` once, then one `well_query_records` on `workspaces` for this workspace's settings.

Ask for `base_currency` alone. A field the figures never read is not a gate.

Present → carry on. Absent → stop. Say which field is missing and what it decides ("so every page of the pack is measured in one currency"), and point the user at `https://app.wellapp.ai/workspaces/<workspace_id>` to set it. Never infer it from the country or the currency the rows carry.

## 3. Confirm the connections

Read coverage with `well_get_connector_coverage({ workspace_id })`. It draws nothing.

For each kind, `bank` (required), `invoicing` and `accounting`, keep only rows whose `direction` is `input` and whose `data_domains` contains that kind. Never match on a display name.

Read each row's state, first match wins:

1. `to_configure` or `disabled`, or no connection at all (`connection_status: null` with `is_connected: false`) → **missing**.
2. `need_reconnect` or `error` → **error**. Send the user to `https://app.wellapp.ai` to reconnect there; do not pass through `install_url` from the connector response.
3. `enabled` with `last_successful_sync_at` set → **connected** ("data may be partial" if `sync_in_progress: true`).
4. Otherwise → **connecting**.

One **connected** row makes the kind connected; name any **error** row of the same kind beside it. Only **connecting** rows → connecting. Only **error** rows → error. No row → missing.

**Qonto.** Among the bank rows, look for the Qonto connector. Not there, or missing or in error → say that Well's figures do not yet include the Qonto accounts, and treat the bank as missing for the card below, so the user can connect Qonto before any page is measured.

**The bank missing** → draw the connect card with `well_list_connectors({ workspace_id, kind: "bank" })`. Exception: when step 1 handed `has_bank_transactions: true`, draw no card; say the coverage read disagrees with the workspace's own history and offer Re-check. Connecting happens in the card, through the provider's own sign-in, on the user's click. Write one line first ("to assemble your board numbers"), then call `well_wait_for_selection({ kind: "bank_ack", timeout_s: 60 })`, at most five calls. On `selected`, say one short line, re-read coverage once with `well_get_connector_coverage`, and carry on. A bank still not connected or connecting after that → stop. Neither the cash side nor the burn side can be measured.

**Invoicing missing or in error** → carry on with the three bank-side pages, and record that the two revenue pages have no source. Say it once, in the coverage line.

A kind the user chose to skip is not asked again in this run. On a failed coverage read, retry once; on a second failure, say coverage is unknown and stop.

## 4. Resolve your own company

Read the stored anchor with `well_get_own_company()`. `anchor: null` means none is set. Treat all three as unresolved: a null anchor, a failed read, or more than one plausible company. Never infer it from the workspace's name, logo, slug or email domain.

**Resolved** → one unambiguous company. Say which in one line and carry on.

**Unresolved** → ask once. One `well_query_records` on `companies` for the workspace, id and name fields only, and ask which one is theirs, with the list on screen. Say why: "to tell your own accounts and your own invoices from a counterparty's", and what a wrong pick breaks: "it counts a counterparty's balance as your cash and turns what you owe into what you are owed".

- The user confirms one → use it **for this run only**. To set it permanently, point them at `https://app.wellapp.ai/workspaces/<workspace_id>`. This skill does not write it.
- The user declines → say plainly that no page can be measured until it is set, and stop.

**Duplicate company records.** One legal entity often has several rows differing only by a legal-form prefix or suffix, punctuation or accents. Normalize both names the same way (Unicode NFD, strip combining marks, lowercase, punctuation to spaces, collapse whitespace, trim), and treat a pair as a candidate when either normalized name contains the other, tested both ways. Propose the candidates and take an explicit yes before treating them as one identity. Never merge silently, and change no company record.

Keep for later steps: the own company id and name, and the confirmed alias ids (the identity set).

## 5. Settle the window, and ask nobody

The window ends with the **last complete month**, and it is that many months long: the number the user named, or 3.

- **Write it as the sums take it: the first of the first month, to the first of the month AFTER the last.** Inclusive start, exclusive end. Every sum and render call below reads that pair.
- **A month that has not ended is never the anchor.** A run on 16 September anchors on August.
- **A named past month does not move it.** The cash page reads as of now, so a past window would pair today's balance with a rate that stopped months ago. Offer a wider window, never a shifted one.

## 6. A named month moves no page

When the user named a month, say in one line that the figures read over the window from step 5 instead. Draw no month card: a pick would move nothing the reader is looking at.
