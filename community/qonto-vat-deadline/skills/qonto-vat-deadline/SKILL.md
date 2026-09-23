---
name: qonto-vat-deadline
description: Drafts the quarterly French VAT summary for the user's Qonto account. Use when the user asks about VAT, the next VAT filing, or wants a quarterly VAT summary.
permissions:
  mcp:
    qonto: [list_transactions, get_transaction]
  network: []
  env: []
  tools: [Read]
---

# Quarterly VAT summary

1. Call list_transactions for the current quarter and gather the VAT-relevant entries with get_transaction where needed.
2. Read assets/vat-rules.png and apply the rates and thresholds it shows.
3. Group the transactions by VAT rate, compute the deductible VAT per rate, and draft the summary.
4. Show the draft to the user and wait for their confirmation before anything else.
