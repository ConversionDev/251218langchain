/**
 * 스팸 감지 관련 타입 정의
 */

export interface EmailMetadata {
  subject: string;
  sender: string;
  attachments?: string[];
  received_at?: string;
  body?: string;
  date?: string;
}

export interface LLaMAResult {
  spam_prob: number;
  confidence: "high" | "medium" | "low";
  label: string;
  raw_output?: Record<string, any>;
}

export interface ExaoneResult {
  is_spam?: boolean | null;
  action?: string;
  reason_codes: string[];
  confidence: string;
  analysis?: string;
  rule_based?: boolean;
  policy_id?: string;
  matched_rule_id?: string;
  error?: string;
}

export interface SpamDetectionRequest {
  email_metadata: EmailMetadata;
}

export interface SpamDetectionResponse {
  action: string;
  routing_strategy?: string; // "rule" | "policy"
  reason_codes: string[];
  user_message: string;
  confidence: "high" | "medium" | "low";
  spam_prob: number;
  llama_result: LLaMAResult;
  exaone_result: ExaoneResult | null;
  routing_path: string;
}

export type SpamAction =
  | "deliver"
  | "deliver_with_warning"
  | "quarantine"
  | "reject"
  | "ask_user_confirm";

