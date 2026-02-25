"use client";

import { ReportPreviewCharts } from "./ReportPreviewCharts";
import type { PerformanceMetrics, DisclosureSummary, ImpactDataPoint } from "../types";

export interface ReportContentProps {
  reportTitle: string;
  summaryName: string;
  metrics: PerformanceMetrics | null;
  chartData: ImpactDataPoint[];
  disclosureSummary: DisclosureSummary | null;
  /** 이사회 보고(전체화면)용 차트 스타일 */
  reportMode?: boolean;
}

export function ReportContent({
  reportTitle,
  summaryName,
  metrics,
  chartData,
  disclosureSummary,
  reportMode = false,
}: ReportContentProps) {
  return (
    <>
      <header className="block border-b border-border pb-4 leading-relaxed">
        <p className="block text-xs font-medium uppercase tracking-wider text-muted-foreground leading-relaxed">
          Success DNA · 인적 자본 가치 공시
        </p>
        <h1 className="mt-2 block text-xl font-bold leading-snug text-foreground">{reportTitle}</h1>
        <p className="mt-1 block text-sm leading-relaxed text-muted-foreground">{summaryName}</p>
      </header>

      <div className="mt-6 grid min-w-0 grid-cols-1 gap-6 md:grid-cols-[1fr,1.15fr]">
        <div className="flex min-w-0 flex-col gap-8 space-y-0">
          {metrics && (
            <section className="mb-10 break-inside-avoid">
              <h2 className="block text-xs font-semibold uppercase tracking-wider leading-relaxed text-muted-foreground">
                핵심 지표 요약
              </h2>
              <div className="mt-2 grid grid-cols-2 gap-3">
                <div className="rounded-lg bg-muted p-3">
                  <p className="text-[10px] text-muted-foreground">인적자본 투자수익률</p>
                  <p className="text-lg font-bold text-foreground">{metrics.humanCapitalROI.toFixed(2)}</p>
                </div>
                <div className="rounded-lg bg-muted p-3">
                  <p className="text-[10px] text-muted-foreground">지속가능 기여도</p>
                  <p className="text-lg font-bold text-foreground">{metrics.sustainabilityImpact}점</p>
                </div>
                <div className="rounded-lg bg-muted p-3">
                  <p className="text-[10px] text-muted-foreground">성과 지수</p>
                  <p className="text-lg font-bold text-foreground">{metrics.performanceIndex}점</p>
                </div>
                <div className="rounded-lg bg-muted p-3">
                  <p className="text-[10px] text-muted-foreground">교육 이수 시간</p>
                  <p className="text-lg font-bold text-foreground">{metrics.trainingHours}h</p>
                </div>
              </div>
            </section>
          )}

          {chartData.length > 0 && (
            <section className="break-inside-avoid mb-10">
              <h2 className="block text-xs font-semibold uppercase tracking-wider leading-relaxed text-muted-foreground">
                성과·미래 가치 (표)
              </h2>
              <div className="mt-2 rounded-lg border border-border bg-muted/50 p-3">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-border text-left text-muted-foreground">
                      <th className="pb-1.5 font-medium">구간</th>
                      <th className="pb-1.5 font-medium">과거 성과</th>
                      <th className="pb-1.5 font-medium">AI 예측</th>
                    </tr>
                  </thead>
                  <tbody>
                    {chartData.map((row) => (
                      <tr key={row.period} className="border-b border-border/60 last:border-0">
                        <td className="py-1.5 font-medium text-foreground">{row.period}</td>
                        <td className="py-1.5 text-muted-foreground">{row.pastPerformance}점</td>
                        <td className="py-1.5 text-muted-foreground">{row.futureValue}점</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <p className="mt-2 text-[10px] text-muted-foreground">
                  Q1–Q4: 실제 성과 · Q5–Q6: AI 예측치
                </p>
              </div>
            </section>
          )}

          {disclosureSummary && (
            <section className="break-inside-avoid mb-10">
              <h2 className="block text-xs font-semibold uppercase tracking-wider leading-relaxed text-muted-foreground">
                IFRS S1/S2 공시 요약
              </h2>
              <div className="mt-2 space-y-3 rounded-lg border border-border bg-muted/30 p-4">
                <p className="block text-xs leading-relaxed text-foreground">{disclosureSummary.narrative}</p>
                <div className="block border-t border-border pt-3">
                  <p className="block text-[10px] font-medium leading-relaxed text-muted-foreground">IFRS S1 요약</p>
                  <p className="mt-0.5 block text-xs leading-relaxed text-muted-foreground">{disclosureSummary.ifrsS1Summary}</p>
                </div>
                <div className="block border-t border-border pt-3">
                  <p className="block text-[10px] font-medium leading-relaxed text-muted-foreground">IFRS S2 요약</p>
                  <p className="mt-0.5 block text-xs leading-relaxed text-muted-foreground">{disclosureSummary.ifrsS2Summary}</p>
                </div>
              </div>
            </section>
          )}
        </div>

        <div className="min-w-0 break-inside-avoid rounded-lg border border-border bg-muted/30 p-4">
          <ReportPreviewCharts metrics={metrics} chartData={chartData} reportMode={reportMode} />
        </div>
      </div>

      <footer className="mt-6 block border-t border-border pt-4 pb-1 text-center text-[10px] leading-relaxed text-muted-foreground">
        본 문서는 Success DNA 시스템에서 생성된 시뮬레이션 미리보기이며, PDF 저장 시 동일 레이아웃으로 출력됩니다.
      </footer>
    </>
  );
}
