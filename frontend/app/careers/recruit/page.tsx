"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { FileText, Search } from "lucide-react";

/** 채용 공고 — 일반 부서 기준(인사·재무·영업·마케팅·개발·IT·경영지원·전략·기획), 한글 메뉴 */

type TabId = "전체" | "신입" | "경력";

interface JobPosting {
  id: string;
  type: TabId;
  department: string;
  title: string;
  startDate: string;
  endDate: string;
  endTime: string;
  daysLeft: number;
}

const MOCK_JOBS: JobPosting[] = [
  { id: "1", type: "경력", department: "인사", title: "인사 부서 인력 기획·채용 담당", startDate: "2026-02-02", endDate: "2026-02-27", endTime: "23:59", daysLeft: 8 },
  { id: "2", type: "경력", department: "재무", title: "재무 부서 회계·재무 분석", startDate: "2026-02-01", endDate: "2026-02-20", endTime: "23:59", daysLeft: 11 },
  { id: "3", type: "신입", department: "영업", title: "영업 부서 신입 채용", startDate: "2026-02-10", endDate: "2026-03-15", endTime: "18:00", daysLeft: 25 },
  { id: "4", type: "경력", department: "마케팅", title: "마케팅 부서 브랜드·디지털 마케팅", startDate: "2026-02-05", endDate: "2026-02-28", endTime: "23:59", daysLeft: 15 },
  { id: "5", type: "신입", department: "개발·IT", title: "개발·IT 부서 신입 개발자", startDate: "2026-02-01", endDate: "2026-03-10", endTime: "18:00", daysLeft: 22 },
  { id: "6", type: "경력", department: "경영지원", title: "경영지원 부서 총무·인프라", startDate: "2026-02-03", endDate: "2026-02-25", endTime: "23:59", daysLeft: 6 },
  { id: "7", type: "경력", department: "전략·기획", title: "전략·기획 부서 기획 담당", startDate: "2026-02-01", endDate: "2026-02-28", endTime: "23:59", daysLeft: 9 },
];

function CareersLogoIcon({ className }: { className?: string }) {
  return (
    <span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-emerald-600 ${className ?? ""}`} aria-hidden>
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className="text-white">
        <circle cx="6" cy="8" r="1.8" fill="currentColor" />
        <line x1="6" y1="8" x2="18" y2="8" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        <circle cx="18" cy="8" r="1.8" fill="currentColor" />
        <line x1="12" y1="8" x2="12" y2="12" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        <circle cx="12" cy="12" r="1.8" fill="currentColor" />
        <circle cx="6" cy="16" r="1.8" fill="currentColor" />
        <line x1="6" y1="16" x2="18" y2="16" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        <circle cx="18" cy="16" r="1.8" fill="currentColor" />
        <line x1="12" y1="16" x2="12" y2="20" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        <circle cx="12" cy="20" r="1.8" fill="currentColor" />
      </svg>
    </span>
  );
}

export default function CareersRecruitPage() {
  const [tab, setTab] = useState<TabId>("전체");
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    let list = MOCK_JOBS.filter((j) => tab === "전체" || j.type === tab);
    if (search.trim()) {
      const q = search.trim().toLowerCase();
      list = list.filter(
        (j) =>
          j.title.toLowerCase().includes(q) ||
          j.department.toLowerCase().includes(q) ||
          j.type.toLowerCase().includes(q)
      );
    }
    return list;
  }, [tab, search]);

  const tabs: TabId[] = ["전체", "신입", "경력"];

  return (
    <div className="min-h-screen bg-white dark:bg-[#0f0f0f]">
      <header className="sticky top-0 z-50 border-b border-slate-200 bg-white dark:border-white/10 dark:bg-[#0f0f0f]">
        <div className="mx-auto flex h-16 max-w-5xl items-center justify-between px-6">
          <Link href="/careers" className="flex items-center gap-3">
            <CareersLogoIcon />
            <div className="flex flex-col">
              <span className="text-xs font-medium text-emerald-700 dark:text-emerald-400">HRInsight 채용</span>
              <span className="font-semibold tracking-tight text-slate-800 dark:text-slate-100">채용</span>
            </div>
          </Link>
          <nav className="flex items-center gap-5">
            <Link href="/resumes" className="flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100">
              <FileText className="h-4 w-4" /> 지원내역
            </Link>
            <Link href="/careers/notice" className="text-sm font-medium text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100">공지</Link>
            <Link href="/careers/faq" className="text-sm font-medium text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100">질의사항</Link>
            <Link href="/careers" className="text-sm font-medium text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100">채용 홈</Link>
            <Link href="/" className="text-sm font-medium text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100">메인</Link>
          </nav>
        </div>
      </header>

      {/* Breadcrumb */}
      <div className="border-b border-slate-200 bg-slate-50/50 dark:border-white/10 dark:bg-[#0a0a0a]/50">
        <div className="mx-auto flex h-10 max-w-5xl items-center gap-2 px-6 text-sm text-slate-600 dark:text-slate-400">
          <Link href="/careers" className="hover:text-slate-900 dark:hover:text-slate-100">채용 홈</Link>
          <span aria-hidden>/</span>
          <span className="font-medium text-slate-800 dark:text-slate-200">채용 공고</span>
        </div>
      </div>

      {/* 탭 + 검색 — 예시처럼 */}
      <div className="border-b border-slate-200 dark:border-white/10">
        <div className="mx-auto flex max-w-5xl flex-col gap-4 px-6 py-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex gap-1">
            {tabs.map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => setTab(t)}
                className={`rounded px-4 py-2 text-sm font-medium transition ${
                  tab === t
                    ? "border border-emerald-600 bg-emerald-50 text-emerald-700 dark:border-emerald-500 dark:bg-emerald-950/40 dark:text-emerald-300"
                    : "border border-transparent text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-white/10"
                }`}
              >
                {t}
              </button>
            ))}
          </div>
          <div className="relative w-full sm:w-48">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="부서·제목 검색"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full rounded border border-slate-300 bg-white py-2 pl-9 pr-3 text-sm dark:border-white/20 dark:bg-[#171717] dark:text-slate-100 dark:placeholder:text-slate-500"
            />
          </div>
        </div>
      </div>

      {/* 공고 개수 + 목록 */}
      <div className="mx-auto max-w-5xl px-6 py-8">
        <p className="mb-6 text-sm text-slate-600 dark:text-slate-400">
          총 <span className="font-semibold text-emerald-600 dark:text-emerald-400">{filtered.length}</span>건의 채용공고가 있습니다.
        </p>

        {filtered.length === 0 ? (
          <p className="py-12 text-center text-slate-500 dark:text-slate-400">조건에 맞는 공고가 없습니다.</p>
        ) : (
          <ul className="space-y-4">
            {filtered.map((job) => (
              <li
                key={job.id}
                className="flex flex-col gap-3 rounded-lg border border-slate-200 bg-white p-5 shadow-sm dark:border-white/10 dark:bg-[#171717] sm:flex-row sm:items-center sm:justify-between"
              >
                <div className="min-w-0 flex-1">
                  <span className="inline-block rounded bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-300">
                    D-{job.daysLeft}
                  </span>
                  <h2 className="mt-2 font-semibold text-slate-900 dark:text-slate-100">
                    [{job.department}] {job.type} · {job.title}
                  </h2>
                  <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                    {job.startDate} ~ {job.endDate} {job.endTime}
                  </p>
                </div>
                <div className="shrink-0">
                  <Link
                    href="/apply"
                    className="inline-flex rounded-lg bg-emerald-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-emerald-700 dark:bg-emerald-500 dark:hover:bg-emerald-600"
                  >
                    지원하기
                  </Link>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
