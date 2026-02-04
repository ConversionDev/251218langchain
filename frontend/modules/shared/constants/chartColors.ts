/**
 * DNA 역량이 아닌 일반 차트용 브랜드 색상 (Indigo / Emerald 계열).
 * Core, Overview, Performance 등 여러 모듈에서 동일하게 사용합니다.
 */
export const BRAND_CHART_COLORS = {
  /** Indigo-500. 막대, 주요 시리즈 */
  primary: "#6366f1",
  /** Emerald-400. 라인, 성장/긍정 시리즈 */
  secondary: "#34d399",
  /** Indigo-400 */
  primaryLight: "#818cf8",
  /** Emerald-300 */
  secondaryLight: "#6ee7b7",
  /** Indigo-300 */
  primaryLighter: "#a5b4fc",
} as const;

/** 성별 도넛/파이용 색상 (한글 라벨 키) */
export const GENDER_CHART_COLORS: Record<string, string> = {
  남: BRAND_CHART_COLORS.primary,
  여: BRAND_CHART_COLORS.secondary,
  기타: "#94a3b8",
  미공개: "#cbd5e1",
};

/** Pie/도넛 여러 조각용 팔레트 (순서대로 사용) */
export const PIE_PALETTE_INDIGO_EMERALD = [
  BRAND_CHART_COLORS.primary,
  BRAND_CHART_COLORS.secondary,
  BRAND_CHART_COLORS.primaryLight,
  BRAND_CHART_COLORS.secondaryLight,
  BRAND_CHART_COLORS.primaryLighter,
] as const;
