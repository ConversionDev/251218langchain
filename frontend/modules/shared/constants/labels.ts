/**
 * Employee 기반 UI용 한글 라벨 (성별, 고용형태, 연령대).
 * Core, Overview 등에서 공통 사용합니다.
 */
export const GENDER_LABELS: Record<string, string> = {
  male: "남",
  female: "여",
  other: "기타",
  undisclosed: "미공개",
};

export const EMPLOYMENT_LABELS: Record<string, string> = {
  regular: "정규직",
  contract: "계약직",
  part_time: "파트타임",
  intern: "인턴",
};

/** 연령대 원본값 → 상세 라벨 (표 등) */
export const AGE_BAND_LABELS: Record<string, string> = {
  under30: "30세 미만",
  "30-39": "30-39세",
  "40-49": "40-49세",
  "50-59": "50-59세",
  "60over": "60세 이상",
};

/** 연령대 BarChart용 그룹 순서 및 라벨 */
export const AGE_GROUP_ORDER = ["20대", "30대", "40대", "50대 이상"] as const;
export type AgeGroupLabel = (typeof AGE_GROUP_ORDER)[number];

/** ageBand(API/스토어 값) → 20대/30대/40대/50대 이상 */
export function toAgeGroup(ageBand: string): AgeGroupLabel {
  if (ageBand === "under30") return "20대";
  if (ageBand === "30-39") return "30대";
  if (ageBand === "40-49") return "40대";
  return "50대 이상";
}
