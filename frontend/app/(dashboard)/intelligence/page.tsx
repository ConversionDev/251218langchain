"use client";

import { useMemo, useState, useEffect } from "react";
import Link from "next/link";
import { useStore } from "@/store/useStore";
import { useHydrated } from "@/hooks/use-hydrated";
import { Sparkles, ShieldCheck, ArrowRight, Brain, Info, FileText } from "lucide-react";
import { DNARadarChart } from "@/modules/intelligence/components/DNARadarChart";
import { DNAGrowthChart } from "@/modules/intelligence/components/DNAGrowthChart";
import { DNAGrowthTrajectoryChart } from "@/modules/intelligence/components/DNAGrowthTrajectoryChart";
import { TransitionTrendChart } from "@/modules/intelligence/components/TransitionTrendChart";
import { DNABadge } from "@/modules/shared/components/DNABadge";
import {
  getIntelligenceEmployee,
  getTransitionReadinessSummary,
  getDNAGrowthHistory,
  getDNAGrowthTrajectory,
  getDNAGrowthTrajectoryFromDNA,
} from "@/modules/intelligence/services";
import {
  analyzeBehavioralDataFromMultiple,
  mergeDnaWithWeights,
} from "@/modules/intelligence/services/unstructuredAnalyzer";
import type { IntelligenceEmployee } from "@/modules/intelligence/types";
import { S2_BENCHMARK } from "@/modules/intelligence/types";
import type { BehavioralSourceItem, SuccessDNA } from "@/modules/shared/types";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

/** 데모: 선택된 직원에 대해 회의록 기반 분석이 없을 때 샘플 3건으로 분석 후 스토어 반영 */
const SAMPLE_TRANSCRIPTS = [
  "이번 주 회의에서 팀 방향을 제시하고 결정을 주도했고, 기술 개선안을 제안했습니다. 데이터 분석 결과를 공유하고 팀과 협업해 합의를 이끌었습니다.",
  "새로운 아이디어와 개선안을 논의했고, 변화에 맞춰 유연하게 대응하기로 했습니다. 개발과 설계 부분을 조율하고 지원 요청에 응했습니다.",
  "리더로서 방향을 정하고, 기술 검증과 시스템 개선을 논의했습니다. 창의적인 대안을 함께 검토하고 적응력 있는 전환 계획을 수립했습니다.",
];

/** 회의록 내용 보기 다이얼로그용 목 데이터 — 실제 데이터가 없을 때 항상 표시 */
const MOCK_SOURCE_ITEMS: BehavioralSourceItem[] = SAMPLE_TRANSCRIPTS.map((content, i) => ({
  kind: "meeting",
  title: `회의록 ${i + 1}`,
  content,
}));

const DIMENSION_LABELS_KO: Record<keyof SuccessDNA, string> = {
  leadership: "리더십",
  technical: "기술력",
  creativity: "창의성",
  collaboration: "협업",
  adaptability: "적응력",
};

const defaultEmployee = getIntelligenceEmployee();

export default function IntelligencePage() {
  const hydrated = useHydrated();
  const selectedEmployee = useStore((s) => s.selectedEmployee);
  const updateEmployee = useStore((s) => s.updateEmployee);
  const [highlightedDimension, setHighlightedDimension] = useState<keyof SuccessDNA | null>(null);

  const { employee, summary } = useMemo((): {
    employee: IntelligenceEmployee;
    summary: ReturnType<typeof getTransitionReadinessSummary>;
  } => {
    const base = defaultEmployee;
    const emp: IntelligenceEmployee = hydrated && selectedEmployee
      ? {
          ...selectedEmployee,
          successDna: selectedEmployee.successDna ?? base.successDna ?? undefined,
          behavioralDna: selectedEmployee.behavioralDna,
          behavioralSource: selectedEmployee.behavioralSource,
          behavioralSourceItems: selectedEmployee.behavioralSourceItems,
          ifrsMetrics: selectedEmployee.ifrsMetrics ?? base.ifrsMetrics ?? undefined,
          transitionTrend: base.transitionTrend,
        }
      : base;

    const sum = getTransitionReadinessSummary(emp);
    return { employee: emp, summary: sum };
  }, [selectedEmployee, hydrated]);

  // 선택된 직원에 대해 비정형(회의록) 분석이 없으면 샘플 회의록 3건으로 분석 후 스토어 반영
  useEffect(() => {
    if (!hydrated || !selectedEmployee?.id) return;
    if (selectedEmployee.behavioralDna != null) return;

    const result = analyzeBehavioralDataFromMultiple(SAMPLE_TRANSCRIPTS);
    updateEmployee(selectedEmployee.id, {
      behavioralDna: result.dna,
      behavioralSource: result.source,
      behavioralSourceItems: result.sourceItems,
    });
  }, [hydrated, selectedEmployee?.id, selectedEmployee?.behavioralDna, updateEmployee]);

  // 차트: 기존 DNA와 비정형 분석이 둘 다 있으면 가중 평균 (기존 0.7 + 비정형 0.3), 없으면 있는 쪽만 사용
  const chartDna: SuccessDNA | undefined =
    employee.successDna && employee.behavioralDna
      ? mergeDnaWithWeights(employee.successDna, employee.behavioralDna)
      : (employee.behavioralDna ?? employee.successDna);
  const successDna = employee.successDna;
  const dataSourceLabel = employee.behavioralSource ?? "이력/평가 기반 데이터";
  const strengthLabel = successDna
    ? DIMENSION_LABELS_KO[summary.strengthDimension]
    : "";

  if (!hydrated) {
    return (
      <div className="space-y-8">
        <div className="h-10 w-48 animate-pulse rounded bg-muted" />
        <div className="h-32 animate-pulse rounded-xl bg-muted/50" />
        <div className="h-80 animate-pulse rounded-xl bg-muted/50" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <div className="mb-1.5 flex items-center gap-2 text-muted-foreground">
          <Brain className="h-3.5 w-3.5 shrink-0" />
          <span className="text-xs">Talent Intelligence: AI 기반 비정형 행동 패턴 및 역량 추출 엔진</span>
        </div>
        <h1 className="text-2xl font-bold text-foreground">Talent Intelligence</h1>
        <p className="mt-1 text-muted-foreground">
          Success DNA 역량과 IFRS S2 전환 준비도 분석
        </p>
      </div>

      {/* AI 전환 가능성 리포트 요약 */}
      <section className="rounded-xl border border-border bg-card p-6 shadow-sm">
        <div className="flex items-center gap-2 text-primary">
          <Sparkles className="h-5 w-5" />
          <h2 className="text-lg font-semibold">AI가 분석한 전환 가능성 리포트</h2>
        </div>
        <div className="mt-4 space-y-4">
          <div>
            <h3 className="text-sm font-medium text-muted-foreground">현재 상태 분석</h3>
            <p className="mt-1 text-foreground leading-relaxed">{summary.currentState}</p>
          </div>
          <div>
            <h3 className="text-sm font-medium text-muted-foreground">전환(Transition) 제언</h3>
            <p className="mt-1 text-foreground leading-relaxed">{summary.transitionRecommendation}</p>
          </div>
          <div>
            <h3 className="text-sm font-medium text-muted-foreground">리스크 알림</h3>
            <p className="mt-1 text-foreground leading-relaxed">{summary.riskNotice}</p>
          </div>
        </div>
        <div className="mt-6 flex flex-wrap items-center gap-4">
          <div className="rounded-lg bg-primary/10 px-4 py-2">
            <span className="text-sm text-muted-foreground">전환 가능성</span>
            <p className="text-2xl font-bold text-primary">{summary.transitionProbability}%</p>
          </div>
          {strengthLabel && (
            <div className="rounded-lg bg-muted/50 px-4 py-2">
              <span className="text-sm text-muted-foreground">핵심 강점 역량</span>
              <p className="font-medium text-foreground">{strengthLabel}</p>
            </div>
          )}
          {successDna && (
            <DNABadge dna={successDna} showTitle={true} />
          )}
        </div>
      </section>

      {/* Success DNA 레이더 차트 + DNA 성장 이력 */}
      <section className="rounded-xl border border-border bg-card p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-foreground">Success DNA 역량 비교</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          본인 vs 전사 고성과자 평균 · 1년 전 대비 성장 서사
        </p>
        <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
          <span className="flex items-center gap-1.5">
            <Info className="h-3.5 w-3.5 shrink-0" aria-hidden />
            Source: {dataSourceLabel}
          </span>
          <Dialog>
            <DialogTrigger asChild>
              <button
                type="button"
                className="inline-flex items-center gap-1 rounded hover:underline focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <FileText className="h-3.5 w-3.5 shrink-0" aria-hidden />
                회의록 내용 보기
              </button>
            </DialogTrigger>
            <DialogContent className="flex max-h-[85vh] max-w-2xl flex-col overflow-hidden">
              <DialogHeader>
                <DialogTitle className="text-base">분석에 사용된 출처 원문</DialogTitle>
              </DialogHeader>
              <div className="flex-1 space-y-4 overflow-y-auto pr-2">
                {(employee.behavioralSourceItems?.length
                  ? employee.behavioralSourceItems
                  : MOCK_SOURCE_ITEMS
                ).map((item, idx) => (
                  <div
                    key={idx}
                    className="rounded-lg border border-border bg-muted/30 p-3"
                  >
                    <p className="mb-2 text-sm font-medium text-foreground">
                      {item.title ?? `${item.kind} ${idx + 1}`}
                    </p>
                    <pre className="whitespace-pre-wrap break-words font-sans text-xs text-muted-foreground">
                      {item.content}
                    </pre>
                  </div>
                ))}
              </div>
            </DialogContent>
          </Dialog>
        </div>
        {chartDna && (
          <div className="mt-6 space-y-8">
            <div className="grid items-stretch gap-8 lg:grid-cols-2">
              <div>
                <h3 className="text-sm font-medium text-muted-foreground">역량 레이더</h3>
                <DNARadarChart
                  data={chartDna}
                  trainingHours={employee.trainingHours ?? undefined}
                  onDimensionClick={(key) =>
                    setHighlightedDimension((prev) => (prev === key ? null : key))
                  }
                  highlightedDimension={highlightedDimension}
                />
              </div>
              <div className="flex min-h-[320px] min-w-0 flex-1 flex-col">
                <h3 className="text-sm font-medium text-muted-foreground">역량별 성장 궤적 (지난 1년)</h3>
                <DNAGrowthTrajectoryChart
                  data={(() => {
                    const empWithChartDna = { ...employee, successDna: chartDna };
                    const t = getDNAGrowthTrajectory(empWithChartDna);
                    return t.length > 0 ? t : getDNAGrowthTrajectoryFromDNA(chartDna);
                  })()}
                  highlightDimension={highlightedDimension}
                  onHighlightChange={setHighlightedDimension}
                />
              </div>
            </div>
            <div>
              <h3 className="text-sm font-medium text-muted-foreground">DNA 성장 이력 (1년 전 → 현재)</h3>
              <DNAGrowthChart data={getDNAGrowthHistory({ ...employee, successDna: chartDna })} />
            </div>
          </div>
        )}
      </section>

      {/* 전환 준비도 추이 */}
      <section className="rounded-xl border border-border bg-card p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-foreground">전환 준비도 추이 (Transition Trend)</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          최근 12개월 전환 준비도 변화. 목표선(S2 Benchmark)은 해당 산업으로 전환하기 위한 최소 준비 점수이며, 이 위에 있으면 전환 준비 완료로 간주합니다.
        </p>
        {employee.ifrsMetrics && (
          <p className="mt-2 text-sm text-muted-foreground">
            현재 역량 갭(Skill Gap): <strong className="text-foreground">{employee.ifrsMetrics.skillGap}점</strong>
            {employee.ifrsMetrics.transitionReadyScore < S2_BENCHMARK ? (
              <span className="ml-2">
                — 목표까지 <strong className="text-primary">{S2_BENCHMARK - employee.ifrsMetrics.transitionReadyScore}점</strong> 남음
              </span>
            ) : (
              <span className="ml-2 text-green-600 dark:text-green-400">— S2 목표 달성</span>
            )}
          </p>
        )}
        {employee.transitionTrend?.length > 0 && (
          <div className="mt-6">
            <TransitionTrendChart
              data={employee.transitionTrend}
              goalScore={S2_BENCHMARK}
            />
          </div>
        )}
      </section>

      {/* 블록체인 안내 + 검증하기 */}
      <section className="rounded-xl border border-border bg-card p-6 shadow-sm">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-3">
            <ShieldCheck className="h-5 w-5 shrink-0 text-primary" />
            <p className="text-sm text-muted-foreground">
              이 분석 결과는 블록체인에 기록되어 위변조로부터 보호됩니다.
            </p>
          </div>
          <Link
            href={`/credential?id=${employee.id}`}
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            검증하기 (Verify)
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>
    </div>
  );
}
