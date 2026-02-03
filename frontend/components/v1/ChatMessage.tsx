"use client";

import { useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";

interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: Date;
  provider?: string;
  usedRag?: boolean;
  semantic_action?: string | null; // BLOCK, RULE_BASED, POLICY_BASED, null=미분류
}

interface ChatMessageProps {
  message: Message;
}

// 일반 텍스트를 마크다운 형식으로 변환하는 헬퍼 함수
function formatPlainText(text: string): string {
  if (!text) return text;

  let formatted = text;

  // === 숫자 리스트 처리 ===
  // "다:1. **항목**" → "다:\n\n1. **항목**"
  formatted = formatted.replace(/(:)(\s*)(\d+\.\s+)/g, ':\n\n$3');

  // "다.1. **항목**" → "다.\n\n1. **항목**"
  formatted = formatted.replace(/(\.)(\s*)(\d+\.\s+\*\*)/g, '.\n\n$3');

  // "다.1. 항목" (볼드 없는 경우) → "다.\n\n1. 항목"
  formatted = formatted.replace(/(\.)(\s*)(\d+\.\s+[^\*\n])/g, '.\n\n$3');

  // === 불릿 리스트 처리 ===
  // "다. - **항목**" → "다.\n\n- **항목**"
  formatted = formatted.replace(/(\.)(\s*)(-\s+\*\*)/g, '.\n\n$3');

  // "다: - **항목**" → "다:\n\n- **항목**"
  formatted = formatted.replace(/(:)(\s*)(-\s+\*\*)/g, ':\n\n$3');

  // 일반 텍스트 뒤 불릿 "텍스트 - **항목**"
  formatted = formatted.replace(/([가-힣a-zA-Z])(\s*)(-\s+\*\*)/g, '$1\n\n$3');

  // === 소제목/섹션 구분 ===
  // "**제목**:" 뒤에 내용이 바로 오면 줄바꿈
  formatted = formatted.replace(/(\*\*[^*]+\*\*:)(\s*)([^\n])/g, '$1\n$3');

  // === 연속된 빈 줄 정리 ===
  formatted = formatted.replace(/\n{3,}/g, '\n\n');

  // === 각 리스트 항목 사이 간격 ===
  // "1. 내용...다.2. " → "1. 내용...다.\n\n2. "
  formatted = formatted.replace(/([.])(\d+\.\s)/g, '$1\n\n$2');

  return formatted.trim();
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";
  const [formattedTime, setFormattedTime] = useState<string>("");

  // timestamp가 문자열로 들어올 수 있으므로 Date 객체로 변환
  const timestamp =
    message.timestamp instanceof Date
      ? message.timestamp
      : new Date(message.timestamp);

  // 클라이언트에서만 시간 포맷팅 (Hydration 에러 방지)
  useEffect(() => {
    setFormattedTime(
      timestamp.toLocaleTimeString("ko-KR", {
        hour: "2-digit",
        minute: "2-digit",
      })
    );
  }, [timestamp]);

  return (
    <div className={`flex mb-6 animate-fadeIn ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`max-w-full px-5 py-5 rounded-2xl break-words md:max-w-[85%] ${
        isUser
          ? "bg-gradient-to-br from-[#667eea] to-[#764ba2] text-white rounded-br-sm"
          : "bg-slate-200/90 border border-slate-300 text-slate-900 rounded-bl-sm shadow-sm dark:bg-slate-800 dark:border-slate-600 dark:text-slate-100"
      }`}>
        <div className={`leading-[1.8] text-base tracking-[0.01em] ${isUser ? "text-white" : "text-slate-900 dark:text-slate-100"} md:text-sm`}>
          {isUser ? (
            // 사용자 메시지는 마크다운 없이 그대로 표시
            <div>{message.content}</div>
          ) : (
            // 어시스턴트 메시지는 마크다운 렌더링 (일반 텍스트도 자동 포맷팅)
            <ReactMarkdown
              className="markdown-content text-slate-800 dark:text-slate-100 [&>*]:text-slate-800 dark:[&>*]:text-slate-100 [&_p]:my-3 [&_p]:leading-[1.85] [&_p]:text-slate-800 [&_p]:dark:text-slate-100 [&_p:first-child]:mt-0 [&_p:last-child]:mb-0 [&_p]:whitespace-pre-wrap [&_strong]:font-semibold [&_em]:italic [&_em]:opacity-90 [&_ul]:my-3 [&_ul]:pl-7 [&_ol]:my-3 [&_ol]:pl-7 [&_li]:my-2 [&_li]:leading-[1.7] [&_li]:pl-1 [&_ul_li]:list-disc [&_ol_li]:list-decimal [&_h1]:mt-5 [&_h1]:mb-3 [&_h1]:font-semibold [&_h1]:leading-[1.4] [&_h1]:text-2xl [&_h1]:text-slate-800 [&_h1]:dark:text-slate-100 [&_h1:first-child]:mt-0 [&_h2]:mt-5 [&_h2]:mb-3 [&_h2]:font-semibold [&_h2]:leading-[1.4] [&_h2]:text-xl [&_h2]:text-slate-800 [&_h2]:dark:text-slate-100 [&_h2:first-child]:mt-0 [&_h3]:mt-5 [&_h3]:mb-3 [&_h3]:font-semibold [&_h3]:leading-[1.4] [&_h3]:text-lg [&_h3]:text-slate-800 [&_h3]:dark:text-slate-100 [&_h3:first-child]:mt-0 [&_h4]:mt-5 [&_h4]:mb-3 [&_h4]:font-semibold [&_h4]:leading-[1.4] [&_h4]:text-slate-800 [&_h4]:dark:text-slate-100 [&_h4:first-child]:mt-0 [&_code]:bg-slate-200 [&_code]:text-slate-800 [&_code]:px-1.5 [&_code]:py-0.5 [&_code]:rounded [&_code]:font-mono [&_code]:text-[0.9em] dark:[&_code]:bg-slate-700 dark:[&_code]:text-slate-200 [&_pre]:block [&_pre]:bg-slate-200 [&_pre]:text-slate-800 dark:[&_pre]:bg-slate-700 dark:[&_pre]:text-slate-200 [&_pre]:p-4 [&_pre]:rounded-lg [&_pre]:overflow-x-auto [&_pre]:font-mono [&_pre]:text-[0.9em] [&_pre]:leading-[1.6] [&_pre]:my-4 [&_pre]:m-0 [&_a]:text-blue-600 [&_a]:underline [&_a]:decoration-blue-400 [&_a]:transition-all [&_a:hover]:text-blue-700 dark:[&_a]:text-blue-400 dark:[&_a:hover]:text-blue-300 [&_blockquote]:border-l-4 [&_blockquote]:border-slate-300 [&_blockquote]:pl-4 [&_blockquote]:my-4 [&_blockquote]:opacity-90 [&_blockquote]:italic [&_blockquote]:text-slate-700 dark:[&_blockquote]:border-slate-600 dark:[&_blockquote]:text-slate-300 [&_hr]:border-0 [&_hr]:border-t [&_hr]:border-slate-200 [&_hr]:my-6 dark:[&_hr]:border-slate-600"
              remarkPlugins={[]}
              rehypePlugins={[]}
              components={{
                // 단락 스타일링
                p: ({ children }) => <p>{children}</p>,
                // 리스트 스타일링
                ul: ({ children }) => <ul>{children}</ul>,
                ol: ({ children }) => <ol>{children}</ol>,
                li: ({ children }) => <li>{children}</li>,
                // 강조 스타일링
                strong: ({ children }) => <strong>{children}</strong>,
                em: ({ children }) => <em>{children}</em>,
                // 코드 블록
                code: ({ inline, className, children, ...props }: any) => {
                  if (inline) {
                    return <code className="inline-code">{children}</code>;
                  }
                  return (
                    <code className="code-block" {...props}>
                      {children}
                    </code>
                  );
                },
                pre: ({ children }) => <pre className="code-pre">{children}</pre>,
                // 헤딩
                h1: ({ children }) => <h1>{children}</h1>,
                h2: ({ children }) => <h2>{children}</h2>,
                h3: ({ children }) => <h3>{children}</h3>,
                h4: ({ children }) => <h4>{children}</h4>,
                // 링크
                a: ({ href, children }: any) => (
                  <a href={href} target="_blank" rel="noopener noreferrer">
                    {children}
                  </a>
                ),
                // 줄바꿈
                br: () => <br />,
                // 인용구
                blockquote: ({ children }) => <blockquote>{children}</blockquote>,
                // 수평선
                hr: () => <hr />,
              }}
            >
              {formatPlainText(message.content)}
            </ReactMarkdown>
          )}
        </div>
        <div className={`flex items-center gap-2 mt-2 flex-wrap ${isUser ? "justify-end" : "justify-start"}`}>
          <span className={`text-[0.7rem] ${isUser ? "text-white/80 text-right" : "text-slate-500 dark:text-slate-400 text-left"}`}>
            {formattedTime}
          </span>
          {/* 어시스턴트 메시지에 추가 정보 표시 - 밝은/어두운 배경 모두 대비 확보 */}
          {!isUser && message.provider && (
            <span className="text-[0.7rem] px-1.5 py-0.5 rounded font-medium bg-indigo-100 text-indigo-800 dark:bg-indigo-900/50 dark:text-indigo-200">
              {message.provider === "exaone" ? "🇰🇷 EXAONE" : message.provider}
            </span>
          )}
          {!isUser && message.usedRag !== undefined && message.usedRag && (
            <span className="text-[0.7rem] px-1.5 py-0.5 rounded font-medium bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-200">
              📚 RAG
            </span>
          )}
          {!isUser && message.semantic_action !== undefined && (
            <span
              className={`text-[0.7rem] px-1.5 py-0.5 rounded font-medium ${
                message.semantic_action === "BLOCK"
                  ? "bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-200"
                  : message.semantic_action === "RULE_BASED"
                    ? "bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-200"
                    : message.semantic_action === "POLICY_BASED"
                      ? "bg-violet-100 text-violet-800 dark:bg-violet-900/50 dark:text-violet-200"
                      : "bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-200"
              }`}
            >
              {message.semantic_action === "BLOCK"
                ? "🚫 차단"
                : message.semantic_action === "RULE_BASED"
                  ? "📋 규칙 기반"
                  : message.semantic_action === "POLICY_BASED"
                    ? "📌 정책 기반"
                    : "❓ 미분류"}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
