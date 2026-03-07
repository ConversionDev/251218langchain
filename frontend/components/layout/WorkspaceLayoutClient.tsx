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
    <div className="flex min-h-screen flex-col bg-[#f0f5f0] dark:bg-[#0b0b0c]">
      <header className="sticky top-0 z-20 flex min-h-[4.5rem] shrink-0 items-center justify-between border-b border-[#a8d5c4]/50 bg-white/85 px-6 py-3 backdrop-blur-md dark:border-primary/20 dark:bg-[#0f0f0f]/90 md:px-8 md:py-4">
        <div className="flex flex-1 items-center gap-3 md:gap-4">
          <Link href="/workspace" className="flex items-baseline gap-1.5">
            <span className="text-[11px] font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
              AI Powered HR Intelligence
            </span>
            <span className="text-base font-bold tracking-tight text-[#14532d] dark:text-emerald-800 md:text-lg">HR</span>
            <span
              className="bg-gradient-to-r from-teal-600 to-emerald-500 bg-clip-text text-base font-bold tracking-tight text-transparent dark:from-teal-400 dark:to-emerald-400 md:text-lg"
              style={{ WebkitBackgroundClip: "text" }}
            >
              Insight
            </span>
          </Link>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <Link
            href="/demo"
            className="text-sm font-medium text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
          >
            시연 역할
          </Link>
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 text-sm font-semibold text-slate-700 transition-colors hover:text-slate-900 md:text-base dark:text-slate-300 dark:hover:text-slate-100"
          >
            <ExternalLink className="h-4 w-4" />
            메인으로
          </Link>
        </div>
      </header>
      <main className="min-h-0 flex-1 p-4 md:p-5">
        {children}
      </main>
    </div>
  );
}
