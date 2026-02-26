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
    <div className="flex min-h-screen flex-col bg-white dark:bg-background">
      {/* 헤더: 채용 홈과 동일 — 채용지원 배지 + 한 줄 로고 + nav + 메인 */}
      <header className="sticky top-0 z-50 flex min-h-[4.5rem] items-center justify-between border-b border-white/30 bg-white/75 px-6 py-3 backdrop-blur-md dark:border-white/10 dark:bg-background/75 md:px-8 md:py-4">
        <div className="flex flex-1 items-center gap-3 md:gap-4">
          <Link href="/" className="flex items-baseline gap-1.5 shrink-0">
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
          <nav aria-label="채용 메뉴" className="flex items-center gap-6 md:gap-8">
            <Link href="/careers" className="text-sm font-semibold text-slate-700 hover:text-slate-900 transition-colors md:text-base">
              채용 홈
            </Link>
            <span className="text-sm font-semibold text-slate-900 dark:text-slate-100 md:text-base">
              채용 공고
            </span>
            <Link href="/careers/notice" className="text-sm font-semibold text-slate-700 hover:text-slate-900 transition-colors md:text-base">
              공지
            </Link>
            <Link href="/careers/faq" className="text-sm font-semibold text-slate-700 hover:text-slate-900 transition-colors md:text-base">
              질의사항
            </Link>
            <Link href="/resumes" className="flex items-center gap-2 text-sm font-semibold text-slate-700 hover:text-slate-900 transition-colors md:text-base">
              <FileText className="h-4 w-4" /> 지원내역
            </Link>
          </nav>
        </div>
        <Link
          href="/"
          className="text-sm font-semibold text-slate-700 hover:text-slate-900 transition-colors md:text-base shrink-0"
        >
          메인
        </Link>
      </header>

      {/* 탭 + 검색 — 배경 흰색, 탭은 테두리로만 구분 */}
      <div className="border-b border-slate-200/80 bg-white dark:border-white/10 dark:bg-[#171717]">
        <div className="mx-auto flex max-w-5xl flex-col gap-4 px-6 py-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex gap-1">
            {tabs.map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => setTab(t)}
                className={`rounded border px-4 py-2 text-sm font-medium transition ${
                  tab === t
                    ? "border-[#7eb89e] bg-[#e8f5ef] text-slate-800 dark:border-emerald-600/70 dark:bg-[#e8f5ef]/40 dark:text-slate-100"
                    : "border-slate-200 bg-transparent text-slate-600 hover:border-[#a8d5c4]/60 hover:text-slate-900 dark:border-white/20 dark:text-slate-400 dark:hover:border-[#a8d5c4]/50 dark:hover:text-slate-100"
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

      {/* 공고 개수 + 목록 — 탭 바와 이어지는 흰색 영역 */}
      <div className="bg-white dark:bg-[#171717]">
        <div className="mx-auto max-w-5xl px-6 py-8">
          <p className="mb-6 text-sm text-slate-600 dark:text-slate-400">
            총 <span className="font-semibold text-foreground">{filtered.length}</span>건의 채용공고가 있습니다.
          </p>

          {filtered.length === 0 ? (
            <p className="py-12 text-center text-slate-500 dark:text-slate-400">조건에 맞는 공고가 없습니다.</p>
          ) : (
            <ul className="space-y-4">
              {filtered.map((job) => (
                <li
                  key={job.id}
                  className="flex flex-col gap-3 rounded-lg border border-slate-200 bg-[#e8f5ef]/50 p-5 shadow-sm dark:border-white/10 dark:bg-[#1a1a1a] sm:flex-row sm:items-center sm:justify-between"
                >
                <div className="min-w-0 flex-1">
                  <span className="inline-block rounded border border-slate-200 bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground dark:border-white/10 dark:bg-white/5 dark:text-slate-300">
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
                    className="recruit-apply-btn inline-flex rounded-lg border-2 border-[#5a9b76] bg-[#b8dfce] px-5 py-2.5 text-sm font-semibold text-slate-800 transition-colors dark:border-emerald-600 dark:bg-[#2d5a45]/30 dark:text-slate-100"
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

      {/* 푸터 — 연두 톤만 하단에 적용 */}
      <footer className="mt-auto border-t border-slate-200 bg-gradient-to-b from-[#e8f5ef] to-[#f0f5f0] py-6 dark:border-white/10 dark:from-[#1a2e24] dark:to-[#0f1f18]">
        <div className="mx-auto max-w-5xl px-6 text-center text-sm text-slate-600 dark:text-slate-400">
          © 2026 HRInsight. 차세대 인적자본 관리 시스템
        </div>
      </footer>
    </div>
  );
}
