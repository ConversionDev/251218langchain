/**
 * LangGraph Agent API 호출 함수
 */

import type {
  AgentRequest,
  AgentResponse,
  AgentHealth,
  ProviderInfo,
  ToolInfo,
} from "../types";

// API 기본 URL (환경 변수 또는 기본값)
const getApiUrl = () => {
  // 클라이언트 사이드에서는 NEXT_PUBLIC_ 환경 변수 사용
  if (typeof window !== "undefined") {
    return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  }
  // 서버 사이드
  return process.env.BACKEND_URL || "http://localhost:8000";
};

/**
 * LangGraph Agent 채팅 API 호출
 */
export async function sendAgentMessage(
  request: AgentRequest
): Promise<AgentResponse> {
  const response = await fetch("/api/v1/agent/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || error.error || `HTTP ${response.status}: 요청 실패`);
  }

  return response.json();
}

/**
 * LangGraph Agent 스트리밍 채팅
 */
export async function* sendAgentMessageStream(
  request: AgentRequest
): AsyncGenerator<string, void, unknown> {
  const response = await fetch("/api/v1/agent/chat/stream", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || error.error || `HTTP ${response.status}: 스트리밍 요청 실패`);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error("스트리밍 응답을 읽을 수 없습니다.");
  }

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        const data = line.slice(6);
        if (data === "[DONE]") {
          return;
        }
        yield data;
      }
    }
  }
}

/**
 * 사용 가능한 LLM 제공자 목록 조회
 */
export async function getProviders(): Promise<ProviderInfo[]> {
  const response = await fetch("/api/v1/agent/providers");

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || error.error || `HTTP ${response.status}: 제공자 목록 조회 실패`);
  }

  return response.json();
}

/**
 * 사용 가능한 도구 목록 조회
 */
export async function getTools(): Promise<{ tools: ToolInfo[] }> {
  const response = await fetch("/api/v1/agent/tools");

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || error.error || `HTTP ${response.status}: 도구 목록 조회 실패`);
  }

  return response.json();
}

/**
 * 에이전트 상태 확인
 */
export async function getAgentHealth(): Promise<AgentHealth> {
  const response = await fetch("/api/v1/agent/health");

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || error.error || `HTTP ${response.status}: 상태 확인 실패`);
  }

  return response.json();
}

/**
 * 기존 LangChain API 채팅 (호환성용)
 */
export async function sendLangChainMessage(
  message: string,
  history: { role: string; content: string }[],
  modelType: "local"
): Promise<{ response: string }> {
  const response = await fetch("/api/v1/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message,
      history,
      model_type: modelType,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.error || `HTTP ${response.status}: 요청 실패`);
  }

  return response.json();
}

/**
 * LangChain 스트리밍 채팅
 */
export async function* sendLangChainMessageStream(
  message: string,
  history: { role: string; content: string }[],
  modelType: "local"
): AsyncGenerator<string, void, unknown> {
  const response = await fetch("/api/v1/chat/stream", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message,
      history,
      model_type: modelType,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || error.error || `HTTP ${response.status}: 스트리밍 요청 실패`);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error("스트리밍 응답을 읽을 수 없습니다.");
  }

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        const data = line.slice(6);
        if (data === "[DONE]") {
          return;
        }
        yield data;
      }
    }
  }
}
