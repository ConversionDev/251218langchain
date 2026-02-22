/**
 * 이력서 파일 → 기본 정보 + Baseline DNA.
 * POST /api/resume/analyze 호출 (RAG+LLM 분석).
 * 동일 파일(name+size+lastModified) 재업로드 시 sessionStorage 캐시로 즉시 반영.
 */

import type { SuccessDNA, Resume, Gender, EmploymentType } from "@/modules/shared/types";

const API_BASE =
  typeof window !== "undefined"
    ? (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000")
    : "http://localhost:8000";

const CACHE_KEY = "resume_parse_cache";
const CACHE_MAX_ENTRIES = 20;

export interface ResumeParseResult {
  /** AI가 채운 기본 정보 (사용자 확인·수정용) */
  name: string;
  jobTitle: string;
  department: string;
  email: string;
  /** 지원일 (YYYY-MM-DD 등) */
  applicationDate?: string;
  joinedAt: string;
  /** 이력서 구조 데이터 (학력·경력·기술·자격) */
  resume: Resume;
  /** 이력서 텍스트 분석으로 추정한 최초 Baseline DNA */
  successDna: SuccessDNA;
  /** 이력서에 기재된 경우 추출: 남(male)/여(female)/미기입(undisclosed) */
  gender?: Gender;
  /** 이력서의 나이/생년 기준 만 나이 (공시용) */
  age?: number;
  /** 고용 형태: 신입(new_hire)/정규직(regular)/계약직(contract)/파트타임(part_time)/인턴(intern) */
  employmentType?: EmploymentType;
  /** 연간 교육·연수 시간 (공시용) */
  trainingHours?: number;
}

export interface ParseResumeResponse {
  result: ResumeParseResult;
  fromCache: boolean;
}

export function fileCacheKey(file: File): string {
  return `${file.name}_${file.size}_${file.lastModified}`;
}

/** 이력서 파일 내용 SHA-256 (동일 이력서 중복 등록 방지). 브라우저 crypto.subtle 사용 */
export async function computeResumeFileHash(file: File): Promise<string> {
  const buf = await file.arrayBuffer();
  const hashBuf = await crypto.subtle.digest("SHA-256", buf);
  const arr = Array.from(new Uint8Array(hashBuf));
  return arr.map((b) => b.toString(16).padStart(2, "0")).join("");
}

/** 동일 파일 이전 분석 결과가 있으면 즉시 반환 (API 호출 없음). 편집/재업로드 시 속도 절감용 */
export function getCachedResumeResult(file: File): ResumeParseResult | null {
  const cache = getCache();
  return cache[fileCacheKey(file)] ?? null;
}

function getCache(): Record<string, ResumeParseResult> {
  if (typeof window === "undefined") return {};
  try {
    const raw = sessionStorage.getItem(CACHE_KEY);
    return raw ? (JSON.parse(raw) as Record<string, ResumeParseResult>) : {};
  } catch {
    return {};
  }
}

function setCache(obj: Record<string, ResumeParseResult>): void {
  if (typeof window === "undefined") return;
  try {
    const keys = Object.keys(obj);
    if (keys.length > CACHE_MAX_ENTRIES) {
      const toDelete = keys.slice(0, keys.length - CACHE_MAX_ENTRIES);
      toDelete.forEach((k) => delete obj[k]);
    }
    sessionStorage.setItem(CACHE_KEY, JSON.stringify(obj));
  } catch {
    // ignore
  }
}

/** 이력서 파일 업로드 → 분석 결과 반환. 동일 파일이면 캐시에서 즉시 반환하여 속도 절감 */
export async function parseResumeToBaseline(file: File): Promise<ParseResumeResponse> {
  const key = fileCacheKey(file);
  const cache = getCache();
  if (cache[key]) {
    return { result: cache[key], fromCache: true };
  }

  const form = new FormData();
  form.append("file", file);

  const res = await fetch(`${API_BASE}/api/resume/analyze`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    const text = await res.text();
    let detail = text;
    try {
      const json = JSON.parse(text);
      detail = json.detail ?? text;
    } catch {
      // ignore
    }
    throw new Error(detail || `이력서 분석 실패 (${res.status})`);
  }

  const data = (await res.json()) as ResumeParseResult;
  cache[key] = data;
  setCache(cache);
  return { result: data, fromCache: false };
}
