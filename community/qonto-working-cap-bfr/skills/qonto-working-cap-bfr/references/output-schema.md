# Output schema (for structured or dashboard output)

{
  "period": {},
  "data_mode": "A | B | C",
  "data_quality": {"duplicates_removed": 0, "coverage_gaps": [], "accounts": []},
  "categorisation": {
    "inflow_coverage": {"existing": 0, "rules": 0, "owner": 0, "unclassified": 0},
    "outflow_coverage": {"existing": 0, "rules": 0, "owner": 0, "unclassified": 0},
    "excluded": {"internal_transfers": 0, "owner_flows": 0, "loan_drawdowns": 0},
    "conflicts": [],
    "proposed_new_categories": [],
    "write_back": {"proposed": 0, "approved": 0, "written": 0, "failed": 0}
  },
  "cash_position": {},
  "working_capital": {
    "dso": {"value": 0, "median": 0, "terms": 0, "days_late": 0, "on_time_pct": 0, "invoices": 0, "coverage_pct": 0, "status": "measured | estimated"},
    "dpo": {"same fields": true},
    "cycle": 0,
    "terms_trend": {"clients": [], "suppliers": []},
    "paid_without_transaction": [],
    "paying_early_cash": 0
  },
  "counterparties": {"clients": [{"name": "", "amount": 0, "share": 0, "invoices": 0, "days_to_pay": 0, "terms": 0, "days_late": 0, "on_time_pct": 0, "open": 0}], "suppliers": []},
  "open_items": [{"side": "client | supplier", "name": "", "ref": "", "amount": 0, "issue": "", "due": "", "ageing_bucket": ""}],
  "monthly_operating_flows": [{"month": "", "inflow": 0, "outflow": 0}],
  "reconciliation": {"reported_balance": 0, "derived_balance": 0, "gap": 0, "explained_by_rebuilt_items": 0, "unreadable_days": []},
  "client_risk": {"concentration": {}, "late_payers": []},
  "supplier_risk": {"concentration": {}, "late_payments": []},
  "fixed_costs": {},
  "gaps": [],
  "forecast_13_weeks": [],
  "scenarios": [],
  "qonto_products": {
    "overdraft": {"status": "active | eligible | unknown | not_available", "signals": [], "limit": null, "used": null},
    "pay_later": {"status": "", "signals": [], "remaining_limit": null, "active_plans": []},
    "flex_card": {"status": "", "signals": [], "settlement_day": null, "monthly_card_spend": null}
  },
  "forecast_layers": {"without_financing": {}, "with_active_products": {}, "optimised": {"mix": [], "cost": null}},
  "financing_need": {},
  "recommendations": [],
  "limitations": []
}

Each metric: value, period, method, source, "measured" or "estimated".
