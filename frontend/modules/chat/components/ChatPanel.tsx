"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { sendChatMessageStream } from "../services";
import type { MessageItem } from "../types";

/** 메시지 + 참고 문서(선택) */
type DisplayMessage = MessageItem & { contextPreview?: string };

export function ChatPanel() {
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    setInput("");
    setError(null);
    const userMessage: MessageItem = { role: "user", content: text };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    const chatHistory: MessageItem[] = [...messages, userMessage].map((m) => ({
      role: m.role,
      content: m.content,
    }));

    setMessages((prev) => [
      ...prev,
      { role: "assistant", content: "", contextPreview: undefined },
    ]);

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
      }
    );
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
                {msg.content || (loading && i === messages.length - 1 && msg.role === "assistant" ? "\u00a0" : "")}
              </div>
            </div>
            {msg.role === "assistant" && msg.contextPreview && (
              <details className="max-w-[85%] rounded border border-border bg-muted/50 px-3 py-2 text-xs text-muted-foreground">
                <summary className="cursor-pointer font-medium">참고한 문서 (RAG 검색 결과)</summary>
                <pre className="mt-2 whitespace-pre-wrap break-words font-sans">{msg.contextPreview}</pre>
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
          placeholder="메시지 입력..."
          disabled={loading}
          className="flex-1"
        />
        <Button type="submit" disabled={loading || !input.trim()}>
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
        </Button>
      </form>
      {error && (
        <div className="px-4 pb-2 text-sm text-destructive">{error}</div>
      )}
    </div>
  );
}
