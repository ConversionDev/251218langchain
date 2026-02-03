"use client";

import { useEffect, useRef } from "react";
import { useChatStore } from "@/lib/store/chatStore";
import ChatMessage from "@/components/v1/ChatMessage";
import ChatInput from "@/components/v1/ChatInput";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { MessageCircle } from "lucide-react";

export default function V20ChatPage() {
  const {
    messages,
    isLoading,
    provider,
    agentStatus,
    sendMessage,
    cancelRequest,
    setProvider,
    clearMessages,
    checkAgentHealth,
  } = useChatStore();

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    checkAgentHealth();
  }, [checkAgentHealth]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">
          직원 상담
        </h1>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
          직원·조직·정책 관련 질문을 AI가 답변합니다.
        </p>
      </div>

      <Card className="overflow-hidden">
        <CardHeader className="border-b border-slate-200 bg-slate-50/50 dark:border-slate-800 dark:bg-slate-900/50 pb-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <MessageCircle className="h-5 w-5 text-slate-600 dark:text-slate-400" />
              <CardTitle className="text-base">AI 상담</CardTitle>
            </div>
            <div className="flex items-center gap-3 flex-wrap">
              <div className="flex items-center gap-2 text-sm">
                <span
                  className={`inline-block w-2 h-2 rounded-full ${
                    agentStatus === "healthy"
                      ? "bg-green-500"
                      : agentStatus === "error"
                        ? "bg-red-500"
                        : "bg-amber-500 animate-pulse"
                  }`}
                />
                <span className="text-slate-600 dark:text-slate-400">
                  {agentStatus === "healthy" ? "연결됨" : agentStatus === "error" ? "오류" : "확인 중..."}
                </span>
              </div>
              <button
                type="button"
                onClick={() => setProvider("exaone")}
                disabled={isLoading}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  provider === "exaone"
                    ? "bg-blue-600 text-white"
                    : "bg-slate-200 text-slate-700 hover:bg-slate-300 dark:bg-slate-700 dark:text-slate-200 dark:hover:bg-slate-600"
                } ${isLoading ? "opacity-60 cursor-not-allowed" : ""}`}
              >
                EXAONE
              </button>
              <span className="text-sm text-slate-500 dark:text-slate-400">RAG 항상 사용</span>
              <button
                type="button"
                onClick={clearMessages}
                disabled={isLoading}
                className="px-3 py-1.5 rounded-lg text-sm font-medium text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-950/30 disabled:opacity-50"
              >
                대화 초기화
              </button>
            </div>
          </div>
          <CardDescription className="sr-only">
            메시지를 입력한 뒤 Enter로 전송할 수 있습니다.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0 flex flex-col min-h-[480px]">
          <div className="flex-1 overflow-y-auto min-h-[320px] max-h-[60vh] p-4 bg-slate-50 dark:bg-slate-950/50">
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center py-12 text-center text-slate-500 dark:text-slate-400">
                <MessageCircle className="h-12 w-12 mb-3 opacity-50" />
                <p className="text-sm">질문을 입력하면 AI가 답변합니다.</p>
                <p className="text-xs mt-1">직원·조직·성과·정책 등 관련 질문을 해보세요.</p>
              </div>
            )}
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
            {isLoading && (
              <div className="flex items-center gap-3 p-4 flex-wrap">
                <div className="flex gap-1.5 px-4 py-3 bg-blue-100 dark:bg-blue-900/30 rounded-2xl border border-blue-200 dark:border-blue-800">
                  <span className="w-2 h-2 rounded-full bg-blue-600 animate-bounce [animation-delay:0ms]" />
                  <span className="w-2 h-2 rounded-full bg-blue-600 animate-bounce [animation-delay:150ms]" />
                  <span className="w-2 h-2 rounded-full bg-blue-600 animate-bounce [animation-delay:300ms]" />
                </div>
                <span className="text-sm text-slate-600 dark:text-slate-400">답변 생성 중...</span>
                <button
                  type="button"
                  onClick={cancelRequest}
                  className="px-3 py-1.5 rounded-lg text-sm font-medium text-red-600 hover:bg-red-50 dark:hover:bg-red-950/30"
                >
                  취소
                </button>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
          <div className="border-t border-slate-200 dark:border-slate-800 p-4 bg-white dark:bg-slate-900/50">
            <ChatInput onSend={sendMessage} disabled={isLoading} />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
