"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  LabelList,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { Employee } from "@/modules/shared/types";
import { PIE_PALETTE_INDIGO_EMERALD, DEPARTMENT_BAR_COLORS } from "@/modules/shared/constants/chartColors";
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
  const genderTotal = genderData.reduce((s, d) => s + d.value, 0);
  const employmentTotal = employmentData.reduce((s, d) => s + d.value, 0);

  if (!mounted) return null;

  if (employees.length === 0) {
    return (
      <div className="flex h-[240px] items-center justify-center rounded-lg border border-dashed border-border bg-muted/20 text-sm text-muted-foreground">
        직원 데이터가 없습니다. Core에서 직원을 등록하면 차트가 표시됩니다.
      </div>
    );
  }

  const pieMargin = { top: 8, right: 8, bottom: 8, left: 8 };
  const pieRadius = { inner: 44, outer: 70 };

  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <div className="min-w-0 rounded-lg border border-border bg-card p-3">
        <p className="mb-2 text-xs font-medium text-muted-foreground">성별 분포</p>
        <div className="mb-2 flex flex-wrap gap-1 text-[11px] text-muted-foreground">
          {genderData.map((d) => {
            const pct = genderTotal ? Math.round((d.value / genderTotal) * 100) : 0;
            return (
              <span key={`g-${d.name}`} className="rounded border border-border px-1.5 py-0.5">
                {d.name} {d.value}명 ({pct}%)
              </span>
            );
          })}
        </div>
        <ResponsiveContainer width="100%" height={220}>
          <PieChart margin={pieMargin}>
            <Pie
              data={genderData}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              innerRadius={pieRadius.inner}
              outerRadius={pieRadius.outer}
              paddingAngle={1.5}
              labelLine={false}
            >
              {genderData.map((_, i) => (
                <Cell key={i} fill={PIE_PALETTE_INDIGO_EMERALD[i % PIE_PALETTE_INDIGO_EMERALD.length]} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(var(--chart-tooltip-bg))",
                border: "1px solid hsl(var(--chart-tooltip-border))",
                borderRadius: "var(--radius)",
              }}
              cursor={{ fill: "hsl(var(--chart-cursor-fill) / var(--chart-cursor-opacity))" }}
              formatter={(value: number | undefined) => {
                const n = value ?? 0;
                const pct = genderTotal ? Math.round((n / genderTotal) * 100) : 0;
                return [`${n}명 (${pct}%)`, "성별"];
              }}
              position={{ y: 0 }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <div className="min-w-0 rounded-lg border border-border bg-card p-3">
        <p className="mb-2 text-xs font-medium text-muted-foreground">고용형태 분포</p>
        <div className="mb-2 flex flex-wrap gap-1 text-[11px] text-muted-foreground">
          {employmentData.map((d) => {
            const pct = employmentTotal ? Math.round((d.value / employmentTotal) * 100) : 0;
            return (
              <span key={`e-${d.name}`} className="rounded border border-border px-1.5 py-0.5">
                {d.name} {d.value}명 ({pct}%)
              </span>
            );
          })}
        </div>
        <ResponsiveContainer width="100%" height={220}>
          <PieChart margin={pieMargin}>
            <Pie
              data={employmentData}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              innerRadius={pieRadius.inner}
              outerRadius={pieRadius.outer}
              paddingAngle={1.5}
              labelLine={false}
            >
              {employmentData.map((_, i) => (
                <Cell key={i} fill={PIE_PALETTE_INDIGO_EMERALD[i % PIE_PALETTE_INDIGO_EMERALD.length]} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(var(--chart-tooltip-bg))",
                border: "1px solid hsl(var(--chart-tooltip-border))",
                borderRadius: "var(--radius)",
              }}
              cursor={{ fill: "hsl(var(--chart-cursor-fill) / var(--chart-cursor-opacity))" }}
              formatter={(value: number | undefined) => {
                const n = value ?? 0;
                const pct = employmentTotal ? Math.round((n / employmentTotal) * 100) : 0;
                return [`${n}명 (${pct}%)`, "고용형태"];
              }}
              position={{ y: 0 }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: [0.25, 0.46, 0.45, 0.94] }}
        className="min-w-0 rounded-lg border border-border bg-card p-3"
      >
        <h3 className="mb-2 text-xs font-medium text-muted-foreground">부서별 인원 현황</h3>
        <ResponsiveContainer width="100%" height={220}>
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
              barSize={30}
              radius={[0, 4, 4, 0]}
              name="인원"
            >
              {departmentData.map((_, i) => (
                <Cell key={i} fill={DEPARTMENT_BAR_COLORS[i % DEPARTMENT_BAR_COLORS.length]} />
              ))}
              <LabelList dataKey="인원" position="right" formatter={(v: unknown) => `${Number(v ?? 0)}명`} />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </motion.div>
    </div>
  );
}
