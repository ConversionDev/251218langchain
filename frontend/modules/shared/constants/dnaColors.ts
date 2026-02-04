import type { SuccessDNA } from "@/modules/shared/types";

/**
 * Success DNA 5대 역량 공통 색상 팔레트.
 * Intelligence 레이더/궤적 차트, DNA 뱃지 등에서 동일하게 사용해 시각적 일관성을 유지합니다.
 */
export const DNA_DIMENSION_COLORS: Record<keyof SuccessDNA, string> = {
  leadership: "#6366f1",
  technical: "#3b82f6",
  creativity: "#f59e0b",
  collaboration: "#10b981",
  adaptability: "#ec4899",
};

export const DNA_DIMENSION_COLORS_CSS: Record<keyof SuccessDNA, string> = {
  leadership: "rgb(99, 102, 241)",
  technical: "rgb(59, 130, 246)",
  creativity: "rgb(245, 158, 11)",
  collaboration: "rgb(16, 185, 129)",
  adaptability: "rgb(236, 72, 153)",
};
