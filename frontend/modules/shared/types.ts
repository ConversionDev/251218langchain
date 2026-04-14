/**
 * 전사 공통 타입 정의
 * Success DNA 도메인 모듈 간 공유
 */

/** 5대 핵심 역량 (Success DNA) */
export interface SuccessDNA {
  /** 리더십 (0–100) */
  leadership: number;
  /** 기술력 (0–100) */
  technical: number;
  /** 창의성 (0–100) */
  creativity: number;
  /** 협업 (0–100) */
  collaboration: number;
  /** 적응력 (0–100) */
  adaptability: number;
}

/** IFRS S1/S2 공시용 인적 자본 지표 (UI/레거시 뷰) */
export interface IfrsMetrics {
  /** S2 기후/산업 전환 준비도 (0–100) */
  transitionReadyScore: number;
  /** 현재 역량과 미래 필요 역량 차이 (갭 크기, 0–100, 낮을수록 양호) */
  skillGap: number;
  /** 인적 자원 투자 회수율 (배수 또는 %) */
  humanCapitalROI: number;
}

/**
 * 공시 지표 한 건 — 표준·코드·지표명·단위·검증·근거를 함께 저장.
 * disclosure_metrics의 items[]에 이 구조 사용. (제안 구조: standard/code/name/value/unit/status/source_id)
 */
export interface DisclosureMetricItem {
  /** 기준 표준 (예: "ISO 30414", "IFRS S1", "IFRS S2") */
  standard: string;
  /** 표준 내 항목 코드 (예: "4.7.1", "B14"). 하위 호환: categoryCode */
  code?: string;
  /** 지표명 (예: "Total training hours"). 하위 호환: description */
  name?: string;
  /** 수치 값 */
  value: number;
  /** 단위 (예: "hours", "percent", "ratio") */
  unit: string;
  /** 검증 상태 (예: "verified") */
  status?: string;
  /** 추출 근거(원문) — 파일명·문서 ID (예: survey_2025_01) */
  source_id?: string;
  /** 측정/기준일 (YYYY-MM-DD) */
  measuredAt?: string;
  /** @deprecated 하위 호환용. 신규는 code 사용 */
  categoryCode?: string;
  /** @deprecated 하위 호환용. 신규는 name 사용 */
  description?: string;
  /** @deprecated 하위 호환용. 신규는 source_id 사용 */
  source?: string;
}

/**
 * DB/API에 저장되는 공시 지표 — 레거시 flat 객체 또는 객체 배열.
 * UI는 getIfrsMetricsView()로 IfrsMetrics 뷰를 쓰면 됨.
 */
export type DisclosureMetricsPayload =
  | IfrsMetrics
  | { items: DisclosureMetricItem[] };

/** 성별 (ISO 30414) */
export type Gender = "male" | "female" | "other" | "undisclosed";

/** 연령대 (ISO 30414) */
export type AgeBand = "under30" | "30-39" | "40-49" | "50-59" | "60over";

/** 고용 형태 (ISO 30414) */
export type EmploymentType = "regular" | "contract" | "part_time" | "intern" | "new_hire";

/** 채용 상태 (ATS) */
export type RecruitStatus = "pending" | "screening" | "hired" | "rejected";

/** 정형화된 이력 정보 (HR Profile / 이력서) */
export interface Resume {
  /** 학력 */
  education: EducationEntry[];
  /** 경력 */
  experience: ExperienceEntry[];
  /** 보유 기술 */
  skills: SkillEntry[];
  /** 자격증 */
  certifications: CertificationEntry[];
}

/** 학력 한 건 */
export interface EducationEntry {
  /** 학교/기관명 */
  school: string;
  /** 학위 (예: 학사, 석사) */
  degree: string;
  /** 전공/분야 (선택) */
  field?: string;
  /** 시작일 (YYYY-MM) */
  startDate: string;
  /** 종료일 (YYYY-MM), 재학 중이면 생략 */
  endDate?: string;
}

/** 경력 한 건 */
export interface ExperienceEntry {
  /** 회사/기관명 */
  company: string;
  /** 직함/역할 */
  role: string;
  /** 시작일 (YYYY-MM) */
  startDate: string;
  /** 종료일 (YYYY-MM), 재직 중이면 생략 */
  endDate?: string;
  /** 업무 설명 (선택) */
  description?: string;
}

/** 보유 기술 한 건 */
export interface SkillEntry {
  /** 기술명 */
  name: string;
  /** 숙련도 등급 (선택, 예: 초급/중급/고급) */
  level?: string;
}

/** 자격증 한 건 */
export interface CertificationEntry {
  /** 자격증명 */
  name: string;
  /** 발급 기관 (선택) */
  issuer?: string;
  /** 취득일 (YYYY-MM) (선택) */
  date?: string;
}

/** 직원 기본 인적 사항 */
export interface Employee {
  id: string;
  /** 이름 */
  name: string;
  /** 직급 */
  jobTitle: string;
  /** 부서 */
  department: string;
  /** 이메일 (선택) */
  email?: string;
  /** 전화번호 (선택, 예: 010-1234-5678) */
  phone?: string;
  /** 생년월일 YYYY-MM-DD (선택) */
  birthDate?: string;
  /** 지원일 YYYY-MM-DD (지원서 제출일). 입사지원 시 저장 */
  applicationDate?: string;
  /** 입사일 YYYY-MM-DD. 입사 확정 후 설정, 지원 시점에는 미설정 */
  joinedAt?: string;
  /** Success DNA 역량 점수 (선택) */
  successDna?: SuccessDNA;
  /** 공시 지표 (선택). IFRS/ISO 30414 등 다중 표준. 레거시 flat 또는 items[] */
  disclosureMetrics?: DisclosureMetricsPayload;
  /** 성별 (남/여/미기입) */
  gender?: Gender;
  /** 연령(만 나이). 연령대는 이 값으로 파생 */
  age?: number;
  /** 연령대. API 응답 시 age로부터 파생된 값 (저장 컬럼 없음) */
  ageBand?: AgeBand;
  /** 고용 형태 (ISO 30414) */
  employmentType?: EmploymentType;
  /** 연간 교육훈련 시간 (ISO 30414) */
  trainingHours?: number;
  /** 정형화된 이력 정보 (학력·경력·기술·자격증) */
  resume?: Resume;
  /** 이력서 파일 SHA-256 (동일 이력서 중복 등록 방지, API 전송용) */
  resumeFileHash?: string;
  /** 시스템 추천 부서 (매칭 결과) */
  matchedDepartment?: string;
  /** 채용 상태 (ATS): pending(미검토)|screening(심사 중)|hired(합격)|rejected(탈락) */
  status?: RecruitStatus | null;
  /** AI 평가 근거 (Success DNA 점수 산정 이유, ATS 관리자 수동 수정 가능) */
  successDnaReason?: string | null;
  /** 탈락 사유 (ATS 관리자가 탈락 처리 시 입력) */
  rejectionReason?: string | null;
}
