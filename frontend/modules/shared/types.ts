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

/** IFRS S1/S2 공시용 인적 자본 지표 */
export interface IfrsMetrics {
  /** S2 기후/산업 전환 준비도 (0–100) */
  transitionReadyScore: number;
  /** 현재 역량과 미래 필요 역량 차이 (갭 크기, 0–100, 낮을수록 양호) */
  skillGap: number;
  /** 인적 자원 투자 회수율 (배수 또는 %) */
  humanCapitalROI: number;
}

/** 성별 (ISO 30414) */
export type Gender = "male" | "female" | "other" | "undisclosed";

/** 연령대 (ISO 30414) */
export type AgeBand = "under30" | "30-39" | "40-49" | "50-59" | "60over";

/** 고용 형태 (ISO 30414) */
export type EmploymentType = "regular" | "contract" | "part_time" | "intern";

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
  /** 입사일 (선택) */
  joinedAt?: string;
  /** Success DNA 역량 점수 (선택) */
  successDna?: SuccessDNA;
  /** 비정형 데이터(회의록·메신저) 분석 기반 역량 점수 (선택) */
  behavioralDna?: SuccessDNA;
  /** behavioralDna 분석 출처 요약 (예: 최근 3개의 주간 회의록 기반 분석됨) */
  behavioralSource?: string;
  /** 분석에 사용된 원문 목록 — UI에서 회의록/이메일/슬랙 내용 직접 확인용 */
  behavioralSourceItems?: BehavioralSourceItem[];
  /** IFRS 공시 지표 (선택) */
  ifrsMetrics?: IfrsMetrics;
  /** 성별 (ISO 30414) */
  gender?: Gender;
  /** 연령대 (ISO 30414) */
  ageBand?: AgeBand;
  /** 고용 형태 (ISO 30414) */
  employmentType?: EmploymentType;
  /** 연간 교육훈련 시간 (ISO 30414) */
  trainingHours?: number;
  /** 정형화된 이력 정보 (학력·경력·기술·자격증) */
  resume?: Resume;
  /** 시스템 추천 부서 (매칭 결과) */
  matchedDepartment?: string;
}

/** 비정형 분석 출처 한 건 (회의록·이메일·슬랙 등 원문 노출용) */
export interface BehavioralSourceItem {
  /** 출처 종류 */
  kind: "meeting" | "email" | "slack";
  /** 제목 (선택, 예: "2024-01-15 주간 회의") */
  title?: string;
  /** 원문 내용 */
  content: string;
}
