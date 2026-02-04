import type { Employee } from "@/modules/shared/types";

/** Human Capital ROI 등 통합 지표 결과 */
export interface PerformanceMetrics {
  humanCapitalROI: number;
  sustainabilityImpact: number;
  performanceIndex: number;
  dnaSum: number;
  trainingHours: number;
  virtualSalaryBase: number;
}

/** 과거/미래 시계열 한 점 (ComposedChart용) */
export interface ImpactDataPoint {
  period: string;
  pastPerformance: number;
  futureValue: number;
}

/** 공시용 AI 요약 */
export interface DisclosureSummary {
  narrative: string;
  ifrsS1Summary: string;
  ifrsS2Summary: string;
}
