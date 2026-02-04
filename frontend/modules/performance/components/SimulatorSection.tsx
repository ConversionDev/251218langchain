"use client";

/**
 * 역량 시뮬레이터: 리포트 본문 흐름 안의 접기/펼치기 섹션.
 * 가치 요약 바로 아래에 두어 "이 수치를 바꾸면 위 ROI가 변한다"는 인과가 자연스럽게 보이도록 함.
 */
import { useMemo, useState, useEffect } from "react";
import { ChevronDown, ChevronUp, SlidersHorizontal } from "lucide-react";
import type { Employee, SuccessDNA } from "@/modules/shared/types";
import { getPerformanceMetrics } from "../services";
import type { PerformanceMetrics } from "../types";

const DIMENSION_LABELS: Record<keyof SuccessDNA, string> = {
  leadership: "리더십",
  technical: "기술력",
  creativity: "창의성",
  collaboration: "협업",
  adaptability: "적응력",
};

const DIMENSION_KEYS = [
  "leadership",
  "technical",
  "creativity",
  "collaboration",
  "adaptability",
] as const;

function clamp(v: number) {
  return Math.max(0, Math.min(100, Math.round(v)));
}

interface SimulatorSectionProps {
  employee: Employee | null;
  fallbackDna?: SuccessDNA;
  onMetricsChange: (metrics: PerformanceMetrics | null) => void;
}

export function SimulatorSection({
  employee,
  fallbackDna,
  onMetricsChange,
}: SimulatorSectionProps) {
  const [open, setOpen] = useState(false);
  const [deltas, setDeltas] = useState<Record<keyof SuccessDNA, number>>({
    leadership: 0,
    technical: 0,
    creativity: 0,
    collaboration: 0,
    adaptability: 0,
  });

  const baseDna = employee?.successDna ?? fallbackDna;
  const baseEmployee = useMemo(
    () =>
      employee ?? ({
        id: "agg",
        name: "전체 평균",
        jobTitle: "",
        department: "",
        successDna: fallbackDna,
        ifrsMetrics: { transitionReadyScore: 70, skillGap: 25, humanCapitalROI: 1.8 },
        trainingHours: 30,
      } as Employee),
    [employee, fallbackDna]
  );

  const simulatedDna = useMemo(() => {
    if (!baseDna) return undefined;
    return {
      leadership: clamp((baseDna.leadership ?? 0) + deltas.leadership),
      technical: clamp((baseDna.technical ?? 0) + deltas.technical),
      creativity: clamp((baseDna.creativity ?? 0) + deltas.creativity),
      collaboration: clamp((baseDna.collaboration ?? 0) + deltas.collaboration),
      adaptability: clamp((baseDna.adaptability ?? 0) + deltas.adaptability),
    };
  }, [baseDna, deltas]);

  const simulatedMetrics = useMemo((): PerformanceMetrics | null => {
    if (!simulatedDna) return null;
    return getPerformanceMetrics({ ...baseEmployee, successDna: simulatedDna });
  }, [baseEmployee, simulatedDna]);

  const hasDelta = Object.values(deltas).some((d) => d !== 0);

  useEffect(() => {
    onMetricsChange(hasDelta ? simulatedMetrics : null);
  }, [hasDelta, simulatedMetrics, onMetricsChange]);

  if (!baseDna && !fallbackDna) return null;

  return (
    <section className="rounded-xl border border-border bg-card shadow-sm">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-start justify-between gap-4 px-6 py-4 text-left transition-colors hover:bg-muted/30 sm:items-center"
        aria-expanded={open}
        aria-controls="simulator-content"
      >
        <div className="min-w-0 flex-1">
          <span className="flex items-center gap-2">
            <SlidersHorizontal className="h-5 w-5 shrink-0 text-primary" />
            <span className="font-semibold text-foreground">역량 시뮬레이터</span>
          </span>
          <p className="mt-1 text-sm text-muted-foreground">
            슬라이더를 조정하면 위 가치 요약 수치가 실시간으로 변합니다.
          </p>
        </div>
        {open ? (
          <ChevronUp className="h-5 w-5 shrink-0 text-muted-foreground" />
        ) : (
          <ChevronDown className="h-5 w-5 shrink-0 text-muted-foreground" />
        )}
      </button>
      <div
        id="simulator-content"
        role="region"
        aria-labelledby="simulator-heading"
        className={open ? "border-t border-border px-6 pb-6 pt-4" : "hidden"}
      >
        <p id="simulator-heading" className="sr-only">
          역량 시뮬레이터 슬라이더
        </p>
        <div className="space-y-3">
          {DIMENSION_KEYS.map((key) => (
            <div key={key} className="flex items-center gap-3">
              <label className="w-20 shrink-0 text-sm text-muted-foreground">
                {DIMENSION_LABELS[key]}
              </label>
              <input
                type="range"
                min="-20"
                max="20"
                value={deltas[key]}
                onChange={(e) =>
                  setDeltas((prev) => ({ ...prev, [key]: Number(e.target.value) }))
                }
                className="h-2 flex-1 cursor-pointer appearance-none rounded-full bg-muted accent-primary"
              />
              <span className="w-10 text-right text-sm tabular-nums text-foreground">
                {deltas[key] >= 0 ? "+" : ""}{deltas[key]}
              </span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
