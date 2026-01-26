/**
 * 스팸 감지 API 클라이언트
 */

import type {
  EmailMetadata,
  SpamDetectionRequest,
  SpamDetectionResponse,
} from "@/lib/types/spam";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * 스팸 감지 API 호출
 */
export async function detectSpam(
  emailMetadata: EmailMetadata
): Promise<SpamDetectionResponse> {
  const request: SpamDetectionRequest = {
    email_metadata: emailMetadata,
  };

  const apiUrl = "/api/v1/mail/filter";
  console.log("[DEBUG] API 호출:", apiUrl);
  console.log("[DEBUG] 요청 데이터:", request);

  try {
    const response = await fetch(apiUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    console.log("[DEBUG] 응답 상태:", response.status, response.statusText);

    if (!response.ok) {
      const errorText = await response.text();
      console.error("[ERROR] 응답 오류:", errorText);

      let errorDetail: string;
      try {
        const errorJson = JSON.parse(errorText);
        errorDetail = errorJson.detail || errorJson.message || errorText;
      } catch {
        errorDetail = errorText || `HTTP ${response.status}: ${response.statusText}`;
      }

      throw new Error(errorDetail);
    }

    const result = await response.json();
    console.log("[DEBUG] 응답 데이터:", result);
    return result;
  } catch (error) {
    if (error instanceof TypeError && error.message.includes("fetch")) {
      throw new Error(
        `백엔드 서버에 연결할 수 없습니다. (${apiUrl})\n` +
        `백엔드 서버가 실행 중인지 확인하세요.`
      );
    }
    throw error;
  }
}

/**
 * 헬스 체크
 */
export async function checkSpamDetectionHealth(): Promise<{
  status: string;
  service: string;
}> {
  const response = await fetch(`${API_BASE}/mcp/health`);

  if (!response.ok) {
    throw new Error("헬스 체크 실패");
  }

  return response.json();
}

