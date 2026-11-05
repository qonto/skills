---
name: weekly-payment-reconciliation
description: Reconciles your open client invoices against the payments that actually landed in your Qonto account. Books the unambiguous matches, attaches the invoice PDF as the receipt, hands back only the cases that genuinely need you, and prepares friendly payment reminders for anything long overdue. Built for a weekly run, works manually too. Triggers on "reconcile payments", "match invoices to payments", "who still owes us", "weekly payment check", "which invoices are still open", "chase unpaid invoices", "payment reconciliation".
permissions:
  mcp:
    qonto: [get_attachment, get_transaction, list_bank_accounts, list_client_invoices, list_transactions, mark_client_invoice_as_paid, request_attachment_upload, upload_attachment]
  network: [qonto.s3.eu-central-1.amazonaws.com]
  env: []
  tools: [Bash, Read, Write]
---

# Weekly payment reconciliation

## What this does

Once a week, this walks your open client invoices against the credits on your bank account and sorts every invoice into one of three buckets:

1. **Clearly paid** — the invoice gets marked paid and the invoice PDF is attached to the payment as its receipt.
2. **Something is off** — partial payment, double payment, overpayment, a credit nobody can place. These are reported to you with evidence, never touched.
3. **Clearly unpaid and long overdue** — a short, friendly reminder email is prepared as a draft for you to read and send.

## What this never does

- It never marks an invoice paid without an unambiguous match. Matching on amount alone is not enough, ever.
- It never sends an email to a customer. It only creates drafts.
- It never re-opens a case you have already decided on.

## The prime directive

Every statement this skill makes about a customer's payment behavior can end up in an email to that customer.

A missed finding costs a week. An invented finding costs credibility with a customer, and you only get to spend that once. So the bias is deliberate: **report one case too few rather than one case too many.** When in doubt, do not assert, report it as "uncertain, please check yourself".

This cuts both ways. "No payment received" is the same class of error as an invented double payment, just mirrored, and it leads directly to a dunning letter sent to someone who already paid. Negative findings get verified exactly as hard as positive ones.

---

## Before the first run: configuration

Fill this in once, then the weekly run needs no further input. Keep it at the top of the skill or in a note the skill reads.

```
REVENUE_ACCOUNT      = <bank_account_id of the account customer payments arrive on>
INVOICE_NUMBER_REGEX = <pattern of your invoice numbers, e.g. INV-[0-9]{4}-[0-9]{3}>
LOOKBACK_MONTHS      = 12
OVERDUE_THRESHOLD    = 30 days past due date
AUTO_BOOK            = false
SIGNATURE            = <name> / <role> / <company>
REMINDER_LANGUAGE    = en
```

**`REVENUE_ACCOUNT`** — call `list_bank_accounts` once and pick the account your customers actually pay into. If you have several, list them all and treat them as one pool; just make sure none is missing, because a missing account produces false "unpaid" findings.

**`INVOICE_NUMBER_REGEX`** — this is how payments get tied to invoices. Make it specific enough that it cannot match a longer number by accident. `INV-2026-01` must not match inside `INV-2026-011`, so anchor the pattern or check the character that follows.

**`AUTO_BOOK`** — leave this `false` for the first few weeks. The skill then proposes bookings in the report instead of writing them, and you can see whether its matches agree with your own judgement. Once you trust it, set it to `true` and the unambiguous matches get booked without asking.

**`OVERDUE_THRESHOLD`** — how long past the due date before the skill prepares a reminder. Thirty days is a reasonable default for B2B customers with an approval workflow. Shorten it if you invoice small amounts to small companies.

---

## Step 1: Pull the open invoices

Call `list_client_invoices` with status `unpaid`, 100 per page, sorted by due date ascending. Page through until you have them all.

Note per invoice: **number, issue date, due date, total amount, amount already paid, customer, invoice id, attachment id.**

The `amount_paid` field matters. Anything above zero but below the total is a partial payment and belongs in Step 5, not in the matching.

## Step 2: Pull the incoming payments

Call `list_transactions` for your revenue account with side `credit`, starting `LOOKBACK_MONTHS` back, 100 per page.

If the oldest open invoice is older than your lookback window, extend the window to cover it. An invoice from fourteen months ago compared against twelve months of payments will always look unpaid.

**Page through to the end.** Compare the number of rows you collected against `meta.total_count` before you evaluate anything. A missing page silently turns paid invoices into dunning letters. If the output is too large for your context, write it to a file and read it back compactly, for example:

```
jq -r '.transactions[] | [.emitted_at[0:10], .amount, (.label//""), .id,
  ((.reference//"")|gsub("[\n\r]+";" ")), (.attachment_ids|length)] | @tsv' <file>
```

Also check `pending`, `declined` and `reversed` credits once. A payment in flight is not a reason to send a reminder.

## The counting rule: one transaction is one payment

**The transaction id is the only unit of counting. Never the payment reference.**

Customers write the invoice number into the reference twice all the time:

```
RE INV-2026-113/RE INV-2026-113
No.INV-2026-022/17.2.2026 ... RGINV-2026-022
```

Pull every regex match out of each line in a loop and count the matches, and you turn one payment into two and report a double payment that never existed. This is the single most common way this task goes wrong.

So: **take at most one invoice number per transaction, and deduplicate by unique transaction id whenever you group.**

## Step 3: Matching

A match counts as unambiguous only when **all four** conditions hold:

- **a)** the payment amount equals the invoice total exactly,
- **b)** the invoice number appears in the payment reference **or** the payer is clearly the invoiced customer,
- **c)** the payment date is on or after the invoice issue date,
- **d)** the payment is not already assigned to another invoice.

### The amount trap

If you sell standard packages, the same amount arrives many times a year from different customers. A payment of exactly your invoice total, arriving right around the due date, routinely belongs to a **different, long since settled invoice.**

Condition (b) is what separates the two, and it is not optional. Amount equality alone is never sufficient. When in doubt: do not book, report.

### The payer name trap, in the other direction

Large customers pay through someone else: a parent company, a shared service center, a payment provider, a factoring partner, or simply a different spelling. "No payment from this customer" is often "no payment under this exact name". Condition (b) is satisfied by a payer you can clearly tie to the customer, not only by an exact name equality.

## Step 4: Book the unambiguous matches

Only if `AUTO_BOOK = true`. Otherwise list them in the report as proposals and stop here.

Per unambiguous match:

1. **Fetch the invoice PDF.** `get_attachment` with the invoice's attachment id, then download the presigned URL to a temporary file. The URL is short-lived and is a credential: do not put it in the report.
2. **Attach the PDF to the payment.** `request_attachment_upload` with content type `application/pdf`, PUT the file to the returned URL, then `upload_attachment` with the blob reference and the transaction id. If the transaction already has an attachment, do not add a second one. Note it in the report instead.
3. **Mark the invoice paid.** `mark_client_invoice_as_paid` with `paid_at` set to the **actual date of the payment**, not today. Booking everything with today's date destroys your own aging analysis and makes next quarter's cash figures wrong.

## Step 5: Report what is unclear, do not touch it

### Mandatory verification before any finding

Before a case goes into the report, **re-fetch the transactions involved individually with `get_transaction`** and check them against the primary source. A claim based only on your own intermediate file is not admissible, because that file is where your parsing bugs live.

For a suspected double payment, additionally call `list_transactions` for the narrow window around the date with status `pending`, `completed`, `reversed` and `declined`, to be sure there really are two bookings.

Every reported case names **date, amount, transaction id, and the payment reference in its original wording.** Having to quote the id is what forces you to have looked at it. If a case cannot be evidenced this way, it does not belong in the report.

### What to report

**Partial and under-payments.** Amount paid is above zero but below the invoice total, or the credit is smaller than the invoice. Two common causes, and they call for opposite responses: an early payment discount taken without agreement, or your invoice was simply too high. Check whether the difference is a clean multiple of a single unit price, for example one seat, one license, one participant. If it is, your invoice is usually the thing that is wrong, not the payment, and that changes the email completely.

**Double payments.** Two credits with **different transaction ids** against the same invoice number, or the same amount twice from the same payer. Apply the counting rule above before you believe it.

**Overpayments and credits you cannot place.** A payment with no identifiable invoice is worth reporting once. If it turns out to be a tax refund, a grant, a platform payout or a supplier refund, note what it is so the next run skips it quietly.

**Anything where the matching is not clean.** That is the whole category. If you had to argue yourself into a match, it is a report, not a booking.

### Known and parked cases

Keep a short list of cases the owner has already decided on, and mention each in **one line as unchanged**, never as a fresh decision. Re-litigating a settled case every week is how a useful weekly report becomes one nobody opens.

```
INV-2025-124  <customer>  — discount remainder deliberately parked
INV-2026-070  <customer>  — double payment, parked on purpose
INV-2026-022  <customer>  — owner decided to ignore, stop reporting
INV-2026-113  <customer>  — not a double payment, parsing artifact, stop reporting
```

Add a line whenever the owner makes a call, including "this was never a real finding". That last kind is the most valuable, because it stops the same false positive from coming back forever.

## Step 6: Reminders for invoices well past due

For every open invoice more than `OVERDUE_THRESHOLD` past its due date where the Step 5 verification found no payment:

### 1. Find a human

In order: the email on the customer record, then the right contact in your CRM at that company, then the most recent email correspondence with that company in your mailbox.

If the address on the customer record is obviously a machine (`invoice@`, `no-reply@`, or an invoicing portal such as Basware, Coupa, Ariba, Tungsten, Tradeshift, Ivalua), do not write to it informally. Find a real person. **If you cannot find one, do not build an email. Ask for the right contact in the report instead.**

### 2. Check nobody already asked

Search the mailbox for the invoice number in quotes over the last 14 days. If a reminder already went out, do not create a second one, just mention it in the report.

Also check whether an **internal** thread about this invoice is still open, for example several invoices covering the same order, a disputed scope, or a credit note being prepared. If so, do not build a customer email. Propose finishing the internal clarification first. An invoice you are not sure you should be charging is not an invoice you should be chasing.

### 3. Write the draft

Short, friendly, on equal footing. Ask them to check whether it is already paid or where it sits in their approval chain, and offer to supply whatever is missing: a purchase order number, a cost center, a different invoice format, a re-issue. Name the invoice number, invoice date, amount and invoice recipient. Attach the invoice PDF.

**No threats, no late fees, no legal language.** The overwhelmingly likely explanation is that your invoice is sitting in an approval queue, not that anyone is refusing to pay. Write for that case.

### 4. The tone rule for claims about the customer

What the customer supposedly did, paid twice, paid short, did not pay, **never goes into the subject line as a fact.** Keep the subject neutral: "Question about the payment from 2 September", not "Invoice was paid twice".

In the body, frame it as your own observation and give them a way to contradict you: "on our side it looks like X, would you mind double checking". You are reading your own books, not theirs, and your books are wrong often enough that the humility is simply accurate.

**Your own mistakes are the exception.** Name those clearly and directly. Being blunt about your own error costs nothing and buys a great deal.

### 5. Create it as a draft

Use whatever drafting tool you have, with the invoice PDF attached. **Never send.** The owner reads it and clicks send.

Template, adjust the voice to yours:

```
Hi <first name>,

quick question from our side on an open invoice.

We still have invoice <number> from <date> for <amount> showing as unpaid.
It covers <what it is for>, invoiced to <recipient>.

Would you mind checking whether it has already gone out on your side and we
just cannot match it, or whether it is still sitting somewhere in approval?
If something is missing at your end, a PO number, a cost center, a particular
invoice format, just say the word and we will send it over or re-issue the
invoice to match.

I have attached the invoice again just in case.

Thanks and best regards
<SIGNATURE>
```

## Step 7: The report

Compact, and in this order. The order is the point: the owner reads from the top and should hit the things only they can decide first.

1. **Where you need to decide** — the Step 5 cases, each with transaction id and the original payment reference as evidence.
2. **What was booked automatically** and linked with a receipt. Or, with `AUTO_BOOK = false`, what the skill proposes booking.
3. **Which email drafts were created**, to whom and for which invoice, with the explicit note that they are **sitting unsent in the mailbox and need to be released by the owner.**
4. **Remaining open items** with a total, short and in a table.

Also worth a line: the verifications that came back negative. "Checked and dismissed: the two credits against INV-2026-012 are partial payments summing exactly to the invoice total, so not a double payment" tells the owner the skill looked, which is the difference between a quiet week and an unexamined one.

---

## Why the guardrails are shaped this way

Each of these cost somebody a real mistake:

- **Counting references instead of transactions** invented a double payment and nearly sent a customer an apology for money they never sent twice.
- **Matching on amount alone** tried to mark an invoice paid using a payment that belonged to a different invoice settled months earlier, because the company sells packages at standard prices.
- **A missing page of transactions** made paid invoices look unpaid.
- **Booking with today's date** instead of the real payment date quietly corrupted the aging report.
- **Re-reporting settled cases** every week trained the owner to skim past the report, which is worse than not running it.

If you change one thing in this skill, do not change these.
