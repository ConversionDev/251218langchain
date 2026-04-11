"use client";

import Link from "next/link";
import { ExternalLink } from "lucide-react";

/** 공지 — 한글 메뉴, 깔끔한 목록 */
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

const NOTICE_ITEMS = [
  { title: "2026년 상반기 채용 안내", date: "2026-02-01", id: "1" },
  { title: "채용 시스템 점검 안내", date: "2026-01-15", id: "2" },
  { title: "지원서 제출 시 유의사항", date: "2026-01-10", id: "3" },
];

export default function CareersNoticePage() {
  return (
    <div className="min-h-screen bg-white dark:bg-[#0f0f0f]">
      <header className="sticky top-0 z-50 flex min-h-[4.5rem] items-center justify-between border-b border-[#a8d5c4]/50 bg-white/85 px-6 py-3 backdrop-blur-md dark:border-primary/20 dark:bg-[#0f0f0f]/90 md:px-8 md:py-4">
        {/* 왼쪽: 로고 */}
        <Link href="/hr" className="flex items-baseline gap-1.5 shrink-0">
          <span className="text-[11px] font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">AI Powered HR Intelligence</span>
          <span className="text-base font-bold tracking-tight text-[#14532d] dark:text-emerald-800 md:text-lg">HR</span>
          <span className="bg-gradient-to-r from-teal-600 to-emerald-500 bg-clip-text text-base font-bold tracking-tight text-transparent dark:from-teal-400 dark:to-emerald-400 md:text-lg" style={{ WebkitBackgroundClip: "text" }}>Insight</span>
        </Link>
        {/* 중앙: 네비게이션 */}
        <nav aria-label="채용 메뉴" className="absolute left-1/2 -translate-x-1/2 flex items-center gap-6 md:gap-8">
          <Link href="/careers" className="text-sm font-semibold text-slate-700 hover:text-slate-900 transition-colors md:text-base">채용 홈</Link>
          <Link href="/careers/recruit" className="text-sm font-semibold text-slate-700 hover:text-slate-900 transition-colors md:text-base">채용 공고</Link>
          <span className="text-sm font-semibold text-slate-900 dark:text-slate-100 md:text-base">공지</span>
          <Link href="/careers/faq" className="text-sm font-semibold text-slate-700 hover:text-slate-900 transition-colors md:text-base">질의사항</Link>
          <Link href="/resumes" className="text-sm font-semibold text-slate-700 hover:text-slate-900 transition-colors md:text-base">
            지원내역
          </Link>
        </nav>
        {/* 오른쪽: 메인 */}
        <Link href="/hr" className="inline-flex items-center gap-1.5 text-sm font-semibold text-slate-700 transition-colors hover:text-slate-900 md:text-base shrink-0 dark:text-slate-300 dark:hover:text-slate-100">
          <ExternalLink className="h-4 w-4" /> 메인
        </Link>
      </header>

      <div className="mx-auto max-w-3xl px-6 py-10">
        <h1 className="border-b border-slate-200 pb-3 text-xl font-semibold text-slate-900 dark:border-white/10 dark:text-slate-100">
          공지
        </h1>
        <div className="mt-6 overflow-x-auto rounded-lg border border-slate-200 dark:border-white/10">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50 dark:border-white/10 dark:bg-[#171717]">
                <th className="px-4 py-3 text-left font-semibold text-slate-700 dark:text-slate-300">제목</th>
                <th className="px-4 py-3 text-left font-semibold text-slate-700 dark:text-slate-300">등록일</th>
              </tr>
            </thead>
            <tbody>
              {NOTICE_ITEMS.map((n) => (
                <tr key={n.id} className="border-b border-slate-100 dark:border-white/5">
                  <td className="px-4 py-3">
                    <Link href="#" className="text-slate-900 hover:underline dark:text-slate-100">
                      {n.title}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-400">{n.date}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
