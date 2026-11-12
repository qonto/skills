// Small persistence seam with atomic one-shot reservation (compare-and-set).
// MemoryStore is used by the browser demo and tests; the Node FileStore
// (src/node/fileStore.ts) gives the same guarantees across CLI processes.

import type { ActResult, Approval, DomainEvent, LifecycleStatus, StoredPr } from './types.js';

export interface PrStore {
  putPr(stored: StoredPr): void;
  getPr(id: string): StoredPr | null;

  putApproval(a: Approval): void;
  getApproval(id: string): Approval | null;

  putLifecycle(id: string, status: LifecycleStatus): void;
  getLifecycle(id: string): LifecycleStatus | null;

  appendEvent(e: DomainEvent): void;
  events(id?: string): DomainEvent[];

  putActResult(r: ActResult): void;
  getActResult(id: string): ActResult | null;

  /** Atomic single-use reservation. Returns true only for the caller that wins. */
  reserveOnce(id: string): boolean;
  isReserved(id: string): boolean;
}

export class MemoryStore implements PrStore {
  private prs = new Map<string, StoredPr>();
  private approvals = new Map<string, Approval>();
  private lifecycle = new Map<string, LifecycleStatus>();
  private acts = new Map<string, ActResult>();
  private reserved = new Set<string>();
  private log: DomainEvent[] = [];

  putPr(stored: StoredPr): void {
    // Immutable body: store a deep copy so external mutation cannot alter it.
    this.prs.set(stored.body.pr_id, structuredCloneSafe(stored));
  }
  getPr(id: string): StoredPr | null {
    const s = this.prs.get(id);
    return s ? structuredCloneSafe(s) : null;
  }

  putApproval(a: Approval): void {
    this.approvals.set(a.pr_id, { ...a });
  }
  getApproval(id: string): Approval | null {
    const a = this.approvals.get(id);
    return a ? { ...a } : null;
  }

  putLifecycle(id: string, status: LifecycleStatus): void {
    this.lifecycle.set(id, status);
  }
  getLifecycle(id: string): LifecycleStatus | null {
    return this.lifecycle.get(id) ?? null;
  }

  appendEvent(e: DomainEvent): void {
    this.log.push(e);
  }
  events(id?: string): DomainEvent[] {
    return id ? this.log.filter((e) => e.pr_id === id) : [...this.log];
  }

  putActResult(r: ActResult): void {
    this.acts.set(r.pr_id, r);
  }
  getActResult(id: string): ActResult | null {
    return this.acts.get(id) ?? null;
  }

  reserveOnce(id: string): boolean {
    if (this.reserved.has(id)) return false;
    this.reserved.add(id);
    return true;
  }
  isReserved(id: string): boolean {
    return this.reserved.has(id);
  }
}

function structuredCloneSafe<T>(v: T): T {
  return JSON.parse(JSON.stringify(v)) as T;
}
