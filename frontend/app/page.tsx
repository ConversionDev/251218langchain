"use client";

import Link from "next/link";
import Image from "next/image";
import { Search, BarChart3, Database } from "lucide-react";

const FEATURES_ID = "features";

export default function LandingPage() {
  return (
    <div className="relative min-h-screen overflow-hidden bg-[#f5f5f5]">
      {/* GNB: 라이트 배경 — 메인, AI POWERED HR INTELLIGENCE HRInsight, 데모·로그인 */}
      <header className="relative z-20 flex h-16 items-center justify-between border-b border-slate-200 bg-white px-6">
        <div className="flex items-center gap-3 md:gap-4">
          <Link href="/" className="text-sm font-medium text-slate-800 hover:text-slate-900 transition-colors">
            메인
          </Link>
          <span className="text-slate-300 hidden sm:inline">|</span>
          <span className="text-sm tracking-tight text-slate-600">
            AI POWERED HR INTELLIGENCE <span className="font-bold text-emerald-600">HRInsight</span>
          </span>
        </div>

        <nav aria-label="메인 메뉴" className="flex items-center gap-6 md:gap-8">
          <a href={`#${FEATURES_ID}`} className="text-sm font-medium text-slate-700 hover:text-slate-900 transition-colors">
            기능
          </a>
          <Link href="/careers" className="text-sm font-medium text-slate-700 hover:text-slate-900 transition-colors">
            채용 지원
          </Link>
          <Link href="/workspace" className="text-sm font-medium text-slate-700 hover:text-slate-900 transition-colors">
            직원 서비스
          </Link>
          <Link href="/dashboard" className="text-sm font-medium text-slate-700 hover:text-slate-900 transition-colors">
            관리자
          </Link>
        </nav>

        <div className="flex items-center gap-3">
          <Link
            href="/demo"
            className="text-sm font-medium text-slate-700 hover:text-slate-900 transition-colors px-3 py-2"
          >
            데모
          </Link>
          <Link
            href="/login"
            className="rounded-md bg-slate-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-slate-700"
          >
            로그인
          </Link>
        </div>
      </header>

      <section className="min-h-[85vh] bg-gradient-to-br from-white from-0% via-[#f0f9f4] via-40% to-[#e0f2eb] to-100% text-gray-900 flex items-center">
        <div className="mx-auto w-full max-w-6xl px-6 py-12 md:px-12 md:py-16 lg:px-16">
          <div className="flex flex-col gap-10 lg:flex-row lg:items-center lg:justify-between lg:gap-14">
            {/* Left: 텍스트 블록 — 이미지와 동일 */}
            <div className="flex flex-col max-w-xl lg:max-w-[480px]">
              <h1 className="text-4xl font-bold leading-[1.2] tracking-tight mb-5 md:text-5xl md:leading-tight">
                <span className="whitespace-nowrap">지능형 인적자본 솔루션,</span>
                <br />
                <span className="text-emerald-600">HRInsight</span>과 함께
              </h1>
              <p className="text-base text-gray-700 leading-relaxed mb-3 md:text-lg">
                AI가 분석한 이력서와 공시 지표로 인재를 찾고,
              </p>
              <p className="text-base text-gray-700 leading-relaxed mb-6 md:text-lg">
                RAG-LLM-Success DNA 역량 분석과 ISO 30414-IFRS S2 대응까지 한 곳에서 관리합니다.
              </p>
              <p className="text-sm text-gray-600">
                이용하실 메뉴는 상단 기능 채용지원 직원 서비스 관리자에서 선택해 주세요.
              </p>
            </div>

            {/* Right: 협업 이미지 — 항상 영역 확보, 데스크톱에서 오른쪽 정렬 */}
            <div className="flex min-w-0 flex-1 basis-[min(100%,420px)] justify-center lg:basis-[min(480px,45%)] lg:justify-end">
              <div className="relative w-full min-w-[280px] max-w-md aspect-[4/3] rounded-2xl overflow-hidden shadow-2xl ring-1 ring-black/5 md:rounded-3xl">
                <Image
                  src="https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=800&q=80"
                  alt="두 사람이 협업하는 회사 사진"
                  fill
                  className="object-cover"
                  priority
                  sizes="(max-width: 1024px) 100vw, min(500px, 45vw)"
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id={FEATURES_ID} className="relative z-10 scroll-mt-20 bg-gradient-to-b from-[#e8f5ef] to-[#f0f5f0]">
        <div className="mx-auto max-w-6xl px-6 py-16">
          <h2 className="text-center text-2xl font-bold tracking-tight text-slate-900 md:text-3xl">
            RAG와 LLM으로 HR 인사이트를 발견하세요
          </h2>
          <p className="mx-auto mt-5 max-w-2xl text-center text-lg leading-[1.7] text-slate-700">
            이력서·공시 역량 데이터를 벡터 검색(RAG)과 LLM으로 연결하고, Fast MCP 기반 도구 호출로 정확한 분석과 인재 매칭을 실현합니다.
          </p>
          <div className="mt-12 grid gap-8 md:grid-cols-3">
            <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm transition-shadow hover:shadow-md">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-slate-100 text-slate-600">
                <Search className="h-6 w-6" />
              </div>
              <h3 className="mt-4 text-lg font-semibold leading-tight tracking-tight text-slate-900">
                정확한 인재 매칭
              </h3>
              <p className="mt-3 text-[15px] leading-[1.65] text-slate-600">
                LLM이 분석한 이력서와 Success DNA 역량 점수를 기반으로 벡터 유사도 검색으로 인재를 추천해 채용 시간을 단축하고 정확도를 높입니다.
              </p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm transition-shadow hover:shadow-md">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-slate-100 text-slate-600">
                <BarChart3 className="h-6 w-6" />
              </div>
              <h3 className="mt-4 text-lg font-semibold leading-tight tracking-tight text-slate-900">
                간편한 공시 리포팅
              </h3>
              <p className="mt-3 text-[15px] leading-[1.65] text-slate-600">
                ISO 30414, IFRS S1/S2 기준에 맞춰 인적자본·교육훈련·전환 준비도 등 공시 지표를 집계하고, 복잡한 공시 프로세스를 단순화합니다.
              </p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm transition-shadow hover:shadow-md">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-slate-100 text-slate-600">
                <Database className="h-6 w-6" />
              </div>
              <h3 className="mt-4 text-lg font-semibold leading-tight tracking-tight text-slate-900">
                데이터 기반 인사이트
              </h3>
              <p className="mt-3 text-[15px] leading-[1.65] text-slate-600">
                비정형 이력서·공시 문서를 RAG로 검색하고 LLM이 질의에 답변하며, 숨은 가치를 발굴하고 미래 인재 전략을 수립할 수 있도록 합니다.
              </p>
            </div>
          </div>
        </div>
      </section>

      <footer className="relative z-10 border-t border-slate-200 bg-white py-8">
        <div className="mx-auto max-w-6xl px-6 text-center">
          <p className="text-[15px] text-slate-600">
            © 2026 HRInsight. 차세대 인적자본 관리 시스템
          </p>
        </div>
      </footer>
    </div>
  );
}
