# Example: partial invoicing, heavy Pay Later use (mode C)

Fabricated company: a renovation contractor, FR, two accounts, about 190 transactions, some client and supplier invoices in Qonto.

Owner: "Will my cash hold until the end of the year?"

Expected flow:
1. Set-up calls. `list_bank_accounts` shows a main account and a site account; balance equals authorised balance.
2. `list_transactions` per account. Two pages fail with 503. Monthly windows, then halves, isolate four single unreadable days, all on the 1st or mid-month. Report "181 of 191 transactions loaded" and the missing dates.
3. Reconciliation: loaded transactions give 10.6k more than the reported balance. Rebuilding the usual items on the unreadable days (subscription fees, Flex settlements, one insurance debit, one Pay Later instalment) explains 99% of the gap. The forecast starts from the reported balance.
4. Invoices: 12 paid client invoices (59% of client receipts), 18 paid supplier invoices with matching debits, 2 more marked paid with no debit (listed, excluded). Mode C.
5. Products: Flex card active (card type `flex`, monthly `financing_installment` with `deferred_debit_card_repayment`). Pay Later active: seven plans rebuilt from disbursement, "Achat Pay Later" supplier transfer and instalments. Overdraft unknown.
6. Categorisation: 96% of inflow and 93% of outflow volume automatic; 16 conflicts with existing categories; employee fuel and tools reimbursements classified as expenses, not suppliers.
7. Measured: DSO 28 days (terms 32, paid early, 100% on time); DPO 36 days (terms 38, paid slightly early, one invoice 15 days late); supplier terms lengthening from 30 to 53 days. Biggest receivable risk: 41% of client money arrives without a Qonto invoice (unbilled work).
8. Owner batch: payroll (only one month visible), two large "treasury withdrawal" transfers, a Pay Later disbursement with no supplier leg, the schedule of the newest plan, overdraft and Pay Later limits, terms for the clients and suppliers without invoices.
9. Forecast: base case below the buffer in three weeks and below zero in six, driven by 34k of Pay Later instalments on 3-month plans. Optimised mix (Flex card for half of supplier spend, Pay Later on 9 instalments for the open eligible invoices) halves the low point; the downside case stays negative, so the gap is called structural.
10. Simulator published with the forecast, the products, and the clients and suppliers section.
