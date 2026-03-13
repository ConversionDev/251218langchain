"use client";

import { useRef } from "react";
import { motion, useInView } from "framer-motion";
import { SectionHeader } from "./SectionHeader";

const BIO = [
  {
    text: "더 빠르고, 더 효율적인 방법을 찾는 과정이 즐겁습니다. 백엔드에서 AI까지 풀스택으로 시스템을 설계하며, 성능의 병목을 추적하고 해결하는 데 깊이 몰입합니다.",
    color: "rgba(220,228,245,0.95)",
  },
  {
    text: "비영리 NGO 활동과 해외 자원봉사에서 다양한 사람들과 소통해온 경험을 바탕으로, 팀 안에서 기술적 맥락을 공유하고 함께 성장하는 것을 가장 중요하게 생각합니다.",
    color: "rgba(220,228,245,0.88)",
  },
  {
    text: "비전공(중어중문학)에서 자기주도적으로 개발에 전환했고, 의료 IT와 백엔드 개발로 견고한 기본기를 쌓은 뒤 현재는 AI/ML 엔지니어링에 집중하며 실전 프로젝트에서 성과를 만들고 있습니다.",
    color: "rgba(220,228,245,0.82)",
  },
];

const STATS = [
  { v: "95%", l: "OCR 정확도" },
  { v: "40%↑", l: "추론 속도" },
  { v: "60%↓", l: "비용 절감" },
];

const TRAITS = [
  { label: "성능 최적화", desc: "측정 가능한 개선을 만듭니다" },
  { label: "끈기 있는 몰입", desc: "본질에 도달할 때까지 파고듭니다" },
  { label: "협업 지향", desc: "함께 성장하는 즐거움" },
];

const INTERESTS = [
  "LLM Engineering",
  "RAG Architecture",
  "OCR Pipeline",
  "Performance Optimization",
  "Prompt Engineering",
  "Multi-Agent System",
];

export function AboutSection() {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: "-60px" });

  return (
    <section
      id="about"
      className="pt-12 md:pt-24 lg:pt-28 pb-28 scroll-mt-14 md:scroll-mt-0"
    >
      <SectionHeader num="01" label="About" />
      <div ref={ref}>
        <div className="space-y-5 mb-8">
          {BIO.map(({ text, color }, i) => (
            <motion.p
              key={i}
              initial={{ opacity: 0, y: 12 }}
              animate={inView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.55, delay: i * 0.1 }}
              style={{
                fontSize: "0.9375rem",
                lineHeight: 1.85,
                color,
                fontWeight: 400,
              }}
            >
              {text}
            </motion.p>
          ))}
        </div>
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.55, delay: 0.3 }}
          className="flex gap-10 py-6 mb-8"
          style={{
            borderTop: "1px solid rgba(142,240,215,0.07)",
            borderBottom: "1px solid rgba(142,240,215,0.07)",
          }}
        >
          {STATS.map((s) => (
            <div key={s.l}>
              <div
                style={{
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: "1.25rem",
                  fontWeight: 700,
                  color: "#8ef0d7",
                  letterSpacing: "-0.01em",
                }}
              >
                {s.v}
              </div>
              <div
                style={{
                  fontSize: "0.625rem",
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
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.55, delay: 0.38 }}
          className="flex flex-col sm:flex-row gap-3 mb-10"
        >
          {TRAITS.map(({ label, desc }) => (
            <div
              key={label}
              className="flex-1 rounded-lg px-4 py-3"
              style={{
                background: "rgba(142,240,215,0.025)",
                border: "1px solid rgba(142,240,215,0.07)",
              }}
            >
              <p
                style={{
                  fontSize: "0.8125rem",
                  fontWeight: 500,
                  color: "rgba(220,228,245,0.92)",
                  marginBottom: 3,
                }}
              >
                {label}
              </p>
              <p
                style={{
                  fontSize: "0.6875rem",
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
        >
          <p
            style={{
              fontSize: "0.625rem",
              color: "rgba(220,228,245,0.7)",
              letterSpacing: "0.15em",
              textTransform: "uppercase",
              marginBottom: "0.75rem",
            }}
          >
            관심 영역
          </p>
          <div className="flex flex-wrap gap-2">
            {INTERESTS.map((tag) => (
              <span
                key={tag}
                style={{
                  fontSize: "0.75rem",
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
