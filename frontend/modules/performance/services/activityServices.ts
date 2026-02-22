/**
 * 성과 활동(Activity Records) API 서비스 — performance_records 통합 테이블 조회.
 *
 * 회의록·보고서·이메일 통합하여 사원별·분기별 조회.
 */

const API_BASE =
  typeof window !== "undefined"
    ? (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000")
    : "http://localhost:8000";

/** 텍스트 유형: meeting|report|email */
export type ActivityTextType = "meeting" | "report" | "email";

/** 성과 활동 단건 */
export interface ActivityRecord {
  id: string;
  employeeId: string;
  period: string;
  textType: ActivityTextType;
  content: string;
  tags: string[];
  grade: "high" | "normal" | null;
  createdAt: string | null;
}

/** 직원 제출 요청 */
export interface SubmitActivityPayload {
  employeeId: string;
  textType: ActivityTextType;
  content: string;
  period: string;
  tags?: string[];
}

export interface ActivityListResponse {
  items: ActivityRecord[];
  total: number;
}

/** 전체 활동 목록 (필터 옵션) */
export async function fetchActivityRecords(params?: {
  period?: string;
  grade?: "high" | "normal";
  textType?: ActivityTextType;
  limit?: number;
}): Promise<ActivityListResponse> {
  const sp = new URLSearchParams();
  if (params?.period) sp.set("period", params.period);
  if (params?.grade) sp.set("grade", params.grade);
  if (params?.textType) sp.set("textType", params.textType);
  if (params?.limit) sp.set("limit", String(params.limit));

  const url = `${API_BASE}/api/activity-records${sp.toString() ? `?${sp}` : ""}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Activity records fetch failed: ${res.status}`);
  return res.json();
}

/** 사원별 활동 목록 */
export async function fetchActivitiesByEmployee(
  employeeId: string,
  params?: { period?: string; textType?: ActivityTextType; limit?: number }
): Promise<ActivityRecord[]> {
  const sp = new URLSearchParams();
  if (params?.period) sp.set("period", params.period);
  if (params?.textType) sp.set("textType", params.textType);
  if (params?.limit) sp.set("limit", String(params.limit));

  const url = `${API_BASE}/api/activity-records/by-employee/${employeeId}${sp.toString() ? `?${sp}` : ""}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Employee activities fetch failed: ${res.status}`);
  return res.json();
}

/** 단건 조회 */
export async function fetchActivityById(id: string): Promise<ActivityRecord> {
  const res = await fetch(`${API_BASE}/api/activity-records/${id}`);
  if (!res.ok) throw new Error(`Activity record fetch failed: ${res.status}`);
  return res.json();
}

/** 직원 본인 제출 목록 (워크스페이스) */
export async function fetchMyActivities(
  employeeId: string,
  params?: { period?: string; textType?: ActivityTextType; limit?: number }
): Promise<ActivityRecord[]> {
  const sp = new URLSearchParams({ employeeId });
  if (params?.period) sp.set("period", params.period);
  if (params?.textType) sp.set("textType", params.textType);
  if (params?.limit) sp.set("limit", String(params.limit));
  const res = await fetch(`${API_BASE}/api/activity-records/my?${sp}`);
  if (!res.ok) throw new Error(`My activities fetch failed: ${res.status}`);
  return res.json();
}

/** 직원 업무 제출 */
export async function submitActivity(payload: SubmitActivityPayload): Promise<ActivityRecord> {
  const res = await fetch(`${API_BASE}/api/activity-records/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail ?? `Submit failed: ${res.status}`);
  }
  return res.json();
}

/** 텍스트 유형 한글 라벨 */
export function getTextTypeLabel(textType: ActivityTextType): string {
  switch (textType) {
    case "meeting":
      return "회의록";
    case "report":
      return "보고서";
    case "email":
      return "이메일";
    default:
      return textType;
  }
}
