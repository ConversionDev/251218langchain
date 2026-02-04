"use client";

import { useState, useEffect } from "react";
import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { SuccessDNA } from "@/modules/shared/types";
import { DNA_DIMENSION_COLORS } from "@/modules/shared/constants/dnaColors";

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

const DIMENSIONS: (keyof SuccessDNA)[] = [
  "leadership",
  "technical",
  "creativity",
  "collaboration",
  "adaptability",
];

interface CompanyDNARadarChartProps {
  data: SuccessDNA;
}

function toChartData(dna: SuccessDNA) {
  return DIMENSIONS.map((key) => ({
    dimension: DIMENSION_LABELS[key],
    value: dna[key] ?? 0,
  }));
}

export function CompanyDNARadarChart({ data }: CompanyDNARadarChartProps) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  if (!mounted) return null;

  const chartData = toChartData(data);

  return (
    <ResponsiveContainer width="100%" height={320}>
      <RadarChart data={chartData} margin={{ top: 24, right: 24, bottom: 24, left: 24 }}>
        <PolarGrid stroke="hsl(var(--border))" />
        <PolarAngleAxis
          dataKey="dimension"
          tick={({ payload, x, y }: { payload?: { value?: string }; x: number; y: number }) => {
            const label = payload?.value ?? "";
            const key = LABEL_TO_KEY[label];
            const fill = key ? DNA_DIMENSION_COLORS[key] : "hsl(var(--foreground))";
            return (
              <g transform={`translate(${x},${y})`}>
                <text textAnchor="middle" fill={fill} fontSize={12} fontWeight={500}>
                  {label}
                </text>
              </g>
            );
          }}
        />
        <PolarRadiusAxis
          angle={90}
          domain={[0, 100]}
          tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10 }}
        />
        <Radar
          name="전사 평균"
          dataKey="value"
          stroke="hsl(var(--primary))"
          fill="hsl(var(--primary))"
          fillOpacity={0.35}
          strokeWidth={2}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "hsl(var(--card))",
            border: "1px solid hsl(var(--border))",
            borderRadius: "var(--radius)",
          }}
          formatter={(value: number) => [`${value}점`, "전사 평균"]}
          labelFormatter={(label) => `역량: ${label}`}
        />
      </RadarChart>
    </ResponsiveContainer>
  );
}
