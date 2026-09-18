// The single allowlisted write seam. Default performs NO Qonto call.
//
// Reaching this seam already required the full Act safety chain to pass. Even
// then, the default adapter refuses to mutate anything — the honest MVP terminal
// is a verified `ready_for_qonto` handoff (see docs/QONTO_TOOL_INVENTORY.md).

import type { ActOutcome, FinancePrBody } from './types.js';

export interface WriteResult {
  outcome: ActOutcome;
  note: string;
}

export interface WriteAdapter {
  readonly id: string;
  submit(body: FinancePrBody): Promise<WriteResult>;
}

/** Default. No Qonto tool is called; Act terminates at ready_for_qonto. */
export const DisabledWriteAdapter: WriteAdapter = {
  id: 'disabled',
  async submit() {
    return {
      outcome: 'ready_for_qonto',
      note: 'Qonto writes disabled by default. Verified handoff only — Qonto permissions, native approval, and SCA still apply.',
    };
  },
};

/** Synthetic-only adapter used by the demo to visualize the boundary crossing.
 * It makes NO network/MCP call; it only emits a synthetic pending outcome. */
export const SyntheticQontoAdapter: WriteAdapter = {
  id: 'synthetic',
  async submit() {
    return {
      outcome: 'qonto_native_approval_pending',
      note: 'SYNTHETIC: proposal reached the Qonto boundary. Qonto native approval and SCA remain.',
    };
  },
};
