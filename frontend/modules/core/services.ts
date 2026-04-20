import type { Employee } from "@/modules/shared/types";

const API_BASE = typeof window !== "undefined" ? (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000") : "http://localhost:8000";

export interface EmployeesPaginatedResult {
  items: Employee[];
  total: number;
  page: number;
  pageSize: number;
}

/** Neon 직원 목록 조회 (전체). 내부는 페이징 API로 나눠 호출 — 단일 대용량 응답으로 인한 게이트웨이 타임아웃·실패 방지. */
export async function fetchEmployees(): Promise<Employee[]> {
  const pageSize = 100;
  const first = await fetchEmployeesPaginated({ page: 1, pageSize });
  const totalCount = first.total ?? 0;
  const collected: Employee[] = [...(first.items ?? [])];
  const totalPages = Math.max(1, Math.ceil(totalCount / pageSize));
  for (let p = 2; p <= totalPages; p++) {
    const next = await fetchEmployeesPaginated({ page: p, pageSize });
    if (next.items?.length) collected.push(...next.items);
  }
  return collected;
}

/** 직원 목록 페이징 조회. employmentType: 'regular'(기존직원), 'new_hire'(신입) */
export async function fetchEmployeesPaginated(params: {
  page?: number;
  pageSize?: number;
  employmentType?: "regular" | "new_hire";
}): Promise<EmployeesPaginatedResult> {
  const { page = 1, pageSize = 20, employmentType } = params;
  const url = new URL(`${API_BASE}/api/employees`);
  url.searchParams.set("page", String(page));
  url.searchParams.set("pageSize", String(pageSize));
  if (employmentType) url.searchParams.set("employmentType", employmentType);
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error(`Employees fetch failed: ${res.status}`);
  return res.json();
}

/** 다음 직원 ID 제안 (직원 추가 폼용) */
export async function fetchNextEmployeeId(): Promise<string> {
  const res = await fetch(`${API_BASE}/api/employees/next-id`);
  if (!res.ok) throw new Error(`Next ID fetch failed: ${res.status}`);
  const data = (await res.json()) as { nextId?: string };
  return data.nextId ?? "E001";
}

/** 이력서 파일 해시로 이미 등록된 지원인지 확인. 중복 시 제출 불가 처리용 */
export async function checkResumeHashApi(resumeHash: string): Promise<{ exists: boolean; existing?: Employee }> {
  const res = await fetch(
    `${API_BASE}/api/employees/check-resume-hash?resume_hash=${encodeURIComponent(resumeHash)}`
  );
  if (!res.ok) return { exists: false };
  const data = (await res.json()) as { exists?: boolean; existing?: Employee };
  return { exists: !!data.exists, existing: data.existing };
}

/** 직원 생성 (Neon). 동일 이력서면 409, 검증/DB 오류 시 서버 메시지 그대로 표시. */
export async function createEmployeeApi(payload: Employee): Promise<Employee> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}/api/employees`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    if (msg === "Failed to fetch" || msg.includes("NetworkError") || msg.includes("Load failed")) {
      throw new Error("백엔드 서버에 연결할 수 없습니다. API 서버(localhost:8000)가 실행 중인지 확인해 주세요.");
    }
    throw e;
  }
  const body = await res.json().catch(() => ({}));
  if (res.status === 409) {
    const msg = (body as { detail?: string }).detail ?? "이미 등록된 직원입니다";
    const err = new Error(msg) as Error & { existing?: Employee };
    err.existing = (body as { existing?: Employee }).existing;
    throw err;
  }
  if (!res.ok) {
    const raw = (body as { detail?: string | unknown[] }).detail;
    const message =
      typeof raw === "string"
        ? raw
        : Array.isArray(raw) && raw.length > 0
          ? (raw as { msg?: string }[]).map((e) => e.msg ?? JSON.stringify(e)).join(". ")
          : `제출 실패 (${res.status})`;
    throw new Error(message);
  }
  return body as Employee;
}

/** 직원 수정 (Neon) */
export async function updateEmployeeApi(id: string, payload: Partial<Employee>): Promise<Employee> {
  const res = await fetch(`${API_BASE}/api/employees/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...payload, id }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail ?? `Update failed: ${res.status}`);
  }
  return res.json();
}

/** 직원 삭제 (Neon) */
export async function deleteEmployeeApi(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/employees/${id}`, { method: "DELETE" });
  if (!res.ok && res.status !== 204) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail ?? `Delete failed: ${res.status}`);
  }
}

/** 직원 이력서 AI 분석 (엑사원 Success DNA 생성 후 DB 반영, 신입은 status → screening) */
export async function analyzeEmployeeResumeApi(
  employeeId: string,
  options?: { force?: boolean }
): Promise<Employee & { analysisSkipped?: boolean }> {
  const q = options?.force ? "?force=true" : "";
  const res = await fetch(`${API_BASE}/api/employees/${employeeId}/analyze${q}`, { method: "POST" });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail ?? `AI 분석 실패: ${res.status}`);
  }
  return res.json();
}

/** 직원+성과 임베딩 갱신 (employees + performance_records 일괄 계산 후 DB 반영, RAG 검색용) */
export async function refreshEmployeeEmbeddingsApi(): Promise<{ updated: number; performanceUpdated?: number }> {
  const res = await fetch(`${API_BASE}/api/employees/embedding`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail ?? `임베딩 갱신 실패: ${res.status}`);
  }
  return res.json();
}

export interface EmployeeProfileBackfillResult {
  dryRun: boolean;
  seed: number;
  targetRegularEmployees: number;
  missingBefore: { gender: number; age: number; trainingHours: number };
  updated: { gender: number; age: number; trainingHours: number };
  preview: Array<Record<string, unknown>>;
}

/** 기존 직원 결측 프로필(성별/나이/교육시간) 일괄 보정 */
export async function backfillEmployeeProfilesApi(params?: {
  dryRun?: boolean;
  seed?: number;
}): Promise<EmployeeProfileBackfillResult> {
  const res = await fetch(`${API_BASE}/api/employees/profile-backfill`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      dryRun: params?.dryRun ?? true,
      seed: params?.seed ?? 42,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail ?? `결측 프로필 보정 실패: ${res.status}`);
  }
  return res.json();
}
