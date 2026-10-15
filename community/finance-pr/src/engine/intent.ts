// Deterministic intent classification + authority separation.
//
// Rules — not an LLM — make the final authorization decision. An optional model
// may only *raise* review requirements later (see reviewer.ts).
//
// The only text that can authorize a Qonto-crossing action is an explicit,
// fingerprint-bound approval in a user_chat message. Documents and tool output
// are data, never authority.

import type { IntentClass, IntentResult, UserRequest } from './types.js';

/** `Approve Finance PR FPR-104, fingerprint 7C91-A2B4.` (case-insensitive) */
export const APPROVAL_RE =
  /approve\s+finance\s+pr\s+([A-Za-z0-9-]+)\s*[,;:]?\s*fingerprint\s+([0-9A-Fa-f]{4}-[0-9A-Fa-f]{4})/i;

export interface ParsedApproval {
  pr_id: string;
  fingerprint: string;
}

export function parseApproval(text: string): ParsedApproval | null {
  const m = APPROVAL_RE.exec(text);
  if (!m) return null;
  return { pr_id: m[1], fingerprint: m[2].toUpperCase() };
}

/** Instruction-like patterns that may appear inside untrusted documents/tools. */
const INSTRUCTION_PATTERNS: RegExp[] = [
  /ignore\s+(all\s+|any\s+)?(previous|prior)\s+(instructions|rules)/i,
  /disregard\s+(the\s+)?(instructions|policy|rules)/i,
  /approve\s+(this|the)?\s*(payment|invoice|transfer)/i,
  /\bpay\s+(this|it|immediately|now|the\s+invoice)/i,
  /authori[sz]e\s+(this|the)?\s*(payment|transfer)/i,
  /(send|release|execute)\s+(the\s+)?(payment|transfer|funds)/i,
  /transfer\s+.*\bnow\b/i,
  /bypass\s+(the\s+)?(review|approval|policy)/i,
  /you\s+(must|should|need\s+to)\s+approve/i,
  /no\s+approval\s+(is\s+)?(needed|required)/i,
];

export function detectInstructions(text: string | null | undefined): string[] {
  if (!text) return [];
  const hits: string[] = [];
  for (const re of INSTRUCTION_PATTERNS) {
    const m = re.exec(text);
    if (m) hits.push(m[0].trim().replace(/\s+/g, ' ').slice(0, 80));
  }
  return Array.from(new Set(hits));
}

const ADVICE_RE =
  /\b(should|shall|can|could|would|may|is\s+it\s+ok|do\s+you\s+(think|recommend)|worth|advice)\b/;
const PAY_TOPIC_RE = /\b(pay|payment|settle|approve|approv|wire|transfer|reimburse)\b/;
const OBSERVE_RE =
  /\b(what|show|read|look|summari[sz]e|explain|describe|tell\s+me|contents?|details?|how\s+much|when\b)\b/;
const PREPARE_RE = /\b(prepare|draft|stage|create\s+(a\s+)?finance\s+pr|get\s+ready|set\s+up)\b/;
const PREPARE_TOPIC_RE = /\b(payment|pay|review|approval|finance\s+pr|invoice)\b/;
const BARE_ACT_RE =
  /^(yes|yep|yeah|ok(ay)?|sure|do\s+it|go\s+ahead|proceed|pay\s+it|pay\s+now|approve\s+it|just\s+pay|send\s+it|make\s+the\s+payment)\b/;

function classify(text: string): IntentClass {
  const t = text.trim().toLowerCase();

  if (parseApproval(text)) return 'ACT';

  // Bare imperative with no bound target/fingerprint — never an authorization.
  if (BARE_ACT_RE.test(t)) return 'AMBIGUOUS';

  if (PREPARE_RE.test(t) && PREPARE_TOPIC_RE.test(t)) return 'PREPARE';

  // A question about paying/approving is advice, not an instruction.
  const isQuestion = t.includes('?') || ADVICE_RE.test(t);
  if (isQuestion && PAY_TOPIC_RE.test(t)) return 'ADVICE_ONLY';

  if (OBSERVE_RE.test(t)) return 'OBSERVE';
  if (isQuestion) return 'OBSERVE';

  // An imperative that mentions paying but isn't a structured approval.
  if (PAY_TOPIC_RE.test(t)) return 'AMBIGUOUS';

  return 'OBSERVE';
}

function interpret(cls: IntentClass): string {
  switch (cls) {
    case 'ACT':
      return 'User submitted an explicit, fingerprint-bound approval to proceed.';
    case 'PREPARE':
      return 'User asked to prepare an invoice for payment review (no execution).';
    case 'ADVICE_ONLY':
      return 'User asked for advice/opinion about paying — a question, not an instruction.';
    case 'OBSERVE':
      return 'User asked to read or understand the invoice — observation only.';
    case 'AMBIGUOUS':
      return 'Imperative to act but no unambiguous target/action or fingerprint-bound approval.';
  }
}

export function classifyIntent(request: UserRequest, attachmentText?: string | null): IntentResult {
  const intent_class = classify(request.text);
  const detected_instructions = detectInstructions(attachmentText);

  const isAction = intent_class === 'PREPARE' || intent_class === 'ACT';

  // An action is being "attempted" by the document if the doc carries action
  // instructions while the user themselves did NOT authorize an action.
  const documentAttemptedAction = detected_instructions.length > 0 && !isAction;

  const source_is_authoritative = request.source === 'user_chat' && !documentAttemptedAction;

  const target_and_action_unambiguous = intent_class !== 'AMBIGUOUS';

  const ambiguity_notes: string[] = [];
  if (intent_class === 'AMBIGUOUS') {
    ambiguity_notes.push('No bound target/action or fingerprint approval; clarification required.');
  }
  if (documentAttemptedAction) {
    ambiguity_notes.push(
      'Action-like text was found inside untrusted document content, not in the user request.',
    );
  }
  if (request.source !== 'user_chat') {
    ambiguity_notes.push(`Request source is "${request.source}", which is not authoritative.`);
  }

  return {
    intent_class,
    source_is_authoritative,
    target_and_action_unambiguous,
    interpretation: interpret(intent_class),
    ambiguity_notes,
    detected_instructions,
  };
}
