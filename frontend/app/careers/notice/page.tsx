"use client";

import Link from "next/link";
import { ExternalLink, FileText } from "lucide-react";

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
        <div className="mx-auto flex w-full max-w-4xl items-center justify-between">
          <Link href="/careers" className="flex items-center gap-3">
            <CareersLogoIcon />
            <span className="font-semibold tracking-tight text-slate-800 dark:text-slate-100">HRInsight 채용 · 공지</span>
          </Link>
          <nav className="flex items-center gap-5">
            <Link href="/careers/recruit" className="text-sm text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100">채용</Link>
            <Link href="/careers/faq" className="text-sm text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100">질의사항</Link>
            <Link href="/resumes" className="flex items-center gap-2 text-sm text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100">
              <FileText className="h-4 w-4" /> 지원내역
            </Link>
            <Link href="/hr" className="inline-flex items-center gap-1.5 text-sm font-semibold text-slate-700 transition-colors hover:text-slate-900 dark:text-slate-300 dark:hover:text-slate-100">
              <ExternalLink className="h-4 w-4" />
              메인
            </Link>
          </nav>
        </div>
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
