"use client";

import { useRef, useEffect, useState } from "react";
import { motion, useInView } from "framer-motion";
import { Download, GripVertical } from "lucide-react";
import { SectionHeader } from "./SectionHeader";

/** 드래그 앤 드롭으로 순서 변경 — 문서 편집처럼 위아래로 이동 */
function DraggableItem({
  index,
  onReorder,
  children,
  className = "",
}: {
  index: number;
  onReorder?: (fromIndex: number, toIndex: number) => void;
  children: React.ReactNode;
  className?: string;
}) {
  const [isDragOver, setIsDragOver] = useState(false);
  const handleDragStart = (e: React.DragEvent) => {
    e.dataTransfer.setData("text/plain", String(index));
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.dropEffect = "move";
    if (e.currentTarget instanceof HTMLElement) e.currentTarget.classList.add("opacity-50");
  };
  const handleDragEnd = (e: React.DragEvent) => {
    if (e.currentTarget instanceof HTMLElement) e.currentTarget.classList.remove("opacity-50");
  };
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    setIsDragOver(true);
  };
  const handleDragLeave = () => setIsDragOver(false);
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const fromIndex = parseInt(e.dataTransfer.getData("text/plain"), 10);
    if (Number.isNaN(fromIndex) || fromIndex === index || !onReorder) return;
    onReorder(fromIndex, index);
  };
  const canDrag = !!onReorder;
  return (
    <div
      data-index={index}
      draggable={canDrag}
      onDragStart={canDrag ? handleDragStart : undefined}
      onDragEnd={canDrag ? handleDragEnd : undefined}
      onDragOver={canDrag ? handleDragOver : undefined}
      onDragLeave={canDrag ? handleDragLeave : undefined}
      onDrop={canDrag ? handleDrop : undefined}
      className={`flex items-start gap-2 transition-colors ${canDrag ? "cursor-grab active:cursor-grabbing" : ""} ${isDragOver ? "bg-slate-100 rounded" : ""} ${className}`}
    >
      {canDrag && (
        <span className="shrink-0 mt-1.5 p-0.5 rounded text-slate-400 hover:text-slate-600 hover:bg-slate-200" aria-label="드래그하여 순서 변경">
          <GripVertical size={14} />
        </span>
      )}
      <div className="flex-1 min-w-0">{children}</div>
    </div>
  );
}

/** 클릭 시 입력란으로 전환, blur 시 저장 — 웹에서 해당 위치 클릭으로 바로 수정 */
function EditableSpan({
  value,
  field,
  onSave,
  className,
  placeholder,
  multiline,
  inputVariant = "dark",
}: {
  value: string;
  field: "name" | "nameEn" | "tagline" | "email" | "phone" | "github" | "blog" | "summary";
  onSave?: (field: "name" | "nameEn" | "tagline" | "email" | "phone" | "github" | "blog" | "summary", value: string) => void;
  className?: string;
  placeholder?: string;
  multiline?: boolean;
  /** dark = 헤더(어두운 배경), light = 본문(흰 배경) */
  inputVariant?: "dark" | "light";
}) {
  const [editing, setEditing] = useState(false);
  const [local, setLocal] = useState(value);
  const ref = useRef<HTMLInputElement | HTMLTextAreaElement>(null);
  useEffect(() => {
    setLocal(value);
  }, [value]);
  useEffect(() => {
    if (editing) ref.current?.focus();
  }, [editing]);
  const save = () => {
    setEditing(false);
    const trimmed = local.trim();
    if (onSave && trimmed !== value) onSave(field, trimmed);
  };
  if (!onSave) {
    return <span className={className} style={multiline ? { whiteSpace: "pre-wrap" } : undefined}>{value || placeholder}</span>;
  }
  if (editing) {
    const inputClass = inputVariant === "dark"
      ? "bg-white/10 border-white/30 text-white"
      : "bg-slate-50 border-slate-300 text-slate-800";
    const common = {
      ref: ref as React.RefObject<HTMLInputElement & HTMLTextAreaElement>,
      value: local,
      onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setLocal(e.target.value),
      onBlur: save,
      onKeyDown: (e: React.KeyboardEvent) => { if (e.key === "Enter" && !multiline) { e.preventDefault(); save(); } },
      className: "w-full min-w-0 border rounded px-1.5 py-0.5 outline-none focus:ring-1 focus:ring-slate-400 " + inputClass,
    };
    if (multiline) {
      return <textarea {...common} rows={4} className={common.className + " resize-y"} />;
    }
    return <input type="text" {...common} />;
  }
  return (
    <span
      role="button"
      tabIndex={0}
      onClick={() => setEditing(true)}
      onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") setEditing(true); }}
      className={(className || "") + " cursor-text rounded focus:outline-none focus:ring-1 " + (inputVariant === "dark" ? "hover:bg-white/10 focus:ring-white/40" : "hover:bg-slate-100 focus:ring-slate-400")}
      title="클릭하여 수정"
      style={multiline ? { whiteSpace: "pre-wrap", display: "block" } : undefined}
    >
      {value || placeholder || " "}
    </span>
  );
}

/** 연락처·메트릭·기술 카테고리·프로젝트 등 확장 이력서 데이터 타입 */
function normalizeUrl(url: string): string {
  if (!url || !url.trim()) return "#";
  const t = url.trim();
  if (t.startsWith("http://") || t.startsWith("https://")) return t;
  if (t.startsWith("www.")) return `https://${t}`;
  return `https://${t}`;
}

export type ResumeData = {
  name: string;
  nameEn: string;
  tagline: string;
  taglineQuote: string;
  email: string;
  phone?: string;
  github: string;
  blog: string;
  homepage?: string;
  summary: string;
  metrics: { value: string; label: string }[];
  skillsByCategory: { title: string; tags: string[]; hot?: string[] }[];
  /** 비개발 경험 (사진처럼 개발 경험과 분리) */
  nonDevExperience: {
    period: string;
    title: string;
    desc?: string;
    bullets?: string[];
  }[];
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

/** 이력서 데이터 (모달·섹션 공통) — 프로젝트/경력 기준 핵심 스택 반영 */
export const RESUME_SAMPLE: ResumeData = {
  name: "강경구",
  nameEn: "Kang Gyeong-gu",
  tagline: "기술적 맥락을 팀과 공유하며 함께 성능 개선을 만들어가는 AI 풀스택 개발자",
  taglineQuote: "기술적 맥락을 팀과 공유하며 함께 성능 개선을 만들어가는 AI 풀스택 개발자",
  email: "kku1031@naver.com",
  phone: "010-4739-2339",
  github: "github.com/ConversionDev",
  blog: "kku1031.tistory.com",
  homepage: "www.kanggyeonggu.store",
  summary:
    "비영리 NGO 근무 후 백엔드 개발에 도전했습니다. 문제를 해결해 나가는 과정과 학습이 즐겁고, 다양한 경험을 통해 소통과 관계를 중요하게 생각합니다. 의료 IT·백엔드 교육을 거쳐 Spring, FastAPI, LangChain 등으로 프로젝트를 진행하고 있습니다.",
  metrics: [],
  nonDevExperience: [
    { period: "2013", title: "통기타 동아리 YEP 부회장" },
    { period: "2014", title: "필리핀(팡가시난) 해외 자원봉사 RaonAtti(6개월)" },
    { period: "2018 – 2019", title: "대구 YMCA 남자 중장기 청소년 쉼터 팀원" },
    { period: "2019 – 2020", title: "한국 YMCA전국연맹 국제개발협력팀 팀원" },
  ],
  skillsByCategory: [
    { title: "Frontend", tags: ["Next.js", "React 19", "TypeScript", "Tailwind CSS", "Zustand", "shadcn/ui", "Framer Motion", "Recharts"], hot: ["Next.js", "React 19", "TypeScript"] },
    { title: "Backend", tags: ["FastAPI", "Spring Boot", "Python", "SQLAlchemy", "Alembic", "Pydantic", "JWT", "PostgreSQL"], hot: ["FastAPI", "Spring Boot"] },
    { title: "AI / ML", tags: ["LangChain", "LangGraph", "Sentence-Transformers", "FlagEmbedding", "BGE-M3", "Llama", "EXAONE", "Gemini", "LoRA", "QLoRA"], hot: ["LangChain", "LangGraph"] },
    { title: "Data & Infra", tags: ["PostgreSQL", "pgvector", "FAISS", "Redis", "BullMQ", "Docker", "AWS EC2", "NGINX"], hot: ["PostgreSQL", "pgvector", "FAISS"] },
    { title: "DevOps", tags: ["Vercel", "Docker", "GitHub Actions", "CI/CD", "Rolling Update"], hot: ["Docker", "GitHub Actions"] },
  ],
  experience: [
    {
      period: "2023.04 – 2024.01",
      title: "제로베이스 백엔드 스쿨 15기",
      org: "Backend Developer",
      bullets: [
        "팀 프로젝트 KeyWord — OAuth 2.0 소셜 로그인, ElasticSearch 회원 검색 기능 구현",
        "검색 시 이미지 S3 연동, 기술 문서화 및 코드 리뷰를 통한 팀 지식 공유",
      ],
      tags: ["Spring Boot", "ElasticSearch", "OAuth", "AWS S3"],
      current: false,
    },
    {
      period: "2022.09 – 2022.12",
      title: "(주)화산시스템 | 의료 IT",
      org: "인터페이스 팀 / 사원",
      bullets: [
        "국내 대학병원 LIS(검사정보시스템)와 장비 간 시리얼 통신 인터페이스 데이터 전송·검증",
        "전국 병원 출장 — 장비·LIS 연동 확인, LOG 분석 및 네트워크 점검",
      ],
      tags: ["Visual Basic 6.0"],
      current: false,
    },
    {
      period: "2022.02 – 2022.09",
      title: "대구 중앙 직업전문학교",
      org: "응용 SW 엔지니어링 Java class 수료",
      desc: "JAVA와 Spring을 활용한 통합 시스템 구축 개발자 양성 과정, 웹 쇼핑몰 개인 프로젝트 진행.",
      tags: ["Java", "Spring"],
      current: false,
    },
  ],
  education: [
    { school: "영남대학교", info: "중어중문학과 졸업", period: "2017" },
    { school: "제로베이스 백엔드 스쿨 15기", info: "백엔드 기본·프레임워크 심화, 프론트 협업 경험", period: "2023.04 – 2024.01" },
    { school: "대구 중앙 직업전문학교", info: "응용 SW 엔지니어링 Java class 수료", period: "2022.02 – 2022.09" },
  ],
  projects: [
    {
      title: "KeyWord (Keep Your Word)",
      type: "팀 프로젝트 | 2023–2024",
      desc: "소셜 로그인(OAuth 2.0) 및 ElasticSearch·Kibana를 활용한 회원 검색 기능 담당. 검색 시 이미지 S3 연동 구현.",
      metrics: ["OAuth 2.0", "ElasticSearch", "AWS S3"],
      stack: ["Spring Boot", "ElasticSearch", "OAuth", "JPA", "MySQL", "AWS S3"],
    },
    {
      title: "Intelligent HR Agent",
      type: "개인 프로젝트 | 2025",
      desc: "OCR & RAG 기반 HR 문서 분석 에이전트. 멀티 포맷 PDF/이미지 OCR, RAG Chunking 최적화, FastAPI RESTful API 설계.",
      metrics: ["OCR 95%", "추론 +40%", "비용 -60%"],
      stack: ["Python", "LangChain", "FastAPI"],
    },
    {
      title: "AIFIX",
      type: "팀 AIFIXR (AI 파트 리드) | 2025",
      desc: "EUBR·IRA 등 글로벌 규제 대응용 배터리 특화 통합 공급망 솔루션. ERP/MES 연동으로 제조·운영 데이터 표준화, PCF 기반 LCA 및 공급망 리스크 가시화 데이터 거버넌스 구축.",
      metrics: ["리스크 탐지 92%", "자동화 85%"],
      stack: ["Next.js", "React 19", "TypeScript", "FastAPI", "Python", "LangChain", "LangGraph", "PostgreSQL", "pgvector", "FAISS", "Redis", "BullMQ", "Docker", "AWS EC2", "Vercel", "GitHub Actions"],
    },
  ],
  aboutCards: [
    {
      title: "배움이 즐거운 개발자",
      text: "개발자 과정을 학습하면서 문제를 해결해 나가는 과정이 즐겁고, 극복했을 때 성취감을 느꼈습니다. 학습할수록 개발에 대한 지식이 쌓이고 이해될 때 행복을 느끼며 더 알아가고 싶어 합니다.",
    },
    {
      title: "소통을 중요하게 생각합니다",
      text: "필리핀 해외 자원봉사(6개월), YMCA 국제개발협력팀·청소년 쉼터 활동을 통해 다양한 배경의 사람들과 협력해 왔습니다. 관계에 있어 장점을 보는 것이 습관화되어 있습니다. \"혼자 가면 빨리, 함께 가면 멀리.\"",
    },
  ],
  skills: ["Spring Boot", "FastAPI", "Python", "LangChain", "LangGraph", "Next.js", "React 19", "TypeScript", "PostgreSQL", "pgvector", "FAISS", "Docker", "AWS EC2", "Vercel", "GitHub Actions"],
  educationLegacy: "영남대 중어중문 졸업 · 대구 중앙 직업전문학교 응용 SW 수료 · 제로베이스 백엔드 스쿨 15기 수료 · 필리핀 자원봉사 6개월, YMCA 활동",
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
                <span className="text-xs font-medium tabular-nums" style={{ fontFamily: "var(--resume-mono)", color: mutedColor }}>{item.period}</span>
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

/** 섹션 제목: 통일된 크기·자간·여백 (2페이지 레이아웃에 맞게 컴팩트) */
function ResumeSectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="resume-section-title text-[10px] font-bold uppercase tracking-[0.12em] text-[var(--resume-ink)] border-b-2 border-[var(--resume-border)] pb-1 mb-2">
      {children}
    </h2>
  );
}

/** 항목 한 줄: 제목(좌) | 기간(우) — 3번 사진 스타일 */
function ResumeEntryRow({ title, period }: { title: string; period: string }) {
  return (
    <div className="flex justify-between items-baseline gap-4 border-b border-[var(--resume-border)] border-dotted pb-0.5">
      <span className="text-sm font-semibold text-[var(--resume-ink)]">{title}</span>
      <span className="text-[11px] text-[var(--resume-mute)] shrink-0 tabular-nums" style={{ fontFamily: "var(--resume-mono)" }}>{period}</span>
    </div>
  );
}

/** 항목 아래 적을 공간: 불릿 리스트 (3번처럼 여백 있게) */
function ResumeEntryBody({ bullets }: { bullets: string[] }) {
  if (bullets.length === 0) return <div className="resume-write-space mt-2 min-h-[2.5rem] pl-4 text-xs text-[var(--resume-mute)] leading-relaxed" />;
  return (
    <ul className="mt-2 pl-4 space-y-1 text-xs text-[var(--resume-ink)] leading-relaxed list-disc list-outside">
      {bullets.map((line, i) => (
        <li key={i}>{line}</li>
      ))}
    </ul>
  );
}

/** 표: PDF 참고 — 헤더/본문 패딩·글자 크기 통일 (들쭉날쭉 방지) */
const resumeTableClass = "w-full border-collapse text-left table-fixed text-[11px]";
const resumeThClass = "border border-[var(--resume-border)] bg-[#f1f5f9] px-2.5 py-1.5 font-semibold text-[var(--resume-ink)] text-[10px] uppercase tracking-[0.08em] align-top";
const resumeTdClass = "border border-[var(--resume-border)] px-2.5 py-1.5 text-[11px] text-[var(--resume-ink)] align-top bg-white leading-[1.35]";

const RESUME_STORAGE_KEY = "portfolio-resume";

/** localStorage에서 이력서 데이터 로드 (없으면 기본값) */
export function loadResumeFromStorage(): ResumeData {
  if (typeof window === "undefined") return RESUME_SAMPLE;
  try {
    const raw = window.localStorage.getItem(RESUME_STORAGE_KEY);
    if (!raw) return RESUME_SAMPLE;
    const parsed = JSON.parse(raw) as Partial<ResumeData>;
    const merged = { ...RESUME_SAMPLE, ...parsed };
    if (!Array.isArray(merged.nonDevExperience)) merged.nonDevExperience = RESUME_SAMPLE.nonDevExperience;
    return merged;
  } catch {
    return RESUME_SAMPLE;
  }
}

/** 모달 전용: 흑백·회색 이력서 톤, 좌측 Tech Stack 영역에 회색 배경 */
const RESUME_HEADER_BG = "#374151";
const RESUME_HEADER_BORDER = "#6b7280";
const RESUME_SIDEBAR_BG = "#f3f4f6";

export type ResumeLayout = {
  sidebarWidth: number;
  fontSizeScale: number;
  padding: "narrow" | "normal" | "wide";
};

const PADDING_MAP = { narrow: "p-4 sm:p-5", normal: "p-6 sm:p-8", wide: "p-8 sm:p-10" } as const;

export function ResumeModalContent({
  currentPage = 1,
  resumeData,
  resumeLayout,
  onSaveResume,
  showAllPages = false,
}: {
  currentPage?: 1 | 2;
  resumeData?: ResumeData;
  resumeLayout?: ResumeLayout;
  onSaveResume?: (next: ResumeData) => void;
  /** true면 1/2 전환 없이 한 번에 스크롤로 모두 표시 */
  showAllPages?: boolean;
}) {
  const R = resumeData ?? RESUME_SAMPLE;
  const layout = resumeLayout ?? { sidebarWidth: 200, fontSizeScale: 1, padding: "normal" as const };
  const ink = "#111827";
  const mute = "#4b5563";
  const border = "#e5e7eb";
  const bar = "#6b7280";

  const handleSaveField = (field: "name" | "nameEn" | "tagline" | "email" | "phone" | "github" | "blog" | "summary", value: string) => {
    if (!onSaveResume) return;
    onSaveResume({ ...R, [field]: field === "phone" ? (value || undefined) : value });
  };

  const reorder = <T,>(arr: T[], from: number, to: number): T[] => {
    const next = [...arr];
    const [removed] = next.splice(from, 1);
    next.splice(to, 0, removed);
    return next;
  };
  const handleReorderEducation = (fromIndex: number, toIndex: number) => {
    onSaveResume?.({ ...R, education: reorder(R.education, fromIndex, toIndex) });
  };
  const handleReorderExperience = (fromIndex: number, toIndex: number) => {
    onSaveResume?.({ ...R, experience: reorder(R.experience, fromIndex, toIndex) });
  };
  const handleReorderProjects = (fromIndex: number, toIndex: number) => {
    onSaveResume?.({ ...R, projects: reorder(R.projects, fromIndex, toIndex) });
  };
  const handleReorderSkills = (fromIndex: number, toIndex: number) => {
    onSaveResume?.({ ...R, skillsByCategory: reorder(R.skillsByCategory, fromIndex, toIndex) });
  };

  const rootPadding = layout.padding === "narrow" ? "pt-0 pl-0 pr-4 sm:pr-5 pb-0" : layout.padding === "wide" ? "pt-0 pl-0 pr-8 sm:pr-10 pb-0" : "pt-0 pl-0 pr-6 sm:pr-8 pb-0";
  const sidebarStyle: React.CSSProperties = {
    width: `${layout.sidebarWidth}px`,
    minWidth: `${layout.sidebarWidth}px`,
    background: RESUME_SIDEBAR_BG,
  };
  return (
    <div
      id="resume-modal-print-area"
      className={`resume-content resume-modal-content resume-modal-paged resume-padding-${layout.padding} resume-edge-to-edge w-full min-h-full bg-white text-left overflow-y-auto h-full ${rootPadding} ${showAllPages ? "resume-single-scroll" : ""}`}
      data-current-page={showAllPages ? "all" : currentPage}
      style={
        {
          "--resume-ink": ink,
          "--resume-mute": mute,
          "--resume-border": border,
          "--resume-bar": bar,
          "--resume-mono": "'JetBrains Mono', 'SF Mono', Consolas, monospace",
          "--resume-sidebar-width": `${layout.sidebarWidth}px`,
          "--resume-font-scale": layout.fontSizeScale,
          fontSize: `${layout.fontSizeScale * 100}%`,
        } as React.CSSProperties
      }
    >
      {/* 1페이지: 헤더 + flex row (aside stretch → 메인 콘츠 높이에 맞춤) */}
      <div
        className="resume-page-1 flex flex-col"
        style={{ minHeight: showAllPages ? undefined : "100%" }}
      >
        <header
            className="resume-header-with-photo pb-4 mb-0 px-6 pt-5 sm:px-8 sm:pt-6 -mr-6 sm:-mr-8 shrink-0"
            style={{ borderBottom: `3px solid ${RESUME_HEADER_BORDER}`, background: RESUME_HEADER_BG, marginLeft: 0, marginTop: 0 }}
          >
            <div className="min-w-0">
              <h1 className="text-base sm:text-lg font-bold tracking-tight text-white">
                <EditableSpan value={R.name} field="name" onSave={onSaveResume ? handleSaveField : undefined} className="text-white" />{" "}
                <span className="font-normal text-gray-300">·</span>{" "}
                <EditableSpan value={R.nameEn} field="nameEn" onSave={onSaveResume ? handleSaveField : undefined} className="text-white" />
              </h1>
              <p className="mt-1 text-[10px] font-semibold uppercase tracking-[0.08em] text-gray-300 line-clamp-2" title={R.tagline}>
                <EditableSpan value={R.tagline} field="tagline" onSave={onSaveResume ? handleSaveField : undefined} className="text-gray-300" />
              </p>
              <div className="mt-2 flex flex-wrap gap-x-4 gap-y-0.5 text-[11px] text-gray-200">
                <span>@ </span>
                <a href={`mailto:${R.email}`} className="text-gray-200 hover:underline focus:outline-none focus:underline" target="_blank" rel="noopener noreferrer">{R.email}</a>
                <span>P </span><EditableSpan value={R.phone ?? ""} field="phone" onSave={onSaveResume ? handleSaveField : undefined} className="text-gray-200" placeholder="연락처" />
                <span>G </span>
                <a href={normalizeUrl(R.github)} className="text-gray-200 hover:underline focus:outline-none focus:underline" target="_blank" rel="noopener noreferrer">{R.github}</a>
                <span>B </span>
                <a href={normalizeUrl(R.blog)} className="text-gray-200 hover:underline focus:outline-none focus:underline" target="_blank" rel="noopener noreferrer">{R.blog}</a>
                {(R.homepage != null && R.homepage.trim() !== "") && (
                  <>
                    <span>H </span>
                    <a href={normalizeUrl(R.homepage)} className="text-gray-200 hover:underline focus:outline-none focus:underline" target="_blank" rel="noopener noreferrer">{R.homepage}</a>
                  </>
                )}
              </div>
              <p className="mt-3 text-[11px] text-gray-200 leading-[1.45] max-w-2xl">
                <EditableSpan value={R.summary} field="summary" onSave={onSaveResume ? handleSaveField : undefined} className="text-gray-200" multiline inputVariant="dark" />
              </p>
            </div>
          </header>

        <div style={{ flex: 1, display: "flex", flexDirection: "row", alignItems: "stretch" }}>
          <aside className="resume-tech-sidebar shrink-0 p-2.5 lg:p-3" style={sidebarStyle}>
            <ResumeSectionTitle>Tech Stack</ResumeSectionTitle>
            <div className="space-y-2">
              {R.skillsByCategory.map((cat, i) => (
                <DraggableItem key={`skill-${i}-${cat.title}`} index={i} onReorder={handleReorderSkills}>
                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-[0.1em] text-[var(--resume-ink)] mb-0.5">{cat.title}</p>
                    <div className="flex flex-wrap gap-1">
                      {cat.tags.map((t) => (
                        <span
                          key={t}
                          className="rounded px-1.5 py-0.5 text-[10px] border border-[var(--resume-border)] text-[var(--resume-ink)] bg-white leading-snug"
                          style={cat.hot?.includes(t) ? { background: "#e5e7eb", fontWeight: 600, borderColor: bar } : {}}
                        >
                          {t}
                        </span>
                      ))}
                    </div>
                  </div>
                </DraggableItem>
              ))}
            </div>
          </aside>
          <div className="resume-main-content flex-1 min-w-0 space-y-4 pl-4 lg:pl-5 pr-6 sm:pr-8 pt-3 pb-8 bg-white">
            <section>
              <ResumeSectionTitle>Education</ResumeSectionTitle>
              <table className={resumeTableClass}>
                <thead>
                  <tr>
                    <th className={resumeThClass + " resume-col-period"}>기간</th>
                    <th className={resumeThClass} style={{ width: "34%" }}>기관</th>
                    <th className={resumeThClass}>상세</th>
                  </tr>
                </thead>
                <tbody>
                  {R.education.map((ed, i) => (
                    <tr key={`edu-${i}-${ed.school}`}>
                      <td className={resumeTdClass + " text-[var(--resume-mute)] tabular-nums"} style={{ fontFamily: "var(--resume-mono)" }}>{ed.period}</td>
                      <td className={resumeTdClass + " font-semibold text-[var(--resume-ink)]"}>{ed.school}</td>
                      <td className={resumeTdClass + " text-[var(--resume-mute)]"}>{ed.info}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
            {R.nonDevExperience.length > 0 && (
              <section>
                <ResumeSectionTitle>비개발 경험</ResumeSectionTitle>
                <table className={resumeTableClass}>
                  <thead>
                    <tr>
                      <th className={resumeThClass + " resume-col-period"}>기간</th>
                      <th className={resumeThClass}>내용</th>
                    </tr>
                  </thead>
                  <tbody>
                    {R.nonDevExperience.map((item, i) => (
                      <tr key={`nondev-${i}-${item.period}`}>
                        <td className={resumeTdClass + " text-[var(--resume-mute)] tabular-nums"} style={{ fontFamily: "var(--resume-mono)" }}>{item.period}</td>
                        <td className={resumeTdClass}>
                          <span className="text-[11px] font-semibold text-[var(--resume-ink)]">{item.title}</span>
                          {(item.bullets?.length ?? 0) > 0 && (
                            <ul className="list-disc list-outside pl-4 mt-0.5 space-y-0.5 text-[11px] text-[var(--resume-ink)] leading-snug">
                              {item.bullets!.map((line, j) => (
                                <li key={j}>{line}</li>
                              ))}
                            </ul>
                          )}
                          {item.desc && !item.bullets?.length && (
                            <p className="mt-0.5 text-[11px] text-[var(--resume-mute)] leading-snug">{item.desc}</p>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </section>
            )}
            <section className="resume-career-section">
              <ResumeSectionTitle>개발 경력</ResumeSectionTitle>
              <table className={resumeTableClass}>
                <thead>
                  <tr>
                    <th className={resumeThClass + " resume-col-period"}>기간</th>
                    <th className={resumeThClass} style={{ width: "38%" }}>회사 / 역할</th>
                    <th className={resumeThClass}>업무 내용</th>
                  </tr>
                </thead>
                <tbody>
                  {R.experience.map((exp, i) => (
                    <tr key={`exp-${i}-${exp.period}`}>
                      <td className={resumeTdClass + " text-[var(--resume-mute)] tabular-nums"} style={{ fontFamily: "var(--resume-mono)" }}>{exp.period}</td>
                      <td className={resumeTdClass + " font-semibold text-[var(--resume-ink)]"}>{exp.title} | {exp.org}</td>
                      <td className={resumeTdClass}>
                        <ul className="list-disc list-outside pl-4 space-y-0.5 text-[11px] text-[var(--resume-ink)] leading-snug pr-1">
                          {(exp.bullets ?? (exp.desc ? [exp.desc] : [])).map((line, j) => (
                            <li key={j}>{line}</li>
                          ))}
                        </ul>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          </div>
        </div>
      </div>

      {/* 2페이지: Project + Key Metrics + Self-introduction (세로형 2페이지 수납) */}
      <div className="resume-page-2 pb-0">
        <section className="pt-0.5">
          <ResumeSectionTitle>Project</ResumeSectionTitle>
          <table className={resumeTableClass}>
            <thead>
              <tr>
                <th className={resumeThClass + " resume-col-period"}>기간</th>
                <th className={resumeThClass} style={{ width: "26%" }}>프로젝트</th>
                <th className={resumeThClass}>설명 · 메트릭</th>
              </tr>
            </thead>
            <tbody>
              {R.projects.map((proj, i) => {
                const period = proj.type.includes("|") ? proj.type.split("|")[1].trim() : proj.type;
                return (
                  <tr key={`proj-${i}-${proj.title}`}>
                    <td className={resumeTdClass + " text-[var(--resume-mute)] tabular-nums"} style={{ fontFamily: "var(--resume-mono)" }}>{period}</td>
                    <td className={resumeTdClass + " font-semibold text-[var(--resume-ink)]"}>{proj.title}</td>
                    <td className={resumeTdClass}>
                      <p className="text-[11px] text-[var(--resume-ink)] leading-snug">{proj.desc}</p>
                      {proj.metrics.length > 0 && (
                        <ul className="mt-0.5 list-disc list-outside pl-4 space-y-0.5 text-[11px] text-[var(--resume-ink)]">
                          {proj.metrics.map((m) => (
                            <li key={m}>{m}</li>
                          ))}
                        </ul>
                      )}
                      {proj.stack.length > 0 && (
                        <div className="mt-0.5 flex flex-wrap gap-1">
                          {proj.stack.map((s) => (
                            <span key={s} className="rounded px-1 py-0.5 text-[10px] bg-[#f8fafc] text-[var(--resume-mute)]">{s}</span>
                          ))}
                        </div>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </section>

        <section className="mt-3">
          <ResumeSectionTitle>Key Metrics</ResumeSectionTitle>
          <div className="min-h-[4.5rem] bg-white rounded border border-[var(--resume-border)]" aria-label="Key Metrics 입력 공간" />
        </section>

        <section className="mt-3">
          <div className="bg-[#f3f4f6] -mx-1 px-2.5 py-1 mb-0">
            <h2 className="text-[10px] font-bold uppercase tracking-[0.1em] text-[var(--resume-ink)]">Self-introduction</h2>
          </div>
          <div className="border-b border-[var(--resume-border)] mb-1.5" aria-hidden />
          <div className="resume-write-space min-h-[3.5rem] pl-2.5 pt-1 text-[11px] text-[var(--resume-ink)] leading-snug whitespace-pre-wrap">
            <EditableSpan value={R.summary} field="summary" onSave={onSaveResume ? handleSaveField : undefined} className="text-[var(--resume-ink)]" multiline inputVariant="light" />
          </div>
          <div className="resume-write-space mt-1.5 min-h-[2rem] pl-2.5 border border-dashed border-[var(--resume-border)] rounded p-1.5 text-[11px] text-[var(--resume-mute)]">
          </div>
        </section>

        <footer
          className="pt-4 mt-3 pb-2 text-center text-[11px] text-[var(--resume-mute)] italic"
          style={{ borderTop: `2px solid ${border}` }}
        >
          &quot;{R.taglineQuote}&quot;
        </footer>
      </div>
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
