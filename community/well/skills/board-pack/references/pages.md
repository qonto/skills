# Stage E: the pages

Steps 16 to 21. Every figure below is computed from what a Well tool returned, by the arithmetic stated here, and every page goes to its render card.

## Currency conversion (used by every page)

The target currency is the workspace's `base_currency` from step 2.

- **One currency, equal to the target** → no rate lookup.
- **Otherwise**, read `well_get_schema({ root: "exchange_rates" })` once, then look up each non-target currency's rate as of the relevant date (today for cash, each month's own end for a monthly series). Use the exact-date rate, or else the most recent one at or before that date, and record the date. Never a rate dated after it. Check the pair's direction in the schema before dividing rather than multiplying.
- **Convert each row or subtotal, then add.** Adding native amounts first is how a figure ends up denominated in nothing.
- **A currency with no rate** is left out of the converted total, kept in the per-currency breakdown, named, and the total is marked partial. A currency value that is not an ISO code is not a currency: exclude it and count it.
- Every converted figure carries its rate and rate date.

## 16. The pack's header

State the window every rate page covers (step 5), the as-of moment the cash page reads (step 9), and the currency every figure is stated in (step 2). Say once that the pack read no close verdict for the window's months. Draw no month card.

## 17. Page one, cash

Take step 9's `well_list_account_balances` result and do not read it again.

1. **Fold second copies.** A row naming `duplicate_of_account_id` is an account arriving a second time through another connector. Leave it out of everything; the named account's balance is the one that counts. Say how many were folded.
2. **Settle membership** with `own_company_id` from the same response. An account is the business's own when its `ownership` is `workspace` and it names no company, or no own company is set, or it names the anchor; or when its `ownership` is `unknown` and its `company_id` equals the anchor. A `workspace` row naming another company is a stale tag, not owned cash. Everything else is a counterparty's and leaves the figure. With a null anchor, `unknown` accounts are neither counted nor dropped: count them and disclose them.
3. **Apply the scope** from step 11: keep only the counted account types. Report what each excluded group removed.
4. **Take each amount**: `closing_booked`, otherwise `opening_booked`, never `closing_value` (it includes payments not yet settled). No readable balance → the account leaves the figure and is counted. `verification_rejected` is its own group.
5. **Convert, then sum**, per account.
6. **The series.** Total each month's `month_ends` under the same scope and ownership rule, converted at that month's own rate. A month no account covered is a gap, never a zero.
7. **Bound the answer.** The total may be a floor when a counted account had no readable balance or no rate. Say which, with the count, and say "may be". Disclose `unsettled_ownership` beside the total.

A negative total is a real reading: report it, never floor it at zero.

Keep the exclusion groups apart: `not_owned`, `out_of_scope_type`, `no_readable_balance`, `no_fx_rate`.

Then call `well_render_cash_position` with the amount, the currency, the as-of moment, the counted accounts, the scope, the exclusion groups, the month-end series as `balance_history`, and `partial` when the total is a floor.

**Then cross-check against Qonto** (see `SKILL.md`, Stage E).

## 18. Page two, burn

The window, the sign convention (step 13) and the exemptions (step 14) are settled.

**Sum, then divide by the window length.** Call `well_sum_transactions({ workspace_id, from, to, axes: ["month", "currency"], scope: "own_and_adopted", exclude_internal_transfers: true, exempt_categories: [...] })`. The scope is always named explicitly: it has no default. Take the outflow subtotal the convention elected, as returned. Convert each month-currency subtotal, add within each month, then divide by the number of months **in** the window, not the number that carried spend.

- Keep the per-month series; a month with no outflow rides in it as a zero.
- **The earlier window.** A second `well_sum_transactions` over the same number of months ending where this window starts, under the same exemptions, convention and conversion. The two windows share no month (Jun to Aug compares against Mar to May). Compute `change` as the signed percentage. Skip the comparison when the earlier window has no data, is cut short, or averages zero.
- `partial: true` → the sum measured nothing. Stop and say so.
- `excluded_zero_leg`, `excluded_multi_leg`, `excluded_no_owned_leg` as `null` mean unmeasured, never zero.
- **`excluded_no_owned_leg` bounds the figure.** Rows with no leg on an account you own are dropped, so the burn may read low. Take the count from this window's sum, never from the baseline's.

Then call `well_render_burn` with the average, the currency, the window, both month counts, the convention and its counts, the transaction count from step 8, the unplaceable count, the per-month series, the exclusion groups, and the baseline and change when measured.

## 19. Page three, runway

The cash from step 17 divided by the burn from step 18, both in the base currency. If not, stop rather than divide.

- **Cash at or below zero** → `0` months, status `ok`. This outranks every branch below.
- **Burn of zero, cash positive** → status `infinite`: report cash-flow positive, never a number.
- **A quotient above 36** → status `capped`, reported as more than 36 months.
- **Anything else** → status `ok`, one decimal, stated as "X months and Y days" where the days are the remainder times 30.44.
- **Either figure unmeasurable** → status `insufficient_data`, `months: 0`, the missing half sent as `null`. The zero is a placeholder, never "no runway left".

Then call `well_render_runway` with the months, the status, the cash, the burn with its window, the as-of moment, the window from step 5 when a burn is sent, and `partial` when the cash is a floor. A refusal names a fault in this run's arithmetic: fix it, do not retry blindly.

## 20. Page four, recurring revenue

Skip this page when step 15 was skipped or nothing was counted as recurring, and name it as not measured.

**Sum, keep the confirmed contexts, divide by the window length.** Call `well_sum_invoices({ workspace_id, from, to, party_scope: "sales" })`. Keep only the rows whose `billing_context` the reader confirmed (the `unclassified` key means the rows whose `billing_context` is `null`). Convert each month-currency subtotal once, add within each month, divide by the number of months in the window. Amounts are net of tax.

- **Credit notes are already netted**; `credit_note_sum` says what that removed. Do not subtract them again, and do report them.
- **A month is when an invoice was issued, not what it covers.** When the window is shorter than the billing cycles the confirmed contexts imply, say so: an annual retainer in a three-month window is a spike, not a run rate. Never infer a cycle from an invoice's `terms` text.
- Keep the per-month series, zeros included.
- **The earlier window**, measured the same way under the same contexts, adjacent and sharing no month. Skip it when it cannot be measured.
- `partial: true` → every figure is a floor; say so.
- `unattributed_count` and `excluded_malformed` as `null` mean unmeasured.
- **A negative average is a finding.** Report it with both halves, never its magnitude.

Then call `well_render_mrr` with the average, the currency, the window, both month counts, the confirmed contexts, the invoice count, the unattributed and unclassified counts, the per-month series, the exclusion groups (`one_off`, `credit_notes`, `unreadable_rows`), and the baseline and change when measured.

## 21. Page five, what is owed on each side

Skip this page when step 3 found no invoicing source.

**This page reads as of now, like the cash page.** What is owed is a balance, so it has no window and no divisor. An invoice issued and paid inside the window is owed by nobody, and an unpaid one issued before the window is still owed.

**Never take an owed figure from `well_sum_invoices`.** It sums what was billed over a window, paid or not, so paid invoices would count as owed. It serves step 20 alone.

### Owed to you

One `well_sum_receivables({ workspace_id })`, with no `customer_ids`. Well applies one fixed rule on the server and echoes it in `rule`:

- the workspace is the issuer and the customer the receiver;
- the document is a billing document (never a proforma, a quote, an order or a credit note);
- it is not a draft and not canceled;
- its payment status is `unpaid` or `partial`;
- its `balance_due` is above zero.

The amount is `balance_due`, never the invoiced total: a paid invoice is not in the figure, and a part-paid invoice counts for what is left.

- **Report each currency row as returned**: `outstanding_count`, `outstanding_total`, and the `overdue_count` and `overdue_total` part past its due date. Convert each currency's total at today's rate under the rules above, then add. The aging bands are not part of this page.
- **Give `as_of` beside the figure.**
- **State what the figure left out, each on its own line, even at zero**: `marked_paid_count` and `marked_paid_total` (a connector says settled, no bank payment matched yet), `draft_count` and `draft_total`, `unsettled_credit_note_count` and `unsettled_credit_note_total`. None of them is in the total, and none is subtracted from it.
- **State the counts beside the total**: `unknown_payment_status_count`, `unattributed_count`, `no_currency_count`, `no_balance_count`. A `null` count means unmeasured, never zero.
- `partial: true` → every figure is a floor; say so. `success: false` → the page is not measured; the empty `currencies` is not a zero.
- Never add up rows to reach or adjust this total.

Then put the rows behind it on screen: read `well_get_schema({ root: "invoices" })` once and take the payment-status, lifecycle-status and due-date fields from it, never a guessed name. One `well_show_records` on `invoices` with `partyScope: "sales"`, payment status `unpaid` or `partial`, lifecycle status neither `draft` nor `canceled`, oldest due date first.

### Owed by you

**Well has no server-side sum of the outstanding balance on the purchase side.** So this side is a count and the rows, and it states no total.

- One `well_show_records` on `invoices` with `partyScope: "purchase"`, payment status `unpaid` or `partial`, lifecycle status neither `draft` nor `canceled`, oldest due date first, using the same schema fields.
- Report its `totalCount` as the number of supplier invoices still unpaid or partly paid. `totalCount` counts every match, not the page on screen. A non-null `nextCursor` is not work left to do.
- Say in one line that the total owed by you is not measured, and why: no outstanding sum exists for supplier invoices.
- Never build that total: not by adding `balance_due` across rows, not by paging, and not from `well_sum_invoices`.
- A failed read → this side is not measured. Say so; never report a zero.

### Both sides

- `unattributed_count` from `well_sum_receivables` is the number of outstanding-looking invoices Well could place on neither side. Report it once, beside the two sides: those invoices may be owed either way and are in no figure.
- Never filter a counterparty by name to build a figure.
