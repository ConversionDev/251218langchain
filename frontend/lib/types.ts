/**
 * 공통 타입 정의
 */

// 메시지 역할
export type MessageRole = "user" | "assistant" | "system";

// 채팅 메시지
export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  provider?: string; // 응답 생성에 사용된 LLM 제공자
  usedRag?: boolean; // RAG 사용 여부
}

// LLM 제공자 타입
export type LLMProvider = "exaone";

// API 모드 (LangChain vs LangGraph)
export type APIMode = "langchain" | "langgraph";

// 에이전트 요청
export interface AgentRequest {
  message: string;
  provider?: LLMProvider;
  use_rag?: boolean;
  system_prompt?: string;
  chat_history?: { role: string; content: string }[];
}

// 에이전트 응답
export interface AgentResponse {
  response: string;
  provider: string;
  used_rag: boolean;
}

// LLM 제공자 정보
export interface ProviderInfo {
  name: string;
  supports_tool_calling: boolean;
  is_current: boolean;
}

// 도구 정보
export interface ToolInfo {
  name: string;
  description: string;
}

// 에이전트 상태
export interface AgentHealth {
  status: "healthy" | "error";
  current_provider?: string;
  supports_tool_calling?: boolean;
  available_providers?: string[];
  error?: string;
}

