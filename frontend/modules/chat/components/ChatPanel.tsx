"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2, Square, X, Plus, Paperclip, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { sendChatMessageStream, uploadChatFiles } from "../services";
import type { MessageItem } from "../types";

type AttachmentItem =
  | { id: string; type: "image"; data: string; name: string }
  | { id: string; type: "file"; name: string };
type DisplayMessage = MessageItem & {
  contextPreview?: string;
  /** 사용자 메시지에 첨부된 이미지(data URL) — 말풍선에 표시용 */
  attachmentImages?: string[];
  /** 사용자 메시지에 첨부된 파일(문서) 이름 — 말풍선에 이미지와 같은 형태로 표시 */
  attachmentFiles?: { name: string }[];
};

function dataUrlToBlob(dataUrl: string): Promise<Blob> {
  return fetch(dataUrl).then((r) => r.blob());
}

export function ChatPanel() {
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [input, setInput] = useState("");
  const [attachments, setAttachments] = useState<AttachmentItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [plusOpen, setPlusOpen] = useState(false);
  const plusRef = useRef<HTMLDivElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    if (!plusOpen) return;
    const close = (e: MouseEvent) => {
      if (plusRef.current && !plusRef.current.contains(e.target as Node)) setPlusOpen(false);
    };
    document.addEventListener("click", close);
    return () => document.removeEventListener("click", close);
  }, [plusOpen]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const addImage = (file: File) => {
    if (!file.type.startsWith("image/")) return false;
    const reader = new FileReader();
    reader.onload = () => {
      setAttachments((prev) => [
        ...prev,
        { id: crypto.randomUUID(), type: "image", data: reader.result as string, name: file.name || "이미지" },
      ]);
    };
    reader.readAsDataURL(file);
    return true;
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    const items = e.clipboardData?.items;
    if (!items) return;
    for (const item of items) {
      if (item.type.startsWith("image/")) {
        e.preventDefault();
        const file = item.getAsFile();
        if (file) addImage(file);
        break;
      }
    }
  };

  const removeAttachment = (id: string) => {
    setAttachments((prev) => prev.filter((a) => a.id !== id));
  };

  const addFiles = (files: FileList | null) => {
    if (!files?.length) return;
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      if (file.type.startsWith("image/")) {
        addImage(file);
      } else {
        setAttachments((prev) => [
          ...prev,
          { id: crypto.randomUUID(), type: "file", name: file.name || "파일" },
        ]);
      }
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isDragging) setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!e.currentTarget.contains(e.relatedTarget as Node)) setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (loading) return;
    addFiles(e.dataTransfer.files);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const text = input.trim();
    const hasContent = text || attachments.length > 0;
    if (!hasContent || loading) return;

    const imageAttachments = attachments.filter((a): a is AttachmentItem & { type: "image" } => a.type === "image");
    const hadAttachments = attachments.length > 0;
    const filesToSend: Blob[] =
      imageAttachments.length > 0
        ? await Promise.all(imageAttachments.map((a) => dataUrlToBlob(a.data)))
        : [];

    setInput("");
    setError(null);
    const attachmentDataUrls = imageAttachments.length > 0 ? imageAttachments.map((a) => a.data) : undefined;
    const fileAttachments = attachments.filter((a): a is AttachmentItem & { type: "file" } => a.type === "file");
    const attachmentFileNames = fileAttachments.length > 0 ? fileAttachments.map((a) => ({ name: a.name })) : undefined;
    setAttachments([]);
    const userMessage: DisplayMessage = {
      role: "user",
      content: text || (hadAttachments ? "[이미지·파일 첨부]" : ""),
      ...(attachmentDataUrls?.length ? { attachmentImages: attachmentDataUrls } : {}),
      ...(attachmentFileNames?.length ? { attachmentFiles: attachmentFileNames } : {}),
    };
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

    let fileIds: string[] | undefined;
    if (filesToSend.length > 0) {
      try {
        const up = await uploadChatFiles(filesToSend, { signal: controller.signal });
        fileIds = up.file_ids ?? [];
      } catch (err) {
        setError(err instanceof Error ? err.message : "업로드 실패");
        setLoading(false);
        abortControllerRef.current = null;
        setMessages((prev) => prev.slice(0, -1));
        return;
      }
    }

    try {
      await sendChatMessageStream(
        {
          message: text || (hadAttachments ? "[이미지 첨부]" : ""),
          use_rag: true,
          chat_history: chatHistory.slice(0, -1),
          ...(fileIds?.length ? { file_ids: fileIds } : {}),
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

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setLoading(false);
  };

  return (
    <div className="flex h-[calc(100vh-12rem)] flex-col rounded-lg border border-border bg-card">
      <div className="border-b border-border px-4 py-3">
        <h2 className="font-semibold text-foreground">RAG 채팅</h2>
        <p className="text-xs text-muted-foreground">
          등록된 데이터를 검색해 답변합니다. 이미지 첨부 시 업로드 후 분석합니다.
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
                msg.role === "user"
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-foreground"
              }`}
            >
              {msg.role === "user" && (msg.attachmentImages?.length || msg.attachmentFiles?.length) ? (
                <div className="mb-2 flex flex-wrap gap-2">
                  {msg.attachmentImages?.map((src, j) => (
                    <img
                      key={`img-${j}`}
                      src={src}
                      alt=""
                      className="max-h-32 max-w-full rounded border border-white/20 object-contain"
                    />
                  ))}
                  {msg.attachmentFiles?.map((f, j) => (
                    <div
                      key={`file-${j}`}
                      className="flex items-center gap-2 rounded border border-white/20 bg-white/10 px-3 py-2"
                    >
                      <FileText className="h-6 w-6 shrink-0 text-white/90" />
                      <span className="max-w-[180px] truncate text-sm text-white/95">{f.name}</span>
                    </div>
                  ))}
                </div>
              ) : null}
              <div className="whitespace-pre-wrap">{msg.content || "…"}</div>
              {msg.role === "assistant" && msg.contextPreview && (
                <details className="mt-2 text-xs text-muted-foreground">
                  <summary>참고 문서</summary>
                  <pre className="mt-1 max-h-32 overflow-auto whitespace-pre-wrap break-words">
                    {msg.contextPreview}
                  </pre>
                </details>
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {error && (
        <div className="border-t border-border px-4 py-2 text-sm text-destructive">{error}</div>
      )}

      <form
        onSubmit={handleSubmit}
        className={`relative border-t border-border p-3 transition-colors ${isDragging ? "bg-primary/5" : ""}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {messages.length === 0 && !isDragging && attachments.length === 0 && (
          <p className="mb-2 text-center text-xs text-muted-foreground">
            메시지를 입력하거나 이미지를 첨부해 전송하세요.
          </p>
        )}
        {isDragging && (
          <div className="absolute inset-0 z-10 flex items-center justify-center rounded-b-lg border-2 border-dashed border-primary bg-background/95 py-6 text-center">
            <p className="text-sm font-medium text-primary">파일을 여기에 놓으세요</p>
            <p className="mt-1 text-xs text-muted-foreground">이미지는 채팅에 첨부됩니다</p>
          </div>
        )}
        {attachments.length > 0 && (
          <div className="mb-3 flex flex-wrap gap-2">
            {attachments.map((a) => (
              <div
                key={a.id}
                className="relative flex items-center gap-2 rounded-lg border border-border bg-muted/50 px-2 py-2 pr-8 text-sm"
              >
                {a.type === "image" ? (
                  <img
                    src={a.data}
                    alt=""
                    className="h-14 w-14 shrink-0 rounded object-cover"
                  />
                ) : (
                  <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded border border-border bg-background">
                    <FileText className="h-7 w-7 text-muted-foreground" />
                  </div>
                )}
                <div className="min-w-0">
                  <p className="truncate font-medium text-foreground">{a.name}</p>
                  <p className="text-xs text-muted-foreground">{a.type === "image" ? "이미지" : "문서"}</p>
                </div>
                <button
                  type="button"
                  onClick={() => removeAttachment(a.id)}
                  className="absolute right-1.5 top-1/2 -translate-y-1/2 rounded-full p-1 text-muted-foreground hover:bg-destructive hover:text-destructive-foreground"
                  aria-label="제거"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        )}
        <div className="flex items-center gap-2">
          <input
            type="file"
            ref={fileInputRef}
            accept="image/*"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) addImage(f);
              e.target.value = "";
            }}
          />
          <div ref={plusRef} className="relative shrink-0">
            <Button
              type="button"
              variant="outline"
              className="h-9 w-9 shrink-0 p-0"
              onClick={() => setPlusOpen((o) => !o)}
              aria-label="첨부"
            >
              <Plus className="h-4 w-4" />
            </Button>
            {plusOpen && (
              <div className="absolute left-0 bottom-full z-50 mb-2 w-56 rounded-xl border border-border bg-card py-1.5 shadow-lg">
                <button
                  type="button"
                  className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm text-foreground transition-colors hover:bg-accent"
                  onClick={() => {
                    setPlusOpen(false);
                    fileInputRef.current?.click();
                  }}
                >
                  <Paperclip className="h-5 w-5 shrink-0 text-muted-foreground" />
                  사진 및 파일 추가
                </button>
              </div>
            )}
          </div>
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onPaste={handlePaste}
            placeholder="무엇이든 물어보세요"
            className="min-w-0 flex-1"
            disabled={loading}
          />
          {loading ? (
            <Button type="button" variant="outline" className="h-9 w-9 shrink-0 p-0" onClick={handleStop} aria-label="중지">
              <Square className="h-4 w-4" />
            </Button>
          ) : (
            <Button type="submit" className="h-9 w-9 shrink-0 p-0" disabled={!input.trim() && attachments.length === 0} aria-label="전송">
              <Send className="h-4 w-4" />
            </Button>
          )}
        </div>
      </form>
    </div>
  );
}
