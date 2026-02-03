/**
 * Zustand 기반 채팅 상태 관리 스토어
 */

import { create } from "zustand";
import type { Message, LLMProvider } from "../types";
import {
  sendAgentMessage,
  sendAgentMessageStream,
  getAgentHealth,
  getProviders,
} from "../api/agent";

interface ChatState {
  // 상태
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  abortController: AbortController | null;

  // 설정
  provider: LLMProvider;

  // 에이전트 정보
  agentStatus: "unknown" | "healthy" | "error";
  availableProviders: string[];

  // 액션
  sendMessage: (content: string) => Promise<void>;
  cancelRequest: () => void;
  setProvider: (provider: LLMProvider) => void;
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
        "안녕하세요! LangGraph 에이전트 챗봇입니다. 🚀\n\n" +
        "도구 사용·RAG가 항상 적용된 에이전트입니다. 상단에서 제공자를 선택하고 메시지를 보내보세요!",
      timestamp: new Date(),
    },
  ],
  isLoading: false,
  error: null,
  abortController: null,

  provider: "exaone",

  agentStatus: "unknown",
  availableProviders: [],

  // 메시지 전송
  sendMessage: async (content: string) => {
    const { messages, provider } = get();

    if (!content.trim() || get().isLoading) return;

    // 사용자 메시지 추가
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content,
      timestamp: new Date(),
    };

    const controller = new AbortController();
    set({ messages: [...messages, userMessage], isLoading: true, error: null, abortController: controller });

    try {
      // LangGraph 에이전트 API (스트리밍)
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
          usedRag: true,
        };

        // 스트리밍 메시지를 먼저 추가
        set((state) => ({
          messages: [...state.messages, assistantMessage],
        }));

        // 스트리밍으로 응답 수신 (첫 청크가 시멘틱 분류 JSON일 수 있음)
        let fullResponse = "";
        let semanticAction: string | undefined;
        try {
          for await (const chunk of sendAgentMessageStream(
            {
              message: content,
              provider,
              chat_history: chatHistory,
            },
            controller.signal
          )) {
            if (semanticAction === undefined) {
              try {
                const parsed = JSON.parse(chunk) as { semantic_action?: string | null };
                if (parsed.semantic_action !== undefined) {
                  semanticAction = parsed.semantic_action ?? undefined;
                  set((state) => ({
                    messages: state.messages.map((msg) =>
                      msg.id === assistantMessageId
                        ? { ...msg, semantic_action: semanticAction }
                        : msg
                    ),
                  }));
                  continue;
                }
              } catch {
                // JSON 아님 → 본문 청크
              }
            }
            fullResponse += chunk;
            set((state) => ({
              messages: state.messages.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, content: fullResponse, semantic_action: semanticAction }
                  : msg
              ),
            }));
          }
        } catch (err) {
          if (err instanceof Error && err.name === "AbortError") {
            set({ isLoading: false, abortController: null });
            return;
          }
          // 스트리밍 실패 시 일반 API로 폴백
          const result = await sendAgentMessage({
            message: content,
            provider,
            chat_history: chatHistory,
          });

          set((state) => ({
            messages: state.messages.map((msg) =>
              msg.id === assistantMessageId
                ? {
                    ...msg,
                    content: result.response,
                    provider: result.provider as LLMProvider,
                    usedRag: result.used_rag,
                    semantic_action: result.semantic_action,
                  }
                : msg
            ),
            isLoading: false,
          }));
          set({ abortController: null });
          return;
        }
      set({ abortController: null });
      set({ isLoading: false, abortController: null });
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
        abortController: null,
      }));
    }
  },

  cancelRequest: () => {
    const { abortController } = get();
    if (abortController) {
      abortController.abort();
      set({ abortController: null, isLoading: false });
    }
  },

  // 제공자 변경
  setProvider: (provider: LLMProvider) => {
    set({ provider });
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

