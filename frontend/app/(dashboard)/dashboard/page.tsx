"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Users, Brain, TrendingUp, ShieldCheck, ArrowRight } from "lucide-react";
import { useHydrated } from "@/hooks/use-hydrated";
import { getIfrsMetricsView } from "@/modules/shared/utils/disclosureMetrics";
import { getAggregatePerformanceMetrics } from "@/modules/performance/services";
import { fetchEmployees } from "@/modules/core/services";
import type { Employee } from "@/modules/shared/types";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { DashboardVisualization } from "@/modules/overview/components/DashboardVisualization";

const isoFields = ["gender", "ageBand", "employmentType", "trainingHours"] as const;

function toRegularEmployees(all: Employee[]): Employee[] {
  return (all ?? []).filter((e) => {
    const type = (e.employmentType ?? "").trim().toLowerCase();
    const status = (e.status ?? "").trim().toLowerCase();
    if (type === "new_hire") return false;
    // ATS 후보만 제외, hired는 기존 직원으로 포함
    return !["pending", "screening", "rejected"].includes(status);
  });
}

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

function hasVerifiableAnalysis(employee: Employee): boolean {
  const hasDna = !!employee.successDna;
  const m = employee.disclosureMetrics;
  if (!m) return hasDna;
  if ("items" in m) {
    return hasDna && Array.isArray(m.items) && m.items.length > 0;
  }
  return hasDna;
}

function useCredentialSummary(employees: Employee[]) {
  const total = employees.length;
  const verifiedCount = employees.filter(hasVerifiableAnalysis).length;
  const pendingCount = Math.max(0, total - verifiedCount);
  const completionRate = total ? Math.round((verifiedCount / total) * 100) : 0;
  return { total, verifiedCount, pendingCount, completionRate };
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
  const [allEmployees, setAllEmployees] = useState<Employee[]>([]);
  const [regularEmployees, setRegularEmployees] = useState<Employee[]>([]);
  const [loadError, setLoadError] = useState(false);

  useEffect(() => {
    if (!hydrated) return;
    fetchEmployees()
      .then((all) => {
        const rows = all ?? [];
        setAllEmployees(rows);
        setRegularEmployees(toRegularEmployees(rows));
        setLoadError(false);
      })
      .catch(() => {
        setAllEmployees([]);
        setRegularEmployees([]);
        setLoadError(true);
      });
  }, [hydrated]);

  const allSummary = useDashboardSummary(allEmployees);
  const regularSummary = useDashboardSummary(regularEmployees);
  const credentialSummary = useCredentialSummary(allEmployees);
  const totalEmployeesValue = loadError ? "연결 오류" : `${allSummary.totalCount}명`;
  const disclosureCompletenessValue = loadError ? "-" : `${allSummary.completeness}%`;
  const avgTrainingHoursValue = loadError ? "-" : `${allSummary.avgTrainingHours}h`;
  const transitionScoreValue = loadError ? "-" : `${regularSummary.avgTransitionScore}점`;
  const hcrValue = loadError ? "-" : regularSummary.humanCapitalROI.toFixed(2);
  const sustainabilityValue = loadError ? "-" : `${regularSummary.sustainabilityImpact}점`;
  const performanceValue = loadError ? "-" : `${regularSummary.performanceIndex}점`;
  const verifiedTotalValue = loadError
    ? "-"
    : `${credentialSummary.verifiedCount}/${credentialSummary.total}건`;
  const verificationRateValue = loadError ? "-" : `${credentialSummary.completionRate}%`;
  const pendingVerificationValue = loadError ? "-" : `${credentialSummary.pendingCount}건`;

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
        { label: "총 직원 (신입+일반)", value: totalEmployeesValue },
        { label: "공시 완성도", value: disclosureCompletenessValue },
        { label: "평균 교육 이수 시간", value: avgTrainingHoursValue },
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
        { label: "전환 준비도 평균", value: transitionScoreValue },
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
        { label: "인적자본 투자수익률", value: hcrValue },
        { label: "지속가능 기여도", value: sustainabilityValue },
        { label: "성과 지수", value: performanceValue },
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
        { label: "검증 완료/전체", value: verifiedTotalValue },
        { label: "검증 완료율", value: verificationRateValue },
        { label: "미검증", value: pendingVerificationValue },
      ],
    },
  ];

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
        <h1 className="text-2xl font-bold text-foreground">전사 현황</h1>
        <p className="mt-1 text-muted-foreground">
          핵심 인사, 역량 진단, 성과·가치 수치를 한눈에 확인하세요.
        </p>
        </div>
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

      <DashboardVisualization employees={regularEmployees} compositionEmployees={allEmployees} />
    </div>
  );
}
