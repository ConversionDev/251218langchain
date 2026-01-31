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
 * @param request - 에이전트 요청
 * @param signal - 취소 시 사용할 AbortSignal (선택)
 */
export async function* sendAgentMessageStream(
  request: AgentRequest,
  signal?: AbortSignal
): AsyncGenerator<string, void, unknown> {
  const response = await fetch("/api/v1/agent/chat/stream", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
    signal,
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
    if (signal?.aborted) break;
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

