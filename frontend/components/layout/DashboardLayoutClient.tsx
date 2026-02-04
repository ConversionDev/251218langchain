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
    <div className="relative min-h-screen bg-background">
      <Sidebar />
      <main className="pl-64">
        <Header />
        <div className="p-8">{children}</div>
      </main>
    </div>
  );
}
