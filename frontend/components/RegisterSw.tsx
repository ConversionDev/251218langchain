"use client";

import { useEffect } from "react";

/**
 * 빌드 후 Workbox가 생성한 public/sw.js를 등록합니다.
 * 프로덕션에서만 등록. 개발 시에는 기존 SW 해제하여 Turbopack 404 방지.
 */
export function RegisterSw() {
  useEffect(() => {
    if (typeof window === "undefined" || !("serviceWorker" in navigator)) return;
    const isProd = process.env.NODE_ENV === "production";

    if (isProd) {
      window.addEventListener("load", () => {
        navigator.serviceWorker
          .register("/sw.js", { scope: "/" })
          .then((reg) => {
            if (reg.installing) reg.installing.addEventListener("statechange", () => {});
          })
          .catch(() => {});
      });
    } else {
      // 개발: 이전에 등록된 SW 해제 → Turbopack 청크 404 / bad-precaching-response 방지
      navigator.serviceWorker.getRegistrations().then((regs) => {
        regs.forEach((r) => r.unregister());
      });
    }
  }, []);

  return null;
}
