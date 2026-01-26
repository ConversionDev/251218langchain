/**
 * Zustand 기반 채팅 상태 관리 스토어
 */

import { create } from "zustand";
import type { Message, LLMProvider, APIMode } from "../types";
import {
  sendAgentMessage,
  sendAgentMessageStream,
  sendLangChainMessage,
  sendLangChainMessageStream,
  getAgentHealth,
  getProviders,
} from "../api/agent";

interface ChatState {
  // 상태
  messages: Message[];
  isLoading: boolean;
  error: string | null;

  // 설정
  provider: LLMProvider;
  useRag: boolean;
  apiMode: APIMode; // "langchain" | "langgraph"

  // 에이전트 정보
  agentStatus: "unknown" | "healthy" | "error";
  availableProviders: string[];

  // 액션
  sendMessage: (content: string) => Promise<void>;
  setProvider: (provider: LLMProvider) => void;
  setApiMode: (mode: APIMode) => void;
  toggleRag: () => void;
  clearMessages: () => void;
  clearError: () => void;
  checkAgentHealth: () => Promise<void>;
}

export const useChatStore = create<ChatState>((set, get) => ({
  // 초기 상태
  messages: [
    {
      id: "welcome",
      role: "assistant",
      content:
        "안녕하세요! LangChain/LangGraph 테스트 챗봇입니다. 🚀\n\n" +
        "- **LangChain**: 기존 RAG 체인 사용\n" +
        "- **LangGraph**: 에이전트 기반 (도구 사용 가능)\n\n" +
        "상단에서 모드와 제공자를 선택하고 메시지를 보내보세요!",
      timestamp: new Date(),
    },
  ],
  isLoading: false,
  error: null,

  provider: "exaone",
  useRag: true,
  apiMode: "langgraph",

  agentStatus: "unknown",
  availableProviders: [],

  // 메시지 전송
  sendMessage: async (content: string) => {
    const { messages, provider, useRag, apiMode } = get();

    if (!content.trim() || get().isLoading) return;

    // 사용자 메시지 추가
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content,
      timestamp: new Date(),
    };

    set({ messages: [...messages, userMessage], isLoading: true, error: null });

    try {
      if (apiMode === "langgraph") {
        // LangGraph Agent API 사용 (스트리밍)
        const chatHistory = messages
          .filter((m) => m.role !== "system" && m.id !== "welcome")
          .map((m) => ({
            role: m.role,
            content: m.content,
          }));

        // 스트리밍 응답을 위한 어시스턴트 메시지 생성
        const assistantMessageId = `assistant-${Date.now()}`;
        const assistantMessage: Message = {
          id: assistantMessageId,
          role: "assistant",
          content: "",
          timestamp: new Date(),
          provider: provider,
          usedRag: useRag,
        };

        // 스트리밍 메시지를 먼저 추가
        set((state) => ({
          messages: [...state.messages, assistantMessage],
        }));

        // 스트리밍으로 응답 수신
        let fullResponse = "";
        try {
          for await (const chunk of sendAgentMessageStream({
            message: content,
            provider,
            use_rag: useRag,
            chat_history: chatHistory,
          })) {
            fullResponse += chunk;
            // 실시간으로 메시지 업데이트
            set((state) => ({
              messages: state.messages.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, content: fullResponse }
                  : msg
              ),
            }));
          }
        } catch {
          // 스트리밍 실패 시 일반 API로 폴백
          const result = await sendAgentMessage({
            message: content,
            provider,
            use_rag: useRag,
            chat_history: chatHistory,
          });

          // 메시지 업데이트
          set((state) => ({
            messages: state.messages.map((msg) =>
              msg.id === assistantMessageId
                ? {
                    ...msg,
                    content: result.response,
                    provider: result.provider as LLMProvider,
                    usedRag: result.used_rag,
                  }
                : msg
            ),
            isLoading: false,
          }));
          return;
        }
      } else {
        // LangChain API 사용 (스트리밍)
        const modelType = "local";
        const history = messages
          .filter((m) => m.id !== "welcome")
          .map((m) => ({
            role: m.role,
            content: m.content,
          }));

        // 스트리밍 응답을 위한 어시스턴트 메시지 생성
        const assistantMessageId = `assistant-${Date.now()}`;
        const assistantMessage: Message = {
          id: assistantMessageId,
          role: "assistant",
          content: "",
          timestamp: new Date(),
        };

        // 스트리밍 메시지를 먼저 추가
        set((state) => ({
          messages: [...state.messages, assistantMessage],
        }));

        // 스트리밍으로 응답 수신
        let fullResponse = "";
        try {
          for await (const chunk of sendLangChainMessageStream(
            content,
            history,
            modelType
          )) {
            fullResponse += chunk;
            // 실시간으로 메시지 업데이트
            set((state) => ({
              messages: state.messages.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, content: fullResponse }
                  : msg
              ),
            }));
          }
        } catch {
          // 스트리밍 실패 시 일반 API로 폴백
          const result = await sendLangChainMessage(content, history, modelType);

          // 메시지 업데이트
          set((state) => ({
            messages: state.messages.map((msg) =>
              msg.id === assistantMessageId
                ? { ...msg, content: result.response }
                : msg
            ),
            isLoading: false,
          }));
          return;
        }
      }

      // 스트리밍 완료 - 이미 메시지가 추가되어 있음 (LangGraph, LangChain 모두)
      set({ isLoading: false });
    } catch (error) {
      const errorMsg =
        error instanceof Error ? error.message : "알 수 없는 오류가 발생했습니다.";

      // 에러 메시지 추가
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        role: "assistant",
        content: `⚠️ 오류: ${errorMsg}`,
        timestamp: new Date(),
      };

      set((state) => ({
        messages: [...state.messages, errorMessage],
        isLoading: false,
        error: errorMsg,
      }));
    }
  },

  // 제공자 변경
  setProvider: (provider: LLMProvider) => {
    set({ provider });
  },

  // API 모드 변경
  setApiMode: (mode: APIMode) => {
    set({ apiMode: mode });
  },

  // RAG 토글
  toggleRag: () => {
    set((state) => ({ useRag: !state.useRag }));
  },

  // 메시지 초기화
  clearMessages: () => {
    set({
      messages: [
        {
          id: "welcome",
          role: "assistant",
          content: "대화가 초기화되었습니다. 새 메시지를 입력해주세요!",
          timestamp: new Date(),
        },
      ],
    });
  },

  // 에러 초기화
  clearError: () => {
    set({ error: null });
  },

  // 에이전트 상태 확인
  checkAgentHealth: async () => {
    try {
      const health = await getAgentHealth();
      const providers = await getProviders();

      set({
        agentStatus: health.status,
        availableProviders: providers.map((p) => p.name),
        provider: (health.current_provider as LLMProvider) || "exaone",
      });
    } catch {
      set({ agentStatus: "error" });
    }
  },
}));

