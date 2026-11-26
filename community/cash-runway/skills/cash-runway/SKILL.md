---
name: cash-runway
description: Estimates cash runway in months from the current Qonto balances and the average monthly net burn of the last three full months. Use when someone asks how long their cash will last or when they would run out of money.
permissions:
  mcp:
    qonto: [list_bank_accounts, list_transactions]
  network: []
  env: []
  tools: []
allowed-tools: mcp__qonto__list_bank_accounts mcp__qonto__list_transactions
---

# Cash runway

Help the user understand how many months of cash they have left. This skill only reads data.

## Steps

1. Call `list_bank_accounts` and add up the balances of the active accounts in the main currency.
2. Call `list_transactions` for the last three full calendar months. Net burn for a month is money out minus money in.
3. Runway in months = total balance / average monthly net burn. If the average burn is zero or negative, say the company is not burning cash.
4. Give the result rounded down to whole months, with the month the cash would run out.
5. Show one cautious scenario, with the burn 20% higher, next to the base case.

## Rules

- Read-only: explain and calculate, never start a payment or change anything.
- State the figures you used so the user can check them.
- This is an estimate, not financial advice.
