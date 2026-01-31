"use client";

import { useEffect, useRef } from "react";
import { useChatStore } from "@/lib/store/chatStore";
import ChatMessage from "@/components/v1/ChatMessage";
import ChatInput from "@/components/v1/ChatInput";

export default function Home() {
  const {
    messages,
    isLoading,
    provider,
    useRag,
    agentStatus,
    sendMessage,
    cancelRequest,
    setProvider,
    toggleRag,
    clearMessages,
    checkAgentHealth,
  } = useChatStore();

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 스크롤 자동 이동
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // 에이전트 상태 확인 (마운트 시)
  useEffect(() => {
    checkAgentHealth();
  }, [checkAgentHealth]);

  return (
    <div className="flex flex-col h-screen max-w-[900px] mx-auto bg-[#1a1a2e] shadow-[0_0_40px_rgba(102,126,234,0.2)]">
      {/* 헤더 */}
      <header className="bg-gradient-to-br from-[#16213e] to-[#1a1a2e] text-[#e0e0e0] px-6 py-4 border-b border-[rgba(102,126,234,0.3)] md:px-4 md:py-3">
        <div className="flex justify-between items-center mb-4">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-semibold text-white md:text-base">🤖 LangGraph 에이전트</h1>
            <a
              href="/v1/spam-detection"
              className="px-3 py-1.5 bg-[rgba(102,126,234,0.2)] border border-[rgba(102,126,234,0.3)] rounded-lg text-[#e0e0e0] no-underline text-sm transition-all hover:bg-[rgba(102,126,234,0.3)]"
            >
              🛡️ 스팸 감지
            </a>
          </div>
          <div className="flex items-center gap-2 text-sm px-3 py-1 bg-[rgba(255,255,255,0.05)] rounded-full">
            <span
              className={`w-2 h-2 rounded-full ${
                agentStatus === "healthy"
                  ? "bg-green-400 shadow-[0_0_8px_#4ade80]"
                  : agentStatus === "error"
                    ? "bg-red-400 shadow-[0_0_8px_#f87171]"
                    : "bg-yellow-400 animate-pulse"
              }`}
            ></span>
            {agentStatus === "healthy"
              ? "연결됨"
              : agentStatus === "error"
                ? "오류"
                : "확인 중..."}
          </div>
        </div>

        {/* LLM 제공자 선택 */}
        <div className="flex items-center gap-2 mb-3 flex-wrap">
          <span className="text-sm text-[#a0a0a0] min-w-[70px] md:min-w-0 md:w-full md:mb-1">LLM:</span>
          <button
            className={`px-3 py-1.5 border rounded-lg text-sm transition-all md:px-2.5 md:py-1 md:text-xs ${
              provider === "exaone"
                ? "bg-gradient-to-br from-[#667eea] to-[#764ba2] border-[#667eea] text-white font-medium"
                : "border-[rgba(102,126,234,0.3)] bg-[rgba(255,255,255,0.05)] text-[#e0e0e0] hover:bg-[rgba(102,126,234,0.2)] hover:border-[rgba(102,126,234,0.5)]"
            } ${isLoading ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
            onClick={() => setProvider("exaone")}
            disabled={isLoading}
          >
            🇰🇷 EXAONE
          </button>
        </div>

        {/* RAG 및 기타 옵션 */}
        <div className="flex items-center gap-4 flex-wrap">
          <label className="flex items-center gap-2 text-sm cursor-pointer text-[#a0a0a0] has-[:checked]:text-[#e0e0e0]">
            <input
              type="checkbox"
              checked={useRag}
              onChange={toggleRag}
              disabled={isLoading}
              className="w-4 h-4 accent-[#667eea]"
            />
            <span>📚 RAG 사용</span>
          </label>
          <button
            className="px-3 py-1.5 border border-[rgba(248,113,113,0.3)] rounded-lg bg-[rgba(248,113,113,0.1)] text-[#f87171] text-sm cursor-pointer transition-all hover:bg-[rgba(248,113,113,0.2)] hover:border-[#f87171] disabled:opacity-50 disabled:cursor-not-allowed"
            onClick={clearMessages}
            disabled={isLoading}
          >
            🗑️ 대화 초기화
          </button>
        </div>
      </header>

      {/* 메시지 영역 */}
      <main className="flex-1 flex flex-col overflow-hidden bg-[#0a0a1a]">
        <div className="flex-1 overflow-y-auto p-6 bg-[#0f0f23]">
          {messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}
          {isLoading && (
            <div className="flex items-center gap-4 p-4 flex-wrap">
              <div className="flex gap-1.5 px-4 py-3 bg-[rgba(102,126,234,0.1)] rounded-2xl border border-[rgba(102,126,234,0.2)]">
                <span className="w-2 h-2 rounded-full bg-[#667eea] animate-typing"></span>
                <span className="w-2 h-2 rounded-full bg-[#667eea] animate-typing [animation-delay:0.2s]"></span>
                <span className="w-2 h-2 rounded-full bg-[#667eea] animate-typing [animation-delay:0.4s]"></span>
              </div>
              <span className="text-sm text-[#a0a0a0]">
                에이전트 처리 중...
              </span>
              <button
                type="button"
                onClick={cancelRequest}
                className="px-3 py-1.5 border border-[rgba(248,113,113,0.4)] rounded-lg bg-[rgba(248,113,113,0.15)] text-[#f87171] text-sm font-medium cursor-pointer transition-all hover:bg-[rgba(248,113,113,0.25)] hover:border-[#f87171]"
              >
                답변 취소
              </button>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <ChatInput onSend={sendMessage} disabled={isLoading} />
      </main>
    </div>
  );
}
