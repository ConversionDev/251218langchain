"use client";

import type { DisclosureSummary } from "../types";

interface DisclosureSectionProps {
  summary: DisclosureSummary | null;
}

export function DisclosureSection({ summary }: DisclosureSectionProps) {
  if (!summary) {
    return (
      <section className="rounded-xl border border-border bg-card p-6 shadow-sm">
        <p className="text-sm text-muted-foreground">직원 선택 시 공시 요약이 표시됩니다.</p>
      </section>
    );
  }

  return (
    <section className="rounded-xl border border-border bg-card p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-foreground">인적 자본 가치 공시 (IFRS S1/S2)</h2>
      <p className="mt-2 text-xs text-muted-foreground">
        본 섹션은 IFRS S1/S2 가이드라인에 따른 인적 자본 공시 요약입니다.
      </p>
      <div className="mt-4 space-y-4">
        <div>
          <h3 className="text-sm font-medium text-foreground">AI 생성 요약</h3>
          <p className="mt-1 text-sm leading-relaxed text-foreground">
            {summary.narrative}
          </p>
        </div>
        <div className="rounded-lg bg-muted/40 p-4">
          <h3 className="text-sm font-medium text-foreground">IFRS S1 요약</h3>
          <p className="mt-1 text-sm text-muted-foreground">{summary.ifrsS1Summary}</p>
        </div>
        <div className="rounded-lg bg-muted/40 p-4">
          <h3 className="text-sm font-medium text-foreground">IFRS S2 요약</h3>
          <p className="mt-1 text-sm text-muted-foreground">{summary.ifrsS2Summary}</p>
        </div>
      </div>
    </section>
  );
}
