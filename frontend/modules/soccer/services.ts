/**
 * Soccer API 클라이언트 (JSONL 업로드, 임베딩 동기화)
 */

import type { EmbeddingJobStatus, SoccerUploadResult } from "./types";

const API_BASE =
  typeof window !== "undefined"
    ? (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000")
    : "http://localhost:8000";

export type SoccerDataType = "players" | "teams" | "schedules" | "stadiums";

const UPLOAD_ENDPOINTS: Record<SoccerDataType, string> = {
  players: "/api/soccer/player/upload",
  teams: "/api/soccer/team/upload",
  schedules: "/api/soccer/schedule/upload",
  stadiums: "/api/soccer/stadium/upload",
};

export async function uploadSoccerJsonl(
  dataType: SoccerDataType,
  file: File
): Promise<SoccerUploadResult> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}${UPLOAD_ENDPOINTS[dataType]}`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `업로드 실패 (${res.status})`);
  }
  return res.json();
}

export async function startEmbeddingJob(
  entities?: ("players" | "teams" | "schedules" | "stadiums")[]
): Promise<{ job_id: string; status: string }> {
  const res = await fetch(`${API_BASE}/api/soccer/embedding`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ entities: entities ?? undefined }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "임베딩 job 시작 실패");
  }
  return res.json();
}

export async function getEmbeddingJobStatus(jobId: string): Promise<EmbeddingJobStatus> {
  const res = await fetch(`${API_BASE}/api/soccer/embedding/status/${jobId}`);
  if (!res.ok) {
    if (res.status === 404) throw new Error("Job not found");
    throw new Error(await res.text());
  }
  return res.json();
}
