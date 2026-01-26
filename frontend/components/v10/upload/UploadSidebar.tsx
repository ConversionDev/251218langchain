"use client";

import { usePathname, useRouter } from "next/navigation";

interface MenuItem {
  id: string;
  label: string;
  icon: string;
  path: string;
}

const menuItems: MenuItem[] = [
  { id: "players", label: "선수", icon: "👤", path: "/v10/upload/player" },
  { id: "teams", label: "팀", icon: "⚽", path: "/v10/upload/team" },
  { id: "stadiums", label: "스타디움", icon: "🏟️", path: "/v10/upload/stadium" },
  { id: "schedules", label: "스케줄", icon: "📅", path: "/v10/upload/schedule" },
];

export default function UploadSidebar() {
  const pathname = usePathname();
  const router = useRouter();

  return (
    <>
      <aside className="sidebar">
        <nav className="sidebar-nav">
          {menuItems.map((item) => {
            const isActive = pathname === item.path;
            return (
              <button
                key={item.id}
                className={`sidebar-item ${isActive ? "active" : ""}`}
                onClick={() => router.push(item.path)}
              >
                <span className="sidebar-icon">{item.icon}</span>
                <span className="sidebar-label">{item.label}</span>
              </button>
            );
          })}
        </nav>
      </aside>

      <style jsx>{`
        /* 사이드바 */
        .sidebar {
          width: 200px;
          background: #ffffff;
          border-right: 1px solid #e5e7eb;
          padding: 1.5rem 0;
          position: sticky;
          top: 60px;
          height: calc(100vh - 60px);
          overflow-y: auto;
        }

        .sidebar-nav {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
          padding: 0 1rem;
        }

        .sidebar-item {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 0.75rem 1rem;
          background: #ffffff;
          border: 1px solid #e5e7eb;
          border-radius: 0.5rem;
          cursor: pointer;
          transition: all 0.2s;
          text-align: left;
          font-size: 0.875rem;
          color: #6b7280;
        }

        .sidebar-item:hover {
          background: #f9fafb;
          border-color: #3b82f6;
          color: #1f2937;
        }

        .sidebar-item.active {
          background: #eff6ff;
          border-color: #3b82f6;
          color: #1f2937;
          font-weight: 600;
        }

        .sidebar-icon {
          font-size: 1.25rem;
        }

        .sidebar-label {
          flex: 1;
        }

        @media (max-width: 768px) {
          .sidebar {
            width: 100%;
            position: relative;
            top: 0;
            height: auto;
            border-right: none;
            border-bottom: 1px solid #e5e7eb;
          }

          .sidebar-nav {
            flex-direction: row;
            overflow-x: auto;
            padding: 0.5rem 1rem;
          }

          .sidebar-item {
            flex-shrink: 0;
            white-space: nowrap;
          }
        }
      `}</style>
    </>
  );
}
