import { afterEach, expect, it } from 'vitest';
import { mkdtempSync, readFileSync, realpathSync, rmSync, statSync, symlinkSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { privateStoreDir, writePrivateJson, assertOutsideProject } from '../src/node/privateStorage.js';

const dirs: string[] = [];
afterEach(() => { for (const dir of dirs.splice(0)) rmSync(dir, { recursive: true, force: true }); });
it('defaults to user-private storage outside project', () => {
  expect(privateStoreDir('/fake/home')).toBe(join('/fake/home', '.finance-pr'));
});
it('rejects project-local private paths', () => {
  expect(() => assertOutsideProject(join(process.cwd(), 'bundle.json'))).toThrow(/outside/);
  expect(() => assertOutsideProject(process.cwd())).toThrow(/outside/);
});
it('rejects a symlink pointing into the served project', () => {
  const dir = mkdtempSync(join(realpathSync(tmpdir()), 'finance-pr-link-')); dirs.push(dir);
  symlinkSync(process.cwd(), join(dir, 'project'));
  expect(() => assertOutsideProject(join(dir, 'project', 'bundle.json'))).toThrow(/symlink/);
});
it('rejects dangling output symlinks', () => {
  const dir = mkdtempSync(join(realpathSync(tmpdir()), 'finance-pr-link-')); dirs.push(dir);
  symlinkSync(join(process.cwd(), 'absent-private.json'), join(dir, 'evidence.json'));
  expect(() => writePrivateJson(join(dir, 'evidence.json'), {})).toThrow(/symlink/);
});
it('writes evidence with owner-only permissions', () => {
  const dir = mkdtempSync(join(realpathSync(tmpdir()), 'finance-pr-private-')); dirs.push(dir);
  const path = join(dir, 'inputs', 'evidence.json');
  writePrivateJson(path, { marker: 'FICTIONAL' });
  expect(statSync(join(dir, 'inputs')).mode & 0o777).toBe(0o700);
  expect(statSync(path).mode & 0o777).toBe(0o600);
  expect(JSON.parse(readFileSync(path, 'utf8')).marker).toBe('FICTIONAL');
});
it('atomically replaces readable existing output with a private file', () => {
  const dir = mkdtempSync(join(realpathSync(tmpdir()), 'finance-pr-private-')); dirs.push(dir);
  const path = join(dir, 'evidence.json');
  writeFileSync(path, 'old', { mode: 0o644 });
  writePrivateJson(path, { marker: 'PRIVATE' });
  expect(statSync(path).mode & 0o777).toBe(0o600);
  expect(JSON.parse(readFileSync(path, 'utf8')).marker).toBe('PRIVATE');
});
