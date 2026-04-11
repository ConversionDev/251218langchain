"use client";

import Link from "next/link";
import { ExternalLink } from "lucide-react";

/** 질의사항 — 한글 메뉴, 깔끔한 Q&A */
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

const FAQ_ITEMS = [
  { q: "지원 방법은 어떻게 되나요?", a: "채용 메뉴에서 원하는 공고의 '지원하기'를 누르면 이력서 작성 페이지로 이동합니다. 항목을 입력한 뒤 제출해 주세요." },
  { q: "지원 내역은 어디서 확인하나요?", a: "지원내역에서 이름과 이메일로 조회하시면 제출한 지원 목록을 볼 수 있습니다." },
  { q: "지원 후 수정이 가능한가요?", a: "제출 후에는 수정이 제한됩니다. 제출 전에 내용을 꼼꼼히 확인해 주세요." },
  { q: "합격 여부는 어떻게 알 수 있나요?", a: "서류 검토 후 개별 연락드립니다." },
];

export default function CareersFaqPage() {
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
          <Link href="/careers/notice" className="text-sm font-semibold text-slate-700 hover:text-slate-900 transition-colors md:text-base">공지</Link>
          <span className="text-sm font-semibold text-slate-900 dark:text-slate-100 md:text-base">질의사항</span>
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
          질의사항
        </h1>
        <ul className="mt-8 space-y-6">
          {FAQ_ITEMS.map((item, i) => (
            <li key={i} className="rounded-lg border border-slate-200 bg-white p-5 dark:border-white/10 dark:bg-[#171717]">
              <h2 className="font-medium text-slate-900 dark:text-slate-100">{item.q}</h2>
              <p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-400">{item.a}</p>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
