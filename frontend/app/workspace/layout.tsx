import { WorkspaceLayoutClient } from "@/components/layout/WorkspaceLayoutClient";

/** 직원 업무 공간 전용 레이아웃 — 관리자 대시보드와 분리. */
export default function WorkspaceLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <WorkspaceLayoutClient>{children}</WorkspaceLayoutClient>;
}
