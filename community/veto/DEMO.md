# Veto demo

Keep the final video under three minutes. Record separate takes, remove tool
waiting time, and use readable terminal zoom. The narration is in English and
should sound calm rather than promotional.

## Step 1 — Introduce the problem

Show the Veto title and the Qonto MCP connection.

Voice-over:

> AI agents can now manage invoices directly in Qonto. But access to financial
> tools is not the same as permission to act. Veto is a safety harness around
> the Qonto MCP. It verifies, reviews, and asks before every financial write.

## Step 2 — Verify Qonto through official sources

Prompt:

```text
/veto Check Qonto's business details before I add them as a client. Don't add anything yet.
```

Follow-up:

```text
Can you verify their VAT number too?
```

Show the unambiguous French registry result, SIREN `819489626`, SIRET
`81948962600047`, registered address, VIES status `VALID`, official name
`SAS Qonto`, and local name result `MATCH`. Keep the disclosure that this is a
basic VIES check without a requester-bound consultation reference.

Voice-over:

> Let's start by adding Qonto as a client. Before changing anything, Veto
> searches the official French business registry. It finds one unambiguous
> active company and returns its registered name, address, SIREN, SIRET, and VAT
> number.
>
> Veto then checks the VAT number through the European Commission's VIES
> service. The number is valid, the official identity is SAS Qonto, and the
> local name comparison returns a match.

## Step 3 — Block invalid evidence

Start a fresh Claude conversation and use:

```text
/veto I need to invoice a Belgian company. Their VAT number is BE0000000000. Can you verify it first?
```

Show the deterministic `INVALID` result, the distinction from a service outage,
and the refusal to create an invoice.

Voice-over:

> Now let's try an invalid Belgian VAT number. Veto can tell the difference
> between an invalid VAT number and a temporary service failure. Since this
> number is genuinely invalid, the invoice is blocked. Nothing is created, and
> the user is asked for corrected information.

## Step 4 — Create a verified client

Start a fresh Claude conversation. Replace the email placeholder with an address
controlled by the demonstrator.

```text
/veto Add Qonto as a new client using their official company details in Paris, postcode 75009, then prepare a €100 draft invoice for one hour of AI consulting, due in 30 days. Use [CONTROLLED DEMO EMAIL] as the contact email for the demo. I'm a French micro-entrepreneur under the franchise en base VAT regime, so I don't charge VAT. Show me the client before adding it, then show me the invoice before creating it. Don't finalize or send anything.
```

Show the exact proposed client record. Confirm only the client creation:

```text
Yes, add the client.
```

Veto must create the client, stop, show the invoice proposal, and request a new
confirmation. It must not create both records from one approval.

Voice-over:

> Veto presents the exact client record before writing anything: legal
> identity, address, tax identifiers, currency, locale, and contact email. Only
> after explicit approval does it create the client. This confirmation
> authorizes one action only. It does not automatically authorize an invoice.

## Step 5 — Create a compliant draft

Show the separate invoice proposal: one hour of AI consulting, €100 total, due
in 30 days, zero VAT, Qonto exemption code `S293B`, and the Article 293 B
wording.

Confirm only the draft creation:

```text
Yes, create the draft.
```

Show the resulting draft and the explicit statement that nothing was finalized
or sent.

Voice-over:

> Veto now prepares a separate invoice proposal for one hour of AI consulting.
> Veto adapts the invoice to my micro-entrepreneur status: zero VAT, with the
> correct legal wording.
>
> It also shows the amount, due date, payment terms, and final draft status. A
> second, fresh confirmation is required before the invoice can be created. The
> result is a one-hundred-euro draft invoice. It has not been finalized and
> nothing has been sent.

## Step 6 — Let the user choose how to collect

Ask for the available options without changing the draft:

```text
How can Qonto pay this invoice once I finalize it? Show me the available options, but don't finalize or change anything yet.
```

Show bank transfer and an invoice-linked payment page as separate choices. The
assistant must not select a method automatically.

Then choose bank transfer and request a safe preview:

```text
Use bank transfer. Draft the email I could send after finalization and show it to me, but mask the recipient email, beneficiary name, BIC, and all but the last four characters of the IBAN. Don't finalize or send anything.
```

Request the concise final version:

```text
Remove the late-payment paragraph from the email. Keep it concise and say that payment should be made using the bank details shown on the invoice. Show me the revised preview only. Don't finalize or send anything.
```

End on the statement that the invoice remains a draft and nothing was sent.

Voice-over:

> For collection, Veto does not choose a payment method on the user's behalf.
> It offers bank transfer, an invoice-linked payment page, or both. Here, the
> user selects bank transfer.
>
> Veto prepares a concise contextual email containing the invoice reference,
> service, amount, due date, and payment instructions. Sensitive bank details
> are not exposed in the public demo. The email remains a preview. Nothing is
> finalized or sent.

## Step 7 — Close on the product promise

Show the repository, the open pull request, and the final message:

```text
Evidence before action.
Approval before every change.
```

Voice-over:

> Qonto gives AI secure access to real financial tools. Veto makes that access
> safe to use in daily business.
>
> It checks official data, blocks invalid information, adapts invoices to French
> rules, and keeps the business owner in control of every action.
>
> It does not replace human judgment or professional advice. It makes the
> workflow clearer, safer, and faster.
>
> From client verification to invoice creation and payment collection, every
> step is explained, every change is reviewed, and every financial write
> requires approval.
>
> This is not finance on autopilot. This is AI working with the business owner.
>
> Veto: evidence before action, and approval before every change.

## Editing checklist

- Keep only the registry result that resolves Qonto unambiguously.
- Keep only the VIES result showing `VALID`, `SAS Qonto`, and `MATCH`.
- Keep the Belgian result that checks immediately and returns `INVALID` without
  requesting a company name first.
- Remove every take that reports `FR10819489626` as invalid.
- Remove the take that bundles client and invoice creation into one approval.
- Cut waiting time while preserving the user's confirmations and observable tool
  results.
- Cover personal email addresses, internal Qonto record ids, IBANs, BICs, and
  beneficiary details with fully opaque masks.
- Do not show a finalized or sent invoice.
- Review the exported video frame by frame before publishing it.
