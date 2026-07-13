#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");

const RESEARCHER = "qonto-reconciliation:qonto-reconciliation-researcher";
const VERIFIER = "qonto-reconciliation:qonto-reconciliation-verifier";
const RESULT_FENCE = /```qonto-reconciliation-result\s*\r?\n([\s\S]*?)\r?\n```/g;
const MAX_ACTIVE_AGE_MS = 24 * 60 * 60 * 1000;

function readInput() {
  const raw = fs.readFileSync(0, "utf8");
  return JSON.parse(raw || "{}");
}

function dataDir() {
  return process.env.CLAUDE_PLUGIN_DATA || path.join(process.env.HOME || process.env.USERPROFILE || ".", ".claude", "qonto-reconciliation-data");
}

function statePaths() {
  // Single global runtime state, not scoped per session_id. This trades away
  // isolation between concurrent sessions for simplicity — the operator is
  // responsible for not running the reconciliation skill from more than one
  // session at a time.
  const runtimeDir = path.join(dataDir(), "runtime", "current");
  return {
    dataDir: dataDir(),
    dbPath: path.join(dataDir(), "qonto-reconciliation.db"),
    runtimeDir,
    statePath: path.join(runtimeDir, "state.json"),
    logPath: path.join(runtimeDir, "harness.log")
  };
}

function defaultState() {
  return {
    schemaVersion: 1,
    active: false,
    activatedAt: null,
    updatedAt: null,
    phase: "inactive",
    promptId: null,
    capabilities: {},
    manifest: {},
    assignments: {},
    candidates: {},
    verifications: {},
    authorizations: {},
    uploadSequences: {},
    runClosed: false,
    dryRun: false,
    violations: []
  };
}

function normalizeState(value) {
  const base = defaultState();
  if (!value || typeof value !== "object" || Array.isArray(value)) return base;
  const state = { ...base, ...value };
  for (const key of ["capabilities", "manifest", "assignments", "candidates", "verifications", "authorizations", "uploadSequences"]) {
    if (!state[key] || typeof state[key] !== "object" || Array.isArray(state[key])) state[key] = {};
  }
  if (!Array.isArray(state.violations)) state.violations = [];
  if (state.active && state.activatedAt) {
    const age = Date.now() - Date.parse(state.activatedAt);
    if (!Number.isFinite(age) || age >= MAX_ACTIVE_AGE_MS) {
      state.active = false;
      state.phase = "expired";
    }
  }
  return state;
}

function loadState() {
  const paths = statePaths();
  try {
    return { state: normalizeState(JSON.parse(fs.readFileSync(paths.statePath, "utf8"))), paths };
  } catch (_) {
    return { state: defaultState(), paths };
  }
}

function saveState(state) {
  const paths = statePaths();
  fs.mkdirSync(paths.runtimeDir, { recursive: true });
  state.updatedAt = new Date().toISOString();
  const temp = `${paths.statePath}.${process.pid}.tmp`;
  fs.writeFileSync(temp, `${JSON.stringify(state, null, 2)}\n`, { mode: 0o600 });
  fs.renameSync(temp, paths.statePath);
}

function logEvent(input, message, details) {
  const paths = statePaths();
  try {
    fs.mkdirSync(paths.runtimeDir, { recursive: true });
    const entry = { at: new Date().toISOString(), event: input.hook_event_name, message, details: details || null };
    fs.appendFileSync(paths.logPath, `${JSON.stringify(entry)}\n`, { mode: 0o600 });
  } catch (_) {
    // Logging must never brick an unrelated session.
  }
}

function output(value) {
  if (value !== undefined) process.stdout.write(JSON.stringify(value));
}

function preToolDecision(decision, reason, additionalContext, updatedInput) {
  const hookSpecificOutput = {
    hookEventName: "PreToolUse",
    permissionDecision: decision,
    permissionDecisionReason: reason
  };
  if (additionalContext) hookSpecificOutput.additionalContext = additionalContext;
  if (updatedInput) hookSpecificOutput.updatedInput = updatedInput;
  return { hookSpecificOutput };
}

function deny(reason) {
  return preToolDecision("deny", reason);
}

function addContext(eventName, text) {
  return { hookSpecificOutput: { hookEventName: eventName, additionalContext: text } };
}

function block(reason) {
  return { decision: "block", reason };
}

function isSubagent(input) {
  return Boolean(input.agent_id);
}

function lowerTool(input) {
  return String(input.tool_name || "").toLowerCase();
}

function isAgentTool(input) {
  return /(^|__)agent$/.test(lowerTool(input)) || lowerTool(input) === "agent";
}

function connectorKey(input) {
  const tool = String(input.tool_name || "");
  if (!/^mcp__/i.test(tool)) return null;
  const rest = tool.slice(5);
  const separator = rest.indexOf("__");
  if (separator < 1) return null;
  const server = rest.slice(0, separator);
  if (/qonto/i.test(server)) return null;
  return canonical(server) || null;
}

function isConnectorTool(input) {
  return Boolean(connectorKey(input));
}

function isToolDiscovery(input) {
  return ["toolsearch", "listmcpresourcestool", "readmcpresourcetool", "readmcpresourcedirtool"].includes(lowerTool(input));
}

function isQontoTool(input, suffix) {
  const tool = lowerTool(input);
  return tool.includes("qonto") && (!suffix || tool.endsWith(suffix.toLowerCase()));
}

function isShellTool(input) {
  return ["bash", "powershell"].includes(lowerTool(input));
}

function isFileTool(input) {
  return ["read", "write", "edit", "glob", "grep", "notebookedit"].includes(lowerTool(input));
}

function canonical(value) {
  return String(value || "").trim().toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

function stringArray(value) {
  if (!Array.isArray(value)) return [];
  return [...new Set(value.map(item => String(item).trim()).filter(Boolean))];
}

function deepStrings(value, result = []) {
  if (typeof value === "string") result.push(value);
  else if (Array.isArray(value)) value.forEach(item => deepStrings(item, result));
  else if (value && typeof value === "object") Object.values(value).forEach(item => deepStrings(item, result));
  return result;
}

function stableHash(value) {
  let hash = 2166136261;
  for (const character of String(value)) {
    hash ^= character.charCodeAt(0);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0).toString(36);
}

function extractResultBlocks(text) {
  const results = [];
  RESULT_FENCE.lastIndex = 0;
  for (const match of String(text || "").matchAll(RESULT_FENCE)) {
    try {
      results.push(JSON.parse(match[1]));
    } catch (error) {
      results.push({ __parseError: error.message });
    }
  }
  return results;
}

function parseAgentPrompt(toolInput) {
  const prompt = String(toolInput && toolInput.prompt || "");
  const blocks = extractResultBlocks(prompt);
  const assignment = blocks.find(item => item && item.kind === "researcher_assignment");
  const verification = blocks.find(item => item && item.kind === "verifier_assignment");
  return { prompt, assignment, verification };
}

function validateResearcherAssignment(value) {
  const errors = [];
  if (!value || typeof value !== "object") return ["missing researcher_assignment JSON block"];
  if (!String(value.assignment_id || "").trim()) errors.push("assignment_id is required");
  if (!String(value.business_key || "").trim()) errors.push("business_key is required");
  if (!String(value.business_name || "").trim()) errors.push("business_name is required");
  if (!stringArray(value.payment_ids).length) errors.push("payment_ids must be a non-empty array");
  if (stringArray(value.business_keys).length > 1) errors.push("one researcher assignment may cover exactly one business");
  if (!value.capability_manifest || typeof value.capability_manifest !== "object") errors.push("capability_manifest is required");
  return errors;
}

function validateVerifierAssignment(value) {
  const errors = [];
  if (!value || typeof value !== "object") return ["missing verifier_assignment JSON block"];
  if (!String(value.verification_id || "").trim()) errors.push("verification_id is required");
  if (!String(value.candidate_id || "").trim()) errors.push("candidate_id is required");
  if (!stringArray(value.payment_ids).length) errors.push("payment_ids must be a non-empty array");
  if (!String(value.document_location || "").trim()) errors.push("document_location is required");
  return errors;
}

function validateResearcherResult(value, assignment) {
  const errors = [];
  if (!value || value.__parseError) return [value && value.__parseError ? `invalid result JSON: ${value.__parseError}` : "missing result"];
  if (value.kind !== "researcher_result") errors.push("kind must be researcher_result");
  if (assignment && value.assignment_id !== assignment.assignment_id) errors.push("assignment_id does not match");
  if (assignment && canonical(value.business_key) !== canonical(assignment.business_key)) errors.push("business_key does not match assigned supplier");
  const expectedPayments = assignment ? stringArray(assignment.payment_ids).sort() : [];
  const actualPayments = stringArray(value.payment_ids).sort();
  if (expectedPayments.length && JSON.stringify(expectedPayments) !== JSON.stringify(actualPayments)) errors.push("payment_ids must exactly match the assignment");
  if (!Array.isArray(value.channels_attempted)) errors.push("channels_attempted must be an array");
  if (!Array.isArray(value.candidates)) errors.push("candidates must be an array");
  if (!Array.isArray(value.blockers)) errors.push("blockers must be an array");
  if (!Array.isArray(value.drafts)) errors.push("drafts must be an array");
  for (const candidate of Array.isArray(value.candidates) ? value.candidates : []) {
    if (!String(candidate.candidate_id || "").trim()) errors.push("every candidate needs candidate_id");
    if (!String(candidate.document_location || "").trim()) errors.push("every candidate needs document_location");
    if (!stringArray(candidate.payment_ids).length) errors.push("every candidate needs payment_ids");
  }
  for (const blockerValue of Array.isArray(value.blockers) ? value.blockers : []) {
    if (blockerValue.blocker_type === "missing_capability") {
      const evidence = blockerValue.probe_evidence;
      if (!evidence || !String(evidence.tool || "").trim() || !String(evidence.outcome || "").trim() || !String(evidence.observed_at || "").trim()) {
        errors.push("missing_capability requires tool/outcome/observed_at probe_evidence");
      }
    }
  }
  if (![value.candidates, value.blockers, value.drafts].some(items => Array.isArray(items) && items.length)) {
    errors.push("result must contain a candidate, typed blocker, or draft");
  }
  return errors;
}

function validateVerifierResult(value, assignment) {
  const errors = [];
  if (!value || value.__parseError) return [value && value.__parseError ? `invalid result JSON: ${value.__parseError}` : "missing result"];
  if (value.kind !== "verifier_result") errors.push("kind must be verifier_result");
  if (assignment && value.verification_id !== assignment.verification_id) errors.push("verification_id does not match");
  if (assignment && value.candidate_id !== assignment.candidate_id) errors.push("candidate_id does not match");
  const expectedPayments = assignment ? stringArray(assignment.payment_ids).sort() : [];
  const actualPayments = stringArray(value.payment_ids).sort();
  if (expectedPayments.length && JSON.stringify(expectedPayments) !== JSON.stringify(actualPayments)) errors.push("payment_ids must exactly match the verification assignment");
  if (!["confirmed", "rejected", "needs_human_review"].includes(value.verdict)) errors.push("verdict must be confirmed, rejected, or needs_human_review");
  if (!value.evidence || typeof value.evidence !== "object") errors.push("evidence is required");
  else if (!Array.isArray(value.evidence.document_fields_read) || !value.evidence.document_fields_read.length) errors.push("evidence.document_fields_read must identify actual document content inspected");
  if (!String(value.reason || "").trim()) errors.push("reason is required");
  return errors;
}

function isConnectorCapabilityProbe(input) {
  if (!isConnectorTool(input)) return false;
  const tool = lowerTool(input);
  const kind = probeKind(input);
  if (["discovery", "schema"].includes(kind)) return true;
  const payload = `${tool} ${deepStrings(input.tool_input).join(" ")}`.toLowerCase();
  return /(?:list|get|inspect|discover|capabilit|account|connection|provider|server.variable)/.test(payload)
    && !/(search|download|attachment.get|invoice|receipt|factura|document)/.test(payload);
}

function capabilityFamily(input) {
  const tool = lowerTool(input);
  if (/mail|gmail|outlook|email/.test(tool)) return "mail";
  if (/browser|playwright|chrome|puppeteer/.test(tool)) return "browser";
  if (/message|whatsapp|linkedin|instagram|slack/.test(tool)) return "messaging";
  if (isToolDiscovery(input)) return "tool-discovery";
  return connectorKey(input);
}

function probeKind(input) {
  const tool = lowerTool(input);
  if (tool.endsWith("search-endpoints") || tool.endsWith("list-endpoints") || tool.endsWith("get-server-variables") || tool.includes("toolsearch")) return "discovery";
  if (tool.endsWith("get-endpoint")) return "schema";
  return "capability";
}

function toolSucceeded(input) {
  const response = input.tool_response;
  if (response === undefined || response === null) return false;
  if (response && typeof response === "object") {
    if (response.isError === true || response.error || response.status === "error") return false;
  }
  const text = deepStrings(response).join("\n").toLowerCase();
  return !/(tool error|authentication required|unauthorized|forbidden|connection failed|timed out)/.test(text);
}

function manifestSupplier(state, businessKey) {
  return state.manifest[canonical(businessKey)];
}

function unresolvedSupplierKeys(state) {
  return Object.entries(state.manifest)
    .filter(([, supplier]) => supplier && supplier.terminal !== true)
    .map(([key]) => key);
}

function pendingCandidates(state) {
  const verifiedCandidateIds = new Set(Object.values(state.verifications).map(item => item && item.candidate_id).filter(Boolean));
  return Object.values(state.candidates).filter(candidate => candidate && !candidate.terminal && !verifiedCandidateIds.has(candidate.candidate_id));
}

function incompleteConfirmed(state) {
  return Object.values(state.authorizations).filter(auth => auth && auth.verdict === "confirmed" && auth.status !== "consumed");
}

function looksLikeRuntimePath(value, paths) {
  const haystack = deepStrings(value).join("\n").replace(/\\/g, "/").toLowerCase();
  const runtime = paths.runtimeDir.replace(/\\/g, "/").toLowerCase();
  const db = paths.dbPath.replace(/\\/g, "/").toLowerCase();
  return haystack.includes(runtime) || haystack.includes(db) || haystack.includes("qonto-reconciliation.db") || haystack.includes("active-run.marker") || haystack.includes("state.json");
}

function isMainResearchTool(input) {
  if (isConnectorTool(input) && !isQontoTool(input)) {
    if (isConnectorCapabilityProbe(input)) return false;
    const payload = `${lowerTool(input)} ${deepStrings(input.tool_input).join(" ")}`.toLowerCase();
    return /(search|query|find|download|fetch|message|mail|email|attachment|invoice|receipt|factura|document|browser|navigate|page)/.test(payload);
  }
  const tool = lowerTool(input);
  if (/gmail|outlook|email|mail|browser|playwright|chrome|puppeteer|webfetch|websearch|google_drive|messag|whatsapp|linkedin|instagram/.test(tool)) return true;
  if (isFileTool(input)) {
    const payload = deepStrings(input.tool_input).join(" ").toLowerCase();
    return /invoice|receipt|factura|justific|attachment|download|pdf/.test(payload);
  }
  if (isShellTool(input)) {
    const command = String(input.tool_input && input.tool_input.command || "").toLowerCase();
    return /(curl|wget|pdftotext|pdfinfo|ocr|tesseract|downloads|receipt|invoice|factura)/.test(command);
  }
  if (isQontoTool(input)) {
    return /(invoice|quote|attachment|statement|supplier)/.test(tool) && !tool.endsWith("list_transaction_attachments");
  }
  return false;
}

function resetRun(input, reason) {
  const { paths } = loadState();
  try {
    fs.rmSync(paths.runtimeDir, { recursive: true, force: true });
  } catch (_) {
    const reset = defaultState();
    reset.phase = "reset";
    saveState(reset);
  }
  logEvent(input, "run-reset", { reason: reason || "manual reset" });
}

function commandInvoked(prompt, commandName) {
  // A genuine slash-command dispatch is either wrapped in a <command-name> tag,
  // or appears as literal leading text at the very start of the prompt. Matching
  // the command name anywhere inside the prompt body (the old behavior) false-fires
  // whenever the user pastes or quotes the command name in an unrelated message.
  const escaped = commandName.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  if (new RegExp(`<command-name>\\/?${escaped}<\\/command-name>`, "i").test(prompt)) return true;
  return new RegExp(`^\\/?${escaped}(?:\\s|$)`, "i").test(String(prompt).trim());
}

function activate(input) {
  const prompt = String(input.prompt || "");
  const resetRequested = commandInvoked(prompt, "qonto-reconciliation:qonto-reconciliation-reset")
    || commandInvoked(prompt, "qonto-reconciliation:reset");
  if (resetRequested) {
    resetRun(input, "explicit reset command");
    output(addContext("UserPromptSubmit", "The reconciliation runtime state was reset. The persistent reconciliation database was preserved. A new reconciliation invocation will start with a clean harness state."));
    return;
  }
  const invoked = commandInvoked(prompt, "qonto-reconciliation:qonto-reconciliation");
  if (!invoked) return;
  const dryRun = /(?:^|\s)(--dry|dry[- ]?run|dryrun|dry)\b/i.test(prompt);
  const fresh = defaultState();
  fresh.active = true;
  fresh.activatedAt = new Date().toISOString();
  fresh.phase = "capability_discovery";
  fresh.promptId = input.prompt_id || null;
  fresh.dryRun = dryRun;
  saveState(fresh);
  const modeLine = dryRun
    ? " DRY RUN MODE ACTIVE: run every step identically (probe, delegate, verify) but never perform the Qonto upload — record each confirmed attachment as a simulated match instead."
    : "";
  output(addContext("UserPromptSubmit", `Reconciliation harness active. Follow the enforced phase order: probe capabilities, discover and group unresolved payments, delegate one researcher per supplier, delegate every candidate to a verifier, then attach only with a matching confirmed verdict.${modeLine}`));
}

function gateAgent(input, state) {
  const toolInput = input.tool_input || {};
  const agentType = String(toolInput.subagent_type || toolInput.agent_type || "");
  const { assignment, verification } = parseAgentPrompt(toolInput);
  if (agentType === RESEARCHER) {
    const errors = validateResearcherAssignment(assignment);
    if (errors.length) return deny(`Researcher delegation denied: ${errors.join("; ")}. Include a fenced qonto-reconciliation-result JSON researcher_assignment block.`);
    const key = canonical(assignment.business_key);
    const manifest = manifestSupplier(state, key);
    if (!manifest) return deny(`Researcher delegation denied: business_key ${assignment.business_key} is not in the finalized unresolved-supplier manifest.`);
    const expected = stringArray(manifest.payment_ids).sort();
    const actual = stringArray(assignment.payment_ids).sort();
    if (JSON.stringify(expected) !== JSON.stringify(actual)) return deny(`Researcher delegation denied: payment_ids must exactly match the manifest for ${assignment.business_name}.`);
    if (Object.values(state.assignments).some(item => item && item.business_key === key && !item.retry_allowed)) {
      return deny(`Researcher delegation denied: ${assignment.business_name} already has an assignment. Use the existing result unless a verifier rejection explicitly opened one retry.`);
    }
    state.phase = "delegation";
    state.assignments[assignment.assignment_id] = {
      ...assignment,
      business_key: key,
      status: "requested",
      requestedAt: new Date().toISOString(),
      agent_id: null,
      retry_allowed: false
    };
    saveState(state);
    return;
  }
  if (agentType === VERIFIER) {
    const errors = validateVerifierAssignment(verification);
    if (errors.length) return deny(`Verifier delegation denied: ${errors.join("; ")}. Include a fenced qonto-reconciliation-result JSON verifier_assignment block.`);
    const candidate = state.candidates[verification.candidate_id];
    if (!candidate) return deny(`Verifier delegation denied: candidate_id ${verification.candidate_id} was not produced by a completed researcher assignment.`);
    const expected = stringArray(candidate.payment_ids).sort();
    const actual = stringArray(verification.payment_ids).sort();
    if (JSON.stringify(expected) !== JSON.stringify(actual)) return deny("Verifier delegation denied: payment_ids must exactly match the candidate handoff.");
    state.phase = "verification";
    state.verifications[verification.verification_id] = {
      ...verification,
      status: "requested",
      requestedAt: new Date().toISOString(),
      agent_id: null
    };
    saveState(state);
    return;
  }
  return deny(`During reconciliation, Agent calls must use exactly ${RESEARCHER} or ${VERIFIER}. The main thread must orchestrate rather than delegate this workflow to a generic agent.`);
}

function findAuthorization(state, paymentIds, candidateId) {
  const expected = stringArray(paymentIds).sort();
  return Object.values(state.authorizations).find(auth => {
    if (!auth || auth.status === "consumed" || auth.verdict !== "confirmed") return false;
    if (candidateId && auth.candidate_id !== candidateId) return false;
    return JSON.stringify(stringArray(auth.payment_ids).sort()) === JSON.stringify(expected);
  });
}

function gateAttachment(input, state) {
  if (isSubagent(input)) return deny("Attachment writes are orchestrator-only; researcher and verifier agents may never call Qonto upload tools.");
  const toolInput = input.tool_input || {};
  if (state.dryRun) {
    if (isQontoTool(input, "request_attachment_upload")) {
      const explicitCandidateId = String(toolInput.candidate_id || "");
      const explicitPaymentIds = stringArray(toolInput.payment_ids || (toolInput.transaction_id ? [toolInput.transaction_id] : []));
      let auth = findAuthorization(state, explicitPaymentIds, explicitCandidateId || null);
      if (!auth) {
        const available = Object.values(state.authorizations).filter(item => item && item.verdict === "confirmed" && item.status === "available");
        if (available.length === 1) auth = available[0];
      }
      if (!auth) return deny("Dry-run attachment denied: no unique, unconsumed confirmed verifier authorization is available. Delegate the candidate to the verifier first.");
      const simulatedAt = new Date().toISOString();
      auth.status = "consumed";
      auth.consumedAt = simulatedAt;
      auth.simulated = true;
      state.uploadSequences[auth.authorization_id] = {
        authorization_id: auth.authorization_id,
        candidate_id: auth.candidate_id,
        payment_ids: auth.payment_ids,
        status: "simulated",
        simulated: true,
        startedAt: simulatedAt,
        completedAt: simulatedAt
      };
      for (const paymentId of auth.payment_ids) {
        for (const supplier of Object.values(state.manifest)) {
          if (supplier && Array.isArray(supplier.payment_ids) && supplier.payment_ids.includes(paymentId)) supplier.terminal = true;
        }
      }
      state.phase = "attachment";
      saveState(state);
      return deny(`Dry-run mode: the Qonto upload was not performed. Record a SIMULATED match for candidate ${auth.candidate_id} (payments ${auth.payment_ids.join(", ")}) — leave matched_attachment_id null and mark the supplier resolved. Continue with the remaining confirmed candidates or close the run.`);
    }
    if (isQontoTool(input, "upload_attachment")) {
      return deny("Dry-run mode: the final Qonto upload_attachment call is suppressed and must not be performed.");
    }
    return;
  }
  if (isQontoTool(input, "request_attachment_upload")) {
    const explicitCandidateId = String(toolInput.candidate_id || "");
    const explicitPaymentIds = stringArray(toolInput.payment_ids || (toolInput.transaction_id ? [toolInput.transaction_id] : []));
    let auth = findAuthorization(state, explicitPaymentIds, explicitCandidateId || null);
    if (!auth) {
      const available = Object.values(state.authorizations).filter(item => item && item.verdict === "confirmed" && item.status === "available");
      if (available.length === 1) auth = available[0];
    }
    if (!auth) return deny("Attachment request denied: no unique, unconsumed confirmed verifier authorization is available. Delegate the candidate to the verifier first.");
    state.phase = "attachment";
    state.uploadSequences[auth.authorization_id] = {
      authorization_id: auth.authorization_id,
      candidate_id: auth.candidate_id,
      payment_ids: auth.payment_ids,
      status: "requesting_upload",
      startedAt: new Date().toISOString()
    };
    saveState(state);
    const sanitizedInput = { ...toolInput };
    delete sanitizedInput.candidate_id;
    delete sanitizedInput.payment_ids;
    return preToolDecision("defer", "Confirmed verifier authorization reserved for this upload request.", null, sanitizedInput);
  }
  if (isQontoTool(input, "upload_attachment")) {
    const transactionId = String(toolInput.transaction_id || "");
    const sequence = Object.values(state.uploadSequences).find(item => item && item.status === "upload_requested" && !item.simulated && (!transactionId || item.payment_ids.includes(transactionId)));
    if (!sequence) return deny("Attachment upload denied: no confirmed, in-progress upload sequence matches this transaction.");
  }
}

function preTool(input) {
  const { state, paths } = loadState();
  if (!state.active) return;
  if ((isShellTool(input) || isFileTool(input)) && !isSubagent(input) && looksLikeRuntimePath(input.tool_input, paths)) {
    output(deny("Reconciliation harness state and database are hook-owned while a run is active. Use the orchestrator protocol instead of editing or querying them directly."));
    return;
  }
  if (isAgentTool(input) && !isSubagent(input)) {
    const decision = gateAgent(input, state);
    output(decision);
    return;
  }
  if (isQontoTool(input, "request_attachment_upload") || isQontoTool(input, "upload_attachment")) {
    const decision = gateAttachment(input, state);
    output(decision);
    return;
  }
  if (!isSubagent(input) && isMainResearchTool(input)) {
    output(deny("The reconciliation main thread is orchestrator-only. Supplier email/message/portal/local-document/Qonto-native research must be delegated to the assigned researcher for that single business. Capability discovery probes remain allowed before delegation."));
    return;
  }
}

function recordCapability(input, state) {
  const family = capabilityFamily(input);
  if (!family || isSubagent(input)) return false;
  const success = toolSucceeded(input);
  const record = state.capabilities[family] || { observations: [] };
  record.observations.push({
    tool: input.tool_name,
    kind: probeKind(input),
    outcome: success ? "succeeded" : "failed",
    observed_at: new Date().toISOString(),
    evidence_hash: stableHash(JSON.stringify(input.tool_response))
  });
  record.last_verified_at = new Date().toISOString();
  record.status = success ? "available" : (record.status || "probe_failed");
  state.capabilities[family] = record;
  if (success && isConnectorCapabilityProbe(input)) record.capability_proven = true;
  return true;
}

function recordQontoDiscovery(input, state) {
  if (isSubagent(input) || !isQontoTool(input)) return false;
  const tool = lowerTool(input);
  if (!tool.endsWith("list_transactions") && !tool.endsWith("get_transaction")) return false;
  if (toolSucceeded(input)) {
    state.phase = "transaction_discovery";
    state.discovery = {
      response_hash: stableHash(JSON.stringify(input.tool_response)),
      observed_at: new Date().toISOString()
    };
    return true;
  }
  return false;
}

function recordUpload(input, state) {
  if (!isQontoTool(input) || isSubagent(input)) return false;
  if (state.dryRun) {
    // Dry mode denies upload tools before they execute, so no PostToolUse is expected.
    // Be defensive: never mutate a simulated sequence as if a real upload happened.
    return false;
  }
  if (isQontoTool(input, "request_attachment_upload")) {
    const sequence = Object.values(state.uploadSequences).find(item => item && item.status === "requesting_upload" && !item.simulated);
    if (!sequence) return false;
    if (toolSucceeded(input)) {
      sequence.status = "upload_requested";
      sequence.request_result_hash = stableHash(JSON.stringify(input.tool_response));
    } else {
      sequence.status = "request_failed";
    }
    return true;
  }
  if (isQontoTool(input, "upload_attachment")) {
    const transactionId = String(input.tool_input && input.tool_input.transaction_id || "");
    const sequence = Object.values(state.uploadSequences).find(item => item && item.status === "upload_requested" && !item.simulated && (!transactionId || item.payment_ids.includes(transactionId)));
    if (!sequence) return false;
    if (toolSucceeded(input)) {
      sequence.status = "attached";
      sequence.completedAt = new Date().toISOString();
      sequence.result_hash = stableHash(JSON.stringify(input.tool_response));
      const auth = state.authorizations[sequence.authorization_id];
      if (auth) {
        auth.status = "consumed";
        auth.consumedAt = sequence.completedAt;
      }
      for (const paymentId of sequence.payment_ids) {
        for (const supplier of Object.values(state.manifest)) {
          if (supplier && Array.isArray(supplier.payment_ids) && supplier.payment_ids.includes(paymentId)) supplier.terminal = true;
        }
      }
    } else {
      sequence.status = "attach_failed";
    }
    return true;
  }
  return false;
}

function recordAgentResponse(input, state) {
  if (!isAgentTool(input) || isSubagent(input)) return false;
  const { assignment, verification } = parseAgentPrompt(input.tool_input || {});
  const text = deepStrings(input.tool_response).join("\n");
  const results = extractResultBlocks(text);
  if (assignment) {
    const result = results.find(item => item && item.kind === "researcher_result");
    const errors = validateResearcherResult(result, assignment);
    const record = state.assignments[assignment.assignment_id] || { ...assignment, business_key: canonical(assignment.business_key) };
    if (errors.length) {
      record.status = "invalid_result";
      record.errors = errors;
    } else {
      record.status = "completed";
      record.completedAt = new Date().toISOString();
      record.result_hash = stableHash(JSON.stringify(result));
      for (const candidate of result.candidates) {
        state.candidates[candidate.candidate_id] = {
          ...candidate,
          assignment_id: assignment.assignment_id,
          business_key: canonical(assignment.business_key),
          terminal: false,
          createdAt: new Date().toISOString()
        };
      }
      const supplier = manifestSupplier(state, assignment.business_key);
      if (supplier && !result.candidates.length) supplier.terminal = true;
    }
    state.assignments[assignment.assignment_id] = record;
    return true;
  }
  if (verification) {
    const result = results.find(item => item && item.kind === "verifier_result");
    const errors = validateVerifierResult(result, verification);
    const record = state.verifications[verification.verification_id] || { ...verification };
    if (errors.length) {
      record.status = "invalid_result";
      record.errors = errors;
    } else {
      record.status = "completed";
      record.completedAt = new Date().toISOString();
      record.verdict = result.verdict;
      record.result_hash = stableHash(JSON.stringify(result));
      const candidate = state.candidates[verification.candidate_id];
      if (candidate) {
        if (result.verdict === "confirmed") {
          const authorizationId = `auth-${verification.verification_id}`;
          state.authorizations[authorizationId] = {
            authorization_id: authorizationId,
            verification_id: verification.verification_id,
            candidate_id: verification.candidate_id,
            payment_ids: stringArray(verification.payment_ids),
            verdict: "confirmed",
            status: "available",
            createdAt: new Date().toISOString()
          };
        } else {
          candidate.terminal = true;
          candidate.verdict = result.verdict;
          const supplier = manifestSupplier(state, candidate.business_key);
          if (result.verdict === "needs_human_review") {
            // No further automated action is possible; resolve the supplier so the
            // run can close, but flag it so the final report surfaces it for a human.
            if (supplier) {
              supplier.terminal = true;
              supplier.resolution = "needs_human_review";
            }
          } else if (result.verdict === "rejected" && supplier && supplier.terminal !== true) {
            // Allow exactly one fresh researcher assignment for this supplier if no
            // other candidate is still pending or already confirmed.
            const siblingCandidates = Object.values(state.candidates)
              .filter(item => item && canonical(item.business_key) === canonical(candidate.business_key) && item.candidate_id !== candidate.candidate_id);
            const stillLive = siblingCandidates.some(item => !item.terminal)
              || Object.values(state.authorizations).some(auth => auth && auth.verdict === "confirmed" && stringArray(auth.payment_ids).sort().join() === stringArray(supplier.payment_ids).sort().join());
            if (!stillLive) {
              const assignment = state.assignments[candidate.assignment_id];
              if (assignment) assignment.retry_allowed = true;
            }
          }
        }
      }
    }
    state.verifications[verification.verification_id] = record;
    return true;
  }
  return false;
}

function postTool(input) {
  const { state } = loadState();
  if (!state.active) return;
  let changed = false;
  changed = recordCapability(input, state) || changed;
  changed = recordQontoDiscovery(input, state) || changed;
  changed = recordAgentResponse(input, state) || changed;
  changed = recordUpload(input, state) || changed;
  if (changed) saveState(state);
}

function subagentStart(input) {
  const { state } = loadState();
  if (!state.active) return;
  const agentType = String(input.agent_type || "");
  if (agentType === RESEARCHER) {
    const record = Object.values(state.assignments).find(item => item && item.status === "requested" && !item.agent_id);
    if (record) {
      record.agent_id = input.agent_id;
      record.status = "running";
      record.startedAt = new Date().toISOString();
      saveState(state);
    }
    output(addContext("SubagentStart", "You are one supplier's researcher. End with exactly one fenced qonto-reconciliation-result JSON researcher_result matching the assignment IDs. A missing_capability blocker is invalid without concrete, connector-agnostic probe evidence for every relevant connected connector."));
  } else if (agentType === VERIFIER) {
    const record = Object.values(state.verifications).find(item => item && item.status === "requested" && !item.agent_id);
    if (record) {
      record.agent_id = input.agent_id;
      record.status = "running";
      record.startedAt = new Date().toISOString();
      saveState(state);
    }
    output(addContext("SubagentStart", "End with exactly one fenced qonto-reconciliation-result JSON verifier_result matching the verification and candidate IDs. Read actual document content and list document_fields_read; filename-only evidence is invalid."));
  }
}

function subagentStop(input) {
  const { state } = loadState();
  if (!state.active) return;
  if (input.stop_hook_active) return;
  const agentType = String(input.agent_type || "");
  const results = extractResultBlocks(input.last_assistant_message || "");
  if (agentType === RESEARCHER) {
    const assignment = Object.values(state.assignments).find(item => item && item.agent_id === input.agent_id);
    const result = results.find(item => item && item.kind === "researcher_result");
    const errors = validateResearcherResult(result, assignment);
    if (errors.length) output(block(`Researcher handoff is incomplete: ${errors.join("; ")}. Continue and return a valid fenced qonto-reconciliation-result JSON block.`));
  } else if (agentType === VERIFIER) {
    const assignment = Object.values(state.verifications).find(item => item && item.agent_id === input.agent_id);
    const result = results.find(item => item && item.kind === "verifier_result");
    const errors = validateVerifierResult(result, assignment);
    if (errors.length) output(block(`Verifier handoff is incomplete: ${errors.join("; ")}. Continue, inspect the actual document, and return a valid fenced qonto-reconciliation-result JSON block.`));
  }
}

function finalClaimProblems(input, state) {
  const text = String(input.last_assistant_message || "").toLowerCase();
  const problems = [];
  if (/(no|without|missing).{0,35}(mail|email|browser|connector)|(?:mail|email|browser|connector).{0,35}(unavailable|unusable|not available|missing)/s.test(text)) {
    const observations = Object.values(state.capabilities).flatMap(item => item && Array.isArray(item.observations) ? item.observations : []);
    if (!observations.some(item => item.kind === "capability" || item.outcome === "failed")) problems.push("connector unavailability was claimed without recorded connector-agnostic capability probes");
  }
  return problems;
}

function stop(input) {
  const { state } = loadState();
  if (!state.active || input.stop_hook_active) return;
  const problems = [];
  const supplierKeys = unresolvedSupplierKeys(state);
  const assignedKeys = new Set(Object.values(state.assignments).map(item => item && canonical(item.business_key)).filter(Boolean));
  const undelegated = supplierKeys.filter(key => !assignedKeys.has(key));
  if (undelegated.length) problems.push(`${undelegated.length} unresolved supplier(s) have no researcher assignment`);
  const invalidAssignments = Object.values(state.assignments).filter(item => item && ["requested", "running", "invalid_result"].includes(item.status));
  if (invalidAssignments.length) problems.push(`${invalidAssignments.length} researcher assignment(s) are incomplete or invalid`);
  const candidates = pendingCandidates(state);
  if (candidates.length) problems.push(`${candidates.length} candidate document(s) have not been routed to a verifier`);
  const invalidVerifications = Object.values(state.verifications).filter(item => item && ["requested", "running", "invalid_result"].includes(item.status));
  if (invalidVerifications.length) problems.push(`${invalidVerifications.length} verifier assignment(s) are incomplete or invalid`);
  const confirmed = incompleteConfirmed(state);
  if (confirmed.length) problems.push(`${confirmed.length} confirmed attachment authorization(s) remain incomplete`);
  problems.push(...finalClaimProblems(input, state));
  if (!state.runClosed && (Object.keys(state.manifest).length || Object.keys(state.assignments).length || Object.keys(state.candidates).length)) problems.push("the reconciliation run has not been explicitly closed");
  if (problems.length) {
    output(block(`Reconciliation cannot stop yet: ${problems.join("; ")}. Continue with the next legal orchestration step, or mark each item with a valid terminal blocker/review state and close the run.`));
    return;
  }
  state.active = false;
  state.phase = "complete";
  state.runClosed = true;
  saveState(state);
}

function registerManifest(input, value) {
  const { state } = loadState();
  if (!state.active) throw new Error("Cannot register a manifest: no active reconciliation run for this session. Run the /qonto-reconciliation:qonto-reconciliation command first.");
  if (!value || !Array.isArray(value.suppliers)) {
    throw new Error(`register-manifest payload must be an object with a top-level "suppliers" array, got: ${JSON.stringify(value)}`);
  }
  const suppliers = value.suppliers;
  if (!suppliers.length) throw new Error("register-manifest payload's suppliers array must not be empty.");
  const manifest = {};
  for (const supplier of suppliers) {
    const key = canonical(supplier.business_key || supplier.business_name);
    if (!key || !stringArray(supplier.payment_ids).length) throw new Error("Each manifest supplier requires business_key/business_name and payment_ids");
    manifest[key] = {
      business_key: key,
      business_name: String(supplier.business_name || supplier.business_key),
      payment_ids: stringArray(supplier.payment_ids),
      terminal: false
    };
  }
  state.manifest = manifest;
  state.phase = "delegation";
  saveState(state);
}

function closeRun(input) {
  const { state } = loadState();
  if (!state.active) throw new Error("Cannot close a run: no active reconciliation run for this session.");
  if (unresolvedSupplierKeys(state).length || pendingCandidates(state).length || incompleteConfirmed(state).length) {
    throw new Error("Cannot close a run with unresolved suppliers, candidates, or confirmed attachments");
  }
  state.runClosed = true;
  state.phase = "closing";
  saveState(state);
}

function main() {
  const action = process.argv[2];
  let input;
  try {
    input = readInput();
    if (action === "activate") activate(input);
    else if (action === "pre-tool") preTool(input);
    else if (action === "post-tool") postTool(input);
    else if (action === "subagent-start") subagentStart(input);
    else if (action === "subagent-stop") subagentStop(input);
    else if (action === "stop") stop(input);
    else if (action === "register-manifest") registerManifest(input, input.manifest || input);
    else if (action === "close-run") closeRun(input);
    else if (action === "reset-run") resetRun(input, input.reason || "manual reset");
    else throw new Error(`Unknown harness action: ${action}`);
  } catch (error) {
    if (input) logEvent(input, "handler-error", { action, error: error.message });
    // Integrity gates fail closed; lifecycle bookkeeping fails open.
    if (["pre-tool", "subagent-stop", "stop"].includes(action)) {
      if (action === "pre-tool") output(deny(`Reconciliation harness could not validate this action safely: ${error.message}`));
      else output(block(`Reconciliation harness validation failed: ${error.message}`));
      return;
    }
    // Control actions (register-manifest, close-run, reset-run) must surface failure
    // via a non-zero exit rather than silently succeeding with no state change.
    process.stderr.write(`${error.message}\n`);
    process.exitCode = 1;
  }
}

if (require.main === module) main();

module.exports = {
  RESEARCHER,
  VERIFIER,
  activate,
  preTool,
  postTool,
  subagentStart,
  subagentStop,
  stop,
  registerManifest,
  closeRun,
  resetRun,
  extractResultBlocks,
  validateResearcherAssignment,
  validateResearcherResult,
  validateVerifierAssignment,
  validateVerifierResult,
  loadState,
  saveState,
  defaultState,
  canonical
};
