"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Info } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { Employee, SuccessDNA, IfrsMetrics, Gender, AgeBand, EmploymentType } from "@/modules/shared/types";

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

const defaultDna: SuccessDNA = {
  leadership: 0,
  technical: 0,
  creativity: 0,
  collaboration: 0,
  adaptability: 0,
};

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
    successDna: { ...defaultDna },
    ifrsMetrics: {
      transitionReadyScore: 0,
      skillGap: 0,
      humanCapitalROI: 0,
    },
  });

  useEffect(() => {
    if (employee) {
      setForm({
        ...employee,
        successDna: employee.successDna ?? { ...defaultDna },
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
        successDna: { ...defaultDna },
        ifrsMetrics: { transitionReadyScore: 0, skillGap: 0, humanCapitalROI: 0 },
      });
    }
  }, [employee, nextId, open]);

  const update = (patch: Partial<Employee>) => setForm((prev) => ({ ...prev, ...patch }));
  const updateDna = (patch: Partial<SuccessDNA>) =>
    setForm((prev) => ({
      ...prev,
      successDna: { ...(prev.successDna ?? defaultDna), ...patch },
    }));
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

          {/* 초기 DNA 점수 */}
          <fieldset className="space-y-3">
            <legend className="text-sm font-semibold text-foreground">초기 DNA 점수</legend>
            <div className="grid grid-cols-2 gap-3">
              {(["leadership", "technical", "creativity", "collaboration", "adaptability"] as const).map((key) => (
                <div key={key}>
                  <Label htmlFor={key}>
                    {key === "leadership" && "리더십"}
                    {key === "technical" && "기술력"}
                    {key === "creativity" && "창의성"}
                    {key === "collaboration" && "협업"}
                    {key === "adaptability" && "적응력"}
                  </Label>
                  <Input
                    id={key}
                    type="number"
                    min={0}
                    max={100}
                    value={form.successDna?.[key] ?? 0}
                    onChange={(e) => updateDna({ [key]: Number(e.target.value) || 0 })}
                    className="mt-1"
                  />
                </div>
              ))}
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
