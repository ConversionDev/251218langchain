"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { FileText, Search } from "lucide-react";
import { useStore } from "@/store/useStore";
import { useHydrated } from "@/hooks/use-hydrated";
import { getRegularEmployees } from "@/modules/shared/utils/employeeAggregates";
import {
  fetchMyActivities,
  getTextTypeLabel,
  type ActivityRecord,
  type ActivityTextType,
} from "@/modules/performance/services/activityServices";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";

const TEXT_FILTER: { value: ActivityTextType | "all"; label: string }[] = [
  { value: "all", label: "전체" },
  { value: "meeting", label: "회의록" },
  { value: "report", label: "보고서" },
  { value: "email", label: "이메일" },
];

function MyActivitiesContent() {
  const hydrated = useHydrated();
  const searchParams = useSearchParams();
  const { employees } = useStore();
  const regularEmployees = getRegularEmployees(employees);

  const [employeeId, setEmployeeId] = useState("");
  const [textType, setTextType] = useState<ActivityTextType | "all">("all");
  const [activities, setActivities] = useState<ActivityRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");

  useEffect(() => {
    const fromUrl = searchParams.get("employeeId");
    if (fromUrl) setEmployeeId(fromUrl);
    else if (regularEmployees.length > 0)
      setEmployeeId((prev) => (prev && regularEmployees.some((e) => e.id === prev) ? prev : regularEmployees[0].id));
  }, [searchParams, regularEmployees]);

  useEffect(() => {
    if (!employeeId) {
      setActivities([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    fetchMyActivities(employeeId, {
      textType: textType === "all" ? undefined : textType,
      limit: 100,
    })
      .then(setActivities)
      .catch(() => setActivities([]))
      .finally(() => setLoading(false));
  }, [employeeId, textType]);

  const filteredActivities = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return activities;
    return activities.filter((a) => {
      const tagText = (a.tags ?? []).join(" ").toLowerCase();
      return (
        a.content.toLowerCase().includes(q) ||
        a.period.toLowerCase().includes(q) ||
        getTextTypeLabel(a.textType).toLowerCase().includes(q) ||
        tagText.includes(q)
      );
    });
  }, [activities, query]);

  if (!hydrated) return null;

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-white/10 dark:bg-[#141518]">
        <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100">
          제출함
        </h1>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
          제출한 기록을 검색하고 유형별로 확인할 수 있습니다.
        </p>

        <div className="mt-4 grid gap-3 lg:grid-cols-[minmax(0,1fr),auto,auto]">
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="본문, 태그, 분기 검색"
              className="pl-9"
            />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-slate-600 dark:text-slate-400">직원</span>
            <Select
              value={employeeId && regularEmployees.some((e) => e.id === employeeId) ? employeeId : undefined}
              onValueChange={setEmployeeId}
            >
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="직원 선택" />
              </SelectTrigger>
              <SelectContent className="max-h-64">
                {regularEmployees.map((e) => (
                  <SelectItem key={e.id} value={e.id}>
                    {e.name} ({e.id})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-slate-600 dark:text-slate-400">유형</span>
            <Select value={textType} onValueChange={(v) => setTextType(v as ActivityTextType | "all")}>
              <SelectTrigger className="w-[120px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {TEXT_FILTER.map((t) => (
                  <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </section>

      {!employeeId ? (
        <p className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-200">
          직원을 선택하면 제출 목록이 표시됩니다.
        </p>
      ) : loading ? (
        <div className="flex items-center justify-center py-12 text-slate-500">
          로딩 중...
        </div>
      ) : filteredActivities.length === 0 ? (
        <p className="rounded-lg border border-slate-200 bg-slate-50 p-6 text-center text-sm text-slate-600 dark:border-white/10 dark:bg-white/5 dark:text-slate-400">
          검색 조건에 맞는 제출 기록이 없습니다.
        </p>
      ) : (
        <ul className="space-y-3">
          {filteredActivities.map((a) => (
            <li
              key={a.id}
              className="flex items-start gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-white/10 dark:bg-[#141518]"
            >
              <FileText className="h-5 w-5 shrink-0 text-slate-400" />
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="outline">{getTextTypeLabel(a.textType)}</Badge>
                  <span className="text-sm text-slate-500">{a.period}</span>
                  {a.id.startsWith("SUB-") && (
                    <span className="text-[10px] text-slate-400">제출</span>
                  )}
                </div>
                <p className="mt-1 line-clamp-2 text-sm text-slate-700 dark:text-slate-300">
                  {a.content}
                </p>
                {a.tags && a.tags.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {a.tags.map((tag, i) => (
                      <Badge key={i} variant="secondary" className="text-[10px]">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function MyActivitiesPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center py-12 text-slate-500">로딩 중...</div>}>
      <MyActivitiesContent />
    </Suspense>
  );
}
