// Injectable clock so synthetic runs are fully deterministic (stable hashes,
// fingerprints, event times) while real runs use wall-clock.

export interface Clock {
  /** current instant as ISO-8601 string. */
  now(): string;
}

/** Deterministic clock: starts at `startIso`, advances `stepMs` on every now(). */
export function fixedClock(startIso: string, stepMs = 1000): Clock {
  let t = Date.parse(startIso);
  return {
    now() {
      const iso = new Date(t).toISOString();
      t += stepMs;
      return iso;
    },
  };
}

/** Frozen clock: always returns the same instant (useful for act revalidation). */
export function frozenClock(iso: string): Clock {
  return { now: () => iso };
}

export const systemClock: Clock = {
  now: () => new Date().toISOString(),
};

export function addMinutes(iso: string, minutes: number): string {
  return new Date(Date.parse(iso) + minutes * 60_000).toISOString();
}

export function isBefore(a: string, b: string): boolean {
  return Date.parse(a) < Date.parse(b);
}
