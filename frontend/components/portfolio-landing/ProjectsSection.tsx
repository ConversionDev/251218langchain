"use client";

import { useState, useRef } from "react";
import Link from "next/link";
import Image from "next/image";
import { motion, useInView, AnimatePresence } from "framer-motion";
import { Bot, Leaf, X, ArrowUpRight, ExternalLink, Key } from "lucide-react";
import { SectionHeader } from "./SectionHeader";

interface Project {
  id: string;
  title: string;
  subtitle: string;
  description: string;
  icon: typeof Bot;
  type: string;
  year: string;
  metrics: { label: string; value: string }[];
  techStack: string[];
  details: string[];
  challenges: string[];
  viewUrl?: string;
  viewLabel?: string;
}

/** 서브 프로젝트: 작은 미리보기 + 클릭 시 외부 링크 */
interface SubProject {
  id: string;
  title: string;
  description: string;
  href: string;
  /** 미리보기 이미지 URL (없으면 디자인 플레이스홀더) */
  previewImage?: string;
  techStack?: string[];
}

/** 카테고리: Personal / Team(ESG 완성 후 추가) / Other(과거 팀프로젝트) */
const PROJECT_CATEGORY = { personal: "personal", team: "team", other: "other" } as const;

const PROJECTS: (Project & { category: keyof typeof PROJECT_CATEGORY })[] = [
  {
    id: "hr-agent",
    title: "Intelligent HR Agent",
    subtitle: "OCR & RAG 기반 지능형 HR 분석 에이전트",
    description:
      "비정형 HR 문서를 이해하고 분석하여 RAG 기반 지능형 질의응답을 제공하는 AI 에이전트. 멀티 포맷 문서 OCR 파이프라인부터 벡터 DB 검색 최적화까지, 기존 수작업 대비 의사결정 속도를 대폭 가속하고 분석 정확도를 극대화했습니다.",
    icon: Bot,
    type: "개인 프로젝트",
    year: "2025",
    category: "personal",
    metrics: [
      { label: "OCR 정확도", value: "95%" },
      { label: "분석 속도 향상", value: "40%↑" },
      { label: "비용 절감", value: "60%↓" },
    ],
    techStack: ["RAG", "OCR"],
    details: [
      "멀티 포맷 문서(PDF, 이미지, 스캔본) OCR 파이프라인 구축",
      "Chunking 전략 최적화로 RAG 검색 정확도 향상",
      "프롬프트 엔지니어링을 통한 환각(Hallucination) 최소화",
      "벡터 DB 인덱싱 최적화로 쿼리 응답 시간 단축",
    ],
    challenges: [
      "저품질 스캔 문서 OCR 정확도 → 전처리 파이프라인 + 후보정 로직으로 해결",
      "대용량 문서 메모리 이슈 → 스트리밍 + 배치 처리 아키텍처 도입",
    ],
    viewUrl: "/hr",
    viewLabel: "인사 시스템 보기",
  },
  {
    id: "aifix",
    title: "AIFIX",
    subtitle: "ESG Supply Chain AI Platform",
    description:
      "공급망 ESG 리스크를 AI로 분석하고 대응 방안을 자동 생성하는 플랫폼. AI 엔진 개발을 리드했으며, 뉴스/보고서 크롤링부터 리스크 스코어링, 리포트 자동화까지 전 과정을 멀티 에이전트 아키텍처로 구현했습니다.",
    icon: Leaf,
    type: "팀 프로젝트",
    year: "2025",
    category: "team",
    metrics: [
      { label: "리스크 탐지 정확도", value: "92%" },
      { label: "분석 시간 단축", value: "70%↓" },
      { label: "자동화율", value: "85%" },
    ],
    techStack: ["Python", "LangChain", "React", "FastAPI", "PostgreSQL", "Docker"],
    details: [
      "뉴스/보고서 크롤링 → NLP 분석 → 리스크 스코어링 파이프라인",
      "멀티 에이전트 아키텍처로 분석-판단-보고 자동화",
      "실시간 대시보드 및 알림 시스템 구축",
      "팀 내 AI 엔진 설계 및 개발 리드",
    ],
    challenges: [
      "다국어 ESG 데이터 분석 → 임베딩 모델 파인튜닝으로 해결",
      "실시간 처리 성능 → 비동기 파이프라인 + 캐싱 전략 도입",
    ],
  },
];

/** 팀 프로젝트: ESG(AIFIX) — 완성도 올라가면 내용만 보강하면 됨 */
const PERSONAL_PROJECTS = PROJECTS.filter((p) => p.category === "personal");
const TEAM_PROJECTS = PROJECTS.filter((p) => p.category === "team");

const SUB_PROJECTS: SubProject[] = [
  {
    id: "keyword",
    title: "KeyWord",
    description: "약속의 시작부터 끝까지, 이용자 일정을 도와주는 서비스.\n프론트엔드와 백엔드 팀 원격 협업 프로젝트",
    href: "https://github.com/ZB-Keyword",
    previewImage:
      "https://github.com/ZB-Keyword/.github/assets/130157565/45b3001f-1705-4d93-acf4-4b979b218186",
    techStack: ["Java", "Spring", "OAuth 2.0", "ElasticSearch"],
  },
];

function Modal({ project, onClose }: { project: Project; onClose: () => void }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[100] flex items-end sm:items-center justify-center p-0 sm:p-6"
      style={{ background: "rgba(0,0,0,0.75)", backdropFilter: "blur(12px)" }}
      onClick={onClose}
    >
      <motion.div
        initial={{ opacity: 0, y: 48 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: 48 }}
        transition={{ duration: 0.32, ease: [0.32, 0, 0.2, 1] }}
        className="w-full sm:max-w-[560px] max-h-[92vh] overflow-y-auto"
        style={{
          background: "#141d2e",
          border: "1px solid rgba(142,240,215,0.08)",
          borderRadius: "1rem 1rem 0 0",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div
          className="sticky top-0 z-10 px-7 pt-7 pb-5"
          style={{ background: "#141d2e", borderBottom: "1px solid rgba(255,255,255,0.32)" }}
        >
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3.5">
              <div
                className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                style={{
                  background: "rgba(142,240,215,0.06)",
                  border: "1px solid rgba(142,240,215,0.12)",
                }}
              >
                <project.icon size={18} style={{ color: "#8ef0d7" }} />
              </div>
              <div>
                <span
                  style={{
                    fontSize: "0.6875rem",
                    color: "rgba(220,228,245,0.8)",
                    display: "block",
                    marginBottom: 2,
                  }}
                >
                  {project.type} · {project.year}
                </span>
                <h2
                  style={{
                    fontSize: "1.1875rem",
                    fontWeight: 700,
                    color: "#ccd6f6",
                    lineHeight: 1.2,
                  }}
                >
                  {project.title}
                </h2>
              </div>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="w-8 h-8 rounded-lg flex items-center justify-center transition-all mt-0.5"
              style={{ color: "rgba(220,228,245,0.8)" }}
            >
              <X size={15} />
            </button>
          </div>
        </div>
        <div className="px-7 pt-6 pb-8 space-y-7">
          <p
            style={{
              fontSize: "0.875rem",
              color: "rgba(220,228,245,0.88)",
              lineHeight: 1.85,
              whiteSpace: "pre-line",
            }}
          >
            {project.description}
          </p>
          <div className="grid grid-cols-3 gap-3">
            {project.metrics.map((m) => (
              <div
                key={m.label}
                className="rounded-xl p-4 text-center"
                style={{
                  background: "rgba(142,240,215,0.03)",
                  border: "1px solid rgba(142,240,215,0.07)",
                }}
              >
                <div
                  style={{
                    fontFamily: "'JetBrains Mono', monospace",
                    fontSize: "1.25rem",
                    fontWeight: 700,
                    color: "#8ef0d7",
                    letterSpacing: "-0.01em",
                  }}
                >
                  {m.value}
                </div>
                <div
                  style={{
                    fontSize: "0.6875rem",
                    color: "rgba(220,228,245,0.8)",
                    marginTop: 5,
                    lineHeight: 1.4,
                  }}
                >
                  {m.label}
                </div>
              </div>
            ))}
          </div>
          <div>
            <p
              style={{
                fontSize: "0.625rem",
                color: "rgba(220,228,245,0.78)",
                letterSpacing: "0.14em",
                textTransform: "uppercase",
                marginBottom: "0.75rem",
              }}
            >
              주요 구현
            </p>
            <ul className="space-y-2.5">
              {project.details.map((d, i) => (
                <li key={i} className="flex items-start gap-3">
                  <span
                    style={{
                      color: "rgba(142,240,215,0.4)",
                      fontSize: "0.5rem",
                      marginTop: "0.42rem",
                      flexShrink: 0,
                    }}
                  >
                    ▸
                  </span>
                  <span
                    style={{
                      fontSize: "0.875rem",
                      color: "rgba(220,228,245,0.88)",
                      lineHeight: 1.7,
                    }}
                  >
                    {d}
                  </span>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <p
              style={{
                fontSize: "0.625rem",
                color: "rgba(220,228,245,0.78)",
                letterSpacing: "0.14em",
                textTransform: "uppercase",
                marginBottom: "0.75rem",
              }}
            >
              문제 해결
            </p>
            {project.challenges.map((c, i) => (
              <div
                key={i}
                className="rounded-lg p-3.5 mb-2.5"
                style={{
                  background: "rgba(142,240,215,0.02)",
                  border: "1px solid rgba(142,240,215,0.06)",
                }}
              >
                <span
                  style={{
                    fontSize: "0.9375rem",
                    color: "rgba(220,228,245,0.85)",
                    lineHeight: 1.7,
                  }}
                >
                  {c}
                </span>
              </div>
            ))}
          </div>
          <div className="flex flex-wrap gap-2">
            {project.techStack.map((t) => (
              <span
                key={t}
                style={{
                  fontSize: "0.75rem",
                  color: "rgba(142,240,215,0.62)",
                  background: "rgba(142,240,215,0.05)",
                  border: "1px solid rgba(142,240,215,0.1)",
                  padding: "4px 12px",
                  borderRadius: 999,
                  fontWeight: 500,
                }}
              >
                {t}
              </span>
            ))}
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}

/** 미리보기·카드 공통 크기 (Personal/Team/Other 통일) */
const PREVIEW_CLASS = "shrink-0 w-[140px] sm:w-[160px] h-[88px] sm:h-[96px] rounded-lg overflow-hidden";

const titleStyle = {
  fontSize: "1.2rem",
  fontWeight: 700 as const,
  color: "#ccd6f6",
  lineHeight: 1.3,
};
const subtitleStyle: React.CSSProperties = {
  fontSize: "1.0625rem",
  color: "rgba(220,228,245,0.88)",
  lineHeight: 1.55,
  marginTop: "0.35rem",
  whiteSpace: "pre-line",
};
const tagStyle = {
  fontSize: "0.9375rem",
  color: "rgba(142,240,215,0.7)",
  background: "rgba(142,240,215,0.06)",
  border: "1px solid rgba(142,240,215,0.12)",
  padding: "2px 8px",
  borderRadius: 4,
  fontWeight: 500,
};

/** 메인 프로젝트: 미리보기 클릭 시 프로젝트로 이동(viewUrl) 또는 모달 */
function MainProjectRow({
  project,
  index,
  onOpen,
}: {
  project: Project;
  index: number;
  onOpen: () => void;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: "-40px" });
  const hasPreview = project.viewUrl && project.viewUrl.startsWith("/");
  const hasLink = !!project.viewUrl;

  const content = (
    <>
      <div
        className={`${PREVIEW_CLASS} cursor-pointer relative`}
        style={{
          border: "1px solid rgba(142,240,215,0.08)",
          background: "rgba(0,0,0,0.25)",
        }}
      >
        {hasPreview ? (
          <div className="absolute inset-0 overflow-hidden">
            <iframe
              src={project.viewUrl}
              title={`${project.title} 미리보기`}
              className="pointer-events-none border-0 absolute left-0 top-0 origin-top-left"
              style={{
                width: "400%",
                height: "400%",
                transform: "scale(0.25)",
              }}
            />
          </div>
        ) : (
          <div className="w-full h-full flex items-center justify-center p-0 min-h-0 min-w-0">
            <project.icon size={44} className="shrink-0" style={{ color: "rgba(142,240,215,0.4)" }} />
          </div>
        )}
      </div>
      <div className="flex-1 min-w-0 cursor-pointer">
        <div className="flex items-center gap-2 flex-wrap">
          <h3 style={titleStyle} className="group-hover:!text-[#8ef0d7] transition-colors">
            {project.title}
          </h3>
          <ArrowUpRight size={14} style={{ color: "rgba(142,240,215,0.5)" }} className="shrink-0" />
        </div>
        <p style={subtitleStyle}>{project.subtitle}</p>
        <div className="flex flex-wrap gap-1.5 mt-2">
          {project.techStack.slice(0, 5).map((tech) => (
            <span key={tech} style={tagStyle}>
              {tech}
            </span>
          ))}
        </div>
      </div>
    </>
  );

  const motionProps = {
    ref,
    initial: { opacity: 0, y: 12 },
    animate: inView ? { opacity: 1, y: 0 } : {},
    transition: { duration: 0.4, delay: index * 0.08 },
    className: "group flex gap-5 sm:gap-6 items-start rounded-xl -mx-4 sm:-mx-5 px-4 sm:px-5 py-4 transition-all duration-300",
    style: { border: "1px solid transparent", borderBottom: "1px solid rgba(255,255,255,0.32)" },
    onMouseEnter: (e: React.MouseEvent<HTMLElement>) => {
      const el = e.currentTarget as HTMLElement;
      el.style.background = "rgba(142,240,215,0.02)";
      el.style.borderLeftColor = "rgba(142,240,215,0.06)";
      el.style.borderTopColor = "rgba(142,240,215,0.06)";
      el.style.borderRightColor = "rgba(142,240,215,0.06)";
      el.style.borderBottomColor = "rgba(255,255,255,0.32)";
    },
    onMouseLeave: (e: React.MouseEvent<HTMLElement>) => {
      const el = e.currentTarget as HTMLElement;
      el.style.background = "transparent";
      el.style.borderLeftColor = "transparent";
      el.style.borderTopColor = "transparent";
      el.style.borderRightColor = "transparent";
      el.style.borderBottomColor = "rgba(255,255,255,0.32)";
    },
  };

  if (hasLink) {
    return (
      <Link href={project.viewUrl!}>
        <motion.article {...motionProps}>{content}</motion.article>
      </Link>
    );
  }
  return (
    <motion.article
      {...motionProps}
      onClick={onOpen}
      onKeyDown={(e) => e.key === "Enter" && onOpen()}
      role="button"
      tabIndex={0}
    >
      {content}
    </motion.article>
  );
}

/** 서브 프로젝트: 미리보기·글자 크기·태그 스타일 통일, 클릭 시 해당 링크로 이동 */
function SubProjectRow({ sub, index }: { sub: SubProject; index: number }) {
  const ref = useRef<HTMLAnchorElement>(null);
  const inView = useInView(ref, { once: true, margin: "-40px" });

  return (
    <motion.a
      ref={ref}
      href={sub.href}
      target="_blank"
      rel="noopener noreferrer"
      initial={{ opacity: 0, y: 12 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.4, delay: index * 0.08 }}
      className="group flex gap-5 sm:gap-6 items-start rounded-xl -mx-4 sm:-mx-5 px-4 sm:px-5 py-4 transition-all duration-300"
      style={{
        border: "1px solid transparent",
        borderBottom: "1px solid rgba(255,255,255,0.32)",
        textDecoration: "none",
      }}
      onMouseEnter={(e) => {
        const el = e.currentTarget as HTMLAnchorElement;
        el.style.background = "rgba(142,240,215,0.02)";
        el.style.borderLeftColor = "rgba(142,240,215,0.06)";
        el.style.borderTopColor = "rgba(142,240,215,0.06)";
        el.style.borderRightColor = "rgba(142,240,215,0.06)";
        el.style.borderBottomColor = "rgba(255,255,255,0.32)";
      }}
      onMouseLeave={(e) => {
        const el = e.currentTarget as HTMLAnchorElement;
        el.style.background = "transparent";
        el.style.borderLeftColor = "transparent";
        el.style.borderTopColor = "transparent";
        el.style.borderRightColor = "transparent";
        el.style.borderBottomColor = "rgba(255,255,255,0.32)";
      }}
    >
      <div
        className={`${PREVIEW_CLASS} relative overflow-hidden`}
        style={{
          border: "1px solid rgba(142,240,215,0.08)",
          background: sub.previewImage ? "#fff" : "rgba(0,0,0,0.25)",
        }}
      >
        {sub.previewImage ? (
          <Image
            src={sub.previewImage}
            alt=""
            width={160}
            height={96}
            className="absolute inset-0 w-full h-full object-contain object-center rounded-lg"
            unoptimized
          />
        ) : (
          <div
            className="w-full h-full flex flex-col items-center justify-center p-0 min-h-0 min-w-0"
            style={{ background: "rgba(142,240,215,0.08)" }}
          >
            <Key size={44} className="shrink-0" style={{ color: "rgba(142,240,215,0.4)" }} />
            <span
              className="mt-1"
              style={{
                fontSize: "0.625rem",
                fontWeight: 700,
                color: "rgba(220,228,245,0.9)",
                letterSpacing: "0.02em",
              }}
            >
              {sub.title}
            </span>
          </div>
        )}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <h3 style={{ ...titleStyle, whiteSpace: "nowrap" }} className="group-hover:!text-[#8ef0d7] transition-colors shrink-0">
            {sub.title}
          </h3>
          <ExternalLink size={14} style={{ color: "rgba(142,240,215,0.5)" }} className="shrink-0" />
        </div>
        <p style={subtitleStyle}>{sub.description}</p>
        {sub.techStack && sub.techStack.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-2">
            {sub.techStack.map((t) => (
              <span key={t} style={tagStyle}>
                {t}
              </span>
            ))}
          </div>
        )}
      </div>
    </motion.a>
  );
}

const blockLabelStyle = {
  fontFamily: '"Segoe UI", system-ui, -apple-system, BlinkMacSystemFont, sans-serif',
  fontSize: "0.875rem",
  fontWeight: 500 as const,
  color: "rgba(220,228,245,0.88)",
  letterSpacing: "0.06em",
  textTransform: "uppercase" as const,
  marginBottom: "1rem",
};

export function ProjectsSection() {
  const [active, setActive] = useState<Project | null>(null);

  return (
    <section id="projects" className="pt-10 pb-28 scroll-mt-14 md:scroll-mt-0">
      <SectionHeader num="02" label="Main Projects" />
      {/* 카드 행과 동일한 수평 범위: -mx-4 sm:-mx-5 + 명시 너비로 실선이 같은 구간에 맞춤 */}
      <div className="-mx-4 sm:-mx-5 w-[calc(100%+2rem)] sm:w-[calc(100%+2.5rem)] mb-6">
        <div role="presentation" className="portfolio-projects-divider" />
      </div>
      {/* Personal Project — 인사 */}
      <div className="mb-10">
        <p style={blockLabelStyle}>Personal Project</p>
        <div className="space-y-0">
          {PERSONAL_PROJECTS.map((p, i) => (
            <MainProjectRow key={p.id} project={p} index={i} onOpen={() => setActive(p)} />
          ))}
        </div>
      </div>
      {/* Team Project — ESG(AIFIX) */}
      <div className="mb-10">
        <p style={blockLabelStyle}>Team Project</p>
        <div className="space-y-0">
          {TEAM_PROJECTS.map((p, i) => (
            <MainProjectRow key={p.id} project={p} index={i} onOpen={() => setActive(p)} />
          ))}
        </div>
      </div>
      {/* Other Project — 과거 팀프로젝트 (KeyWord 등) */}
      <div>
        <p style={blockLabelStyle}>Other Project</p>
        <div className="space-y-0">
          {SUB_PROJECTS.map((sub, i) => (
            <SubProjectRow key={sub.id} sub={sub} index={i} />
          ))}
        </div>
      </div>
      <AnimatePresence>
        {active && <Modal project={active} onClose={() => setActive(null)} />}
      </AnimatePresence>
    </section>
  );
}
