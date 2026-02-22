/**
 * 차트용 브랜드 색상. Success DNA 액센트(emerald) 우선, 라이트/다크 분위기 통일.
 */
export const BRAND_CHART_COLORS = {
  /** Emerald. 막대, 주요 시리즈 (라이트/다크 공통 액센트) */
  primary: "#059669",
  /** Teal. 라인, 성장/긍정 시리즈 */
  secondary: "#0d9488",
  primaryLight: "#10b981",
  secondaryLight: "#14b8a6",
  primaryLighter: "#64748b",
} as const;

/** 성별 도넛/파이용 색상. emerald·teal·슬레이트 */
export const GENDER_CHART_COLORS: Record<string, string> = {
  남: "#059669",
  여: "#0d9488",
  기타: "#64748b",
  미공개: "#94a3b8",
};

/** Pie/도넛 팔레트. emerald·teal 우선 */
export const PIE_PALETTE_INDIGO_EMERALD = [
  "#059669",
  "#0d9488",
  "#10b981",
  "#14b8a6",
  "#64748b",
  "#0891b2",
] as const;

/** 연령대별 막대 색상 (20대 → 50대 이상). emerald·teal 톤 */
export const AGE_GROUP_BAR_COLORS = [
  "#059669", /* 20대 */
  "#0d9488", /* 30대 */
  "#10b981", /* 40대 */
  "#475569", /* 50대 이상 */
] as const;

/** 부서별 막대 색상. emerald·teal 우선 */
export const DEPARTMENT_BAR_COLORS = [
  "#059669",
  "#0d9488",
  "#10b981",
  "#14b8a6",
  "#475569",
  "#0891b2",
  "#0e7490",
  "#64748b",
  "#0369a1",
  "#4f46e5",
] as const;
