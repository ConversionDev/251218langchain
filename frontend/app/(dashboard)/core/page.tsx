"use client";

import { useEffect, useState } from "react";
import { Plus, Database } from "lucide-react";
import { useStore } from "@/store/useStore";
import { useHydrated } from "@/hooks/use-hydrated";
import { INITIAL_EMPLOYEES } from "@/modules/core/services";
import { ISOComplianceDashboard } from "@/modules/core/components/ISOComplianceDashboard";
import { EmployeeListTable } from "@/modules/core/components/EmployeeListTable";
import { EmployeeFormModal } from "@/modules/core/components/EmployeeFormModal";
import { ProfileSheet } from "@/modules/hr-profile/components";
import { Button } from "@/components/ui/button";
import type { Employee } from "@/modules/shared/types";

export default function CorePage() {
  const hydrated = useHydrated();
  const { employees, setEmployees, addEmployee, updateEmployee, deleteEmployee, setSelectedEmployee } = useStore();
  const [modalOpen, setModalOpen] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState<Employee | null>(null);
  const [profileSheetOpen, setProfileSheetOpen] = useState(false);
  const [profileEmployeeId, setProfileEmployeeId] = useState<string | null>(null);
  const profileEmployee = profileEmployeeId ? employees.find((e) => e.id === profileEmployeeId) ?? null : null;

  // 초기 로드 시: 목데이터(E001~E010)에 있는 직원은 항상 INITIAL_EMPLOYEES 기준으로 덮어써
  // 수아·미래 등 학력/경력이 항상 표시되도록 함 (persist에 resume 없이 저장된 경우 대비)
  useEffect(() => {
    if (!hydrated) return;
    if (employees.length === 0) {
      setEmployees(INITIAL_EMPLOYEES);
      return;
    }
    const initialById = new Map(INITIAL_EMPLOYEES.map((e) => [e.id, e]));
    const merged = employees.map((e) => {
      const seed = initialById.get(e.id);
      if (!seed) return e;
      return seed;
    });
    const changed =
      merged.length !== employees.length ||
      merged.some((e, i) => e !== employees[i]);
    if (changed) setEmployees(merged);
  }, [hydrated, employees, setEmployees]);

  const nextId = (() => {
    const ids = employees.map((e) => e.id);
    const num = ids
      .map((s) => parseInt(s.replace(/\D/g, ""), 10))
      .filter((n) => !Number.isNaN(n));
    const max = num.length ? Math.max(...num) : 10;
    return `E${String(max + 1).padStart(3, "0")}`;
  })();

  const handleSave = (employee: Employee) => {
    if (editingEmployee) {
      updateEmployee(employee.id, employee);
    } else {
      addEmployee(employee);
    }
    setEditingEmployee(null);
    setModalOpen(false);
  };

  const handleEdit = (emp: Employee) => {
    setEditingEmployee(emp);
    setModalOpen(true);
  };

  const handleDelete = (id: string) => {
    if (window.confirm("이 직원 데이터를 삭제할까요?")) {
      deleteEmployee(id);
      setSelectedEmployee(null);
    }
  };

  const handleAddNew = () => {
    setEditingEmployee(null);
    setModalOpen(true);
  };

  const handleOpenProfile = (emp: Employee) => {
    setProfileEmployeeId(emp.id);
    setProfileSheetOpen(true);
  };

  if (!hydrated) {
    return (
      <div className="space-y-8">
        <div className="h-10 w-48 animate-pulse rounded bg-muted" />
        <div className="grid gap-4 md:grid-cols-3">
          <div className="h-28 animate-pulse rounded-xl bg-muted/50" />
          <div className="h-28 animate-pulse rounded-xl bg-muted/50" />
          <div className="h-28 animate-pulse rounded-xl bg-muted/50" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="mb-1.5 flex items-center gap-2 text-muted-foreground">
            <Database className="h-3.5 w-3.5 shrink-0" />
            <span className="text-xs">Structured Root: ISO-30414 표준 기반 인사 정형 데이터 시스템</span>
          </div>
          <h1 className="text-2xl font-bold text-foreground">Core HR</h1>
          <p className="mt-1 text-muted-foreground">
            ISO 30414 인적 자본 공시 준수 현황
          </p>
        </div>
        <Button onClick={handleAddNew} className="inline-flex items-center gap-2">
          <Plus className="h-4 w-4" />
          직원 등록
        </Button>
      </div>

      <ISOComplianceDashboard employees={employees.length > 0 ? employees : INITIAL_EMPLOYEES} />

      <section className="rounded-xl border border-border bg-card p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-foreground">직원 리스트</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          행 클릭 또는 상세 버튼으로 이력 상세를 확인할 수 있습니다. 수정/삭제는 행 내 버튼을 사용하세요.
        </p>
        <div className="mt-4">
          <EmployeeListTable
            employees={employees}
            onEdit={handleEdit}
            onDelete={handleDelete}
            onOpenProfile={handleOpenProfile}
          />
        </div>
      </section>

      <ProfileSheet
        employee={profileEmployee}
        open={profileSheetOpen}
        onOpenChange={(open) => {
          setProfileSheetOpen(open);
          if (!open) setProfileEmployeeId(null);
        }}
        onResumeUpdate={(id, resume) => updateEmployee(id, { resume })}
      />

      <EmployeeFormModal
        open={modalOpen}
        onOpenChange={(open) => {
          setModalOpen(open);
          if (!open) setEditingEmployee(null);
        }}
        employee={editingEmployee}
        onSave={handleSave}
        nextId={nextId}
      />
    </div>
  );
}
