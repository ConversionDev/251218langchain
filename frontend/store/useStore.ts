import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Employee } from "@/modules/shared/types";

/**
 * Core에서 수정 시: updateEmployee(id, payload)가 employees와
 * selectedEmployee(id 일치 시)를 함께 갱신하므로, Intelligence/ Credential이
 * 동일 스토어를 참조하면 즉시 반영됩니다.
 * payload에는 resume(이력서), matchedDepartment(추천 부서) 등 Partial<Employee> 전체를 넘길 수 있습니다.
 */

export interface AppState {
  /** 현재 대시보드에서 조회 중인 직원 */
  selectedEmployee: Employee | null;
  /** 외부 공시(ISO/IFRS) 지표 가시화 여부 */
  isDisclosureMode: boolean;
  /** 직원 목록 (Core CRUD) */
  employees: Employee[];
}

export interface AppActions {
  setSelectedEmployee: (employee: Employee | null) => void;
  setDisclosureMode: (value: boolean) => void;
  toggleDisclosureMode: () => void;
  setEmployees: (employees: Employee[]) => void;
  addEmployee: (employee: Employee) => void;
  updateEmployee: (id: string, employee: Partial<Employee>) => void;
  deleteEmployee: (id: string) => void;
}

export type AppStore = AppState & AppActions;

const initialState: AppState = {
  selectedEmployee: null,
  isDisclosureMode: false,
  employees: [],
};

export const useStore = create<AppStore>()(
  persist(
    (set) => ({
      ...initialState,
      setSelectedEmployee: (employee) => set({ selectedEmployee: employee }),
      setDisclosureMode: (value) => set({ isDisclosureMode: value }),
      toggleDisclosureMode: () =>
        set((state) => ({ isDisclosureMode: !state.isDisclosureMode })),
      setEmployees: (employees) => set({ employees }),
      addEmployee: (employee) =>
        set((state) => ({ employees: [...state.employees, employee] })),
      updateEmployee: (id, payload) =>
        set((state) => {
          const nextEmployees = state.employees.map((e) =>
            e.id === id ? { ...e, ...payload } : e
          );
          const nextSelected =
            state.selectedEmployee?.id === id
              ? { ...state.selectedEmployee, ...payload }
              : state.selectedEmployee;
          return {
            employees: nextEmployees,
            selectedEmployee: nextSelected,
          };
        }),
      deleteEmployee: (id) =>
        set((state) => ({
          employees: state.employees.filter((e) => e.id !== id),
          selectedEmployee: state.selectedEmployee?.id === id ? null : state.selectedEmployee,
        })),
    }),
    {
      name: "success-dna-store",
      partialize: (state) => ({
        selectedEmployee: state.selectedEmployee,
        employees: state.employees,
      }),
    }
  )
);
