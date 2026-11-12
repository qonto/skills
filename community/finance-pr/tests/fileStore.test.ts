import { afterEach, describe, expect, it } from 'vitest';
import { mkdtempSync, readFileSync, realpathSync, rmSync, statSync, symlinkSync, mkdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { FileStore } from '../src/node/fileStore.js';
import { prepare } from '../src/engine/prepare.js';
import { frozenClock } from '../src/engine/clock.js';
import { EventLog } from '../src/engine/events.js';
import { makeEvidence, prepareRequest } from './helpers.js';

const dirs: string[] = [];
afterEach(() => { for (const dir of dirs.splice(0)) rmSync(dir, { recursive: true, force: true }); });
function fixture() {
  const dir = mkdtempSync(join(realpathSync(tmpdir()), 'finance-pr-test-')); dirs.push(dir);
  const clock = frozenClock('2026-10-23T12:00:00Z');
  const stored = prepare({ request: prepareRequest, evidence: makeEvidence(), clock, events: new EventLog(clock), prId: 'FPR-TEST' }).stored;
  return { dir, stored, store: new FileStore(dir) };
}
describe('private file store', () => {
  it('rejects symlinked store children', () => {
    const dir = mkdtempSync(join(realpathSync(tmpdir()), 'finance-pr-test-')); dirs.push(dir);
    mkdirSync(join(dir, 'outside'));
    symlinkSync(join(dir, 'outside'), join(dir, 'prs'));
    expect(() => new FileStore(dir)).toThrow(/symlink/);
  });
  it.each(['../../outside', '../outside', '/absolute', 'a/b', 'a\\b'])('rejects unsafe PR id %s', (id) => {
    const { stored, store } = fixture(); stored.body.pr_id = id;
    expect(() => store.putPr(stored)).toThrow(/PR id/);
    expect(() => store.getPr(id)).toThrow(/PR id/);
  });
  it('creates owner-only directories and files', () => {
    const { dir, stored, store } = fixture(); store.putPr(stored);
    expect(statSync(join(dir, 'prs')).mode & 0o777).toBe(0o700);
    expect(statSync(join(dir, 'prs', 'FPR-TEST.json')).mode & 0o777).toBe(0o600);
    expect(JSON.parse(readFileSync(join(dir, 'prs', 'FPR-TEST.json'), 'utf8')).body.pr_id).toBe('FPR-TEST');
  });
});
