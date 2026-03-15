"use client";

import { useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { Users, UserCog, FileEdit } from "lucide-react";
import {
  useDemoRoleStore,
  DEMO_ROLE_CONFIG,
  type DemoRole,
} from "@/store/useDemoRoleStore";
import { useHydrated } from "@/hooks/use-hydrated";
import { cn } from "@/lib/utils";

const ROLE_OPTIONS: { role: DemoRole; icon: React.ComponentType<{ className?: string }> }[] = [
  { role: "admin", icon: UserCog },
  { role: "employee", icon: Users },
  { role: "applicant", icon: FileEdit },
];

export function RoleSwitcher() {
  const hydrated = useHydrated();
  const router = useRouter();
  const pathname = usePathname();
  const { demoRole, setDemoRole } = useDemoRoleStore();
  const [open, setOpen] = useState(false);

  if (!hydrated) return null;
  if (pathname === "/" || pathname === "/resume") return null;

  const handleSwitch = (role: DemoRole) => {
    setDemoRole(role);
    setOpen(false);
    router.push(DEMO_ROLE_CONFIG[role].path);
  };

  return (
    <div className="fixed bottom-6 right-6 z-50">
      <div className="relative">
        <button
          type="button"
          onClick={() => setOpen((o) => !o)}
          className="flex h-12 w-12 items-center justify-center rounded-full border-2 border-slate-200 bg-white shadow-lg transition hover:border-emerald-400 hover:bg-emerald-50 dark:border-white/20 dark:bg-[#171717] dark:hover:border-emerald-500 dark:hover:bg-emerald-950/40"
          aria-label="시연용 역할 전환"
          aria-expanded={open}
        >
          <Users className="h-5 w-5 text-slate-600 dark:text-slate-300" />
        </button>

        {open && (
          <>
            <div
              className="fixed inset-0 z-40"
              aria-hidden
              onClick={() => setOpen(false)}
            />
            <div
              role="dialog"
              aria-label="역할 전환"
              className="absolute bottom-14 right-0 z-50 w-64 rounded-xl border border-slate-200 bg-white p-3 shadow-xl dark:border-white/10 dark:bg-[#1a1a1a]"
            >
              <p className="mb-2 text-xs font-medium text-slate-500 dark:text-slate-400">
                시연용 역할 전환
              </p>
              {demoRole ? (
                <p className="mb-3 text-sm text-slate-700 dark:text-slate-200">
                  현재 <strong>{DEMO_ROLE_CONFIG[demoRole].shortLabel}</strong>로 보는 중
                </p>
              ) : null}
              <div className="flex flex-col gap-1">
                {ROLE_OPTIONS.map(({ role, icon: Icon }) => (
                  <button
                    key={role}
                    type="button"
                    onClick={() => handleSwitch(role)}
                    className={cn(
                      "flex items-center gap-2 rounded-lg px-3 py-2.5 text-left text-sm font-medium transition-colors",
                      demoRole === role
                        ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-200"
                        : "text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-white/10"
                    )}
                  >
                    <Icon className="h-4 w-4 shrink-0" />
                    {DEMO_ROLE_CONFIG[role].label}
                  </button>
                ))}
              </div>
              <button
                type="button"
                onClick={() => {
                  setDemoRole(null);
                  setOpen(false);
                  router.push("/hr");
                }}
                className="mt-2 w-full rounded-lg border border-slate-200 py-1.5 text-xs text-slate-500 hover:bg-slate-50 dark:border-white/10 dark:text-slate-400 dark:hover:bg-white/5"
              >
                역할 초기화 · 메인으로
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
