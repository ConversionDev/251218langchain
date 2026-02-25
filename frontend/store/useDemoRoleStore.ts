"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

/** 포트폴리오 시연용: 현재 체험 중인 역할 (실제 인증 없음) */
export type DemoRole = "admin" | "employee" | "applicant";

export interface DemoRoleState {
  demoRole: DemoRole | null;
}

export interface DemoRoleActions {
  setDemoRole: (role: DemoRole | null) => void;
}

export type DemoRoleStore = DemoRoleState & DemoRoleActions;

export const DEMO_ROLE_CONFIG: Record<
  DemoRole,
  { label: string; shortLabel: string; path: string }
> = {
  admin: { label: "관리자", shortLabel: "관리자", path: "/dashboard" },
  employee: { label: "일반직원", shortLabel: "일반직원", path: "/workspace" },
  applicant: { label: "일반사용자", shortLabel: "일반사용자", path: "/careers" },
};

export const useDemoRoleStore = create<DemoRoleStore>()(
  persist(
    (set) => ({
      demoRole: null,
      setDemoRole: (role) => set({ demoRole: role }),
    }),
    {
      name: "success-dna-demo-role",
      partialize: (state) => ({ demoRole: state.demoRole }),
    }
  )
);
