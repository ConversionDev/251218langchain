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

  const update = (patch: Partial<Employee>) => setForm((prev) => ({ ...prev, ...patch }));

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
