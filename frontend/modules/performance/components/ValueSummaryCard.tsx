"use client";

import { useState } from "react";
import { ShieldCheck, Info } from "lucide-react";
import { useCountUp } from "@/hooks/use-count-up";
import type { PerformanceMetrics } from "../types";

const TOOLTIPS: Record<string, string> = {
  roi: "Success DNA 5개 역량 합산점수와 연간 교육시간을 가상 연봉 상계치로 나눈 지표입니다.",
  sustainability: "적응력(Adaptability) DNA 60%와 전환 준비도(IFRS S2) 40%로 산출한 산업 전환 기여도입니다.",
  performance: "기존 KPI 성과 60%와 미래 역량(전환 준비도) 40%를 가중 합산한 통합 지수입니다.",
  training: "ISO 30414에 따른 연간 교육훈련 시간입니다.",
};

const AI_INSIGHTS: Record<string, string> = {
  roi: "Core의 DNA 점수·교육시간과 가상 연봉 상계치로 산정. IFRS S1 Value Creation 지표로 공시 가능.",
  sustainability: "Adaptability DNA와 전환 준비도(IFRS S2)를 가중하여 Green/산업 전환 기여도를 정량화.",
  performance: "과거 성과 60%와 미래 역량 40% 가중. 공시 시 Integrated Capability Index로 표기.",
  training: "ISO 30414 인적 자본 공시 필수 항목. 연간 교육훈련 이수 시간 기준.",
};

interface ValueSummaryCardProps {
  employeeName: string;
  metrics: PerformanceMetrics | null;
  /** 시뮬레이터로 변경된 지표 (있으면 이 값으로 표시 + 카운트업 애니메이션) */
  displayMetrics?: PerformanceMetrics | null;
  isDisclosureMode?: boolean;
}

function AnimatedMetric({
  value,
  format = (v) => String(Math.round(v)),
}: {
  value: number;
  format?: (v: number) => string;
}) {
  const display = useCountUp(value);
  return <>{format(display)}</>;
}

export function ValueSummaryCard({
  employeeName,
  metrics,
  displayMetrics,
  isDisclosureMode = false,
}: ValueSummaryCardProps) {
  const [tooltipKey, setTooltipKey] = useState<string | null>(null);
  const effective = displayMetrics ?? metrics;

  if (!metrics) {
    return (
      <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
        <p className="text-sm text-muted-foreground">직원을 선택하면 핵심 지표가 표시됩니다.</p>
      </div>
    );
  }

  const base = metrics;
  const showDelta = Boolean(displayMetrics);

  const items = [
    {
      key: "roi",
      label: isDisclosureMode ? "IFRS S1 Value Creation Index" : "Human Capital ROI",
      value: effective.humanCapitalROI,
      unit: "",
      format: (v: number) => v.toFixed(2),
      delta: showDelta && base.humanCapitalROI
        ? ((effective.humanCapitalROI - base.humanCapitalROI) / base.humanCapitalROI) * 100
        : null,
      deltaFormat: (d: number) => (d >= 0 ? `+${d.toFixed(1)}% 상승` : `${d.toFixed(1)}% 하락`),
    },
    {
      key: "sustainability",
      label: isDisclosureMode ? "IFRS S2 Transition Contribution" : "Sustainability Impact",
      value: effective.sustainabilityImpact,
      unit: "점",
      format: (v: number) => String(Math.round(v)),
      delta: showDelta ? effective.sustainabilityImpact - base.sustainabilityImpact : null,
      deltaFormat: (d: number) => (d >= 0 ? `+${d}점 상승` : `${d}점 하락`),
    },
    {
      key: "performance",
      label: isDisclosureMode ? "Integrated Capability Index" : "Performance Index",
      value: effective.performanceIndex,
      unit: "점",
      format: (v: number) => String(Math.round(v)),
      delta: showDelta ? effective.performanceIndex - base.performanceIndex : null,
      deltaFormat: (d: number) => (d >= 0 ? `+${d}점 상승` : `${d}점 하락`),
    },
    {
      key: "training",
      label: isDisclosureMode ? "Training Hours (ISO 30414)" : "교육 이수 시간",
      value: effective.trainingHours,
      unit: "h",
      format: (v: number) => String(Math.round(v * 10) / 10),
      delta: showDelta ? effective.trainingHours - base.trainingHours : null,
      deltaFormat: (d: number) => (d >= 0 ? `+${d}h 상승` : `${d}h 하락`),
    },
  ];

  return (
    <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-foreground">가치 요약</h2>
          <p className="mt-1 text-sm text-muted-foreground">{employeeName}</p>
        </div>
        <div
          className="inline-flex items-center gap-2 rounded-lg border border-primary/30 bg-primary/5 px-3 py-2 text-sm font-medium text-primary"
          aria-label="블록체인 검증 완료"
        >
          <ShieldCheck className="h-4 w-4 shrink-0" />
          <span>Verified by Blockchain</span>
        </div>
      </div>
      <dl className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
        {items.map((item) => (
          <div key={item.key} className="relative rounded-lg bg-muted/40 px-3 py-2">
            <dt className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
              {item.label}
              <span
                className="relative inline-flex"
                onMouseEnter={() => setTooltipKey(item.key)}
                onMouseLeave={() => setTooltipKey(null)}
              >
                <Info className="h-3.5 w-3.5 shrink-0 cursor-help opacity-70" aria-label="설명 보기" />
                {tooltipKey === item.key && (
                  <span className="absolute left-0 top-full z-10 mt-1.5 max-w-[280px] rounded-md border border-border bg-card px-2.5 py-2 text-xs font-normal text-card-foreground shadow-md">
                    <p>{TOOLTIPS[item.key]}</p>
                    {AI_INSIGHTS[item.key] && (
                      <p className="mt-2 border-t border-border pt-2 text-primary">
                        AI 분석: {AI_INSIGHTS[item.key]}
                      </p>
                    )}
                  </span>
                )}
              </span>
            </dt>
            <dd className="mt-1 flex flex-wrap items-baseline gap-2">
              <span className="text-lg font-semibold text-foreground tabular-nums">
                <AnimatedMetric value={item.value} format={item.format} />
                {item.unit}
              </span>
              {item.delta != null && item.delta !== 0 && (
                <span
                  className={
                    item.delta > 0
                      ? "text-sm font-medium text-emerald-600 dark:text-emerald-400"
                      : "text-sm font-medium text-red-600 dark:text-red-400"
                  }
                >
                  {item.deltaFormat(item.delta)}
                </span>
              )}
            </dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
