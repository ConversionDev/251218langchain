"use client";

import { useCallback, useEffect, useState } from "react";
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
import { parseResumeToBaseline } from "@/modules/core/services/resumeToBaseline";
import type { Employee, IfrsMetrics, Gender, AgeBand, EmploymentType } from "@/modules/shared/types";

const GENDER_OPTIONS: { value: Gender; label: string }[] = [
  { value: "male", label: "남" },
  { value: "female", label: "여" },
  { value: "other", label: "기타" },
  { value: "undisclosed", label: "미공개" },
];

const AGE_OPTIONS: { value: AgeBand; label: string }[] = [
  { value: "under30", label: "30세 미만" },
  { value: "30-39", label: "30-39세" },
  { value: "40-49", label: "40-49세" },
  { value: "50-59", label: "50-59세" },
  { value: "60over", label: "60세 이상" },
];

const EMPLOYMENT_OPTIONS: { value: EmploymentType; label: string }[] = [
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
    joinedAt: "",
    gender: "undisclosed",
    ageBand: "30-39",
    employmentType: "regular",
    trainingHours: 0,
    ifrsMetrics: {
      transitionReadyScore: 0,
      skillGap: 0,
      humanCapitalROI: 0,
    },
  });
  const [uploadLoading, setUploadLoading] = useState(false);
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

  const apiBase = typeof window !== "undefined"
    ? (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000")
    : "http://localhost:8000";

  useEffect(() => {
    if (employee) {
      setForm({
        ...employee,
        successDna: employee.successDna,
        ifrsMetrics: employee.ifrsMetrics ?? {
          transitionReadyScore: 0,
          skillGap: 0,
          humanCapitalROI: 0,
        },
      });
    } else {
      setForm({
        id: nextId,
        name: "",
        jobTitle: "",
        department: "",
        email: "",
        joinedAt: "",
        gender: "undisclosed",
        ageBand: "30-39",
        employmentType: "regular",
        trainingHours: 0,
        successDna: undefined,
        ifrsMetrics: { transitionReadyScore: 0, skillGap: 0, humanCapitalROI: 0 },
      });
    }
  }, [employee, nextId, open]);

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
          age_band: form.ageBand ?? undefined,
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
  }, [apiBase, form.name, form.jobTitle, form.department, form.email, form.gender, form.ageBand, form.employmentType, form.trainingHours]);

  const handleResumeFile = useCallback(
    async (file: File) => {
      setUploadLoading(true);
      try {
        const result = await parseResumeToBaseline(file);
        setForm((prev) => ({
          ...prev,
          name: result.name,
          jobTitle: result.jobTitle,
          department: result.department,
          email: result.email,
          joinedAt: result.joinedAt,
          resume: result.resume,
          successDna: result.successDna,
        }));
        toast.success("이력서를 분석했습니다. 아래 내용을 확인한 뒤 등록해 주세요.");
      } catch {
        toast.error("이력서 처리에 실패했습니다.");
      } finally {
        setUploadLoading(false);
      }
    },
    []
  );

  const updateIfrs = (patch: Partial<IfrsMetrics>) =>
    setForm((prev) => ({
      ...prev,
      ifrsMetrics: { ...(prev.ifrsMetrics ?? { transitionReadyScore: 0, skillGap: 0, humanCapitalROI: 0 }), ...patch },
    }));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(form);
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
                  accept=".pdf,.txt,application/pdf,text/plain"
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
                    {uploadLoading ? "분석 중…" : "이력서를 놓거나 클릭해 업로드"}
                  </p>
                  <p className="mt-0.5 text-xs text-muted-foreground">PDF, TXT · AI가 기본 정보와 Baseline DNA를 채웁니다</p>
                </label>
              </div>
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
                <Label>연령대</Label>
                <select
                  className="mt-1 flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm"
                  value={form.ageBand ?? "30-39"}
                  onChange={(e) => update({ ageBand: e.target.value as AgeBand })}
                >
                  {AGE_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <Label>고용 형태</Label>
                <select
                  className="mt-1 flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm"
                  value={form.employmentType ?? "regular"}
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
