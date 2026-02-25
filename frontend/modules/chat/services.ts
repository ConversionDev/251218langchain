/**
 * 채팅 API 클라이언트 (업로드 → file_ids, 채팅 스트림 JSON)
 * 백엔드: POST /api/agent/upload, POST /api/agent/chat/stream
 */

import type { AgentRequest } from "./types";

const API_BASE =
  typeof window !== "undefined"
    ? (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000")
    : "http://localhost:8000";

export interface SourceItem {
  table?: string;
  id?: number;
  source?: string;
  page?: string | number;
  standard_type?: string;
  section_title?: string;
  unique_id?: string;
}

export interface StreamEvent {
  content?: string;
  context_preview?: string | null;
  sources?: SourceItem[] | null;
  error?: string;
}

/** 채팅 첨부용 파일 업로드 (이미지 + 문서). POST /api/agent/upload → file_ids */
export async function uploadChatFiles(
  files: (Blob | File)[],
  options?: { fileNames?: string[]; signal?: AbortSignal }
): Promise<{ file_ids: string[] }> {
  const form = new FormData();
  const names = options?.fileNames;
  files.forEach((file, i) => {
    const name =
      names?.[i] ?? (file instanceof File ? file.name : `image_${i}.${file.type?.startsWith("image/png") ? "png" : "jpg"}`);
    form.append("files", file, name);
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

const CHAT_STORAGE_KEY = "chat_thread_id";

/** 저장된 thread_id 반환. 없으면 새로 생성해 저장 후 반환 */
export function getOrCreateThreadId(): string {
  if (typeof window === "undefined") return "";
  let id = sessionStorage.getItem(CHAT_STORAGE_KEY);
  if (!id) {
    id = crypto.randomUUID?.() ?? `thread_${Date.now()}`;
    sessionStorage.setItem(CHAT_STORAGE_KEY, id);
  }
  return id;
}

/** 현재 thread_id만 반환 (없으면 null) */
export function getStoredThreadId(): string | null {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem(CHAT_STORAGE_KEY);
}

/** thread_id 저장 (초기화 시 새 ID 저장용) */
export function setStoredThreadId(threadId: string): void {
  if (typeof window === "undefined") return;
  sessionStorage.setItem(CHAT_STORAGE_KEY, threadId);
}

/** 대화 내역 조회. GET /api/agent/threads/:thread_id/history */
export async function getThreadHistory(threadId: string): Promise<{ thread_id: string; messages: Array<{ role: string; content: string }> }> {
  const res = await fetch(`${API_BASE}/api/agent/threads/${encodeURIComponent(threadId)}/history`);
  if (!res.ok) throw new Error(`내역 조회 실패 (${res.status})`);
  return res.json();
}

/** 대화 초기화. DELETE /api/agent/threads/:thread_id */
export async function deleteThread(threadId: string): Promise<{ status: string; thread_id: string }> {
  const res = await fetch(`${API_BASE}/api/agent/threads/${encodeURIComponent(threadId)}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`삭제 실패 (${res.status})`);
  return res.json();
}

/** 스트리밍 채팅. POST /api/agent/chat/stream (JSON만) */
export async function sendChatMessageStream(
  payload: AgentRequest,
  callbacks: {
    onChunk: (content: string) => void;
    onContextPreview?: (preview: string | null) => void;
    onSources?: (sources: SourceItem[] | null) => void;
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
    callbacks.onDone?.();
    return;
  }
  const reader = res.body?.getReader();
  if (!reader) {
    callbacks.onError?.("스트림을 읽을 수 없습니다.");
    callbacks.onDone?.();
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
            if (event?.sources !== undefined) callbacks.onSources?.(event.sources ?? null);
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
          if (event?.sources !== undefined) callbacks.onSources?.(event.sources ?? null);
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
