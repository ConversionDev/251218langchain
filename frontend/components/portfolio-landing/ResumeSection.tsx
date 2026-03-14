"use client";

import { useRef } from "react";
import { motion, useInView } from "framer-motion";
import { Download } from "lucide-react";
import { SectionHeader } from "./SectionHeader";

/** PDF 참고용 샘플 이력서 데이터 (모달·섹션 공통) */
export const RESUME_SAMPLE = {
  name: "강경구",
  tagline: "AI Developer",
  email: "kanggyeonggu@gmail.com",
  summary:
    "비전공에서 개발로 전환해 의료 IT·백엔드를 거쳐 현재는 AI/ML 엔지니어링에 집중합니다. OCR & RAG 기반 Intelligent HR Agent, ESG Supply Chain Platform 등 성능 중심의 AI 프로젝트를 설계·개발합니다. 성능 최적화, RAG 아키텍처, 프롬프트 엔지니어링에 강점이 있습니다.",
  experience: [
    { period: "2025.09 — Present", title: "AI Developer", org: "AI/ML 프로젝트 집중", desc: "OCR & RAG 기반 Intelligent HR Agent, ESG Supply Chain Platform 등 설계 및 개발.", tags: ["LangChain", "GPT-4", "FastAPI", "RAG"], current: true },
    { period: "2023.10 — 2024.01", title: "제로베이스 백엔드 스쿨 12기", org: "온라인 부트캠프", desc: "팀 프로젝트 KeyWord 원격 협업. 소셜 로그인 및 ElasticSearch 기반 회원 검색 담당.", tags: ["Django", "ElasticSearch"], current: false },
    { period: "2022.09 — 2022.12", title: "의료 IT / Backend", org: "(주)화산시스템", desc: "병원 LIS 시스템 간 인터페이스 데이터 전송·검증, 전국 병원 출장 LOG 분석 및 네트워크 진단.", tags: ["Visual Basic 6.0"], current: false },
    { period: "2022.02 — 2022.09", title: "응용 SW 엔지니어링 수료", org: "대구 중앙 직업전문학교", desc: "Java와 Spring을 활용한 통합 시스템 구축 과정.", tags: ["Java", "Spring"], current: false },
  ],
  skills: ["Python", "LangChain", "FastAPI", "RAG", "OCR", "Java", "Spring", "PostgreSQL", "Docker", "React"],
  education: "영남대학교 중어중문학과 (2013—2020) · 필리핀 해외 자원봉사 6개월, YMCA 국제개발협력팀 근무",
};

/** 모달용: PDF 참고 샘플 이력서 본문만 (스크롤 가능) */
export function ResumeSampleContent({ variant = "modal" }: { variant?: "modal" | "section" }) {
  const isModal = variant === "modal";
  const R = RESUME_SAMPLE;
  const nameColor = isModal ? "#0f172a" : "#ccd6f6";
  const accentColor = isModal ? "#0d9488" : "rgba(142,240,215,0.9)";
  const textColor = isModal ? "#334155" : "rgba(220,228,245,0.9)";
  const mutedColor = isModal ? "#64748b" : "rgba(220,228,245,0.75)";
  const tagBg = isModal ? "rgba(13,148,136,0.1)" : "rgba(142,240,215,0.08)";
  const tagColor = isModal ? "#0d9488" : "rgba(142,240,215,0.85)";

  return (
    <div className={isModal ? "resume-content p-6 sm:p-8 overflow-y-auto h-full" : "resume-content"}>
      <div className="mb-6">
        <h2 className="text-2xl font-bold tracking-tight" style={{ color: nameColor }}>{R.name}</h2>
        <p className="mt-1 text-sm" style={{ color: accentColor }}>{R.tagline}</p>
        <p className="mt-2 text-sm" style={{ color: mutedColor }}>{R.email}</p>
      </div>
      <div className="mb-6">
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider" style={{ color: accentColor }}>Summary</h3>
        <p className="text-sm leading-relaxed" style={{ color: textColor }}>{R.summary}</p>
      </div>
      <div className="mb-6">
        <h3 className="mb-4 text-xs font-semibold uppercase tracking-wider" style={{ color: accentColor }}>Experience</h3>
        <ul className="space-y-4">
          {R.experience.map((item) => (
            <li key={item.period}>
              <div className="flex flex-wrap items-baseline gap-2">
                <span className="text-xs font-medium" style={{ fontFamily: "'JetBrains Mono', monospace", color: mutedColor }}>{item.period}</span>
                {item.current && (
                  <span className="rounded-full px-2 py-0.5 text-[10px] font-semibold" style={{ background: tagBg, color: tagColor }}>Current</span>
                )}
              </div>
              <h4 className="mt-0.5 text-base font-semibold" style={{ color: nameColor }}>{item.title}</h4>
              <p className="text-sm" style={{ color: mutedColor }}>{item.org}</p>
              <p className="mt-1 text-sm leading-relaxed" style={{ color: textColor }}>{item.desc}</p>
              {item.tags.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {item.tags.map((t) => (
                    <span key={t} className="rounded px-2 py-0.5 text-xs" style={{ background: tagBg, color: tagColor }}>{t}</span>
                  ))}
                </div>
              )}
            </li>
          ))}
        </ul>
      </div>
      <div className="mb-6">
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider" style={{ color: accentColor }}>Skills</h3>
        <p className="text-sm leading-relaxed" style={{ color: textColor }}>{R.skills.join(" · ")}</p>
      </div>
      <div>
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider" style={{ color: accentColor }}>Education &amp; Other</h3>
        <p className="text-sm leading-relaxed" style={{ color: textColor }}>{R.education}</p>
      </div>
    </div>
  );
}

const RESUME = RESUME_SAMPLE;

export function ResumeSection() {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: "-60px" });

  const handleDownloadPdf = () => {
    window.print();
  };

  return (
    <section id="resume" className="pt-10 pb-28 scroll-mt-14 md:scroll-mt-0">
      <SectionHeader num="05" label="Resume" />
      <div ref={ref}>
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5 }}
          className="flex flex-col gap-6"
        >
          <button
            type="button"
            onClick={handleDownloadPdf}
            className="inline-flex items-center gap-2 self-start rounded-lg px-4 py-2.5 text-sm font-semibold transition-colors print:hidden"
            style={{
              background: "rgba(142,240,215,0.1)",
              color: "#8ef0d7",
              border: "1px solid rgba(142,240,215,0.25)",
            }}
          >
            <Download size={16} />
            PDF 다운로드
          </button>

          <div
            id="resume-print-area"
            className="rounded-xl border p-8 sm:p-10 resume-print-area"
            style={{
              background: "rgba(13,28,66,0.4)",
              borderColor: "rgba(142,240,215,0.12)",
            }}
          >
            <ResumeSampleContent variant="section" />
          </div>
        </motion.div>
      </div>
    </section>
  );
}
