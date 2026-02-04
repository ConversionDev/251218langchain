"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { DNAGrowthPoint } from "../types";
import { BRAND_CHART_COLORS } from "@/modules/shared/constants/chartColors";
const PAST_COLOR = "hsl(var(--muted-foreground) / 0.5)";

interface DNAGrowthChartProps {
  data: DNAGrowthPoint[];
}

export function DNAGrowthChart({ data }: DNAGrowthChartProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted || !data.length) {
    return (
      <div className="h-[280px] w-full animate-pulse rounded-lg bg-muted/50" />
    );
  }

  const chartData = data.map((d) => ({
    name: d.label,
    "1년 전": d.pastYear,
    현재: d.current,
    성장률: d.growthPct,
  }));

  return (
    <motion.div
      className="h-[280px] w-full"
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.25, 0.46, 0.45, 0.94] }}
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 8, right: 16, left: 48, bottom: 8 }}
        >
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="hsl(var(--border))"
            vertical={false}
          />
          <XAxis
            type="number"
            domain={[0, 100]}
            tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10 }}
          />
          <YAxis
            type="category"
            dataKey="name"
            width={44}
            tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "hsl(var(--chart-tooltip-bg))",
              border: "1px solid hsl(var(--chart-tooltip-border))",
              borderRadius: "var(--radius)",
            }}
            cursor={{ fill: "hsl(var(--chart-cursor-fill) / var(--chart-cursor-opacity))" }}
            formatter={(value: number, name: string) => [
              `${value}점`,
              name === "성장률" ? `성장률 ${value}%` : name,
            ]}
            labelFormatter={(label) => `역량: ${label}`}
          />
          <Bar dataKey="1년 전" fill={PAST_COLOR} radius={[0, 2, 2, 0]} barSize={12} />
          <Bar dataKey="현재" fill={BRAND_CHART_COLORS.secondary} radius={[0, 2, 2, 0]} barSize={12} />
        </BarChart>
      </ResponsiveContainer>
      <p className="mt-2 text-xs text-muted-foreground">
        1년 전 대비 현재 역량. 교육·경험을 통한 성장 서사를 반영합니다.
      </p>
    </motion.div>
  );
}
