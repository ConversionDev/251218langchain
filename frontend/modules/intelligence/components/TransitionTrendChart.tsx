"use client";

import { useState, useEffect } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Legend,
} from "recharts";
import type { TransitionTrendPoint } from "../types";

interface TransitionTrendChartProps {
  data: TransitionTrendPoint[];
  /** S2 Benchmark: 전환 준비 완료로 간주하는 최소 준비 점수 (목표선) */
  goalScore?: number;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: readonly { value?: number }[];
  label?: string | number;
  goalScore?: number;
}

function CustomTooltip({ active, payload, label, goalScore }: CustomTooltipProps) {
  if (!active || !payload?.length || payload[0].value == null) return null;
  const value = Number(payload[0].value);
  const gap =
    goalScore != null
      ? value >= goalScore
        ? "목표 달성"
        : `목표 대비 ${goalScore - value}점 부족`
      : null;
  const labelStr = label == null ? "" : String(label);

  return (
    <div
      className="rounded-lg border border-border bg-card px-3 py-2 text-sm shadow-md"
      style={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))" }}
    >
      <p className="font-medium text-foreground">{labelStr}</p>
      <p className="mt-1 text-muted-foreground">
        전환 준비도: <strong className="text-foreground">{value}점</strong>
      </p>
      {gap != null && (
        <p className={value >= (goalScore ?? 0) ? "text-green-600 dark:text-green-400" : "text-amber-600 dark:text-amber-400"}>
          {gap}
        </p>
      )}
    </div>
  );
}

export function TransitionTrendChart({ data, goalScore }: TransitionTrendChartProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <div className="h-[320px] w-full animate-pulse rounded-lg bg-muted/50" />
    );
  }

  return (
    <ResponsiveContainer width="100%" height={320}>
      <AreaChart
        data={data}
        margin={{ top: 16, right: 16, bottom: 16, left: 16 }}
      >
        <defs>
          <linearGradient id="transitionGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="hsl(var(--primary))" stopOpacity={0.4} />
            <stop offset="100%" stopColor="hsl(var(--primary))" stopOpacity={0.05} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
        <XAxis
          dataKey="monthLabel"
          tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }}
          interval="preserveStartEnd"
        />
        <YAxis
          domain={[0, 100]}
          tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }}
          tickFormatter={(v) => `${v}`}
        />
        <Tooltip
          content={(props) => <CustomTooltip {...props} goalScore={goalScore} />}
        />
        <Area
          type="monotone"
          dataKey="transitionReadyScore"
          name="전환 준비도"
          stroke="hsl(var(--primary))"
          strokeWidth={2}
          fill="url(#transitionGradient)"
        />
        {goalScore != null && (
          <ReferenceLine
            y={goalScore}
            stroke="hsl(0 72% 51%)"
            strokeWidth={2}
            strokeDasharray="6 4"
            label={{
              value: "S2 목표 (최소 준비도)",
              position: "right",
              fill: "hsl(var(--foreground))",
              fontSize: 11,
            }}
          />
        )}
        <Legend />
      </AreaChart>
    </ResponsiveContainer>
  );
}
