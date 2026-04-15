/**
 * Spring 게이트웨이(OAuth) 연동 — 로그인 URL 발급 및 액세스 토큰 보관.
 * 백엔드: POST /auth/kakao|naver|google/login → { success, message, authUrl }
 * 로그인 완료 후: FRONTEND_CALLBACK_URL?token=JWT (application.yaml frontend.callback-url)
 */

export type OAuthProvider = "kakao" | "naver" | "google";

const STORAGE_KEY = "gateway_access_token";

export function getGatewayBaseUrl(): string {
  const raw =
    typeof window !== "undefined"
      ? (process.env.NEXT_PUBLIC_GATEWAY_URL ?? "http://localhost:8080")
      : (process.env.NEXT_PUBLIC_GATEWAY_URL ?? "http://localhost:8080");
  return raw.replace(/\/$/, "");
}

export type GatewayLoginResponse = {
  success: boolean;
  message?: string;
  authUrl?: string;
};

export async function fetchOAuthLoginUrl(provider: OAuthProvider): Promise<string> {
  const base = getGatewayBaseUrl();
  const res = await fetch(`${base}/auth/${provider}/login`, {
    method: "POST",
    headers: { Accept: "application/json" },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `게이트웨이 오류 (${res.status})`);
  }
  const data = (await res.json()) as GatewayLoginResponse;
  if (!data.success || !data.authUrl) {
    throw new Error(data.message ?? "로그인 URL을 받지 못했습니다.");
  }
  return data.authUrl;
}

/** 소셜 제공자 로그인 페이지로 이동(카카오/네이버/구글 호스트). */
export async function startOAuthLogin(provider: OAuthProvider): Promise<void> {
  const url = await fetchOAuthLoginUrl(provider);
  window.location.assign(url);
}

export function persistGatewayAccessToken(token: string): void {
  try {
    sessionStorage.setItem(STORAGE_KEY, token);
  } catch {
    /* ignore quota / private mode */
  }
}

export function getGatewayAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return sessionStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

export function clearGatewayAccessToken(): void {
  if (typeof window === "undefined") return;
  try {
    sessionStorage.removeItem(STORAGE_KEY);
  } catch {
    /* ignore */
  }
}
