"use client";

import { Fragment } from "react";

/** ClickMe RAG 품질 평가 표 — 발표 슬라이드·이력서와 동일 수치 (단일 출처) */
export interface EvalTier {
  tier: string;
  rows: { metric: string; change: string; work: string }[];
}

export const RAG_EVAL_TIERS: EvalTier[] = [
  {
    tier: "RAG Pipeline 평가 지표",
    rows: [
      {
        metric: "Hit Rate@K",
        change: "단일 0.886 → 1.000 · 복합 0.800 → 1.000",
        work: "하이브리드 검색, 검색 결과 다양화, 리랭킹",
      },
      {
        metric: "MRR",
        change: "단일 0.705 → 0.938 · 복합 0.634 → 0.833",
        work: "리랭킹을 통한 정답 문서 순위 개선",
      },
      {
        metric: "Context Precision",
        change: "단일 신규측정 → 0.886 · 복합 신규측정 → 0.926",
        work: "관련 문서 정밀도 지표 신규 도입, 계산 로직 오류 수정",
      },
    ],
  },
  {
    tier: "LLM as Judge",
    rows: [
      {
        metric: "Faithfulness",
        change: "0.51 → 1.00",
        work: "자료 근거 강제, CRAG 기반 자기교정, 재검색·답변 거절",
      },
      {
        metric: "Factual Correctness",
        change: "단일 0.714 → 0.986 · 복합 0.857 → 0.971",
        work: "회사 고유 규칙에 대한 자료 기반 답변 강제",
      },
      {
        metric: "환각 억제",
        change: "함정 질문 23개 별도평가",
        work: "근거 확인, 재검색, 답변 거절, CRAG 자기교정",
      },
    ],
  },
];

export function RagEvalTable({ tiers }: { tiers: EvalTier[] }) {
  return (
    <div
      className="overflow-x-auto rounded-lg"
      style={{ border: "1px solid rgba(142,240,215,0.1)" }}
    >
      <table
        className="w-full"
        style={{ borderCollapse: "collapse", fontSize: "0.75rem", minWidth: 480 }}
      >
        <tbody>
          {tiers.map((tier) => (
            <Fragment key={tier.tier}>
              <tr>
                <td
                  colSpan={3}
                  style={{
                    padding: "7px 10px",
                    fontSize: "0.6875rem",
                    fontWeight: 700,
                    letterSpacing: "0.08em",
                    textTransform: "uppercase",
                    color: "#8ef0d7",
                    background: "rgba(142,240,215,0.06)",
                  }}
                >
                  {tier.tier}
                </td>
              </tr>
              {tier.rows.map((r) => (
                <tr key={r.metric} style={{ borderTop: "1px solid rgba(255,255,255,0.08)" }}>
                  <td
                    style={{
                      padding: "8px 10px",
                      color: "rgba(220,228,245,0.92)",
                      fontWeight: 600,
                      whiteSpace: "nowrap",
                      verticalAlign: "top",
                    }}
                  >
                    {r.metric}
                  </td>
                  <td
                    style={{
                      padding: "8px 10px",
                      fontFamily: "'JetBrains Mono', monospace",
                      color: "#8ef0d7",
                      verticalAlign: "top",
                    }}
                  >
                    {r.change}
                  </td>
                  <td
                    style={{
                      padding: "8px 10px",
                      color: "rgba(220,228,245,0.75)",
                      lineHeight: 1.55,
                      verticalAlign: "top",
                    }}
                  >
                    {r.work}
                  </td>
                </tr>
              ))}
            </Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
}
