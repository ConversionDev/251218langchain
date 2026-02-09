/** 채팅 API 요청/응답 타입 (백엔드 /api/agent/chat 와 동일) */

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
}

export interface AgentResponse {
  response: string;
  provider: string;
  used_rag: boolean;
  thread_id?: string;
  semantic_action?: string;
  /** RAG에서 참고한 문서(검색된 컨텍스트) 미리보기 */
  context_preview?: string;
}
