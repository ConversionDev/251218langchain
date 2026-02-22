"use client";

import Link from "next/link";
import Image from "next/image";

/** 채용 진입 — 한글 메뉴, 깔끔한 구성 */
function CareersLogoIcon({ className }: { className?: string }) {
  return (
    <span
      className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-emerald-600 ${className ?? ""}`}
      aria-hidden
    >
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

export default function CareersEntryPage() {
  return (
    <div className="relative min-h-screen overflow-hidden">
      {/* 숲 느낌 배경 — 그라데이션 + 이미지 오버레이 */}
      <div className="absolute inset-0 bg-gradient-to-br from-green-900/95 via-emerald-900/90 to-teal-900/95 dark:from-[#0d2818] dark:via-[#0a1f14] dark:to-[#0d2d1a]" />
      <div className="absolute inset-0">
        <Image
          src="https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=1920&q=80"
          alt=""
          fill
          className="object-cover opacity-40 dark:opacity-30"
          sizes="100vw"
          priority
        />
      </div>
      <div className="absolute inset-0 bg-gradient-to-t from-green-950/80 via-transparent to-green-900/60" />

      {/* 헤더 */}
      <header className="relative z-10 flex h-16 items-center justify-between px-6">
        <Link href="/" className="flex items-center gap-3">
          <CareersLogoIcon />
          <span className="font-semibold tracking-tight text-white/95">HRInsight 채용</span>
        </Link>
        <Link
          href="/"
          className="text-sm font-medium text-white/80 hover:text-white"
        >
          메인
        </Link>
      </header>

      {/* 중앙 — 진입 메시지 + 채용 바로가기 + 세로 메뉴 (이전 구성) */}
      <main className="relative z-10 flex min-h-[calc(100vh-4rem)] flex-col items-center justify-center px-6 py-12">
        <h1 className="text-center text-3xl font-bold tracking-tight text-white md:text-4xl">
          함께 성장할 인재를 찾습니다
        </h1>
        <p className="mt-4 max-w-md text-center text-base text-white/80">
          HRInsight과 함께할 분을 기다립니다.
        </p>

        <nav className="mt-10 flex w-full max-w-sm flex-col items-center gap-3 px-4" aria-label="채용 메뉴">
          <Link
            href="/careers/recruit"
            className="inline-flex min-w-[14rem] w-full justify-center rounded-full border-2 border-white/90 bg-white/10 px-8 py-3 text-base font-semibold text-white backdrop-blur-sm transition hover:bg-white/20 hover:border-white"
          >
            채용
          </Link>
          <Link
            href="/careers/notice"
            className="inline-flex min-w-[14rem] w-full justify-center rounded-full border-2 border-white/90 bg-white/10 px-8 py-3 text-base font-semibold text-white backdrop-blur-sm transition hover:bg-white/20 hover:border-white"
          >
            공지
          </Link>
          <Link
            href="/careers/faq"
            className="inline-flex min-w-[14rem] w-full justify-center rounded-full border-2 border-white/90 bg-white/10 px-8 py-3 text-base font-semibold text-white backdrop-blur-sm transition hover:bg-white/20 hover:border-white"
          >
            질의사항
          </Link>
          <Link
            href="/resumes"
            className="inline-flex min-w-[14rem] w-full justify-center rounded-full border-2 border-white/90 bg-white/10 px-8 py-3 text-base font-semibold text-white backdrop-blur-sm transition hover:bg-white/20 hover:border-white"
          >
            지원내역
          </Link>
        </nav>
      </main>
    </div>
  );
}
