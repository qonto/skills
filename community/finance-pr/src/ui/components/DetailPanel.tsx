import type { ScenarioRun, StationId } from '../../fixtures/scenarios.js';
import type { World } from '../world.js';
import type { Gate, Signal } from '../../engine/types.js';

function decisionClass(d: string): string {
  if (d === 'ready_for_finance_review') return 'ok';
  if (d === 'manual_review_required') return 'review';
  return 'block';
}

function SignalRow({ s }: { s: Signal }): JSX.Element {
  const observed = s.status === 'observed';
  const contribution = observed ? (s.risk * s.weight).toFixed(3) : '—';
  const pct = observed ? Math.round(s.risk * 100) : 0;
  return (
    <div className={`sig sig--${s.status}`}>
      <div className="sig__head">
        <span className="sig__id">{s.id}</span>
        <span className="sig__w">w{s.weight.toFixed(2)}</span>
      </div>
      <div className="sig__bar">
        <div className="sig__fill" style={{ width: `${pct}%` }} />
      </div>
      <div className="sig__meta">
        <span className={`tag tag--${s.status}`}>{observed ? `risk ${s.risk.toFixed(2)}` : s.status}</span>
        <span className="sig__contrib">contrib {contribution}</span>
      </div>
      <div className="sig__reason">{s.reason}</div>
    </div>
  );
}

function GateRow({ g }: { g: Gate }): JSX.Element {
  return (
    <div className={`gate gate--${g.status}`}>
      <span className="gate__mark">{g.status === 'pass' ? '✓' : g.status === 'fail' ? '✕' : '?'}</span>
      <div>
        <div className="gate__id">{g.id}</div>
        <div className="gate__reason">{g.reason}</div>
        {g.status !== 'pass' && g.remediation && <div className="gate__rem">→ {g.remediation}</div>}
      </div>
    </div>
  );
}

export function DetailPanel({
  run,
  world,
  selected,
}: {
  run: ScenarioRun;
  world: World;
  selected: StationId | null;
  onSelect: (s: StationId) => void;
}): JSX.Element {
  const b = run.stored.body;
  const r = b.risk;
  const decided = world.visited.includes('finance_pr') || run.prepare.decision === 'blocked';
  const focus = selected ?? world.tokenStation;

  return (
    <aside className="panel">
      <div className="panel__hd">
        <div>
          <div className="panel__pr">{b.pr_id}</div>
          <div className="panel__scn">Scenario {run.id} · {run.title}</div>
        </div>
        <span className={`badge badge--${decisionClass(run.prepare.decision)}`}>
          {decided ? run.prepare.decision.replace(/_/g, ' ') : 'preparing…'}
        </span>
      </div>

      <div className="panel__body">
        <section className={`sec ${focus === 'intent' || focus === 'intake' ? 'sec--focus' : ''}`}>
          <h4>Request &amp; intent</h4>
          <p className="quote">“{b.intent.literal_request}”</p>
          <div className="kv"><span>source</span><b>{b.intent.request_source}</b></div>
          <div className="kv"><span>intent</span><b>{b.intent.intent_class}</b></div>
          <div className="kv"><span>authority</span><b className={run.prepare.intent.source_is_authoritative ? 'good' : 'bad'}>{run.prepare.intent.source_is_authoritative ? 'valid' : 'NOT authoritative'}</b></div>
          <p className="muted">{b.intent.interpretation}</p>
        </section>

        <section className={`sec ${focus === 'finance_pr' ? 'sec--focus' : ''}`}>
          <h4>Proposed action (exact · immutable)</h4>
          <div className="kv"><span>invoice</span><b>{b.target.invoice_number}</b></div>
          <div className="kv"><span>supplier</span><b>{b.proposed_action.parameters.supplier_name}</b></div>
          <div className="kv"><span>amount</span><b>{b.critical_state_display.amount.value} {b.critical_state_display.amount.currency}</b></div>
          <div className="kv"><span>IBAN</span><b>{b.critical_state_display.iban_masked ?? 'none on file'}</b></div>
          <div className="kv"><span>status</span><b>{b.critical_state_display.status}</b></div>
        </section>

        {b.sanitization.detected_instructions.length > 0 && (
          <section className="sec sec--warn">
            <h4>⚠ Untrusted document instructions</h4>
            <p className="muted">Detected inside the invoice — treated as data, never authority:</p>
            {b.sanitization.detected_instructions.map((d, i) => (
              <p key={i} className="inject">“{d}”</p>
            ))}
          </section>
        )}

        <section className={`sec ${focus === 'risk' ? 'sec--focus' : ''}`}>
          <h4>Risk signals <span className="muted">(advisory — never authorize)</span></h4>
          {b.signals.map((s) => <SignalRow key={s.id} s={s} />)}
          <div className="coverage">
            <div className="kv"><span>observed risk</span><b>{r.observed_risk === null ? 'not scored' : r.observed_risk.toFixed(3)}</b></div>
            <div className="kv"><span>coverage</span><b>{Math.round(r.coverage * 100)}%</b></div>
            <div className="kv"><span>band</span><b>{r.band.replace(/_/g, ' ')}</b></div>
          </div>
        </section>

        <section className={`sec ${focus === 'risk' || focus === 'act' ? 'sec--focus' : ''}`}>
          <h4>Hard gates <span className="muted">(all must pass · a score can't override)</span></h4>
          {b.gates.map((g) => <GateRow key={g.id} g={g} />)}
          {run.act && (
            <>
              <h4 className="mt">Act revalidation gates</h4>
              {run.act.gates.filter((g) => g.phase === 'act').map((g) => <GateRow key={g.id} g={g} />)}
            </>
          )}
        </section>

        <section className={`sec ${focus === 'finance_pr' || focus === 'approver' ? 'sec--focus' : ''}`}>
          <h4>Policy &amp; integrity</h4>
          <div className="kv"><span>decision</span><b className={decisionClass(run.prepare.decision)}>{run.prepare.decision.replace(/_/g, ' ')}</b></div>
          <div className="kv"><span>route</span><b>{b.policy.reviewer_route.replace(/_/g, ' ')}</b></div>
          <div className="kv"><span>policy</span><b>{b.policy.policy_id}@{b.policy.policy_version}</b></div>
          <div className="kv"><span>fingerprint</span><b className="mono">{run.stored.integrity.fingerprint}</b></div>
          <div className="kv"><span>sha256</span><b className="mono tiny">{run.stored.integrity.hash.slice(0, 24)}…</b></div>
          <div className="kv"><span>expires</span><b className="tiny">{b.expires_at}</b></div>
          {run.prepare.decision !== 'blocked' && (
            <p className="approve">Approve Finance PR {b.pr_id}, fingerprint {run.stored.integrity.fingerprint}</p>
          )}
        </section>

        {run.act && (
          <section className={`sec ${focus === 'boundary' || focus === 'qonto' ? 'sec--focus' : ''}`}>
            <h4>Act outcome</h4>
            <div className="kv"><span>outcome</span><b className={run.act.outcome.includes('pending') || run.act.outcome === 'ready_for_qonto' ? 'ok' : 'block'}>{run.act.outcome.replace(/_/g, ' ')}</b></div>
            {run.act.reasons.map((rs, i) => <p key={i} className="muted">{rs}</p>)}
          </section>
        )}

        <section className="sec sec--boundary">
          <h4>The Qonto boundary</h4>
          <p className="muted">
            Finance PR approval only lets a proposal <b>reach</b> Qonto. Qonto still owns permissions,
            native approval, and SCA (2FA). This tool moves no money and completes no 2FA.
          </p>
        </section>
      </div>
    </aside>
  );
}
