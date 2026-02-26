"use client";

import { usePathname } from "next/navigation";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { ChatPanel } from "@/modules/chat/components/ChatPanel";

export function DashboardLayoutClient({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const isChatPage = pathname === "/chat" || pathname === "/dashboard/chat";

  return (
    <div className="relative min-h-screen bg-gradient-to-br from-[#e8f5ef] via-[#f0f5f0] to-[#e8f5ef]/80 dark:from-[#0a0a0a] dark:via-[#0f0f0f] dark:to-[#0a0a0a]">
      <Sidebar />
      <main className="pl-56">
        <Header />
        <div className="pl-8 pr-3 py-8">
          {/* ChatPanel: 항상 마운트 유지 → 다른 페이지 이동 중에도 스트리밍 끊기지 않음 */}
          <div
            className={isChatPage ? "flex h-[calc(100vh-8rem)] flex-col" : "pointer-events-none fixed left-[-9999px] h-0 overflow-hidden opacity-0"}
            aria-hidden={!isChatPage}
          >
            <ChatPanel />
          </div>
          {!isChatPage && children}
        </div>
      </main>
    </div>
  );
}
