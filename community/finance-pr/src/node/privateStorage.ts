import { existsSync, lstatSync, mkdirSync, mkdtempSync, realpathSync, renameSync, rmSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { dirname, isAbsolute, join, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const PROJECT_ROOT = fileURLToPath(new URL('../../', import.meta.url));

/** Keep raw evidence and lifecycle data outside the demo's served project. */
export function privateStoreDir(home = homedir()): string {
  return join(home, '.finance-pr');
}

/** Resolve existing ancestors too, so a symlink cannot redirect into the project. */
export function assertOutsideProject(path: string, project = PROJECT_ROOT): void {
  const absolute = resolve(path);
  assertNoSymlinks(absolute);
  let ancestor = absolute;
  while (!existsSync(ancestor)) ancestor = dirname(ancestor);
  const physical = resolve(realpathSync(ancestor), relative(ancestor, absolute));
  const rel = relative(realpathSync(project), physical);
  if (!rel || (rel !== '..' && !rel.startsWith(`..${sep}`) && !isAbsolute(rel))) {
    throw new Error('Private finance data must be stored outside the demo project.');
  }
}

export function assertNoSymlinks(path: string): void {
  let current = resolve(path);
  while (true) {
    try {
      if (lstatSync(current).isSymbolicLink()) throw new Error('Private finance path must not contain symlinks.');
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code !== 'ENOENT') throw error;
    }
    const parent = dirname(current);
    if (parent === current) break;
    current = parent;
  }
}

export function writePrivateJson(path: string, value: unknown): void {
  assertOutsideProject(path);
  const dir = dirname(path);
  mkdirSync(dir, { recursive: true, mode: 0o700 });
  const tempDir = mkdtempSync(join(dir, '.finance-write-'));
  try {
    const tmp = join(tempDir, 'data');
    writeFileSync(tmp, JSON.stringify(value, null, 2), { mode: 0o600, flag: 'wx' });
    renameSync(tmp, path);
  } finally {
    rmSync(tempDir, { recursive: true, force: true });
  }
}
