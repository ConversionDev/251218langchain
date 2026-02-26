"use client";

import { Suspense, useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import { useStore } from "@/store/useStore";
import { useHydrated } from "@/hooks/use-hydrated";
import { getRegularEmployees } from "@/modules/shared/utils/employeeAggregates";
import { submitActivity, getTextTypeLabel, type ActivityTextType } from "@/modules/performance/services/activityServices";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const TEXT_TYPES: { value: ActivityTextType; label: string }[] = [
  { value: "meeting", label: "회의록" },
  { value: "report", label: "보고서" },
];

function currentPeriod(): string {
  const now = new Date();
  return `${now.getFullYear()}-Q${Math.floor(now.getMonth() / 3) + 1}`;
}

function SubmitForm() {
  const hydrated = useHydrated();
  const searchParams = useSearchParams();
  const { employees } = useStore();
  const regularEmployees = getRegularEmployees(employees);
  const [employeeId, setEmployeeId] = useState("");
  const [textType, setTextType] = useState<ActivityTextType>("meeting");
  const [content, setContent] = useState("");
  const [tagsStr, setTagsStr] = useState("");
  const [period, setPeriod] = useState(currentPeriod());
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const fromUrl = searchParams.get("employeeId");
    if (fromUrl) setEmployeeId(fromUrl);
    else if (regularEmployees.length > 0)
      setEmployeeId((prev) => (prev && regularEmployees.some((e) => e.id === prev) ? prev : regularEmployees[0].id));
  }, [searchParams, regularEmployees]);

  useEffect(() => {
    const fromType = searchParams.get("textType");
    if (fromType === "meeting" || fromType === "report") {
      setTextType(fromType);
    }
  }, [searchParams]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const raw = content.trim();
    if (!raw) { toast.error("본문을 입력해주세요."); return; }
    if (!employeeId) { toast.error("직원을 선택해주세요."); return; }
    setSubmitting(true);
    try {
      const tags = tagsStr.trim() ? tagsStr.split(/[,，\s]+/).map((t) => t.trim()).filter(Boolean) : undefined;
      await submitActivity({ employeeId, textType, content: raw, period, tags });
      toast.success(`${getTextTypeLabel(textType)} 제출이 완료되었습니다.`);
      setContent("");
      setTagsStr("");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "제출에 실패했습니다.");
    } finally {
      setSubmitting(false);
    }
  };

  if (!hydrated) return null;

  return (
    <div className="flex min-h-[calc(100vh-4.5rem)] flex-col items-center justify-center py-6">
      <div className="mx-auto w-full max-w-3xl">
        <div className="rounded-xl border border-[#a8d5c4] bg-white shadow-sm dark:border-primary/30 dark:bg-card">
        <div className="border-b border-[#a8d5c4]/60 px-5 py-4 dark:border-primary/20">
          <h1 className="text-lg font-semibold text-slate-900 dark:text-foreground">업무 제출</h1>
          <p className="mt-0.5 text-sm text-slate-500 dark:text-muted-foreground">
            회의록·보고서를 등록하면 성과 활동 데이터로 저장됩니다.
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            {TEXT_TYPES.map((t) => (
              <Button
                key={t.value}
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setTextType(t.value)}
                className={`h-8 border-[#a8d5c4]/80 dark:border-primary/30 dark:hover:bg-primary/10 ${
                  textType === t.value ? "border-[#a8d5c4] bg-[#e8f5ef] font-medium dark:bg-primary/20 dark:border-primary/40" : ""
                }`}
              >
                {t.label} 작성
              </Button>
            ))}
          </div>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-5">
          <div className="space-y-2">
            <Label htmlFor="employeeId" className="text-slate-700 dark:text-muted-foreground">직원</Label>
            <Select value={employeeId && regularEmployees.some((e) => e.id === employeeId) ? employeeId : undefined} onValueChange={setEmployeeId} required>
              <SelectTrigger id="employeeId" className="w-full border-[#a8d5c4]/60 dark:border-primary/30"><SelectValue placeholder="직원 선택" /></SelectTrigger>
              <SelectContent className="max-h-64">
                {regularEmployees.map((e) => <SelectItem key={e.id} value={e.id}>{e.name} ({e.id})</SelectItem>)}
              </SelectContent>
            </Select>
            {regularEmployees.length === 0 && <p className="text-xs text-amber-600 dark:text-amber-400">등록된 직원이 없습니다.</p>}
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="textType" className="text-slate-700 dark:text-muted-foreground">유형</Label>
              <Select value={textType} onValueChange={(v) => setTextType(v as ActivityTextType)}>
                <SelectTrigger id="textType" className="border-[#a8d5c4]/60 dark:border-primary/30"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {TEXT_TYPES.map((t) => <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="period" className="text-slate-700 dark:text-muted-foreground">분기</Label>
              <Input id="period" value={period} onChange={(e) => setPeriod(e.target.value)} placeholder="2026-Q1" className="border-[#a8d5c4]/60 dark:border-primary/30" />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="content" className="text-slate-700 dark:text-muted-foreground">본문</Label>
            <Textarea id="content" value={content} onChange={(e) => setContent(e.target.value)} placeholder="회의 내용, 보고서 요약 등을 입력하세요." rows={10} className="resize-none border-[#a8d5c4]/60 dark:border-primary/30" required />
          </div>
          <div className="space-y-2">
            <Label htmlFor="tags" className="text-slate-700 dark:text-muted-foreground">태그 (쉼표 구분)</Label>
            <Input id="tags" value={tagsStr} onChange={(e) => setTagsStr(e.target.value)} placeholder="예: 프로젝트A, 협업" className="border-[#a8d5c4]/60 dark:border-primary/30" />
          </div>
          <div className="flex flex-wrap items-center gap-3 pt-1">
            <Button
              type="submit"
              variant="outline"
              disabled={submitting || regularEmployees.length === 0}
              className="hero-gradient-hover border-2 border-[#a8d5c4] bg-[#e8f5ef] text-slate-800 hover:border-[#a8d5c4] dark:border-primary/40 dark:bg-primary/15 dark:text-foreground"
            >
              {submitting ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />제출 중...</> : "제출하기"}
            </Button>
            <p className="text-xs text-slate-500 dark:text-muted-foreground">
              분기 형식 YYYY-QN · 태그는 쉼표로 구분하면 검색에 유리합니다.
            </p>
          </div>
        </form>
        </div>
      </div>
    </div>
  );
}

export default function SubmitPage() {
  return <Suspense fallback={<div className="flex items-center justify-center py-12 text-slate-500 dark:text-muted-foreground">로딩 중...</div>}><SubmitForm /></Suspense>;
}
