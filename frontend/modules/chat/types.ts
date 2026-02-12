/** 채팅 API 요청/응답 타입 (백엔드 /api/agent/chat·chat/stream 과 동일) */

export interface MessageItem {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface AgentRequest {
  message: string;
  provider?: string;
  use_rag: boolean;
  system_prompt?: string;
  chat_history?: MessageItem[];
  thread_id?: string;
  /** 업로드 API로 받은 file_id 목록 (BP: 2단계) */
  file_ids?: string[];
}

export interface AgentResponse {
  response: string;
  provider: string;
  used_rag: boolean;
  thread_id?: string;
  semantic_action?: string;
  context_preview?: string;
}
