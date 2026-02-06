"use client";

import { useState, useEffect } from "react";
import { toast } from "sonner";
import { Database, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { startEmbeddingJob, getEmbeddingJobStatus } from "../services";
import type { EmbeddingJobStatus } from "../types";
import type { SoccerDataType } from "../services";

const POLL_INTERVAL_MS = 2000;
const MAX_POLL_ATTEMPTS = 120;
const ESTIMATED_MINUTES = 5;
const ENTITY_LABELS: Record<string, string> = {
  players: "선수",
  teams: "팀",
  schedules: "일정",
  stadiums: "경기장",
};

const ENTITY_OPTIONS: { value: SoccerDataType; label: string }[] = [
  { value: "stadiums", label: "경기장만" },
  { value: "teams", label: "팀만" },
  { value: "players", label: "선수만" },
  { value: "schedules", label: "일정만" },
];

function getErrorMessage(err: unknown): string {
  if (err instanceof Error) return err.message;
  if (typeof err === "string") return err;
  return "실패";
}

function formatElapsed(ms: number): string {
  const sec = Math.floor(ms / 1000);
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  if (m > 0) return `${m}분 ${s}초`;
  return `${s}초`;
}

function formatResultsSummary(result: EmbeddingJobStatus["result"]): string | null {
  const results = result as Record<string, { processed?: number; failed?: number }> | undefined;
  if (!results || typeof results !== "object") return null;
  const parts = Object.entries(results).map(([key, val]) => {
    const label = ENTITY_LABELS[key] ?? key;
    const p = typeof val?.processed === "number" ? val.processed : 0;
    const f = typeof val?.failed === "number" ? val.failed : 0;
    if (p === 0 && f === 0) return `${label} 0건`;
    return `${label} ${p}건${f > 0 ? ` (실패 ${f})` : ""}`;
  });
  return parts.length ? parts.join(", ") : null;
}

export function EmbeddingSyncSection() {
  const [loading, setLoading] = useState(false);
  const [jobStatus, setJobStatus] = useState<EmbeddingJobStatus | null>(null);
  const [elapsedMs, setElapsedMs] = useState(0);
  const [startedAt, setStartedAt] = useState<number | null>(null);

  useEffect(() => {
    if (!loading || startedAt == null) return;
    const update = () => setElapsedMs(Date.now() - startedAt);
    update();
    const id = setInterval(update, 1000);
    return () => clearInterval(id);
  }, [loading, startedAt]);

  const runSync = async (entities: SoccerDataType[] | undefined) => {
    const startTime = Date.now();
    setLoading(true);
    setJobStatus(null);
    setElapsedMs(0);
    setStartedAt(startTime);
    try {
      const { job_id } = await startEmbeddingJob(entities);
      setJobStatus({ status: "processing" });
      const scope = entities?.length === 1 ? ENTITY_LABELS[entities[0]] : "전체";
      toast.info(`${scope} 임베딩 동기화를 시작했습니다.`);

      for (let i = 0; i < MAX_POLL_ATTEMPTS; i++) {
        await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS));
        const status = await getEmbeddingJobStatus(job_id);
        setJobStatus(status);
        if (status.status === "completed") {
          setElapsedMs(Date.now() - startTime);
          toast.success("임베딩 동기화가 완료되었습니다.");
          break;
        }
        if (status.status === "failed") {
          setElapsedMs(Date.now() - startTime);
          const msg = (status.result?.error as string) || status.error || "알 수 없는 오류";
          toast.error(`임베딩 동기화 실패: ${msg}`);
          break;
        }
      }
    } catch (err) {
      const msg = getErrorMessage(err);
      setJobStatus({ status: "failed", error: msg });
      toast.error(`임베딩 동기화 실패: ${msg}`);
    } finally {
      setLoading(false);
      setStartedAt(null);
    }
  };

  const isProcessing =
    jobStatus?.status === "processing" ||
    (loading && jobStatus?.status !== "completed" && jobStatus?.status !== "failed");
  const summary = jobStatus?.status === "completed" ? formatResultsSummary(jobStatus.result) : null;

  return (
    <section className="rounded-xl border border-border bg-card p-4 shadow-sm">
      <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
        <Database className="h-4 w-4" />
        임베딩 동기화
      </div>
      <p className="mt-1 text-xs text-muted-foreground">
        이미 테이블에 데이터가 있으면 항목을 선택해 해당 테이블만 임베딩할 수 있습니다. JSONL을 다시 올리지 않아도 됩니다.
      </p>

      {(!jobStatus || isProcessing) && (
        <p className="mt-2 text-xs text-muted-foreground">
          예상 소요 시간: 선택한 엔티티 수에 따라 약 1~{ESTIMATED_MINUTES}분 (데이터량에 따라 달라질 수 있습니다).
        </p>
      )}

      <div className="mt-3 flex flex-wrap gap-2">
        {ENTITY_OPTIONS.map(({ value, label }) => (
          <Button
            key={value}
            type="button"
            variant="outline"
            disabled={loading}
            onClick={() => runSync([value])}
            className="gap-2"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : null}
            {label}
          </Button>
        ))}
        <Button
          type="button"
          variant="default"
          disabled={loading}
          onClick={() => runSync(undefined)}
          className="gap-2"
        >
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : null}
          전체 동기화
        </Button>
      </div>

      {(loading || jobStatus) && (
        <div className="mt-4 space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">
              {isProcessing ? "진행 중" : jobStatus?.status === "completed" ? "완료" : jobStatus?.status === "failed" ? "실패" : jobStatus?.status}
            </span>
            {elapsedMs > 0 && (
              <span className="tabular-nums text-muted-foreground">
                경과 {formatElapsed(elapsedMs)}
              </span>
            )}
          </div>
          {isProcessing && (
            <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
              <div className="h-full animate-pulse rounded-full bg-primary/70" style={{ width: "40%" }} />
            </div>
          )}
          {jobStatus?.status === "completed" && (
            <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
              <div className="h-full rounded-full bg-green-500 dark:bg-green-600" style={{ width: "100%" }} />
            </div>
          )}
          {summary && <p className="text-xs text-muted-foreground">{summary}</p>}
          {(jobStatus?.error ?? (jobStatus?.result?.error as string | undefined)) && (
            <p className="text-xs text-destructive">
              {jobStatus?.error ?? (jobStatus?.result?.error as string)}
            </p>
          )}
        </div>
      )}
    </section>
  );
}
