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
      <header className="block border-b border-slate-200 pb-4 leading-relaxed">
        <p className="block text-xs font-medium uppercase tracking-wider text-slate-500 leading-relaxed">
          Success DNA · 인적 자본 가치 공시
        </p>
        <h1 className="mt-2 block text-xl font-bold leading-snug text-slate-900">{reportTitle}</h1>
        <p className="mt-1 block text-sm leading-relaxed text-slate-600">{summaryName}</p>
      </header>

      <div className="mt-6 grid min-w-0 grid-cols-1 gap-6 md:grid-cols-[1fr,1.15fr]">
        <div className="flex min-w-0 flex-col gap-8 space-y-0">
          {metrics && (
            <section className="mb-10 break-inside-avoid">
              <h2 className="block text-xs font-semibold uppercase tracking-wider leading-relaxed text-slate-500">
                핵심 지표 요약
              </h2>
              <div className="mt-2 grid grid-cols-2 gap-3">
                <div className="rounded-lg bg-slate-50 p-3">
                  <p className="text-[10px] text-slate-500">Human Capital ROI</p>
                  <p className="text-lg font-bold text-slate-900">{metrics.humanCapitalROI.toFixed(2)}</p>
                </div>
                <div className="rounded-lg bg-slate-50 p-3">
                  <p className="text-[10px] text-slate-500">Sustainability Impact</p>
                  <p className="text-lg font-bold text-slate-900">{metrics.sustainabilityImpact}점</p>
                </div>
                <div className="rounded-lg bg-slate-50 p-3">
                  <p className="text-[10px] text-slate-500">Performance Index</p>
                  <p className="text-lg font-bold text-slate-900">{metrics.performanceIndex}점</p>
                </div>
                <div className="rounded-lg bg-slate-50 p-3">
                  <p className="text-[10px] text-slate-500">교육 이수 시간</p>
                  <p className="text-lg font-bold text-slate-900">{metrics.trainingHours}h</p>
                </div>
              </div>
            </section>
          )}

          {chartData.length > 0 && (
            <section className="break-inside-avoid mb-10">
              <h2 className="block text-xs font-semibold uppercase tracking-wider leading-relaxed text-slate-500">
                성과·미래 가치 (표)
              </h2>
              <div className="mt-2 rounded-lg border border-slate-200 bg-slate-50/50 p-3">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-slate-200 text-left text-slate-500">
                      <th className="pb-1.5 font-medium">구간</th>
                      <th className="pb-1.5 font-medium">과거 성과</th>
                      <th className="pb-1.5 font-medium">AI 예측</th>
                    </tr>
                  </thead>
                  <tbody>
                    {chartData.map((row) => (
                      <tr key={row.period} className="border-b border-slate-100 last:border-0">
                        <td className="py-1.5 font-medium text-slate-700">{row.period}</td>
                        <td className="py-1.5 text-slate-600">{row.pastPerformance}점</td>
                        <td className="py-1.5 text-slate-600">{row.futureValue}점</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <p className="mt-2 text-[10px] text-slate-500">
                  Q1–Q4: 실제 성과 · Q5–Q6: AI 예측치
                </p>
              </div>
            </section>
          )}

          {disclosureSummary && (
            <section className="break-inside-avoid mb-10">
              <h2 className="block text-xs font-semibold uppercase tracking-wider leading-relaxed text-slate-500">
                IFRS S1/S2 공시 요약
              </h2>
              <div className="mt-2 space-y-3 rounded-lg border border-slate-200 bg-slate-50/30 p-4">
                <p className="block text-xs leading-relaxed text-slate-700">{disclosureSummary.narrative}</p>
                <div className="block border-t border-slate-200 pt-3">
                  <p className="block text-[10px] font-medium leading-relaxed text-slate-500">IFRS S1 요약</p>
                  <p className="mt-0.5 block text-xs leading-relaxed text-slate-600">{disclosureSummary.ifrsS1Summary}</p>
                </div>
                <div className="block border-t border-slate-200 pt-3">
                  <p className="block text-[10px] font-medium leading-relaxed text-slate-500">IFRS S2 요약</p>
                  <p className="mt-0.5 block text-xs leading-relaxed text-slate-600">{disclosureSummary.ifrsS2Summary}</p>
                </div>
              </div>
            </section>
          )}
        </div>

        <div className="min-w-0 break-inside-avoid rounded-lg border border-slate-200 bg-slate-50/30 p-4">
          <ReportPreviewCharts metrics={metrics} chartData={chartData} reportMode={reportMode} />
        </div>
      </div>

      <footer className="mt-6 block border-t border-slate-200 pt-4 pb-1 text-center text-[10px] leading-relaxed text-slate-400">
        본 문서는 Success DNA 시스템에서 생성된 시뮬레이션 미리보기이며, PDF 저장 시 동일 레이아웃으로 출력됩니다.
      </footer>
    </>
  );
}
