# Qonto financing products: status check and working-capital modelling

Covers the three short-term products that directly change working capital: **Overdraft**, **Pay Later**, and the **Flex card** (deferred debit). Run the status check in workflow Step 4, before categorisation, because each product changes how transactions are read and how the forecast is built.

## 1. Status check

The MCP exposes no eligibility endpoint. Status is determined from data signals, then confirmed with the owner. Each product ends up in one of four statuses:

| Status | Meaning | How it enters the analysis |
|---|---|---|
| **Active** | Product in use or contracted | Part of the **base case**: headroom counts as available liquidity, repayments are in the forecast |
| **Eligible, not active** | Owner sees the offer in the app | **Optimisation scenario**: "if you activate X" |
| **Unknown** | No signal, owner does not know | **Conditional scenario**, clearly labelled "subject to eligibility" |
| **Not available** | Not offered in the customer's country or plan, or owner says not eligible | Not mentioned |

### Overdraft

Data signals of activity:
- Negative `balance` or `authorized_balance` on any account, or negative `settled_balance` anywhere in the transaction history.
- Overdraft interest or fee debits: labels or references containing "découvert", "agios", "overdraft", "Überziehung", "Dispo", "scoperto", "descubierto", "rood staan", or a `qonto_fee` that recurs after negative-balance periods.

What the MCP does not show: the authorised limit and the rate. Ask the owner for the limit.

### Pay Later

Data signals of activity:
Pay Later leaves three kinds of transactions on the account. Match them on `label` and `reference` (filter locally, never with an `operation_type` filter, which has triggered 503 errors):

| Leg | How it appears | Class |
|---|---|---|
| Disbursement | `operation_type: income`, label "Qonto Pay Later", reference such as "Financement Pay Later", usually categorised as bank loan proceeds | Loan proceeds (Pay Later) |
| Supplier payment | `operation_type: transfer` to the supplier on the same day as the disbursement, reference "Achat Pay Later - <supplier>" | Suppliers (the real cost) |
| Instalment | `operation_type: direct_debit`, label "Qonto Pay Later", reference "Echeance Pay Later (capital + interets)" or similar | Loan and financing repayments |

Rebuild each plan:
- Pair every disbursement with the instalments that follow it. Equal instalments at monthly intervals give the instalment count and the total cost (sum of instalments minus disbursement).
- A disbursement with no matching supplier payment, or with fewer instalments than its plan implies, is an open question for the owner, not a finished plan.
- A plan whose last expected instalment is missing from the history stays in the forecast as still due.
- Do not rely on `list_supplier_invoices` with `filter_source: pay_later`: it can return nothing even when Pay Later is used.

What the MCP does not show: the remaining limit, and the schedule of a plan with no instalment yet. Ask the owner. Until they answer, assume the instalment count most used in the customer's past plans, and label it as an assumption.

### Flex card (deferred debit)

Data signals of activity:
- `list_cards` with `statuses: ["live"]`: any card with `card_type: "flex"` means a Flex card exists.
- A monthly settlement debit: `operation_type: financing_installment`, label "Qonto", with a `deferred_debit_card_repayment` block. That block gives the settled `capital_amount`, `accumulated_fees_amount`, the period start and end, and `total_transactions_count`. Use it, not the label, to identify the settlement and to check it against the card purchases of the period.
- Settlement days (usually the 1st of the month) are where `list_transactions` errors have clustered. If those days cannot be loaded, say so and rebuild the missing settlements from the card purchases of the previous period.

`card_type: "flex"` is the confirmed signal for the deferred debit card. What the MCP does not show is whether deferred mode is switched on, and the monthly settlement date, so ask the owner.

### Availability

Call `get_qonto_public_pricing` with `include_addons: true` and `get_subscription`. If the public page does not list a product for the organisation's country or plan, mark it **Not available**. Take rates and instalment options only from this output, never from memory.

### Owner question

Add a single question to the categorisation batch, only for products not already confirmed active by data:

> To include Qonto's financing options in your cash plan: in the Financing section of your Qonto app, do you see Overdraft, Pay Later or a Flex card offer? If yes, what limit is shown? If you already use them, what is your current limit?

If the owner skips the question, the products stay **Unknown**.

## 2. Effects on categorisation (avoid double counting)

- **Flex card**: individual card payments already appear as transactions. The monthly settlement debit is **not** an extra cost; classify it as an internal financing movement and exclude it from opex. For cash timing, model card spend at the settlement date, not at the purchase date.
- **Pay Later**: the disbursement lands on the account and the customer pays the supplier from it, so both legs are visible. The supplier payment is the cost (count it once, for cost and DPO). The disbursement is a financing inflow, never revenue. The instalments are debt service in the forecast. Keep the link between plan and supplier.
- **Overdraft**: interest and fees are Bank fees. Negative balance periods are not cash inflows.

## 3. Modelling

Run the forecast in three layers. Show them side by side to the owner.

**Layer 1. Without any financing.** The raw cash profile, which reveals the true working-capital gap.

**Layer 2. With active products (base case).**
- Available liquidity = cash + unused overdraft limit + remaining Pay Later limit (shown as headroom, not as cash).
- Forecast includes the remaining Pay Later instalments and the next Flex settlements.
- Runway and minimum cash are measured against the buffer, counting the overdraft headroom as liquidity. Also show "lowest cash before overdraft", so the owner sees how much of the overdraft is used.

**Layer 3. Optimised (active plus eligible or unknown products).** For each product not yet active, simulate its effect on the 13-week forecast:

| Product | Simulation | Benefit metric | Cost |
|---|---|---|---|
| Overdraft | Cover forecast troughs up to the limit, repay as soon as inflows allow | Trough covered, days in overdraft | Rate x amount x days, from public pricing |
| Pay Later | Select supplier invoices due in or just before the trough week. Pay them with Pay Later; spread them into instalments. Test each instalment option the public pricing lists | Increase in minimum cash, new trough date | Total fees per option |
| Flex card | Move each month's card spend to the settlement date | Average float = monthly card spend x days deferred / 30; increase in minimum cash | Card or plan fee, from public pricing |

Selection rules:
- Pick the cheapest combination that brings the lowest projected cash back above the buffer in the base case. Then check the downside case.
- **Duration match**: choose the Pay Later instalment count whose duration best matches the receivables/payables cycle. Plans longer than the cycle cost more without solving more.
- Use the overdraft for short, recurring troughs. If the forecast stays in overdraft for most of the 13 weeks, flag a structural gap rather than recommend a larger overdraft.
- The Flex card is the lowest-effort lever when card spend is material. Card spend is material when it exceeds about 10% of monthly outflows.
- Operational levers still come first. Optimise what remains after invoicing unbilled work, chasing late clients, and aligning payment dates.
- Never stack products to fund a structural loss. If Layer 1 shows cash declining month after month, say so plainly.

## 4. Presenting to the owner

One table:

| | Without financing | With what you use today | Optimised |
|---|---:|---:|---:|
| Lowest cash (13 weeks) | | | |
| Date | | | |
| Weeks below buffer | | | |
| Estimated cost | 0 | | |

Then one sentence per suggested product: what it does for their cash, the amount, the duration and the cost.

Wording:
- Active product: "you already have X; it covers..."
- Eligible product: "you could activate X in your app, subject to Qonto's final review".
- Unknown product: "if X is available to you, it could...; you can check in the Financing section".
- Never say the business qualifies, and never give a credit decision.

## 5. Other products

AR Financing and longer-term financing only appear if the forecast shows a gap these three products cannot close, or a structural need. They are subject to the same availability check and the same wording rules.
