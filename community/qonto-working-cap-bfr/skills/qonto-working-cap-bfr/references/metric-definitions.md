# Metric definitions

Every metric is reported with: value, period, method, and whether it is **measured** (from invoices or bank data) or **estimated** (from stated terms or assumptions).

## Invoice-based payment metrics (always compute when paid invoices exist)

Compute these from invoices whenever there are paid invoices, whatever the data mode. Coverage only changes how they are labelled: "measured on N invoices, covering X% of client receipts".

Sources:
- Clients: `list_client_invoices` with `filter_status: ["paid"]` and `exclude_imported: false`. Use `issue_date`, `due_date`, `paid_at` and `total_amount`. Deposit, partial and balance invoices (`invoice_type`) all count. Net credit notes.
- Suppliers: `list_supplier_invoices` with `filter_status: paid` and `filter_exclude_credit_notes: true`. Use `issue_date`, `due_date`, `payment_date`, `total_amount`, and `matched_transactions` when present.

Payment date: use the date of the matching bank transaction (same counterparty, amount within 1%, on or after the issue date; or `matched_transactions`). Fall back to `paid_at` / `payment_date` only when there is no match. An invoice marked paid with no matching debit or credit on any Qonto account is listed separately ("marked paid, no matching transaction"): it may have been paid from another bank, or marked paid by mistake. Exclude it from the measured averages.

Per invoice:
- `days to pay = payment date - issue date`
- `terms = due date - issue date`
- `days late = payment date - due date` (negative means early)

Report, weighted by invoice amount, for all clients, all suppliers, and each counterparty:
- **DSO (measured)**: average days to pay on client invoices. Also give the median.
- **DPO (measured)**: average days to pay on supplier invoices.
- Average terms granted (clients) and received (suppliers), and their **trend by issue month**. Lengthening supplier terms or shortening client terms is a lever; say so.
- Average days early or late, share paid on time, number and maximum of late payments.
- **Paying early**: if the business pays suppliers before the due date on average, the cash it could keep is `average days early x average daily supplier spend`.

Open items (unpaid client and supplier invoices):
- Ageing buckets from today: not yet due, 1 to 30, 31 to 60, over 60 days overdue.
- Overdue client invoices are forecast at today plus that client's average days late (or 30 days if unknown), never on their original due date.

Balance method, as a cross-check only: `open receivables / client receipts over the last 90 days x 90`. It is low when clients pay quickly, even if the real problem is unbilled work.

## When invoices are missing

- **Mode B, estimated from stated terms**: weighted average of the terms the owner gave for each main client, weighted by that client's share of receipts. Label it "estimated from the payment terms you told me". Do not claim clients pay late or on time: bank data alone cannot show it.
- If the owner declared outstanding invoices, report them as "declared outstanding", not as measured receivables.
- Mode C: measured on the covered side, estimated on the other. Never mix the two into one figure.

## Receivables/payables cycle

`DSO - DPO`. Inventory days are not available from Qonto data: do not invent them, and do not call the result a full cash conversion cycle. A positive cycle means the business funds its clients; negative means suppliers fund the business.

## Collection-pattern metrics (all modes, especially mode B)

- Monthly client receipts and their volatility (coefficient of variation).
- Share of receipts from the top 1, 3, 5 clients, and trend.
- Number of active paying clients per month.
- Typical gap between receipts from recurring clients.
- Day-of-month profile of receipts vs fixed outflows (shows timing mismatches).

## Concentration

Top 1 / 3 / 5 share of client receipts and of supplier spend. A single client above 30% of receipts, or a supplier above 40% of spend, is worth flagging. Concentration is a risk indicator, not a credit judgement.

## Fixed-cost base

Monthly average of payroll, social charges, rent, utilities, subscriptions, insurance and loan repayments over the last 3 to 6 months. Used for the default minimum cash buffer (one month of fixed costs).

## Runway

- Preferred: forecast date when cash falls below the minimum buffer, and date it would turn negative.
- Only if no forecast is possible and burn is stable: `available cash / average monthly net outflow`, labelled as a rough estimate.

## Available liquidity

`cash + unused overdraft limit + remaining Pay Later limit`. Show cash and headroom separately. Limits come from the owner, as the MCP does not expose them.

## Flex card float

`average monthly card spend x average days between purchase and settlement / 30`.

## Financing need

Compute on the **Layer 1** forecast (without any financing): `required amount = buffer - lowest projected cash`, if positive, for base and downside cases. Duration = time spent below the buffer. Then compute the residual gap after the active products (Layer 2), and after the optimised mix (Layer 3).
