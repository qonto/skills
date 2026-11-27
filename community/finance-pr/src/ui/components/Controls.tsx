import type { Beat, ScenarioRun } from '../../fixtures/scenarios.js';

const SPEEDS = [1, 2, 4];

export function Controls({
  run,
  runs,
  idx,
  cursorMs,
  total,
  playing,
  speed,
  guided,
  beat,
  onPlayPause,
  onRestart,
  onStep,
  onScrub,
  onSpeed,
  onScenario,
  onStopGuided,
}: {
  run: ScenarioRun;
  runs: ScenarioRun[];
  idx: number;
  cursorMs: number;
  total: number;
  playing: boolean;
  speed: number;
  guided: boolean;
  beat: Beat | undefined;
  onPlayPause: () => void;
  onRestart: () => void;
  onStep: (dir: -1 | 1) => void;
  onScrub: (ms: number) => void;
  onSpeed: (s: number) => void;
  onScenario: (i: number) => void;
  onStopGuided: () => void;
}): JSX.Element {
  return (
    <footer className="controls">
      <div className="controls__narration">
        <span className={`narr__label ${guided ? 'narr__label--guided' : ''}`}>{guided ? 'GUIDED' : beat?.label ?? 'Ready'}</span>
        <span className="narr__text">{beat?.caption ?? run.teaching}</span>
      </div>

      <div className="controls__bar">
        <div className="transport">
          <button className="tbtn" onClick={() => onStep(-1)} title="Previous beat (←)">⏮</button>
          <button className="tbtn tbtn--play" onClick={onPlayPause} title="Play / Pause (Space)">
            {playing ? '❚❚' : '▶'}
          </button>
          <button className="tbtn" onClick={() => onStep(1)} title="Next beat (→)">⏭</button>
          <button className="tbtn" onClick={onRestart} title="Restart (R)">↺</button>
        </div>

        <input
          className="scrub"
          type="range"
          min={0}
          max={Math.max(1, Math.round(total))}
          value={Math.min(Math.round(cursorMs), Math.round(total))}
          onPointerDown={() => {/* pause handled in onChange */}}
          onChange={(e) => onScrub(Number(e.target.value))}
          aria-label="Timeline scrubber"
        />

        <div className="speeds">
          {SPEEDS.map((s) => (
            <button key={s} className={`spd ${speed === s ? 'spd--on' : ''}`} onClick={() => onSpeed(s)}>
              {s}×
            </button>
          ))}
        </div>
      </div>

      <div className="scenarios">
        {runs.map((r, i) => (
          <button
            key={r.id}
            className={`scn ${i === idx ? 'scn--on' : ''} scn--${r.id[0].toLowerCase()}`}
            onClick={() => {
              onStopGuided();
              onScenario(i);
            }}
            title={r.title}
          >
            <b>{r.id}</b>
            <span>{r.title}</span>
          </button>
        ))}
      </div>
    </footer>
  );
}
