// Append-only domain event log. The visual reducer consumes exactly these
// events; it never owns business state.

import type { Clock } from './clock.js';
import type { DomainEvent, EventType } from './types.js';

export class EventLog {
  private seq = 0;
  private readonly events: DomainEvent[] = [];

  constructor(private readonly clock: Clock) {}

  emit(type: EventType, pr_id: string, payload: Record<string, unknown> = {}, note?: string): DomainEvent {
    const ev: DomainEvent = { seq: this.seq++, t: this.clock.now(), type, pr_id, payload, note };
    this.events.push(ev);
    return ev;
  }

  all(): DomainEvent[] {
    return [...this.events];
  }
}
