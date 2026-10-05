# Stages C and D: whose accounts, and the three policies

Steps 10 to 15. Steps 10 and 12 are the only steps where data can change, and only through the card, on the user's click.

## Stage C: whose accounts

### 10. Attach every account to a company you own

**Ask whether the gate is open before you read the worklist.** One `well_get_worklist_status({ workspace_id, worklist: "accounts_needing_company" })`. It draws nothing; the worklist read below draws its card on every call, the empty one included.

- `success: false` → the gate is unknown, not clear. Retry once; on a second failure stop and say the account links could not be read.
- `open: false` → carry on. Nothing is drawn and nothing is said about it.
- `open: true` → read the worklist.

One `well_list_accounts_needing_company({ workspace_id })`. It returns only the accounts that fail, for one of two reasons, which are one decision (whose account is this):

- No company attached. Nothing can place the account on either side of a transfer.
- `ownership: "unknown"`. The account has a company, and whether the workspace owns it is unanswered.

Check `success` before `records`: a failed read is unknown, never "every account is attached".

Any account on the list → **stop on the assignment card**. The read draws it. Say what it decides: "so an account you own can be told from a counterparty's, in the balances and in the transfer rule at once".

**The user confirms the write here.** The user picks the company for each account on the card and clicks it; the card writes it through `well_assign_account`. You never call `well_assign_account` yourself, you never infer an owner from the account's name, its bank, or the company most often beside it, and a `company_suggestion` on a row is the user's to accept, never yours to apply. In a host that draws no card, list the accounts, say the pack cannot be measured until each is attached, point at `https://app.wellapp.ai/workspaces/<workspace_id>`, and stop.

**Resuming.** The card's Continue names this step: re-run the probe alone, not the worklist, and continue from here.

This gate serves three pages at once: an unclaimed account contributes nothing to the cash and cannot be placed inside or outside the internal-transfer rule, so it shrinks the cash, distorts the burn and moves the runway in the same run.

## Stage D: the three policies

The three policy cards below (steps 11, 14 and 15) are the only questions the pack asks. Draw them one at a time, in order, and take each answer before drawing the next. Each answer is used by every page that reads it, so no policy is asked twice. A click on a policy card records the answer for this run; it changes no record.

### 11. Confirm what counts as cash

Ownership is already settled by the anchor rule. Do not offer it here and do not describe this step as excluding it.

This is the reader's own decision: which kinds of account are cash for their business. A credit card and a loan are liabilities; a brokerage account may or may not be money they can spend this month. **The exclusion is keyed on the account type, and only on it.** A reader who wants one particular account left out is asking for something this step cannot express: say so.

Call `well_list_cash_scope({ workspace_id })` once. It draws the card, with what each type holds, per currency, never blended. Write one line, then wait on the card as its `next_step` says.

- Empty `groups` with `partial: true` → the read was cut short. Say so and offer to try again.
- Empty `groups` otherwise → the workspace holds no type to scope. Say so and carry on.
- `unsettled_ownership` above zero → stop. Those accounts are in no type, so no choice here reaches them. Send the reader back to step 10.
- Take no default beyond the card's own: deposits start counted, nothing contested does.
- **Counting nothing is an answer.** Say there is no cash position to report, rather than zero, and end the run there.

Keep: the counted account types, the types offered and what each held.

### 12. Categorize the window

**Ask whether the gate is open first.** One `well_get_worklist_status({ workspace_id, worklist: "uncategorized_window", from, to })` with the window's bounds.

- `success: false` → unknown. Retry once; on a second failure stop and say categorization coverage could not be read.
- `open: false` → carry on, nothing drawn.
- `open: true` → read the worklist.

One `well_list_uncategorized_window({ workspace_id, from, to })`, `from` inclusive, `to` exclusive. It returns only the rows with no category.

Any → **stop on the categorize card**. The read draws it. Say how many rows and how much of the window's value sit behind them, and what it unlocks: "so the categories you exempt can actually be applied, and so the burn rests on the categories the window carries". `truncated: true` means the count is a floor: say "at least".

**The user confirms the write here.** The user validates or changes the categories on the card; the card writes them through `well_set_transaction_category`. You never call `well_set_transaction_category` yourself, you do not offer to categorize, and you propose no label in the chat. In a host that draws no card, say how many rows are uncategorized, point at `https://app.wellapp.ai/workspaces/<workspace_id>`, and stop.

**Resuming.** The card's Continue names this step: re-run the probe alone. A reader who fixed some rows comes back to a smaller number, which is progress.

### 13. Elect the sign convention

Which sign means money leaving is a property of the feed. Measure it, never assume it.

Run `well_sum_transactions({ workspace_id, from, to, axes: ["month", "currency"], scope: "own_and_adopted", exclude_internal_transfers: true })` over the window, and read `count_negative` and `count_positive` over the whole window, not per month.

- Negatives are a substantial share of the rows → the feed is **signed**. The outflow is `sum_negative` as returned. It is already a positive magnitude: never negate it.
- Almost no negatives, positives throughout → the feed records **magnitude only**, and the sum cannot separate direction. Stop, and say the burn cannot be computed from this feed as things stand.
- `partial: true` → the sum measured nothing. Stop and say so; offer to try again.
- Neither shape is clear → say so and stop. A convention elected from ambiguous evidence produces a confident figure that may be inverted.

State the convention elected and the counts behind it.

### 14. Confirm the exemptions

Internal transfers are already out by the leg rule. Do not offer them here.

This is the reader's own decision: what is not burn for their business (loan principal, an intra-group recharge, something they treat as investment). **The exclusion is keyed on the category, and only on it.** A type no category isolates cannot be excluded: say so.

One `well_list_burn_exemptions({ workspace_id, from, to, convention })`. It draws the card, grouping the window's outflow by category with what exempting each would remove. Do not build this list with `well_sum_transactions`. Read `success` before `groups`. Write one line, then wait on the card.

- Empty `groups` on a successful read → nothing to exempt. Say so and carry on; the card asks for no click.
- `unclassified_amount` above zero → outflow no exemption can touch; say `total` is not the whole window.
- `partial: true` → the list is empty because the sum measured nothing. Say so.
- The card pre-ticks `TREASURY_PLACEMENT_OUT` and `TREASURY_REDEMPTION_IN` when they carry outflow in the window. Add no exemption of your own.
- A `success: false` naming its cause (more than one currency, rows disagreeing on direction) is a refusal: show the message as it stands, do not retry.
- **Exempting everything is an answer.** Say the burn has nothing left to measure, rather than zero.

Keep: the exempted category keys.

### 15. Confirm which contexts are recurring

Skip this step and the recurring revenue page when step 3 found no invoicing source.

Purchase invoices are already out by the party scope. Do not offer them.

This is the reader's own decision: which billing is recurring for their business. **The selection is keyed on the billing context, and only on it.**

One `well_list_recurring_contexts({ workspace_id, from, to })` from the **start of the earlier comparison window** (the same number of months, ending where this window starts) to the end of this window, so a context that stopped billing is still offered. It draws the card with each context's amount per currency, never converted. Do not build this list with `well_sum_invoices`. Read `success` before `groups`. Write one line, then wait with `well_wait_for_selection({ kind: "recurring_contexts", timeout_s: 60 })`.

- Empty `groups` on a successful read → no issued revenue to classify; the card asks for no click. Skip the recurring revenue page.
- **The "No billing context" row is usually the largest, and it is a real choice.** State its amount whether it is counted or not. Its key is `unclassified`, which stands for the invoices whose `billing_context` is `null`.
- `partial: true` → every amount is a floor. Say so.
- Take no default. Nothing is recurring until the reader says so.
- An empty selection on `selected` is an answer: the recurring revenue page has nothing to measure. Say so rather than reporting zero.

Keep: the recurring context keys, and the amount and count of the no-billing-context row.
