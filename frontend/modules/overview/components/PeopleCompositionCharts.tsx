"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { Employee } from "@/modules/shared/types";
import { PIE_PALETTE_INDIGO_EMERALD, BRAND_CHART_COLORS } from "@/modules/shared/constants/chartColors";
import {
  getGenderDistribution,
  getEmploymentDistribution,
  getDepartmentHeadcount,
} from "@/modules/shared/utils/employeeAggregates";

interface PeopleCompositionChartsProps {
  employees: Employee[];
}

export function PeopleCompositionCharts({ employees }: PeopleCompositionChartsProps) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  const genderData = getGenderDistribution(employees);
  const employmentData = getEmploymentDistribution(employees);
  const departmentData = getDepartmentHeadcount(employees)
    .map((d) => ({ name: d.department, 인원: d.총인원 }))
    .sort((a, b) => b.인원 - a.인원);

  if (!mounted) return null;

  if (employees.length === 0) {
    return (
      <div className="flex h-[240px] items-center justify-center rounded-lg border border-dashed border-border bg-muted/20 text-sm text-muted-foreground">
        직원 데이터가 없습니다. Core에서 직원을 등록하면 차트가 표시됩니다.
      </div>
    );
  }

  const legendStyle = { paddingTop: 8, fontSize: 11 };
  const pieMargin = { top: 16, right: 16, bottom: 48, left: 16 };
  const pieRadius = { inner: 40, outer: 62 };

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <div className="space-y-4">
        <h3 className="text-sm font-medium text-muted-foreground">성별 · 고용 형태</h3>
        <div className="grid grid-cols-2 gap-4">
          {/* 성별 도넛: 여백 확보로 잘림 방지, 범례 스타일 통일 */}
          <div className="min-w-0 overflow-hidden">
            <ResponsiveContainer width="100%" height={240}>
              <PieChart margin={pieMargin}>
                <Pie
                  data={genderData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="42%"
                  innerRadius={pieRadius.inner}
                  outerRadius={pieRadius.outer}
                  paddingAngle={2}
                >
                  {genderData.map((_, i) => (
                    <Cell key={i} fill={PIE_PALETTE_INDIGO_EMERALD[i % PIE_PALETTE_INDIGO_EMERALD.length]} />
                  ))}
                </Pie>
                <Legend
                  layout="horizontal"
                  align="center"
                  verticalAlign="bottom"
                  wrapperStyle={legendStyle}
                  iconSize={8}
                  formatter={(value) => {
                    const item = genderData.find((d) => d.name === value);
                    const total = genderData.reduce((s, d) => s + d.value, 0);
                    const pct = item && total ? Math.round((item.value / total) * 100) : 0;
                    return `${value} ${pct}%`;
                  }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--chart-tooltip-bg))",
                    border: "1px solid hsl(var(--chart-tooltip-border))",
                    borderRadius: "var(--radius)",
                  }}
                  cursor={{ fill: "hsl(var(--chart-cursor-fill) / var(--chart-cursor-opacity))" }}
                  formatter={(value: number | undefined) => [value ?? 0, "명"]}
                  position={{ y: 0 }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          {/* 고용형태 도넛: 동일 여백·반경·범례 스타일 */}
          <div className="min-w-0 overflow-hidden">
            <ResponsiveContainer width="100%" height={240}>
              <PieChart margin={pieMargin}>
                <Pie
                  data={employmentData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="42%"
                  innerRadius={pieRadius.inner}
                  outerRadius={pieRadius.outer}
                  paddingAngle={2}
                >
                  {employmentData.map((_, i) => (
                    <Cell key={i} fill={PIE_PALETTE_INDIGO_EMERALD[i % PIE_PALETTE_INDIGO_EMERALD.length]} />
                  ))}
                </Pie>
                <Legend
                  layout="horizontal"
                  align="center"
                  verticalAlign="bottom"
                  wrapperStyle={legendStyle}
                  iconSize={8}
                  formatter={(value) => {
                    const item = employmentData.find((d) => d.name === value);
                    const total = employmentData.reduce((s, d) => s + d.value, 0);
                    const pct = item && total ? Math.round((item.value / total) * 100) : 0;
                    return `${value} ${pct}%`;
                  }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--chart-tooltip-bg))",
                    border: "1px solid hsl(var(--chart-tooltip-border))",
                    borderRadius: "var(--radius)",
                  }}
                  cursor={{ fill: "hsl(var(--chart-cursor-fill) / var(--chart-cursor-opacity))" }}
                  formatter={(value: number | undefined) => [value ?? 0, "명"]}
                  position={{ y: 0 }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
      <motion.div
        initial={{ opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: [0.25, 0.46, 0.45, 0.94] }}
        className="min-w-0 overflow-hidden"
      >
        <h3 className="mb-4 text-sm font-medium text-muted-foreground">부서별 인원 현황</h3>
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={departmentData} layout="vertical" margin={{ top: 8, right: 32, left: 64, bottom: 8 }}>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="hsl(var(--border))"
              vertical={false}
            />
            <XAxis
              type="number"
              allowDecimals={false}
              tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }}
              domain={[0, (dataMax: number) => Math.ceil((dataMax ?? 0) * 1.1) || 1]}
            />
            <YAxis
              type="category"
              dataKey="name"
              width={56}
              tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(var(--chart-tooltip-bg))",
                border: "1px solid hsl(var(--chart-tooltip-border))",
                borderRadius: "var(--radius)",
              }}
              cursor={{ fill: "hsl(var(--chart-cursor-fill) / var(--chart-cursor-opacity))" }}
              formatter={(value: number | undefined) => [value ?? 0, "명"]}
            />
            <Bar
              dataKey="인원"
              fill={BRAND_CHART_COLORS.primary}
              barSize={30}
              radius={[0, 4, 4, 0]}
              name="인원"
            />
          </BarChart>
        </ResponsiveContainer>
      </motion.div>
    </div>
  );
}
