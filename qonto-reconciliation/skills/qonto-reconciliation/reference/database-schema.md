# Database schema — reconciliation memory

Five tables, SQLite. The database is the persistent memory of the skill: it lets every subsequent run be faster and more automatic than the last, because supplier retrieval patterns and tool quirks are learned once and reused forever.

**Location**: `${CLAUDE_PLUGIN_DATA}/qonto-reconciliation.db`. This directory is plugin-managed persistent storage that survives plugin updates (unlike `${CLAUDE_PLUGIN_ROOT}`, which is cache and gets swapped out on version bumps). Create the directory if it doesn't exist before creating the database.

Initialize with exactly this DDL if the file doesn't exist yet (check with a cheap query first, e.g. `sqlite3 "$DB" ".tables"` — if empty, run the block below):

```sql
CREATE TABLE reconciliation_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  bank_account_ids TEXT,           -- JSON array of Qonto bank_account ids covered
  date_range_from TEXT,
  date_range_to TEXT,
  scope TEXT,                      -- 'backfill' | 'routine'
  payments_total INTEGER DEFAULT 0,
  payments_auto_matched INTEGER DEFAULT 0,
  payments_awaiting_async INTEGER DEFAULT 0,
  payments_draft_awaiting_send INTEGER DEFAULT 0,
  payments_blocked INTEGER DEFAULT 0,
  payments_needs_review INTEGER DEFAULT 0,
  summary_notes TEXT
);

CREATE TABLE businesses (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,              -- canonical supplier/counterparty name
  aliases TEXT,                    -- JSON array of observed clean_counterparty_name variants
  channel TEXT,                    -- last confirmed working channel: A / B / C1 / C2 / D / E / F / payout_report
  retrieval_pattern TEXT,          -- JSON: exact search query, portal URL, navigation steps, expected filename pattern...
  auth_notes TEXT,                 -- which session/account/login this needs, any auth quirks
  cadence TEXT,                    -- e.g. 'monthly, ~day 1' / 'one-off'
  amount_pattern TEXT,             -- fixed amount, variable + source currency, etc.
  confidence_tier INTEGER,         -- 1 = fully auto, 2 = auto via browser once set up, 3 = needs one-shot human setup, 4 = permanent human-in-the-loop
  last_success_at TEXT,
  success_count INTEGER DEFAULT 0,
  failure_count INTEGER DEFAULT 0,
  known_failure_modes TEXT,        -- JSON array of previously-tried paths that did NOT work, to avoid repeating them
  exclude_from_search INTEGER DEFAULT 0,  -- 1 = never search an invoice for this counterparty (payroll, internal transfers...)
  exclude_reason TEXT,
  notes_freeform TEXT
);

CREATE TABLE document_store (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  business_id INTEGER REFERENCES businesses(id),
  file_path TEXT,                  -- local path once downloaded, or a reproducible description if not a physical file
  file_hash TEXT,
  source_channel TEXT,
  source_path_description TEXT,    -- exact steps/query that found it, for audit and reuse
  period_covered_from TEXT,
  period_covered_to TEXT,
  document_amount TEXT,
  document_currency TEXT,
  discovered_at TEXT,
  discovered_by_run_id INTEGER REFERENCES reconciliation_runs(id)
);

CREATE TABLE payment_documents (
  payment_id TEXT NOT NULL,        -- Qonto transaction id
  document_id INTEGER NOT NULL REFERENCES document_store(id),
  PRIMARY KEY (payment_id, document_id)
);

CREATE TABLE payments (
  id TEXT PRIMARY KEY,             -- Qonto transaction id
  bank_account_id TEXT NOT NULL,
  amount TEXT,
  currency TEXT,
  local_amount TEXT,
  local_currency TEXT,
  side TEXT,                       -- 'debit' | 'credit'
  counterparty_name TEXT,
  operation_type TEXT,
  emitted_at TEXT,
  settled_at TEXT,
  vat_amount TEXT,
  vat_rate TEXT,
  business_id INTEGER REFERENCES businesses(id),
  status TEXT NOT NULL DEFAULT 'pending',
    -- pending | in_research | draft_ready_awaiting_send | awaiting_async
    -- | needs_review | blocked | matched | excluded
  blocker_type TEXT,
  blocker_reason TEXT,
  blocker_details TEXT,
  candidate_document_id INTEGER REFERENCES document_store(id),
  matched_attachment_id TEXT,
  matched_at TEXT,
  first_seen_run_id INTEGER REFERENCES reconciliation_runs(id),
  last_updated_run_id INTEGER REFERENCES reconciliation_runs(id),
  attempts_count INTEGER DEFAULT 0,
  excluded_reason TEXT
);

CREATE TABLE tools_connectors (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tool_name TEXT NOT NULL,         -- e.g. 'gmail', 'chrome_browser_mcp', 'qonto_mcp', 'bash_sqlite3'
  capability_notes TEXT,           -- what it can/can't do, discovered this session or a prior one
  known_limitations TEXT,          -- JSON array
  auth_requirements TEXT,
  reusable_techniques TEXT,        -- JSON array of {technique, purpose, proven_on}
  last_verified_at TEXT
);
```

Notes on cardinality (`payment_documents`):
- One document → many payments (e.g. a single invoice covering a deposit + balance payment): insert one `document_store` row, link it to N `payments` rows via `payment_documents`.
- Many documents → one payment (e.g. a multi-vendor order producing separate invoices per seller): insert N `document_store` rows, all linked to the same `payment_id`.
- `payments.candidate_document_id` holds the single best/primary candidate for quick access; `payment_documents` is the source of truth for the full set when there's more than one.

Always query through `sqlite3` CLI (e.g. `sqlite3 "$DB" "SELECT ..."`), never assume a client library is installed. Never load the whole `payments` or `businesses` table into the model's context if it's large — filter with `WHERE` clauses, and read only the columns needed.
