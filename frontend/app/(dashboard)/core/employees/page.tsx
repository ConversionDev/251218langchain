"use client";

import { useEffect, useState, useCallback } from "react";
import { Plus, Users, ChevronLeft, ChevronRight } from "lucide-react";
import Link from "next/link";
import { useStore } from "@/store/useStore";
import { useHydrated } from "@/hooks/use-hydrated";
import {
  fetchEmployeesPaginated,
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
import { toast } from "sonner";
import { CORE_EMPLOYEES_MESSAGES } from "@/modules/shared/constants/messages";

const PAGE_SIZE = 20;

export default function CoreEmployeesPage() {
  const hydrated = useHydrated();
  const { addEmployee, updateEmployee, deleteEmployee, setSelectedEmployee, setEmployees, selectedEmployee, setAnalyzingEmployeeId } = useStore();
  const [employees, setEmployeesPage] = useState<Employee[]>([]);
  const [summaryEmployees, setSummaryEmployees] = useState<Employee[]>([]);
  const [allEmployees, setAllEmployees] = useState<Employee[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [nextId, setNextId] = useState("E001");
  const [modalOpen, setModalOpen] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState<Employee | null>(null);
  const [profileSheetOpen, setProfileSheetOpen] = useState(false);
  const [profileEmployeeId, setProfileEmployeeId] = useState<string | null>(null);
  const profileEmployee = profileEmployeeId ? employees.find((e) => e.id === profileEmployeeId) ?? null : null;

  const loadRegularSummary = useCallback(async () => {
    // 백엔드 regular 분류 기준을 단일 소스로 사용해 대시보드/목록 수치 불일치 제거
    const first = await fetchEmployeesPaginated({ page: 1, pageSize: 100, employmentType: "regular" });
    const totalCount = first.total ?? 0;
    const collected: Employee[] = [...(first.items ?? [])];
    const totalPages = Math.max(1, Math.ceil(totalCount / 100));
    if (totalPages > 1) {
      for (let p = 2; p <= totalPages; p++) {
        const next = await fetchEmployeesPaginated({ page: p, pageSize: 100, employmentType: "regular" });
        if (next.items?.length) collected.push(...next.items);
      }
    }
    setSummaryEmployees(collected);
  }, []);

  const loadAllEmployees = useCallback(async () => {
    const first = await fetchEmployeesPaginated({ page: 1, pageSize: 100 });
    const totalCount = first.total ?? 0;
    const collected: Employee[] = [...(first.items ?? [])];
    const totalPages = Math.max(1, Math.ceil(totalCount / 100));
    if (totalPages > 1) {
      for (let p = 2; p <= totalPages; p++) {
        const next = await fetchEmployeesPaginated({ page: p, pageSize: 100 });
        if (next.items?.length) collected.push(...next.items);
      }
    }
    setAllEmployees(collected);
  }, []);

  const loadPage = useCallback((p: number) => {
    setLoading(true);
    fetchEmployeesPaginated({ page: p, pageSize: PAGE_SIZE, employmentType: "regular" })
      .then(({ items, total: t }) => {
        const pageItems = Array.isArray(items) ? items : [];
        setEmployeesPage(pageItems);
        setTotal(typeof t === "number" ? t : 0);
        setEmployees(pageItems);
        setPage(p);
      })
      .catch(() => { setEmployeesPage([]); setSummaryEmployees([]); setTotal(0); })
      .finally(() => setLoading(false));
  }, [setEmployees]);

  useEffect(() => {
    if (!hydrated) return;
    loadPage(1);
    loadRegularSummary().catch(() => setSummaryEmployees([]));
    loadAllEmployees().catch(() => setAllEmployees([]));
  }, [hydrated, loadPage, loadRegularSummary, loadAllEmployees]);

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
        loadRegularSummary();
        loadAllEmployees();
      } else {
        const created = await createEmployeeApi(employee);
        addEmployee(created);
        loadPage(1);
        loadRegularSummary();
        loadAllEmployees();
      }
      setEditingEmployee(null);
      setModalOpen(false);
    } catch (e) {
      console.error(e);
      toast.error(e instanceof Error ? e.message : CORE_EMPLOYEES_MESSAGES.toast.saveFailed);
    }
  };

  const handleEdit = (emp: Employee) => {
    setEditingEmployee(emp);
    setModalOpen(true);
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm(CORE_EMPLOYEES_MESSAGES.confirm.deleteEmployee)) return;
    try {
      await deleteEmployeeApi(id);
      deleteEmployee(id);
      setSelectedEmployee(null);
      const nextPage = employees.length <= 1 && page > 1 ? page - 1 : page;
      loadPage(nextPage);
      loadRegularSummary();
      loadAllEmployees();
    } catch (e) {
      console.error(e);
      toast.error(e instanceof Error ? e.message : CORE_EMPLOYEES_MESSAGES.toast.deleteFailed);
    }
  };

  const handleAnalyze = async (emp: Employee) => {
    setAnalyzingEmployeeId(emp.id);
    try {
      await analyzeEmployeeResumeApi(emp.id);
      toast.success(CORE_EMPLOYEES_MESSAGES.toast.analyzeSuccess(emp.name));
      loadPage(page);
      loadRegularSummary();
      loadAllEmployees();
    } catch (e) {
      console.error(e);
      toast.error(e instanceof Error ? e.message : CORE_EMPLOYEES_MESSAGES.toast.analyzeFailed);
    } finally {
      setAnalyzingEmployeeId(null);
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
            <span className="text-xs">{CORE_EMPLOYEES_MESSAGES.header.flow}</span>
          </div>
          <h1 className="text-2xl font-bold text-foreground">{CORE_EMPLOYEES_MESSAGES.header.title}</h1>
          <p className="mt-1 text-muted-foreground">
            {CORE_EMPLOYEES_MESSAGES.header.descriptionPrefix}{" "}
            <Link href="/core/new-hires" className="text-primary underline hover:no-underline">
              {CORE_EMPLOYEES_MESSAGES.header.newHireLinkLabel}
            </Link>
            {CORE_EMPLOYEES_MESSAGES.header.descriptionTail}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button onClick={handleAddNew} variant="outline" className="inline-flex items-center gap-2">
            <Plus className="h-4 w-4" />
            {CORE_EMPLOYEES_MESSAGES.buttons.addEmployee}
          </Button>
        </div>
      </div>

      <ISOComplianceDashboard employees={summaryEmployees} deptEmployees={allEmployees} />

      <section className="rounded-xl border border-border bg-card px-5 py-6 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 className="text-lg font-semibold text-foreground">{CORE_EMPLOYEES_MESSAGES.section.listTitle}</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              {CORE_EMPLOYEES_MESSAGES.section.listDescription}
            </p>
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span>{CORE_EMPLOYEES_MESSAGES.section.totalLabel(total)}</span>
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
              {CORE_EMPLOYEES_MESSAGES.section.loading}
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
