import { useCallback, useEffect, useMemo, useState } from 'react';
import { buildScenarios, beatsFor, type ScenarioRun, type StationId } from '../fixtures/scenarios.js';
import { computeSummary, totalMs, worldAt } from './world.js';
import { useClock } from './useClock.js';
import { Stage } from './components/Stage.js';
import { DetailPanel } from './components/DetailPanel.js';
import { Controls } from './components/Controls.js';
import { Summary } from './components/Summary.js';

const TAIL_MS = 1800;
const GUIDED_TAIL_MS = 3200;

function msOfSeq(run: ScenarioRun, seq: number): number {
  const e = run.events.find((ev) => ev.seq === seq) ?? run.events[0];
  const t0 = Date.parse(run.events[0].t);
  return Date.parse(e.t) - t0;
}

const SCENARIO_IDS = ['A', 'B', 'C', 'D1', 'D2', 'D3'];

// Deep-link support (also used for deterministic screenshots): ?scn=C&t=99999&play=1
function initialFromUrl(): { idx: number; cursorMs: number; playing: boolean; guided: boolean } {
  if (typeof window === 'undefined') return { idx: 0, cursorMs: 0, playing: false, guided: false };
  const p = new URLSearchParams(window.location.search);
  const scn = p.get('scn');
  const idx = scn ? Math.max(0, SCENARIO_IDS.indexOf(scn)) : 0;
  const cursorMs = p.get('t') ? Number(p.get('t')) : 0;
  const guided = p.get('demo') === '1';
  const playing = p.get('play') === '1' || guided;
  return { idx: idx < 0 ? 0 : idx, cursorMs, playing, guided };
}

export function App(): JSX.Element {
  const init = initialFromUrl();
  const [runs, setRuns] = useState<ScenarioRun[] | null>(null);
  const [idx, setIdx] = useState(init.idx);
  const [cursorMs, setCursorMs] = useState(init.cursorMs);
  const [playing, setPlaying] = useState(init.playing);
  const [speed, setSpeed] = useState(2);
  const [guided, setGuided] = useState(init.guided);
  const [showSummary, setShowSummary] = useState(false);
  const [selected, setSelected] = useState<StationId | null>(null);

  useEffect(() => {
    void buildScenarios().then(setRuns);
  }, []);

  const run = runs?.[idx] ?? null;
  const total = run ? totalMs(run.events) : 0;
  const tail = guided ? GUIDED_TAIL_MS : TAIL_MS;
  const world = useMemo(() => (run ? worldAt(run.events, cursorMs) : null), [run, cursorMs]);
  const beats = useMemo(() => (run ? beatsFor(run) : []), [run]);

  const beatTimes = useMemo(() => beats.map((b) => msOfSeq(run!, b.atSeq)), [beats, run]);
  const currentBeatIdx = useMemo(() => {
    let i = 0;
    for (let k = 0; k < beatTimes.length; k++) if (beatTimes[k] <= cursorMs) i = k;
    return i;
  }, [beatTimes, cursorMs]);

  const advance = useCallback(
    (dt: number) => {
      if (!run) return;
      setCursorMs((c) => {
        const next = c + speed * dt;
        if (next >= total + tail) {
          if (guided) {
            if (idx < (runs?.length ?? 0) - 1) {
              setIdx((i) => i + 1);
              return 0;
            }
            setPlaying(false);
            setGuided(false);
            setShowSummary(true);
            return total + tail;
          }
          setPlaying(false);
          return total + tail;
        }
        return next;
      });
    },
    [run, speed, total, tail, guided, idx, runs],
  );
  useClock(playing, advance);

  const goScenario = useCallback((i: number) => {
    setIdx(i);
    setCursorMs(0);
    setSelected(null);
  }, []);

  const run3min = useCallback(() => {
    setShowSummary(false);
    setSelected(null);
    setIdx(0);
    setCursorMs(0);
    setSpeed(2);
    setGuided(true);
    setPlaying(true);
  }, []);

  const restart = useCallback(() => {
    setCursorMs(0);
    setShowSummary(false);
    setPlaying(true);
  }, []);

  const stepBeat = useCallback(
    (dir: -1 | 1) => {
      setPlaying(false);
      const target = Math.min(Math.max(currentBeatIdx + dir, 0), beatTimes.length - 1);
      setCursorMs(beatTimes[target] ?? 0);
    },
    [currentBeatIdx, beatTimes],
  );

  // Keyboard: Space play/pause, ←/→ step beat, R restart, Esc close.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement) return;
      if (e.key === ' ') {
        e.preventDefault();
        setPlaying((p) => !p);
      } else if (e.key === 'ArrowRight') stepBeat(1);
      else if (e.key === 'ArrowLeft') stepBeat(-1);
      else if (e.key.toLowerCase() === 'r') restart();
      else if (e.key === 'Escape') {
        setSelected(null);
        setShowSummary(false);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [stepBeat, restart]);

  if (!runs || !run || !world) {
    return (
      <div className="app app--loading">
        <div className="loading">Running the Finance PR engine…</div>
      </div>
    );
  }

  const summary = computeSummary(runs);
  const beat = beats[currentBeatIdx];
  const showTitleCard = guided && cursorMs < 700;

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand__mark" aria-hidden />
          <div>
            <div className="brand__name">Finance PR <span>for Qonto MCP</span></div>
            <div className="brand__tag">Review before money moves.</div>
          </div>
        </div>
        <div className="topbar__right">
          <span className="chip chip--synthetic">SYNTHETIC DEMO</span>
          <button className="btn btn--primary" onClick={run3min}>▶ Run 3-minute demo</button>
        </div>
      </header>

      <main className="workspace">
        <Stage
          run={run}
          world={world}
          focus={beat?.focus ?? null}
          selected={selected}
          onSelect={setSelected}
        />
        <DetailPanel run={run} world={world} selected={selected} onSelect={setSelected} />
      </main>

      <Controls
        run={run}
        runs={runs}
        idx={idx}
        cursorMs={cursorMs}
        total={total + tail}
        playing={playing}
        speed={speed}
        guided={guided}
        beat={beat}
        onPlayPause={() => setPlaying((p) => !p)}
        onRestart={restart}
        onStep={stepBeat}
        onScrub={(ms) => {
          setPlaying(false);
          setCursorMs(ms);
        }}
        onSpeed={setSpeed}
        onScenario={goScenario}
        onStopGuided={() => setGuided(false)}
      />

      {showTitleCard && (
        <div className="titlecard" key={run.id}>
          <div className="titlecard__id">Scenario {run.id}</div>
          <div className="titlecard__title">{run.title}</div>
          <div className="titlecard__sub">{run.subtitle}</div>
        </div>
      )}

      {showSummary && <Summary summary={summary} runs={runs} onClose={() => setShowSummary(false)} onReplay={run3min} />}
    </div>
  );
}
