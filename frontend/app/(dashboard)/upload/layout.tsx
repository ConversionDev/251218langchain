"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { usePathname } from "next/navigation";
import BottomNavigation from "@/components/v10/BottomNavigation";
import UploadSidebar from "@/components/v10/upload/UploadSidebar";

const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const POLL_INTERVAL_MS = 2000;

const EMBEDDING_BY_PATH: Record<
  string,
  { entities: string[]; label: string; description: string }
> = {
  "/upload/stadium": {
    entities: ["stadiums"],
    label: "스타디움 임베딩 생성",
    description: "stadiums 테이블만 임베딩 테이블로 동기화합니다.",
  },
  "/upload/team": {
    entities: ["teams"],
    label: "팀 임베딩 생성",
    description: "teams 테이블만 임베딩 테이블로 동기화합니다.",
  },
  "/upload/player": {
    entities: ["players"],
    label: "선수 임베딩 생성",
    description: "players 테이블만 임베딩 테이블로 동기화합니다.",
  },
  "/upload/schedule": {
    entities: ["schedules"],
    label: "스케줄 임베딩 생성",
    description: "schedules 테이블만 임베딩 테이블로 동기화합니다.",
  },
};

const DEFAULT_EMBEDDING = {
  entities: ["players", "teams", "stadiums", "schedules"],
  label: "전체 임베딩 생성",
  description: "관계형 테이블 전체를 임베딩 테이블로 동기화합니다.",
};

export default function UploadLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [embeddingLoading, setEmbeddingLoading] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<{
    status: string;
    error?: string;
  } | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const pollStatus = useCallback(
    async (id: string) => {
      try {
        const res = await fetch(`${backendUrl}/api/soccer/embedding/status/${id}`);
        const data = await res.json();
        if (!res.ok) {
          setJobStatus({ status: "failed", error: data.detail || "상태 조회 실패" });
          return;
        }
        setJobStatus({ status: data.status ?? "unknown", error: data.error });
        if (data.status === "completed" || data.status === "failed") {
          if (pollRef.current) {
            clearInterval(pollRef.current);
            pollRef.current = null;
          }
          setEmbeddingLoading(false);
        }
      } catch {
        setJobStatus({ status: "error", error: "상태 조회 중 오류" });
      }
    },
    []
  );

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  const cancelEmbedding = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
    setEmbeddingLoading(false);
    setJobStatus((prev) => (prev ? { ...prev, status: "cancelled" } : null));
  }, []);

  const pathname = usePathname();
  const embeddingConfig = EMBEDDING_BY_PATH[pathname ?? ""] ?? DEFAULT_EMBEDDING;

  const runEmbedding = useCallback(
    async (entities: string[]) => {
      setEmbeddingLoading(true);
      setJobId(null);
      setJobStatus(null);
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
      try {
        const res = await fetch(`${backendUrl}/api/soccer/embedding`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ entities }),
        });
        const data = await res.json();
        if (!res.ok) {
          setJobStatus({ status: "failed", error: data.detail || "요청 실패" });
          setEmbeddingLoading(false);
          return;
        }
        const id = data.job_id;
        setJobId(id);
        setJobStatus({ status: data.status ?? "waiting" });
        pollRef.current = setInterval(() => pollStatus(id), POLL_INTERVAL_MS);
        await pollStatus(id);
      } catch (e) {
        setJobStatus({
          status: "failed",
          error: e instanceof Error ? e.message : "네트워크 오류",
        });
        setEmbeddingLoading(false);
      }
    },
    [pollStatus]
  );

  return (
    <div className="flex min-h-screen flex-col bg-slate-50 dark:bg-slate-900">
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white px-5 py-4 dark:border-slate-800 dark:bg-slate-900">
        <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100">파일 업로드</h1>
      </header>

      <div className="flex flex-1 flex-col pb-20 md:flex-row">
        <UploadSidebar />
        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          {children}
          <section className="mt-8 border-t border-slate-200 pt-6 dark:border-slate-700">
            <h2 className="mb-2 text-sm font-semibold text-slate-700 dark:text-slate-300">
              임베딩 동기화
            </h2>
            <p className="mb-3 text-xs text-slate-500 dark:text-slate-400">
              {embeddingConfig.description}
            </p>
            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={() => runEmbedding(embeddingConfig.entities)}
                disabled={embeddingLoading}
                className="rounded-lg border border-blue-500 bg-blue-500 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-600 disabled:opacity-50 dark:border-blue-600 dark:bg-blue-600 dark:hover:bg-blue-700"
              >
                {embeddingLoading ? "처리 중..." : embeddingConfig.label}
              </button>
              {embeddingLoading && (
                <button
                  type="button"
                  onClick={cancelEmbedding}
                  className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
                >
                  취소
                </button>
              )}
            </div>
            {jobStatus && (
              <div
                className={`mt-3 rounded-lg border px-3 py-2 text-sm ${
                  jobStatus.status === "completed"
                    ? "border-green-200 bg-green-50 text-green-800 dark:border-green-800 dark:bg-green-950/50 dark:text-green-200"
                    : jobStatus.status === "failed" || jobStatus.status === "error"
                      ? "border-red-200 bg-red-50 text-red-800 dark:border-red-800 dark:bg-red-950/50 dark:text-red-200"
                      : jobStatus.status === "cancelled"
                        ? "border-slate-200 bg-slate-50 text-slate-600 dark:border-slate-600 dark:bg-slate-800/50 dark:text-slate-400"
                        : "border-slate-200 bg-slate-50 text-slate-700 dark:border-slate-700 dark:bg-slate-800/50 dark:text-slate-300"
                }`}
              >
                {jobStatus.status === "completed" ? (
                  <p className="font-medium">동기화 완료</p>
                ) : jobStatus.status === "failed" || jobStatus.status === "error" ? (
                  <p>{jobStatus.error ?? "오류 발생"}</p>
                ) : jobStatus.status === "cancelled" ? (
                  <p className="font-medium">대기/처리 중단함</p>
                ) : (
                  <>
                    {jobId && <p className="text-xs text-slate-500 dark:text-slate-400">job: {jobId}</p>}
                    <p className="font-medium">
                      {jobStatus.status === "waiting" && "대기 중..."}
                      {jobStatus.status === "processing" && "처리 중..."}
                      {!["waiting", "processing", "completed", "failed", "error", "cancelled"].includes(jobStatus.status) && jobStatus.status}
                    </p>
                  </>
                )}
              </div>
            )}
          </section>
        </main>
      </div>

      <BottomNavigation currentPage="upload" />
    </div>
  );
}
