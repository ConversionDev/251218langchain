"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { Info, Upload } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RESUME_ACCEPT } from "@/lib/documentExtensions";
import type { ResumeParseResult } from "@/modules/core/services/resumeToBaseline";
import {
  computeResumeFileHash,
  getCachedResumeResult,
  parseResumeToBaseline,
} from "@/modules/core/services/resumeToBaseline";
import { getIfrsMetricsView } from "@/modules/shared/utils/disclosureMetrics";
import type { Employee, IfrsMetrics, Gender, EmploymentType } from "@/modules/shared/types";

const GENDER_OPTIONS: { value: Gender; label: string }[] = [
  { value: "male", label: "남" },
  { value: "female", label: "여" },
  { value: "undisclosed", label: "미기입" },
  { value: "other", label: "기타" },
];

const EMPLOYMENT_OPTIONS: { value: EmploymentType; label: string }[] = [
  { value: "new_hire", label: "신입" },
  { value: "regular", label: "정규직" },
  { value: "contract", label: "계약직" },
  { value: "part_time", label: "파트타임" },
  { value: "intern", label: "인턴" },
];

interface EmployeeFormModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  employee: Employee | null;
  onSave: (employee: Employee) => void;
  nextId: string;
}

export function EmployeeFormModal({
  open,
  onOpenChange,
  employee,
  onSave,
  nextId,
}: EmployeeFormModalProps) {
  const isEdit = employee != null;
  const [form, setForm] = useState<Employee>({
    id: nextId,
    name: "",
    jobTitle: "",
    department: "",
    email: "",
    applicationDate: undefined,
    joinedAt: "",
    gender: "undisclosed",
    age: undefined,
    employmentType: "new_hire",
    trainingHours: 0,
    disclosureMetrics: {
      transitionReadyScore: 0,
      skillGap: 0,
      humanCapitalROI: 0,
    },
  });
  const [uploadLoading, setUploadLoading] = useState(false);
  /** 체감 속도: 단계별 메시지 (파일 확인 → 추출 → AI 분석) */
  const [uploadPhase, setUploadPhase] = useState<"idle" | "uploading" | "extracting" | "analyzing">("idle");
  const [disclosureStatus, setDisclosureStatus] = useState<{
    ingested: boolean;
    document_count: number;
  } | null>(null);
  const [disclosureStatusLoading, setDisclosureStatusLoading] = useState(false);
  const [checkResult, setCheckResult] = useState<{
    suitable: boolean;
    message: string;
    suggestions: string[];
  } | null>(null);
  const [checkLoading, setCheckLoading] = useState(false);
  /** 신입 연속 등록: 한 명 저장 후 nextId 갱신되면 폼 초기화 */
  const [expectingNewNextId, setExpectingNewNextId] = useState(false);
  const prevNextIdRef = useRef<string>(nextId);
  /** 마지막 업로드한 이력서 파일 해시 (동일 이력서 중복 등록 방지) */
  const [lastResumeFileHash, setLastResumeFileHash] = useState<string | null>(null);

  const apiBase = typeof window !== "undefined"
    ? (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000")
    : "http://localhost:8000";

  useEffect(() => {
    if (employee) {
      setForm({
        ...employee,
        successDna: employee.successDna,
        disclosureMetrics:
          getIfrsMetricsView(employee.disclosureMetrics) ?? {
            transitionReadyScore: 0,
            skillGap: 0,
            humanCapitalROI: 0,
          },
      });
      prevNextIdRef.current = employee.id;
    } else {
      setForm({
        id: nextId,
        name: "",
        jobTitle: "",
        department: "",
        email: "",
        applicationDate: undefined,
        joinedAt: "",
        gender: "undisclosed",
        age: undefined,
        employmentType: "new_hire",
        trainingHours: 0,
        successDna: undefined,
        disclosureMetrics: { transitionReadyScore: 0, skillGap: 0, humanCapitalROI: 0 },
      });
      prevNextIdRef.current = nextId;
      setLastResumeFileHash(null);
    }
  }, [employee, nextId, open]);

  /** 신입 연속 등록: 저장 후 부모가 nextId 갱신하면 폼만 초기화하고 모달은 유지 */
  useEffect(() => {
    if (!open || employee != null) return;
    if (expectingNewNextId && nextId !== prevNextIdRef.current) {
      prevNextIdRef.current = nextId;
      setExpectingNewNextId(false);
      setForm({
        id: nextId,
        name: "",
        jobTitle: "",
        department: "",
        email: "",
        applicationDate: undefined,
        joinedAt: "",
        gender: "undisclosed",
        age: undefined,
        employmentType: "new_hire",
        trainingHours: 0,
        successDna: undefined,
        disclosureMetrics: { transitionReadyScore: 0, skillGap: 0, humanCapitalROI: 0 },
      });
    }
  }, [open, employee, nextId, expectingNewNextId]);

  useEffect(() => {
    if (!open || isEdit) return;
    setDisclosureStatusLoading(true);
    setDisclosureStatus(null);
    fetch(`${apiBase}/api/disclosure/status`)
      .then((res) => (res.ok ? res.json() : Promise.reject(new Error("status failed"))))
      .then((data: { ingested: boolean; document_count: number }) => setDisclosureStatus(data))
      .catch(() => setDisclosureStatus({ ingested: false, document_count: 0 }))
      .finally(() => setDisclosureStatusLoading(false));
  }, [open, isEdit, apiBase]);

  const update = (patch: Partial<Employee>) => setForm((prev) => ({ ...prev, ...patch }));

  const handleDisclosureCheck = useCallback(async () => {
    setCheckLoading(true);
    setCheckResult(null);
    try {
      const startRes = await fetch(`${apiBase}/api/disclosure/check`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: form.name,
          job_title: form.jobTitle,
          department: form.department,
          email: form.email ?? undefined,
          gender: form.gender ?? undefined,
          age: form.age ?? undefined,
          employment_type: form.employmentType ?? undefined,
          training_hours: form.trainingHours ?? undefined,
        }),
      });
      if (!startRes.ok) throw new Error(await startRes.text());
      const { job_id } = await startRes.json() as { job_id: string };

      const maxAttempts = 60;
      const pollIntervalMs = 1500;
      for (let attempt = 0; attempt < maxAttempts; attempt++) {
        const res = await fetch(`${apiBase}/api/disclosure/check/result/${job_id}`);
        if (!res.ok) throw new Error(await res.text());
        const data = await res.json() as { status: string; result?: { suitable: boolean; message: string; suggestions: string[] }; error?: string };
        if (data.status === "pending") {
          await new Promise((r) => setTimeout(r, pollIntervalMs));
          continue;
        }
        if (data.status === "failed") {
          setCheckResult({
            suitable: false,
            message: data.error ?? "처리 실패",
            suggestions: [],
          });
          toast.error("공시 기여도 예측에 실패했습니다.");
          return;
        }
        if (data.status === "completed" && data.result) {
          setCheckResult({
            suitable: data.result.suitable,
            message: data.result.message,
            suggestions: data.result.suggestions ?? [],
          });
          if (data.result.suitable) toast.success("공시 기여 잠재력이 있습니다.");
          else toast.info("면접·확인 가이드를 참고해 주세요.");
        }
        return;
      }
      toast.error("공시 기여도 예측 시간이 초과되었습니다.");
      setCheckResult({ suitable: false, message: "응답 대기 시간 초과", suggestions: [] });
    } catch (e) {
      toast.error("공시 기준 확인에 실패했습니다.");
      setCheckResult({
        suitable: false,
        message: e instanceof Error ? e.message : "요청 실패",
        suggestions: [],
      });
    } finally {
      setCheckLoading(false);
    }
  }, [apiBase, form.name, form.jobTitle, form.department, form.email, form.gender, form.age, form.employmentType, form.trainingHours]);

  const applyResumeResult = useCallback((result: ResumeParseResult) => {
    setForm((prev) => ({
      ...prev,
      name: result.name,
      jobTitle: result.jobTitle,
      department: result.department,
      email: result.email,
      applicationDate: result.applicationDate,
      joinedAt: result.joinedAt,
      resume: result.resume,
      successDna: result.successDna,
      ...(result.gender != null && { gender: result.gender }),
      ...(result.age != null && result.age > 0 && { age: result.age }),
      ...(result.employmentType != null && { employmentType: result.employmentType }),
      ...(result.trainingHours != null && result.trainingHours >= 0 && { trainingHours: result.trainingHours }),
    }));
  }, []);

  /** 이력서 업로드 시 빈칸에만 채움. 등록은 사용자가 등록 버튼으로 함. 파일 해시 저장(동일 이력서 중복 방지). */
  const handleResumeFile = useCallback(
    async (file: File) => {
      try {
        const hash = await computeResumeFileHash(file);
        setLastResumeFileHash(hash);
      } catch {
        setLastResumeFileHash(null);
      }
      const cached = getCachedResumeResult(file);
      if (cached) {
        applyResumeResult(cached);
        toast.success("저장된 분석 결과를 불러왔습니다. 내용 확인 후 등록 버튼을 눌러 주세요.");
        return;
      }
      setUploadLoading(true);
      setUploadPhase("uploading");
      const t1 = window.setTimeout(() => setUploadPhase("extracting"), 600);
      const t2 = window.setTimeout(() => setUploadPhase("analyzing"), 2200);
      try {
        const { result } = await parseResumeToBaseline(file);
        applyResumeResult(result);
        toast.success("이력서를 분석했습니다. 내용을 확인한 뒤 등록 버튼을 눌러 주세요.");
      } catch {
        toast.error("이력서 처리에 실패했습니다.");
      } finally {
        window.clearTimeout(t1);
        window.clearTimeout(t2);
        setUploadLoading(false);
        setUploadPhase("idle");
      }
    },
    [applyResumeResult]
  );

  const updateIfrs = (patch: Partial<IfrsMetrics>) =>
    setForm((prev) => ({
      ...prev,
      disclosureMetrics: { ...(prev.disclosureMetrics ?? { transitionReadyScore: 0, skillGap: 0, humanCapitalROI: 0 }), ...patch },
    }));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave({
      ...form,
      ...(isEdit ? {} : { resumeFileHash: lastResumeFileHash ?? undefined }),
    });
    onOpenChange(false);
    if (isEdit) {
      toast.success("데이터 변경사항이 저장되었습니다. Credential 모듈에서 해시 갱신이 필요합니다.");
    } else {
      toast.success("직원이 등록되었습니다.");
    }
  };

  const tooltipText = "이 데이터는 IFRS S2 보고서에 활용됩니다.";

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{isEdit ? "직원 수정" : "직원 등록"}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* 이력서 업로드 (등록 시 메인 트리거, 목 데이터로 기본 정보 + Baseline DNA 채움) */}
          {!isEdit && (
            <fieldset className="space-y-2">
              <legend className="text-sm font-semibold text-foreground">이력서 업로드</legend>
              {disclosureStatusLoading ? (
                <p className="text-xs text-muted-foreground">공시 기준 학습 여부 확인 중…</p>
              ) : disclosureStatus ? (
                disclosureStatus.ingested ? (
                  <p className="text-xs text-green-600 dark:text-green-400">
                    ISO 30414 공시 기준 학습 완료 (적재 문서 {disclosureStatus.document_count}건)
                  </p>
                ) : (
                  <p className="text-xs text-muted-foreground">
                    ISO 30414가 아직 학습되지 않았습니다. 채팅에서 문서를 먼저 적재해 주세요.
                  </p>
                )
              ) : null}
              <div
                onDrop={(e) => {
                  e.preventDefault();
                  const file = e.dataTransfer?.files?.[0];
                  if (file) handleResumeFile(file);
                }}
                onDragOver={(e) => e.preventDefault()}
                className={`flex min-h-[100px] flex-col items-center justify-center rounded-xl border-2 border-dashed p-4 text-center text-sm transition-colors ${
                  uploadLoading ? "cursor-wait bg-muted/50" : "border-border bg-muted/30 hover:border-primary/50"
                }`}
              >
                <input
                  type="file"
                  accept={RESUME_ACCEPT}
                  className="hidden"
                  id="core-resume-upload"
                  disabled={uploadLoading}
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (f) handleResumeFile(f);
                    e.target.value = "";
                  }}
                />
                <label htmlFor="core-resume-upload" className={uploadLoading ? "pointer-events-none" : "cursor-pointer"}>
                  <Upload className="mx-auto h-8 w-8 text-muted-foreground" />
                  <p className="mt-1 font-medium text-foreground">
                    {uploadLoading
                      ? uploadPhase === "uploading"
                        ? "파일 확인 중…"
                        : uploadPhase === "extracting"
                          ? "텍스트 추출 중…"
                          : "AI가 이력서를 분석하고 있습니다…"
                      : "이력서를 놓거나 클릭해 업로드"}
                  </p>
                  <p className="mt-0.5 text-xs text-muted-foreground">PDF, TXT, Word(.docx), HWP(.hwp) · 업로드 시 빈칸에 정보가 채워집니다. 등록은 등록 버튼을 눌러 주세요.</p>
                </label>
              </div>
            </fieldset>
          )}

          {/* 편집 시: DB에 저장된 이력서 즉시 반영 안내 + 새 파일로 갱신(선택) */}
          {isEdit && (
            <fieldset className="space-y-2">
              <legend className="text-sm font-semibold text-foreground">이력서</legend>
              {form.resume && (form.resume.education?.length > 0 || form.resume.experience?.length > 0) ? (
                <>
                  <p className="rounded-md bg-muted/50 px-3 py-2 text-xs text-muted-foreground">
                    등록된 이력서가 반영되어 있습니다 (학력 {form.resume.education?.length ?? 0}건, 경력 {form.resume.experience?.length ?? 0}건). 새 파일을 올리면 덮어씁니다.
                  </p>
                  <div
                    onDrop={(e) => { e.preventDefault(); const f = e.dataTransfer?.files?.[0]; if (f) handleResumeFile(f); }}
                    onDragOver={(e) => e.preventDefault()}
                    className={`flex min-h-[72px] flex-col items-center justify-center rounded-lg border border-dashed border-border bg-muted/20 p-3 text-center text-xs ${uploadLoading ? "cursor-wait opacity-70" : "hover:border-primary/40"}`}
                  >
                    <input
                      type="file"
                      accept={RESUME_ACCEPT}
                      className="hidden"
                      id="core-resume-upload-edit"
                      disabled={uploadLoading}
                      onChange={(e) => { const f = e.target.files?.[0]; if (f) handleResumeFile(f); e.target.value = ""; }}
                    />
                    <label htmlFor="core-resume-upload-edit" className={uploadLoading ? "pointer-events-none" : "cursor-pointer"}>
                      <Upload className="mx-auto h-5 w-5 text-muted-foreground" />
                      <span className="mt-1 block text-muted-foreground">새 이력서로 갱신 (빈칸 채움 후 저장 버튼)</span>
                    </label>
                  </div>
                </>
              ) : (
                <>
                  <p className="text-xs text-muted-foreground">등록된 이력서가 없습니다. 새 파일을 올리면 분석 후 반영됩니다.</p>
                  <div
                    onDrop={(e) => { e.preventDefault(); const f = e.dataTransfer?.files?.[0]; if (f) handleResumeFile(f); }}
                    onDragOver={(e) => e.preventDefault()}
                    className={`flex min-h-[72px] flex-col items-center justify-center rounded-lg border border-dashed border-border bg-muted/20 p-3 text-center text-xs ${uploadLoading ? "cursor-wait opacity-70" : "hover:border-primary/40"}`}
                  >
                    <input
                      type="file"
                      accept={RESUME_ACCEPT}
                      className="hidden"
                      id="core-resume-upload-edit"
                      disabled={uploadLoading}
                      onChange={(e) => { const f = e.target.files?.[0]; if (f) handleResumeFile(f); e.target.value = ""; }}
                    />
                    <label htmlFor="core-resume-upload-edit" className={uploadLoading ? "pointer-events-none" : "cursor-pointer"}>
                      <Upload className="mx-auto h-5 w-5 text-muted-foreground" />
                      <span className="mt-1 block text-muted-foreground">이력서 업로드 (빈칸 채움 후 저장 버튼)</span>
                    </label>
                  </div>
                </>
              )}
            </fieldset>
          )}

          {/* 기본 정보 */}
          <fieldset className="space-y-3">
            <legend className="text-sm font-semibold text-foreground">기본 정보</legend>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label htmlFor="name">이름</Label>
                <Input
                  id="name"
                  value={form.name}
                  onChange={(e) => update({ name: e.target.value })}
                  required
                  className="mt-1"
                />
              </div>
              <div>
                <Label htmlFor="jobTitle">직급</Label>
                <Input
                  id="jobTitle"
                  value={form.jobTitle}
                  onChange={(e) => update({ jobTitle: e.target.value })}
                  required
                  className="mt-1"
                />
              </div>
              <div className="col-span-2">
                <Label htmlFor="department">부서</Label>
                <Input
                  id="department"
                  value={form.department}
                  onChange={(e) => update({ department: e.target.value })}
                  required
                  className="mt-1"
                />
              </div>
              <div>
                <Label htmlFor="email">이메일</Label>
                <Input
                  id="email"
                  type="email"
                  value={form.email ?? ""}
                  onChange={(e) => update({ email: e.target.value || undefined })}
                  className="mt-1"
                />
              </div>
              <div>
                <Label htmlFor="applicationDate">지원일</Label>
                <Input
                  id="applicationDate"
                  type="date"
                  value={form.applicationDate ?? ""}
                  onChange={(e) => update({ applicationDate: e.target.value || undefined })}
                  className="mt-1"
                />
              </div>
              <div>
                <Label htmlFor="joinedAt">입사일</Label>
                <Input
                  id="joinedAt"
                  type="date"
                  value={form.joinedAt ?? ""}
                  onChange={(e) => update({ joinedAt: e.target.value || undefined })}
                  className="mt-1"
                />
              </div>
            </div>
          </fieldset>

          {/* 공시용 지표 (ISO) */}
          <fieldset className="space-y-3">
            <legend className="flex items-center gap-2 text-sm font-semibold text-foreground">
              공시용 지표 (ISO)
              <span
                className="text-muted-foreground"
                title={tooltipText}
              >
                <Info className="h-4 w-4" aria-label={tooltipText} />
              </span>
            </legend>
            <p className="text-xs text-muted-foreground" title={tooltipText}>
              {tooltipText}
            </p>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>성별</Label>
                <select
                  className="mt-1 flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm"
                  value={form.gender ?? "undisclosed"}
                  onChange={(e) => update({ gender: e.target.value as Gender })}
                >
                  {GENDER_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <Label htmlFor="age">연령</Label>
                <Input
                  id="age"
                  type="number"
                  min={0}
                  max={120}
                  placeholder="만 나이"
                  value={form.age ?? ""}
                  onChange={(e) => {
                    const v = e.target.value === "" ? undefined : Number(e.target.value);
                    update({ age: v === undefined || Number.isNaN(v) ? undefined : Math.max(0, Math.min(120, v)) });
                  }}
                  className="mt-1"
                />
              </div>
              <div>
                <Label>고용 형태</Label>
                <select
                  className="mt-1 flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm"
                  value={form.employmentType ?? (isEdit ? "regular" : "new_hire")}
                  onChange={(e) => update({ employmentType: e.target.value as EmploymentType })}
                >
                  {EMPLOYMENT_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <Label htmlFor="trainingHours">교육시간 (연간)</Label>
                <Input
                  id="trainingHours"
                  type="number"
                  min={0}
                  value={form.trainingHours ?? 0}
                  onChange={(e) => update({ trainingHours: Number(e.target.value) || 0 })}
                  className="mt-1"
                />
              </div>
            </div>
          </fieldset>

          {!isEdit && disclosureStatus?.ingested && (
            <div className="space-y-2 rounded-xl border border-border bg-muted/30 p-4">
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm font-medium text-foreground">공시 기여도 예측</span>
                <Button
                  type="button"
                  variant="outline"
                  disabled={checkLoading}
                  onClick={handleDisclosureCheck}
                  className="text-sm"
                >
                  {checkLoading ? "예측 중…" : "기여도 예측"}
                </Button>
              </div>
              {checkResult && (
                <div className="space-y-1.5 text-sm">
                  <p className={checkResult.suitable ? "text-green-600 dark:text-green-400" : "text-amber-600 dark:text-amber-400"}>
                    {checkResult.message}
                  </p>
                  {checkResult.suggestions.length > 0 && (
                    <>
                      <p className="text-xs font-medium text-muted-foreground">면접·확인 시 질문/가이드</p>
                      <ul className="list-inside list-disc text-muted-foreground">
                        {checkResult.suggestions.map((s, i) => (
                          <li key={i}>{s}</li>
                        ))}
                      </ul>
                    </>
                  )}
                </div>
              )}
            </div>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              취소
            </Button>
            <Button type="submit">{isEdit ? "저장" : "등록"}</Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
