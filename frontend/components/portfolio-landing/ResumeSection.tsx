"use client";

import { useRef, useEffect } from "react";
import { motion, useInView } from "framer-motion";
import { Download } from "lucide-react";
import { SectionHeader } from "./SectionHeader";

/** 연락처·메트릭·기술 카테고리·프로젝트 등 확장 이력서 데이터 타입 */
export type ResumeData = {
  name: string;
  nameEn: string;
  tagline: string;
  taglineQuote: string;
  email: string;
  phone?: string;
  github: string;
  blog: string;
  summary: string;
  metrics: { value: string; label: string }[];
  skillsByCategory: { title: string; tags: string[]; hot?: string[] }[];
  experience: {
    period: string;
    title: string;
    org: string;
    desc?: string;
    bullets?: string[];
    tags: string[];
    current: boolean;
  }[];
  education: { school: string; info: string; period: string }[];
  projects: {
    title: string;
    type: string;
    desc: string;
    metrics: string[];
    stack: string[];
  }[];
  aboutCards?: { title: string; text: string }[];
  skills: string[];
  educationLegacy: string;
};

/** PDF·HTML 참고용 이력서 데이터 (모달·섹션 공통) */
export const RESUME_SAMPLE: ResumeData = {
  name: "강경구",
  nameEn: "Kang Gyeong-gu",
  tagline: "Performance-Driven Full-Stack AI Developer",
  taglineQuote: "한 줄의 코드가 세상을 바꾼다고 믿는 풀스택 AI 개발자",
  email: "kanggyeonggu@gmail.com",
  github: "github.com/ConversionDev",
  blog: "kku1031.tistory.com",
  summary:
    "비전공에서 개발로 전환해 의료 IT·백엔드를 거쳐 현재는 AI/ML 엔지니어링에 집중합니다. OCR & RAG 기반 Intelligent HR Agent, ESG Supply Chain Platform 등 성능 중심의 AI 프로젝트를 설계·개발합니다.",
  metrics: [
    { value: "95%", label: "OCR 정확도" },
    { value: "+40%", label: "추론 속도 개선" },
    { value: "-60%", label: "인프라 비용 절감" },
    { value: "92%", label: "리스크 탐지 정확도" },
    { value: "85%", label: "분석 자동화율" },
  ],
  skillsByCategory: [
    { title: "AI / ML", tags: ["LangChain", "RAG", "GPT-4", "Prompt Eng.", "Tesseract OCR", "ChromaDB", "Vector DB", "Multi-Agent"], hot: ["LangChain", "RAG", "GPT-4"] },
    { title: "Backend", tags: ["FastAPI", "Python", "Django", "REST API", "ElasticSearch", "Redis"], hot: ["FastAPI", "Python"] },
    { title: "Database", tags: ["PostgreSQL", "SQLite", "Redis", "ChromaDB"], hot: ["PostgreSQL"] },
    { title: "Frontend", tags: ["React", "TypeScript", "Next.js", "Tailwind CSS", "JavaScript"] },
    { title: "Infra / DevOps", tags: ["Docker", "Linux", "AWS", "CI/CD", "Git"] },
  ],
  experience: [
    {
      period: "2025.09 – Present",
      title: "AI Developer | 개인 프로젝트",
      org: "Full-Stack AI Developer",
      bullets: [
        "OCR & RAG 기반 HR 문서 분석 에이전트 — OCR 정확도 95%, 속도 +40%, 비용 -60%",
        "ESG AI 플랫폼 AIFIX — 리스크 탐지 92%, 자동화율 85%",
        "멀티 에이전트 아키텍처 설계 & 팀 리딩, 프롬프트 엔지니어링",
      ],
      tags: ["LangChain", "GPT-4", "FastAPI", "RAG"],
      current: true,
    },
    {
      period: "2023.10 – 2024.01",
      title: "제로베이스 백엔드 스쿨 12기",
      org: "Backend Developer",
      bullets: [
        "팀 프로젝트 KeyWord — OAuth 2.0 소셜 로그인, ElasticSearch 검색 기능 개발",
        "기술 의사결정 문서화 · 코드 리뷰를 통한 팀 지식 공유 경험",
      ],
      tags: ["Django", "ElasticSearch"],
      current: false,
    },
    {
      period: "2022.09 – 2022.12",
      title: "(주)화산시스템 | 의료 IT",
      org: "Backend Developer",
      bullets: [
        "대학병원 LIS(검사정보시스템) 개발·유지보수",
        "시리얼 통신 인터페이스 데이터 전송·검증 모듈 구현",
        "전국 병원 현장 트러블슈팅 → 견고한 시스템 설계 역량 확립",
      ],
      tags: ["Visual Basic 6.0"],
      current: false,
    },
    {
      period: "2022.02 – 2022.09",
      title: "응용 SW 엔지니어링 수료",
      org: "대구 중앙 직업전문학교",
      desc: "Java와 Spring을 활용한 통합 시스템 구축 과정.",
      tags: ["Java", "Spring"],
      current: false,
    },
  ],
  education: [
    { school: "영남대학교", info: "중어중문학과 학사 졸업", period: "2013.03 – 2020.02" },
    { school: "대구 중앙 직업전문학교 & 제로베이스 백엔드 스쿨 12기", info: "응용 SW 엔지니어링 / 백엔드 개발 심화 수료", period: "2022.02 – 2024.01" },
  ],
  projects: [
    {
      title: "Intelligent HR Agent",
      type: "개인 프로젝트 | 2025",
      desc: "OCR & RAG 기반 지능형 HR 문서 분석 에이전트. 멀티 포맷 PDF/이미지 OCR 파이프라인 구축, RAG Chunking 전략 최적화로 검색 정확도·속도 개선, FastAPI 기반 RESTful API 서버 설계.",
      metrics: ["OCR 정확도 95%", "추론 속도 +40%", "비용 -60%"],
      stack: ["Python", "LangChain", "GPT-4", "Tesseract OCR", "FastAPI", "ChromaDB"],
    },
    {
      title: "AIFIX ESG Supply Chain AI",
      type: "팀 프로젝트 (AI 파트 리드) | 2025",
      desc: "뉴스·보고서 크롤링 → NLP 분석 → 리스크 스코어링 파이프라인. 멀티 에이전트 아키텍처(분석-판단-보고 자동화) 설계, 실시간 ESG 대시보드 개발, AI 파트 팀 리딩.",
      metrics: ["리스크 탐지 92%", "자동화율 85%", "분석 시간 -70%"],
      stack: ["Python", "LangChain", "React", "FastAPI", "PostgreSQL", "Docker"],
    },
  ],
  aboutCards: [
    {
      title: "성능 최적화에 집중하는 개발자",
      text: "더 빠르고, 더 효율적인 방법을 찾는 과정이 즐겁습니다. 백엔드에서 AI까지 풀스택 시스템을 설계하며 성능 병목을 추적하고 해결하는 데 몰입해왔습니다. OCR 정확도 95%, 추론 속도 40% 개선, 인프라 비용 60% 절감이라는 측정 가능한 성과를 달성했습니다.",
    },
    {
      title: "협업으로 함께 성장하는 개발자",
      text: "필리핀 해외 자원봉사(6개월)와 YMCA 국제개발협력팀 활동을 통해 다양한 배경의 사람들과 협력하는 방법을 배웠습니다. 팀원이 이해할 수 있는 기술 문서 작성, 코드 리뷰를 통한 지식 공유를 중요하게 생각합니다. \"혼자 가면 빨리, 함께 가면 멀리.\"",
    },
  ],
  skills: ["Python", "LangChain", "FastAPI", "RAG", "OCR", "Java", "Spring", "PostgreSQL", "Docker", "React"],
  educationLegacy: "영남대학교 중어중문학과 (2013—2020) · 필리핀 해외 자원봉사 6개월, YMCA 국제개발협력팀 근무",
};

/** 랜딩 섹션용: 간단 요약 이력서 (기존 스타일 유지) */
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
              {(item.bullets?.length ? item.bullets : item.desc ? [item.desc] : []).map((line, i) => (
                <p key={i} className="mt-1 text-sm leading-relaxed" style={{ color: textColor }}>{line}</p>
              ))}
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
        <p className="text-sm leading-relaxed" style={{ color: textColor }}>{R.educationLegacy}</p>
      </div>
    </div>
  );
}

/** 모달 전용: 모노톤·모던 이력서 레이아웃 (헤더·메트릭·기술·경력·학력·프로젝트) */
export function ResumeModalContent() {
  const R = RESUME_SAMPLE;
  const ink = "#0f172a";
  const mute = "#64748b";
  const border = "#e2e8f0";
  const bar = "#64748b";

  return (
    <div
      id="resume-modal-print-area"
      className="resume-content resume-modal-content w-full min-h-full bg-white text-left p-6 sm:p-8 overflow-y-auto h-full"
      style={
        {
          "--resume-ink": ink,
          "--resume-mute": mute,
          "--resume-border": border,
          "--resume-bar": bar,
        } as React.CSSProperties
      }
    >
      {/* 헤더 */}
      <header className="border-b border-[var(--resume-border)] pb-4 mb-4">
        <h1 className="text-2xl font-bold tracking-tight text-[var(--resume-ink)]">
          {R.name} <span className="font-normal text-[var(--resume-mute)]">·</span> {R.nameEn}
        </h1>
        <p className="mt-1 text-xs font-medium uppercase tracking-widest text-[var(--resume-mute)]">{R.tagline}</p>
        <div className="mt-2 flex flex-wrap gap-x-4 gap-y-0 text-sm text-[var(--resume-mute)]">
          <span>@ {R.email}</span>
          <span>G {R.github}</span>
          <span>B {R.blog}</span>
        </div>
      </header>

      {/* 메트릭 바 */}
      <div
        className="flex flex-wrap items-center justify-around gap-4 py-3 px-2 mb-6 rounded-md"
        style={{ background: "#f1f5f9", border: `1px solid ${border}` }}
      >
        {R.metrics.map((m) => (
          <div key={m.label} className="text-center">
            <div className="text-lg font-bold text-[var(--resume-ink)]" style={{ fontFamily: "'JetBrains Mono', monospace" }}>{m.value}</div>
            <div className="text-[10px] font-medium text-[var(--resume-mute)]">{m.label}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[200px_1fr] gap-6 lg:gap-8">
        {/* 사이드: 기술 스택 카테고리 */}
        <aside className="space-y-4">
          {R.skillsByCategory.map((cat) => (
            <div key={cat.title}>
              <h3 className="text-[10px] font-bold uppercase tracking-wider text-[var(--resume-mute)] border-b border-[var(--resume-border)] pb-1 mb-2">
                {cat.title}
              </h3>
              <div className="flex flex-wrap gap-1">
                {cat.tags.map((t) => (
                  <span
                    key={t}
                    className="rounded px-1.5 py-0.5 text-[10px] border border-[var(--resume-border)] text-[var(--resume-ink)]"
                    style={cat.hot?.includes(t) ? { background: "#f1f5f9", fontWeight: 600 } : {}}
                  >
                    {t}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </aside>

        <div className="space-y-6">
          {/* Experience */}
          <section>
            <div className="flex items-center gap-2 mb-3">
              <span className="w-0.5 h-3.5 rounded-full bg-[var(--resume-bar)]" />
              <h2 className="text-sm font-bold uppercase tracking-wide text-[var(--resume-ink)]">Experience</h2>
            </div>
            <ul className="space-y-4">
              {R.experience.map((exp) => (
                <li key={exp.period}>
                  <div className="flex flex-wrap justify-between items-baseline gap-2">
                    <div>
                      <p className="font-semibold text-[var(--resume-ink)]">{exp.title}</p>
                      <p className="text-xs font-medium text-[var(--resume-mute)]">{exp.org}</p>
                    </div>
                    <span className="text-[10px] font-medium text-[var(--resume-mute)] bg-[#f8fafc] px-2 py-0.5 rounded" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
                      {exp.period}
                    </span>
                  </div>
                  {(exp.bullets ?? (exp.desc ? [exp.desc] : [])).map((line, i) => (
                    <p key={i} className="mt-1 text-xs text-[var(--resume-ink)] leading-relaxed pl-1 border-l-2 border-[var(--resume-border)] ml-0.5">
                      {line}
                    </p>
                  ))}
                </li>
              ))}
            </ul>
          </section>

          {/* Education */}
          <section>
            <div className="flex items-center gap-2 mb-3">
              <span className="w-0.5 h-3.5 rounded-full bg-[var(--resume-bar)]" />
              <h2 className="text-sm font-bold uppercase tracking-wide text-[var(--resume-ink)]">Education</h2>
            </div>
            <ul className="space-y-2">
              {R.education.map((ed) => (
                <li key={ed.school} className="flex gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-[var(--resume-bar)] mt-1.5 shrink-0" />
                  <div>
                    <p className="text-sm font-semibold text-[var(--resume-ink)]">{ed.school}</p>
                    <p className="text-xs text-[var(--resume-mute)]">{ed.info}</p>
                    <p className="text-[10px] text-[var(--resume-mute)]">{ed.period}</p>
                  </div>
                </li>
              ))}
            </ul>
          </section>

          {/* Projects */}
          <section>
            <div className="flex items-center gap-2 mb-3">
              <span className="w-0.5 h-3.5 rounded-full bg-[var(--resume-bar)]" />
              <h2 className="text-sm font-bold uppercase tracking-wide text-[var(--resume-ink)]">Projects</h2>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {R.projects.map((proj) => (
                <div key={proj.title} className="border border-[var(--resume-border)] rounded-lg p-3 pl-4 border-l-4" style={{ borderLeftColor: bar }}>
                  <p className="font-semibold text-sm text-[var(--resume-ink)]">{proj.title}</p>
                  <p className="text-[10px] text-[var(--resume-mute)]">{proj.type}</p>
                  <p className="mt-1.5 text-xs text-[var(--resume-ink)] leading-relaxed">{proj.desc}</p>
                  <div className="mt-2 flex flex-wrap gap-1">
                    {proj.metrics.map((m) => (
                      <span key={m} className="rounded px-1.5 py-0.5 text-[10px] font-semibold border border-[var(--resume-border)] text-[var(--resume-ink)]">
                        {m}
                      </span>
                    ))}
                  </div>
                  <div className="mt-1.5 flex flex-wrap gap-1">
                    {proj.stack.map((s) => (
                      <span key={s} className="rounded px-1 py-0.5 text-[10px] bg-[#f8fafc] text-[var(--resume-mute)]">{s}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* About Me (접이식 느낌) */}
          {R.aboutCards && R.aboutCards.length > 0 && (
            <section>
              <div className="flex items-center gap-2 mb-3">
                <span className="w-0.5 h-3.5 rounded-full bg-[var(--resume-bar)]" />
                <h2 className="text-sm font-bold uppercase tracking-wide text-[var(--resume-ink)]">About Me</h2>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {R.aboutCards.map((card) => (
                  <div key={card.title} className="border border-[var(--resume-border)] rounded-lg p-3 pl-4 border-l-4" style={{ borderLeftColor: bar }}>
                    <p className="font-semibold text-xs text-[var(--resume-ink)]">{card.title}</p>
                    <p className="mt-1 text-xs text-[var(--resume-mute)] leading-relaxed">{card.text}</p>
                  </div>
                ))}
              </div>
            </section>
          )}
        </div>
      </div>

      {/* 푸터 태그라인 */}
      <footer className="mt-8 pt-4 border-t border-[var(--resume-border)] text-center text-xs text-[var(--resume-mute)] italic">
        &quot;{R.taglineQuote}&quot;
      </footer>
    </div>
  );
}

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
