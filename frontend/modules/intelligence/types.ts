import type { Employee, SuccessDNA } from "@/modules/shared/types";

/** 전환 준비도 시계열 한 점 (월별) */
export interface TransitionTrendPoint {
  month: string;
  year: number;
  monthLabel: string;
  transitionReadyScore: number;
}

/** DNA 성장 이력 한 축 (1년 전 vs 현재) */
export interface DNAGrowthPoint {
  dimension: keyof SuccessDNA;
  label: string;
  pastYear: number;
  current: number;
  growthPct: number;
}

/** 월별 역량 궤적 (Line Chart용, 지난 12개월) */
export interface DNATrajectoryPoint {
  month: string;
  monthLabel: string;
  leadership: number;
  technical: number;
  creativity: number;
  collaboration: number;
  adaptability: number;
}

/** 전사 고성과자 평균 Success DNA (비교용) */
export type HighPerformerAverage = SuccessDNA;

/** 인재 분석 페이지에 필요한 직원 확장 데이터 */
export interface IntelligenceEmployee extends Employee {
  /** 최근 12개월 전환 준비도 추이 */
  transitionTrend: TransitionTrendPoint[];
}

/** AI 전환 가능성 리포트 요약 */
export interface TransitionReadinessSummary {
  /** 전환 가능성 점수 (0–100, %) */
  transitionProbability: number;
  /** 핵심 강점 역량 (요약에 인용) */
  strengthDimension: keyof SuccessDNA;
  /** 통합 요약 문구 (하위 호환) */
  narrative: string;
  /** 현재 상태 분석 문구 */
  currentState: string;
  /** 전환(Transition) 제언 문구 */
  transitionRecommendation: string;
  /** 리스크 알림 문구 */
  riskNotice: string;
}

/**
 * IFRS S2 Benchmark: 특정 산업(예: Green/저탄소)으로 성공적으로 전환하기 위해
 * 필요한 최소 준비 점수. 이 목표선 이상이면 전환 준비 완료로 간주.
 */
export const S2_BENCHMARK = 85;
