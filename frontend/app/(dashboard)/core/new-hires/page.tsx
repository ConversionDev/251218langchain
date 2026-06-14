"use client";

import { useEffect, useMemo, useState, useCallback } from "react";
import { toast } from "sonner";
import {
  FileUp,
  UserPlus,
  Sparkles,
  CheckCircle,
  XCircle,
  ChevronLeft,
  ChevronRight,
  Pencil,
  Trash2,
} from "lucide-react";
import Link from "next/link";
import { useStore } from "@/store/useStore";
import { useHydrated } from "@/hooks/use-hydrated";
import {
  fetchEmployeesPaginated,
  fetchNextEmployeeId,
  createEmployeeApi,
  deleteEmployeeApi,
  analyzeEmployeeResumeApi,
  updateEmployeeApi,
} from "@/modules/core/services";
import { EmployeeFormModal } from "@/modules/core/components/EmployeeFormModal";
import { NewHireCompareDialog } from "@/modules/core/components/NewHireCompareDialog";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type { Employee, RecruitStatus } from "@/modules/shared/types";
import { NEW_HIRE_STATUS_LABELS, NEW_HIRES_MESSAGES } from "@/modules/shared/constants/messages";

function formatAppDate(s: string | undefined): string {
  if (!s) return "—";
  const d = new Date(s);
  if (Number.isNaN(d.getTime())) return s;
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  if (s.includes("T") || s.length > 10) {
    const h = String(d.getHours()).padStart(2, "0");
    const min = String(d.getMinutes()).padStart(2, "0");
    return `${y}.${m}.${day} ${h}:${min}`;
  }
  return `${y}.${m}.${day}`;
}

const PAGE_SIZE = 20;

/** 신입 관리: 입사 대상을 고르는 페이지. 이력서 업로드 → 분석 → 등록 시 신입 목록에서 관리 */
export default function CoreNewHiresPage() {
  const hydrated = useHydrated();
  const { addEmployee, updateEmployee, deleteEmployee, analyzingEmployeeId, setAnalyzingEmployeeId, setSelectedEmployee } = useStore();
  const [newHires, setNewHires] = useState<Employee[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [nextId, setNextId] = useState("E001");
  const [modalOpen, setModalOpen] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState<Employee | null>(null);
  const [justRegistered, setJustRegistered] = useState<string | null>(null);

  const loadPage = useCallback((p: number, search?: string) => {
    const term = (search ?? "").trim();
    setLoading(true);
    // 검색 시에는 전체 신입 대상으로 조회(현재 페이지 한정 아님). 매칭 결과를 넉넉히 가져옴.
    fetchEmployeesPaginated({ page: p, pageSize: term ? 100 : PAGE_SIZE, employmentType: "new_hire", search: term || undefined })
      .then(({ items, total: t }) => {
        setNewHires(Array.isArray(items) ? items : []);
        setTotal(typeof t === "number" ? t : 0);
        setPage(p);
      })
      .catch(() => { setNewHires([]); setTotal(0); })
      .finally(() => setLoading(false));
  }, []);

  const list = newHires ?? [];

  const [compareCandidate, setCompareCandidate] = useState<Employee | null>(null);
  const [filterName, setFilterName] = useState("");
  const [filterDept, setFilterDept] = useState("");

  // 초기 로드 + 서버 검색(디바운스): 이름/부서로 전체 신입을 검색 (현재 페이지 한정 아님)
  useEffect(() => {
    if (!hydrated) return;
    const term = filterName.trim() || filterDept.trim();
    const t = setTimeout(() => loadPage(1, term), term ? 300 : 0);
    return () => clearTimeout(t);
  }, [filterName, filterDept, hydrated, loadPage]);

  const refreshList = () => loadPage(page);

  const filteredList = useMemo(() => {
    return list.filter((e) => {
      const matchName = !filterName.trim() || (e.name ?? "").toLowerCase().includes(filterName.trim().toLowerCase());
      const matchDept = !filterDept.trim() || (e.department ?? "").toLowerCase().includes(filterDept.trim().toLowerCase());
      return matchName && matchDept;
    });
  }, [list, filterName, filterDept]);

  const byStatus = useMemo(() => {
    const statusKey = (s: RecruitStatus | null | undefined) => s || "pending";
    const map: Record<string, Employee[]> = { pending: [], screening: [], hired: [], rejected: [] };
    for (const e of filteredList) {
      const key = statusKey(e.status);
      if (map[key]) map[key].push(e);
      else map.pending.push(e);
    }
    return map;
  }, [filteredList]);
  const kpis = useMemo(
    () => [
      { label: NEW_HIRES_MESSAGES.kpi.totalApplicants, value: total },
      { label: NEW_HIRES_MESSAGES.kpi.screening, value: byStatus.screening.length },
      { label: NEW_HIRES_MESSAGES.kpi.hired, value: byStatus.hired.length },
      { label: NEW_HIRES_MESSAGES.kpi.rejected, value: byStatus.rejected.length },
    ],
    [total, byStatus]
  );

  const [activeTab, setActiveTab] = useState<string>("pending");
  const [updatingId, setUpdatingId] = useState<string | null>(null);
  const [reasonDialogEmp, setReasonDialogEmp] = useState<Employee | null>(null);
  const [reasonEditText, setReasonEditText] = useState("");
  const [rejectDialogEmp, setRejectDialogEmp] = useState<Employee | null>(null);
  const [rejectReasonText, setRejectReasonText] = useState("");

  const handleSelectForIntelligence = (emp: Employee) => {
    setSelectedEmployee(emp);
    window.location.href = "/intelligence";
  };

  const handleAnalyze = async (emp: Employee, opts?: { force?: boolean }) => {
    setAnalyzingEmployeeId(emp.id);
    try {
      const result = await analyzeEmployeeResumeApi(emp.id, opts);
      if (result.analysisSkipped) {
        toast.success(NEW_HIRES_MESSAGES.toast.promoteScreening(emp.name));
      } else {
        toast.success(NEW_HIRES_MESSAGES.toast.analyzeSuccess(emp.name));
      }
      refreshList();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : NEW_HIRES_MESSAGES.toast.analyzeFailed);
    } finally {
      setAnalyzingEmployeeId(null);
    }
  };

  const handleReanalyzeConfirm = (emp: Employee) => {
    if (!window.confirm(NEW_HIRES_MESSAGES.confirm.reanalyzeAi(emp.name))) return;
    void handleAnalyze(emp, { force: true });
  };

  const handleSetStatus = async (emp: Employee, status: RecruitStatus, rejectionReason?: string | null) => {
    setUpdatingId(emp.id);
    try {
      await updateEmployeeApi(emp.id, { status, ...(rejectionReason !== undefined && { rejectionReason }) });
      toast.success(NEW_HIRES_MESSAGES.toast.statusUpdated(emp.name, status));
      refreshList();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : NEW_HIRES_MESSAGES.toast.statusUpdateFailed);
    } finally {
      setUpdatingId(null);
    }
  };

  const handleSaveReason = async () => {
    if (!reasonDialogEmp) return;
    setUpdatingId(reasonDialogEmp.id);
    try {
      await updateEmployeeApi(reasonDialogEmp.id, { successDnaReason: reasonEditText.trim() || null });
      toast.success(NEW_HIRES_MESSAGES.toast.reasonSaved);
      refreshList();
      setReasonDialogEmp(null);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : NEW_HIRES_MESSAGES.toast.saveFailed);
    } finally {
      setUpdatingId(null);
    }
  };

  const handleRejectConfirm = async () => {
    if (!rejectDialogEmp) return;
    await handleSetStatus(rejectDialogEmp, "rejected", rejectReasonText.trim() || null);
    setRejectDialogEmp(null);
    setRejectReasonText("");
  };


  const handleSave = async (employee: Employee) => {
    try {
      if (editingEmployee) {
        const updated = await updateEmployeeApi(employee.id, employee);
        updateEmployee(employee.id, updated);
        toast.success(NEW_HIRES_MESSAGES.toast.infoUpdated(updated.name));
        loadPage(page);
      } else {
        const created = await createEmployeeApi(employee);
        addEmployee(created);
        setJustRegistered(created.id);
        loadPage(1);
        fetchNextEmployeeId().then(setNextId).catch(() => {});
      }
      setEditingEmployee(null);
    } catch (e) {
      const err = e as Error & { existing?: Employee };
      if (
        err.message?.includes("동일한 이력서") ||
        err.message?.includes("이미 등록된") ||
        (err as { existing?: unknown }).existing
      ) {
        const name = err.existing?.name ?? employee.name;
        toast.warning(NEW_HIRES_MESSAGES.toast.duplicateResume(name));
        return;
      }
      console.error(e);
      toast.error(e instanceof Error ? e.message : NEW_HIRES_MESSAGES.toast.createFailed);
    }
  };

  const handleOpenModal = () => {
    setJustRegistered(null);
    setEditingEmployee(null);
    fetchNextEmployeeId()
      .then((id) => { setNextId(id); setModalOpen(true); })
      .catch(() => setModalOpen(true));
  };

  const handleEdit = (emp: Employee) => {
    setEditingEmployee(emp);
    setModalOpen(true);
  };

  const handleDelete = async (emp: Employee) => {
    if (!window.confirm(NEW_HIRES_MESSAGES.confirm.deleteApplicant(emp.name))) return;
    setUpdatingId(emp.id);
    try {
      await deleteEmployeeApi(emp.id);
      deleteEmployee(emp.id);
      toast.success(NEW_HIRES_MESSAGES.toast.deleted(emp.name));
      const currentCount = byStatus[activeTab]?.length ?? 0;
      const nextPage = currentCount <= 1 && page > 1 ? page - 1 : page;
      loadPage(nextPage);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : NEW_HIRES_MESSAGES.toast.deleteFailed);
    } finally {
      setUpdatingId(null);
    }
  };

  const handleOnboardToRegular = async (emp: Employee) => {
    if (!window.confirm(NEW_HIRES_MESSAGES.confirm.onboardApplicant(emp.name))) return;
    setUpdatingId(emp.id);
    try {
      const today = new Date();
      const joinedAt = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;
      await updateEmployeeApi(emp.id, {
        employmentType: "regular",
        joinedAt,
        status: null,
      });
      toast.success(NEW_HIRES_MESSAGES.toast.onboarded(emp.name));
      loadPage(page);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : NEW_HIRES_MESSAGES.toast.onboardFailed);
    } finally {
      setUpdatingId(null);
    }
  };

  if (!hydrated) {
    return (
      <div className="space-y-8">
        <div className="h-10 w-48 animate-pulse rounded bg-muted" />
        <div className="h-64 animate-pulse rounded-xl bg-muted/50" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <div className="mb-1.5 flex items-center gap-2 text-muted-foreground">
          <UserPlus className="h-3.5 w-3.5 shrink-0" />
          <span className="text-xs">{NEW_HIRES_MESSAGES.header.flow}</span>
        </div>
        <h1 className="text-2xl font-bold text-foreground">{NEW_HIRES_MESSAGES.header.title}</h1>
        <p className="mt-1 text-muted-foreground">
          {NEW_HIRES_MESSAGES.header.descriptionPrefix}{" "}
          <strong>{NEW_HIRES_MESSAGES.header.descriptionEmphasis}</strong>{" "}
          {NEW_HIRES_MESSAGES.header.descriptionSuffix}{" "}
          <Link href="/core/employees" className="text-primary underline hover:no-underline">
            {NEW_HIRES_MESSAGES.header.existingEmployeesLinkLabel}
          </Link>
          {NEW_HIRES_MESSAGES.header.descriptionTail}
        </p>
      </div>

      <section className="grid gap-4 md:grid-cols-4">
        {kpis.map((k) => (
          <div key={k.label} className="rounded-xl border border-border bg-card p-4 shadow-sm">
            <p className="text-sm text-muted-foreground">{k.label}</p>
            <p className="text-2xl font-bold text-foreground">{k.value}명</p>
          </div>
        ))}
      </section>

      <section className="rounded-xl border border-border bg-card p-5 shadow-sm">
        <div className="flex flex-col items-center justify-center gap-3 text-center sm:flex-row sm:justify-between sm:text-left">
          <div className="flex items-start gap-3">
            <div className="rounded-full bg-primary/10 p-2.5">
              <FileUp className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-foreground">{NEW_HIRES_MESSAGES.section.registerTitle}</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                {NEW_HIRES_MESSAGES.section.registerDescription}
              </p>
            </div>
          </div>
          <div className="flex flex-col items-center gap-2 sm:items-end">
            <Button onClick={handleOpenModal} className="inline-flex items-center gap-2">
              <FileUp className="h-4 w-4" />
              {NEW_HIRES_MESSAGES.section.registerButton}
            </Button>
            {justRegistered && (
              <p className="text-xs text-green-600 dark:text-green-400">
                {NEW_HIRES_MESSAGES.section.registerDoneHint}
              </p>
            )}
          </div>
        </div>
      </section>

      <section className="rounded-xl border border-border bg-card px-5 py-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-foreground">{NEW_HIRES_MESSAGES.section.atsTitle}</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              {NEW_HIRES_MESSAGES.section.atsDescription}
            </p>
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span>{NEW_HIRES_MESSAGES.section.totalLabel(total)}</span>
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
            <Button variant="outline" size="sm" onClick={() => loadPage(page)} disabled={loading}>
              {NEW_HIRES_MESSAGES.section.refresh}
            </Button>
          </div>
        </div>
        {loading && list.length === 0 ? (
          <div className="flex h-32 items-center justify-center rounded border border-border bg-muted/20 text-sm text-muted-foreground">
            {NEW_HIRES_MESSAGES.section.loading}
          </div>
        ) : list.length === 0 ? (
          <p className="rounded border border-border bg-muted/30 px-4 py-8 text-center text-sm text-muted-foreground">
            {NEW_HIRES_MESSAGES.section.emptyListLead} <strong>{NEW_HIRES_MESSAGES.section.emptyListRefresh}</strong>{" "}
            {NEW_HIRES_MESSAGES.section.emptyListTail}
            <br />
            <span className="mt-2 block text-xs">{NEW_HIRES_MESSAGES.section.emptyListHint}</span>
          </p>
        ) : (
          <>
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <div className="mb-3 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                <div className="flex flex-wrap items-center gap-2">
                  <div className="flex items-center gap-2">
                    <Label htmlFor="newhire-filter-name" className="text-sm">이름</Label>
                    <Input
                      id="newhire-filter-name"
                      type="text"
                      value={filterName}
                      onChange={(e) => setFilterName(e.target.value)}
                      placeholder={NEW_HIRES_MESSAGES.input.searchPlaceholder}
                      className="h-8 w-40"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <Label htmlFor="newhire-filter-dept" className="text-sm">부서</Label>
                    <Input
                      id="newhire-filter-dept"
                      type="text"
                      value={filterDept}
                      onChange={(e) => setFilterDept(e.target.value)}
                      placeholder={NEW_HIRES_MESSAGES.input.searchPlaceholder}
                      className="h-8 w-40"
                    />
                  </div>
                </div>
                <TabsList className="h-9 w-fit max-w-full overflow-x-auto">
                  <TabsTrigger value="pending" className="whitespace-nowrap">
                    {NEW_HIRES_MESSAGES.tabs.pending} ({byStatus.pending.length})
                  </TabsTrigger>
                  <TabsTrigger value="screening" className="whitespace-nowrap">
                    {NEW_HIRES_MESSAGES.tabs.screening} ({byStatus.screening.length})
                  </TabsTrigger>
                  <TabsTrigger value="hired" className="whitespace-nowrap">
                    {NEW_HIRES_MESSAGES.tabs.hired} ({byStatus.hired.length})
                  </TabsTrigger>
                  <TabsTrigger value="rejected" className="whitespace-nowrap">
                    {NEW_HIRES_MESSAGES.tabs.rejected} ({byStatus.rejected.length})
                  </TabsTrigger>
                </TabsList>
              </div>
            {(["pending", "screening", "hired", "rejected"] as const).map((tab) => (
              <TabsContent key={tab} value={tab} className="mt-0">
                <div className="overflow-x-auto rounded border border-border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>{NEW_HIRES_MESSAGES.table.headers.name}</TableHead>
                        <TableHead>{NEW_HIRES_MESSAGES.table.headers.department}</TableHead>
                        <TableHead>{NEW_HIRES_MESSAGES.table.headers.jobTitle}</TableHead>
                        <TableHead>{NEW_HIRES_MESSAGES.table.headers.applicationDate}</TableHead>
                        <TableHead>{NEW_HIRES_MESSAGES.table.headers.status}</TableHead>
                        {tab === "rejected" && <TableHead>{NEW_HIRES_MESSAGES.table.headers.rejectionReason}</TableHead>}
                        <TableHead className="min-w-[260px] text-right">{NEW_HIRES_MESSAGES.table.headers.actions}</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {byStatus[tab].length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={tab === "rejected" ? 7 : 6} className="text-center text-muted-foreground py-8">
                            {NEW_HIRES_MESSAGES.section.empty}
                          </TableCell>
                        </TableRow>
                      ) : (
                        byStatus[tab].map((emp) => (
                          <TableRow key={emp.id}>
                            <TableCell className="font-medium">
                              <button
                                type="button"
                                className="text-left underline-offset-2 hover:underline"
                                onClick={() => handleSelectForIntelligence(emp)}
                                title={NEW_HIRES_MESSAGES.table.nameTitle}
                              >
                                {emp.name}
                              </button>
                            </TableCell>
                            <TableCell>{emp.department || "—"}</TableCell>
                            <TableCell>{emp.jobTitle || "—"}</TableCell>
                            <TableCell>{formatAppDate(emp.applicationDate)}</TableCell>
                            <TableCell>{NEW_HIRE_STATUS_LABELS[(emp.status || "pending") as RecruitStatus]}</TableCell>
                            {tab === "rejected" && (
                              <TableCell className="max-w-[200px] truncate text-muted-foreground" title={emp.rejectionReason ?? undefined}>
                                {emp.rejectionReason || "—"}
                              </TableCell>
                            )}
                            <TableCell className="min-w-[260px] text-right align-middle">
                              <div className="ml-auto inline-flex flex-wrap items-center justify-end gap-1">
                                {tab === "pending" && (
                                  <div className="flex flex-col items-end gap-1">
                                    <div className="inline-flex flex-nowrap items-center justify-end gap-1">
                                      <Button
                                        variant="outline"
                                        size="sm"
                                        disabled={analyzingEmployeeId !== null}
                                        onClick={() => handleAnalyze(emp)}
                                        className="h-8 w-[86px] justify-center whitespace-nowrap px-2 text-xs"
                                        title={
                                          emp.successDna
                                            ? "저장된 Success DNA가 있으면 LLM 없이 심사 중으로만 넘깁니다."
                                            : undefined
                                        }
                                      >
                                        {analyzingEmployeeId === emp.id ? (
                                          NEW_HIRES_MESSAGES.buttons.analyzing
                                        ) : (
                                          <>
                                            <Sparkles className="mr-1 h-3.5 w-3.5" />
                                            {NEW_HIRES_MESSAGES.buttons.analyze}
                                          </>
                                        )}
                                      </Button>
                                      <Button
                                        variant="outline"
                                        size="sm"
                                        disabled={updatingId !== null}
                                        onClick={() => handleEdit(emp)}
                                        className="h-8 w-[72px] justify-center px-2 text-xs"
                                      >
                                        <Pencil className="mr-1 h-3.5 w-3.5" />
                                        {NEW_HIRES_MESSAGES.buttons.edit}
                                      </Button>
                                      <Button
                                        variant="outline"
                                        size="sm"
                                        disabled={updatingId !== null}
                                        onClick={() => handleDelete(emp)}
                                        className="h-8 w-[72px] justify-center px-2 text-xs text-muted-foreground hover:text-destructive"
                                      >
                                        <Trash2 className="mr-1 h-3.5 w-3.5" />
                                        {NEW_HIRES_MESSAGES.buttons.delete}
                                      </Button>
                                    </div>
                                    {emp.successDna && (
                                      <button
                                        type="button"
                                        disabled={analyzingEmployeeId !== null}
                                        onClick={() => handleReanalyzeConfirm(emp)}
                                        className="text-[11px] text-muted-foreground underline-offset-2 hover:underline disabled:opacity-50"
                                      >
                                        {NEW_HIRES_MESSAGES.buttons.analyzeAgain}
                                      </button>
                                    )}
                                  </div>
                                )}
                                {tab === "screening" && !emp.successDna && (
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    disabled={analyzingEmployeeId !== null}
                                    onClick={() => handleAnalyze(emp)}
                                    className="h-8 w-[86px] justify-center whitespace-nowrap px-2 text-xs"
                                  >
                                    {analyzingEmployeeId === emp.id ? (
                                      NEW_HIRES_MESSAGES.buttons.analyzing
                                    ) : (
                                      <>
                                        <Sparkles className="mr-1 h-3.5 w-3.5" />
                                        {NEW_HIRES_MESSAGES.buttons.analyze}
                                      </>
                                    )}
                                  </Button>
                                )}
                                {tab === "screening" && (
                                  <>
                                    <Button
                                      variant="outline"
                                      size="sm"
                                      disabled={updatingId !== null}
                                      onClick={() => handleSetStatus(emp, "pending")}
                                      className="h-8 w-[72px] justify-center px-2 text-xs"
                                    >
                                      {NEW_HIRES_MESSAGES.tabs.pending}
                                    </Button>
                                    <Button
                                      variant="outline"
                                      size="sm"
                                      disabled={updatingId !== null}
                                      onClick={() => handleEdit(emp)}
                                      className="h-8 w-[72px] justify-center px-2 text-xs"
                                    >
                                      <Pencil className="mr-1 h-3.5 w-3.5" />
                                      {NEW_HIRES_MESSAGES.buttons.edit}
                                    </Button>
                                    <Button
                                      variant="outline"
                                      size="sm"
                                      disabled={updatingId !== null}
                                      onClick={() => handleDelete(emp)}
                                      className="h-8 w-[72px] justify-center px-2 text-xs text-muted-foreground hover:text-destructive"
                                    >
                                      <Trash2 className="mr-1 h-3.5 w-3.5" />
                                      {NEW_HIRES_MESSAGES.buttons.delete}
                                    </Button>
                                    <Button
                                      variant="outline"
                                      size="sm"
                                      disabled={updatingId !== null}
                                      onClick={() => handleSetStatus(emp, "hired")}
                                      className="h-8 w-[72px] justify-center border-emerald-500/40 px-2 text-xs text-emerald-700 hover:bg-emerald-500/10 hover:text-emerald-700 dark:border-emerald-500/40 dark:text-emerald-400 dark:hover:bg-emerald-500/20 dark:hover:text-emerald-300"
                                    >
                                      <CheckCircle className="mr-1 h-3.5 w-3.5" />
                                      {NEW_HIRES_MESSAGES.buttons.hired}
                                    </Button>
                                    <Button
                                      variant="outline"
                                      size="sm"
                                      disabled={updatingId !== null}
                                      onClick={() => {
                                        setRejectDialogEmp(emp);
                                        setRejectReasonText(emp.rejectionReason ?? "");
                                      }}
                                      className="h-8 w-[72px] justify-center border-rose-500/40 px-2 text-xs text-rose-700 hover:bg-rose-500/10 hover:text-rose-700 dark:border-rose-500/40 dark:text-rose-400 dark:hover:bg-rose-500/20 dark:hover:text-rose-300"
                                    >
                                      <XCircle className="mr-1 h-3.5 w-3.5" />
                                      {NEW_HIRES_MESSAGES.buttons.rejected}
                                    </Button>
                                  </>
                                )}
                                {tab === "hired" && (
                                  <>
                                    <Button
                                      variant="default"
                                      size="sm"
                                      disabled={updatingId !== null}
                                      onClick={() => handleOnboardToRegular(emp)}
                                      className="h-8 w-[72px] justify-center px-2 text-xs"
                                    >
                                      {NEW_HIRES_MESSAGES.buttons.onboard}
                                    </Button>
                                  </>
                                )}
                                {tab !== "screening" && tab !== "pending" && (
                                  <>
                                    <Button
                                      variant="outline"
                                      size="sm"
                                      disabled={updatingId !== null}
                                      onClick={() => handleEdit(emp)}
                                      className="h-8 w-[72px] justify-center px-2 text-xs"
                                    >
                                      <Pencil className="mr-1 h-3.5 w-3.5" />
                                      {NEW_HIRES_MESSAGES.buttons.edit}
                                    </Button>
                                    <Button
                                      variant="outline"
                                      size="sm"
                                      disabled={updatingId !== null}
                                      onClick={() => handleDelete(emp)}
                                      className="h-8 w-[72px] justify-center px-2 text-xs text-muted-foreground hover:text-destructive"
                                    >
                                      <Trash2 className="mr-1 h-3.5 w-3.5" />
                                      {NEW_HIRES_MESSAGES.buttons.delete}
                                    </Button>
                                  </>
                                )}
                                {tab === "hired" && (
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    disabled={updatingId !== null}
                                    onClick={() => handleSetStatus(emp, "screening")}
                                    className="h-8 w-[72px] justify-center px-2 text-xs"
                                  >
                                    {NEW_HIRES_MESSAGES.buttons.screening}
                                  </Button>
                                )}
                                {tab === "hired" && (
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    disabled={updatingId !== null}
                                    onClick={() => {
                                      setRejectDialogEmp(emp);
                                      setRejectReasonText(emp.rejectionReason ?? "");
                                    }}
                                    className="h-8 w-[72px] justify-center border-rose-500/40 px-2 text-xs text-rose-700 hover:bg-rose-500/10 hover:text-rose-700 dark:border-rose-500/40 dark:text-rose-400 dark:hover:bg-rose-500/20 dark:hover:text-rose-300"
                                  >
                                    <XCircle className="mr-1 h-3.5 w-3.5" />
                                    {NEW_HIRES_MESSAGES.buttons.rejected}
                                  </Button>
                                )}
                                {tab === "rejected" && (
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    disabled={updatingId !== null}
                                    onClick={() => handleSetStatus(emp, "screening")}
                                    className="h-8 w-[80px] justify-center px-2 text-xs"
                                  >
                                    {NEW_HIRES_MESSAGES.buttons.screening}
                                  </Button>
                                )}
                                {tab === "rejected" && (
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    disabled={updatingId !== null}
                                    onClick={() => handleSetStatus(emp, "hired")}
                                    className="h-8 w-[80px] justify-center border-emerald-500/40 px-2 text-xs text-emerald-700 hover:bg-emerald-500/10 hover:text-emerald-700 dark:border-emerald-500/40 dark:text-emerald-400 dark:hover:bg-emerald-500/20 dark:hover:text-emerald-300"
                                  >
                                    <CheckCircle className="mr-1 h-3.5 w-3.5" />
                                    {NEW_HIRES_MESSAGES.buttons.hired}
                                  </Button>
                                )}
                              </div>
                            </TableCell>
                          </TableRow>
                        ))
                      )}
                    </TableBody>
                  </Table>
                </div>
              </TabsContent>
            ))}
            </Tabs>
            <p className="mt-4 text-sm text-muted-foreground">
              {NEW_HIRES_MESSAGES.section.footerGuide}
            </p>
          </>
        )}
      </section>

      <EmployeeFormModal
        open={modalOpen}
        onOpenChange={(open) => {
          setModalOpen(open);
          if (!open) {
            setJustRegistered(null);
            setEditingEmployee(null);
          }
        }}
        employee={editingEmployee}
        onSave={handleSave}
        nextId={nextId}
        forceNewHire
      />

      <NewHireCompareDialog
        open={!!compareCandidate}
        onOpenChange={(open) => !open && setCompareCandidate(null)}
        candidate={compareCandidate}
      />

      <Dialog
        open={!!reasonDialogEmp}
        onOpenChange={(open) => {
          if (!open) setReasonDialogEmp(null);
        }}
      >
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{reasonDialogEmp ? NEW_HIRES_MESSAGES.dialogs.reasonTitle(reasonDialogEmp.name) : ""}</DialogTitle>
          </DialogHeader>
          {reasonDialogEmp?.successDna && (
            <div className="mb-3 rounded-md border border-border bg-muted/30 px-3 py-2 text-sm">
              <span className="font-medium text-muted-foreground">{NEW_HIRES_MESSAGES.dialogs.reasonDnaLabel} </span>
              리더십 {reasonDialogEmp.successDna.leadership} · 기술력 {reasonDialogEmp.successDna.technical} · 창의성 {reasonDialogEmp.successDna.creativity} · 협업 {reasonDialogEmp.successDna.collaboration} · 적응력 {reasonDialogEmp.successDna.adaptability}
            </div>
          )}
          <textarea
            value={reasonEditText}
            onChange={(e) => setReasonEditText(e.target.value)}
            placeholder={NEW_HIRES_MESSAGES.input.reasonPlaceholder}
            rows={5}
            className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          />
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" size="sm" onClick={() => setReasonDialogEmp(null)}>
              {NEW_HIRES_MESSAGES.buttons.cancel}
            </Button>
            <Button size="sm" disabled={updatingId !== null} onClick={handleSaveReason}>
              {updatingId === reasonDialogEmp?.id ? NEW_HIRES_MESSAGES.buttons.saving : NEW_HIRES_MESSAGES.buttons.save}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      <Dialog
        open={!!rejectDialogEmp}
        onOpenChange={(open) => {
          if (!open) {
            setRejectDialogEmp(null);
            setRejectReasonText("");
          }
        }}
      >
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{rejectDialogEmp ? NEW_HIRES_MESSAGES.dialogs.rejectTitle(rejectDialogEmp.name) : ""}</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">
            {NEW_HIRES_MESSAGES.dialogs.rejectDescription}
          </p>
          <textarea
            value={rejectReasonText}
            onChange={(e) => setRejectReasonText(e.target.value)}
            placeholder={NEW_HIRES_MESSAGES.input.rejectionPlaceholder}
            rows={4}
            className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          />
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" size="sm" onClick={() => { setRejectDialogEmp(null); setRejectReasonText(""); }}>
              {NEW_HIRES_MESSAGES.buttons.cancel}
            </Button>
            <Button
              variant="destructive"
              size="sm"
              disabled={updatingId !== null}
              onClick={handleRejectConfirm}
            >
              {updatingId === rejectDialogEmp?.id ? NEW_HIRES_MESSAGES.buttons.rejectProcessing : NEW_HIRES_MESSAGES.buttons.rejectConfirm}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
