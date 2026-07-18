"use client";

import { useState, useRef, Fragment } from "react";
import Image from "next/image";
import { motion, useInView, AnimatePresence } from "framer-motion";
import { Bot, Leaf, X, ArrowUpRight, ExternalLink, Key, Megaphone, Activity } from "lucide-react";
import { SectionHeader } from "./SectionHeader";

/** RAG 품질 평가 표 (계층 × 지표 × 개선전후 × 적용 작업) */
interface EvalTier {
  tier: string;
  rows: { metric: string; change: string; work: string }[];
}

interface ProjectLink {
  label: string;
  href: string;
}

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
  evalTable?: EvalTier[];
  links?: ProjectLink[];
  /** 내부 경로일 때 카드 미리보기 iframe으로 사용 */
  previewUrl?: string;
}

/** 서브 프로젝트: 작은 미리보기 + 클릭 시 외부 링크(없으면 정적 카드) */
interface SubProject {
  id: string;
  title: string;
  description: string;
  href?: string;
  /** 미리보기 이미지 URL (없으면 디자인 플레이스홀더) */
  previewImage?: string;
  techStack?: string[];
  icon?: typeof Key;
}

/** 카테고리: Personal / Team / Other(과거·소규모 프로젝트) */
const PROJECT_CATEGORY = { personal: "personal", team: "team", other: "other" } as const;

const PROJECTS: (Project & { category: keyof typeof PROJECT_CATEGORY })[] = [
  {
    id: "hr-insight",
    title: "HR Insight (Success DNA)",
    subtitle:
      "비정형 업무 데이터(이력서·메일·회의록) 통합 HCM 플랫폼.\nsLLM 파인튜닝부터 Agentic RAG·CPU 서빙까지 전 계층 직접 구현",
    description:
      "이력서·메일·회의록 등 비정형 업무 데이터를 통합해 ISO 30414 기반으로 역량을 정량화하고, 채용 이후 역량 발현·성장을 추적하는 HCM 플랫폼. EXAONE 파인튜닝, 11.8만 건 역량 지식베이스, LangGraph 기반 SSE 스트리밍 채팅까지 전 과정을 직접 구현했습니다.",
    icon: Bot,
    type: "개인 프로젝트 · 삼정KPMG",
    year: "2026",
    category: "personal",
    metrics: [
      { label: "EXAONE 학습 속도 (4bit 양자화)", value: "2×" },
      { label: "11.8만 건 FAISS 인덱스 빌드", value: "~12초" },
      { label: "12개 시나리오 Tool Calling 성공률", value: "0.95" },
    ],
    techStack: ["EXAONE Fine-tuning", "QLoRA · Unsloth", "LangGraph", "BGE-M3 · FAISS", "llama.cpp"],
    details: [
      "멀티 포맷 문서 파싱 + 스캔본 OCR → LLM 의미 분석 → 5대 핵심 역량 정량화(리더십·기술력·창의성·협업·적응력)",
      "직무역량 원천(O*NET·NCS) 11.8만 건 → BGE-M3 임베딩 → FAISS K-Means·UMAP → 파인튜닝 EXAONE 자동 라벨링 지식베이스",
      "LangGraph RAG 에이전트 SSE 스트리밍 채팅 — 직원·성과·공시·역량 단일·복합 질의",
      "Polyglot 아키텍처 — Spring Boot(인증 게이트웨이) + FastAPI(AI 연산) 분리, 헥사고날 라이트 레이어링",
    ],
    challenges: [
      "GPU 파인튜닝 모델의 CPU 서빙 — NF4 4bit 학습 모델을 GGUF Q4_K_M으로 재변환, 변환 중 tokenizer 손상은 수동 패치, OOM은 n_ctx 축소로 해결해 GPU 없는 EC2에 배포",
      "Neon 스토리지 한도로 11.8만 건 임베딩 적재 불가 → 검색 계층 이원화: 정적·대용량(역량·공시)은 FAISS 인메모리, 동적·트랜잭션(직원)은 pgvector HNSW·FlatIP",
      "Transformers + PEFT + bitsandbytes 4bit 양자화로 EXAONE 학습 약 2배, Unsloth로 LLaMA 학습 2.5~3배 가속",
    ],
    links: [
      { label: "인사 시스템 데모", href: "/hr" },
      { label: "GitHub", href: "https://github.com/ConversionDev/251218langchain" },
    ],
    previewUrl: "/hr",
  },
  {
    id: "clickme",
    title: "ClickMe",
    subtitle:
      "광고 집행 전 AI 소비자 시뮬레이션으로 사전 검증·개선하고,\n집행 후 실측 성과 진단·조치 제안까지 연결하는 광고 운영 플랫폼",
    description:
      "Meta 광고 캠페인 실측 데이터를 실시간 연동하고, LangGraph ReAct 딥에이전트가 운영·생성 작업을 한 채팅에서 조율하는 광고 운영 플랫폼. 이상 감지→진단→조치 제안→HITL 승인 플로우와 Ragas 기반 RAG 품질 평가 체계 구축을 담당했습니다.",
    icon: Megaphone,
    type: "팀 프로젝트 · 6인 · 하이미디어",
    year: "2026",
    category: "team",
    metrics: [
      { label: "RAG Hit Rate@K (단일·복합)", value: "1.000" },
      { label: "MRR (0.705에서 개선)", value: "0.938" },
      { label: "Faithfulness", value: "0.51→1.00" },
    ],
    techStack: ["LangGraph", "LangSmith · Ragas", "pgvector (Neon)", "Meta Graph API", "FastAPI"],
    details: [
      "LangGraph ReAct 딥에이전트 오케스트레이터 — plan→act→observe 루프로 운영·생성 작업을 한 채팅에서 조율",
      "pgvector 벡터 검색 + GIN 키워드 검색 → RRF 융합 하이브리드 검색 구축",
      "채팅 메모리 3단 구조 — 최근 원문·요약·롱텀(tsvector 키워드 회수) 컨텍스트 조립",
      "이상 감지 → 진단 → 조치 제안 → Tier 판정 → 자율 통과/사람 승인(HITL) 분기 — '관측은 자율, 집행은 사람' 경계 설계",
      "Meta Graph API 실측 연동 — 배치 insights·TTL 캐시·토큰 암호화",
    ],
    challenges: [
      "정답 문서가 검색 상위에 안정적으로 노출되지 않음 → 청크 크기 조정·리랭커 도입·프롬프트 강화·랭킹 알고리즘·few-shot 보강 (결과는 아래 평가 표)",
      "모델 검증용 실측 데이터 부재 → Meta에 사비로 트래픽·잠재고객 캠페인을 직접 집행, 실측 CTR·CPC를 확보해 합성 데이터의 한계 극복",
      "Meta API Standard 등급 제약 → 15일 내 실호출 500개 적립, 사업자 등록 후 Advanced 상향 신청 — 선제 구현으로 승인 즉시 실서비스 전환 설계",
    ],
    evalTable: [
      {
        tier: "RAG Pipeline 평가 지표",
        rows: [
          {
            metric: "Hit Rate@K",
            change: "단일 0.886 → 1.000 · 복합 0.800 → 1.000",
            work: "하이브리드 검색, 검색 결과 다양화, 리랭킹",
          },
          {
            metric: "MRR",
            change: "단일 0.705 → 0.938 · 복합 0.634 → 0.833",
            work: "리랭킹을 통한 정답 문서 순위 개선",
          },
          {
            metric: "Context Precision",
            change: "단일 신규측정 → 0.886 · 복합 신규측정 → 0.926",
            work: "관련 문서 정밀도 지표 신규 도입, 계산 로직 오류 수정",
          },
        ],
      },
      {
        tier: "LLM as Judge",
        rows: [
          {
            metric: "Faithfulness",
            change: "0.51 → 1.00",
            work: "자료 근거 강제, CRAG 기반 자기교정, 재검색·답변 거절",
          },
          {
            metric: "Factual Correctness",
            change: "단일 0.714 → 0.986 · 복합 0.857 → 0.971",
            work: "회사 고유 규칙에 대한 자료 기반 답변 강제",
          },
          {
            metric: "환각 억제",
            change: "함정 질문 23개 별도평가",
            work: "근거 확인, 재검색, 답변 거절, CRAG 자기교정",
          },
        ],
      },
    ],
    links: [
      { label: "데모", href: "https://www.clickme.co.kr" },
      { label: "GitHub", href: "https://github.com/cclickstudio/click-me" },
    ],
  },
];

const PERSONAL_PROJECTS = PROJECTS.filter((p) => p.category === "personal");
const TEAM_PROJECTS = PROJECTS.filter((p) => p.category === "team");

const SUB_PROJECTS: SubProject[] = [
  {
    id: "fom",
    title: "FOM",
    description:
      "댄스 동작 분석 AI 평가 플랫폼 (팀 6인 · 2026.05)\n비전 모델 기반 영상 키포인트 추출 → 레퍼런스 대비 동작 채점 End-to-End 파이프라인 담당",
    href: "https://github.com/Hi-Six/FOM",
    techStack: ["FastAPI", "MediaPipe", "YOLO11", "librosa", "Flutter"],
    icon: Activity,
  },
  {
    id: "aifix",
    title: "AIFIX",
    description:
      "ESG 공급망 리스크 관리·PCF 산정 지원 시스템 (삼정KPMG · 4인 · 2026.03–04)\n백그라운드 워커 비동기 알림 파이프라인, WebSocket 실시간 브로드캐스트·Slack/Gmail API 연동 담당",
    techStack: ["WebSocket", "Slack API", "Gmail API", "Vercel"],
    icon: Leaf,
  },
  {
    id: "keyword",
    title: "KeyWord",
    description:
      "약속의 시작부터 끝까지, 이용자 일정을 도와주는 서비스 (팀 5인 · 2023.09–10)\nElasticSearch 기반 고성능 회원 검색 기능 담당, 원격 협업 프로젝트",
    href: "https://github.com/ZB-Keyword",
    previewImage:
      "https://github.com/ZB-Keyword/.github/assets/130157565/45b3001f-1705-4d93-acf4-4b979b218186",
    techStack: ["Java", "Spring", "OAuth 2.0", "ElasticSearch"],
  },
];

const modalLabelStyle: React.CSSProperties = {
  fontSize: "0.625rem",
  color: "rgba(220,228,245,0.78)",
  letterSpacing: "0.14em",
  textTransform: "uppercase",
  marginBottom: "0.75rem",
};

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
        className="w-full sm:max-w-[620px] max-h-[92vh] overflow-y-auto"
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
          {project.links && project.links.length > 0 && (
            <div className="flex flex-wrap gap-2.5">
              {project.links.map((l) => (
                <a
                  key={l.href}
                  href={l.href}
                  target={l.href.startsWith("/") ? undefined : "_blank"}
                  rel={l.href.startsWith("/") ? undefined : "noopener noreferrer"}
                  className="inline-flex items-center gap-1.5 rounded-lg transition-all"
                  style={{
                    padding: "8px 14px",
                    fontSize: "0.8125rem",
                    fontWeight: 600,
                    color: "#8ef0d7",
                    background: "rgba(142,240,215,0.07)",
                    border: "1px solid rgba(142,240,215,0.18)",
                  }}
                >
                  {l.label}
                  <ExternalLink size={12} />
                </a>
              ))}
            </div>
          )}
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
            <p style={modalLabelStyle}>주요 구현</p>
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
            <p style={modalLabelStyle}>문제 해결</p>
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
          {project.evalTable && (
            <div>
              <p style={modalLabelStyle}>RAG 품질 평가 — Ragas · 골든셋 정량 평가</p>
              <div
                className="overflow-x-auto rounded-lg"
                style={{ border: "1px solid rgba(142,240,215,0.1)" }}
              >
                <table
                  className="w-full"
                  style={{ borderCollapse: "collapse", fontSize: "0.75rem", minWidth: 480 }}
                >
                  <tbody>
                    {project.evalTable.map((tier) => (
                      <Fragment key={tier.tier}>
                        <tr>
                          <td
                            colSpan={3}
                            style={{
                              padding: "7px 10px",
                              fontSize: "0.6875rem",
                              fontWeight: 700,
                              letterSpacing: "0.08em",
                              textTransform: "uppercase",
                              color: "#8ef0d7",
                              background: "rgba(142,240,215,0.06)",
                            }}
                          >
                            {tier.tier}
                          </td>
                        </tr>
                        {tier.rows.map((r) => (
                          <tr
                            key={r.metric}
                            style={{ borderTop: "1px solid rgba(255,255,255,0.08)" }}
                          >
                            <td
                              style={{
                                padding: "8px 10px",
                                color: "rgba(220,228,245,0.92)",
                                fontWeight: 600,
                                whiteSpace: "nowrap",
                                verticalAlign: "top",
                              }}
                            >
                              {r.metric}
                            </td>
                            <td
                              style={{
                                padding: "8px 10px",
                                fontFamily: "'JetBrains Mono', monospace",
                                color: "#8ef0d7",
                                verticalAlign: "top",
                              }}
                            >
                              {r.change}
                            </td>
                            <td
                              style={{
                                padding: "8px 10px",
                                color: "rgba(220,228,245,0.75)",
                                lineHeight: 1.55,
                                verticalAlign: "top",
                              }}
                            >
                              {r.work}
                            </td>
                          </tr>
                        ))}
                      </Fragment>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
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

const rowHoverProps = {
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

/** 메인 프로젝트: 클릭 시 상세 모달 (데모·GitHub 링크는 모달 내부 버튼) */
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
  const hasPreview = project.previewUrl && project.previewUrl.startsWith("/");

  return (
    <motion.article
      ref={ref}
      initial={{ opacity: 0, y: 12 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.4, delay: index * 0.08 }}
      className="group flex gap-5 sm:gap-6 items-start rounded-xl -mx-4 sm:-mx-5 px-4 sm:px-5 py-4 transition-all duration-300"
      style={{ border: "1px solid transparent", borderBottom: "1px solid rgba(255,255,255,0.32)" }}
      onClick={onOpen}
      onKeyDown={(e) => e.key === "Enter" && onOpen()}
      role="button"
      tabIndex={0}
      {...rowHoverProps}
    >
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
              src={project.previewUrl}
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
        {project.links && project.links.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-2.5">
            {project.links.map((l) => (
              <a
                key={l.href}
                href={l.href}
                target={l.href.startsWith("/") ? undefined : "_blank"}
                rel={l.href.startsWith("/") ? undefined : "noopener noreferrer"}
                onClick={(e) => e.stopPropagation()}
                className="inline-flex items-center gap-1 transition-colors hover:!text-[#8ef0d7]"
                style={{
                  fontSize: "0.875rem",
                  fontWeight: 600,
                  color: "rgba(142,240,215,0.75)",
                  textDecoration: "none",
                }}
              >
                {l.label}
                <ExternalLink size={12} className="shrink-0" />
              </a>
            ))}
          </div>
        )}
      </div>
    </motion.article>
  );
}

/** 서브 프로젝트: 미리보기·글자 크기·태그 스타일 통일, 링크가 있으면 클릭 시 이동 */
function SubProjectRow({ sub, index }: { sub: SubProject; index: number }) {
  const ref = useRef<HTMLElement>(null);
  const inView = useInView(ref, { once: true, margin: "-40px" });
  const SubIcon = sub.icon ?? Key;

  const inner = (
    <>
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
            <SubIcon size={44} className="shrink-0" style={{ color: "rgba(142,240,215,0.4)" }} />
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
          {sub.href && (
            <ExternalLink size={14} style={{ color: "rgba(142,240,215,0.5)" }} className="shrink-0" />
          )}
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
    </>
  );

  const motionProps = {
    initial: { opacity: 0, y: 12 },
    animate: inView ? { opacity: 1, y: 0 } : {},
    transition: { duration: 0.4, delay: index * 0.08 },
    className:
      "group flex gap-5 sm:gap-6 items-start rounded-xl -mx-4 sm:-mx-5 px-4 sm:px-5 py-4 transition-all duration-300",
    style: {
      border: "1px solid transparent",
      borderBottom: "1px solid rgba(255,255,255,0.32)",
      textDecoration: "none",
    },
    ...rowHoverProps,
  };

  if (sub.href) {
    return (
      <motion.a
        ref={ref as React.RefObject<HTMLAnchorElement>}
        href={sub.href}
        target="_blank"
        rel="noopener noreferrer"
        {...motionProps}
      >
        {inner}
      </motion.a>
    );
  }
  return (
    <motion.div ref={ref as React.RefObject<HTMLDivElement>} {...motionProps}>
      {inner}
    </motion.div>
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
      {/* 이력서 순서와 동일: Team(ClickMe) → Personal(HR Insight) → Other */}
      <div className="mb-10">
        <p style={blockLabelStyle}>Team Project</p>
        <div className="space-y-0">
          {TEAM_PROJECTS.map((p, i) => (
            <MainProjectRow key={p.id} project={p} index={i} onOpen={() => setActive(p)} />
          ))}
        </div>
      </div>
      <div className="mb-10">
        <p style={blockLabelStyle}>Personal Project</p>
        <div className="space-y-0">
          {PERSONAL_PROJECTS.map((p, i) => (
            <MainProjectRow key={p.id} project={p} index={i} onOpen={() => setActive(p)} />
          ))}
        </div>
      </div>
      {/* Other Project — FOM · AIFIX · KeyWord */}
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
