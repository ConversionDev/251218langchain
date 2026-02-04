"use client";

import { useCallback, useEffect, useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import type { Resume, EducationEntry, ExperienceEntry, SkillEntry, CertificationEntry } from "@/modules/shared/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const emptyEducation = (): EducationEntry => ({
  school: "",
  degree: "학사",
  startDate: "",
  endDate: undefined,
});
const emptyExperience = (): ExperienceEntry => ({
  company: "",
  role: "",
  startDate: "",
  endDate: undefined,
  description: undefined,
});
const emptySkill = (): SkillEntry => ({ name: "", level: undefined });
const emptyCert = (): CertificationEntry => ({ name: "", issuer: undefined, date: undefined });

interface ResumeEditFormProps {
  initialResume: Resume;
  onResumeChange: (resume: Resume) => void;
}

export function ResumeEditForm({ initialResume, onResumeChange }: ResumeEditFormProps) {
  const [resume, setResume] = useState<Resume>(initialResume);

  useEffect(() => {
    setResume(initialResume);
  }, [initialResume]);

  const emit = useCallback(
    (next: Resume) => {
      setResume(next);
      onResumeChange(next);
    },
    [onResumeChange]
  );

  const updateEducation = useCallback(
    (i: number, patch: Partial<EducationEntry>) => {
      const next = { ...resume, education: resume.education.slice() };
      next.education[i] = { ...next.education[i], ...patch };
      emit(next);
    },
    [resume, emit]
  );
  const addEducation = useCallback(() => {
    emit({ ...resume, education: [...resume.education, emptyEducation()] });
  }, [resume, emit]);
  const removeEducation = useCallback(
    (i: number) => {
      const next = resume.education.filter((_, j) => j !== i);
      emit({ ...resume, education: next });
    },
    [resume, emit]
  );

  const updateExperience = useCallback(
    (i: number, patch: Partial<ExperienceEntry>) => {
      const next = { ...resume, experience: resume.experience.slice() };
      next.experience[i] = { ...next.experience[i], ...patch };
      emit(next);
    },
    [resume, emit]
  );
  const addExperience = useCallback(() => {
    emit({ ...resume, experience: [...resume.experience, emptyExperience()] });
  }, [resume, emit]);
  const removeExperience = useCallback(
    (i: number) => {
      const next = resume.experience.filter((_, j) => j !== i);
      emit({ ...resume, experience: next });
    },
    [resume, emit]
  );

  const updateSkill = useCallback(
    (i: number, patch: Partial<SkillEntry>) => {
      const next = { ...resume, skills: resume.skills.slice() };
      next.skills[i] = { ...next.skills[i], ...patch };
      emit(next);
    },
    [resume, emit]
  );
  const addSkill = useCallback(() => {
    emit({ ...resume, skills: [...resume.skills, emptySkill()] });
  }, [resume, emit]);
  const removeSkill = useCallback(
    (i: number) => {
      const next = resume.skills.filter((_, j) => j !== i);
      emit({ ...resume, skills: next });
    },
    [resume, emit]
  );

  const updateCert = useCallback(
    (i: number, patch: Partial<CertificationEntry>) => {
      const next = { ...resume, certifications: resume.certifications.slice() };
      next.certifications[i] = { ...next.certifications[i], ...patch };
      emit(next);
    },
    [resume, emit]
  );
  const addCert = useCallback(() => {
    emit({ ...resume, certifications: [...resume.certifications, emptyCert()] });
  }, [resume, emit]);
  const removeCert = useCallback(
    (i: number) => {
      const next = resume.certifications.filter((_, j) => j !== i);
      emit({ ...resume, certifications: next });
    },
    [resume, emit]
  );

  return (
    <div className="flex flex-1 flex-col gap-6 overflow-y-auto pb-4">
      <section>
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-semibold text-foreground">학력</h4>
          <Button type="button" variant="ghost" className="h-7 px-2 text-xs" onClick={addEducation}>
            <Plus className="mr-1 h-3.5 w-3.5" /> 추가
          </Button>
        </div>
        <ul className="mt-2 space-y-3">
          {resume.education.map((ed, i) => (
            <li key={i} className="rounded-lg border border-border bg-muted/20 p-3">
              <div className="flex justify-end">
                <Button type="button" variant="ghost" className="h-6 w-6 p-0 text-muted-foreground" onClick={() => removeEducation(i)}>
                  <Trash2 className="h-3.5 w-3.5" />
                </Button>
              </div>
              <div className="grid gap-2">
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <Label className="text-xs">학교</Label>
                    <Input value={ed.school} onChange={(e) => updateEducation(i, { school: e.target.value })} className="h-8 text-sm" placeholder="학교명" />
                  </div>
                  <div>
                    <Label className="text-xs">학위</Label>
                    <Input value={ed.degree} onChange={(e) => updateEducation(i, { degree: e.target.value })} className="h-8 text-sm" placeholder="학사/석사" />
                  </div>
                </div>
                <div>
                  <Label className="text-xs">전공/분야</Label>
                  <Input value={ed.field ?? ""} onChange={(e) => updateEducation(i, { field: e.target.value || undefined })} className="h-8 text-sm" placeholder="전공" />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <Label className="text-xs">시작</Label>
                    <Input value={ed.startDate} onChange={(e) => updateEducation(i, { startDate: e.target.value })} className="h-8 text-sm" placeholder="YYYY-MM" />
                  </div>
                  <div>
                    <Label className="text-xs">종료</Label>
                    <Input value={ed.endDate ?? ""} onChange={(e) => updateEducation(i, { endDate: e.target.value || undefined })} className="h-8 text-sm" placeholder="YYYY-MM 또는 재학" />
                  </div>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </section>

      <section>
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-semibold text-foreground">경력</h4>
          <Button type="button" variant="ghost" className="h-7 px-2 text-xs" onClick={addExperience}>
            <Plus className="mr-1 h-3.5 w-3.5" /> 추가
          </Button>
        </div>
        <ul className="mt-2 space-y-3">
          {resume.experience.map((ex, i) => (
            <li key={i} className="rounded-lg border border-border bg-muted/20 p-3">
              <div className="flex justify-end">
                <Button type="button" variant="ghost" className="h-6 w-6 p-0 text-muted-foreground" onClick={() => removeExperience(i)}>
                  <Trash2 className="h-3.5 w-3.5" />
                </Button>
              </div>
              <div className="grid gap-2">
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <Label className="text-xs">회사</Label>
                    <Input value={ex.company} onChange={(e) => updateExperience(i, { company: e.target.value })} className="h-8 text-sm" placeholder="회사명" />
                  </div>
                  <div>
                    <Label className="text-xs">직함</Label>
                    <Input value={ex.role} onChange={(e) => updateExperience(i, { role: e.target.value })} className="h-8 text-sm" placeholder="역할" />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <Label className="text-xs">시작</Label>
                    <Input value={ex.startDate} onChange={(e) => updateExperience(i, { startDate: e.target.value })} className="h-8 text-sm" placeholder="YYYY-MM" />
                  </div>
                  <div>
                    <Label className="text-xs">종료</Label>
                    <Input value={ex.endDate ?? ""} onChange={(e) => updateExperience(i, { endDate: e.target.value || undefined })} className="h-8 text-sm" placeholder="YYYY-MM 또는 재직" />
                  </div>
                </div>
                <div>
                  <Label className="text-xs">설명</Label>
                  <Input value={ex.description ?? ""} onChange={(e) => updateExperience(i, { description: e.target.value || undefined })} className="h-8 text-sm" placeholder="업무 내용" />
                </div>
              </div>
            </li>
          ))}
        </ul>
      </section>

      <section>
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-semibold text-foreground">기술</h4>
          <Button type="button" variant="ghost" className="h-7 px-2 text-xs" onClick={addSkill}>
            <Plus className="mr-1 h-3.5 w-3.5" /> 추가
          </Button>
        </div>
        <ul className="mt-2 space-y-2">
          {resume.skills.map((s, i) => (
            <li key={i} className="flex items-center gap-2">
              <Input value={s.name} onChange={(e) => updateSkill(i, { name: e.target.value })} className="h-8 flex-1 text-sm" placeholder="기술명" />
              <Input value={s.level ?? ""} onChange={(e) => updateSkill(i, { level: e.target.value || undefined })} className="h-8 w-20 text-sm" placeholder="수준" />
              <Button type="button" variant="ghost" className="h-8 w-8 shrink-0 p-0" onClick={() => removeSkill(i)}>
                <Trash2 className="h-3.5 w-3.5 text-muted-foreground" />
              </Button>
            </li>
          ))}
        </ul>
      </section>

      <section>
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-semibold text-foreground">자격증</h4>
          <Button type="button" variant="ghost" className="h-7 px-2 text-xs" onClick={addCert}>
            <Plus className="mr-1 h-3.5 w-3.5" /> 추가
          </Button>
        </div>
        <ul className="mt-2 space-y-2">
          {resume.certifications.map((c, i) => (
            <li key={i} className="flex flex-wrap items-center gap-2">
              <Input value={c.name} onChange={(e) => updateCert(i, { name: e.target.value })} className="h-8 w-36 text-sm" placeholder="자격명" />
              <Input value={c.issuer ?? ""} onChange={(e) => updateCert(i, { issuer: e.target.value || undefined })} className="h-8 w-24 text-sm" placeholder="발급기관" />
              <Input value={c.date ?? ""} onChange={(e) => updateCert(i, { date: e.target.value || undefined })} className="h-8 w-24 text-sm" placeholder="YYYY-MM" />
              <Button type="button" variant="ghost" className="h-8 w-8 shrink-0 p-0" onClick={() => removeCert(i)}>
                <Trash2 className="h-3.5 w-3.5 text-muted-foreground" />
              </Button>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
