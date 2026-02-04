"use client";

import { useState, useEffect } from "react";

/**
 * 클라이언트 마운트 완료 여부를 반환합니다.
 * Zustand persist 등으로 인한 SSR/클라이언트 Hydration 불일치를 막기 위해
 * 스토어를 구독하는 UI는 이 훅으로 마운트 후에만 렌더하세요.
 */
export function useHydrated(): boolean {
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    setHydrated(true);
  }, []);

  return hydrated;
}
