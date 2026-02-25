"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ExternalLink } from "lucide-react";
import { useHydrated } from "@/hooks/use-hydrated";
import { useDemoRoleStore } from "@/store/useDemoRoleStore";

export function WorkspaceLayoutClient({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const hydrated = useHydrated();
  const demoRole = useDemoRoleStore((s) => s.demoRole);
  const isWorkspacePortal = pathname === "/workspace";
  const isDemoEmployee = hydrated && demoRole === "employee";

  if (isWorkspacePortal) {
    return <div className="min-h-screen bg-[#08130e] dark:bg-[#050907]">{children}</div>;
  }

  return (
    <div className="flex min-h-screen flex-col bg-slate-100/80 dark:bg-[#0b0b0c]">
      <header className="sticky top-0 z-20 flex shrink-0 items-center justify-between border-b border-slate-200/70 bg-white px-4 py-2.5 md:px-6 dark:border-white/10 dark:bg-[#111214]">
        <div className="flex items-center gap-3">
          <span className="rounded-md bg-emerald-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-300">
            {isDemoEmployee ? "데모 · 직원 포털" : "직원 포털"}
          </span>
          <Link href="/workspace" className="flex items-center gap-2 text-sm">
            <span className="text-[10px] font-medium uppercase tracking-wider text-[#707A8A] dark:text-slate-400">
              AI POWERED HR INTELLIGENCE
            </span>
            <span className="font-bold tracking-tight">
              <span className="text-[#3D7D3D] dark:text-emerald-700">HR</span>
              <span className="text-[#27B39E] dark:text-teal-400">Insight</span>
            </span>
          </Link>
        </div>
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
