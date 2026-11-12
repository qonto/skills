import { useEffect, useRef } from 'react';

/** requestAnimationFrame play-clock. Calls onTick(dtMs) each frame while playing.
 * The callback is held in a ref so changing it does not restart the loop. */
export function useClock(playing: boolean, onTick: (dtMs: number) => void): void {
  const cb = useRef(onTick);
  cb.current = onTick;

  useEffect(() => {
    if (!playing) return;
    let raf = 0;
    let last = performance.now();
    const loop = (now: number) => {
      const dt = now - last;
      last = now;
      cb.current(dt);
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [playing]);
}
