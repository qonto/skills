import type { ScenarioRun } from '../../fixtures/scenarios.js';
import type { Summary as SummaryData } from '../world.js';

export function Summary({
  summary,
  runs,
  onClose,
  onReplay,
}: {
  summary: SummaryData;
  runs: ScenarioRun[];
  onClose: () => void;
  onReplay: () => void;
}): JSX.Element {
  const tiles: Array<[string, number | string, string]> = [
    ['Invoices observed', summary.observed, 'ok'],
    ['Finance PRs prepared', summary.prepared, 'ok'],
    ['Ready for Finance review', summary.ready_for_review, 'ok'],
    ['Manual review required', summary.manual_review, 'review'],
    ['Blocked before Qonto', summary.blocked_before_qonto, 'block'],
    ['Fingerprint approvals', summary.approvals, 'ok'],
    ['Reached Qonto boundary', summary.submitted_across_boundary, 'ok'],
    ['Native approval pending', summary.native_pending, 'accent'],
    ['Tamper / stale / replay prevented', summary.integrity_stale_replay_prevented, 'block'],
  ];

  return (
    <div className="overlay" role="dialog" aria-modal="true" aria-label="Run summary">
      <div className="summary">
        <div className="summary__hd">
          <div>
            <div className="summary__kicker">SYNTHETIC DEMO · computed from engine events</div>
            <h2>What Finance PR did before Qonto</h2>
          </div>
          <button className="btn" onClick={onClose}>✕</button>
        </div>

        <div className="summary__grid">
          {tiles.map(([label, value, tone]) => (
            <div key={label} className={`tile tile--${tone}`}>
              <div className="tile__value">{value}</div>
              <div className="tile__label">{label}</div>
            </div>
          ))}
        </div>

        <div className="summary__note">
          Across {runs.length} scenarios, every proposal was intercepted <b>before</b> Qonto. Nothing crossed
          the boundary without passing intent, evidence, integrity, freshness and one-shot checks — and a
          risk score never overrode a failed gate. Crossing only starts Qonto's own permissions, native
          approval and SCA. This demo used a synthetic Qonto adapter and made no Qonto calls.
        </div>

        <div className="summary__actions">
          <button className="btn btn--primary" onClick={onReplay}>▶ Replay 3-minute demo</button>
          <button className="btn" onClick={onClose}>Explore freely</button>
        </div>
      </div>
    </div>
  );
}
