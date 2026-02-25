"use client";

import Link from "next/link";
import Image from "next/image";
import { FileUp, Mail, Sparkles } from "lucide-react";

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

      {/* 헤더: 직원 포털 + 로고만 (우측 메인 링크 없음) */}
      <header className="relative z-10 flex h-16 items-center border-b border-border/80 bg-white/70 px-6 backdrop-blur-sm dark:bg-background/70">
        <div className="flex items-center gap-3">
          <span className="rounded-md border border-border bg-muted/80 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
            직원 포털
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

      <main className="relative z-10 mx-auto flex min-h-[calc(100vh-4rem)] max-w-5xl flex-col items-center justify-center px-4 py-10 animate-fadeIn">
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
              <div className="rounded-2xl border border-emerald-200/60 bg-emerald-50/80 p-4 text-foreground dark:border-emerald-800/50 dark:bg-emerald-950/30 dark:text-card-foreground">
                <p className="text-sm font-medium">업무를 제출하시겠습니까?</p>
                <p className="mt-1 text-sm text-muted-foreground">
                  업무를 제출하시려면{" "}
                  <span className="font-semibold text-foreground">업무 제출</span>
                  을 눌러주세요.
                </p>
              </div>
              <div className="rounded-2xl border border-teal-200/60 bg-teal-50/80 p-4 text-foreground dark:border-teal-800/50 dark:bg-teal-950/30 dark:text-card-foreground">
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
                className="inline-flex items-center gap-2 rounded-full border-2 border-border bg-background px-6 py-3 text-sm font-semibold text-foreground transition hover:bg-muted hover:border-emerald-400"
              >
                업무 제출
                <FileUp className="h-4 w-4" />
              </Link>
              <Link
                href="/workspace/mail"
                className="inline-flex items-center gap-2 rounded-full border-2 border-emerald-400 bg-emerald-500 px-6 py-3 text-sm font-semibold text-white transition hover:bg-emerald-600"
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
