"use client";

import { useEffect, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { persistGatewayAccessToken } from "@/modules/auth/gatewayAuth";

/**
 * 게이트웨이 OAuth 성공 후 리다이렉트: ?token=JWT 를 sessionStorage에 저장하고 URL에서 제거.
 */
export function GatewayTokenCapture() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const done = useRef(false);

  useEffect(() => {
    if (done.current) return;
    const token = searchParams.get("token");
    const error = searchParams.get("error");
    if (!token && !error) return;
    done.current = true;
    if (token) {
      persistGatewayAccessToken(token);
    }
    const path = window.location.pathname;
    router.replace(path);
  }, [searchParams, router]);

  return null;
}
