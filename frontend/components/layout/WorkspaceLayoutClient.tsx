"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ExternalLink } from "lucide-react";

export function WorkspaceLayoutClient({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const isWorkspacePortal = pathname === "/workspace";

  if (isWorkspacePortal) {
    return <div className="min-h-screen bg-[#08130e] dark:bg-[#050907]">{children}</div>;
  }

  return (
    <div className="flex min-h-screen flex-col bg-slate-100/80 dark:bg-[#0b0b0c]">
      <header className="sticky top-0 z-20 flex shrink-0 items-center justify-between border-b border-slate-200/70 bg-white px-4 py-2.5 md:px-6 dark:border-white/10 dark:bg-[#111214]">
        <Link
          href="/workspace"
          className="text-sm font-semibold text-slate-800 dark:text-slate-100"
        >
          HRInsight 직원 서비스
        </Link>
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-sm text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700 dark:text-slate-400 dark:hover:bg-white/5 dark:hover:text-slate-200"
        >
          <ExternalLink className="h-4 w-4" />
          메인으로
        </Link>
      </header>
      <main className="min-h-0 flex-1 p-4 md:p-5">
        {children}
      </main>
    </div>
  );
}
