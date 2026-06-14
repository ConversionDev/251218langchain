"use client";

import { useState, useCallback, useEffect } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { ArrowLeft, Send, Plus, Trash2, Upload, FileText, CheckCircle2, X } from "lucide-react";
import { createEmployeeApi, checkResumeHashApi, fetchNextEmployeeId } from "@/modules/core/services";
import type { Employee, EducationEntry, ExperienceEntry } from "@/modules/shared/types";
import type { ResumeParseResult } from "@/modules/core/services/resumeToBaseline";
import {
  computeResumeFileHash,
  getCachedResumeResult,
  parseResumeToBaseline,
} from "@/modules/core/services/resumeToBaseline";
import { APPLY_MESSAGES } from "@/modules/shared/constants/messages";
import { RESUME_ACCEPT } from "@/lib/documentExtensions";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

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

/** API/LLM 날짜 문자열을 <input type="month">에 맞는 YYYY-MM으로 정규화 */
function normalizeYearMonthInput(v: string | undefined): string {
  const s = (v ?? "").trim();
  if (!s) return "";
  if (/^\d{4}-\d{2}$/.test(s)) return s;
  if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s.slice(0, 7);
  const slash = s.match(/^(\d{4})[/.\s-](\d{1,2})$/);
  if (slash) {
    const mo = parseInt(slash[2], 10);
    if (mo >= 1 && mo <= 12) return `${slash[1]}-${String(mo).padStart(2, "0")}`;
  }
  const kr = s.match(/^(\d{4})\s*년\s*(\d{1,2})\s*월/);
  if (kr) {
    const mo = parseInt(kr[2], 10);
    if (mo >= 1 && mo <= 12) return `${kr[1]}-${String(mo).padStart(2, "0")}`;
  }
  return "";
}

const defaultPayload = (): Employee => ({
  id: "",
  name: "",
  jobTitle: APPLY_MESSAGES.form.defaultJobTitle,
  department: "",
  email: "",
  gender: "undisclosed",
  age: undefined,
  employmentType: "new_hire",
  trainingHours: undefined,
  disclosureMetrics: undefined,
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

const APPLY_RESUME_STORAGE_KEY = "apply_page_resume";

interface StoredApplyResume {
  fileName: string;
  result: ResumeParseResult;
  fileHash: string | null;
}

function loadStoredApplyResume(): StoredApplyResume | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = sessionStorage.getItem(APPLY_RESUME_STORAGE_KEY);
    return raw ? (JSON.parse(raw) as StoredApplyResume) : null;
  } catch {
    return null;
  }
}

function saveStoredApplyResume(data: StoredApplyResume): void {
  if (typeof window === "undefined") return;
  try {
    sessionStorage.setItem(APPLY_RESUME_STORAGE_KEY, JSON.stringify(data));
  } catch {
    // ignore
  }
}

function clearStoredApplyResume(): void {
  if (typeof window === "undefined") return;
  try {
    sessionStorage.removeItem(APPLY_RESUME_STORAGE_KEY);
  } catch {
    // ignore
  }
}

/** 분석 결과만 보고 비었거나 제출에 쓸 수 없는 항목 라벨 (폼 반영 전·후 동일 기준) */
function missingApplyFieldsFromParseResult(r: ResumeParseResult): string[] {
  const missing: string[] = [];
  if (!(r.name ?? "").trim()) missing.push("이름");
  if (!(r.email ?? "").trim()) missing.push("이메일");
  const deptRaw = (r.department ?? "").trim();
  if (!deptRaw) {
    missing.push("희망 부서");
  } else if (deptRaw.includes("지원할 수 없습니다")) {
    missing.push("희망 부서");
  } else if (deptRaw.includes(APPLY_MESSAGES.form.departmentFallbackKeyword)) {
    missing.push("희망 부서");
  }
  if (!(r.jobTitle ?? "").trim()) missing.push("지원 직급");
  return missing;
}

function warnIfIncompleteExtraction(result: ResumeParseResult): void {
  const labels = missingApplyFieldsFromParseResult(result);
  if (labels.length > 0) {
    toast.warning(APPLY_MESSAGES.toast.incompleteExtraction(labels.join(", ")));
  }
}

export default function ApplyPage() {
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [form, setForm] = useState<Employee>(defaultPayload());
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadPhase, setUploadPhase] = useState<"idle" | "uploading" | "extracting" | "analyzing">("idle");
  const [lastResumeFileHash, setLastResumeFileHash] = useState<string | null>(null);
  const [lastResumeText, setLastResumeText] = useState<string | null>(null);
  const [attachedFileName, setAttachedFileName] = useState<string | null>(null);
  const [hydrated, setHydrated] = useState(false);
  const [isDuplicateResume, setIsDuplicateResume] = useState(false);

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

  /** 이력서 분석 결과를 폼에 반영. 학력/경력은 비어 있으면 기본 1칸 유지 */
  const applyResumeToForm = useCallback((result: ResumeParseResult) => {
    const eduList =
      result.resume?.education?.length && result.resume.education.some((e) => (e as { school?: string }).school?.trim())
        ? result.resume.education.map((e: { school?: string; degree?: string; field?: string; startDate?: string; endDate?: string }) => ({
            school: e.school ?? "",
            degree: e.degree ?? "",
            field: e.field ?? "",
            startDate: normalizeYearMonthInput(e.startDate),
            endDate: normalizeYearMonthInput(e.endDate),
          }))
        : [emptyEducation()];
    const expList =
      result.resume?.experience?.length && result.resume.experience.some((x) => (x as { company?: string }).company?.trim())
        ? result.resume.experience.map((x: { company?: string; role?: string; startDate?: string; endDate?: string; description?: string }) => ({
            company: x.company ?? "",
            role: x.role ?? "",
            startDate: normalizeYearMonthInput(x.startDate),
            endDate: normalizeYearMonthInput(x.endDate),
            description: x.description ?? "",
          }))
        : [emptyExperience()];
    setForm((prev) => ({
      ...prev,
      name: result.name ?? prev.name,
      jobTitle: result.jobTitle ?? prev.jobTitle,
      department:
        (result.department?.includes(APPLY_MESSAGES.form.departmentFallbackKeyword)
          ? APPLY_MESSAGES.form.departmentFallbackValue
          : result.department) ?? prev.department,
      email: result.email ?? prev.email,
      phone: result.phone ?? prev.phone,
      birthDate: result.birthDate ?? prev.birthDate,
      gender: result.gender ?? prev.gender,
      age: result.age ?? prev.age,
      employmentType: result.employmentType ?? "new_hire",
      resume: {
        education: eduList,
        experience: expList,
        skills: result.resume?.skills ?? prev.resume?.skills ?? [],
        certifications: result.resume?.certifications ?? prev.resume?.certifications ?? [],
      },
    }));
  }, []);

  const handleResumeFile = useCallback(
    async (file: File) => {
      let fileHash: string | null = null;
      try {
        fileHash = await computeResumeFileHash(file);
        setLastResumeFileHash(fileHash);
      } catch {
        setLastResumeFileHash(null);
      }
      const cached = getCachedResumeResult(file);
      if (cached) {
        applyResumeToForm(cached);
        warnIfIncompleteExtraction(cached);
        setAttachedFileName(file.name);
        if (cached._resumeText) setLastResumeText(cached._resumeText);
        saveStoredApplyResume({ fileName: file.name, result: cached, fileHash });
        toast.success(APPLY_MESSAGES.toast.cachedLoaded);
        if (fileHash) {
          checkResumeHashApi(fileHash).then(({ exists }) => {
            setIsDuplicateResume(!!exists);
            if (exists) toast.warning(APPLY_MESSAGES.toast.duplicateResume);
          });
        } else setIsDuplicateResume(false);
        return;
      }
      setUploadLoading(true);
      setUploadPhase("uploading");
      const t1 = window.setTimeout(() => setUploadPhase("extracting"), 600);
      const t2 = window.setTimeout(() => setUploadPhase("analyzing"), 2200);
      try {
        const { result } = await parseResumeToBaseline(file);
        applyResumeToForm(result);
        warnIfIncompleteExtraction(result);
        setAttachedFileName(file.name);
        if (result._resumeText) setLastResumeText(result._resumeText);
        saveStoredApplyResume({ fileName: file.name, result, fileHash });
        toast.success(APPLY_MESSAGES.toast.analyzed);
        if (fileHash) {
          checkResumeHashApi(fileHash).then(({ exists }) => {
            setIsDuplicateResume(!!exists);
            if (exists) toast.warning(APPLY_MESSAGES.toast.duplicateResume);
          });
        } else setIsDuplicateResume(false);
      } catch {
        toast.error(APPLY_MESSAGES.toast.uploadFailed);
      } finally {
        window.clearTimeout(t1);
        window.clearTimeout(t2);
        setUploadLoading(false);
        setUploadPhase("idle");
      }
    },
    [applyResumeToForm]
  );

  /** 다른 화면 갔다 와도 저장된 이력서 복원 */
  useEffect(() => {
    if (typeof window === "undefined") return;
    setHydrated(true);
  }, []);
  useEffect(() => {
    if (!hydrated) return;
    const stored = loadStoredApplyResume();
    if (stored?.result) {
      applyResumeToForm(stored.result);
      setAttachedFileName(stored.fileName);
      if (stored.fileHash) setLastResumeFileHash(stored.fileHash);
      if (stored.fileHash) {
        checkResumeHashApi(stored.fileHash).then(({ exists }) => setIsDuplicateResume(!!exists));
      } else setIsDuplicateResume(false);
    }
  }, [hydrated, applyResumeToForm]);

  const removeAttachment = useCallback(() => {
    clearStoredApplyResume();
    setForm(defaultPayload());
    setAttachedFileName(null);
    setLastResumeFileHash(null);
    setLastResumeText(null);
    setIsDuplicateResume(false);
    toast.info(APPLY_MESSAGES.toast.attachmentRemoved);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name?.trim() || !form.email?.trim() || !form.department?.trim()) {
      toast.error(APPLY_MESSAGES.form.requiredFieldError);
      return;
    }
    setSubmitting(true);
    try {
      const employeeId = await fetchNextEmployeeId();
      // 지원 접수 시 successDna/successDnaReason은 보내지 않음 → DB에 null 저장.
      // 그러면 ATS에서 "AI 분석" 버튼만 보이고, 분석 후에만 평가 근거·심사 중으로 표시됨.
      const payload = {
        ...form,
        id: employeeId,
        employmentType: "new_hire" as const,
        status: "pending" as const,
        joinedAt: undefined as string | undefined,
        successDna: undefined,
        successDnaReason: undefined,
        resumeFileHash: lastResumeFileHash ?? undefined,
        resumeText: lastResumeText ?? undefined,
        resume: {
          education: education.filter((e) => e.school?.trim()),
          experience: experience.filter((x) => x.company?.trim()),
          skills: form.resume?.skills ?? [],
          certifications: form.resume?.certifications ?? [],
        },
      };
      await createEmployeeApi(payload);
      setSubmitted(true);
      clearStoredApplyResume();
      toast.success(APPLY_MESSAGES.toast.submitted);
    } catch (err) {
      console.error("[지원서 제출 오류]", err);
      const message = err instanceof Error ? err.message : APPLY_MESSAGES.toast.submitFailed;
      if (message.includes("이미 등록") || (err as Error & { existing?: unknown }).existing) {
        setIsDuplicateResume(true);
      }
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
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">{APPLY_MESSAGES.page.submittedTitle}</h1>
          <p className="mt-2 text-slate-600 dark:text-slate-400">
            {APPLY_MESSAGES.page.submittedDescription}
          </p>
          <Link
            href="/hr"
            className="hero-gradient-hover mt-8 inline-flex items-center gap-2 rounded-xl border-2 border-[#a8d5c4] bg-gradient-to-b from-[#e8f5ef] to-[#f0f5f0] px-5 py-2.5 text-sm font-semibold text-slate-800 shadow transition-colors dark:border-emerald-800/50 dark:text-slate-900"
          >
            <ArrowLeft className="h-4 w-4" />
            {APPLY_MESSAGES.page.backToMain}
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#e8f5ef] to-[#f0f5f0] dark:bg-background">
      {/* 헤더: 로고(왼쪽) + 채용 공고(가운데), 메인 링크 없음 — 로고 클릭 시 메인 이동 */}
      <header className="sticky top-0 z-10 flex min-h-[4.5rem] items-center justify-between border-b border-[#a8d5c4]/50 bg-white/85 px-6 py-3 backdrop-blur-md dark:border-primary/20 dark:bg-[#0f0f0f]/90 md:px-8 md:py-4">
        <Link href="/hr" className="flex items-baseline gap-1.5 shrink-0">
          <span className="text-[11px] font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
            AI Powered HR Intelligence
          </span>
          <span className="text-base font-bold tracking-tight text-[#14532d] dark:text-emerald-800 md:text-lg">HR</span>
          <span
            className="bg-gradient-to-r from-teal-600 to-emerald-500 bg-clip-text text-base font-bold tracking-tight text-transparent dark:from-teal-400 dark:to-emerald-400 md:text-lg"
            style={{ WebkitBackgroundClip: "text" }}
          >
            Insight
          </span>
        </Link>
        <Link
          href="/careers/recruit"
          className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-sm font-semibold text-slate-700 hover:text-slate-900 transition-colors md:text-base"
        >
          채용 공고
        </Link>
        <div className="w-[1px] shrink-0 md:min-w-[120px]" aria-hidden />
      </header>
      <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6 sm:py-12">

        <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-lg dark:border-white/10 dark:bg-[#171717] sm:p-8">
          <div className="mb-8 text-center">
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">{APPLY_MESSAGES.form.title}</h1>
            <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
              {APPLY_MESSAGES.form.description}
            </p>
          </div>

          {/* 이력서 업로드 — 첨부 시 표시 + 다른 화면 갔다 와도 복원 */}
          <section className="mb-8">
            <h2 className="mb-3 flex items-center gap-2 border-b border-slate-200 pb-2 text-sm font-semibold text-slate-700 dark:border-white/10 dark:text-slate-300">
              <FileText className="h-4 w-4 text-slate-500 dark:text-slate-400" />
              {APPLY_MESSAGES.uploadSection.title}
            </h2>
            <p className="mb-3 text-xs text-slate-500 dark:text-slate-400">
              {APPLY_MESSAGES.uploadSection.description}
            </p>

            {attachedFileName ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between gap-3 rounded-xl border border-emerald-200 bg-emerald-50/80 px-4 py-3 dark:border-emerald-800/60 dark:bg-emerald-950/40">
                  <div className="flex min-w-0 items-center gap-3">
                    <CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-600 dark:text-emerald-400" />
                    <span className="truncate text-sm font-medium text-emerald-800 dark:text-emerald-200">
                      {APPLY_MESSAGES.uploadSection.attachedPrefix} {attachedFileName}
                    </span>
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={removeAttachment}
                    className="shrink-0 gap-1.5 text-slate-600 hover:bg-emerald-100 hover:text-slate-800 dark:text-slate-400 dark:hover:bg-emerald-900/60"
                    aria-label={APPLY_MESSAGES.uploadSection.removeAriaLabel}
                  >
                    <X className="h-4 w-4" />
                    {APPLY_MESSAGES.uploadSection.removeButton}
                  </Button>
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  {APPLY_MESSAGES.uploadSection.autofilledHint}
                </p>
              </div>
            ) : null}

            <div
              onDrop={(e) => {
                e.preventDefault();
                const file = e.dataTransfer?.files?.[0];
                if (file) handleResumeFile(file);
              }}
              onDragOver={(e) => e.preventDefault()}
              className={`mt-3 flex min-h-[120px] flex-col items-center justify-center rounded-xl border-2 border-dashed p-6 text-center transition-colors ${
                uploadLoading
                  ? "cursor-wait border-[#a8d5c4] bg-[#e8f5ef]/80 dark:border-emerald-700/50 dark:bg-emerald-950/30"
                  : "border-slate-200 bg-slate-50/60 hover:border-[#a8d5c4] hover:bg-[#e8f5ef]/50 dark:border-white/15 dark:bg-white/5 dark:hover:border-emerald-700/50 dark:hover:bg-emerald-950/20"
              } ${attachedFileName ? "min-h-[80px] p-4" : ""}`}
            >
              <input
                type="file"
                accept={RESUME_ACCEPT}
                className="hidden"
                id="apply-resume-upload"
                disabled={uploadLoading}
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) handleResumeFile(f);
                  e.target.value = "";
                }}
              />
              <label
                htmlFor="apply-resume-upload"
                className={uploadLoading ? "pointer-events-none cursor-wait" : "cursor-pointer"}
              >
                <Upload className={`mx-auto text-slate-400 dark:text-slate-500 ${attachedFileName ? "h-7 w-7" : "h-10 w-10"}`} />
                <p className={`mt-2 font-medium text-slate-700 dark:text-slate-300 ${attachedFileName ? "text-sm" : ""}`}>
                  {uploadLoading
                    ? uploadPhase === "uploading"
                      ? APPLY_MESSAGES.upload.phaseUploading
                      : uploadPhase === "extracting"
                        ? APPLY_MESSAGES.upload.phaseExtracting
                        : APPLY_MESSAGES.upload.phaseAnalyzing
                    : attachedFileName
                      ? APPLY_MESSAGES.upload.switchResume
                      : APPLY_MESSAGES.upload.idle}
                </p>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                  PDF, Word(.docx), TXT, 이미지(스캔본 OCR)
                </p>
              </label>
            </div>
          </section>

          <form onSubmit={handleSubmit} className="space-y-8">
            {/* 기본 정보 - 2열 그리드, 모바일 1열 */}
            <section>
              <h2 className="mb-4 border-b border-slate-200 pb-2 text-sm font-semibold text-slate-700 dark:border-white/10 dark:text-slate-300">
                {APPLY_MESSAGES.form.basicInfoTitle}
              </h2>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <Label htmlFor="name">{APPLY_MESSAGES.form.nameLabel}</Label>
                  <Input
                    id="name"
                    value={form.name}
                    onChange={(e) => update({ name: e.target.value })}
                    placeholder={APPLY_MESSAGES.form.namePlaceholder}
                    required
                    className="mt-1"
                    aria-required="true"
                  />
                </div>
                <div>
                  <Label htmlFor="email">{APPLY_MESSAGES.form.emailLabel}</Label>
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
                  <Label htmlFor="phone">{APPLY_MESSAGES.form.phoneLabel}</Label>
                  <Input
                    id="phone"
                    type="tel"
                    value={form.phone ?? ""}
                    onChange={(e) => update({ phone: e.target.value })}
                    placeholder="010-0000-0000"
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor="birthDate">{APPLY_MESSAGES.form.birthDateLabel}</Label>
                  <Input
                    id="birthDate"
                    type="date"
                    value={form.birthDate ?? ""}
                    onChange={(e) => update({ birthDate: e.target.value })}
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor="department">{APPLY_MESSAGES.form.departmentLabel}</Label>
                  <Input
                    id="department"
                    value={form.department}
                    onChange={(e) => update({ department: e.target.value })}
                    placeholder={APPLY_MESSAGES.form.departmentPlaceholder}
                    required
                    className="mt-1"
                    aria-required="true"
                  />
                </div>
                <div>
                  <Label htmlFor="jobTitle">{APPLY_MESSAGES.form.jobTitleLabel}</Label>
                  <select
                    id="jobTitle"
                    value={form.jobTitle}
                    onChange={(e) => update({ jobTitle: e.target.value })}
                    className="mt-1 flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm"
                  >
                    <option value={APPLY_MESSAGES.form.jobTitleIntern}>{APPLY_MESSAGES.form.jobTitleIntern}</option>
                    <option value={APPLY_MESSAGES.form.jobTitleStaff}>{APPLY_MESSAGES.form.jobTitleStaff}</option>
                  </select>
                </div>
                <div>
                  <Label htmlFor="gender">{APPLY_MESSAGES.form.genderLabel}</Label>
                  <select
                    id="gender"
                    value={form.gender ?? "undisclosed"}
                    onChange={(e) => update({ gender: e.target.value as Employee["gender"] })}
                    className="mt-1 flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm"
                  >
                    <option value="undisclosed">{APPLY_MESSAGES.form.genderUndisclosed}</option>
                    <option value="male">{APPLY_MESSAGES.form.genderMale}</option>
                    <option value="female">{APPLY_MESSAGES.form.genderFemale}</option>
                  </select>
                </div>
                <div>
                  <Label htmlFor="age">{APPLY_MESSAGES.form.ageLabel}</Label>
                  <Input
                    id="age"
                    type="number"
                    min={18}
                    max={99}
                    value={form.age ?? ""}
                    onChange={(e) =>
                      update({ age: e.target.value ? parseInt(e.target.value, 10) : undefined })
                    }
                    placeholder={APPLY_MESSAGES.form.agePlaceholder}
                    className="mt-1"
                  />
                </div>
              </div>
            </section>

            {/* 학력 - 동적 리스트 */}
            <section>
              <div className="mb-4 flex items-center justify-between border-b border-slate-200 pb-2 dark:border-white/10">
                <h2 className="text-sm font-semibold text-slate-700 dark:text-slate-300">{APPLY_MESSAGES.educationSection.title}</h2>
                <Button type="button" variant="outline" size="sm" onClick={addEducation} className="gap-1">
                  <Plus className="h-3.5 w-3.5" />
                  {APPLY_MESSAGES.common.add}
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
                        {APPLY_MESSAGES.educationSection.itemLabel(index)}
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
                          {APPLY_MESSAGES.common.remove}
                        </Button>
                      )}
                    </div>
                    <div className="grid gap-4 sm:grid-cols-2">
                      <div className="sm:col-span-2">
                        <Label>{APPLY_MESSAGES.educationSection.schoolLabel}</Label>
                        <Input
                          value={edu.school ?? ""}
                          onChange={(e) => updateEdu(index, { school: e.target.value })}
                          placeholder={APPLY_MESSAGES.educationSection.schoolPlaceholder}
                          className="mt-1"
                        />
                      </div>
                      <div>
                        <Label>{APPLY_MESSAGES.educationSection.degreeLabel}</Label>
                        <Input
                          value={edu.degree ?? ""}
                          onChange={(e) => updateEdu(index, { degree: e.target.value })}
                          placeholder={APPLY_MESSAGES.educationSection.degreePlaceholder}
                          className="mt-1"
                        />
                      </div>
                      <div>
                        <Label>{APPLY_MESSAGES.educationSection.fieldLabel}</Label>
                        <Input
                          value={edu.field ?? ""}
                          onChange={(e) => updateEdu(index, { field: e.target.value })}
                          placeholder={APPLY_MESSAGES.educationSection.fieldPlaceholder}
                          className="mt-1"
                        />
                      </div>
                      <div>
                        <Label>{APPLY_MESSAGES.educationSection.graduationLabel}</Label>
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
                <h2 className="text-sm font-semibold text-slate-700 dark:text-slate-300">{APPLY_MESSAGES.experienceSection.title}</h2>
                <Button type="button" variant="outline" size="sm" onClick={addExperience} className="gap-1">
                  <Plus className="h-3.5 w-3.5" />
                  {APPLY_MESSAGES.common.add}
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
                        {APPLY_MESSAGES.experienceSection.itemLabel(index)}
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
                          {APPLY_MESSAGES.common.remove}
                        </Button>
                      )}
                    </div>
                    <div className="grid gap-4 sm:grid-cols-2">
                      <div>
                        <Label>{APPLY_MESSAGES.experienceSection.companyLabel}</Label>
                        <Input
                          value={exp.company ?? ""}
                          onChange={(e) => updateExp(index, { company: e.target.value })}
                          placeholder={APPLY_MESSAGES.experienceSection.companyPlaceholder}
                          className="mt-1"
                        />
                      </div>
                      <div>
                        <Label>{APPLY_MESSAGES.experienceSection.roleLabel}</Label>
                        <Input
                          value={exp.role ?? ""}
                          onChange={(e) => updateExp(index, { role: e.target.value })}
                          placeholder={APPLY_MESSAGES.experienceSection.rolePlaceholder}
                          className="mt-1"
                        />
                      </div>
                      <div>
                        <Label>{APPLY_MESSAGES.experienceSection.startDateLabel}</Label>
                        <Input
                          type="month"
                          value={exp.startDate ?? ""}
                          onChange={(e) => updateExp(index, { startDate: e.target.value })}
                          className="mt-1"
                        />
                      </div>
                      <div>
                        <Label>{APPLY_MESSAGES.experienceSection.endDateLabel}</Label>
                        <Input
                          type="month"
                          value={exp.endDate ?? ""}
                          onChange={(e) => updateExp(index, { endDate: e.target.value })}
                          placeholder={APPLY_MESSAGES.experienceSection.endDatePlaceholder}
                          className="mt-1"
                        />
                      </div>
                      <div className="sm:col-span-2">
                        <Label>{APPLY_MESSAGES.experienceSection.descriptionLabel}</Label>
                        <Input
                          value={exp.description ?? ""}
                          onChange={(e) => updateExp(index, { description: e.target.value })}
                          placeholder={APPLY_MESSAGES.experienceSection.descriptionPlaceholder}
                          className="mt-1"
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <div className="flex flex-wrap items-center gap-3 border-t border-slate-200 pt-6 dark:border-white/10">
              {isDuplicateResume && (
                <p className="w-full rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800 dark:border-amber-800/60 dark:bg-amber-950/40 dark:text-amber-200">
                  {APPLY_MESSAGES.duplicateBlockNotice}
                </p>
              )}
              <Button type="submit" disabled={submitting || isDuplicateResume} className="hero-gradient-hover gap-2 bg-emerald-600 hover:bg-emerald-600">
                {submitting
                  ? APPLY_MESSAGES.submitButton.submitting
                  : isDuplicateResume
                    ? APPLY_MESSAGES.submitButton.blockedDuplicate
                    : APPLY_MESSAGES.submitButton.submit}
                <Send className="h-4 w-4" />
              </Button>
              <Link href="/careers/recruit">
                <Button type="button" variant="outline" className="border-[#a8d5c4] text-slate-700 hover:bg-[#e8f5ef]/80 hover:border-[#a8d5c4] dark:border-white/20 dark:hover:bg-white/10">
                  {APPLY_MESSAGES.common.cancel}
                </Button>
              </Link>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
