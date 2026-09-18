# Payment reminder templates

Adapt tone to lateness. Always personalize the client name, invoice number,
amount, due date, and days overdue. Draft in the client's locale. The user
sends the reminder; never send autonomously. The examples below are in English.

## Friendly reminder: 1 to 14 days overdue

> Subject: Invoice {number}: gentle reminder
>
> Hi {name}, just a quick note: invoice {number} for €{amount} was due on
> {due_date} and appears unpaid. You can settle it here: {payment_link}.
> If payment is already on its way, please disregard this message.
> Best, {user_name}

## Firm reminder: 15 to 30 days overdue

> Subject: Invoice {number}: payment overdue
>
> Hi {name},
>
> Despite our previous reminder, invoice {number} for €{amount}, due on
> {due_date}, remains unpaid and is now {days_late} days overdue.
>
> Under our payment terms, late-payment interest at {penalty_rate} and the
> statutory €40 recovery fee apply. Please settle the invoice within eight
> days: {payment_link}
>
> Best regards,
> {user_name}

## Formal notice: more than 30 days overdue

> Subject: Formal notice: invoice {number}
>
> {name},
>
> Despite our reminders dated {reminder_dates}, invoice {number} for
> €{amount}, due on {due_date}, remains unpaid.
>
> This is formal notice to pay €{amount}, plus €{penalties} in late-payment
> interest and the statutory €40 recovery fee, within eight days of receipt.
>
> Failing payment, we reserve the right to begin recovery proceedings without
> further notice.
>
> {user_name}

## Escalation guidance

- `{penalty_rate}` is the invoice's contractual late-payment rate (read it
  from the invoice terms, or ask the user). Never paste a hardcoded semester
  figure — the reference rate changes.
- Always compute `{penalties}` with the deterministic validator:
  `python3 scripts/validate_fr.py penalty <amount_ttc> <days_late> <annual_rate_percent>`,
  and show the calculation to the user.
- A formal notice should be sent by registered mail with proof of delivery;
  remind the user that the email draft is only a courtesy copy.
- If a client disputes the invoice, stop the escalation and flag for human
  resolution.
