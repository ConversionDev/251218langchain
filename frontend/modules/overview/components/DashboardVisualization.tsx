"use client";

import { useMemo } from "react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { useStore } from "@/store/useStore";
import { useHydrated } from "@/hooks/use-hydrated";
import type { SuccessDNA } from "@/modules/shared/types";
import { CompanyDNARadarChart } from "./CompanyDNARadarChart";
import { PeopleCompositionCharts } from "./PeopleCompositionCharts";
import { TransitionReadinessTrendChart } from "./TransitionReadinessTrendChart";

const DEFAULT_AVERAGE_DNA: SuccessDNA = {
  leadership: 70,
  technical: 72,
  creativity: 68,
  collaboration: 75,
  adaptability: 74,
};

function useCompanyAverageDNA(): SuccessDNA {
  const employees = useStore((s) => s.employees);
  return useMemo(() => {
    const withDna = employees.filter((e) => e.successDna);
    if (withDna.length === 0) return DEFAULT_AVERAGE_DNA;
    const sum: SuccessDNA = {
      leadership: 0,
      technical: 0,
      creativity: 0,
      collaboration: 0,
      adaptability: 0,
    };
    withDna.forEach((e) => {
      const d = e.successDna!;
      (Object.keys(sum) as (keyof SuccessDNA)[]).forEach((k) => (sum[k] += d[k] ?? 0));
    });
    const n = withDna.length;
    return {
      leadership: Math.round(sum.leadership / n),
      technical: Math.round(sum.technical / n),
      creativity: Math.round(sum.creativity / n),
      collaboration: Math.round(sum.collaboration / n),
      adaptability: Math.round(sum.adaptability / n),
    };
  }, [employees]);
}

function ChartSkeleton({ className }: { className?: string }) {
  return (
    <div className={`animate-pulse rounded-lg bg-muted/50 ${className ?? ""}`} />
  );
}

export function DashboardVisualization() {
  const hydrated = useHydrated();
  const employees = useStore((s) => s.employees);
  const companyAverageDNA = useCompanyAverageDNA();

  if (!hydrated) {
    return (
      <div className="report-grid-bg space-y-6 rounded-xl p-6">
        <Card className="border-border bg-card">
          <CardHeader>
            <div className="h-5 w-40 rounded bg-muted/70" />
            <div className="mt-1 h-4 w-56 rounded bg-muted/50" />
          </CardHeader>
          <CardContent>
            <ChartSkeleton className="h-[320px] w-full" />
          </CardContent>
        </Card>
        <div className="grid gap-6 lg:grid-cols-2">
          <Card className="border-border bg-card">
            <CardHeader>
              <div className="h-5 w-32 rounded bg-muted/70" />
            </CardHeader>
            <CardContent>
              <ChartSkeleton className="h-[240px] w-full" />
            </CardContent>
          </Card>
          <Card className="border-border bg-card">
            <CardHeader>
              <div className="h-5 w-36 rounded bg-muted/70" />
            </CardHeader>
            <CardContent>
              <ChartSkeleton className="h-[240px] w-full" />
            </CardContent>
          </Card>
        </div>
        <Card className="border-border bg-card">
          <CardHeader>
            <div className="h-5 w-48 rounded bg-muted/70" />
            <div className="mt-1 h-4 w-64 rounded bg-muted/50" />
          </CardHeader>
          <CardContent>
            <ChartSkeleton className="h-[280px] w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="report-grid-bg space-y-6 rounded-xl p-6">
      <Card className="border-border bg-card">
        <CardHeader>
          <h2 className="text-lg font-semibold text-foreground">전사 평균 역량 DNA</h2>
          <p className="text-sm text-muted-foreground">
            전체 직원의 Success DNA 5대 역량 평균을 레이더로 표시합니다.
          </p>
        </CardHeader>
        <CardContent>
          <CompanyDNARadarChart data={companyAverageDNA} />
        </CardContent>
      </Card>

      <Card className="border-border bg-card">
        <CardHeader>
          <h2 className="text-lg font-semibold text-foreground">인적 자본 구성</h2>
          <p className="text-sm text-muted-foreground">
            성별·고용 형태 분포와 부서별 인원 현황입니다.
          </p>
        </CardHeader>
        <CardContent>
          <PeopleCompositionCharts employees={employees} />
        </CardContent>
      </Card>

      <Card className="border-border bg-card">
        <CardHeader>
          <h2 className="text-lg font-semibold text-foreground">조직 역량 성장 추이</h2>
          <p className="text-sm text-muted-foreground">
            분기별 전사 평균 전환 준비도(Transition Readiness) 추이입니다.
          </p>
        </CardHeader>
        <CardContent>
          <TransitionReadinessTrendChart employees={employees} />
        </CardContent>
      </Card>
    </div>
  );
}
