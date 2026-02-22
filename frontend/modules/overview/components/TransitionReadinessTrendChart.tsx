"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { getIfrsMetricsView } from "@/modules/shared/utils/disclosureMetrics";
import type { Employee } from "@/modules/shared/types";

interface TransitionReadinessTrendChartProps {
  employees: Employee[];
}

/** 실제 DB의 전환 준비도만 사용. 목/합성 분기 데이터 없음 */
function getQuarterlyTrend(employees: Employee[]): { quarter: string; score: number }[] {
  if (employees.length === 0) return [];
  const withScore = employees.filter(
    (e) => getIfrsMetricsView(e.disclosureMetrics)?.transitionReadyScore != null
  );
  if (withScore.length === 0) return [];
  const sum = withScore.reduce(
    (s, e) => s + (getIfrsMetricsView(e.disclosureMetrics)?.transitionReadyScore ?? 0),
    0
  );
  const current = Math.round(sum / withScore.length);
  return [{ quarter: "현재", score: Math.max(0, Math.min(100, current)) }];
}

export function TransitionReadinessTrendChart({ employees }: TransitionReadinessTrendChartProps) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  const data = getQuarterlyTrend(employees);

  if (!mounted) return null;

  if (data.length === 0) {
    return (
      <div className="flex h-[280px] items-center justify-center rounded-lg border border-dashed border-border bg-muted/20 text-sm text-muted-foreground">
        전환 준비도 데이터가 없습니다. (실제 DB 기준)
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] }}
      className="w-full"
    >
      <ResponsiveContainer width="100%" height={280}>
        <AreaChart data={data} margin={{ top: 16, right: 16, left: 8, bottom: 8 }}>
          <defs>
            <linearGradient id="transitionReadinessGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="hsl(var(--primary))" stopOpacity={0.4} />
              <stop offset="100%" stopColor="hsl(var(--primary))" stopOpacity={0.05} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis
            dataKey="quarter"
            tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
          />
          <YAxis
            domain={[0, 100]}
            tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }}
            width={28}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "hsl(var(--card))",
              border: "1px solid hsl(var(--border))",
              borderRadius: "var(--radius)",
            }}
            formatter={(value: number | undefined) => [value ?? 0, "전환 준비도"]}
            labelFormatter={(label) => `분기: ${label}`}
          />
          <Area
            type="monotone"
            dataKey="score"
            name="전환 준비도"
            stroke="hsl(var(--primary))"
            strokeWidth={2}
            fill="url(#transitionReadinessGradient)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </motion.div>
  );
}
