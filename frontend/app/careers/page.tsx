"use client";

import Link from "next/link";
import Image from "next/image";

export default function CareersEntryPage() {
  return (
    <div className="relative min-h-screen overflow-hidden">
      {/* workspace와 같은 밝은 오피스 톤 (careers 전용 이미지) */}
      <div className="absolute inset-0">
        <Image
          src="https://images.unsplash.com/photo-1504384308090-c894fdcc538d?w=1920&q=80"
          alt=""
          fill
          className="object-cover object-center"
          sizes="100vw"
          priority
        />
      </div>
      <div className="absolute inset-0 bg-white/70 dark:bg-background/75" aria-hidden />

      {/* 헤더: 메인과 동일 형식 — 영역·로고 스타일·왼쪽 정렬 */}
      <header className="relative z-10 flex min-h-[4.5rem] items-center justify-between border-b border-white/30 bg-white/75 px-6 py-3 backdrop-blur-md dark:border-white/10 dark:bg-background/75 md:px-8 md:py-4">
        <div className="flex flex-1 items-center gap-3 md:gap-4">
          <Link href="/" className="flex items-baseline gap-1.5">
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
        </div>
        <Link
          href="/"
          className="text-sm font-semibold text-slate-700 hover:text-slate-900 transition-colors md:text-base shrink-0"
        >
          메인
        </Link>
      </header>

      {/* 중앙 — 진입 메시지 + 채용 바로가기 */}
      <main className="relative z-10 flex min-h-[calc(100vh-4.5rem)] flex-col items-center justify-center px-6 py-10 animate-fadeIn">
        <h1 className="text-center text-3xl font-bold tracking-tight text-foreground md:text-4xl">
          함께 성장할 인재를 찾습니다
        </h1>
        <p className="mt-4 max-w-md text-center text-base text-muted-foreground">
          HRInsight과 함께할 분을 기다립니다.
        </p>

        <nav className="mt-10 flex w-full max-w-sm flex-col items-center gap-3 px-4" aria-label="채용 메뉴">
          <Link
            href="/careers/recruit"
            className="inline-flex min-w-[14rem] w-full justify-center rounded-full border-2 border-white/80 bg-white px-8 py-3 text-base font-semibold text-foreground shadow-lg backdrop-blur-sm transition hover:border-[#a8d5c4] hover:bg-gradient-to-b hover:from-[#e8f5ef] hover:to-[#f0f5f0] dark:border-white/10 dark:bg-white/10"
          >
            채용
          </Link>
          <Link
            href="/careers/notice"
            className="inline-flex min-w-[14rem] w-full justify-center rounded-full border-2 border-white/80 bg-white px-8 py-3 text-base font-semibold text-foreground shadow-lg backdrop-blur-sm transition hover:border-[#a8d5c4] hover:bg-gradient-to-b hover:from-[#e8f5ef] hover:to-[#f0f5f0] dark:border-white/10 dark:bg-white/10"
          >
            공지
          </Link>
          <Link
            href="/careers/faq"
            className="inline-flex min-w-[14rem] w-full justify-center rounded-full border-2 border-white/80 bg-white px-8 py-3 text-base font-semibold text-foreground shadow-lg backdrop-blur-sm transition hover:border-[#a8d5c4] hover:bg-gradient-to-b hover:from-[#e8f5ef] hover:to-[#f0f5f0] dark:border-white/10 dark:bg-white/10"
          >
            질의사항
          </Link>
          <Link
            href="/resumes"
            className="hero-gradient-hover careers-resumes-btn inline-flex min-w-[14rem] w-full justify-center rounded-full border-2 border-white/80 bg-white px-8 py-3 text-base font-semibold text-foreground shadow-lg transition-colors duration-200 dark:border-white/10 dark:bg-white/10"
          >
            지원내역
          </Link>
        </nav>
      </main>
    </div>
  );
}
