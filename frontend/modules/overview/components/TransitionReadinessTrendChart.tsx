"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import type { Employee } from "@/modules/shared/types";

interface TransitionReadinessTrendChartProps {
  employees: Employee[];
}

function getQuarterlyTrend(employees: Employee[]): { quarter: string; score: number }[] {
  if (employees.length === 0) {
    return [
      { quarter: "Q1", score: 68 },
      { quarter: "Q2", score: 70 },
      { quarter: "Q3", score: 72 },
      { quarter: "Q4", score: 74 },
    ];
  }
  const avg =
    employees.reduce((s, e) => s + (e.ifrsMetrics?.transitionReadyScore ?? 0), 0) / employees.length;
  const current = Math.round(avg);
  return [
    { quarter: "Q1", score: Math.max(0, current - 4) },
    { quarter: "Q2", score: Math.max(0, current - 2) },
    { quarter: "Q3", score: Math.max(0, current - 1) },
    { quarter: "Q4", score: Math.min(100, current) },
  ];
}

export function TransitionReadinessTrendChart({ employees }: TransitionReadinessTrendChartProps) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  const data = getQuarterlyTrend(employees);

  if (!mounted) return null;

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
            formatter={(value: number) => [value, "전환 준비도"]}
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
