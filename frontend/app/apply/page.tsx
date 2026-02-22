"use client";

import { useState } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { ArrowLeft, Send, Plus, Trash2 } from "lucide-react";
import { createEmployeeApi } from "@/modules/core/services";
import type { Employee, EducationEntry, ExperienceEntry } from "@/modules/shared/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

function nextId(): string {
  return "APPLY-" + Date.now();
}

const emptyEducation = (): EducationEntry => ({
  school: "",
  degree: "",
  field: "",
  startDate: "",
  endDate: "",
});

const emptyExperience = (): ExperienceEntry => ({
  company: "",
  role: "",
  startDate: "",
  endDate: "",
  description: "",
});

const defaultPayload = (): Employee => ({
  id: nextId(),
  name: "",
  jobTitle: "인턴",
  department: "",
  email: "",
  gender: "undisclosed",
  age: undefined,
  employmentType: "new_hire",
  trainingHours: 0,
  disclosureMetrics: {
    transitionReadyScore: 0,
    skillGap: 0,
    humanCapitalROI: 0,
  },
  resume: {
    education: [emptyEducation()],
    experience: [emptyExperience()],
    skills: [],
    certifications: [],
  },
  successDna: {
    leadership: 0,
    technical: 0,
    creativity: 0,
    collaboration: 0,
    adaptability: 0,
  },
});

export default function ApplyPage() {
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [form, setForm] = useState<Employee>(defaultPayload());

  const update = (patch: Partial<Employee>) => setForm((prev) => ({ ...prev, ...patch }));
  const updateResume = (patch: Partial<Employee["resume"]>) =>
    setForm((prev) => ({ ...prev, resume: { ...prev.resume!, ...patch } }));

  const education = form.resume?.education ?? [emptyEducation()];
  const experience = form.resume?.experience ?? [emptyExperience()];

  const setEducation = (list: EducationEntry[]) => updateResume({ education: list });
  const setExperience = (list: ExperienceEntry[]) => updateResume({ experience: list });

  const addEducation = () => setEducation([...education, emptyEducation()]);
  const removeEducation = (index: number) => {
    if (education.length <= 1) return;
    setEducation(education.filter((_, i) => i !== index));
  };

  const addExperience = () => setExperience([...experience, emptyExperience()]);
  const removeExperience = (index: number) => {
    if (experience.length <= 1) return;
    setExperience(experience.filter((_, i) => i !== index));
  };

  const updateEdu = (index: number, patch: Partial<EducationEntry>) => {
    setEducation(
      education.map((e, i) => (i === index ? { ...e, ...patch } : e))
    );
  };
  const updateExp = (index: number, patch: Partial<ExperienceEntry>) => {
    setExperience(
      experience.map((e, i) => (i === index ? { ...e, ...patch } : e))
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name?.trim() || !form.email?.trim() || !form.department?.trim()) {
      toast.error("이름, 이메일, 희망 부서를 입력해 주세요.");
      return;
    }
    setSubmitting(true);
    try {
      // 지원 접수 시 successDna/successDnaReason은 보내지 않음 → DB에 null 저장.
      // 그러면 ATS에서 "AI 분석" 버튼만 보이고, 분석 후에만 평가 근거·심사 중으로 표시됨.
      const payload = {
        ...form,
        id: nextId(),
        employmentType: "new_hire" as const,
        status: "pending" as const,
        joinedAt: undefined as string | undefined,
        successDna: undefined,
        successDnaReason: undefined,
        resume: {
          education: education.filter((e) => e.school?.trim()),
          experience: experience.filter((x) => x.company?.trim()),
          skills: form.resume?.skills ?? [],
          certifications: form.resume?.certifications ?? [],
        },
      };
      await createEmployeeApi(payload);
      setSubmitted(true);
      toast.success("지원서가 접수되었습니다.");
    } catch (err) {
      const message = err instanceof Error ? err.message : "제출에 실패했습니다.";
      toast.error(message);
    } finally {
      setSubmitting(false);
    }
  };

  if (submitted) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-sky-200/60 via-teal-100/80 to-emerald-200/60 dark:from-[#0a0a0a] dark:via-[#0f0f0f] dark:to-[#0a0a0a]">
        <div className="mx-auto max-w-lg px-6 py-16 text-center">
          <div className="mb-6 inline-flex h-14 w-14 items-center justify-center rounded-full bg-emerald-100 text-emerald-600 dark:bg-emerald-900/50 dark:text-emerald-400">
            <Send className="h-7 w-7" />
          </div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">지원이 완료되었습니다</h1>
          <p className="mt-2 text-slate-600 dark:text-slate-400">
            입력하신 내용이 정상적으로 접수되었습니다. 검토 후 연락드리겠습니다.
          </p>
          <Link
            href="/"
            className="mt-8 inline-flex items-center gap-2 rounded-xl border-2 border-slate-300 bg-white px-5 py-2.5 text-sm font-semibold text-slate-800 shadow transition hover:border-emerald-400 hover:bg-emerald-50 dark:border-white/20 dark:bg-[#171717] dark:text-slate-200 dark:hover:border-emerald-500/80 dark:hover:bg-white/10"
          >
            <ArrowLeft className="h-4 w-4" />
            메인으로 돌아가기
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-200/60 via-teal-100/80 to-emerald-200/60 dark:from-[#0a0a0a] dark:via-[#0f0f0f] dark:to-[#0a0a0a]">
      <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6 sm:py-12">
        <Link
          href="/"
          className="mb-6 inline-flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
        >
          <ArrowLeft className="h-4 w-4" />
          메인으로
        </Link>

        <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-lg dark:border-white/10 dark:bg-[#171717] sm:p-8">
          <div className="mb-8 text-center">
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">이력서 지원</h1>
            <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
              아래 항목을 작성한 뒤 제출해 주세요. 검토 후 연락드리겠습니다.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-8">
            {/* 기본 정보 - 2열 그리드, 모바일 1열 */}
            <section>
              <h2 className="mb-4 border-b border-slate-200 pb-2 text-sm font-semibold text-slate-700 dark:border-white/10 dark:text-slate-300">
                기본 정보
              </h2>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <Label htmlFor="name">이름 *</Label>
                  <Input
                    id="name"
                    value={form.name}
                    onChange={(e) => update({ name: e.target.value })}
                    placeholder="홍길동"
                    required
                    className="mt-1"
                    aria-required="true"
                  />
                </div>
                <div>
                  <Label htmlFor="email">이메일 *</Label>
                  <Input
                    id="email"
                    type="email"
                    value={form.email ?? ""}
                    onChange={(e) => update({ email: e.target.value })}
                    placeholder="you@example.com"
                    required
                    className="mt-1"
                    aria-required="true"
                  />
                </div>
                <div>
                  <Label htmlFor="department">희망 부서 *</Label>
                  <Input
                    id="department"
                    value={form.department}
                    onChange={(e) => update({ department: e.target.value })}
                    placeholder="예: 개발, 마케팅, 컨설팅"
                    required
                    className="mt-1"
                    aria-required="true"
                  />
                </div>
                <div>
                  <Label htmlFor="jobTitle">지원 직급</Label>
                  <select
                    id="jobTitle"
                    value={form.jobTitle}
                    onChange={(e) => update({ jobTitle: e.target.value })}
                    className="mt-1 flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm"
                  >
                    <option value="인턴">인턴</option>
                    <option value="사원">사원</option>
                  </select>
                </div>
                <div>
                  <Label htmlFor="gender">성별</Label>
                  <select
                    id="gender"
                    value={form.gender ?? "undisclosed"}
                    onChange={(e) => update({ gender: e.target.value as Employee["gender"] })}
                    className="mt-1 flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm"
                  >
                    <option value="undisclosed">미기입</option>
                    <option value="male">남</option>
                    <option value="female">여</option>
                  </select>
                </div>
                <div>
                  <Label htmlFor="age">만 나이 (선택)</Label>
                  <Input
                    id="age"
                    type="number"
                    min={18}
                    max={99}
                    value={form.age ?? ""}
                    onChange={(e) =>
                      update({ age: e.target.value ? parseInt(e.target.value, 10) : undefined })
                    }
                    placeholder="25"
                    className="mt-1"
                  />
                </div>
              </div>
            </section>

            {/* 학력 - 동적 리스트 */}
            <section>
              <div className="mb-4 flex items-center justify-between border-b border-slate-200 pb-2 dark:border-white/10">
                <h2 className="text-sm font-semibold text-slate-700 dark:text-slate-300">학력</h2>
                <Button type="button" variant="outline" size="sm" onClick={addEducation} className="gap-1">
                  <Plus className="h-3.5 w-3.5" />
                  추가
                </Button>
              </div>
              <div className="space-y-6">
                {education.map((edu, index) => (
                  <div
                    key={index}
                    className="rounded-lg border border-slate-100 bg-slate-50/50 p-4 dark:border-white/10 dark:bg-[#171717]/80"
                  >
                    <div className="mb-3 flex items-center justify-between">
                      <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
                        학력 {index + 1}
                      </span>
                      {education.length > 1 && (
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => removeEducation(index)}
                          className="h-8 gap-1 text-red-600 hover:bg-red-50 hover:text-red-700 dark:hover:bg-red-950/50"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                          삭제
                        </Button>
                      )}
                    </div>
                    <div className="grid gap-4 sm:grid-cols-2">
                      <div className="sm:col-span-2">
                        <Label>학교명</Label>
                        <Input
                          value={edu.school ?? ""}
                          onChange={(e) => updateEdu(index, { school: e.target.value })}
                          placeholder="OO대학교"
                          className="mt-1"
                        />
                      </div>
                      <div>
                        <Label>학위 / 전공</Label>
                        <Input
                          value={edu.degree ?? ""}
                          onChange={(e) => updateEdu(index, { degree: e.target.value })}
                          placeholder="예: 컴퓨터공학 학사"
                          className="mt-1"
                        />
                      </div>
                      <div>
                        <Label>졸업일 (YYYY-MM)</Label>
                        <Input
                          type="month"
                          value={edu.endDate ?? ""}
                          onChange={(e) => updateEdu(index, { endDate: e.target.value })}
                          className="mt-1"
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            {/* 경력/활동 - 동적 리스트 */}
            <section>
              <div className="mb-4 flex items-center justify-between border-b border-slate-200 pb-2 dark:border-white/10">
                <h2 className="text-sm font-semibold text-slate-700 dark:text-slate-300">경력 / 활동 (선택)</h2>
                <Button type="button" variant="outline" size="sm" onClick={addExperience} className="gap-1">
                  <Plus className="h-3.5 w-3.5" />
                  추가
                </Button>
              </div>
              <div className="space-y-6">
                {experience.map((exp, index) => (
                  <div
                    key={index}
                    className="rounded-lg border border-slate-100 bg-slate-50/50 p-4 dark:border-white/10 dark:bg-[#171717]/80"
                  >
                    <div className="mb-3 flex items-center justify-between">
                      <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
                        경력 {index + 1}
                      </span>
                      {experience.length > 1 && (
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => removeExperience(index)}
                          className="h-8 gap-1 text-red-600 hover:bg-red-50 hover:text-red-700 dark:hover:bg-red-950/50"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                          삭제
                        </Button>
                      )}
                    </div>
                    <div className="grid gap-4 sm:grid-cols-2">
                      <div>
                        <Label>회사 / 단체명</Label>
                        <Input
                          value={exp.company ?? ""}
                          onChange={(e) => updateExp(index, { company: e.target.value })}
                          placeholder="예: 스타트업, 동아리"
                          className="mt-1"
                        />
                      </div>
                      <div>
                        <Label>역할</Label>
                        <Input
                          value={exp.role ?? ""}
                          onChange={(e) => updateExp(index, { role: e.target.value })}
                          placeholder="예: 인턴, 팀장"
                          className="mt-1"
                        />
                      </div>
                      <div>
                        <Label>시작일 (YYYY-MM)</Label>
                        <Input
                          type="month"
                          value={exp.startDate ?? ""}
                          onChange={(e) => updateExp(index, { startDate: e.target.value })}
                          className="mt-1"
                        />
                      </div>
                      <div>
                        <Label>종료일 (YYYY-MM)</Label>
                        <Input
                          type="month"
                          value={exp.endDate ?? ""}
                          onChange={(e) => updateExp(index, { endDate: e.target.value })}
                          placeholder="재직 중"
                          className="mt-1"
                        />
                      </div>
                      <div className="sm:col-span-2">
                        <Label>업무 설명 (선택)</Label>
                        <Input
                          value={exp.description ?? ""}
                          onChange={(e) => updateExp(index, { description: e.target.value })}
                          placeholder="담당 업무 요약"
                          className="mt-1"
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <div className="flex flex-wrap items-center gap-3 border-t border-slate-200 pt-6 dark:border-white/10">
              <Button type="submit" disabled={submitting} className="gap-2">
                {submitting ? "제출 중..." : "지원서 제출"}
                <Send className="h-4 w-4" />
              </Button>
              <Link href="/">
                <Button type="button" variant="outline">
                  취소
                </Button>
              </Link>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
