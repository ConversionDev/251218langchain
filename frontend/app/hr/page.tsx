"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import Image from "next/image";
import { Search, BarChart3, Database, ChevronDown } from "lucide-react";

const FEATURES_ID = "features";

/** 메인 히어로 슬로건 — 1줄 + 2줄(통해 다음 줄바꿈) */
const HERO_SLOGAN = {
  main: "인사(HR)의 직관을 데이터의 확신으로 바꾸다",
  sub1: "리더십부터 적응력까지, AI가 분석한 5대 핵심 역량 지표를 통해",
  sub2: "오차 없는 인재 배치와 성과 예측을 경험하세요.",
} as const;

/** 배경 캐러셀용 플레이스홀더 이미지 (추후 기업 신뢰 이미지로 교체) */
const HERO_BG_IMAGES = [
  "https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=1920&q=80",
  "https://images.unsplash.com/photo-1552664730-d307ca884978?w=1920&q=80",
  "https://images.unsplash.com/photo-1600880292203-757bb62b4baf?w=1920&q=80",
] as const;

const SLIDE_COUNT = HERO_BG_IMAGES.length;

export default function HRLandingPage() {
  const [heroSlide, setHeroSlide] = useState(0);

  useEffect(() => {
    const t = setInterval(() => {
      setHeroSlide((s) => (s + 1) % SLIDE_COUNT);
    }, 5000);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="font-sans relative min-h-screen overflow-hidden bg-[#f5f5f5]">
      {/* 히어로 블록: 높이 제한으로 아래 섹션이 살짝 보이게 + 스크롤 유도 */}
      <section className="relative h-[72vh] min-h-[420px] max-h-[720px] w-full overflow-hidden flex flex-col">
        {/* 헤더: 살짝 축소 — 영역·글자 크기 약간 줄임 */}
        <header className="absolute top-0 left-0 right-0 z-20 flex min-h-[4.5rem] items-center justify-between border-b border-[#a8d5c4]/50 bg-white/85 px-6 py-3 backdrop-blur-md dark:border-primary/20 dark:bg-[#0f0f0f]/90 md:px-8 md:py-4">
          <Link href="/hr" className="flex flex-col leading-tight shrink-0">
            <span className="text-[11px] font-medium uppercase tracking-wider text-slate-500">
              AI Powered HR Intelligence
            </span>
            <span className="mt-0.5 flex items-baseline gap-1">
              <span className="text-lg font-bold tracking-tight text-[#14532d] md:text-xl">HR</span>
              <span
                className="bg-gradient-to-r from-teal-600 to-emerald-500 bg-clip-text text-lg font-bold tracking-tight text-transparent md:text-xl"
                style={{ WebkitBackgroundClip: "text" }}
              >
                Insight
              </span>
            </span>
          </Link>

          <nav aria-label="메인 메뉴" className="absolute left-1/2 top-1/2 flex -translate-x-1/2 -translate-y-1/2 items-center gap-6 md:gap-8">
            <a href={`#${FEATURES_ID}`} className="text-sm font-semibold text-slate-700 hover:text-slate-900 transition-colors md:text-base">
              기능
            </a>
            <Link href="/careers" className="text-sm font-semibold text-slate-700 hover:text-slate-900 transition-colors md:text-base">
              채용 지원
            </Link>
            <Link href="/workspace" className="text-sm font-semibold text-slate-700 hover:text-slate-900 transition-colors md:text-base">
              직원 서비스
            </Link>
            <Link href="/dashboard" className="text-sm font-semibold text-slate-700 hover:text-slate-900 transition-colors md:text-base">
              관리자
            </Link>
          </nav>

          <div className="flex shrink-0 items-center">
            <Link
              href="/login"
              className="rounded-md bg-slate-700 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-slate-800 md:text-base"
            >
              로그인
            </Link>
          </div>
        </header>

        {/* 1) 배경: 빨간 대각선 패턴 — 선명한 이미지를 위해 얇게만 겹침 */}
        <div
          className="absolute inset-0 z-0 opacity-50"
          style={{
            backgroundImage: `repeating-linear-gradient(
              -45deg,
              transparent,
              transparent 12px,
              rgba(220, 38, 38, 0.07) 12px,
              rgba(220, 38, 38, 0.07) 14px
            ), repeating-linear-gradient(
              45deg,
              transparent,
              transparent 12px,
              rgba(220, 38, 38, 0.05) 12px,
              rgba(220, 38, 38, 0.05) 14px
            )`,
            backgroundColor: "transparent",
          }}
        />

        {/* 2) 배경 캐러셀(슬라이더) — 선명한 색감, 슬로건 쪽만 그라데이션으로 가독성 확보 */}
        <div className="absolute inset-0 z-[1]">
          {HERO_BG_IMAGES.map((src, i) => (
            <div
              key={i}
              className="absolute inset-0 transition-opacity duration-500 ease-out"
              style={{
                opacity: i === heroSlide ? 1 : 0,
                pointerEvents: i === heroSlide ? "auto" : "none",
              }}
            >
              <Image
                src={src}
                alt=""
                fill
                className="object-cover"
                sizes="100vw"
                unoptimized
                loading="eager"
                fetchPriority={i === 0 ? "high" : "low"}
              />
              {/* 슬로건 영역(왼쪽) 가독성 확보, 오른쪽은 이미지 유지 */}
              <div
                className="absolute inset-0 bg-gradient-to-r from-white/90 via-white/60 to-transparent"
                aria-hidden
              />
            </div>
          ))}
        </div>

        {/* 3) 글자: 슬로건 — 왼쪽 정렬, 크기·간격 강화 */}
        <div className="relative z-10 flex flex-1 items-center justify-start px-6 pt-24 pb-16 md:px-12 md:pt-28 lg:px-16">
          <div className="mx-auto w-full max-w-6xl flex justify-start">
            <div className="max-w-xl text-left">
              <h2 className="text-3xl font-extrabold leading-tight tracking-tight text-slate-900 md:text-5xl lg:text-[3.25rem]">
                {HERO_SLOGAN.main}
              </h2>
              <p className="mt-6 text-base leading-relaxed text-slate-700 md:mt-8 md:text-xl md:leading-relaxed">
                {HERO_SLOGAN.sub1}
                <br />
                {HERO_SLOGAN.sub2}
              </p>
            </div>
          </div>
        </div>

        {/* 4) 슬라이더 인디케이터 + 스크롤 유도 */}
        <div className="relative z-10 flex flex-col items-center gap-4 pb-6" aria-label="슬라이드 선택">
          <div className="flex justify-center gap-3">
            {HERO_BG_IMAGES.map((_, i) => (
              <button
                key={i}
                type="button"
                onClick={() => setHeroSlide(i)}
                className="h-3 w-3 rounded-full border-2 border-[#a8d5c4] transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-[#a8d5c4] focus-visible:ring-offset-2"
                style={{
                  backgroundColor: i === heroSlide ? "#e8f5ef" : "transparent",
                }}
                aria-label={`${i + 1}번째 슬라이드`}
                aria-current={i === heroSlide ? "true" : undefined}
              />
            ))}
          </div>
          <a
            href={`#${FEATURES_ID}`}
            className="flex flex-col items-center gap-1 text-sm font-medium text-slate-600 transition-colors hover:text-slate-900"
            aria-label="아래 섹션으로 스크롤"
          >
            <span>더 보기</span>
            <ChevronDown className="h-5 w-5 animate-bounce" />
          </a>
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
