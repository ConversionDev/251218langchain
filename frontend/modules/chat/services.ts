import type { AgentRequest } from "./types";

const API_BASE =
  typeof window !== "undefined"
    ? (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000")
    : "http://localhost:8000";

/** 스트림 이벤트: content 청크 또는 context_preview / semantic_action / error */
export interface StreamEvent {
  content?: string;
  context_preview?: string;
  semantic_action?: string | null;
  error?: string;
}

/**
 * 스트리밍 채팅: POST /api/agent/chat/stream, SSE로 청크 수신.
 * onChunk(content), onContextPreview(preview), onDone() 콜백으로 전달.
 * signal 전달 시 취소 가능.
 */
export async function sendChatMessageStream(
  payload: AgentRequest,
  callbacks: {
    onChunk: (content: string) => void;
    onContextPreview?: (preview: string | null) => void;
    onDone?: () => void;
    onError?: (message: string) => void;
  },
  options?: { signal?: AbortSignal }
): Promise<void> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}/api/agent/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: options?.signal,
    });
  } catch (e) {
    if (e instanceof Error && e.name === "AbortError") {
      callbacks.onDone?.();
      return;
    }
    throw e;
  }
  if (!res.ok) {
    if (options?.signal?.aborted) return;
    const text = await res.text();
    callbacks.onError?.(`채팅 요청 실패 (${res.status}): ${text}`);
    return;
  }
  const reader = res.body?.getReader();
  if (!reader) {
    callbacks.onError?.("스트림을 읽을 수 없습니다.");
    return;
  }
  const decoder = new TextDecoder();
  let buffer = "";
  try {
    while (true) {
      if (options?.signal?.aborted) {
        await reader.cancel();
        callbacks.onDone?.();
        return;
      }
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";
      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const raw = line.slice(6).trim();
          if (raw === "[DONE]") {
            callbacks.onDone?.();
            return;
          }
          try {
            const event = JSON.parse(raw) as StreamEvent;
            if (event.content != null) callbacks.onChunk(event.content);
            if (event.context_preview !== undefined) callbacks.onContextPreview?.(event.context_preview);
            if (event.error) callbacks.onError?.(event.error);
          } catch {
            // ignore non-JSON lines
          }
        }
      }
    }
    if (buffer.startsWith("data: ")) {
      const raw = buffer.slice(6).trim();
      if (raw !== "[DONE]") {
        try {
          const event = JSON.parse(raw) as StreamEvent;
          if (event.content != null) callbacks.onChunk(event.content);
          if (event.context_preview !== undefined) callbacks.onContextPreview?.(event.context_preview);
          if (event.error) callbacks.onError?.(event.error);
        } catch {
          // ignore
        }
      }
    }
    callbacks.onDone?.();
  } catch (e) {
    if (e instanceof Error && e.name === "AbortError") {
      callbacks.onDone?.();
      return;
    }
    throw e;
  } finally {
    try {
      reader.releaseLock();
    } catch {
      // ignore if already released or cancelled
    }
  }
}
