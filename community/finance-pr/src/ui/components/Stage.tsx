import type { ScenarioRun, StationId } from '../../fixtures/scenarios.js';
import type { StationStatus, World } from '../world.js';

interface StationDef {
  id: StationId;
  x: number;
  y: number;
  label: string;
  sub: string;
  zone: 'before' | 'qonto';
  branch?: boolean;
}

// Coordinates in a 0..100 x 0..100 space (stage keeps a 16:9 aspect ratio).
const STATIONS: StationDef[] = [
  { id: 'intake', x: 7, y: 22, label: 'Invoice Intake', sub: 'source + masked invoice', zone: 'before' },
  { id: 'observe', x: 19, y: 22, label: 'Observe', sub: 'Qonto evidence · read-only', zone: 'before' },
  { id: 'intent', x: 31, y: 22, label: 'Intent Gate', sub: 'advice vs action · authority', zone: 'before' },
  { id: 'risk', x: 43, y: 22, label: 'Risk & Gates', sub: 'signals + hard gates', zone: 'before' },
  { id: 'finance_pr', x: 55, y: 22, label: 'Finance PR', sub: 'immutable · fingerprint', zone: 'before' },
  { id: 'independent', x: 43, y: 64, label: 'Independent Review', sub: 'optional · escalate-only', zone: 'before', branch: true },
  { id: 'approver', x: 55, y: 64, label: 'Designated Approver', sub: 'policy label · not a Qonto role', zone: 'before', branch: true },
  { id: 'act', x: 60, y: 43, label: 'Act Revalidation', sub: 're-hash · re-read · one-shot', zone: 'before' },
  { id: 'qonto', x: 80, y: 28, label: 'Native Qonto Approval', sub: 'permissions · SCA · execution', zone: 'qonto' },
  { id: 'outcome', x: 90, y: 60, label: 'Outcome', sub: 'pending / blocked / returned', zone: 'qonto' },
  { id: 'boundary', x: 68, y: 50, label: '', sub: '', zone: 'before' },
];

const BY_ID = Object.fromEntries(STATIONS.map((s) => [s.id, s])) as Record<StationId, StationDef>;
const BOUNDARY_X = 68;

const CONNECTORS: Array<[StationId, StationId, boolean]> = [
  ['intake', 'observe', false],
  ['observe', 'intent', false],
  ['intent', 'risk', false],
  ['risk', 'finance_pr', false],
  ['finance_pr', 'act', false],
  ['act', 'qonto', false],
  ['qonto', 'outcome', false],
  ['risk', 'independent', true],
  ['finance_pr', 'approver', true],
];

function statusClass(s: StationStatus): string {
  return `st--${s}`;
}

export function Stage({
  run,
  world,
  focus,
  selected,
  onSelect,
}: {
  run: ScenarioRun;
  world: World;
  focus: StationId | null;
  selected: StationId | null;
  onSelect: (s: StationId) => void;
}): JSX.Element {
  const token = BY_ID[world.tokenStation];
  // Float the token just above its station card.
  const tx = token.x;
  const ty = token.y - 12;
  const fp = world.visited.includes('finance_pr') ? run.stored.integrity.fingerprint : '····-····';
  const b = run.stored.body;

  return (
    <section className="stage" aria-label="Finance PR review floor">
      {/* Zone backdrops */}
      <div className="zone zone--before">
        <span className="zone__label">BEFORE QONTO — intent · evidence · risk · Finance review</span>
      </div>
      <div className="zone zone--qonto">
        <span className="zone__label">INSIDE QONTO — permissions · native approval · SCA</span>
      </div>

      {/* Connectors */}
      <svg className="wires" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden>
        {CONNECTORS.map(([a, c, dashed]) => {
          const A = BY_ID[a];
          const C = BY_ID[c];
          const active = world.visited.includes(c) || world.tokenStation === c;
          return (
            <line
              key={`${a}-${c}`}
              x1={A.x}
              y1={A.y}
              x2={C.x}
              y2={C.y}
              className={`wire ${dashed ? 'wire--branch' : ''} ${active ? 'wire--active' : ''}`}
            />
          );
        })}
      </svg>

      {/* Qonto boundary gate */}
      <div
        className={`boundary boundary--${world.gate} ${world.mode === 'blocked' ? 'boundary--blocked' : ''}`}
        style={{ left: `${BOUNDARY_X}%` }}
      >
        <div className="boundary__door boundary__door--top" />
        <div className="boundary__door boundary__door--bottom" />
        <div className="boundary__seam" />
        <div className="boundary__badge">
          <span className="boundary__lock">{world.gate === 'open' ? '⇥' : '🔒'}</span>
          QONTO BOUNDARY
        </div>
      </div>

      {/* Stations */}
      {STATIONS.filter((s) => s.id !== 'boundary').map((s) => {
        const st = world.status[s.id];
        const isFocus = focus === s.id;
        const isSelected = selected === s.id;
        return (
          <button
            key={s.id}
            className={`station ${statusClass(st)} ${s.branch ? 'station--branch' : ''} ${isFocus ? 'is-focus' : ''} ${isSelected ? 'is-selected' : ''}`}
            style={{ left: `${s.x}%`, top: `${s.y}%` }}
            onClick={() => onSelect(s.id)}
          >
            <span className="station__dot" />
            <span className="station__label">{s.label}</span>
            <span className="station__sub">{s.sub}</span>
          </button>
        );
      })}

      {/* The Finance PR token */}
      <div
        className={`token token--${world.mode}`}
        style={{ left: `${tx}%`, top: `${ty}%` }}
        onClick={() => onSelect(world.tokenStation)}
      >
        <div className="token__ring" />
        <div className="token__body">
          <div className="token__row">
            <span className="token__supplier">{b.target.supplier_name}</span>
            <span className="chip chip--syn">SYN</span>
          </div>
          <div className="token__amount">
            {b.critical_state_display.amount.value} {b.critical_state_display.amount.currency}
          </div>
          <div className="token__fp">
            <span>{b.pr_id}</span>
            <span className="token__fpcode">{fp}</span>
          </div>
        </div>
        {world.mode === 'blocked' && world.terminalLabel && (
          <div className="stamp stamp--block">{world.terminalLabel}</div>
        )}
        {world.mode === 'crossed' && <div className="stamp stamp--cross">CROSSED</div>}
        {world.mode === 'manual_review' && <div className="stamp stamp--review">MANUAL REVIEW</div>}
        <div className="token__dwell">{(world.dwellMs / 1000).toFixed(1)}s</div>
      </div>
    </section>
  );
}
