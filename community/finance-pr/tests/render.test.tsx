// SSR smoke test: render the heavy UI components with REAL scenario data to
// catch render-time crashes (no browser needed).
import { describe, expect, it } from 'vitest';
import { renderToString } from 'react-dom/server';
import { buildScenarios } from '../src/fixtures/scenarios.js';
import { worldAt, totalMs, computeSummary } from '../src/ui/world.js';
import { Stage } from '../src/ui/components/Stage.js';
import { DetailPanel } from '../src/ui/components/DetailPanel.js';
import { Controls } from '../src/ui/components/Controls.js';
import { Summary } from '../src/ui/components/Summary.js';

describe('UI render smoke (SSR)', () => {
  it('renders Stage + DetailPanel at several cursor positions for every scenario', async () => {
    const runs = await buildScenarios();
    for (const run of runs) {
      const total = totalMs(run.events);
      for (const frac of [0, 0.5, 1]) {
        const world = worldAt(run.events, total * frac);
        const stage = renderToString(<Stage run={run} world={world} focus={null} selected={null} onSelect={() => {}} />);
        const panel = renderToString(<DetailPanel run={run} world={world} selected={null} onSelect={() => {}} />);
        expect(stage).toContain('BEFORE QONTO');
        expect(panel).toContain(run.stored.body.pr_id);
      }
    }
  });

  it('renders Controls and Summary without throwing', async () => {
    const runs = await buildScenarios();
    const controls = renderToString(
      <Controls
        run={runs[0]}
        runs={runs}
        idx={0}
        cursorMs={0}
        total={1000}
        playing={false}
        speed={1}
        guided={false}
        beat={undefined}
        onPlayPause={() => {}}
        onRestart={() => {}}
        onStep={() => {}}
        onScrub={() => {}}
        onSpeed={() => {}}
        onScenario={() => {}}
        onStopGuided={() => {}}
      />,
    );
    expect(controls).toContain('spd--on'); // speed control rendered
    expect(controls).toContain('Clean invoice reaches Qonto'); // scenario chips rendered
    const summary = renderToString(<Summary summary={computeSummary(runs)} runs={runs} onClose={() => {}} onReplay={() => {}} />);
    expect(summary).toContain('Finance PR did before Qonto');
  });
});
