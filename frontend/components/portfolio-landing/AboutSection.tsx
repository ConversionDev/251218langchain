"use client";

import { useRef, useState } from "react";
import { motion, useInView } from "framer-motion";
import { ChevronDown } from "lucide-react";
import { SectionHeader } from "./SectionHeader";
import { RagEvalTable, RAG_EVAL_TIERS } from "./RagEvalTable";
import { renderEmphasis } from "./emphasis";

const BIO = [
  {
    text: "**sLLM 파인튜닝부터 RAG 파이프라인·AI Agent·실서비스 배포까지**, AI 시스템 전 계층을 직접 구현합니다. 제한된 인프라에서 **고성능 모델을 양자화·최적화해 CPU 환경에 서빙**하는 등, 비용과 성능을 동시에 고려한 실용적 설계에 강점이 있습니다.",
    color: "rgba(220,228,245,0.95)",
  },
  {
    text: "비영리 NGO 활동과 해외 자원봉사에서 다양한 사람들과 소통해온 경험을 바탕으로, 팀 안에서 기술적 맥락을 공유하고 함께 성장하는 것을 가장 중요하게 생각합니다.",
    color: "rgba(220,228,245,0.88)",
  },
  {
    text: "비전공(중어중문학)에서 자기주도적으로 개발에 전환했고, 의료 IT와 백엔드 개발로 견고한 기본기를 쌓은 뒤 현재는 **AI/ML 엔지니어링에 집중**하며 실전 프로젝트에서 성과를 만들고 있습니다.",
    color: "rgba(220,228,245,0.82)",
  },
];

/** 출처: ClickMe Ragas 골든셋 평가 · HR Insight 실측 — 이력서·발표자료와 동일 수치 */
const STATS = [
  { v: "1.000", l: "RAG Hit Rate@K" },
  { v: "0.705→0.938", l: "MRR (리랭커 도입)" },
  { v: "0.51→1.00", l: "Faithfulness" },
  { v: "2.5~3×", l: "LLM 학습 속도" },
  { v: "11.8만", l: "지식베이스 임베딩" },
];

const TRAITS = [
  { label: "성능 최적화", desc: "측정 가능한 개선을 만듭니다" },
  { label: "끈기 있는 몰입", desc: "본질에 도달할 때까지 파고듭니다" },
  { label: "협업 지향", desc: "함께 성장하는 즐거움" },
];

const INTERESTS = [
  "LLM Fine-tuning (QLoRA)",
  "Agentic RAG",
  "LLM Evaluation (Ragas)",
  "Multi-Agent System",
  "Performance Optimization",
  "Computer Vision",
];

export function AboutSection() {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: "-60px" });
  const [evalOpen, setEvalOpen] = useState(false);

  return (
    <section
      id="about"
      className="pt-12 md:pt-24 lg:pt-28 pb-28 scroll-mt-40 md:scroll-mt-0 overflow-visible"
    >
      <SectionHeader num="01" label="About" />
      <div ref={ref} className="w-full">
        <div className="space-y-5 mb-8">
          {BIO.map(({ text, color }, i) => (
            <motion.p
              key={i}
              initial={{ opacity: 0, y: 12 }}
              animate={inView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.55, delay: i * 0.1 }}
              style={{
                fontSize: "1.2rem",
                lineHeight: 1.85,
                color,
                fontWeight: 400,
              }}
            >
              {renderEmphasis(text)}
            </motion.p>
          ))}
        </div>
        {/* About 섹션 실선 통일: 콘텐츠 너비 100% 기준 좌우 맞춤 */}
        <div
          role="presentation"
          className="w-full"
          style={{ height: 1, background: "rgba(255,255,255,0.32)" }}
        />
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.55, delay: 0.3 }}
          className="w-full flex flex-wrap gap-8 sm:gap-10 py-6 mb-6"
        >
          {STATS.map((s) => (
            <div key={s.l}>
              <div
                style={{
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: "1.5rem",
                  fontWeight: 700,
                  color: "#8ef0d7",
                  letterSpacing: "-0.01em",
                }}
              >
                {s.v}
              </div>
              <div
                style={{
                  fontSize: "0.875rem",
                  color: "rgba(220,228,245,0.75)",
                  marginTop: 4,
                  letterSpacing: "0.04em",
                }}
              >
                {s.l}
              </div>
            </div>
          ))}
        </motion.div>
        {/* ClickMe RAG 품질 평가 상세 — 스탯 수치의 출처 표 (접이식) */}
        <div className="mb-6">
          <button
            type="button"
            onClick={() => setEvalOpen((v) => !v)}
            className="inline-flex items-center gap-2 rounded-lg transition-all"
            style={{
              padding: "8px 14px",
              fontSize: "0.875rem",
              fontWeight: 600,
              color: "rgba(142,240,215,0.75)",
              background: "rgba(142,240,215,0.04)",
              border: "1px solid rgba(142,240,215,0.12)",
              cursor: "pointer",
            }}
          >
            ClickMe RAG 품질 평가 상세 — Ragas · 골든셋
            <ChevronDown
              size={14}
              className="transition-transform duration-300"
              style={{ transform: evalOpen ? "rotate(180deg)" : "none" }}
            />
          </button>
          {evalOpen && (
            <motion.div
              initial={{ opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              className="mt-3"
            >
              <RagEvalTable tiers={RAG_EVAL_TIERS} />
            </motion.div>
          )}
        </div>
        {/* About 섹션 실선 통일 */}
        <div
          role="presentation"
          className="mb-10 w-full"
          style={{ height: 1, background: "rgba(255,255,255,0.32)" }}
        />
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.55, delay: 0.38 }}
          className="flex flex-col sm:flex-row gap-2 sm:gap-2.5 mb-12"
        >
          {TRAITS.map(({ label, desc }) => (
            <div
              key={label}
              className="flex-1 min-w-0 sm:min-w-[220px] rounded-lg px-3 py-4 sm:px-3.5 sm:py-5"
              style={{
                background: "rgba(142,240,215,0.025)",
                border: "1px solid rgba(142,240,215,0.07)",
              }}
            >
              <p
                style={{
                  fontSize: "1.0625rem",
                  fontWeight: 500,
                  color: "rgba(220,228,245,0.92)",
                  marginBottom: 3,
                }}
              >
                {label}
              </p>
              <p
                style={{
                  fontSize: "0.9375rem",
                  color: "rgba(220,228,245,0.78)",
                  lineHeight: 1.5,
                }}
              >
                {desc}
              </p>
            </div>
          ))}
        </motion.div>
        <motion.div
          initial={{ opacity: 0 }}
          animate={inView ? { opacity: 1 } : {}}
          transition={{ duration: 0.55, delay: 0.48 }}
          className="mt-2"
        >
          <p
            style={{
              fontSize: "0.875rem",
              color: "rgba(220,228,245,0.7)",
              letterSpacing: "0.15em",
              textTransform: "uppercase",
              marginBottom: "0.75rem",
            }}
          >
            관심 영역
          </p>
          <div className="flex flex-wrap gap-x-2 gap-y-3">
            {INTERESTS.map((tag) => (
              <span
                key={tag}
                style={{
                  fontSize: "1rem",
                  color: "rgba(142,240,215,0.6)",
                  background: "rgba(142,240,215,0.05)",
                  border: "1px solid rgba(142,240,215,0.1)",
                  padding: "4px 13px",
                  borderRadius: 999,
                  fontWeight: 500,
                  transition: "all 0.2s",
                  cursor: "default",
                }}
                onMouseEnter={(e) => {
                  const el = e.target as HTMLElement;
                  el.style.color = "#8ef0d7";
                  el.style.background = "rgba(142,240,215,0.1)";
                  el.style.borderColor = "rgba(142,240,215,0.2)";
                }}
                onMouseLeave={(e) => {
                  const el = e.target as HTMLElement;
                  el.style.color = "rgba(142,240,215,0.6)";
                  el.style.background = "rgba(142,240,215,0.05)";
                  el.style.borderColor = "rgba(142,240,215,0.1)";
                }}
              >
                {tag}
              </span>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
}
