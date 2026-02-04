"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Moon, Sun } from "lucide-react";
import { useStore } from "@/store/useStore";
import { useHydrated } from "@/hooks/use-hydrated";
import { cn } from "@/lib/utils";

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
        : "공식 공시 모드(Official Mode)로 전환되었습니다. 지표가 IFRS 표준 용어로 표기됩니다."
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
  const selectedEmployee = useStore((s) => s.selectedEmployee);

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-border bg-background/95 px-8 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex items-center gap-4">
        <h1 className="text-lg font-semibold text-foreground">Success DNA</h1>
        {hydrated && selectedEmployee !== null && (
          <span className="text-sm text-muted-foreground">
            조회 중: <strong className="text-foreground">{selectedEmployee.name}</strong>
            {selectedEmployee.department && (
              <span className="ml-1">({selectedEmployee.department})</span>
            )}
          </span>
        )}
      </div>
      {hydrated && (
        <div className="flex items-center gap-3">
          <ThemeToggle />
          <span className="text-sm font-medium text-muted-foreground">
            공시 모드 (Disclosure Mode)
          </span>
          <DisclosureModeSwitch />
        </div>
      )}
    </header>
  );
}
