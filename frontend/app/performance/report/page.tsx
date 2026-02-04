"use client";

import { useEffect, useState } from "react";
import { FileDown, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ReportContent } from "@/modules/performance/components/ReportContent";
import type { PerformanceMetrics, DisclosureSummary, ImpactDataPoint } from "@/modules/performance/types";

const STORAGE_KEY = "performance-report-payload";
const THEME_KEY = "theme";

export interface PerformanceReportPayload {
  reportTitle: string;
  summaryName: string;
  metrics: PerformanceMetrics | null;
  chartData: ImpactDataPoint[];
  disclosureSummary: DisclosureSummary | null;
}

export default function PerformanceReportPage() {
  const [payload, setPayload] = useState<PerformanceReportPayload | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const stored = localStorage.getItem(THEME_KEY);
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const isDark = stored === "dark" || (stored !== "light" && prefersDark);
    document.documentElement.classList.toggle("dark", isDark);
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const data = JSON.parse(raw) as Partial<PerformanceReportPayload>;
        const payload: PerformanceReportPayload = {
          reportTitle: data.reportTitle ?? "인적 자본 가치 리포트",
          summaryName: data.summaryName ?? "",
          metrics: data.metrics ?? null,
          chartData: Array.isArray(data.chartData) ? data.chartData : [],
          disclosureSummary: data.disclosureSummary ?? null,
        };
        setPayload(payload);
        localStorage.removeItem(STORAGE_KEY);
      }
    } catch {
      setPayload(null);
    }
  }, []);

  const handlePrint = () => {
    window.print();
  };

  const handleClose = () => {
    if (window.opener) {
      window.close();
    } else {
      window.location.href = "/performance";
    }
  };

  if (payload === null) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-100 dark:bg-background p-8">
        <div className="rounded-xl border border-slate-200 dark:border-border bg-white dark:bg-card p-8 text-center shadow-sm">
          <p className="text-slate-600 dark:text-foreground">리포트 데이터가 없거나 만료되었습니다.</p>
          <p className="mt-2 text-sm text-slate-500 dark:text-muted-foreground">
            Performance 페이지에서 다시 「공시 리포트 다운로드」를 눌러 주세요.
          </p>
          <Button variant="outline" className="mt-4" onClick={handleClose}>
            Performance로 돌아가기
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="performance-report-page min-h-screen bg-white dark:bg-background">
      <div className="fixed right-4 top-4 z-10 flex gap-2 print:hidden">
        <Button
          onClick={handlePrint}
          className="inline-flex items-center gap-2 bg-slate-800 dark:bg-primary text-white hover:bg-slate-700 dark:hover:bg-primary/90"
        >
          <FileDown className="h-4 w-4" />
          PDF 저장
        </Button>
        <Button variant="outline" onClick={handleClose} className="inline-flex items-center gap-2">
          <X className="h-4 w-4" />
          닫기
        </Button>
      </div>

      <main className="performance-report-main mx-auto max-w-4xl bg-white px-6 py-12 pt-20 print:pt-8 sm:px-10 print:bg-white dark:bg-card">
        <ReportContent
          reportTitle={payload.reportTitle}
          summaryName={payload.summaryName}
          metrics={payload.metrics}
          chartData={payload.chartData}
          disclosureSummary={payload.disclosureSummary}
          reportMode={false}
        />
      </main>
    </div>
  );
}
