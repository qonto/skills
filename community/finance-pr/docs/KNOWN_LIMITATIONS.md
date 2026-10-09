# Known limitations (honest scope)

## Qonto integration
- **No Qonto write is performed.** Act terminates at a verified `ready_for_qonto`
  handoff and writes are disabled by default. The sandbox exposes no tool that
  promotes a supplier invoice into a payment-request/native-approval workflow;
  the sampled invoices are additionally unpayable (`iban: null`, `pay: false` /
  `missing_iban`), and `list_requests` returns `403` on this plan. The nearest
  write, `create_multi_transfer_request`, only creates a *pending* request still
  gated by the user's own SCA. We do not call it. See
  `docs/QONTO_TOOL_INVENTORY.md`.
- **Reads only.** Observe uses `get_organization`,
  `get_authenticated_membership`, `get_supplier_invoice`,
  `list_supplier_invoices` (and transactions/attachments where useful).
- **Documents are not OCR-extracted.** `attachment_text` is treated as an
  optional/unavailable evidence source in the sandbox path; the injection
  detector runs on whatever text is provided (populated in synthetic scenarios).

## Detection scope
- The five signals are **transparent policy heuristics, not calibrated fraud
  probabilities**: possible duplicate, supplier IBAN drift, unusual amount,
  optional evidence gap, untrusted-instruction indicator.
- Sparse history → `insufficient_data` and lower coverage, which routes to
  manual review. This is intentional (unknown ≠ low risk), and it is why the real
  single-history sandbox supplier lands in `manual_review_required`.
- The untrusted-instruction detector is **advisory** (a pattern list); it will
  not catch every possible injection and should not be relied on as complete.

## Enforcement scope
- Finance PR protects **this** review workflow. It is **not** a global MCP proxy;
  another tool could still call Qonto writes directly. Org-wide enforcement is
  roadmap.

## Independent reviewer
- The optional second reviewer is an **offline, deterministic, escalate-only
  heuristic** (no network, no Qonto tools). A networked model would implement the
  same interface; it is documented but not wired to a provider by default. It can
  only preserve or increase review requirements — never authorize, never
  downgrade a gate.

## Persistence
- The Node `FileStore` uses atomic file writes + an exclusive-create one-shot
  reservation (the same compare-and-set guarantee SQLite would give). It is
  sufficient for the CLI/Skill flow and the demo; it is not a multi-tenant
  database.

## Visual
- The demo shows **one invoice per scenario** (six single-token runs). A
  multi-invoice queue is roadmap. Below ~1100px width the detail panel is hidden;
  record at ≥1600px.

## Language
- `designated_approver` / `finance_reviewer` are **Finance PR policy labels**,
  not Qonto roles. "Green" means "no material risk observed; ready for Finance
  review" — never safe/paid/approved/executed.
