// Node file-backed store with the same guarantees SQLite would give:
// the immutable body is written once; the one-shot reservation uses an atomic
// exclusive-create (open "wx") as the compare-and-set primitive.

import { closeSync, existsSync, mkdirSync, openSync, readFileSync, writeFileSync, renameSync } from 'node:fs';
import { join } from 'node:path';
import type { PrStore } from '../engine/store.js';
import type { ActResult, Approval, DomainEvent, LifecycleStatus, StoredPr } from '../engine/types.js';

export class FileStore implements PrStore {
  constructor(private readonly dir: string) {
    mkdirSync(join(dir, 'prs'), { recursive: true });
    mkdirSync(join(dir, 'approvals'), { recursive: true });
    mkdirSync(join(dir, 'acts'), { recursive: true });
    mkdirSync(join(dir, 'reservations'), { recursive: true });
    if (!existsSync(this.eventsPath)) writeFileSync(this.eventsPath, '');
  }

  private get eventsPath(): string {
    return join(this.dir, 'events.jsonl');
  }
  private prPath(id: string): string {
    return join(this.dir, 'prs', `${id}.json`);
  }
  private approvalPath(id: string): string {
    return join(this.dir, 'approvals', `${id}.json`);
  }
  private actPath(id: string): string {
    return join(this.dir, 'acts', `${id}.json`);
  }
  private lifecyclePath(id: string): string {
    return join(this.dir, 'prs', `${id}.lifecycle`);
  }
  private reservationPath(id: string): string {
    return join(this.dir, 'reservations', `${id}.lock`);
  }

  private writeAtomic(path: string, data: string): void {
    const tmp = `${path}.tmp`;
    writeFileSync(tmp, data);
    renameSync(tmp, path);
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
    writeFileSync(this.eventsPath, `${JSON.stringify(e)}\n`, { flag: 'a' });
  }
  events(id?: string): DomainEvent[] {
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
      const fd = openSync(this.reservationPath(id), 'wx');
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
