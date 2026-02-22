import type { Employee } from "@/modules/shared/types";

const API_BASE = typeof window !== "undefined" ? (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000") : "http://localhost:8000";

export interface EmployeesPaginatedResult {
  items: Employee[];
  total: number;
  page: number;
  pageSize: number;
}

/** Neon 직원 목록 조회 (전체, 페이징 없음) */
export async function fetchEmployees(): Promise<Employee[]> {
  const res = await fetch(`${API_BASE}/api/employees`);
  if (!res.ok) throw new Error(`Employees fetch failed: ${res.status}`);
  return res.json();
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

/** 직원 생성 (Neon). 동일 이름이 이미 있으면 409 에러(기존 데이터 반환). */
export async function createEmployeeApi(payload: Employee): Promise<Employee> {
  const res = await fetch(`${API_BASE}/api/employees`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const body = await res.json().catch(() => ({}));
  if (res.status === 409) {
    const msg = (body as { detail?: string }).detail ?? "이미 등록된 직원입니다";
    const err = new Error(msg) as Error & { existing?: Employee };
    err.existing = (body as { existing?: Employee }).existing;
    throw err;
  }
  if (!res.ok) {
    throw new Error((body as { detail?: string }).detail ?? `Create failed: ${res.status}`);
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

/** 직원 이력서 AI 분석 (엑사원 Success DNA 생성 후 DB 반영, status → screening) */
export async function analyzeEmployeeResumeApi(employeeId: string): Promise<Employee> {
  const res = await fetch(`${API_BASE}/api/employees/${employeeId}/analyze`, { method: "POST" });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail ?? `AI 분석 실패: ${res.status}`);
  }
  return res.json();
}

/** 직원 임베딩 갱신 (embedding이 비어 있는 직원만 일괄 계산 후 DB 반영, RAG 검색용) */
export async function refreshEmployeeEmbeddingsApi(): Promise<{ updated: number }> {
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
