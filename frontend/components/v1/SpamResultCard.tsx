"use client";

import type { SpamDetectionResponse } from "@/lib/types/spam";
import ModelResultView from "./ModelResultView";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface SpamResultCardProps {
  result: SpamDetectionResponse;
}

export default function SpamResultCard({ result }: SpamResultCardProps) {
  const getActionColor = (action: string) => {
    switch (action) {
      case "reject":
        return "#f87171"; // 빨강
      case "quarantine":
        return "#fbbf24"; // 노랑
      case "deliver_with_warning":
        return "#fbbf24"; // 노랑
      case "deliver":
        return "#4ade80"; // 녹색
      case "ask_user_confirm":
        return "#60a5fa"; // 파랑
      default:
        return "#a0a0a0"; // 회색
    }
  };

  const getActionLabel = (action: string) => {
    const labels: Record<string, string> = {
      reject: "차단",
      quarantine: "격리",
      deliver_with_warning: "경고와 함께 전달",
      deliver: "전달",
      ask_user_confirm: "사용자 확인 필요",
    };
    return labels[action] || action;
  };

  const getConfidenceColor = (confidence: string) => {
    switch (confidence) {
      case "high":
        return "#4ade80";
      case "medium":
        return "#fbbf24";
      case "low":
        return "#f87171";
      default:
        return "#a0a0a0";
    }
  };

  return (
    <div className="flex flex-col gap-6 p-6">
      {/* 최종 결정 카드 */}
      <Card className="bg-[rgba(255,255,255,0.05)] border border-[rgba(102,126,234,0.3)] rounded-xl p-6">
        <CardHeader className="p-0 mb-4">
          <CardTitle className="m-0 text-white text-lg font-semibold">최종 결정</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4 p-0">
          <div
            className="inline-block px-4 py-2 rounded-lg text-white font-semibold text-sm w-fit"
            style={{ backgroundColor: getActionColor(result.action) }}
          >
            {getActionLabel(result.action)}
          </div>
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-4">
              <span className="text-sm text-[#a0a0a0] min-w-[80px]">스팸 확률</span>
              <div className="flex-1 h-6 bg-[rgba(0,0,0,0.3)] rounded-xl relative overflow-hidden">
                <div
                  className="h-full rounded-xl transition-all duration-300"
                  style={{
                    width: `${result.spam_prob * 100}%`,
                    backgroundColor: getActionColor(result.action),
                  }}
                />
                <span className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-xs font-semibold text-white drop-shadow-[0_1px_2px_rgba(0,0,0,0.5)]">
                  {(result.spam_prob * 100).toFixed(1)}%
                </span>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-[#a0a0a0] min-w-[80px]">신뢰도</span>
              <span
                className="px-3 py-1 rounded-lg bg-[rgba(0,0,0,0.3)] font-semibold text-sm"
                style={{ color: getConfidenceColor(result.confidence) }}
              >
                {result.confidence.toUpperCase()}
              </span>
            </div>
          </div>
          <div className="p-4 bg-[rgba(0,0,0,0.2)] rounded-lg text-[#e0e0e0] leading-[1.6]">
            {result.user_message}
          </div>
          {result.reason_codes.length > 0 && (
            <div className="p-3 bg-[rgba(0,0,0,0.2)] rounded-lg text-[#e0e0e0] text-sm">
              <strong>이유 코드:</strong>
              <ul className="mt-2 mb-0 ml-6 list-disc">
                {result.reason_codes.map((code, idx) => (
                  <li key={idx} className="my-1">{code}</li>
                ))}
              </ul>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 모델 결과 카드들 */}
      <div className="grid grid-cols-[repeat(auto-fit,minmax(300px,1fr))] gap-4 md:grid-cols-1">
        <ModelResultView
          title="LLaMA 게이트웨이"
          result={result.llama_result}
          type="llama"
        />
        {result.exaone_result && (
          <ModelResultView
            title="EXAONE 상세 분석"
            result={result.exaone_result}
            type="exaone"
          />
        )}
      </div>

      {/* 라우팅 경로 */}
      <div className="p-4 bg-[rgba(0,0,0,0.2)] rounded-lg border border-[rgba(102,126,234,0.2)]">
        <h4 className="m-0 mb-2 text-[#e0e0e0] text-sm font-semibold">실행 경로</h4>
        <div className="font-mono text-sm text-[#a0a0a0] p-2 bg-[rgba(0,0,0,0.3)] rounded break-all">
          {result.routing_path}
        </div>
      </div>
    </div>
  );
}
