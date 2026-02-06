/** JSONL 업로드 결과 (선수/팀/일정/경기장) */
export interface SoccerUploadResult {
  success: boolean;
  message: string;
  data_type: string;
  filename?: string;
  total_rows?: number;
  preview_rows?: number;
  preview?: Array<{ row: number; data?: unknown; error?: string; raw?: string }>;
  strategy?: string;
  results?: { processed?: number; total?: number };
}

/** 임베딩 동기화 job 상태 */
export interface EmbeddingJobStatus {
  status: "waiting" | "processing" | "completed" | "failed";
  result?: Record<string, unknown>;
  error?: string;
}
