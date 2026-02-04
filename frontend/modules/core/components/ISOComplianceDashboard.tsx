"use client";

import { useState, useEffect, useMemo } from "react";
import { motion } from "framer-motion";
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  Line,
  ComposedChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { Users, FileCheck, Clock } from "lucide-react";
import type { Employee } from "@/modules/shared/types";
import { GENDER_CHART_COLORS, BRAND_CHART_COLORS } from "@/modules/shared/constants/chartColors";
import {
  getGenderDistribution,
  getAgeGroupDistribution,
  getDepartmentHeadcount,
} from "@/modules/shared/utils/employeeAggregates";
import { INITIAL_EMPLOYEES } from "../services";

interface ISOComplianceDashboardProps {
  employees: Employee[];
}

export function ISOComplianceDashboard({ employees }: ISOComplianceDashboardProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const { genderData, ageBarData, headcountByDeptComposed, totalCount, completeness, avgTrainingHours } =
    useMemo(() => {
      const source = employees.length > 0 ? employees : INITIAL_EMPLOYEES;
      const total = source.length;

      const isoFields: (keyof Employee)[] = ["gender", "ageBand", "employmentType", "trainingHours"];
      let filled = 0;
      source.forEach((e) => {
        filled += isoFields.filter((f) => {
          const v = e[f];
          return v !== undefined && v !== null && (typeof v !== "number" || !Number.isNaN(v));
        }).length;
      });
      const completeness = total ? Math.round((filled / (total * isoFields.length)) * 100) : 0;
      const avgTrainingHours =
        total ? Math.round((source.reduce((s, e) => s + (e.trainingHours ?? 0), 0) / total) * 10) / 10 : 0;

      return {
        genderData: getGenderDistribution(source),
        ageBarData: getAgeGroupDistribution(source),
        headcountByDeptComposed: getDepartmentHeadcount(source),
        totalCount: source.length,
        completeness,
        avgTrainingHours,
      };
    }, [employees]);

  if (!mounted) {
    return (
      <div className="grid gap-6 md:grid-cols-3">
        <div className="h-28 animate-pulse rounded-xl bg-muted/50" />
        <div className="h-28 animate-pulse rounded-xl bg-muted/50" />
        <div className="h-28 animate-pulse rounded-xl bg-muted/50" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Users className="h-5 w-5" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">총 임직원 수</p>
              <p className="text-2xl font-bold text-foreground">{totalCount}명</p>
            </div>
          </div>
        </div>
        <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <FileCheck className="h-5 w-5" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">공시 데이터 완성도</p>
              <p className="text-2xl font-bold text-foreground">{completeness}%</p>
            </div>
          </div>
        </div>
        <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Clock className="h-5 w-5" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">평균 교육 시간</p>
              <p className="text-2xl font-bold text-foreground">{avgTrainingHours}h</p>
            </div>
          </div>
        </div>
      </div>

      {/* Diversity: Gender & Age PieCharts */}
      <div className="grid gap-6 lg:grid-cols-2">
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }}
          className="rounded-xl border border-border bg-card p-6 shadow-sm"
        >
          <h3 className="text-sm font-semibold text-foreground">성별 분포</h3>
          <div className="mt-4 h-[240px] w-full min-h-[240px]">
            {genderData.length > 0 ? (
              <ResponsiveContainer width="100%" height={240}>
                <PieChart>
                  <Pie
                    data={genderData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    innerRadius={48}
                    outerRadius={80}
                    label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}
                    animationBegin={0}
                    animationDuration={800}
                  >
                    {genderData.map((entry, i) => (
                      <Cell key={i} fill={GENDER_CHART_COLORS[entry.name] ?? GENDER_CHART_COLORS["미공개"]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--chart-tooltip-bg))",
                      border: "1px solid hsl(var(--chart-tooltip-border))",
                      borderRadius: "var(--radius)",
                    }}
                    cursor={{ fill: "hsl(var(--chart-cursor-fill) / var(--chart-cursor-opacity))" }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="flex h-full items-center justify-center text-sm text-muted-foreground">데이터 없음</p>
            )}
          </div>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4, delay: 0.08, ease: [0.25, 0.46, 0.45, 0.94] }}
          className="rounded-xl border border-border bg-card p-6 shadow-sm"
        >
          <h3 className="text-sm font-semibold text-foreground">연령대 분포</h3>
          <div className="mt-4 h-[240px] w-full min-h-[240px]">
            {ageBarData.length > 0 ? (
              <ResponsiveContainer width="100%" height={240}>
                <BarChart
                  data={ageBarData}
                  margin={{ top: 8, right: 8, left: 8, bottom: 8 }}
                  barCategoryGap="20%"
                >
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="hsl(var(--border))"
                    vertical={false}
                  />
                  <XAxis
                    dataKey="name"
                    tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }}
                  />
                  <YAxis
                    allowDecimals={false}
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
                  <Bar
                    dataKey="인원"
                    fill={BRAND_CHART_COLORS.primary}
                    barSize={38}
                    radius={[4, 4, 0, 0]}
                    animationBegin={0}
                    animationDuration={600}
                  />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="flex h-full items-center justify-center text-sm text-muted-foreground">데이터 없음</p>
            )}
          </div>
        </motion.div>
      </div>

      {/* Headcount BarChart: 부서별 + 고용형태 */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.16, ease: [0.25, 0.46, 0.45, 0.94] }}
        className="rounded-xl border border-border bg-card p-6 shadow-sm"
      >
        <h3 className="text-sm font-semibold text-foreground">부서별 인원 및 고용 형태</h3>
        <div className="mt-4 h-[280px] w-full min-h-[280px]">
          {headcountByDeptComposed.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <ComposedChart
                data={headcountByDeptComposed}
                margin={{ top: 8, right: 32, left: 8, bottom: 8 }}
                barCategoryGap="12%"
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="hsl(var(--border))"
                  vertical={false}
                />
                <XAxis
                  dataKey="department"
                  tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }}
                />
                <YAxis
                  yAxisId="left"
                  allowDecimals={false}
                  tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }}
                />
                <YAxis
                  yAxisId="right"
                  orientation="right"
                  tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }}
                  tickFormatter={(v) => `${v}%`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--chart-tooltip-bg))",
                    border: "1px solid hsl(var(--chart-tooltip-border))",
                    borderRadius: "var(--radius)",
                  }}
                  cursor={{ fill: "hsl(var(--chart-cursor-fill) / var(--chart-cursor-opacity))" }}
                  formatter={(value, name) =>
                    name === "정규직비율" ? [`${Number(value)}%`, "정규직 비율"] : [value, "총 인원"]
                  }
                />
                <Legend />
                <Bar
                  yAxisId="left"
                  dataKey="총인원"
                  fill={BRAND_CHART_COLORS.primary}
                  barSize={30}
                  radius={[4, 4, 0, 0]}
                  name="총 인원"
                  animationBegin={0}
                  animationDuration={600}
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="정규직비율"
                  stroke={BRAND_CHART_COLORS.secondary}
                  strokeWidth={2}
                  name="정규직 비율"
                  dot={{ r: 4 }}
                  animationBegin={200}
                  animationDuration={600}
                />
              </ComposedChart>
            </ResponsiveContainer>
          ) : (
            <p className="flex h-full items-center justify-center text-sm text-muted-foreground">데이터 없음</p>
          )}
        </div>
      </motion.div>
    </div>
  );
}
