"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Users, Brain, TrendingUp, ShieldCheck, ArrowRight } from "lucide-react";
import { useHydrated } from "@/hooks/use-hydrated";
import { getIfrsMetricsView } from "@/modules/shared/utils/disclosureMetrics";
import { getAggregatePerformanceMetrics } from "@/modules/performance/services";
import { fetchEmployeesPaginated } from "@/modules/core/services";
import type { Employee } from "@/modules/shared/types";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { DashboardVisualization } from "@/modules/overview/components/DashboardVisualization";

const isoFields = ["gender", "ageBand", "employmentType", "trainingHours"] as const;

function useDashboardSummary(employees: Employee[]) {
  const total = employees.length;
  let filled = 0;
  employees.forEach((e) => {
    filled += isoFields.filter((f) => {
      const v = e[f];
      return v !== undefined && v !== null && (typeof v !== "number" || !Number.isNaN(v));
    }).length;
  });
  const completeness = total ? Math.round((filled / (total * isoFields.length)) * 100) : 0;
  const avgTrainingHours =
    total
      ? Math.round((employees.reduce((s, e) => s + (e.trainingHours ?? 0), 0) / total) * 10) / 10
      : 0;
  const avgTransitionScore =
    total
      ? Math.round(
          (employees.reduce(
            (s, e) => s + (getIfrsMetricsView(e.disclosureMetrics)?.transitionReadyScore ?? 0),
            0
          ) / total)
        )
      : 0;
  const perf = getAggregatePerformanceMetrics(employees);
  return {
    totalCount: total,
    completeness,
    avgTrainingHours,
    avgTransitionScore,
    humanCapitalROI: perf?.humanCapitalROI ?? 0,
    sustainabilityImpact: perf?.sustainabilityImpact ?? 0,
    performanceIndex: perf?.performanceIndex ?? 0,
  };
}

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.08 },
  },
};

const item = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0 },
};

export default function DashboardPage() {
  const hydrated = useHydrated();
  const [regularEmployees, setRegularEmployees] = useState<Employee[]>([]);

  useEffect(() => {
    if (!hydrated) return;
    fetchEmployeesPaginated({ page: 1, pageSize: 500, employmentType: "regular" })
      .then(({ items }) => setRegularEmployees(items ?? []))
      .catch(() => setRegularEmployees([]));
  }, [hydrated]);

  const summary = useDashboardSummary(regularEmployees);

  if (!hydrated) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 animate-pulse rounded bg-muted" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-28 animate-pulse rounded-xl bg-muted/50" />
          ))}
        </div>
      </div>
    );
  }

  const widgets = [
    {
      title: "핵심 인사",
      description: "ISO 30414 준수 현황",
      icon: Users,
      href: "/core",
      color: "text-indigo-400",
      bg: "bg-indigo-500/10",
      values: [
        { label: "총 임직원", value: `${summary.totalCount}명` },
        { label: "공시 완성도", value: `${summary.completeness}%` },
        { label: "평균 교육 이수 시간", value: `${summary.avgTrainingHours}h` },
      ],
    },
    {
      title: "역량 진단",
      description: "IFRS S2 전환 준비도",
      icon: Brain,
      href: "/intelligence",
      color: "text-emerald-400",
      bg: "bg-emerald-500/10",
      values: [
        { label: "전환 준비도 평균", value: `${summary.avgTransitionScore}점` },
        { label: "Green/AI 역량", value: "분석 가능" },
      ],
    },
    {
      title: "성과·가치",
      description: "인적 자본 가치",
      icon: TrendingUp,
      href: "/performance",
      color: "text-amber-400",
      bg: "bg-amber-500/10",
      values: [
        { label: "인적자본 투자수익률", value: summary.humanCapitalROI.toFixed(2) },
        { label: "지속가능 기여도", value: `${summary.sustainabilityImpact}점` },
        { label: "성과 지수", value: `${summary.performanceIndex}점` },
      ],
    },
    {
      title: "자격 검증",
      description: "블록체인 무결성",
      icon: ShieldCheck,
      href: "/credential",
      color: "text-slate-300",
      bg: "bg-slate-500/10",
      values: [
        { label: "검증 가능 건수", value: `${summary.totalCount}건` },
        { label: "상태", value: "직원 선택 후 검증" },
      ],
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">전사 현황</h1>
        <p className="mt-1 text-muted-foreground">
          핵심 인사, 역량 진단, 성과·가치 수치를 한눈에 확인하세요.
        </p>
      </div>

      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4"
      >
        {widgets.map((w) => {
          const Icon = w.icon;
          return (
            <motion.div key={w.title} variants={item}>
              <Link href={w.href}>
                <Card className="h-full border-border bg-card transition-colors hover:bg-muted/30">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <span className="text-sm font-medium text-muted-foreground">{w.title}</span>
                    <span className={`rounded-lg p-2 ${w.bg} ${w.color}`}>
                      <Icon className="h-5 w-5" />
                    </span>
                  </CardHeader>
                  <CardContent>
                    <p className="text-xs text-muted-foreground">{w.description}</p>
                    <ul className="mt-3 space-y-1">
                      {w.values.map((v) => (
                        <li key={v.label} className="flex justify-between text-sm">
                          <span className="text-muted-foreground">{v.label}</span>
                          <span className="font-semibold text-foreground">{v.value}</span>
                        </li>
                      ))}
                    </ul>
                    <p className="mt-3 inline-flex items-center gap-1 text-xs text-primary">
                      자세히 보기
                      <ArrowRight className="h-3.5 w-3.5" />
                    </p>
                  </CardContent>
                </Card>
              </Link>
            </motion.div>
          );
        })}
      </motion.div>

      <DashboardVisualization employees={regularEmployees} />
    </div>
  );
}
