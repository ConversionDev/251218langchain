"use client";

import { useRouter, usePathname } from "next/navigation";

interface BottomNavigationProps {
  currentPage: string;
}

export default function BottomNavigation({
  currentPage,
}: BottomNavigationProps) {
  const router = useRouter();
  const pathname = usePathname();

  const navItems = [
    {
      id: "upload",
      label: "업로드",
      icon: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
          <path
            d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"
            stroke="currentColor"
            strokeWidth="2"
            fill="none"
          />
          <polyline points="17 8 12 3 7 8" stroke="currentColor" strokeWidth="2" fill="none" />
          <line x1="12" y1="3" x2="12" y2="15" stroke="currentColor" strokeWidth="2" />
        </svg>
      ),
      path: "/v10/upload",
    },
  ];

  const handleNavigation = (path: string) => {
    router.push(path);
  };

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 flex justify-around items-center py-2 z-[100] shadow-[0_-2px_8px_rgba(0,0,0,0.05)] md:max-w-[768px] md:left-1/2 md:-translate-x-1/2">
      {navItems.map((item) => {
        // 업로드 페이지는 하위 경로도 활성화
        const isActive =
          pathname === item.path ||
          currentPage === item.id ||
          (item.id === "upload" && pathname.startsWith("/v10/upload"));
        return (
          <button
            key={item.id}
            className={`flex flex-col items-center gap-1 bg-none border-none px-3 py-2 cursor-pointer transition-all flex-1 max-w-[80px] ${
              isActive
                ? "text-gray-800 [&>div]:scale-110 [&>span]:font-semibold"
                : "text-gray-500 hover:text-gray-800"
            }`}
            onClick={() => handleNavigation(item.path)}
            aria-label={item.label}
          >
            <div className="flex items-center justify-center transition-transform">{item.icon}</div>
            <span className="text-[0.625rem] font-medium">{item.label}</span>
          </button>
        );
      })}
    </nav>
  );
}
