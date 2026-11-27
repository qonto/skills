# Transaction categorisation

Goal: every material transaction belongs to one **analysis class**, mapped to a leaf ID in the customer's Qonto category tree. The analysis uses the class; the Qonto ID is only needed for write-back.

## 1. Analysis classes

| Class | Direction | Used for | Typical Qonto default mapping |
|---|---|---|---|
| Client receipts | In | Revenue, DSO, concentration | Sales revenue |
| Grants and subsidies | In | Other inflows, not revenue | Subsidies & grants |
| Loan proceeds | In | Financing, excluded from revenue (includes Pay Later disbursements) | Bank loan proceeds |
| Owner contributions | In | Excluded from revenue | Missing in default tree: propose |
| Tax and VAT refunds | In | Other inflows | Missing: propose |
| Supplier refunds | In | Net against purchases | Missing: propose, or net |
| Internal transfers | Both | Excluded entirely | Missing: propose |
| Suppliers, direct costs | Out | DPO, supplier concentration | Operational expenses > Production costs |
| Subcontractors | Out | DPO, often large | Employee expenses > Sub-contractors |
| Payroll (net salaries) | Out | Fixed costs | Employee expenses > Salaries |
| Social charges | Out | Fixed costs, tax calendar | Taxes > National insurance, or Employee expenses > Pension / Health insurance |
| VAT | Out | Tax calendar | Taxes > VAT payments |
| Corporate and other taxes | Out | Tax calendar | Taxes > Income tax / Other taxes |
| Rent | Out | Fixed costs | Operational expenses > Rent |
| Utilities, telecom | Out | Fixed costs | Operational expenses > Utilities |
| Software and subscriptions | Out | Fixed costs | Technology expenses > Software licenses / Hosting |
| Insurance | Out | Fixed costs | Administrative expenses > Insurance fees |
| Professional fees | Out | Opex | Administrative expenses > Accounting / Legal fees |
| Travel, fuel, vehicles | Out | Opex | Travel > ... |
| Marketing | Out | Opex | Marketing expenses > ... |
| Loan and financing repayments | Out | Debt service (includes Pay Later instalments) | Bank fees > Loan repayments |
| Flex card settlement | Out | Excluded from opex (card spend is already counted); timing only | Bank fees > Credit card repayments |
| Bank fees | Out | Opex | Bank fees > Other bank charges / Subscription fees |
| Owner withdrawals, personal spend | Out | Excluded from opex, flagged | Personal expenses |
| Savings movements | Out | Excluded from opex, still liquidity | Savings |
| Unclassified | Both | Kept visible, never hidden | none |

The customer's tree may differ from the default. Map each class to the closest existing leaf; if none fits, propose a new one (step 5).

## 2. Exclusions first

Before anything else, mark:
- **Internal transfers**: require a **matching opposite leg** (same amount, same or next day) on another of the customer's accounts, or a label equal to one of the customer's own account names (for example "Compte chantier"). A counterparty IBAN equal to one of the customer's own IBANs is a hint only, never enough on its own: client payments made against Qonto invoices can carry the customer's own IBAN in the counterparty field.
- **Owner contributions and withdrawals**: label equals the company name or an owner/manager name with no matching own-account leg, or note/reference containing "apport", "compte courant d'associé", "Einlage", "Gesellschafterdarlehen", "versamento soci", "aportación socios", "storting", "owner top-up". Ask the owner to confirm the person names.
- **Loan drawdowns**: incoming transfers from banks or lenders, `operation_type` related to financing, or notes with "prêt", "déblocage", "Darlehen", "finanziamento", "préstamo", "lening".
- **Employee expense reimbursements**: transfers to employees with a note such as fuel, tolls, tools or site supplies. Classify by the expense, never as a supplier in concentration or DPO figures.
- **Refunds**: credits from a counterparty that is normally a supplier, or "remboursement", "avoir", "Erstattung", "Gutschrift", "rimborso", "devolución", "terugbetaling".

## 3. Rule cascade

Apply in order; stop at the first confident match. Record the rule used for each transaction.

1. **Existing category, if trustworthy.** Trust it unless one of these applies:
   - The same counterparty has different categories across transactions (for example a client whose receipts are split between Sales revenue and Subsidies & grants).
   - The category contradicts the note or reference (for example a utilities category with the note "Fournitures de chantier").
   - The category is implausible for the operation (for example a "Salaries" category on a treasury withdrawal, an insurance category on a tax office debit, or a sales category on a transfer labelled with the company's own name).
   - A tax debit whose mandate reference names a different tax than its reference text (for example a "TVA" reference with a corporate-tax mandate). Ask which tax it is.
   Conflicts go into the owner question batch rather than being silently fixed.
2. **Operation type.** `qonto_fee` is Bank fees, except overdraft interest (see `qonto-financing.md`). A `financing_installment` with a `deferred_debit_card_repayment` block is a Flex card settlement. Transactions labelled "Qonto Pay Later" are Loan proceeds (credits) or Loan and financing repayments (debits); the supplier transfer referenced "Achat Pay Later" is a supplier cost. Card payments are never client receipts.
3. **Counterparty dictionary.** Match `clean_counterparty_name`, then `label`, against `counterparty-dictionary.md` for the organisation's country (tax offices, social security, payroll providers, utilities, telecom, insurers, leasing, common SaaS).
4. **Card merchant.** For card payments use `label`, not `reference`. Fuel stations to Travel; DIY and building suppliers to Suppliers for trades businesses; software and hosting merchants to Technology.
5. **Invoice matching.** In modes A and C, a transaction matched to a client invoice is Client receipts; matched to a supplier invoice is Suppliers. Match on counterparty name plus amount within 1% and date after issue date.
6. **Recurrence patterns.**
   - Several outgoing transfers to individuals on the same day or within 2 days, around month end, with similar amounts each month: probable Payroll. Confirm with the owner before treating as payroll.
   - Same amount, same counterparty, monthly, around the same day: Rent, leasing, subscription or loan; disambiguate with the dictionary or ask.
   - Incoming transfers from companies or public bodies with references like "facture", "invoice", "Rechnung", "fattura", "factura", "acompte", "Abschlag": Client receipts.
7. **Notes and references** for transfers: keywords mapping to classes (see dictionary).
8. Otherwise: **Unclassified**.

Label confidence as high (rules 1 to 5), medium (6 and 7), low (anything inferred from a single weak signal). Low confidence goes into the owner batch if material.

## 4. Owner question batch

- Group unclassified and low-confidence transactions by counterparty.
- Rank by total absolute amount.
- Ask about the top 10 to 15 counterparties in one message, until about 90% of total inflow and outflow volume is classified.
- Include conflicting existing categories in the same message.
- For each, show: counterparty, number of transactions, total amount, date range, your best guess. Let the owner answer briefly ("yes", a class name, or "personal").
- The remaining tail stays Unclassified and is reported with its total.

Example wording (adapt language):

> I've sorted 84% of your transactions automatically. A few I'd like you to confirm:
> 1. Camille Martin, 6 payments, 2,340 EUR: is this a subcontractor, an employee, or something else?
> 2. Ville de Nantes: most receipts are marked as sales, one as a grant. Are they all payments for work?
> 3. "Retrait trésorerie", 2 transfers, 18,695 EUR: owner withdrawals, or payroll?

## 5. Proposing new categories

If a class is needed and no leaf fits, propose creating it under the closest parent, or as a top-level category with the right direction. Typical proposals for the default tree: "Internal transfers" (top level, one inflow and one outflow version, or excluded from write-back), "Owner contributions" (inflow), "Customer refunds" and "Tax refunds" (inflow). Present all proposals in one list with the write-back summary.

## 6. Missing recurring classes

After classification, check that the classes every employer business has are present: payroll, social charges and VAT. If payroll shows only one or two months, or none, do not assume there are no employees. Report "payroll not found in the account" and ask how salaries are paid (another bank, a payroll provider, the owner). Keep payroll as an explicit assumption in the forecast until answered.

## 7. Coverage report

Before the analysis, state:
- Share of inflow volume and outflow volume classified, split by: existing categories, automatic rules, owner answers, unclassified.
- Number of conflicts found and how they were resolved.
- Amount excluded as internal transfers, owner flows and loan drawdowns.
