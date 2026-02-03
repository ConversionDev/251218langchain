"use client";

import { useState } from "react";
import SpamDetectionForm from "@/components/v1/SpamDetectionForm";
import SpamResultCard from "@/components/v1/SpamResultCard";
import type {
  EmailMetadata,
  SpamDetectionResponse,
} from "@/lib/types/spam";
import { detectSpam } from "@/lib/api/spamDetection";

export default function SpamDetectionPage() {
  const [result, setResult] = useState<SpamDetectionResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (emailMetadata: EmailMetadata) => {
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await detectSpam(emailMetadata);
      setResult(response);
    } catch (err) {
      const errorMessage =
        err instanceof Error
          ? err.message
          : "스팸 감지 중 오류가 발생했습니다.";
      setError(errorMessage);

      if (err instanceof TypeError && err.message.includes("fetch")) {
        setError(
          `백엔드 서버에 연결할 수 없습니다.\n\n` +
          `확인 사항:\n` +
          `1. 백엔드 서버가 실행 중인지 확인 (http://localhost:8000)\n` +
          `2. CORS 설정이 올바른지 확인\n` +
          `3. 브라우저 콘솔에서 자세한 오류 확인`
        );
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">
          🛡️ 스팸 감지
        </h1>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
          LLaMA와 EXAONE 모델을 활용한 이메일 스팸 감지
        </p>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900">
        <h2 className="mb-4 text-lg font-semibold text-slate-900 dark:text-slate-100">이메일 입력</h2>
        <SpamDetectionForm onSubmit={handleSubmit} isLoading={isLoading} />
      </div>

      {isLoading && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-slate-200 bg-slate-50 py-12 dark:border-slate-800 dark:bg-slate-900">
          <div className="h-12 w-12 animate-spin rounded-full border-4 border-slate-200 border-t-blue-600 dark:border-slate-700 dark:border-t-blue-400" />
          <p className="mt-4 text-sm font-medium text-slate-700 dark:text-slate-300">스팸 감지 분석 중...</p>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">첫 실행 시 모델 로딩으로 10~30초 소요될 수 있습니다.</p>
        </div>
      )}

      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-6 dark:border-red-900 dark:bg-red-950/30">
          <h3 className="mb-2 font-semibold text-red-800 dark:text-red-200">오류 발생</h3>
          <p className="whitespace-pre-line text-sm text-red-700 dark:text-red-300">{error}</p>
        </div>
      )}

      {result && !isLoading && (
        <div className="rounded-xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900">
          <h2 className="mb-4 text-lg font-semibold text-slate-900 dark:text-slate-100">분석 결과</h2>
          <SpamResultCard result={result} />
        </div>
      )}
    </div>
  );
}
