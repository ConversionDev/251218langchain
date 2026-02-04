"use client";

import { useEffect } from "react";

/**
 * 빌드 후 Workbox가 생성한 public/sw.js를 등록합니다.
 * 프로덕션 또는 sw.js가 존재할 때만 등록합니다.
 */
export function RegisterSw() {
  useEffect(() => {
    if (typeof window === "undefined" || !("serviceWorker" in navigator)) return;
    const isProd = process.env.NODE_ENV === "production";
    if (!isProd) return;

    window.addEventListener("load", () => {
      navigator.serviceWorker
        .register("/sw.js", { scope: "/" })
        .then((reg) => {
          if (reg.installing) reg.installing.addEventListener("statechange", () => {});
        })
        .catch(() => {});
    });
  }, []);

  return null;
}
