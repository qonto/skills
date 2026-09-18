# Legal basis for invoice set-off (netting) in the EU

> This is background information for drafting proposals, **not legal advice**.
> Every generated set-off agreement is a draft to be reviewed by the parties'
> counsel before signature.

## Italy — Codice Civile, artt. 1241–1252

Set-off ("compensazione") extinguishes reciprocal obligations between two
parties, each being at once creditor and debtor of the other (art. 1241).

- **Compensazione legale (art. 1243, co. 1).** Operates by law when both
  debts are monetary (or fungible of the same kind), **liquid** (certain in
  amount) and **collectable** (due and payable). Overdue invoices between the
  same two companies typically qualify. It must be pleaded by the interested
  party; it takes effect from the day the debts began to coexist (art. 1242).
- **Compensazione giudiziale (art. 1243, co. 2).** Ordered by a judge when
  one debt is not yet liquid but easy and quick to liquidate.
- **Compensazione volontaria (art. 1252).** The parties may agree to set off
  debts **even when the statutory conditions are not met** (e.g. invoices not
  yet due, disputed amounts) and may agree in advance on the conditions for
  future set-off. This is the vehicle used by the proposal template in
  `assets/compensation_proposal.md`, and the natural instrument for
  *multilateral* clearing, which the two-party mechanism of art. 1241 does
  not cover on its own: each participant in a cycle consents contractually.

Practical notes:
- Set-off is excluded for claims listed in art. 1246 (e.g. unseizable
  credits, claims for restitution of things deposited) — plain trade
  invoices between companies are not affected.
- Accounting/VAT: set-off settles the *payment* of the invoices; it does not
  alter the invoices themselves or their VAT treatment. Both parties record
  the extinction of the reciprocal positions.

## France — Code civil, artt. 1347–1348-2

"Compensation" extinguishes reciprocal obligations up to the lower amount
between fungible, certain, liquid and due debts (art. 1347, 1347-1); it must
be invoked. Judicial (art. 1348) and **contractual** compensation
(art. 1348-2) mirror the Italian judicial and voluntary forms.

## Germany — BGB §§ 387–396

"Aufrechnung" requires reciprocal obligations of the same kind, with the
declaring party's claim due and enforceable (§ 387). It is exercised by
declaration to the other party (§ 388) and takes retroactive effect to the
moment the positions first coexisted (§ 389). Contractual set-off agreements
(Aufrechnungsvertrag) are generally admissible under freedom of contract.

## Spain — Código Civil, artt. 1195–1202

"Compensación" operates when two parties are reciprocally creditor and
debtor of monetary or fungible debts that are due, liquid and collectable
(artt. 1195–1196), extinguishing both up to the concurrent amount
(art. 1202). Contractual compensation beyond the statutory conditions is
recognized by doctrine and case law.

## Multilateral clearing

All the mechanisms above are **bilateral**. A closed cycle of debts
(A→B→C→A) settles only through a *multilateral voluntary set-off agreement*:
every participant consents to extinguish its debt toward the next member of
the chain up to the cycle amount. This is contractually straightforward but
operationally hard without a coordinator — the counterparties do not know
the cycle exists. Detecting such cycles across companies is precisely the
role of a clearing house (e.g. the Nexyzen clearing engine): participants
submit their open positions, and the coordinator proposes the multilateral
agreement to all members of a detected cycle.
