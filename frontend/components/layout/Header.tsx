"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { toast } from "sonner";
import { BriefcaseBusiness, Moon, Sun, Sparkles } from "lucide-react";
import { useStore } from "@/store/useStore";
import { useHydrated } from "@/hooks/use-hydrated";
import { cn } from "@/lib/utils";
import { backfillEmployeeProfilesApi, refreshEmployeeEmbeddingsApi } from "@/modules/core/services";
import { CORE_EMPLOYEES_MESSAGES } from "@/modules/shared/constants/messages";

const THEME_KEY = "theme";

function ThemeToggle() {
  const [dark, setDark] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem(THEME_KEY);
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const isDark = stored === "dark" || (stored !== "light" && prefersDark);
    setDark(isDark);
    if (isDark) document.documentElement.classList.add("dark");
    else document.documentElement.classList.remove("dark");
  }, []);

  const toggle = () => {
    const next = !dark;
    setDark(next);
    document.documentElement.classList.toggle("dark", next);
    localStorage.setItem(THEME_KEY, next ? "dark" : "light");
    toast.success(next ? "다크 모드로 전환되었습니다." : "라이트 모드로 전환되었습니다.");
  };

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={dark ? "라이트 모드로 전환" : "다크 모드로 전환"}
      className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
    >
      {dark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
    </button>
  );
}

function DisclosureModeSwitch() {
  const { isDisclosureMode, toggleDisclosureMode } = useStore();

  const handleToggle = () => {
    toggleDisclosureMode();
    toast.success(
      isDisclosureMode
        ? "일반 보기 모드로 전환되었습니다."
        : "공식 공시 모드로 전환되었습니다. 지표가 IFRS 표준 용어로 표기됩니다."
    );
  };

  return (
    <button
      type="button"
      role="switch"
      aria-checked={isDisclosureMode}
      aria-label="공시 모드"
      onClick={handleToggle}
      className={cn(
        "relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
        isDisclosureMode ? "bg-primary" : "bg-muted"
      )}
    >
      <span
        className={cn(
          "pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition",
          isDisclosureMode ? "translate-x-5" : "translate-x-0.5"
        )}
      />
    </button>
  );
}

export function Header() {
  const hydrated = useHydrated();
  const pathname = usePathname();
  const selectedEmployee = useStore((s) => s.selectedEmployee);
  const setSelectedEmployee = useStore((s) => s.setSelectedEmployee);
  const [embeddingLoading, setEmbeddingLoading] = useState(false);
  const [backfillLoading, setBackfillLoading] = useState(false);
  const showBackfillButton = pathname === "/core/employees";

  const handleBackfillProfiles = async () => {
    setBackfillLoading(true);
    try {
      const preview = await backfillEmployeeProfilesApi({ dryRun: true, seed: 42 });
      const msg = CORE_EMPLOYEES_MESSAGES.confirm.profileBackfill({
        targetRegularEmployees: preview.targetRegularEmployees,
        gender: preview.updated.gender,
        age: preview.updated.age,
        trainingHours: preview.updated.trainingHours,
      });
      const ok = window.confirm(msg);
      if (!ok) return;
      const saved = await backfillEmployeeProfilesApi({ dryRun: false, seed: 42 });
      toast.success(CORE_EMPLOYEES_MESSAGES.toast.backfillCompleted(saved.updated), { duration: 5000 });
    } catch (e) {
      toast.error(e instanceof Error ? e.message : CORE_EMPLOYEES_MESSAGES.toast.backfillFailed, { duration: 5000 });
    } finally {
      setBackfillLoading(false);
    }
  };

  const handleRefreshEmbeddings = async () => {
    setEmbeddingLoading(true);
    try {
      const result = await refreshEmployeeEmbeddingsApi();
      const perf = result.performanceUpdated ?? 0;
      const opts = { duration: 5000 };
      if (result.updated === 0 && perf === 0) {
        toast.info("갱신할 대상이 없습니다. 모든 직원·성과 기록에 이미 임베딩이 반영되어 있습니다.", opts);
        return;
      }
      const perfMsg = perf > 0 ? `, 성과 ${perf}건` : "";
      toast.success(`임베딩 갱신 완료 (직원 ${result.updated}명${perfMsg} 반영). RAG 검색에 반영됩니다.`, opts);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "임베딩 갱신에 실패했습니다.", { duration: 5000 });
    } finally {
      setEmbeddingLoading(false);
    }
  };

  return (
    <header className="sticky top-0 z-30 flex min-h-[4.5rem] items-center justify-between border-b border-[#a8d5c4]/50 bg-white/85 px-6 py-3 backdrop-blur-md dark:border-primary/20 dark:bg-[#0f0f0f]/90 md:px-8 md:py-4">
      <div className="flex items-center gap-4">
        <h1 className="text-lg font-semibold text-foreground">Success DNA</h1>
        {hydrated && selectedEmployee !== null && (
          <span className="flex items-center gap-2 text-sm text-muted-foreground">
            <span>
              선택 직원: <strong className="text-foreground">{selectedEmployee.name}</strong>
              {selectedEmployee.department && (
                <span className="ml-1">({selectedEmployee.department})</span>
              )}
            </span>
            <button
              type="button"
              onClick={() => setSelectedEmployee(null)}
              className="rounded px-2 py-1 text-xs font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              aria-label="선택 해제"
            >
              선택 해제
            </button>
          </span>
        )}
      </div>
      {hydrated && (
        <div className="flex items-center gap-3">
          {showBackfillButton && (
            <button
              type="button"
              onClick={handleBackfillProfiles}
              disabled={backfillLoading}
              title="기존 직원 결측 프로필 자동 보정"
              className="inline-flex items-center gap-2 rounded-lg border border-[#a8d5c4]/80 bg-[#e8f5ef]/80 px-3 py-1.5 text-sm font-medium text-slate-700 transition-colors hover:bg-[#e8f5ef] disabled:opacity-50 dark:border-primary/30 dark:bg-primary/10 dark:text-foreground dark:hover:bg-primary/20"
            >
              {backfillLoading ? CORE_EMPLOYEES_MESSAGES.buttons.backfilling : CORE_EMPLOYEES_MESSAGES.buttons.backfill}
            </button>
          )}
          <button
            type="button"
            onClick={handleRefreshEmbeddings}
            disabled={embeddingLoading}
            title="직원·성과 RAG 임베딩 일괄 갱신"
            className="inline-flex items-center gap-2 rounded-lg border border-[#a8d5c4]/80 bg-[#e8f5ef]/80 px-3 py-1.5 text-sm font-medium text-slate-700 transition-colors hover:bg-[#e8f5ef] disabled:opacity-50 dark:border-primary/30 dark:bg-primary/10 dark:text-foreground dark:hover:bg-primary/20"
          >
            <Sparkles className="h-4 w-4" />
            {embeddingLoading ? "갱신 중…" : "임베딩 갱신"}
          </button>
          <Link
            href="/workspace"
            className="inline-flex items-center gap-2 rounded-lg border border-[#a8d5c4]/80 bg-[#e8f5ef]/80 px-3 py-1.5 text-sm font-medium text-slate-700 transition-colors hover:bg-[#e8f5ef] dark:border-primary/30 dark:bg-primary/10 dark:text-foreground dark:hover:bg-primary/20"
            title="직원 업무 서비스로 이동"
          >
            <BriefcaseBusiness className="h-4 w-4" />
            직원 서비스
          </Link>
          <ThemeToggle />
          <span className="text-sm font-medium text-muted-foreground">
            공시 모드
          </span>
          <DisclosureModeSwitch />
        </div>
      )}
    </header>
  );
}
