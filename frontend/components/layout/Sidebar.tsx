"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Users,
  UserPlus,
  Brain,
  ShieldCheck,
  BarChart3,
  MessageCircle,
  Map,
  Home,
  Settings,
  FileText,
  ShieldAlert,
} from "lucide-react";
import { useHydrated } from "@/hooks/use-hydrated";
import { useDemoRoleStore } from "@/store/useDemoRoleStore";
import { cn } from "@/lib/utils";

const navItems: {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  /** true면 하위 경로(/performance/activities 등)에서 이 메뉴는 비활성 */
  exact?: boolean;
}[] = [
  { href: "/", label: "메인", icon: Home, exact: true },
  { href: "/dashboard", label: "전사 현황", icon: LayoutDashboard },
  { href: "/chat", label: "AI 질의", icon: MessageCircle },
  { href: "/data-map", label: "데이터 지도", icon: Map },
  { href: "/core/new-hires", label: "신입 관리", icon: UserPlus },
  { href: "/core/employees", label: "기존 직원", icon: Users },
  { href: "/performance/activities", label: "활동기록", icon: FileText },
  { href: "/risk", label: "감사 로그", icon: ShieldAlert },
  { href: "/intelligence", label: "역량 진단", icon: Brain },
  { href: "/credential", label: "자격 검증", icon: ShieldCheck },
  { href: "/performance", label: "성과·가치", icon: BarChart3, exact: true },
  { href: "/settings", label: "설정", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const hydrated = useHydrated();
  const demoRole = useDemoRoleStore((s) => s.demoRole);
  const isDemoAdmin = hydrated && demoRole === "admin";

  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-56 border-r border-slate-200/30 bg-white/80 shadow-sm backdrop-blur-md dark:border-white/10 dark:bg-[#0f0f0f]/95">
      <div className="flex h-16 flex-col justify-center gap-0.5 border-b border-slate-200/40 px-4 dark:border-white/10">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-emerald-500 text-white">
            <LayoutDashboard className="h-5 w-5" />
          </div>
          <div className="min-w-0">
            <span className="block font-semibold text-slate-800 dark:text-slate-100">Success DNA</span>
            <span className="block text-[10px] font-medium uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
              {isDemoAdmin ? "데모 · 관리자" : "관리자"}
            </span>
          </div>
        </div>
      </div>
      <nav className="flex flex-col gap-1 p-3.5">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = item.exact
            ? pathname === item.href
            : pathname === item.href ||
              (item.href !== "/" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-2 rounded-lg px-2.5 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-emerald-500 text-white dark:bg-white/10 dark:text-emerald-400 dark:border-l-2 dark:border-emerald-500 dark:border-y-0 dark:border-r-0"
                  : "text-slate-600 hover:bg-emerald-50/90 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-white/5 dark:hover:text-slate-100"
              )}
            >
              <Icon className="h-5 w-5 shrink-0" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
