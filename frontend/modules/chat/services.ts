/**
 * 채팅 API 클라이언트 (업로드 → file_ids, 채팅 스트림 JSON)
 * 백엔드: POST /api/agent/upload, POST /api/agent/chat/stream
 */

import type { AgentRequest } from "./types";

const API_BASE =
  typeof window !== "undefined"
    ? (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000")
    : "http://localhost:8000";

export interface StreamEvent {
  content?: string;
  context_preview?: string | null;
  semantic_action?: string | null;
  error?: string;
}

/** 채팅 첨부용 파일 업로드. POST /api/agent/upload → file_ids */
export async function uploadChatFiles(
  files: Blob[],
  options?: { signal?: AbortSignal }
): Promise<{ file_ids: string[] }> {
  const form = new FormData();
  files.forEach((blob, i) => {
    const ext = blob.type?.startsWith("image/png") ? "png" : "jpg";
    form.append("files", blob, `image_${i}.${ext}`);
  });
  const res = await fetch(`${API_BASE}/api/agent/upload`, {
    method: "POST",
    body: form,
    signal: options?.signal,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `업로드 실패 (${res.status})`);
  }
  return res.json();
}

/** 스트리밍 채팅. POST /api/agent/chat/stream (JSON만) */
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
            const event = raw ? (JSON.parse(raw) as StreamEvent) : null;
            if (event?.content != null) callbacks.onChunk(event.content);
            if (event?.context_preview !== undefined)
              callbacks.onContextPreview?.(event.context_preview ?? null);
            if (event?.error) callbacks.onError?.(event.error);
          } catch {
            // ignore non-JSON
          }
        }
      }
    }
    if (buffer.startsWith("data: ")) {
      const raw = buffer.slice(6).trim();
      if (raw !== "[DONE]") {
        try {
          const event = raw ? (JSON.parse(raw) as StreamEvent) : null;
          if (event?.content != null) callbacks.onChunk(event.content);
          if (event?.context_preview !== undefined)
            callbacks.onContextPreview?.(event.context_preview ?? null);
          if (event?.error) callbacks.onError?.(event.error);
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
      // ignore
    }
  }
}
