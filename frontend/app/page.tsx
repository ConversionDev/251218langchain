"use client";

import Link from "next/link";
import Image from "next/image";
import {
  ArrowRight,
  FileText,
  Search,
  BarChart3,
  Database,
  BriefcaseBusiness,
} from "lucide-react";

const FEATURES_ID = "features";

/** 헤더용 로고: 초록 사각 + 연결형 아이콘 (토글/연결 감성) */
function LogoIcon({ className }: { className?: string }) {
  return (
    <span
      className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-emerald-500 ${className ?? ""}`}
      aria-hidden
    >
      <svg
        width="18"
        height="18"
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="text-white"
      >
        {/* 위쪽 가로선: 양끝 원, 중앙에서 아래 짧은 세로선 + 원 */}
        <circle cx="6" cy="8" r="1.8" fill="currentColor" />
        <line x1="6" y1="8" x2="18" y2="8" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        <circle cx="18" cy="8" r="1.8" fill="currentColor" />
        <line x1="12" y1="8" x2="12" y2="12" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        <circle cx="12" cy="12" r="1.8" fill="currentColor" />
        {/* 아래쪽 가로선: 동일 구조 */}
        <circle cx="6" cy="16" r="1.8" fill="currentColor" />
        <line x1="6" y1="16" x2="18" y2="16" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        <circle cx="18" cy="16" r="1.8" fill="currentColor" />
        <line x1="12" y1="16" x2="12" y2="20" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        <circle cx="12" cy="20" r="1.8" fill="currentColor" />
      </svg>
    </span>
  );
}

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-200/60 via-teal-100/80 to-emerald-200/60 dark:from-[#0a0a0a] dark:via-[#0f0f0f] dark:to-[#0a0a0a]">
      {/* Header - 구분선 최소화, 배경은 그라데이션과 자연스럽게 블렌드 */}
      <header className="sticky top-0 z-50 border-b border-slate-200/20 bg-white/50 backdrop-blur-md dark:border-white/10 dark:bg-[#0f0f0f]/90">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
          <Link href="/" className="flex items-center gap-3">
            <LogoIcon />
            <div className="flex flex-col">
              <span className="text-[11px] font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
                AI Powered HR Intelligence
              </span>
              <span className="text-lg font-semibold tracking-tight text-slate-800 dark:text-slate-100">
                HRInsight
              </span>
            </div>
          </Link>
          <nav className="flex items-center">
            <a
              href={`#${FEATURES_ID}`}
              className="text-sm font-medium text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white transition-colors"
            >
              기능 보기
            </a>
          </nav>
        </div>
      </header>

      {/* Hero - 구분선 없이 그라데이션만 자연스럽게 */}
      <section className="relative overflow-hidden bg-transparent">
        <div className="mx-auto flex max-w-6xl flex-col px-6 py-16 md:flex-row md:items-center md:gap-16 md:py-24">
          <div className="flex-1">
            <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-slate-100 md:text-4xl lg:text-5xl leading-tight">
              <span className="block">지능형 인적자본 솔루션,</span>
              <span className="mt-1.5 block">
                <span className="text-emerald-600 dark:text-emerald-400">HRInsight</span>
                과 함께
              </span>
            </h1>
            <p className="mt-6 max-w-lg text-lg leading-[1.7] text-slate-700 dark:text-slate-300">
              AI가 분석한 이력서와 공시 지표로 최고의 인재를 찾아보세요. RAG·LLM·Success DNA 역량 분석과 ISO 30414·IFRS S2 대응까지 한 곳에서 관리합니다.
            </p>
            <div className="mt-8 space-y-4">
              <div>
                <Link
                  href="/dashboard"
                  className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-emerald-600 px-6 py-3.5 text-base font-semibold text-white shadow-lg transition-all duration-200 ease-out hover:-translate-y-2 hover:scale-[1.05] hover:shadow-xl active:scale-[0.98]"
                >
                  관리자 시작
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
              <div className="flex flex-wrap items-center gap-3 border-t border-slate-200/60 pt-4 dark:border-white/10">
                <span className="mr-1 text-sm font-medium text-slate-500 dark:text-slate-400">지원자 · 직원</span>
                <Link
                  href="/careers"
                  className="inline-flex items-center gap-2 rounded-xl border-2 border-emerald-500/60 bg-emerald-50 px-5 py-3 text-base font-semibold text-emerald-800 shadow-md transition-all duration-200 ease-out hover:-translate-y-2 hover:scale-[1.05] hover:shadow-xl hover:bg-emerald-100 active:scale-[0.98] dark:border-emerald-500/40 dark:bg-emerald-950/40 dark:text-emerald-100 dark:hover:bg-emerald-900/50"
                >
                  이력서 지원하기
                  <FileText className="h-4 w-4" />
                </Link>
                <Link
                  href="/workspace"
                  className="inline-flex items-center gap-2 rounded-xl border border-slate-300 bg-white/85 px-5 py-3 text-base font-semibold text-slate-800 shadow-md transition-all duration-200 ease-out hover:-translate-y-2 hover:scale-[1.05] hover:shadow-xl hover:bg-white active:scale-[0.98] dark:border-white/15 dark:bg-white/5 dark:text-slate-100 dark:hover:bg-white/10"
                >
                  직원 서비스 바로가기
                  <BriefcaseBusiness className="h-4 w-4" />
                </Link>
              </div>
            </div>
          </div>
          {/* 캐릭터/비주얼 영역: 나중에 AI 어시스턴트 캐릭터 이미지로 교체 시 그대로 어울리도록 글래스·초록 글로우 톤 유지 */}
          <div className="relative mt-12 flex flex-1 justify-center md:mt-0">
            <div className="character-panel relative aspect-[4/3] w-full min-w-[280px] max-w-md overflow-hidden rounded-2xl ring-2 ring-white/50 backdrop-blur-sm dark:ring-emerald-500/10">
              <Image
                src="https://images.unsplash.com/photo-1600880292203-757bb62b4baf?w=800&q=80"
                alt="인사와 IT가 함께하는 현대적 업무·협업 환경"
                fill
                className="object-cover"
                sizes="(max-width: 768px) 100vw,  min(400px, 50vw)"
                priority
              />
              {/* 캐릭터 배치 시 하단 초록 톤 바가 일체감 있음 (선택) */}
              <div className="absolute inset-x-0 bottom-0 h-1 bg-gradient-to-r from-transparent via-emerald-400/60 to-transparent dark:via-emerald-500/40" aria-hidden />
            </div>
          </div>
        </div>
      </section>

      {/* Feature intro + RAG & LLM */}
      <section
        id={FEATURES_ID}
        className="scroll-mt-20 bg-transparent"
      >
        <div className="mx-auto max-w-6xl px-6 py-16">
          <h2 className="text-center text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 md:text-3xl">
            RAG와 LLM으로 HR 인사이트를 발견하세요
          </h2>
          <p className="mx-auto mt-5 max-w-2xl text-center text-lg leading-[1.7] text-slate-700 dark:text-slate-300">
            이력서·공시·역량 데이터를 벡터 검색(RAG)과 LLM으로 연결하고, Fast MCP 기반 도구 호출로 정확한 분석과 인재 매칭을 실현합니다.
          </p>

          <div className="mt-12 grid gap-8 md:grid-cols-3">
            <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-md transition-all duration-200 ease-out hover:-translate-y-2 hover:scale-[1.02] hover:border-emerald-200 hover:bg-emerald-50/50 hover:shadow-xl dark:border-white/10 dark:bg-[#171717] dark:hover:border-emerald-900/50 dark:hover:bg-emerald-950/20">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-500/10 text-blue-600 dark:text-blue-400">
                <Search className="h-6 w-6" />
              </div>
              <h3 className="mt-4 text-lg font-semibold leading-tight tracking-tight text-slate-900 dark:text-slate-100">
                정확한 인재 매칭
              </h3>
              <p className="mt-3 text-[15px] leading-[1.65] text-slate-600 dark:text-slate-400">
                LLM이 분석한 이력서와 Success DNA(리더십·기술력·창의성·협업·적응력) 역량 점수를 기반으로 벡터 유사도 검색(FAISS·pgvector)으로 인재를 추천해 채용 시간을 단축하고 정확도를 높입니다.
              </p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-md transition-all duration-200 ease-out hover:-translate-y-2 hover:scale-[1.02] hover:border-emerald-200 hover:bg-emerald-50/50 hover:shadow-xl dark:border-white/10 dark:bg-[#171717] dark:hover:border-emerald-900/50 dark:hover:bg-emerald-950/20">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                <BarChart3 className="h-6 w-6" />
              </div>
              <h3 className="mt-4 text-lg font-semibold tracking-tight text-slate-900 dark:text-slate-100">
                간편한 공시 리포팅
              </h3>
              <p className="mt-3 text-[15px] leading-[1.65] text-slate-600 dark:text-slate-400">
                ISO 30414, IFRS S1/S2 기준에 맞춰 인적자본·교육훈련·전환 준비도 등 공시 지표를 집계하고, 복잡한 공시 프로세스를 단순화합니다.
              </p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-md transition-all duration-200 ease-out hover:-translate-y-2 hover:scale-[1.02] hover:border-violet-200 hover:bg-violet-50/50 hover:shadow-xl dark:border-white/10 dark:bg-[#171717] dark:hover:border-violet-900/50 dark:hover:bg-violet-950/20">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-amber-500/10 text-amber-600 dark:text-amber-400">
                <Database className="h-6 w-6" />
              </div>
              <h3 className="mt-4 text-lg font-semibold leading-tight tracking-tight text-slate-900 dark:text-slate-100">
                데이터 기반 인사이트
              </h3>
              <p className="mt-3 text-[15px] leading-[1.65] text-slate-600 dark:text-slate-400">
                비정형 이력서·공시 문서를 RAG로 검색하고 LLM이 질의에 답변하며, 숨은 가치를 발굴하고 미래 인재 전략을 수립할 수 있도록 합니다.
              </p>
            </div>
          </div>
        </div>
      </section>

      <footer className="scroll-mt-20 border-t border-slate-200/60 bg-white/50 py-8 dark:border-white/10 dark:bg-[#0f0f0f]/50">
        <div className="mx-auto max-w-6xl px-6 text-center">
          <p className="text-[15px] text-slate-600 dark:text-slate-400">
            © 2026 HRInsight. 차세대 인적자본 관리 시스템
          </p>
        </div>
      </footer>
    </div>
  );
}
