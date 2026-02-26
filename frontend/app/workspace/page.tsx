"use client";

import Link from "next/link";
import Image from "next/image";
import { ExternalLink, FileUp, Mail, Sparkles } from "lucide-react";

export default function WorkspaceHomePage() {
  return (
    <div className="relative min-h-screen overflow-hidden">
      {/* 로그인과 다른 이미지, 같은 밝은 오피스 톤 */}
      <div className="absolute inset-0">
        <Image
          src="https://images.unsplash.com/photo-1524758631624-e2822e304c36?w=1920&q=80"
          alt=""
          fill
          className="object-cover object-center"
          sizes="100vw"
          priority
        />
      </div>
      <div className="absolute inset-0 bg-white/70 dark:bg-background/75" aria-hidden />

      {/* 헤더: 메인과 동일 형식 — 영역·로고 스타일·왼쪽 정렬 */}
      <header className="relative z-10 flex min-h-[4.5rem] items-center justify-between border-b border-[#a8d5c4]/50 bg-white/85 px-6 py-3 backdrop-blur-md dark:border-primary/20 dark:bg-[#0f0f0f]/90 md:px-8 md:py-4">
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
          className="inline-flex items-center gap-1.5 text-sm font-semibold text-slate-700 transition-colors hover:text-slate-900 md:text-base shrink-0 dark:text-slate-300 dark:hover:text-slate-100"
        >
          <ExternalLink className="h-4 w-4" />
          메인
        </Link>
      </header>

      <main className="relative z-10 mx-auto flex min-h-[calc(100vh-4.5rem)] max-w-5xl flex-col items-center justify-center px-4 py-10 animate-fadeIn">
        <div className="grid w-full gap-6 rounded-3xl border border-border bg-card/95 p-6 shadow-xl backdrop-blur-md md:grid-cols-[1.05fr,0.95fr] md:p-8">
          <section className="flex flex-col justify-center">
            <p className="inline-flex w-fit items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs text-emerald-800 dark:border-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-200">
              <Sparkles className="h-3.5 w-3.5" />
              Holo Assistant Online
            </p>
            <h1 className="mt-4 text-2xl font-bold tracking-tight text-foreground md:text-3xl">
              직원 서비스에 접속하시겠습니까?
            </h1>

            <div className="mt-5 space-y-3">
              <div className="rounded-2xl border border-white/80 bg-white p-4 text-foreground shadow-sm dark:border-white/10 dark:bg-white/10 dark:text-card-foreground">
                <p className="text-sm font-medium">업무를 제출하시겠습니까?</p>
                <p className="mt-1 text-sm text-muted-foreground">
                  업무를 제출하시려면{" "}
                  <span className="font-semibold text-foreground">업무 제출</span>
                  을 눌러주세요.
                </p>
              </div>
              <div className="rounded-2xl border border-white/80 bg-white p-4 text-foreground shadow-sm dark:border-white/10 dark:bg-white/10 dark:text-card-foreground">
                <p className="text-sm font-medium">사내 메일에 접속하시겠습니까?</p>
                <p className="mt-1 text-sm text-muted-foreground">
                  메일함과 분석 결과를 확인하려면{" "}
                  <span className="font-semibold text-foreground">사내 메일</span>
                  을 눌러주세요.
                </p>
              </div>
            </div>

            <div className="mt-6 flex flex-wrap gap-3">
              <Link
                href="/workspace/submit"
                className="hero-gradient-hover workspace-hero-btn inline-flex items-center gap-2 rounded-full border-2 border-white/80 bg-white px-6 py-3 text-sm font-semibold text-foreground shadow-sm transition-colors duration-200 dark:border-white/10 dark:bg-white/10"
              >
                업무 제출
                <FileUp className="h-4 w-4" />
              </Link>
              <Link
                href="/workspace/mail"
                className="hero-gradient-hover workspace-hero-btn inline-flex items-center gap-2 rounded-full border-2 border-white/80 bg-white px-6 py-3 text-sm font-semibold text-foreground shadow-sm transition-colors duration-200 dark:border-white/10 dark:bg-white/10"
              >
                사내 메일
                <Mail className="h-4 w-4" />
              </Link>
            </div>
          </section>

          <section className="relative flex items-center justify-center rounded-2xl border border-border bg-white/60 p-4 backdrop-blur-sm dark:bg-white/10">
            <Image
              src="/images/workspace-holo-character.png"
              alt="홀로그램 AI 캐릭터"
              width={540}
              height={540}
              className="relative w-full max-w-[360px] rounded-2xl object-contain"
              priority
            />
          </section>
        </div>
      </main>
    </div>
  );
}
