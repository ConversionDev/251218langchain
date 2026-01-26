"use client";

import type { ExaoneResult, LLaMAResult } from "@/lib/types/spam";

interface ModelResultViewProps {
  title: string;
  result: LLaMAResult | ExaoneResult;
  type: "llama" | "exaone";
}

export default function ModelResultView({
  title,
  result,
  type,
}: ModelResultViewProps) {
  if (type === "llama") {
    const llamaResult = result as LLaMAResult;
    return (
      <div className="bg-[rgba(255,255,255,0.05)] border border-[rgba(102,126,234,0.3)] rounded-xl p-4">
        <h4 className="m-0 mb-4 text-white text-base font-semibold">{title}</h4>
        <div className="flex flex-col gap-3">
          <div className="flex justify-between items-center py-2 border-b border-[rgba(255,255,255,0.1)] last:border-b-0">
            <span className="text-sm text-[#a0a0a0]">스팸 확률:</span>
            <span className="text-sm text-[#e0e0e0] font-medium">
              {(llamaResult.spam_prob * 100).toFixed(2)}%
            </span>
          </div>
          <div className="flex justify-between items-center py-2 border-b border-[rgba(255,255,255,0.1)] last:border-b-0">
            <span className="text-sm text-[#a0a0a0]">신뢰도:</span>
            <span className={`px-3 py-1 rounded-lg text-sm font-semibold ${
              llamaResult.confidence === "high"
                ? "bg-[rgba(74,222,128,0.2)] text-[#4ade80]"
                : llamaResult.confidence === "medium"
                  ? "bg-[rgba(251,191,36,0.2)] text-[#fbbf24]"
                  : "bg-[rgba(248,113,113,0.2)] text-[#f87171]"
            }`}>
              {llamaResult.confidence}
            </span>
          </div>
          <div className="flex justify-between items-center py-2 border-b border-[rgba(255,255,255,0.1)] last:border-b-0">
            <span className="text-sm text-[#a0a0a0]">레이블:</span>
            <span className="text-sm text-[#e0e0e0] font-medium">{llamaResult.label}</span>
          </div>
        </div>
      </div>
    );
  }

  // EXAONE 결과
  const exaoneResult = result as ExaoneResult;
  return (
    <div className="bg-[rgba(255,255,255,0.05)] border border-[rgba(118,75,162,0.3)] rounded-xl p-4">
      <h4 className="m-0 mb-4 text-white text-base font-semibold">{title}</h4>
      <div className="flex flex-col gap-3">
        {exaoneResult.is_spam !== null && (
          <div className="flex flex-col gap-2 py-2 border-b border-[rgba(255,255,255,0.1)] last:border-b-0">
            <span className="text-sm text-[#a0a0a0] font-medium">스팸 여부:</span>
            <span className={`px-3 py-1 rounded-lg text-sm font-semibold w-fit ${
              exaoneResult.is_spam
                ? "bg-[rgba(248,113,113,0.2)] text-[#f87171]"
                : "bg-[rgba(74,222,128,0.2)] text-[#4ade80]"
            }`}>
              {exaoneResult.is_spam ? "스팸" : "정상"}
            </span>
          </div>
        )}
        <div className="flex flex-col gap-2 py-2 border-b border-[rgba(255,255,255,0.1)] last:border-b-0">
          <span className="text-sm text-[#a0a0a0] font-medium">신뢰도:</span>
          <span className={`px-3 py-1 rounded-lg text-sm font-semibold w-fit ${
            exaoneResult.confidence === "high"
              ? "bg-[rgba(74,222,128,0.2)] text-[#4ade80]"
              : exaoneResult.confidence === "medium"
                ? "bg-[rgba(251,191,36,0.2)] text-[#fbbf24]"
                : "bg-[rgba(248,113,113,0.2)] text-[#f87171]"
          }`}>
            {exaoneResult.confidence}
          </span>
        </div>
        {exaoneResult.reason_codes && exaoneResult.reason_codes.length > 0 && (
          <div className="flex flex-col gap-2 py-2 border-b border-[rgba(255,255,255,0.1)] last:border-b-0">
            <span className="text-sm text-[#a0a0a0] font-medium">이유 코드:</span>
            <div className="flex flex-wrap gap-2">
              {exaoneResult.reason_codes.map((code, idx) => (
                <span key={idx} className="px-2 py-1 bg-[rgba(248,113,113,0.2)] text-[#f87171] rounded text-xs font-medium">
                  {code}
                </span>
              ))}
            </div>
          </div>
        )}
        {exaoneResult.action && (
          <div className="flex flex-col gap-2 py-2 border-b border-[rgba(255,255,255,0.1)] last:border-b-0">
            <span className="text-sm text-[#a0a0a0] font-medium">액션:</span>
            <span className="text-sm text-[#e0e0e0] font-medium">{exaoneResult.action}</span>
          </div>
        )}
        {exaoneResult.rule_based !== undefined && (
          <div className="flex flex-col gap-2 py-2 border-b border-[rgba(255,255,255,0.1)] last:border-b-0">
            <span className="text-sm text-[#a0a0a0] font-medium">처리 방식:</span>
            <span className="text-sm text-[#e0e0e0] font-medium">
              {exaoneResult.rule_based ? "규칙 기반" : "정책 기반"}
            </span>
          </div>
        )}
        {exaoneResult.analysis && (
          <div className="flex flex-col gap-2 py-2 border-b border-[rgba(255,255,255,0.1)] last:border-b-0">
            <span className="text-sm text-[#a0a0a0] font-medium">분석 내용:</span>
            <div className="p-3 bg-[rgba(0,0,0,0.2)] rounded-lg text-[#e0e0e0] text-sm leading-[1.6] max-h-[200px] overflow-y-auto">
              {exaoneResult.analysis}
            </div>
          </div>
        )}
        {exaoneResult.error && (
          <div className="flex flex-col gap-2 py-2 border-b border-[rgba(255,255,255,0.1)] last:border-b-0">
            <span className="text-sm text-[#a0a0a0] font-medium">오류:</span>
            <span className="text-[#f87171] text-sm">{exaoneResult.error}</span>
          </div>
        )}
      </div>
    </div>
  );
}
