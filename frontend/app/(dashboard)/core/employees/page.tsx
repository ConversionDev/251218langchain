"use client";

import { useEffect, useState, useCallback } from "react";
import { Plus, Users, ChevronLeft, ChevronRight } from "lucide-react";
import Link from "next/link";
import { useStore } from "@/store/useStore";
import { useHydrated } from "@/hooks/use-hydrated";
import {
  fetchEmployeesPaginated,
  fetchEmployees,
  fetchNextEmployeeId,
  createEmployeeApi,
  analyzeEmployeeResumeApi,
  updateEmployeeApi,
  deleteEmployeeApi,
} from "@/modules/core/services";
import { ISOComplianceDashboard } from "@/modules/core/components/ISOComplianceDashboard";
import { EmployeeListTable } from "@/modules/core/components/EmployeeListTable";
import { EmployeeFormModal } from "@/modules/core/components/EmployeeFormModal";
import { ProfileSheet } from "@/modules/hr-profile/components";
import { Button } from "@/components/ui/button";
import type { Employee } from "@/modules/shared/types";

const PAGE_SIZE = 20;

export default function CoreEmployeesPage() {
  const hydrated = useHydrated();
  const { addEmployee, updateEmployee, deleteEmployee, setSelectedEmployee, setEmployees, selectedEmployee } = useStore();
  const [employees, setEmployeesPage] = useState<Employee[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [nextId, setNextId] = useState("E001");
  const [modalOpen, setModalOpen] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState<Employee | null>(null);
  const [profileSheetOpen, setProfileSheetOpen] = useState(false);
  const [profileEmployeeId, setProfileEmployeeId] = useState<string | null>(null);
  const profileEmployee = profileEmployeeId ? employees.find((e) => e.id === profileEmployeeId) ?? null : null;

  const loadPage = useCallback((p: number) => {
    setLoading(true);
    fetchEmployeesPaginated({ page: p, pageSize: PAGE_SIZE, employmentType: "regular" })
      .then(async ({ items, total: t }) => {
        // 백엔드 필터/이관 상태 차이로 regular 결과가 비는 경우를 대비한 프론트 폴백
        if ((t ?? 0) > 0) {
          const pageItems = Array.isArray(items) ? items : [];
          setEmployeesPage(pageItems);
          setTotal(typeof t === "number" ? t : 0);
          setEmployees(pageItems);
          setPage(p);
          return;
        }
        const all = await fetchEmployees();
        const regular = (all ?? []).filter((e) => {
          const type = (e.employmentType ?? "").trim().toLowerCase();
          const status = (e.status ?? "").trim().toLowerCase();
          if (type === "new_hire") return false;
          // ATS 후보만 제외. hired는 기존 직원으로 허용.
          return !["pending", "screening", "rejected"].includes(status);
        });
        const start = (p - 1) * PAGE_SIZE;
        const end = start + PAGE_SIZE;
        const pageItems = regular.slice(start, end);
        setEmployeesPage(pageItems);
        setTotal(regular.length);
        setEmployees(regular);
        setPage(p);
      })
      .catch(() => { setEmployeesPage([]); setTotal(0); })
      .finally(() => setLoading(false));
  }, [setEmployees]);

  useEffect(() => {
    if (!hydrated) return;
    loadPage(1);
  }, [hydrated, loadPage]);

  useEffect(() => {
    if (!hydrated || !selectedEmployee) return;
    const exists = employees.some((e) => e.id === selectedEmployee.id);
    // 기존 직원 목록이 비어 있을 때만 stale 선택값 정리 (페이지네이션에 없는 정상 선택값은 유지)
    if (!exists && total === 0) setSelectedEmployee(null);
  }, [hydrated, selectedEmployee, employees, total, setSelectedEmployee]);

  const handleAddNew = () => {
    fetchNextEmployeeId()
      .then((id) => {
        setNextId(id);
        setEditingEmployee(null);
        setModalOpen(true);
      })
      .catch(() => { setEditingEmployee(null); setModalOpen(true); });
  };

  const handleSave = async (employee: Employee) => {
    try {
      if (editingEmployee) {
        const updated = await updateEmployeeApi(employee.id, employee);
        updateEmployee(employee.id, updated);
        loadPage(page);
      } else {
        const created = await createEmployeeApi(employee);
        addEmployee(created);
        loadPage(1);
      }
      setEditingEmployee(null);
      setModalOpen(false);
    } catch (e) {
      console.error(e);
      alert(e instanceof Error ? e.message : "저장에 실패했습니다.");
    }
  };

  const handleEdit = (emp: Employee) => {
    setEditingEmployee(emp);
    setModalOpen(true);
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm("이 직원 데이터를 삭제할까요?")) return;
    try {
      await deleteEmployeeApi(id);
      deleteEmployee(id);
      setSelectedEmployee(null);
      const nextPage = employees.length <= 1 && page > 1 ? page - 1 : page;
      loadPage(nextPage);
    } catch (e) {
      console.error(e);
      alert(e instanceof Error ? e.message : "삭제에 실패했습니다.");
    }
  };

  const handleAnalyze = async (emp: Employee) => {
    try {
      await analyzeEmployeeResumeApi(emp.id);
      alert(`${emp.name} AI 분석이 완료되었습니다.`);
      loadPage(page);
    } catch (e) {
      console.error(e);
      alert(e instanceof Error ? e.message : "AI 분석에 실패했습니다.");
    }
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
            <Users className="h-3.5 w-3.5 shrink-0" />
            <span className="text-xs">등록된 직원 목록 · 수정/삭제</span>
          </div>
          <h1 className="text-2xl font-bold text-foreground">기존 직원 관리</h1>
          <p className="mt-1 text-muted-foreground">
            DB에 등록된 직원의 이력·공시 지표를 조회·수정합니다. 신입은{" "}
            <Link href="/core/new-hires" className="text-primary underline hover:no-underline">
              신입 관리
            </Link>
            에서 등록하세요.
          </p>
        </div>
        <Button onClick={handleAddNew} variant="outline" className="inline-flex items-center gap-2">
          <Plus className="h-4 w-4" />
          직원 추가
        </Button>
      </div>

      <ISOComplianceDashboard employees={employees} />

      <section className="rounded-xl border border-border bg-card px-5 py-6 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 className="text-lg font-semibold text-foreground">직원 리스트</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              이름을 제외한 행 영역 또는 상세(문서) 버튼을 클릭하면 이력 상세가 열립니다. 수정/삭제는 행 내 버튼을 사용하세요.
            </p>
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span>전체 {total}명</span>
            <div className="flex items-center gap-1">
              <Button
                variant="outline"
                size="icon"
                className="h-8 w-8"
                disabled={page <= 1 || loading}
                onClick={() => loadPage(page - 1)}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <span className="min-w-[6rem] text-center">
                {total ? `${(page - 1) * PAGE_SIZE + 1}-${Math.min(page * PAGE_SIZE, total)}` : "0"} / {total}
              </span>
              <Button
                variant="outline"
                size="icon"
                className="h-8 w-8"
                disabled={page * PAGE_SIZE >= total || loading}
                onClick={() => loadPage(page + 1)}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
        <div className="mt-4">
          {loading ? (
            <div className="flex h-32 items-center justify-center rounded border border-border bg-muted/20 text-sm text-muted-foreground">
              로딩 중…
            </div>
          ) : (
            <EmployeeListTable
              employees={employees}
              onAnalyze={handleAnalyze}
              onEdit={handleEdit}
              onDelete={handleDelete}
              onOpenProfile={handleOpenProfile}
            />
          )}
        </div>
      </section>

      <ProfileSheet
        employee={profileEmployee}
        open={profileSheetOpen}
        onOpenChange={(open) => {
          setProfileSheetOpen(open);
          if (!open) setProfileEmployeeId(null);
        }}
        onResumeUpdate={async (id, resume) => {
          try {
            const updated = await updateEmployeeApi(id, { resume });
            updateEmployee(id, updated);
          } catch (e) {
            console.error(e);
          }
        }}
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
