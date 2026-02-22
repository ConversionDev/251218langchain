"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useStore } from "@/store/useStore";
import { useHydrated } from "@/hooks/use-hydrated";
import {
  Brain,
  Info,
  FileText,
  UserX,
  ShieldCheck,
  ArrowRight,
  Target,
} from "lucide-react";
import { DNARadarChart } from "@/modules/intelligence/components/DNARadarChart";
import { DNAGrowthChart } from "@/modules/intelligence/components/DNAGrowthChart";
import { DNAGrowthTrajectoryChart } from "@/modules/intelligence/components/DNAGrowthTrajectoryChart";
import { DNABadge } from "@/modules/shared/components/DNABadge";
import {
  toIntelligenceEmployee,
  getCapabilitySummary,
  getDNAGrowthHistory,
  getDNAGrowthTrajectory,
  getTransitionReadinessSummary,
  buildTransitionAnalysisPrompt,
  parseTransitionAnalysisResponse,
} from "@/modules/intelligence/services";
import { sendChatMessageStream } from "@/modules/chat/services";
import { fetchEmployeesPaginated } from "@/modules/core/services";
import { Button } from "@/components/ui/button";
import { mergeDnaWithWeights } from "@/modules/intelligence/services/unstructuredAnalyzer";
import type { IntelligenceEmployee } from "@/modules/intelligence/types";
import type { Employee, SuccessDNA } from "@/modules/shared/types";
import { getAverageSuccessDna } from "@/modules/shared/utils/employeeAggregates";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

export default function IntelligencePage() {
  const hydrated = useHydrated();
  const selectedEmployee = useStore((s) => s.selectedEmployee);
  const [highlightedDimension, setHighlightedDimension] = useState<keyof SuccessDNA | null>(null);
  const [regularAverageDna, setRegularAverageDna] = useState<SuccessDNA | undefined>(undefined);
  const [aiTransitionNarrative, setAiTransitionNarrative] = useState<string>("");
  const [aiTransitionLoading, setAiTransitionLoading] = useState(false);
  const [aiTransitionError, setAiTransitionError] = useState<string | null>(null);

  useEffect(() => {
    setAiTransitionNarrative("");
    setAiTransitionError(null);
  }, [selectedEmployee?.id]);

  useEffect(() => {
    if (!hydrated) return;
    fetchEmployeesPaginated({ page: 1, pageSize: 100, employmentType: "regular" })
      .then(({ items }) => {
        const avg = getAverageSuccessDna(items ?? []);
        setRegularAverageDna(avg ?? undefined);
      })
      .catch(() => setRegularAverageDna(undefined));
  }, [hydrated]);

  const employee = useMemo((): IntelligenceEmployee | null => {
    if (!hydrated || !selectedEmployee) return null;
    return toIntelligenceEmployee(selectedEmployee);
  }, [selectedEmployee, hydrated]);

  const capabilitySummary = useMemo(
    () => (employee?.successDna ? getCapabilitySummary(employee.successDna) : null),
    [employee?.successDna]
  );

  const requestTransitionAnalysis = () => {
    if (!employee) return;
    const { message, system_prompt } = buildTransitionAnalysisPrompt(employee);
    setAiTransitionLoading(true);
    setAiTransitionError(null);
    setAiTransitionNarrative("");
    sendChatMessageStream(
      { message, system_prompt, use_rag: true },
      {
        onChunk: (content) => setAiTransitionNarrative((prev) => prev + content),
        onDone: () => setAiTransitionLoading(false),
        onError: (err) => {
          setAiTransitionError(err);
          setAiTransitionLoading(false);
        },
      }
    );
  };

  const chartDna: SuccessDNA | undefined =
    (employee &&
      (employee.successDna && employee.behavioralDna
        ? mergeDnaWithWeights(employee.successDna, employee.behavioralDna)
        : employee.behavioralDna ?? employee.successDna)) ?? undefined;
  const dataSourceLabel = employee?.behavioralSource ?? "이력/평가 기반 데이터";

  if (!hydrated) {
    return (
      <div className="space-y-8">
        <div className="h-10 w-48 animate-pulse rounded bg-muted" />
        <div className="h-32 animate-pulse rounded-xl bg-muted/50" />
        <div className="h-80 animate-pulse rounded-xl bg-muted/50" />
      </div>
    );
  }

  if (hydrated && !employee) {
    return (
      <div className="space-y-8">
        <div>
          <div className="mb-1.5 flex items-center gap-2 text-muted-foreground">
            <Brain className="h-3.5 w-3.5 shrink-0" />
            <span className="text-xs">AI 기반 역량 추출 및 진단</span>
          </div>
          <h1 className="text-2xl font-bold text-foreground">역량 진단</h1>
          <p className="mt-1 text-muted-foreground">5대 역량 진단 및 직무 전환 분석</p>
        </div>
        <section className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border bg-muted/30 py-16 text-center">
          <UserX className="h-12 w-12 text-muted-foreground" />
          <p className="mt-4 text-sm font-medium text-foreground">분석할 직원을 선택해 주세요</p>
          <p className="mt-1 text-sm text-muted-foreground">
            <Link href="/core/employees" className="underline hover:no-underline">
              기존 직원
            </Link>
            에서 직원을 선택하면 이곳에서 역량 진단을 확인할 수 있습니다.
          </p>
        </section>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* 헤더: 페이지 타이틀 + 선택 직원 + 데이터 출처 배지 */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="mb-1.5 flex items-center gap-2 text-muted-foreground">
            <Brain className="h-3.5 w-3.5 shrink-0" />
            <span className="text-xs">역량 진단</span>
          </div>
          <h1 className="text-2xl font-bold text-foreground">역량 진단</h1>
          <p className="mt-1 text-muted-foreground">
            {employee?.name ?? "이름 없음"}
            {employee?.department ? ` · ${employee.department}` : ""}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="inline-flex items-center gap-1.5 rounded-md border border-border bg-muted/50 px-2.5 py-1 text-xs text-muted-foreground">
            <Info className="h-3.5 w-3.5 shrink-0" aria-hidden />
            {dataSourceLabel}
          </span>
          {employee?.successDna && <DNABadge dna={employee.successDna} showTitle={true} />}
        </div>
      </div>

      {/* 역량 진단: 요약 카드 3개 */}
      {capabilitySummary && (
        <section className="grid gap-4 sm:grid-cols-3">
          <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              종합 점수
            </p>
            <p className="mt-1 text-2xl font-bold text-foreground">
              {capabilitySummary.overallScore}
              <span className="ml-0.5 text-sm font-normal text-muted-foreground">/ 100</span>
            </p>
          </div>
          <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              강점 역량 (Top 2)
            </p>
            <p className="mt-1 font-medium text-foreground">
              {capabilitySummary.topDimensions
                .map((d) => `${d.label} ${d.score}`)
                .join(", ")}
            </p>
          </div>
          <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              보완 역량
            </p>
            <p className="mt-1 font-medium text-foreground">
              {capabilitySummary.improveDimension
                ? `${capabilitySummary.improveDimension.label} ${capabilitySummary.improveDimension.score}`
                : "—"}
            </p>
          </div>
        </section>
      )}

      {/* 2열: 레이더 | 평가 근거 패널 */}
      <section className="rounded-xl border border-border bg-card p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-foreground">Success DNA 역량 비교</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          본인 vs 조직 평균 (실제 DB 데이터 기준)
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
                {(employee?.behavioralSourceItems ?? []).length === 0 ? (
                  <p className="py-8 text-center text-sm text-muted-foreground">
                    분석된 회의록이 없습니다.
                  </p>
                ) : (
                  (employee?.behavioralSourceItems ?? []).map((item, idx) => (
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
                  ))
                )}
              </div>
            </DialogContent>
          </Dialog>
        </div>
        <div className="mt-6 grid gap-8 lg:grid-cols-2">
          <div>
            <h3 className="text-sm font-medium text-muted-foreground">역량 레이더</h3>
            {chartDna && (
              <DNARadarChart
                data={chartDna}
                highPerformerAverage={regularAverageDna}
                trainingHours={employee?.trainingHours ?? undefined}
                onDimensionClick={(key) =>
                  setHighlightedDimension((prev) => (prev === key ? null : key))
                }
                highlightedDimension={highlightedDimension}
              />
            )}
          </div>
          <div>
            <h3 className="text-sm font-medium text-muted-foreground">평가 근거</h3>
            <div className="mt-2 min-h-[200px] rounded-lg border border-border bg-muted/20 p-4">
              {employee?.successDnaReason?.trim() ? (
                <p className="whitespace-pre-wrap text-sm text-foreground leading-relaxed">
                  {employee.successDnaReason}
                </p>
              ) : (
                <p className="text-sm text-muted-foreground">
                  평가 근거 데이터가 없습니다. AI 분석을 실행하거나 수동으로 입력해 주세요.
                </p>
              )}
            </div>
          </div>
        </div>
        {/* 성장 이력/궤적: 데이터 있을 때만 표시 */}
        {chartDna && (
          <>
            {employee && getDNAGrowthTrajectory({ ...employee, successDna: chartDna } as Employee).length > 0 && (
              <div className="mt-8 flex min-h-[320px] min-w-0 flex-1 flex-col">
                <h3 className="text-sm font-medium text-muted-foreground">역량별 성장 궤적</h3>
                <DNAGrowthTrajectoryChart
                  data={getDNAGrowthTrajectory({ ...employee, successDna: chartDna })}
                  highlightDimension={highlightedDimension}
                  onHighlightChange={setHighlightedDimension}
                />
              </div>
            )}
            {employee && getDNAGrowthHistory({ ...employee, successDna: chartDna } as Employee).length > 0 && (
              <div className="mt-8">
                <h3 className="text-sm font-medium text-muted-foreground">DNA 성장 이력</h3>
                <DNAGrowthChart
                  data={getDNAGrowthHistory({ ...employee, successDna: chartDna })}
                />
              </div>
            )}
          </>
        )}
      </section>

      {/* 직무 전환 분석: 숫자는 데이터 기반, 문구는 엑사원 생성 */}
      <section className="rounded-xl border border-border bg-card p-6 shadow-sm">
        <div className="flex items-center gap-2 text-muted-foreground">
          <Target className="h-5 w-5 shrink-0" />
          <h2 className="text-lg font-semibold text-foreground">직무 전환 분석</h2>
        </div>
        <p className="mt-1 text-sm text-muted-foreground">
          전환 가능성·지표는 DB 데이터로 산출하고, 아래 분석 문구는 AI가 직원 데이터를 바탕으로 생성합니다. 「직무 전환 분석 요청」을 누르면 직원별 맞춤 문구가 생성됩니다.
        </p>
        {(() => {
          if (!employee) return null;
          const summary = getTransitionReadinessSummary(employee);
          const parsed =
            aiTransitionNarrative && !aiTransitionLoading
              ? parseTransitionAnalysisResponse(aiTransitionNarrative)
              : null;
          const showAiBlocks =
            parsed && (parsed.transitionRecommendation || parsed.riskNotice || parsed.currentState);
          const showStreaming = aiTransitionLoading && aiTransitionNarrative;
          return (
            <div className="mt-4 space-y-4">
              <div className="flex flex-wrap items-center gap-4">
                <div className="rounded-lg border border-border bg-muted/30 px-4 py-3">
                  <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">전환 가능성</p>
                  <p className="mt-0.5 text-2xl font-bold text-foreground">{summary.transitionProbability}%</p>
                </div>
                {summary.transitionReadyScore != null && (
                  <div className="rounded-lg border border-border bg-muted/30 px-4 py-3">
                    <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">전환 준비도 (IFRS S2)</p>
                    <p className="mt-0.5 text-2xl font-bold text-foreground">{summary.transitionReadyScore}점</p>
                  </div>
                )}
                {summary.skillGap != null && (
                  <div className="rounded-lg border border-border bg-muted/30 px-4 py-3">
                    <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">스킬 갭</p>
                    <p className="mt-0.5 text-2xl font-bold text-foreground">{summary.skillGap}점</p>
                  </div>
                )}
              </div>
              {aiTransitionError && (
                <p className="text-sm text-destructive">{aiTransitionError}</p>
              )}
              {aiTransitionLoading && (
                <p className="text-sm text-muted-foreground">AI 직무 전환 분석 중…</p>
              )}
              <div className="grid gap-3 sm:grid-cols-1">
                <div className="rounded-lg border border-border bg-muted/20 p-4">
                  <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">현재 상태</p>
                  <p className="mt-1.5 whitespace-pre-wrap text-sm text-foreground">
                    {showStreaming
                      ? aiTransitionNarrative
                      : showAiBlocks
                        ? parsed!.currentState
                        : summary.currentState}
                  </p>
                </div>
                <div className="rounded-lg border border-border bg-muted/20 p-4">
                  <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">전환 제언</p>
                  <p className="mt-1.5 whitespace-pre-wrap text-sm text-foreground">
                    {showStreaming ? "" : showAiBlocks ? parsed!.transitionRecommendation : summary.transitionRecommendation}
                  </p>
                </div>
                <div className="rounded-lg border border-border bg-muted/20 p-4">
                  <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">배치 시 고려사항</p>
                  <p className="mt-1.5 whitespace-pre-wrap text-sm text-foreground">
                    {showStreaming ? "" : showAiBlocks ? parsed!.riskNotice : summary.riskNotice}
                  </p>
                </div>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={requestTransitionAnalysis}
                  disabled={aiTransitionLoading}
                >
                  {aiTransitionNarrative && !aiTransitionLoading ? "직무 전환 다시 분석" : "직무 전환 분석 요청"}
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                시계열 전환 준비도·직무별 목표 역량 데이터가 쌓이면 추이 차트와 매핑 분석이 확장됩니다.
              </p>
            </div>
          );
        })()}
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
            href={`/credential?id=${employee?.id ?? ""}`}
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            검증하기
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>
    </div>
  );
}
