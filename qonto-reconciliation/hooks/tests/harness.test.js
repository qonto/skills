"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { spawnSync } = require("node:child_process");
const test = require("node:test");

const HARNESS = path.join(__dirname, "..", "scripts", "harness.js");
const RESEARCHER = "qonto-reconciliation:qonto-reconciliation-researcher";
const VERIFIER = "qonto-reconciliation:qonto-reconciliation-verifier";

function fixture() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "qonto-harness-"));
  const env = { ...process.env, CLAUDE_PLUGIN_DATA: root };
  const session_id = `session-${path.basename(root)}`;
  return { root, env, session_id };
}

function run(context, action, input) {
  const result = spawnSync(process.execPath, [HARNESS, action], {
    input: JSON.stringify({ session_id: context.session_id, cwd: process.cwd(), ...input }),
    env: context.env,
    encoding: "utf8"
  });
  assert.equal(result.status, 0, result.stderr);
  return result.stdout ? JSON.parse(result.stdout) : undefined;
}

function state(context) {
  return JSON.parse(fs.readFileSync(path.join(context.root, "runtime", "current", "state.json"), "utf8"));
}

function activate(context) {
  return run(context, "activate", {
    hook_event_name: "UserPromptSubmit",
    prompt: "/qonto-reconciliation:qonto-reconciliation last 7 days"
  });
}

function registerManifest(context, suppliers) {
  return run(context, "register-manifest", { manifest: { suppliers } });
}

function blockOf(value) {
  return value && value.hookSpecificOutput && value.hookSpecificOutput.permissionDecision;
}

function fenced(value) {
  return `\`\`\`qonto-reconciliation-result\n${JSON.stringify(value)}\n\`\`\``;
}

function researcherAssignment(overrides = {}) {
  return {
    kind: "researcher_assignment",
    assignment_id: "research-acme",
    business_key: "acme",
    business_name: "Acme",
    payment_ids: ["pay-1"],
    capability_manifest: { connectors: { "mail-connector": { status: "available" } } },
    known_memory: {},
    ...overrides
  };
}

function researcherResult(overrides = {}) {
  return {
    kind: "researcher_result",
    assignment_id: "research-acme",
    business_key: "acme",
    business_name: "Acme",
    payment_ids: ["pay-1"],
    channels_attempted: [{ channel: "A", tool: "mail-connector", outcome: "found", observed_at: "2026-07-13T12:00:00Z" }],
    candidates: [{ candidate_id: "candidate-1", payment_ids: ["pay-1"], document_location: "C:/docs/acme.pdf", source_channel: "A" }],
    blockers: [],
    drafts: [],
    memory_updates: {},
    bonus_findings: [],
    ...overrides
  };
}

function verifierAssignment(overrides = {}) {
  return {
    kind: "verifier_assignment",
    verification_id: "verify-1",
    candidate_id: "candidate-1",
    payment_ids: ["pay-1"],
    document_location: "C:/docs/acme.pdf",
    ...overrides
  };
}

function verifierResult(overrides = {}) {
  return {
    kind: "verifier_result",
    verification_id: "verify-1",
    candidate_id: "candidate-1",
    payment_ids: ["pay-1"],
    verdict: "confirmed",
    evidence: {
      document_fields_read: ["supplier", "amount", "currency", "invoice_date"],
      document_values: { supplier: "Acme", amount: "42.00", currency: "EUR", invoice_date: "2026-07-10" },
      transaction_values: { amount: "42.00", currency: "EUR", settled_at: "2026-07-11", counterparty: "Acme" },
      tolerances_applied: []
    },
    reason: "Exact amount, currency, and supplier; date within one day.",
    ...overrides
  };
}

test("unrelated prompts do not activate the harness", () => {
  const context = fixture();
  const result = run(context, "activate", { hook_event_name: "UserPromptSubmit", prompt: "fix my README" });
  assert.equal(result, undefined);
  assert.equal(fs.existsSync(path.join(context.root, "runtime", "current", "state.json")), false);
});

test("explicit skill invocation activates capability discovery", () => {
  const context = fixture();
  const result = activate(context);
  assert.match(result.hookSpecificOutput.additionalContext, /harness active/i);
  assert.equal(state(context).phase, "capability_discovery");
});

test("reset skill clears active runtime state but preserves the database", () => {
  const context = fixture();
  activate(context);
  const database = path.join(context.root, "qonto-reconciliation.db");
  fs.writeFileSync(database, "persistent-memory");
  const result = run(context, "activate", {
    hook_event_name: "UserPromptSubmit",
    prompt: "/qonto-reconciliation:qonto-reconciliation-reset"
  });
  assert.match(result.hookSpecificOutput.additionalContext, /runtime state.*reset/i);
  assert.equal(fs.existsSync(path.join(context.root, "runtime", "current", "state.json")), false);
  assert.equal(fs.readFileSync(database, "utf8"), "persistent-memory");
  const stopped = run(context, "stop", {
    hook_event_name: "Stop", stop_hook_active: false, last_assistant_message: "Reset complete"
  });
  assert.equal(stopped, undefined);
});

test("direct reset-run control clears a stuck run", () => {
  const context = fixture();
  activate(context);
  registerManifest(context, [{ business_key: "acme", business_name: "Acme", payment_ids: ["pay-1"] }]);
  run(context, "reset-run", { reason: "operator requested clean restart" });
  assert.equal(fs.existsSync(path.join(context.root, "runtime", "current", "state.json")), false);
});

test("connector discovery and account-capability probes are allowed while supplier research is denied", () => {
  const context = fixture();
  activate(context);
  const discover = run(context, "pre-tool", {
    hook_event_name: "PreToolUse",
    tool_name: "mcp__mailbridge__list-endpoints",
    tool_input: { pattern: "email accounts" }
  });
  assert.equal(discover, undefined);
  const accountProbe = run(context, "pre-tool", {
    hook_event_name: "PreToolUse",
    tool_name: "mcp__mailbridge__execute-request",
    tool_input: { harRequest: { method: "GET", url: "https://example.test/accounts" } }
  });
  assert.equal(accountProbe, undefined);
  const research = run(context, "pre-tool", {
    hook_event_name: "PreToolUse",
    tool_name: "mcp__mailbridge__execute-request",
    tool_input: { harRequest: { method: "GET", url: "https://example.test/emails?search=Acme" } }
  });
  assert.equal(blockOf(research), "deny");
  assert.match(research.hookSpecificOutput.permissionDecisionReason, /orchestrator-only/i);
});

test("successful connector capability probes are recorded generically", () => {
  const context = fixture();
  activate(context);
  run(context, "post-tool", {
    hook_event_name: "PostToolUse",
    tool_name: "mcp__mailbridge__execute-request",
    tool_input: { harRequest: { method: "GET", url: "https://example.test/accounts" } },
    tool_response: { accounts: [{ provider: "GENERIC_MAIL", capabilities: ["MAIL"] }] }
  });
  assert.equal(state(context).capabilities.mail.capability_proven, true);
  assert.equal(state(context).capabilities.mail.status, "available");
});

test("researcher assignment must cover exactly one manifest supplier and exact payments", () => {
  const context = fixture();
  activate(context);
  registerManifest(context, [{ business_key: "acme", business_name: "Acme", payment_ids: ["pay-1", "pay-2"] }]);
  const invalid = researcherAssignment({ payment_ids: ["pay-1"], business_keys: ["acme", "other"] });
  const result = run(context, "pre-tool", {
    hook_event_name: "PreToolUse",
    tool_name: "Agent",
    tool_input: { subagent_type: RESEARCHER, prompt: fenced(invalid) }
  });
  assert.equal(blockOf(result), "deny");
});

test("generic agents are denied during an active run", () => {
  const context = fixture();
  activate(context);
  const result = run(context, "pre-tool", {
    hook_event_name: "PreToolUse",
    tool_name: "Agent",
    tool_input: { subagent_type: "general-purpose", prompt: "find invoices" }
  });
  assert.equal(blockOf(result), "deny");
  assert.match(result.hookSpecificOutput.permissionDecisionReason, /exactly/);
});

test("researcher missing_capability requires concrete probe evidence", () => {
  const context = fixture();
  activate(context);
  registerManifest(context, [{ business_key: "acme", business_name: "Acme", payment_ids: ["pay-1"] }]);
  const assignment = researcherAssignment();
  run(context, "pre-tool", {
    hook_event_name: "PreToolUse",
    tool_name: "Agent",
    tool_input: { subagent_type: RESEARCHER, prompt: fenced(assignment) }
  });
  const result = researcherResult({
    candidates: [],
    blockers: [{ payment_ids: ["pay-1"], blocker_type: "missing_capability", reason: "No email" }]
  });
  const stop = run(context, "subagent-stop", {
    hook_event_name: "SubagentStop",
    agent_id: "agent-1",
    agent_type: RESEARCHER,
    stop_hook_active: false,
    last_assistant_message: fenced(result)
  });
  assert.equal(stop.decision, "block");
  assert.match(stop.reason, /probe_evidence/);
});

test("candidate cannot reach attachment before verifier confirmation", () => {
  const context = fixture();
  activate(context);
  registerManifest(context, [{ business_key: "acme", business_name: "Acme", payment_ids: ["pay-1"] }]);
  const assignment = researcherAssignment();
  run(context, "pre-tool", {
    hook_event_name: "PreToolUse",
    tool_name: "Agent",
    tool_input: { subagent_type: RESEARCHER, prompt: fenced(assignment) }
  });
  run(context, "post-tool", {
    hook_event_name: "PostToolUse",
    tool_name: "Agent",
    tool_input: { subagent_type: RESEARCHER, prompt: fenced(assignment) },
    tool_response: { content: fenced(researcherResult()) }
  });
  const denied = run(context, "pre-tool", {
    hook_event_name: "PreToolUse",
    tool_name: "mcp__qonto__request_attachment_upload",
    tool_input: { file_name: "acme.pdf", content_type: "application/pdf", size_bytes: 100 }
  });
  assert.equal(blockOf(denied), "deny");
});

test("confirmed verifier grants a single-use attachment sequence", () => {
  const context = fixture();
  activate(context);
  registerManifest(context, [{ business_key: "acme", business_name: "Acme", payment_ids: ["pay-1"] }]);
  const researchAssignment = researcherAssignment();
  run(context, "pre-tool", {
    hook_event_name: "PreToolUse", tool_name: "Agent",
    tool_input: { subagent_type: RESEARCHER, prompt: fenced(researchAssignment) }
  });
  run(context, "post-tool", {
    hook_event_name: "PostToolUse", tool_name: "Agent",
    tool_input: { subagent_type: RESEARCHER, prompt: fenced(researchAssignment) },
    tool_response: { content: fenced(researcherResult()) }
  });
  const verifyAssignment = verifierAssignment();
  run(context, "pre-tool", {
    hook_event_name: "PreToolUse", tool_name: "Agent",
    tool_input: { subagent_type: VERIFIER, prompt: fenced(verifyAssignment) }
  });
  run(context, "post-tool", {
    hook_event_name: "PostToolUse", tool_name: "Agent",
    tool_input: { subagent_type: VERIFIER, prompt: fenced(verifyAssignment) },
    tool_response: { content: fenced(verifierResult()) }
  });
  const allowed = run(context, "pre-tool", {
    hook_event_name: "PreToolUse",
    tool_name: "mcp__qonto__request_attachment_upload",
    tool_input: { file_name: "acme.pdf", content_type: "application/pdf", size_bytes: 100 }
  });
  assert.equal(blockOf(allowed), "defer");
  run(context, "post-tool", {
    hook_event_name: "PostToolUse",
    tool_name: "mcp__qonto__request_attachment_upload",
    tool_input: { file_name: "acme.pdf", content_type: "application/pdf", size_bytes: 100 },
    tool_response: { upload_url: "redacted", blob_ref: "blob-1" }
  });
  const uploadAllowed = run(context, "pre-tool", {
    hook_event_name: "PreToolUse",
    tool_name: "mcp__qonto__upload_attachment",
    tool_input: { blob_ref: "blob-1", target: "transaction", transaction_id: "pay-1", idempotency_key: "key-1" }
  });
  assert.equal(uploadAllowed, undefined);
  run(context, "post-tool", {
    hook_event_name: "PostToolUse",
    tool_name: "mcp__qonto__upload_attachment",
    tool_input: { blob_ref: "blob-1", target: "transaction", transaction_id: "pay-1", idempotency_key: "key-1" },
    tool_response: { attachment_id: "attachment-1" }
  });
  assert.equal(Object.values(state(context).authorizations)[0].status, "consumed");
});

test("state and database tampering is denied on the main thread", () => {
  const context = fixture();
  activate(context);
  const result = run(context, "pre-tool", {
    hook_event_name: "PreToolUse",
    tool_name: "Bash",
    tool_input: { command: "sqlite3 qonto-reconciliation.db 'delete from payments'" }
  });
  assert.equal(blockOf(result), "deny");
  assert.match(result.hookSpecificOutput.permissionDecisionReason, /hook-owned/i);
});

test("Stop blocks undelegated suppliers once and honors stop_hook_active", () => {
  const context = fixture();
  activate(context);
  registerManifest(context, [{ business_key: "acme", business_name: "Acme", payment_ids: ["pay-1"] }]);
  const first = run(context, "stop", {
    hook_event_name: "Stop", stop_hook_active: false, last_assistant_message: "Done"
  });
  assert.equal(first.decision, "block");
  assert.match(first.reason, /no researcher assignment/);
  const second = run(context, "stop", {
    hook_event_name: "Stop", stop_hook_active: true, last_assistant_message: "Done"
  });
  assert.equal(second, undefined);
});

test("expired active state fails open", () => {
  const context = fixture();
  activate(context);
  const current = state(context);
  current.activatedAt = "2020-01-01T00:00:00.000Z";
  fs.writeFileSync(path.join(context.root, "runtime", "current", "state.json"), JSON.stringify(current));
  const result = run(context, "pre-tool", {
    hook_event_name: "PreToolUse", tool_name: "mcp__mailbridge__execute-request", tool_input: {}
  });
  assert.equal(result, undefined);
});

test("dry-run invocation sets state.dryRun", () => {
  const context = fixture();
  run(context, "activate", {
    hook_event_name: "UserPromptSubmit",
    prompt: "/qonto-reconciliation:qonto-reconciliation dry last 7 days"
  });
  assert.equal(state(context).dryRun, true);
});

test("dry mode consumes a confirmed authorization as simulated and marks the supplier terminal without uploading", () => {
  const context = fixture();
  run(context, "activate", {
    hook_event_name: "UserPromptSubmit",
    prompt: "/qonto-reconciliation:qonto-reconciliation dry"
  });
  registerManifest(context, [{ business_key: "acme", business_name: "Acme", payment_ids: ["pay-1"] }]);
  const researchAssignment = researcherAssignment();
  run(context, "pre-tool", {
    hook_event_name: "PreToolUse", tool_name: "Agent",
    tool_input: { subagent_type: RESEARCHER, prompt: fenced(researchAssignment) }
  });
  run(context, "post-tool", {
    hook_event_name: "PostToolUse", tool_name: "Agent",
    tool_input: { subagent_type: RESEARCHER, prompt: fenced(researchAssignment) },
    tool_response: { content: fenced(researcherResult()) }
  });
  const verifyAssignment = verifierAssignment();
  run(context, "pre-tool", {
    hook_event_name: "PreToolUse", tool_name: "Agent",
    tool_input: { subagent_type: VERIFIER, prompt: fenced(verifyAssignment) }
  });
  run(context, "post-tool", {
    hook_event_name: "PostToolUse", tool_name: "Agent",
    tool_input: { subagent_type: VERIFIER, prompt: fenced(verifyAssignment) },
    tool_response: { content: fenced(verifierResult()) }
  });
  const denied = run(context, "pre-tool", {
    hook_event_name: "PreToolUse",
    tool_name: "mcp__qonto__request_attachment_upload",
    tool_input: { file_name: "acme.pdf", content_type: "application/pdf", size_bytes: 100 }
  });
  assert.equal(blockOf(denied), "deny");
  assert.match(denied.hookSpecificOutput.permissionDecisionReason, /simulated/i);
  const after = state(context);
  assert.equal(Object.values(after.authorizations)[0].status, "consumed");
  assert.equal(Object.values(after.authorizations)[0].simulated, true);
  assert.equal(Object.values(after.uploadSequences)[0].status, "simulated");
  assert.equal(after.manifest.acme.terminal, true);
});

test("dry run reaches close-run cleanly with no real upload", () => {
  const context = fixture();
  run(context, "activate", {
    hook_event_name: "UserPromptSubmit",
    prompt: "/qonto-reconciliation:qonto-reconciliation dry"
  });
  registerManifest(context, [{ business_key: "acme", business_name: "Acme", payment_ids: ["pay-1"] }]);
  const researchAssignment = researcherAssignment();
  run(context, "pre-tool", {
    hook_event_name: "PreToolUse", tool_name: "Agent",
    tool_input: { subagent_type: RESEARCHER, prompt: fenced(researchAssignment) }
  });
  run(context, "post-tool", {
    hook_event_name: "PostToolUse", tool_name: "Agent",
    tool_input: { subagent_type: RESEARCHER, prompt: fenced(researchAssignment) },
    tool_response: { content: fenced(researcherResult()) }
  });
  const verifyAssignment = verifierAssignment();
  run(context, "pre-tool", {
    hook_event_name: "PreToolUse", tool_name: "Agent",
    tool_input: { subagent_type: VERIFIER, prompt: fenced(verifyAssignment) }
  });
  run(context, "post-tool", {
    hook_event_name: "PostToolUse", tool_name: "Agent",
    tool_input: { subagent_type: VERIFIER, prompt: fenced(verifyAssignment) },
    tool_response: { content: fenced(verifierResult()) }
  });
  run(context, "pre-tool", {
    hook_event_name: "PreToolUse",
    tool_name: "mcp__qonto__request_attachment_upload",
    tool_input: { file_name: "acme.pdf", content_type: "application/pdf", size_bytes: 100 }
  });
  const stopped = run(context, "stop", {
    hook_event_name: "Stop", stop_hook_active: false, last_assistant_message: "Dry run done"
  });
  assert.equal(stopped.decision, "block");
  run(context, "close-run");
  const clean = run(context, "stop", {
    hook_event_name: "Stop", stop_hook_active: true, last_assistant_message: "Dry run done"
  });
  assert.equal(clean, undefined);
});
