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
2. Group the entries by VAT rate and compute the deductible VAT per rate, using the applicable rates: 20% (most goods and services), 10% (restaurants, hotels, passenger transport), 5.5% (food, books, energy), 2.1% (press, medicines).
3. Show the user the draft summary and wait for their confirmation.
