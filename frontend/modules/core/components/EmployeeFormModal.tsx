"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { Upload } from "lucide-react";
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
import type { Employee } from "@/modules/shared/types";
import { EMPLOYEE_FORM_MESSAGES } from "@/modules/shared/constants/messages";

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
    trainingHours: undefined,
    disclosureMetrics: undefined,
  });
  const [uploadLoading, setUploadLoading] = useState(false);
  /** 체감 속도: 단계별 메시지 (파일 확인 → 추출 → AI 분석) */
  const [uploadPhase, setUploadPhase] = useState<"idle" | "uploading" | "extracting" | "analyzing">("idle");
  /** 신입 연속 등록: 한 명 저장 후 nextId 갱신되면 폼 초기화 */
  const [expectingNewNextId, setExpectingNewNextId] = useState(false);
  const prevNextIdRef = useRef<string>(nextId);
  /** 마지막 업로드한 이력서 파일 해시 (동일 이력서 중복 등록 방지) */
  const [lastResumeFileHash, setLastResumeFileHash] = useState<string | null>(null);

  useEffect(() => {
    if (employee) {
      setForm({
        ...employee,
        successDna: employee.successDna,
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
        trainingHours: undefined,
        successDna: undefined,
        disclosureMetrics: undefined,
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
        trainingHours: undefined,
        successDna: undefined,
        disclosureMetrics: undefined,
      });
    }
  }, [open, employee, nextId, expectingNewNextId]);

  const update = (patch: Partial<Employee>) => setForm((prev) => ({ ...prev, ...patch }));

  const applyResumeResult = useCallback((result: ResumeParseResult) => {
    setForm((prev) => {
      const isNewHire = (result.employmentType ?? prev.employmentType) === "new_hire";
      return {
        ...prev,
        name: result.name,
        jobTitle: result.jobTitle,
        department: result.department?.includes(EMPLOYEE_FORM_MESSAGES.upload.departmentFallbackKeyword)
          ? EMPLOYEE_FORM_MESSAGES.upload.departmentFallbackValue
          : result.department,
        email: result.email,
        applicationDate: result.applicationDate,
        // 신입은 입사일을 비워 둠. 입사 확정 시에만 화면에서 설정됨.
        joinedAt: isNewHire ? "" : (result.joinedAt ?? prev.joinedAt ?? ""),
        resume: result.resume,
        successDna: result.successDna,
        ...(result.gender != null && { gender: result.gender }),
        ...(result.age != null && result.age > 0 && { age: result.age }),
        ...(result.employmentType != null && { employmentType: result.employmentType }),
      };
    });
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
        toast.success(EMPLOYEE_FORM_MESSAGES.upload.cachedLoaded);
        return;
      }
      setUploadLoading(true);
      setUploadPhase("uploading");
      const t1 = window.setTimeout(() => setUploadPhase("extracting"), 600);
      const t2 = window.setTimeout(() => setUploadPhase("analyzing"), 2200);
      try {
        const { result } = await parseResumeToBaseline(file);
        applyResumeResult(result);
        toast.success(EMPLOYEE_FORM_MESSAGES.upload.analyzed);
      } catch {
        toast.error(EMPLOYEE_FORM_MESSAGES.upload.failed);
      } finally {
        window.clearTimeout(t1);
        window.clearTimeout(t2);
        setUploadLoading(false);
        setUploadPhase("idle");
      }
    },
    [applyResumeResult]
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave({
      ...form,
      ...(isEdit ? {} : { resumeFileHash: lastResumeFileHash ?? undefined }),
    });
    onOpenChange(false);
    if (isEdit) {
      toast.success(EMPLOYEE_FORM_MESSAGES.toast.updated);
    } else {
      toast.success(EMPLOYEE_FORM_MESSAGES.toast.created);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{isEdit ? EMPLOYEE_FORM_MESSAGES.dialog.editTitle : EMPLOYEE_FORM_MESSAGES.dialog.createTitle}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* 이력서 업로드 (등록 시 메인 트리거, 목 데이터로 기본 정보 + Baseline DNA 채움) */}
          {!isEdit && (
            <fieldset className="space-y-2">
              <legend className="text-sm font-semibold text-foreground">{EMPLOYEE_FORM_MESSAGES.upload.uploadLegend}</legend>
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
                        ? EMPLOYEE_FORM_MESSAGES.upload.phaseUploading
                        : uploadPhase === "extracting"
                          ? EMPLOYEE_FORM_MESSAGES.upload.phaseExtracting
                          : EMPLOYEE_FORM_MESSAGES.upload.phaseAnalyzing
                      : EMPLOYEE_FORM_MESSAGES.upload.dropzoneIdle}
                  </p>
                  <p className="mt-0.5 text-xs text-muted-foreground">{EMPLOYEE_FORM_MESSAGES.upload.acceptedHint}</p>
                </label>
              </div>
            </fieldset>
          )}

          {/* 편집 시: DB에 저장된 이력서 즉시 반영 안내 + 새 파일로 갱신(선택) */}
          {isEdit && (
            <fieldset className="space-y-2">
              <legend className="text-sm font-semibold text-foreground">{EMPLOYEE_FORM_MESSAGES.upload.resumeLegend}</legend>
              {form.resume && (form.resume.education?.length > 0 || form.resume.experience?.length > 0) ? (
                <>
                  <p className="rounded-md bg-muted/50 px-3 py-2 text-xs text-muted-foreground">
                    {EMPLOYEE_FORM_MESSAGES.upload.existingResumeSummary(
                      form.resume.education?.length ?? 0,
                      form.resume.experience?.length ?? 0,
                    )}
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
                      <span className="mt-1 block text-muted-foreground">{EMPLOYEE_FORM_MESSAGES.upload.editReplaceHint}</span>
                    </label>
                  </div>
                </>
              ) : (
                <>
                  <p className="text-xs text-muted-foreground">{EMPLOYEE_FORM_MESSAGES.upload.noResumeSummary}</p>
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
                      <span className="mt-1 block text-muted-foreground">{EMPLOYEE_FORM_MESSAGES.upload.editUploadHint}</span>
                    </label>
                  </div>
                </>
              )}
            </fieldset>
          )}

          {/* 기본 정보 */}
          <fieldset className="space-y-3">
            <legend className="text-sm font-semibold text-foreground">{EMPLOYEE_FORM_MESSAGES.form.legend}</legend>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label htmlFor="name">{EMPLOYEE_FORM_MESSAGES.form.labels.name}</Label>
                <Input
                  id="name"
                  value={form.name}
                  onChange={(e) => update({ name: e.target.value })}
                  required
                  className="mt-1"
                />
              </div>
              <div>
                <Label htmlFor="jobTitle">{EMPLOYEE_FORM_MESSAGES.form.labels.jobTitle}</Label>
                <Input
                  id="jobTitle"
                  value={form.jobTitle}
                  onChange={(e) => update({ jobTitle: e.target.value })}
                  required
                  className="mt-1"
                />
              </div>
              <div className="col-span-2">
                <Label htmlFor="department">{EMPLOYEE_FORM_MESSAGES.form.labels.department}</Label>
                <Input
                  id="department"
                  value={form.department}
                  onChange={(e) => update({ department: e.target.value })}
                  required
                  className="mt-1"
                />
              </div>
              <div>
                <Label htmlFor="email">{EMPLOYEE_FORM_MESSAGES.form.labels.email}</Label>
                <Input
                  id="email"
                  type="email"
                  value={form.email ?? ""}
                  onChange={(e) => update({ email: e.target.value || undefined })}
                  className="mt-1"
                />
              </div>
              <div>
                <Label htmlFor="applicationDate">{EMPLOYEE_FORM_MESSAGES.form.labels.applicationDate}</Label>
                <Input
                  id="applicationDate"
                  type="date"
                  value={form.applicationDate ?? ""}
                  onChange={(e) => update({ applicationDate: e.target.value || undefined })}
                  className="mt-1"
                />
              </div>
              <div>
                <Label htmlFor="joinedAt">{EMPLOYEE_FORM_MESSAGES.form.labels.joinedAt}</Label>
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

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              {EMPLOYEE_FORM_MESSAGES.form.cancel}
            </Button>
            <Button type="submit">{isEdit ? EMPLOYEE_FORM_MESSAGES.dialog.saveButton : EMPLOYEE_FORM_MESSAGES.dialog.createButton}</Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
