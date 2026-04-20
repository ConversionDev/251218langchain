"use client";

import { useEffect, useMemo, useState } from "react";
import { notFound } from "next/navigation";

const API_BASE =
  typeof window !== "undefined"
    ? (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000")
    : "http://localhost:8000";

export default function DataMapPage() {
  if (process.env.NODE_ENV !== "development") {
    notFound();
  }
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    const check = () =>
      setIsDark(document.documentElement.classList.contains("dark"));
    check();
    const observer = new MutationObserver(check);
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["class"],
    });
    return () => observer.disconnect();
  }, []);

  const mapUrl = useMemo(
    () => `${API_BASE}/api/clustering/map?theme=${isDark ? "dark" : "light"}`,
    [isDark]
  );

  return (
    <div className="flex h-[calc(100vh-6rem)] flex-col gap-3 overflow-hidden">
      <div className="shrink-0 space-y-2 px-4 pt-2">
        <h1 className="text-lg font-semibold text-foreground">데이터 지도</h1>
        <p className="text-xs text-muted-foreground">
          역량 관련 항목을 유사도 기준으로 군집화한 지도입니다. 전체 약 11만 건 중 일부만 샘플링해 시각화했습니다. 색·모양으로 군집 구분, 파스텔 영역은 군집 범위, ★는 군집 중심입니다.
        </p>
        <div className="space-y-1 rounded-md bg-muted/50 px-3 py-2 text-xs text-muted-foreground">
          <p className="font-medium text-foreground/90">분석 방법</p>
          <p>
            임베딩 벡터 → K-Means 클러스터링(전체 군집) → UMAP 2차원 축소 → 상위 군집 시각화(볼록 껍질·군집별 색).
          </p>
          <p className="mt-1 font-medium text-foreground/90">사용 데이터 (원본)</p>
          <p>
            competency_anchors — Data from original sources: Abilities.xlsx, Task Statements.xlsx, Technology Skills.xlsx, Work Styles.xlsx, 대인관계능력_01_교수자용.pdf, 문제해결능력_01_교수자용.pdf, 의사소통능력_01_교수자용.pdf, 자기개발능력_01_교수자용.pdf.
          </p>
        </div>
      </div>
      <div className="relative min-h-0 flex-1 px-4 pb-4">
        <div className="absolute inset-0 rounded-lg border border-[#a8d5c4]/50 bg-card dark:border-primary/20" />
        <iframe
          src={mapUrl}
          title="역량 군집화 지도"
          className="absolute inset-0 h-full w-full rounded-lg border-0 bg-transparent"
        />
      </div>
    </div>
  );
}
