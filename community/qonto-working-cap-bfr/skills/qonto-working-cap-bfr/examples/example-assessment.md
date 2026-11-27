# Example: transactions-only customer (mode B)

See also `example-assessment-hybrid.md` for a customer with partial invoicing and heavy Pay Later use.

Owner: "Est-ce que je vais manquer de trésorerie dans les prochains mois ?"

Expected flow:
1. `get_organization` (FR, fr locale: answer in French), `list_bank_accounts` (main account, project account, closed VAT account; all names fabricated), `list_cash_flow_categories`.
2. `list_transactions` on all three accounts, 12 months, all pages. Remove duplicates.
3. Invoice check: few client invoices, no supplier invoices: mode B.
4. Categorise: exclude transfers between own IBANs and an "Apport associé" credit labelled with the company name. URSSAF and DGFIP from the dictionary. Card payments at Leroy Merlin and Point.P as Suppliers. Recurring end-of-month transfers to four individuals flagged as probable payroll.
5. One question to the owner: the 12 largest unclassified counterparties, one client whose receipts are split between "Sales revenue" and "Subsidies", the probable payroll group, plus typical payment terms for the 5 main clients and 4 main suppliers, and any large unpaid invoices right now.
6. After answers: 93% of volume classified. Propose writing 141 categories to Qonto and creating "Owner contributions" and "Internal transfers". Owner says yes to all.
7. Analysis with DSO and DPO labelled "estimated from your stated terms", 13-week forecast with URSSAF on the 15th and VAT around the 19th (from history), three scenarios.
8. Answer: headline, key numbers, drivers, forecast, actions (invoice unbilled work, ask deposits), then Pay Later as an option for the September supplier peak, sized to the gap and checked against `get_qonto_public_pricing`, subject to eligibility.
9. Reliability section: mode B, 93% coverage, terms as stated by the owner.
10. Interactive cash simulator built from `assets/cash-simulator.html` with the same figures, so the owner can test a client delay, a lower payroll, the Flex card share, Pay Later on chosen invoices, or an overdraft limit.
