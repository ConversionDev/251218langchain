"use client";

import { useState, useEffect, useRef } from "react";

const DURATION_MS = 400;

/**
 * 목표 값으로 부드럽게 카운트업되는 숫자를 반환합니다.
 * 슬라이더 등으로 값이 바뀔 때 "손맛" 있는 피드백에 사용.
 */
export function useCountUp(value: number, durationMs: number = DURATION_MS): number {
  const [display, setDisplay] = useState(value);
  const prevValue = useRef(value);
  const rafId = useRef<number>(0);
  const startTime = useRef(0);

  useEffect(() => {
    const target = value;
    const start = prevValue.current;

    if (start === target) {
      setDisplay(target);
      return;
    }

    startTime.current = performance.now();

    const tick = (now: number) => {
      const elapsed = now - startTime.current;
      const t = Math.min(elapsed / durationMs, 1);
      const eased = 1 - (1 - t) * (1 - t);
      const current = start + (target - start) * eased;
      setDisplay(Math.round(current * 100) / 100);
      if (t >= 1) {
        prevValue.current = target;
      } else {
        rafId.current = requestAnimationFrame(tick);
      }
    };

    rafId.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafId.current);
  }, [value, durationMs]);

  return display;
}
