"use client";

import { useMemo, useState, useCallback } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { FileDown, Presentation, Users, ArrowRight, LineChart } from "lucide-react";
import { useStore } from "@/store/useStore";
import { useHydrated } from "@/hooks/use-hydrated";
import { ValueSummaryCard } from "@/modules/performance/components/ValueSummaryCard";
import { ImpactAnalysisChart } from "@/modules/performance/components/ImpactAnalysisChart";
import { DisclosureSection } from "@/modules/performance/components/DisclosureSection";
import { VerificationStatusIndicator } from "@/modules/performance/components/VerificationStatusIndicator";
import { ReportPreviewModal } from "@/modules/performance/components/ReportPreviewModal";
import { SimulatorSection } from "@/modules/performance/components/SimulatorSection";
import { DNABadge } from "@/modules/shared/components/DNABadge";
import type { PerformanceMetrics } from "@/modules/performance/types";
import type { SuccessDNA } from "@/modules/shared/types";
import {
  getPerformanceMetrics,
  getImpactChartData,
  getDisclosureSummary,
  getAggregatePerformanceMetrics,
  getAggregateImpactChartData,
  getAggregateDisclosureSummary,
} from "@/modules/performance/services";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

export default function PerformancePage() {
  const hydrated = useHydrated();
  const selectedEmployee = useStore((s) => s.selectedEmployee);
  const employees = useStore((s) => s.employees);
  const isDisclosureMode = useStore((s) => s.isDisclosureMode);
  const [boardReportOpen, setBoardReportOpen] = useState(false);
  const [simulatedMetrics, setSimulatedMetrics] = useState<PerformanceMetrics | null>(null);
  const handleSimulationMetrics = useCallback((metrics: PerformanceMetrics | null) => {
    setSimulatedMetrics(metrics);
  }, []);

  const isAggregate = !selectedEmployee && employees.length > 0;
  const metrics = useMemo(
    () =>
      selectedEmployee
        ? getPerformanceMetrics(selectedEmployee)
        : getAggregatePerformanceMetrics(employees),
    [selectedEmployee, employees]
  );
  const chartData = useMemo(
    () =>
      selectedEmployee
        ? getImpactChartData(selectedEmployee)
        : getAggregateImpactChartData(employees),
    [selectedEmployee, employees]
  );
  const disclosureSummary = useMemo(
    () =>
      selectedEmployee
        ? getDisclosureSummary(selectedEmployee)
        : getAggregateDisclosureSummary(employees),
    [selectedEmployee, employees]
  );

  /** 전체 평균 시뮬레이터용 평균 DNA */
  const aggregateDna = useMemo((): SuccessDNA | undefined => {
    if (employees.length === 0) return undefined;
    const sum = {
      leadership: 0,
      technical: 0,
      creativity: 0,
      collaboration: 0,
      adaptability: 0,
    };
    let count = 0;
    employees.forEach((e) => {
      if (e.successDna) {
        (Object.keys(sum) as (keyof SuccessDNA)[]).forEach(
          (k) => (sum[k] += e.successDna![k] ?? 0)
        );
        count++;
      }
    });
    if (count === 0) return undefined;
    return {
      leadership: Math.round(sum.leadership / count),
      technical: Math.round(sum.technical / count),
      creativity: Math.round(sum.creativity / count),
      collaboration: Math.round(sum.collaboration / count),
      adaptability: Math.round(sum.adaptability / count),
    };
  }, [employees]);

  if (!hydrated) {
    return (
      <div className="report-grid-bg min-h-[60vh] rounded-xl p-8">
        <div className="h-10 w-48 animate-pulse rounded bg-muted" />
        <div className="mt-6 grid gap-4 md:grid-cols-3">
          <div className="h-28 animate-pulse rounded-xl bg-muted/50" />
          <div className="h-28 animate-pulse rounded-xl bg-muted/50" />
          <div className="h-28 animate-pulse rounded-xl bg-muted/50" />
        </div>
      </div>
    );
  }

  if (!selectedEmployee && employees.length === 0) {
    return (
      <div className="report-grid-bg flex min-h-[60vh] items-center justify-center rounded-xl p-8">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, ease: "easeOut" }}
          className="flex max-w-md flex-col items-center rounded-2xl border border-border bg-card p-10 text-center shadow-sm"
        >
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-primary/10 text-primary">
            <Users className="h-7 w-7" />
          </div>
          <h2 className="mt-4 text-lg font-semibold text-foreground">
            직원을 선택해주세요
          </h2>
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
            인적 자본 가치 분석을 시작하려면 직원을 선택해주세요.
            <br />
            Core에서 직원을 선택한 뒤 이 페이지에서 리포트를 확인할 수 있습니다.
          </p>
          <Link href="/core" className="mt-6">
            <Button className="inline-flex items-center gap-2">
              <Users className="h-4 w-4" />
              Core에서 직원 선택하기
              <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
        </motion.div>
      </div>
    );
  }

  const reportTitle = isAggregate ? "Performance 리포트 (전체 임직원 평균)" : "Performance 리포트";
  const reportSubtitle = isAggregate
    ? `${employees.length}명 기준 평균 인적 자본 가치 · 개인 분석은 Core에서 직원 선택`
    : "Core · Intelligence · Credential 통합 인적 자본 가치";
  const summaryName = isAggregate ? `전체 임직원 (${employees.length}명 평균)` : selectedEmployee!.name;

  return (
    <div
      className={`report-grid-bg min-h-[60vh] rounded-xl p-8 ${isDisclosureMode ? "report-grid-bg-official" : ""}`}
    >
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }}
        className="relative z-10 space-y-8"
      >
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="mb-1.5 flex items-center gap-2 text-muted-foreground">
              <LineChart className="h-3.5 w-3.5 shrink-0" />
              <span className="text-xs">Total Performance: 정형·비정형 데이터 통합 성과 리포트</span>
            </div>
            <h1 className="text-2xl font-bold text-foreground">{reportTitle}</h1>
            <p className="mt-1 text-muted-foreground">{reportSubtitle}</p>
            {selectedEmployee && (
              <div className="mt-2">
                <DNABadge dna={selectedEmployee.successDna} showTitle={true} />
              </div>
            )}
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              className="inline-flex items-center gap-2"
              onClick={() => {
                const payload = {
                  reportTitle,
                  summaryName,
                  metrics,
                  chartData,
                  disclosureSummary,
                };
                localStorage.setItem("performance-report-payload", JSON.stringify(payload));
                window.open("/performance/report", "_blank", "noopener,noreferrer");
              }}
              title="새 창에서 리포트 확인 후 PDF 저장"
            >
              <FileDown className="h-4 w-4" />
              공시 리포트 다운로드 (PDF)
            </Button>
            <Button
              variant="outline"
              className="inline-flex items-center gap-2"
              onClick={() => {
                if (!isDisclosureMode) {
                  toast.info("이사회 보고 모드를 사용하려면 상단에서 공시 모드를 먼저 켜 주세요.");
                  return;
                }
                setBoardReportOpen(true);
              }}
              title="전체 화면 발표 모드 (공시 모드 켜야 사용 가능, Esc로 닫기)"
            >
              <Presentation className="h-4 w-4" />
              이사회 보고 모드
            </Button>
          </div>
        </div>

        <ReportPreviewModal
          open={boardReportOpen}
          onOpenChange={setBoardReportOpen}
          reportTitle={reportTitle}
          summaryName={summaryName}
          metrics={metrics}
          chartData={chartData}
          disclosureSummary={disclosureSummary}
          fullscreen
        />

        <VerificationStatusIndicator employee={selectedEmployee} />

        <ValueSummaryCard
          employeeName={summaryName}
          metrics={metrics}
          displayMetrics={simulatedMetrics ?? undefined}
          isDisclosureMode={isDisclosureMode}
        />

        <SimulatorSection
          employee={selectedEmployee}
          fallbackDna={aggregateDna}
          onMetricsChange={handleSimulationMetrics}
        />

        <section className="rounded-xl border border-border bg-card p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-foreground">
            {isDisclosureMode ? "과거 성과 및 미래 가치 추정 (IFRS S1/S2)" : "성과·미래 가치 분석"}
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {isDisclosureMode
              ? "과거 성과 지표(막대) 및 AI 기반 미래 가치 추정(라인)"
              : "과거 성과(막대)와 AI 예측 미래 가치(라인)"}
          </p>
          <div className="mt-6">
            <ImpactAnalysisChart data={chartData} />
          </div>
        </section>

        <DisclosureSection summary={disclosureSummary} />
      </motion.div>
    </div>
  );
}
