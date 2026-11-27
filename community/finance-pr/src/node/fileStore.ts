// Node file-backed store with the same guarantees SQLite would give:
// the immutable body is written once; the one-shot reservation uses an atomic
// exclusive-create (open "wx") as the compare-and-set primitive.

import { chmodSync, closeSync, existsSync, mkdirSync, mkdtempSync, openSync, readFileSync, writeFileSync, renameSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import type { PrStore } from '../engine/store.js';
import type { ActResult, Approval, DomainEvent, LifecycleStatus, StoredPr } from '../engine/types.js';
import { assertNoSymlinks } from './privateStorage.js';

export class FileStore implements PrStore {
  constructor(private readonly dir: string) {
    assertNoSymlinks(dir);
    mkdirSync(dir, { recursive: true, mode: 0o700 });
    chmodSync(dir, 0o700);
    for (const name of ['prs', 'approvals', 'acts', 'reservations']) {
      const path = join(dir, name);
      assertNoSymlinks(path);
      mkdirSync(path, { recursive: true, mode: 0o700 });
      chmodSync(path, 0o700);
    }
    assertNoSymlinks(this.eventsPath);
    if (!existsSync(this.eventsPath)) writeFileSync(this.eventsPath, '', { mode: 0o600 });
    chmodSync(this.eventsPath, 0o600);
  }

  private validId(id: string): string {
    if (!/^[A-Za-z0-9-]{1,128}$/.test(id)) throw new Error('PR id must contain only letters, digits and hyphens (1–128 characters).');
    return id;
  }
  private checkedPath(folder: string, id: string, extension: string): string {
    const path = join(this.dir, folder, `${this.validId(id)}.${extension}`);
    assertNoSymlinks(path);
    return path;
  }

  private get eventsPath(): string {
    return join(this.dir, 'events.jsonl');
  }
  private prPath(id: string): string {
    return this.checkedPath('prs', id, 'json');
  }
  private approvalPath(id: string): string {
    return this.checkedPath('approvals', id, 'json');
  }
  private actPath(id: string): string {
    return this.checkedPath('acts', id, 'json');
  }
  private lifecyclePath(id: string): string {
    return this.checkedPath('prs', id, 'lifecycle');
  }
  private reservationPath(id: string): string {
    return this.checkedPath('reservations', id, 'lock');
  }

  private writeAtomic(path: string, data: string): void {
    assertNoSymlinks(path);
    const tempDir = mkdtempSync(join(this.dir, '.write-'));
    try {
      const tmp = join(tempDir, 'data');
      writeFileSync(tmp, data, { mode: 0o600, flag: 'wx' });
      renameSync(tmp, path);
    } finally {
      rmSync(tempDir, { recursive: true, force: true });
    }
  }

  putPr(stored: StoredPr): void {
    this.writeAtomic(this.prPath(stored.body.pr_id), JSON.stringify(stored, null, 2));
  }
  getPr(id: string): StoredPr | null {
    const p = this.prPath(id);
    return existsSync(p) ? (JSON.parse(readFileSync(p, 'utf8')) as StoredPr) : null;
  }

  putApproval(a: Approval): void {
    this.writeAtomic(this.approvalPath(a.pr_id), JSON.stringify(a, null, 2));
  }
  getApproval(id: string): Approval | null {
    const p = this.approvalPath(id);
    return existsSync(p) ? (JSON.parse(readFileSync(p, 'utf8')) as Approval) : null;
  }

  putLifecycle(id: string, status: LifecycleStatus): void {
    this.writeAtomic(this.lifecyclePath(id), status);
  }
  getLifecycle(id: string): LifecycleStatus | null {
    const p = this.lifecyclePath(id);
    return existsSync(p) ? (readFileSync(p, 'utf8').trim() as LifecycleStatus) : null;
  }

  appendEvent(e: DomainEvent): void {
    assertNoSymlinks(this.eventsPath);
    writeFileSync(this.eventsPath, `${JSON.stringify(e)}\n`, { flag: 'a', mode: 0o600 });
  }
  events(id?: string): DomainEvent[] {
    assertNoSymlinks(this.eventsPath);
    const raw = readFileSync(this.eventsPath, 'utf8').trim();
    if (!raw) return [];
    const all = raw.split('\n').map((l) => JSON.parse(l) as DomainEvent);
    return id ? all.filter((e) => e.pr_id === id) : all;
  }

  putActResult(r: ActResult): void {
    this.writeAtomic(this.actPath(r.pr_id), JSON.stringify(r, null, 2));
  }
  getActResult(id: string): ActResult | null {
    const p = this.actPath(id);
    return existsSync(p) ? (JSON.parse(readFileSync(p, 'utf8')) as ActResult) : null;
  }

  /** Atomic single-use reservation: exclusive create succeeds for exactly one caller. */
  reserveOnce(id: string): boolean {
    try {
      const fd = openSync(this.reservationPath(id), 'wx', 0o600);
      closeSync(fd);
      return true;
    } catch {
      return false;
    }
  }
  isReserved(id: string): boolean {
    return existsSync(this.reservationPath(id));
  }
}
