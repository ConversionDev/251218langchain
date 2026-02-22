"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { DNATrajectoryPoint } from "../types";
import type { SuccessDNA } from "@/modules/shared/types";
import { DNA_DIMENSION_COLORS } from "@/modules/shared/constants/dnaColors";

/** 반기 라벨 그대로 사용 (예: "2025 상반기") 또는 month "2025-06" → "25 상반기" */
function formatPeriodLabel(monthOrLabel: string): string {
  if (monthOrLabel.includes("상반기") || monthOrLabel.includes("하반기")) return monthOrLabel;
  const [y, m] = String(monthOrLabel).split("-");
  if (!y || !m) return monthOrLabel;
  return Number(m) <= 6 ? `${y.slice(-2)} 상반기` : `${y.slice(-2)} 하반기`;
}

/** 커스텀 툴팁: 달 + 역량별 점수 */
function CustomTrajectoryTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string }>;
  label?: string;
}) {
  if (!active || !payload?.length || label == null) return null;
  const periodLabel = formatPeriodLabel(String(label));
  return (
    <div
      className="rounded-lg border px-3 py-2 shadow-lg"
      style={{
        backgroundColor: "hsl(var(--chart-tooltip-bg))",
        borderColor: "hsl(var(--chart-tooltip-border))",
      }}
    >
      <p className="text-xs font-medium text-muted-foreground">{periodLabel}</p>
      {payload.map((entry) => (
        <p key={entry.name} className="mt-0.5 text-sm font-medium" style={{ color: entry.color }}>
          {entry.name}: <span className="text-foreground">{entry.value}점</span>
        </p>
      ))}
    </div>
  );
}

const DIMENSION_KEYS = [
  "leadership",
  "technical",
  "creativity",
  "collaboration",
  "adaptability",
] as const;

const DIMENSION_LABELS: Record<keyof SuccessDNA, string> = {
  leadership: "리더십",
  technical: "기술력",
  creativity: "창의성",
  collaboration: "협업",
  adaptability: "적응력",
};

const LABEL_TO_KEY: Record<string, keyof SuccessDNA> = {
  리더십: "leadership",
  기술력: "technical",
  창의성: "creativity",
  협업: "collaboration",
  적응력: "adaptability",
};

interface DNAGrowthTrajectoryChartProps {
  data: DNATrajectoryPoint[];
  /** 부모에서 제어하는 강조 역량 (레이더 차트 클릭과 연동) */
  highlightDimension?: keyof SuccessDNA | null;
  /** Legend 클릭 시 부모 상태 갱신 */
  onHighlightChange?: (dimension: keyof SuccessDNA | null) => void;
}

/** 선택 역량의 상반기 대비 하반기 성장률 (첫 시점 vs 마지막 시점) */
function getGrowthPct(data: DNATrajectoryPoint[], dimension: keyof SuccessDNA): number {
  if (!data.length) return 0;
  const first = data[0][dimension] ?? 0;
  const last = data[data.length - 1][dimension] ?? 0;
  if (first <= 0) return last > 0 ? 100 : 0;
  return Math.round(((last - first) / first) * 100);
}

export function DNAGrowthTrajectoryChart({
  data,
  highlightDimension: controlledHighlight,
  onHighlightChange,
}: DNAGrowthTrajectoryChartProps) {
  const [mounted, setMounted] = useState(false);
  const [internalHighlight, setInternalHighlight] = useState<keyof SuccessDNA | null>(null);

  const highlightDimension = controlledHighlight ?? internalHighlight;
  const setHighlightDimension = (key: keyof SuccessDNA | null) => {
    if (onHighlightChange) onHighlightChange(key);
    else setInternalHighlight(key);
  };

  useEffect(() => {
    setMounted(true);
  }, []);

  const effectiveData = data;

  if (!mounted) {
    return (
      <div className="flex min-h-[320px] w-full flex-col gap-2">
        <p className="mb-2 text-xs text-muted-foreground">
          역량을 클릭하면 해당 역량의 반기 단위 성장 궤적이 강조됩니다. (좌측 레이더 축 클릭 가능)
        </p>
        <div className="min-h-[280px] w-full flex-1 animate-pulse rounded-lg border border-border/50 bg-muted/50" />
      </div>
    );
  }

  if (!effectiveData.length) {
    return (
      <div className="flex min-h-[280px] w-full items-center justify-center rounded-lg border border-border/50 bg-muted/20 text-sm text-muted-foreground">
        DNA 성장 궤적 데이터가 없습니다.
      </div>
    );
  }

  return (
    <div className="flex min-h-0 w-full flex-1 flex-col min-w-0">
      <p className="mb-2 text-xs text-muted-foreground">
        역량을 클릭하면 해당 역량의 반기 단위 성장 궤적이 강조됩니다. (좌측 레이더 축 클릭 가능)
      </p>
      <AnimatePresence initial={false} mode="wait">
        <motion.div
          key={highlightDimension ?? "all"}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0.7 }}
          transition={{ duration: 0.35, ease: "easeOut" }}
          className="dna-trajectory-chart h-full min-h-[280px] w-full rounded-lg border border-border/50 bg-muted/20"
        >
          <div className="h-full w-full min-h-[280px] aspect-[3/2]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                key={mounted ? "ready" : "loading"}
                data={effectiveData}
                margin={{ top: 12, right: 16, left: 4, bottom: 12 }}
              >
              <defs>
                {DIMENSION_KEYS.map((key) => (
                  <linearGradient
                    key={key}
                    id={`trajectory-gradient-${key}`}
                    x1="0"
                    y1="0"
                    x2="1"
                    y2="0"
                    gradientUnits="userSpaceOnUse"
                  >
                    <stop offset="0%" stopColor={DNA_DIMENSION_COLORS[key]} stopOpacity={0.8} />
                    <stop offset="100%" stopColor={DNA_DIMENSION_COLORS[key]} stopOpacity={1} />
                  </linearGradient>
                ))}
              </defs>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="hsl(var(--border) / 0.3)"
                vertical={false}
              />
              <XAxis
                dataKey="monthLabel"
                tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10 }}
                tickFormatter={formatPeriodLabel}
                interval="preserveStartEnd"
              />
              <YAxis
                domain={[0, 100]}
                tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10 }}
                width={28}
              />
              <Tooltip
                content={<CustomTrajectoryTooltip />}
                cursor={{ fill: "hsl(var(--chart-cursor-fill) / var(--chart-cursor-opacity))" }}
              />
              <Legend
            wrapperStyle={{ fontSize: 11 }}
            formatter={(value: string) => {
              const key = LABEL_TO_KEY[value];
              const isHighlighted = highlightDimension === null || highlightDimension === key;
              return (
                <button
                  type="button"
                  className="inline-flex items-center gap-1.5 py-0.5 pr-2 transition-opacity hover:opacity-100"
                  style={{
                    opacity: isHighlighted ? 1 : 0.4,
                    fontWeight: highlightDimension === key ? 700 : 400,
                  }}
                  onClick={() =>
                    setHighlightDimension(highlightDimension === key ? null : key)
                  }
                >
                  {value}
                </button>
              );
            }}
          />
          {DIMENSION_KEYS.map((key) => {
            const isHighlighted = highlightDimension === null || highlightDimension === key;
            return (
              <Line
                key={key}
                type="monotone"
                dataKey={key}
                name={DIMENSION_LABELS[key]}
                stroke={isHighlighted ? `url(#trajectory-gradient-${key})` : DNA_DIMENSION_COLORS[key]}
                strokeWidth={isHighlighted ? 2.5 : 1}
                strokeOpacity={isHighlighted ? 1 : 0.35}
                dot={isHighlighted}
                activeDot={isHighlighted ? { r: 4 } : false}
                connectNulls
                animationDuration={600}
                animationBegin={0}
              />
            );
          })}
            </LineChart>
            </ResponsiveContainer>
          </div>
        </motion.div>
      </AnimatePresence>

      {/* 성장 서사: 차트 바로 아래, 시각 데이터와 해석이 한눈에 */}
      <AnimatePresence mode="wait">
        {highlightDimension && (() => {
          const pct = getGrowthPct(effectiveData, highlightDimension);
          return (
            <motion.div
              key={highlightDimension}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.22 }}
              className="mt-2 rounded-b-lg border-t border-border/60 bg-muted/30 px-3 py-2"
            >
              <p className="text-sm text-muted-foreground">
                <span className="font-medium text-foreground">성장 서사:</span>{" "}
                {DIMENSION_LABELS[highlightDimension]} DNA가 상반기 대비 하반기{" "}
                <strong className="text-primary">
                  {pct >= 0 ? "+" : ""}{pct}%
                </strong>{" "}
                {pct >= 0 ? "상승" : "변화"}하며 조직 내 핵심 인재로 성장 중입니다.
              </p>
            </motion.div>
          );
        })()}
      </AnimatePresence>
    </div>
  );
}
