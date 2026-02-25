"use client";

import { useMemo } from "react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { useHydrated } from "@/hooks/use-hydrated";
import type { Employee, SuccessDNA } from "@/modules/shared/types";
import { CompanyDNARadarChart } from "./CompanyDNARadarChart";
import { PeopleCompositionCharts } from "./PeopleCompositionCharts";
import { TransitionReadinessTrendChart } from "./TransitionReadinessTrendChart";

/** 전사 평균 Success DNA. 역량 데이터가 한 건도 없으면 null (목 데이터 사용 안 함) */
function getCompanyAverageDNA(employees: Employee[]): SuccessDNA | null {
  const withDna = employees.filter((e) => e.successDna);
  if (withDna.length === 0) return null;
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
}

function ChartSkeleton({ className }: { className?: string }) {
  return (
    <div className={`animate-pulse rounded-lg bg-muted/50 ${className ?? ""}`} />
  );
}

interface DashboardVisualizationProps {
  employees: Employee[];
  compositionEmployees?: Employee[];
}

export function DashboardVisualization({ employees, compositionEmployees }: DashboardVisualizationProps) {
  const hydrated = useHydrated();
  const companyAverageDNA = useMemo(
    () => getCompanyAverageDNA(employees),
    [employees]
  );

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
            전체 직원의 Success DNA 5대 역량 평균을 레이더로 표시합니다. (실제 DB 기준)
          </p>
        </CardHeader>
        <CardContent>
          {companyAverageDNA ? (
            <CompanyDNARadarChart data={companyAverageDNA} />
          ) : (
            <div className="flex h-[320px] items-center justify-center rounded-lg border border-dashed border-border bg-muted/20 text-sm text-muted-foreground">
              역량 데이터가 없습니다. 직원에 AI 분석을 적용하면 차트가 표시됩니다.
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="border-border bg-card">
        <CardHeader>
          <h2 className="text-lg font-semibold text-foreground">인적 자본 구성</h2>
          <p className="text-sm text-muted-foreground">
            성별·고용 형태 분포와 부서별 인원 현황입니다. (실제 DB 기준)
          </p>
        </CardHeader>
        <CardContent>
          <PeopleCompositionCharts employees={compositionEmployees ?? employees} />
        </CardContent>
      </Card>

      <Card className="border-border bg-card">
        <CardHeader>
          <h2 className="text-lg font-semibold text-foreground">조직 역량 성장 추이</h2>
          <p className="text-sm text-muted-foreground">
            전사 평균 전환 준비도(없으면 적응력 평균 대체). (실제 DB 기준)
          </p>
        </CardHeader>
        <CardContent>
          <TransitionReadinessTrendChart employees={employees} />
        </CardContent>
      </Card>
    </div>
  );
}
