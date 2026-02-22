"use client";

import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";

/** 공시 모드는 헤더 토글로만 용어 전환. 레이아웃은 항상 동일(사이드바·헤더·버튼 유지). */
export function DashboardLayoutClient({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="relative min-h-screen bg-gradient-to-br from-sky-100/90 via-teal-50/70 to-emerald-100/80 dark:from-[#0a0a0a] dark:via-[#0f0f0f] dark:to-[#0a0a0a]">
      <Sidebar />
      <main className="pl-56">
        <Header />
        <div className="pl-8 pr-3 py-8">{children}</div>
      </main>
    </div>
  );
}
