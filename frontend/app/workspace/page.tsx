"use client";

import Link from "next/link";
import Image from "next/image";
import {
  ArrowRight,
  FileUp,
  Mail,
  Sparkles,
} from "lucide-react";

export default function WorkspaceHomePage() {
  return (
    <div className="relative min-h-screen overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-[#0d2e1f]/95 via-[#0a2518]/90 to-[#0b3221]/95" />
      <div className="absolute inset-0">
        <Image
          src="https://images.unsplash.com/photo-1511497584788-876760111969?w=1920&q=80"
          alt=""
          fill
          className="object-cover opacity-35"
          sizes="100vw"
          priority
        />
      </div>
      <div className="absolute inset-0 bg-gradient-to-t from-[#031109]/80 via-[#052214]/35 to-[#052518]/70" />

      <header className="relative z-10 flex h-16 items-center justify-between px-6">
        <Link href="/" className="inline-flex items-center gap-2 text-sm font-semibold text-white/95">
          <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500 text-white">
            <Sparkles className="h-4 w-4" />
          </span>
          HRInsight 직원 서비스
        </Link>
        <Link href="/" className="text-sm font-medium text-white/80 hover:text-white">
          메인
        </Link>
      </header>

      <main className="relative z-10 mx-auto flex min-h-[calc(100vh-4rem)] w-full max-w-6xl flex-col items-center justify-center px-4 py-12">
        <div className="grid w-full max-w-5xl gap-6 rounded-3xl border border-emerald-300/30 bg-white/10 p-5 backdrop-blur-md md:grid-cols-[1.05fr,0.95fr] md:p-7">
          <section className="flex flex-col justify-center">
            <p className="inline-flex w-fit items-center gap-1.5 rounded-full border border-white/30 bg-white/10 px-3 py-1 text-xs text-white/90">
              <Sparkles className="h-3.5 w-3.5" />
              Holo Assistant Online
            </p>
            <h1 className="mt-4 text-2xl font-bold tracking-tight text-white md:text-3xl">
              직원 서비스에 접속하시겠습니까?
            </h1>

            <div className="mt-5 space-y-3">
              <div className="rounded-2xl border border-emerald-200/35 bg-emerald-900/25 p-4 text-white/90">
                <p className="text-sm font-medium">업무를 제출하시겠습니까?</p>
                <p className="mt-1 text-sm text-white/80">
                  업무를 제출하시려면 <span className="font-semibold text-white">업무 제출</span>을 눌러주세요.
                </p>
              </div>
              <div className="rounded-2xl border border-teal-200/35 bg-teal-900/25 p-4 text-white/90">
                <p className="text-sm font-medium">사내 메일에 접속하시겠습니까?</p>
                <p className="mt-1 text-sm text-white/80">
                  메일함과 분석 결과를 확인하려면 <span className="font-semibold text-white">사내 메일</span>을 눌러주세요.
                </p>
              </div>
            </div>

            <div className="mt-6 flex flex-wrap gap-3">
              <Link
                href="/workspace/submit"
                className="inline-flex items-center gap-2 rounded-full border border-white/60 bg-white/20 px-6 py-3 text-sm font-semibold text-white transition hover:bg-white/30"
              >
                업무 제출
                <FileUp className="h-4 w-4" />
              </Link>
              <Link
                href="/workspace/mail"
                className="inline-flex items-center gap-2 rounded-full border border-emerald-300/80 bg-emerald-400/20 px-6 py-3 text-sm font-semibold text-white transition hover:bg-emerald-400/30"
              >
                사내 메일
                <Mail className="h-4 w-4" />
              </Link>
            </div>
          </section>

          <section className="relative flex items-center justify-center rounded-2xl border border-emerald-300/30 bg-gradient-to-b from-white/10 to-emerald-900/20 p-4">
            <div className="pointer-events-none absolute inset-x-10 bottom-4 h-3 rounded-full bg-emerald-400/60 blur-md" />
            <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_30%,rgba(52,211,153,0.25),transparent_55%)]" />
            <Image
              src="/images/workspace-holo-character.png"
              alt="홀로그램 AI 캐릭터"
              width={540}
              height={540}
              className="relative w-full max-w-[360px] rounded-2xl object-contain drop-shadow-[0_0_18px_rgba(74,222,128,0.45)]"
              priority
            />
          </section>
        </div>
      </main>
    </div>
  );
}
