"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
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
} from "recharts";
import type { ImpactDataPoint } from "../types";
import { BRAND_CHART_COLORS } from "@/modules/shared/constants/chartColors";

interface ImpactAnalysisChartProps {
  data: ImpactDataPoint[];
  /** 공시 모드: 고정 높이 500px 컨테이너 사용 (레이아웃 붕괴 방지) */
  disclosureMode?: boolean;
}

const CHART_HEIGHT_DEFAULT = 320;
const CHART_HEIGHT_DISCLOSURE = 500;

export function ImpactAnalysisChart({ data, disclosureMode }: ImpactAnalysisChartProps) {
  const [mounted, setMounted] = useState(false);
  const chartHeight = disclosureMode ? CHART_HEIGHT_DISCLOSURE : CHART_HEIGHT_DEFAULT;

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <div className="w-full animate-pulse rounded-lg bg-muted/50" style={{ height: chartHeight }} />
    );
  }

  if (!data.length) {
    return (
      <div
        className="flex items-center justify-center rounded-lg border border-border bg-muted/20 text-sm text-muted-foreground"
        style={{ height: chartHeight }}
      >
        데이터가 없습니다.
      </div>
    );
  }

  const chart = (
    <ResponsiveContainer width="100%" height={chartHeight}>
        <ComposedChart data={data} margin={{ top: 16, right: 16, left: 16, bottom: 16 }}>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="hsl(var(--border))"
            vertical={false}
          />
          <XAxis
            dataKey="period"
            tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }}
          />
          <YAxis
            domain={[0, 100]}
            tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "hsl(var(--chart-tooltip-bg))",
              border: "1px solid hsl(var(--chart-tooltip-border))",
              borderRadius: "var(--radius)",
            }}
            cursor={{ fill: "hsl(var(--chart-cursor-fill) / var(--chart-cursor-opacity))" }}
          />
          <Legend />
          <Bar
            dataKey="pastPerformance"
            name="과거 성과"
            fill={BRAND_CHART_COLORS.primary}
            barSize={28}
            radius={[4, 4, 0, 0]}
            animationBegin={0}
            animationDuration={500}
          />
          <Line
            type="monotone"
            dataKey="futureValue"
            name="AI 예측 미래 가치"
            stroke={BRAND_CHART_COLORS.secondary}
            strokeWidth={2}
            dot={{ r: 4 }}
            animationBegin={300}
            animationDuration={500}
          />
        </ComposedChart>
      </ResponsiveContainer>
  );

  if (disclosureMode) {
    return (
      <div className="relative block h-[500px] w-full" style={{ minHeight: 500 }}>
        {chart}
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.25, 0.46, 0.45, 0.94] }}
      className="w-full"
    >
      {chart}
    </motion.div>
  );
}
