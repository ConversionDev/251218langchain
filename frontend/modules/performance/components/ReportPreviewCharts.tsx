"use client";

import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
} from "recharts";
import type { PerformanceMetrics, ImpactDataPoint } from "../types";

/** PDF/공시 미리보기용 색상 (흰 배경에 맞춤) */
const REPORT_CHART_COLORS = {
  primary: "#6366f1",
  secondary: "#10b981",
  grid: "#e2e8f0",
  text: "#64748b",
  textStrong: "#0f172a",
} as const;

interface ReportPreviewChartsProps {
  metrics: PerformanceMetrics | null;
  chartData: ImpactDataPoint[];
  /** 이사회 보고 모드(전체화면)일 때 차트 높이 확대 */
  reportMode?: boolean;
}

export function ReportPreviewCharts({ metrics, chartData, reportMode }: ReportPreviewChartsProps) {
  if (!metrics && !chartData.length) return null;

  const metricBars = metrics
    ? [
        { name: "HC ROI", value: Math.min(metrics.humanCapitalROI * 25, 100), label: metrics.humanCapitalROI.toFixed(2) },
        { name: "Sustainability", value: metrics.sustainabilityImpact, label: `${metrics.sustainabilityImpact}점` },
        { name: "Performance", value: metrics.performanceIndex, label: `${metrics.performanceIndex}점` },
        { name: "교육시간", value: Math.min(metrics.trainingHours * 2.5, 100), label: `${metrics.trainingHours}h` },
      ]
    : [];

  return (
    <div className="flex flex-col gap-6">
      {chartData.length > 0 && (
        <div className="rounded-lg border border-slate-200 bg-slate-50/50 p-4">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            성과·미래 가치 추이
          </h3>
          <div className={`mt-3 w-full ${reportMode ? "h-[400px]" : "h-[220px]"}`}>
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={chartData} margin={{ top: 8, right: 8, left: -8, bottom: 8 }}>
                <CartesianGrid stroke={REPORT_CHART_COLORS.grid} strokeDasharray="3 3" vertical={false} />
                <XAxis
                  dataKey="period"
                  tick={{ fill: REPORT_CHART_COLORS.text, fontSize: 10 }}
                />
                <YAxis
                  domain={[0, 100]}
                  tick={{ fill: REPORT_CHART_COLORS.text, fontSize: 10 }}
                  width={24}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#fff",
                    border: "1px solid #e2e8f0",
                    borderRadius: "6px",
                    fontSize: "12px",
                  }}
                  formatter={(value) => [`${value ?? 0}점`, ""]}
                  labelFormatter={(label) => label}
                />
                <Legend wrapperStyle={{ fontSize: 10 }} />
                <Bar
                  dataKey="pastPerformance"
                  name="과거 성과"
                  fill={REPORT_CHART_COLORS.primary}
                  barSize={20}
                  radius={[4, 4, 0, 0]}
                  animationDuration={400}
                />
                <Line
                  type="monotone"
                  dataKey="futureValue"
                  name="AI 예측 미래 가치"
                  stroke={REPORT_CHART_COLORS.secondary}
                  strokeWidth={2}
                  dot={{ r: 3 }}
                  animationDuration={400}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
          <p className="mt-2 text-[10px] text-slate-500">
            Q1–Q4: 실제 성과 · Q5–Q6: AI 예측치
          </p>
        </div>
      )}

      {metricBars.length > 0 && (
        <div className="rounded-lg border border-slate-200 bg-slate-50/50 p-4">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            핵심 지표
          </h3>
          <div className={`mt-3 w-full ${reportMode ? "h-[200px]" : "h-[140px]"}`}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={metricBars}
                layout="vertical"
                margin={{ top: 0, right: 8, left: 40, bottom: 0 }}
              >
                <CartesianGrid stroke={REPORT_CHART_COLORS.grid} strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" domain={[0, 100]} hide />
                <YAxis
                  type="category"
                  dataKey="name"
                  tick={{ fill: REPORT_CHART_COLORS.text, fontSize: 10 }}
                  width={70}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#fff",
                    border: "1px solid #e2e8f0",
                    borderRadius: "6px",
                    fontSize: "11px",
                  }}
                  formatter={(value, _name, item) => [
                    (item?.payload as { label?: string } | undefined)?.label ?? String(value ?? ""),
                    "",
                  ]}
                />
                <Bar
                  dataKey="value"
                  fill={REPORT_CHART_COLORS.primary}
                  barSize={14}
                  radius={[0, 4, 4, 0]}
                  animationDuration={400}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      <div className="flex-1 min-h-[40px]" />
    </div>
  );
}
