"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Code2, Users, ChevronRight } from "lucide-react";

export function PortfolioMain() {
  return (
    <div className="min-h-screen bg-[#0c0c0e] text-[#e4e4e7]">
      <header className="sticky top-0 z-10 border-b border-white/[0.06] bg-[#0c0c0e]/80 backdrop-blur-md">
        <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-4 sm:px-6">
          <Link href="/portfolio" className="text-sm font-semibold tracking-tight text-white">
            강경구
          </Link>
          <nav className="flex items-center gap-6 text-sm text-[#a1a1aa]">
            <a href="#about" className="transition-colors hover:text-white">
              소개
            </a>
            <a href="#projects" className="transition-colors hover:text-white">
              프로젝트
            </a>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 pb-24 sm:px-6">
        <motion.section
          className="pt-16 pb-20 md:pt-24 md:pb-28"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
        >
          <p className="text-sm font-medium text-[#22d3ee]/90">Developer Portfolio</p>
          <h1 className="mt-3 text-3xl font-bold tracking-tight text-white md:text-4xl">
            안녕하세요, 강경구입니다.
          </h1>
          <p className="mt-4 max-w-xl text-base leading-relaxed text-[#a1a1aa]">
            사용자 경험과 성능을 고려한 웹 개발과 서비스 설계에 관심이 많습니다.
          </p>
        </motion.section>

        <motion.section
          id="projects"
          className="space-y-6"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.15, ease: [0.22, 1, 0.36, 1] }}
        >
          <h2 className="text-lg font-semibold text-white">프로젝트</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <Link
              href="/portfolio/personal"
              className="group flex items-center gap-4 rounded-xl border border-white/[0.08] bg-white/[0.02] p-5 transition-colors hover:border-[#22d3ee]/30 hover:bg-white/[0.04]"
            >
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg border border-white/[0.08] bg-white/[0.03] text-[#22d3ee]">
                <Code2 className="h-5 w-5" />
              </div>
              <div className="min-w-0 flex-1">
                <span className="font-medium text-white">개인 프로젝트</span>
                <p className="mt-0.5 text-sm text-[#71717a]">지금 진행 중인 프로젝트를 확인하세요.</p>
              </div>
              <ChevronRight className="h-5 w-5 shrink-0 text-[#71717a] transition-transform group-hover:translate-x-0.5 group-hover:text-[#22d3ee]" />
            </Link>

            <Link
              href="/portfolio/team"
              className="group flex items-center gap-4 rounded-xl border border-white/[0.08] bg-white/[0.02] p-5 transition-colors hover:border-[#22d3ee]/30 hover:bg-white/[0.04]"
            >
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg border border-white/[0.08] bg-white/[0.03] text-[#22d3ee]">
                <Users className="h-5 w-5" />
              </div>
              <div className="min-w-0 flex-1">
                <span className="font-medium text-white">팀 프로젝트</span>
                <p className="mt-0.5 text-sm text-[#71717a]">함께 진행한 팀 프로젝트를 소개합니다.</p>
              </div>
              <ChevronRight className="h-5 w-5 shrink-0 text-[#71717a] transition-transform group-hover:translate-x-0.5 group-hover:text-[#22d3ee]" />
            </Link>
          </div>
        </motion.section>

        <motion.section
          id="about"
          className="mt-20 rounded-xl border border-white/[0.06] bg-white/[0.02] p-6 md:p-8"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.25, ease: [0.22, 1, 0.36, 1] }}
        >
          <h2 className="text-lg font-semibold text-white">소개</h2>
          <p className="mt-3 text-[15px] leading-relaxed text-[#a1a1aa]">
            개발자 포트폴리오에 방문해 주셔서 감사합니다. 개인 프로젝트와 팀 프로젝트를 통해 쌓은 경험을 공유합니다.
          </p>
        </motion.section>
      </main>
    </div>
  );
}
