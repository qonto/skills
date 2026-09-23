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
2. Group the entries by VAT rate and compute the deductible VAT per rate; the applicable 2026 rates are summarized in the bundled chart, assets/vat-rules.png.
3. Show the user the draft summary together with the chart, and wait for their confirmation.
