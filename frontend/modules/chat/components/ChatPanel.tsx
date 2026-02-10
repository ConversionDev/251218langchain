"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2, Square } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { sendChatMessageStream } from "../services";
import type { MessageItem } from "../types";

/** 메시지 + 참고 문서(선택) */
type DisplayMessage = MessageItem & { contextPreview?: string };

/** 모델이 잘못 붙인 ```json / ``` 코드 블록만 제거 (앞쪽 빈 블록) */
function stripLeadingJsonCodeBlock(text: string): string {
  if (!text?.trim()) return text;
  let s = text.trim();
  if (s.startsWith("```json")) {
    s = s.slice(7).trimStart();
    if (s.startsWith("```")) s = s.slice(3).trimStart();
  } else if (s.startsWith("```")) {
    s = s.slice(3).trimStart();
    if (s.startsWith("```")) s = s.slice(3).trimStart();
  }
  return s.trim();
}

/** 모델이 텍스트로 출력한 도구 호출 JSON 줄 제거 (define 등) */
function stripToolCallJsonLines(text: string): string {
  if (!text?.trim()) return text;
  return text
    .split("\n")
    .filter((line) => {
      const t = line.trim();
      if (!t.startsWith("{")) return true;
      try {
        const o = JSON.parse(t) as { name?: string };
        return o?.name !== "define";
      } catch {
        return true;
      }
    })
    .join("\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

export function ChatPanel() {
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setLoading(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    setInput("");
    setError(null);
    const userMessage: MessageItem = { role: "user", content: text };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    const chatHistory: MessageItem[] = [...messages, userMessage].map((m) => ({
      role: m.role,
      content: m.content,
    }));

    setMessages((prev) => [
      ...prev,
      { role: "assistant", content: "", contextPreview: undefined },
    ]);

    try {
      await sendChatMessageStream(
        {
          message: text,
          use_rag: true,
          chat_history: chatHistory.slice(0, -1),
        },
        {
          onChunk(content) {
            setMessages((prev) => {
              const next = [...prev];
              const last = next[next.length - 1];
              if (last?.role === "assistant")
                next[next.length - 1] = { ...last, content: last.content + content };
              return next;
            });
          },
          onContextPreview(preview) {
            setMessages((prev) => {
              const next = [...prev];
              const last = next[next.length - 1];
              if (last?.role === "assistant")
                next[next.length - 1] = { ...last, contextPreview: preview ?? undefined };
              return next;
            });
          },
          onDone() {
            abortControllerRef.current = null;
            setLoading(false);
          },
          onError(msg) {
            setError(msg);
            setMessages((prev) => {
              const next = [...prev];
              const last = next[next.length - 1];
              if (last?.role === "assistant")
                next[next.length - 1] = { ...last, content: last.content || `오류: ${msg}` };
              return next;
            });
            setLoading(false);
          },
        },
        { signal: controller.signal }
      );
    } catch {
      abortControllerRef.current = null;
      setLoading(false);
    }
  };

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col rounded-lg border border-border bg-card">
      <div className="border-b border-border px-4 py-3">
        <h2 className="font-semibold text-foreground">RAG 채팅</h2>
        <p className="text-xs text-muted-foreground">
          등록된 데이터(Soccer 등)를 검색해 답변합니다.
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex h-full items-center justify-center text-muted-foreground text-sm">
            메시지를 입력하고 전송하세요.
          </div>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex flex-col gap-1 ${msg.role === "user" ? "items-end" : "items-start"}`}
          >
            <div
              className={`max-w-[85%] rounded-lg px-4 py-2 text-sm ${
                msg.role === "user"
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-foreground"
              }`}
            >
              <div className="whitespace-pre-wrap break-words">
                {msg.role === "assistant"
                  ? stripToolCallJsonLines(stripLeadingJsonCodeBlock(msg.content ?? "")) ||
                    (loading && i === messages.length - 1 ? "\u00a0" : "")
                  : msg.content || ""}
              </div>
            </div>
            {msg.role === "assistant" && msg.contextPreview !== undefined && (
              <details className="max-w-[85%] rounded border border-border bg-muted/50 px-3 py-2 text-xs text-muted-foreground" open={!!msg.contextPreview}>
                <summary className="cursor-pointer font-medium">참고한 문서 (RAG 검색 결과)</summary>
                {msg.contextPreview ? (
                  <pre className="mt-2 whitespace-pre-wrap break-words font-sans">{msg.contextPreview}</pre>
                ) : (
                  <p className="mt-2 text-muted-foreground">검색된 문서가 없습니다. (이 답변은 DB 검색 결과를 사용하지 않았습니다.)</p>
                )}
              </details>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="flex items-center gap-2 rounded-lg bg-muted px-4 py-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              답변 생성 중…
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <form
        onSubmit={handleSubmit}
        className="flex gap-2 border-t border-border p-4"
      >
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="무엇이든 물어보세요"
          disabled={loading}
          className="flex-1"
        />
        {loading ? (
          <Button
            type="button"
            variant="outline"
            onClick={handleStop}
            className="h-10 w-10 rounded-full border-border bg-background p-0 hover:bg-muted"
            aria-label="답변 생성 중지"
          >
            <Square className="h-4 w-4 fill-foreground" />
          </Button>
        ) : (
          <Button type="submit" disabled={!input.trim()} className="h-10 w-10 rounded-full p-0">
            <Send className="h-4 w-4" />
          </Button>
        )}
      </form>
      {error && (
        <div className="px-4 pb-2 text-sm text-destructive">{error}</div>
      )}
    </div>
  );
}
