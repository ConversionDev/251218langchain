"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowLeft } from "lucide-react";

export default function PortfolioTeamPage() {
  return (
    <div className="min-h-screen bg-[#0c0c0e] text-[#e4e4e7]">
      <header className="sticky top-0 z-10 border-b border-white/[0.06] bg-[#0c0c0e]/80 backdrop-blur-md">
        <div className="mx-auto flex h-14 max-w-5xl items-center px-4 sm:px-6">
          <Link
            href="/portfolio"
            className="flex items-center gap-2 text-sm text-[#a1a1aa] transition-colors hover:text-white"
          >
            <ArrowLeft className="h-4 w-4" />
            포트폴리오
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-12 sm:px-6">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          <h1 className="text-2xl font-bold text-white md:text-3xl">팀 프로젝트</h1>
          <p className="mt-2 text-[#a1a1aa]">함께 진행한 팀 프로젝트를 소개합니다.</p>
          <div className="mt-8 rounded-xl border border-white/[0.08] bg-white/[0.02] p-8 text-center text-[#71717a]">
            팀 프로젝트 카드·목록은 추후 추가 예정입니다.
          </div>
        </motion.div>
      </main>
    </div>
  );
}
