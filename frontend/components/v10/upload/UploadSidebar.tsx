"use client";

import { usePathname, useRouter } from "next/navigation";

interface MenuItem {
  id: string;
  label: string;
  icon: string;
  path: string;
}

// 데이터 의존성 순서에 맞게 정렬 (Foreign Key 참조 순서)
// 1. Stadiums → 2. Teams → 3. Players → 4. Schedules
const menuItems: MenuItem[] = [
  { id: "stadiums", label: "스타디움", icon: "🏟️", path: "/upload/stadium" },
  { id: "teams", label: "팀", icon: "⚽", path: "/upload/team" },
  { id: "players", label: "선수", icon: "👤", path: "/upload/player" },
  { id: "schedules", label: "스케줄", icon: "📅", path: "/upload/schedule" },
];

export default function UploadSidebar() {
  const pathname = usePathname();
  const router = useRouter();

  return (
    <aside className="w-full border-b border-slate-200 bg-white px-4 py-4 dark:border-slate-800 dark:bg-slate-900 md:h-[calc(100vh-60px)] md:w-52 md:border-b-0 md:border-r md:py-6 md:sticky md:top-[60px]">
      <nav className="flex gap-2 overflow-x-auto md:flex-col md:overflow-visible md:px-3">
        {menuItems.map((item) => {
          const isActive = pathname === item.path;
          return (
            <button
              key={item.id}
              type="button"
              className={`flex flex-shrink-0 items-center gap-3 rounded-lg border px-4 py-2.5 text-left text-sm transition-all md:whitespace-nowrap ${
                isActive
                  ? "border-blue-500 bg-blue-50 font-semibold text-slate-900 dark:border-blue-500 dark:bg-blue-950/50 dark:text-slate-100"
                  : "border-slate-200 bg-white text-slate-600 hover:border-blue-400 hover:bg-slate-50 hover:text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-400 dark:hover:border-blue-600 dark:hover:bg-slate-700 dark:hover:text-slate-100"
              }`}
              onClick={() => router.push(item.path)}
            >
              <span className="text-lg">{item.icon}</span>
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
