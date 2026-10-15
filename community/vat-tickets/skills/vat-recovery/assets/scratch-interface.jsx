/**
 * ============================================================================
 * OBSOLETE — DO NOT USE
 * ============================================================================
 * This stub aimed at the wrong target.
 *
 * Cowork artifacts are NOT JSX: `mcp__cowork__create_artifact` takes an
 * `html_path` — a standalone, inline HTML file, no build step.
 * (Verified by test on 2026-07-13: the artifact opens as a panel to the right
 * of the chat, in the same window, and the local reveal is instant.)
 *
 *   ➜  THE INTERFACE NOW LIVES IN:  assets/board.html
 *
 * The data contract specified here has become executable code: it is produced
 * by `scripts/build_tickets.py` (tickets.json), with its three mechanical locks
 * (two fields that never merge; `won` impossible without a read invoice;
 * enforced grammar). The board reads this file and NEVER computes a verdict.
 *
 * Platform limits to know before touching the interface:
 *   - an artifact CANNOT read an image (no vision in JS);
 *   - an artifact CANNOT write into the conversation;
 *   - it CAN call the connectors (window.cowork.callMcpTool) and
 *     remember its state (localStorage works).
 * So: all intelligence goes through the model, in the thread. The board
 * displays, reveals and celebrates — it decides nothing.
 * ============================================================================
 */

export default function ScratchInterfaceVAT() {
  return null; // See assets/board.html
}
