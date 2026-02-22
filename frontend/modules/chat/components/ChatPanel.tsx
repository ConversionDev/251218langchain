"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2, Square, X, Plus, Paperclip, FileText, Sparkles } from "lucide-react";
import { useStore } from "@/store/useStore";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { DOCUMENT_ACCEPT } from "@/lib/documentExtensions";
import { sendChatMessageStream, uploadChatFiles, type SourceItem } from "../services";
import type { MessageItem } from "../types";

/** 개발/테스트용 추천 질문 (RAG·직원·공시·이력서 등) */
const RECOMMENDED_QUESTIONS = [
  "어떤 직원이 SAP FI 경험이 있나요?",
  "ISO 30414의 다양성 지표는 무엇인가요?",
  "IFRS S2 전환 준비도가 뭔가요?",
  "최근 입사한 직원들의 평균 연령은?",
  "전체 임직원 수와 공시 완성도 알려줘",
  "이 이력서를 분석해 주세요",
  "RAG에 어떤 문서가 등록되어 있나요?",
  "교육훈련 시간을 공시 지표로 어떻게 집계하나요?",
];

type AttachmentItem =
  | { id: string; type: "image"; data: string; name: string }
  | { id: string; type: "file"; name: string; file: File };
type DisplayMessage = MessageItem & {
  contextPreview?: string;
  /** RAG 출처 목록 (참고 문서 전부 표시) */
  sources?: SourceItem[] | null;
  /** 사용자 메시지에 첨부된 이미지(data URL) — 말풍선에 표시용 */
  attachmentImages?: string[];
  /** 사용자 메시지에 첨부된 파일(문서) 이름 — 말풍선에 이미지와 같은 형태로 표시 */
  attachmentFiles?: { name: string }[];
};

function dataUrlToBlob(dataUrl: string): Promise<Blob> {
  return fetch(dataUrl).then((r) => r.blob());
}

/** 선택된 직원이 있을 때 채팅 컨텍스트용 시스템 프롬프트 문구 생성 */
function buildSelectedEmployeeContext(employee: { id: string; name?: string | null; department?: string | null; jobTitle?: string | null }): string {
  const parts = [`현재 선택된 직원: ${employee.name ?? "이름 없음"}`, `ID: ${employee.id}`];
  if (employee.department) parts.push(`부서: ${employee.department}`);
  if (employee.jobTitle) parts.push(`직무: ${employee.jobTitle}`);
  return `${parts.join(", ")}. 사용자 질문이 이 직원에 관한 경우 해당 직원 정보를 활용해 답변하세요.`;
}

export function ChatPanel() {
  const selectedEmployee = useStore((s) => s.selectedEmployee);
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
          { id: crypto.randomUUID(), type: "file", name: file.name || "파일", file },
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
    const fileAttachments = attachments.filter((a): a is AttachmentItem & { type: "file" } => a.type === "file");
    const hadAttachments = attachments.length > 0;
    const filesToSend: (Blob | File)[] = [
      ...(imageAttachments.length > 0 ? await Promise.all(imageAttachments.map((a) => dataUrlToBlob(a.data))) : []),
      ...fileAttachments.map((a) => a.file),
    ];
    const fileNamesForUpload: string[] = [
      ...imageAttachments.map((_, i) => `image_${i}.png`),
      ...fileAttachments.map((a) => a.file.name),
    ];

    setInput("");
    setError(null);
    const attachmentDataUrls = imageAttachments.length > 0 ? imageAttachments.map((a) => a.data) : undefined;
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
    let fileNames: string[] | undefined;
    if (filesToSend.length > 0) {
      try {
        const up = await uploadChatFiles(filesToSend, {
          fileNames: fileNamesForUpload,
          signal: controller.signal,
        });
        fileIds = up.file_ids ?? [];
        fileNames = fileNamesForUpload;
      } catch (err) {
        setError(err instanceof Error ? err.message : "업로드 실패");
        setLoading(false);
        abortControllerRef.current = null;
        setMessages((prev) => prev.slice(0, -1));
        return;
      }
    }

    const systemPrompt = selectedEmployee
      ? buildSelectedEmployeeContext(selectedEmployee)
      : undefined;

    try {
      await sendChatMessageStream(
        {
          message: text || (hadAttachments ? "[이미지·파일 첨부]" : ""),
          use_rag: true,
          chat_history: chatHistory.slice(0, -1),
          ...(systemPrompt ? { system_prompt: systemPrompt } : {}),
          ...(fileIds?.length ? { file_ids: fileIds, file_names: fileNames } : {}),
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
          onSources(sources) {
            setMessages((prev) => {
              const next = [...prev];
              const last = next[next.length - 1];
              if (last?.role === "assistant")
                next[next.length - 1] = { ...last, sources: sources ?? undefined };
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
    <div
      className="relative flex min-h-0 flex-1 flex-col rounded-xl border border-slate-200/60 bg-slate-50/80 dark:border-white/10 dark:bg-white/5"
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {isDragging && (
        <div className="absolute inset-0 z-20 flex items-center justify-center rounded-xl border-2 border-dashed border-emerald-400 bg-white/95 text-center dark:bg-[#0f0f0f]/95">
          <div>
            <p className="text-sm font-medium text-emerald-600 dark:text-emerald-400">파일을 여기에 놓으세요</p>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">이미지·문서는 채팅에 첨부됩니다</p>
          </div>
        </div>
      )}
      <div className="flex items-center gap-2 border-b border-slate-200/60 px-4 py-3 dark:border-white/10">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-emerald-500 text-white">
          <Sparkles className="h-5 w-5" />
        </div>
        <div className="min-w-0 flex-1">
          <h2 className="font-semibold text-slate-900 dark:text-slate-100">HRInsight AI</h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            {selectedEmployee
              ? `선택 직원: ${selectedEmployee.name ?? "이름 없음"} — 질문 시 해당 직원 정보가 참고됩니다.`
              : "이력서·공시·역량 데이터 검색 및 답변"}
          </p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="mb-4 rounded-xl border border-slate-200/60 bg-white/60 p-4 dark:border-white/10 dark:bg-[#171717]/80">
            <p className="mb-3 text-sm font-medium text-slate-700 dark:text-slate-300">추천 질문</p>
            <ul className="flex flex-wrap gap-2">
              {RECOMMENDED_QUESTIONS.map((q) => (
                <li key={q}>
                  <button
                    type="button"
                    onClick={() => setInput(q)}
                    className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-left text-sm text-slate-700 shadow-sm transition-colors hover:border-emerald-300 hover:bg-emerald-50 dark:border-white/10 dark:bg-[#171717] dark:text-slate-300 dark:hover:border-emerald-600 dark:hover:bg-emerald-950/40"
                  >
                    {q}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] rounded-xl px-4 py-2.5 text-sm leading-relaxed ${
                msg.role === "user"
                  ? "bg-gradient-to-r from-blue-600 to-emerald-600 text-white"
                  : "bg-slate-100 text-slate-900 dark:bg-[#171717] dark:text-slate-100"
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
              {msg.role === "assistant" && (msg.contextPreview || (msg.sources && msg.sources.length > 0)) && (
                <details className="mt-2 text-xs text-muted-foreground" open>
                  <summary>참고 문서 {msg.sources?.length ? `(${msg.sources.length}건)` : ""}</summary>
                  {msg.sources && msg.sources.length > 0 ? (
                    <ul className="mt-1 max-h-64 list-inside list-disc space-y-1 overflow-y-auto">
                      {msg.sources.map((s, j) => (
                        <li key={j} className="break-words">
                          [출처: {[s.table && `table=${s.table}`, s.id != null && `id=${s.id}`, s.source && `source=${s.source}`, s.page != null && s.page !== "" && `page=${s.page}`, s.standard_type && `standard_type=${s.standard_type}`, s.unique_id && `unique_id=${s.unique_id}`].filter(Boolean).join(", ")}
                          {s.section_title ? ` — ${String(s.section_title).slice(0, 80)}${String(s.section_title).length > 80 ? "…" : ""}` : ""}]
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <pre className="mt-1 max-h-32 overflow-auto whitespace-pre-wrap break-words">
                      {msg.contextPreview}
                    </pre>
                  )}
                </details>
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {error && (
        <div className="border-t border-slate-200/60 px-4 py-2 text-sm text-red-600 dark:text-red-400">{error}</div>
      )}

      <form
        onSubmit={handleSubmit}
        className="relative border-t border-slate-200/60 p-4 dark:border-white/10"
      >
        {attachments.length > 0 && (
          <div className="mb-3 flex flex-wrap gap-2">
            {attachments.map((a) => (
              <div
                key={a.id}
                className="relative flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-100 px-2 py-2 pr-8 text-sm dark:border-white/10 dark:bg-[#171717]"
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
            accept={`image/*,${DOCUMENT_ACCEPT}`}
            className="hidden"
            multiple
            onChange={(e) => {
              addFiles(e.target.files);
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
            placeholder="질문이나 요청 사항을 입력하세요... (Shift+Enter로 줄바꿈)"
            className="min-w-0 flex-1 rounded-xl border-slate-200 bg-slate-100 dark:border-white/10 dark:bg-[#171717]"
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
