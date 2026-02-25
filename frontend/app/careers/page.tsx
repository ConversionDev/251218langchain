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

      {/* 헤더: workspace와 동일 스타일, 우측 메인 없음 */}
      <header className="relative z-10 flex h-16 items-center border-b border-border/80 bg-white/70 px-6 backdrop-blur-sm dark:bg-background/70">
        <div className="flex items-center gap-3">
          <span className="rounded-md border border-border bg-muted/80 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
            채용·지원
          </span>
          <Link href="/" className="flex items-center gap-2 text-sm">
            <span className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
              AI POWERED HR INTELLIGENCE
            </span>
            <span className="font-bold tracking-tight text-foreground">
              <span className="text-[#14532d] dark:text-emerald-800">HR</span>
              <span className="bg-gradient-to-r from-teal-600 to-emerald-500 bg-clip-text text-transparent dark:from-teal-400 dark:to-emerald-400">
                Insight
              </span>
            </span>
          </Link>
        </div>
      </header>

      {/* 중앙 — 진입 메시지 + 채용 바로가기 */}
      <main className="relative z-10 flex min-h-[calc(100vh-4rem)] flex-col items-center justify-center px-6 py-10 animate-fadeIn">
        <h1 className="text-center text-3xl font-bold tracking-tight text-foreground md:text-4xl">
          함께 성장할 인재를 찾습니다
        </h1>
        <p className="mt-4 max-w-md text-center text-base text-muted-foreground">
          HRInsight과 함께할 분을 기다립니다.
        </p>

        <nav className="mt-10 flex w-full max-w-sm flex-col items-center gap-3 px-4" aria-label="채용 메뉴">
          <Link
            href="/careers/recruit"
            className="inline-flex min-w-[14rem] w-full justify-center rounded-full border-2 border-border bg-card/90 px-8 py-3 text-base font-semibold text-foreground shadow-lg backdrop-blur-sm transition hover:bg-muted hover:border-emerald-400"
          >
            채용
          </Link>
          <Link
            href="/careers/notice"
            className="inline-flex min-w-[14rem] w-full justify-center rounded-full border-2 border-border bg-card/90 px-8 py-3 text-base font-semibold text-foreground shadow-lg backdrop-blur-sm transition hover:bg-muted hover:border-emerald-400"
          >
            공지
          </Link>
          <Link
            href="/careers/faq"
            className="inline-flex min-w-[14rem] w-full justify-center rounded-full border-2 border-border bg-card/90 px-8 py-3 text-base font-semibold text-foreground shadow-lg backdrop-blur-sm transition hover:bg-muted hover:border-emerald-400"
          >
            질의사항
          </Link>
          <Link
            href="/resumes"
            className="inline-flex min-w-[14rem] w-full justify-center rounded-full border-2 border-emerald-400 bg-emerald-500 px-8 py-3 text-base font-semibold text-white shadow-lg transition hover:bg-emerald-600"
          >
            지원내역
          </Link>
        </nav>
      </main>
    </div>
  );
}
