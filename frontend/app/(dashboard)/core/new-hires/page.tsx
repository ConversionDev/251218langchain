"use client";

import { useEffect, useMemo, useState, useCallback } from "react";
import { toast } from "sonner";
import { FileUp, UserPlus, Sparkles, CheckCircle, XCircle, ChevronLeft, ChevronRight, BarChart3 } from "lucide-react";
import Link from "next/link";
import { useStore } from "@/store/useStore";
import { useHydrated } from "@/hooks/use-hydrated";
import {
  fetchEmployeesPaginated,
  fetchNextEmployeeId,
  createEmployeeApi,
  deleteEmployeeApi,
  refreshEmployeeEmbeddingsApi,
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
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type { Employee, RecruitStatus } from "@/modules/shared/types";

const STATUS_LABELS: Record<string, string> = {
  pending: "미검토",
  screening: "심사 중",
  hired: "합격",
  rejected: "탈락",
};

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
  const [embeddingLoading, setEmbeddingLoading] = useState(false);

  const loadPage = useCallback((p: number) => {
    setLoading(true);
    fetchEmployeesPaginated({ page: p, pageSize: PAGE_SIZE, employmentType: "new_hire" })
      .then(({ items, total: t }) => {
        setNewHires(Array.isArray(items) ? items : []);
        setTotal(typeof t === "number" ? t : 0);
        setPage(p);
      })
      .catch(() => { setNewHires([]); setTotal(0); })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    loadPage(1);
  }, [hydrated, loadPage]);

  const list = newHires ?? [];

  const byStatus = useMemo(() => {
    const statusKey = (s: RecruitStatus | null | undefined) => s || "pending";
    const map: Record<string, Employee[]> = { pending: [], screening: [], hired: [], rejected: [] };
    for (const e of list) {
      const key = statusKey(e.status);
      if (map[key]) map[key].push(e);
      else map.pending.push(e);
    }
    return map;
  }, [list]);

  const [activeTab, setActiveTab] = useState<string>("pending");
  const [updatingId, setUpdatingId] = useState<string | null>(null);
  const [reasonDialogEmp, setReasonDialogEmp] = useState<Employee | null>(null);
  const [reasonEditText, setReasonEditText] = useState("");
  const [rejectDialogEmp, setRejectDialogEmp] = useState<Employee | null>(null);
  const [rejectReasonText, setRejectReasonText] = useState("");
  const [compareCandidate, setCompareCandidate] = useState<Employee | null>(null);

  const refreshList = () => loadPage(page);

  const handleSelectForIntelligence = (emp: Employee) => {
    setSelectedEmployee(emp);
    window.location.href = "/intelligence";
  };

  const handleAnalyze = async (emp: Employee) => {
    setAnalyzingEmployeeId(emp.id);
    try {
      await analyzeEmployeeResumeApi(emp.id);
      toast.success(`${emp.name}님 AI 분석 완료. Success DNA가 저장되었습니다.`);
      refreshList();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "AI 분석에 실패했습니다.");
    } finally {
      setAnalyzingEmployeeId(null);
    }
  };

  const handleSetStatus = async (emp: Employee, status: RecruitStatus, rejectionReason?: string | null) => {
    setUpdatingId(emp.id);
    try {
      await updateEmployeeApi(emp.id, { status, ...(rejectionReason !== undefined && { rejectionReason }) });
      toast.success(`${emp.name}님 상태가 ${STATUS_LABELS[status]}(으)로 변경되었습니다.`);
      refreshList();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "상태 변경에 실패했습니다.");
    } finally {
      setUpdatingId(null);
    }
  };

  const handleSaveReason = async () => {
    if (!reasonDialogEmp) return;
    setUpdatingId(reasonDialogEmp.id);
    try {
      await updateEmployeeApi(reasonDialogEmp.id, { successDnaReason: reasonEditText.trim() || null });
      toast.success("평가 근거가 저장되었습니다.");
      refreshList();
      setReasonDialogEmp(null);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "저장에 실패했습니다.");
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
        toast.success(`${updated.name} 정보가 수정되었습니다.`);
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
        toast.warning(`동일한 이력서가 이미 등록되어 있습니다 (${name}). DB에 추가하지 않았습니다.`);
        return;
      }
      console.error(e);
      toast.error(e instanceof Error ? e.message : "등록에 실패했습니다.");
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
    if (!window.confirm(`${emp.name} 지원자 데이터를 삭제할까요?`)) return;
    setUpdatingId(emp.id);
    try {
      await deleteEmployeeApi(emp.id);
      deleteEmployee(emp.id);
      toast.success(`${emp.name} 데이터가 삭제되었습니다.`);
      const currentCount = byStatus[activeTab]?.length ?? 0;
      const nextPage = currentCount <= 1 && page > 1 ? page - 1 : page;
      loadPage(nextPage);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "삭제에 실패했습니다.");
    } finally {
      setUpdatingId(null);
    }
  };

  const handleOnboardToRegular = async (emp: Employee) => {
    if (!window.confirm(`${emp.name}님을 입사 확정 처리하고 기존 직원으로 전환할까요?`)) return;
    setUpdatingId(emp.id);
    try {
      const today = new Date();
      const joinedAt = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;
      await updateEmployeeApi(emp.id, {
        employmentType: "regular",
        joinedAt,
        status: null,
      });
      toast.success(`${emp.name}님이 기존 직원으로 전환되었습니다.`);
      loadPage(page);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "입사 확정 처리에 실패했습니다.");
    } finally {
      setUpdatingId(null);
    }
  };

  const handleRefreshEmbeddings = async () => {
    setEmbeddingLoading(true);
    try {
      const { updated } = await refreshEmployeeEmbeddingsApi();
      toast.success(`임베딩 갱신 완료 (${updated}명 반영). RAG 검색에 반영됩니다.`);
      loadPage(page);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "임베딩 갱신에 실패했습니다.");
    } finally {
      setEmbeddingLoading(false);
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
          <span className="text-xs">이력서 업로드 → AI 분석 → 등록</span>
        </div>
        <h1 className="text-2xl font-bold text-foreground">신입 관리</h1>
        <p className="mt-1 text-muted-foreground">
          이력서를 업로드하면 AI가 기본 정보와 Success DNA를 채웁니다. 확인 후 등록하면 이 페이지의{' '}
          <strong>신입 목록</strong>에 추가됩니다. 기존 직원은{' '}
          <Link href="/core/employees" className="text-primary underline hover:no-underline">기존 직원</Link>에서 관리하세요.
        </p>
      </div>

      <section className="rounded-xl border border-border bg-card p-8 shadow-sm">
        <div className="flex flex-col items-center justify-center gap-6 text-center">
          <div className="rounded-full bg-primary/10 p-4">
            <FileUp className="h-10 w-10 text-primary" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-foreground">이력서로 신입 등록</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              PDF, Word, HWP 등 이력서를 올리면 기본 정보와 역량 분석이 자동으로 채워집니다.
            </p>
          </div>
          <div className="flex flex-wrap items-center justify-center gap-3">
            <Button onClick={handleOpenModal} size="lg" className="inline-flex items-center gap-2">
              <FileUp className="h-4 w-4" />
              이력서 업로드하여 등록하기
            </Button>
            <Button
              variant="outline"
              size="lg"
              className="inline-flex items-center gap-2"
              onClick={handleRefreshEmbeddings}
              disabled={embeddingLoading}
            >
              <Sparkles className="h-4 w-4" />
              {embeddingLoading ? "갱신 중…" : "임베딩 갱신"}
            </Button>
          </div>
          {justRegistered && (
            <p className="text-sm text-green-600 dark:text-green-400">
              등록되었습니다. 아래 신입 목록에서 확인하세요.
            </p>
          )}
        </div>
      </section>

      <section className="rounded-xl border border-border bg-card p-6 shadow-sm">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-lg font-semibold text-foreground">지원자 · 신입 목록 (ATS)</h2>
          <div className="flex items-center gap-3">
            <span className="text-sm text-muted-foreground">신입 전체 {total}명</span>
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
              <span className="min-w-[6rem] text-center text-sm text-muted-foreground">
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
              새로고침
            </Button>
          </div>
        </div>
        {loading && list.length === 0 ? (
          <div className="flex h-32 items-center justify-center rounded border border-border bg-muted/20 text-sm text-muted-foreground">
            로딩 중…
          </div>
        ) : list.length === 0 ? (
          <p className="rounded border border-border bg-muted/30 px-4 py-8 text-center text-sm text-muted-foreground">
            지원자가 없습니다. JSONL 적재 후 <strong>새로고침</strong>을 누르거나, 위에서 이력서 업로드로 등록하세요.
            <br />
            <span className="mt-2 block text-xs">(적재한 DB와 프론트가 같은 API를 쓰는지 확인하세요.)</span>
          </p>
        ) : (
          <>
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="mb-4">
              <TabsTrigger value="pending">
                미검토 ({byStatus.pending.length})
              </TabsTrigger>
              <TabsTrigger value="screening">
                심사 중 ({byStatus.screening.length})
              </TabsTrigger>
              <TabsTrigger value="hired">
                합격 ({byStatus.hired.length})
              </TabsTrigger>
              <TabsTrigger value="rejected">
                탈락 ({byStatus.rejected.length})
              </TabsTrigger>
            </TabsList>
            {(["pending", "screening", "hired", "rejected"] as const).map((tab) => (
              <TabsContent key={tab} value={tab} className="mt-0">
                <div className="overflow-x-auto rounded border border-border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>이름</TableHead>
                        <TableHead>부서</TableHead>
                        <TableHead>직급</TableHead>
                        <TableHead>지원일</TableHead>
                        <TableHead>상태</TableHead>
                        {tab === "rejected" && <TableHead>탈락 사유</TableHead>}
                        <TableHead className="text-right">액션</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {byStatus[tab].length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={tab === "rejected" ? 7 : 6} className="text-center text-muted-foreground py-8">
                            해당 상태의 지원자가 없습니다.
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
                                title="이 직원을 Intelligence에서 조회"
                              >
                                {emp.name}
                              </button>
                            </TableCell>
                            <TableCell>{emp.department || "—"}</TableCell>
                            <TableCell>{emp.jobTitle || "—"}</TableCell>
                            <TableCell>{formatAppDate(emp.applicationDate)}</TableCell>
                            <TableCell>{STATUS_LABELS[emp.status || "pending"]}</TableCell>
                            {tab === "rejected" && (
                              <TableCell className="max-w-[200px] truncate text-muted-foreground" title={emp.rejectionReason ?? undefined}>
                                {emp.rejectionReason || "—"}
                              </TableCell>
                            )}
                            <TableCell className="text-right">
                              <div className="flex items-center justify-end gap-2 flex-wrap">
                                {emp.successDna && (
                                  <>
                                    <Button
                                      variant="outline"
                                      size="sm"
                                      onClick={() => setCompareCandidate(emp)}
                                      className="gap-1"
                                    >
                                      <BarChart3 className="h-3.5 w-3.5" />
                                      기존 직원과 비교
                                    </Button>
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      onClick={() => {
                                        setReasonDialogEmp(emp);
                                        setReasonEditText(emp.successDnaReason ?? "");
                                      }}
                                      className="gap-1 text-muted-foreground hover:text-foreground"
                                    >
                                      평가 근거
                                    </Button>
                                  </>
                                )}
                                {(tab === "pending" || tab === "screening") && !emp.successDna && (
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    disabled={analyzingEmployeeId !== null}
                                    onClick={() => handleAnalyze(emp)}
                                    className="gap-1"
                                  >
                                    {analyzingEmployeeId === emp.id ? "분석 중…" : <><Sparkles className="h-3.5 w-3.5" /> AI 분석</>}
                                  </Button>
                                )}
                                {tab === "pending" && emp.successDna && (
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    disabled={updatingId !== null}
                                    onClick={() => handleSetStatus(emp, "screening")}
                                  >
                                    심사 중으로
                                  </Button>
                                )}
                                {tab === "screening" && (
                                  <>
                                    <Button
                                      variant="default"
                                      size="sm"
                                      disabled={updatingId !== null}
                                      onClick={() => handleSetStatus(emp, "hired")}
                                      className="gap-1"
                                    >
                                      <CheckCircle className="h-3.5 w-3.5" />
                                      합격
                                    </Button>
                                    <Button
                                      variant="destructive"
                                      size="sm"
                                      disabled={updatingId !== null}
                                      onClick={() => {
                                        setRejectDialogEmp(emp);
                                        setRejectReasonText(emp.rejectionReason ?? "");
                                      }}
                                      className="gap-1"
                                    >
                                      <XCircle className="h-3.5 w-3.5" />
                                      탈락
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
                                    >
                                      입사 확정(기존 직원 전환)
                                    </Button>
                                    <Button
                                      variant="outline"
                                      size="sm"
                                      disabled={updatingId !== null}
                                      onClick={() => handleSetStatus(emp, "screening")}
                                    >
                                      심사 중으로
                                    </Button>
                                    <Button
                                      variant="destructive"
                                      size="sm"
                                      disabled={updatingId !== null}
                                      onClick={() => {
                                        setRejectDialogEmp(emp);
                                        setRejectReasonText(emp.rejectionReason ?? "");
                                      }}
                                      className="gap-1"
                                    >
                                      <XCircle className="h-3.5 w-3.5" />
                                      탈락
                                    </Button>
                                  </>
                                )}
                                {tab === "rejected" && (
                                  <>
                                    <Button
                                      variant="outline"
                                      size="sm"
                                      disabled={updatingId !== null}
                                      onClick={() => handleSetStatus(emp, "screening")}
                                    >
                                      심사 중으로
                                    </Button>
                                    <Button
                                      variant="default"
                                      size="sm"
                                      disabled={updatingId !== null}
                                      onClick={() => handleSetStatus(emp, "hired")}
                                      className="gap-1"
                                    >
                                      <CheckCircle className="h-3.5 w-3.5" />
                                      합격
                                    </Button>
                                  </>
                                )}
                                <Button
                                  variant="outline"
                                  size="sm"
                                  disabled={updatingId !== null}
                                  onClick={() => handleEdit(emp)}
                                >
                                  수정
                                </Button>
                                <Button
                                  variant="destructive"
                                  size="sm"
                                  disabled={updatingId !== null}
                                  onClick={() => handleDelete(emp)}
                                >
                                  삭제
                                </Button>
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
            미검토: 이력서 접수만 된 상태. [AI 분석]으로 엑사원이 Success DNA를 생성합니다. 심사 중에서 [합격]/[탈락]으로 결정하세요.
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
            <DialogTitle>{reasonDialogEmp?.name} · 평가 근거 (수동 수정 가능)</DialogTitle>
          </DialogHeader>
          {reasonDialogEmp?.successDna && (
            <div className="mb-3 rounded-md border border-border bg-muted/30 px-3 py-2 text-sm">
              <span className="font-medium text-muted-foreground">Success DNA </span>
              리더십 {reasonDialogEmp.successDna.leadership} · 기술력 {reasonDialogEmp.successDna.technical} · 창의성 {reasonDialogEmp.successDna.creativity} · 협업 {reasonDialogEmp.successDna.collaboration} · 적응력 {reasonDialogEmp.successDna.adaptability}
            </div>
          )}
          <textarea
            value={reasonEditText}
            onChange={(e) => setReasonEditText(e.target.value)}
            placeholder="AI가 생성한 평가 근거를 확인·수정하세요."
            rows={5}
            className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          />
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" size="sm" onClick={() => setReasonDialogEmp(null)}>
              취소
            </Button>
            <Button size="sm" disabled={updatingId !== null} onClick={handleSaveReason}>
              {updatingId === reasonDialogEmp?.id ? "저장 중…" : "저장"}
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
            <DialogTitle>{rejectDialogEmp?.name} · 탈락 사유</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">
            탈락 처리 시 사유를 입력하면 이의 제기·감사 대응 시 참고할 수 있습니다. (선택)
          </p>
          <textarea
            value={rejectReasonText}
            onChange={(e) => setRejectReasonText(e.target.value)}
            placeholder="예: 경력 부합도 낮음, 자격 요건 미충족 등"
            rows={4}
            className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          />
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" size="sm" onClick={() => { setRejectDialogEmp(null); setRejectReasonText(""); }}>
              취소
            </Button>
            <Button
              variant="destructive"
              size="sm"
              disabled={updatingId !== null}
              onClick={handleRejectConfirm}
            >
              {updatingId === rejectDialogEmp?.id ? "처리 중…" : "탈락 처리"}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
