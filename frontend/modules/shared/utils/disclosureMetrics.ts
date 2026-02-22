/**
 * 공시 지표(disclosure_metrics) 뷰 헬퍼.
 * DB는 레거시 flat 객체 또는 DisclosureMetricItem[] 형태를 지원하며,
 * UI에서는 항상 IfrsMetrics 뷰(레거시 3필드)로 읽으면 됨.
 */

import type {
  DisclosureMetricItem,
  IfrsMetrics,
  DisclosureMetricsPayload,
} from "../types";

/** 레거시 3개 지표와 매핑되는 code (표준 무관). code 또는 categoryCode로 매칭 */
const LEGACY_CODES = {
  transitionReadyScore: ["transition_ready", "ifrs_s2_transition_ready"],
  skillGap: ["skill_gap"],
  humanCapitalROI: ["human_capital_roi"],
} as const;

function getItemCode(i: DisclosureMetricItem): string {
  return (i.code ?? i.categoryCode ?? "").toLowerCase().replace(/-/g, "_");
}

function findValue(
  items: DisclosureMetricItem[],
  codes: readonly string[]
): number | undefined {
  const norm = (c: string) => c.toLowerCase().replace(/-/g, "_");
  const item = items.find((i) =>
    codes.some((c) => getItemCode(i) === norm(c))
  );
  return item?.value;
}

/**
 * 저장 형태(레거시 | items[])를 UI용 IfrsMetrics로 변환.
 * 기존 대시보드/폼은 이 뷰만 사용하면 됨.
 */
export function getIfrsMetricsView(
  payload: DisclosureMetricsPayload | undefined | null
): IfrsMetrics | undefined {
  if (payload == null) return undefined;
  if ("items" in payload && Array.isArray(payload.items)) {
    const items = payload.items as DisclosureMetricItem[];
    const transitionReadyScore = findValue(
      items,
      LEGACY_CODES.transitionReadyScore
    );
    const skillGap = findValue(items, LEGACY_CODES.skillGap);
    const humanCapitalROI = findValue(items, LEGACY_CODES.humanCapitalROI);
    if (
      transitionReadyScore === undefined &&
      skillGap === undefined &&
      humanCapitalROI === undefined
    ) {
      return undefined;
    }
    return {
      transitionReadyScore: transitionReadyScore ?? 0,
      skillGap: skillGap ?? 0,
      humanCapitalROI: humanCapitalROI ?? 0,
    };
  }
  return payload as IfrsMetrics;
}

/**
 * 표준·코드로 단일 지표 값 조회 (확장 지표용). code 또는 categoryCode로 매칭.
 */
export function getDisclosureMetric(
  payload: DisclosureMetricsPayload | undefined | null,
  standard: string,
  code: string
): number | undefined {
  if (payload == null) return undefined;
  if ("items" in payload && Array.isArray(payload.items)) {
    const want = code.toLowerCase().replace(/-/g, "_");
    const item = (payload.items as DisclosureMetricItem[]).find(
      (i) => i.standard === standard && getItemCode(i) === want
    );
    return item?.value;
  }
  return undefined;
}
