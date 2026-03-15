"use client";

import { useRef } from "react";
import { motion, useInView } from "framer-motion";
import { ExternalLink } from "lucide-react";
import { SectionHeader } from "./SectionHeader";

const ITEMS = [
  { period: "2025.09 — Present", title: "AI Developer", org: "AI/ML 프로젝트 집중", desc: "OCR & RAG 기반 Intelligent HR Agent, ESG Supply Chain Platform 등 성능 중심의 AI 프로젝트 설계 및 개발. 추론 최적화, 파이프라인 아키텍처, 프롬프트 엔지니어링에 집중.", tags: ["LangChain", "GPT-4", "FastAPI", "RAG"], link: "", current: true },
  { period: "2023.10 — 2024.01", title: "제로베이스 백엔드 스쿨 12기", org: "온라인 부트캠프 · 원격 협업 경험", desc: "백엔드 심화 학습. 팀 프로젝트 KeyWord 원격 협업. 소셜 로그인 및 ElasticSearch 기반 회원 검색 기능 담당.", tags: ["Django", "ElasticSearch"], link: "https://github.com/ZB-Keyword", current: false },
  { period: "2022.09 — 2022.12", title: "의료 IT / Backend", org: "(주)화산시스템 · 인터페이스 팀", desc: "병원 LIS 시스템 간 시리얼 통신 인터페이스 데이터 전송·검증 담당. 전국 병원 출장 LOG 분석 및 네트워크 진단, 사용자 교육 수행.", tags: ["Visual Basic 6.0"], link: "", current: false },
  { period: "2022.02 — 2022.09", title: "응용 SW 엔지니어링 수료", org: "대구 중앙 직업전문학교 · Java Class", desc: "Java와 Spring을 활용한 통합 시스템 구축 과정. 개발자로의 전환 시작.", tags: ["Java", "Spring"], link: "", current: false },
  { period: "2013 — 2020", title: "영남대학교 & 비개발 경험", org: "중어중문학과 · 소통과 리더십의 기반", desc: "필리핀 해외 자원봉사 6개월, 대구 YMCA 청소년 쉼터, 한국 YMCA 국제개발협력팀 근무.", tags: [], link: "", current: false },
];

export function TimelineSection() {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: "-60px" });

  return (
    <section id="timeline" className="pt-10 pb-28 scroll-mt-14 md:scroll-mt-0">
      <SectionHeader num="04" label="Career" />
      <div ref={ref} className="space-y-1">
        {ITEMS.map((item, i) => (
          <motion.div
            key={item.period}
            initial={{ opacity: 0, y: 14 }}
            animate={inView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.5, delay: i * 0.09 }}
            className="group -mx-4 sm:-mx-5 rounded-xl px-4 sm:px-5 py-5 transition-all duration-300"
            style={{ border: "1px solid transparent" }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLDivElement).style.background = "rgba(142,240,215,0.02)";
              (e.currentTarget as HTMLDivElement).style.borderColor = "rgba(142,240,215,0.06)";
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLDivElement).style.background = "transparent";
              (e.currentTarget as HTMLDivElement).style.borderColor = "transparent";
            }}
          >
            <div className="sm:flex sm:gap-7">
              <div className="sm:w-[148px] shrink-0 mb-2 sm:mb-0">
                <span
                  style={{
                    fontFamily: "'JetBrains Mono', monospace",
                    fontSize: "0.75rem",
                    color: item.current ? "rgba(142,240,215,0.9)" : "rgba(220,228,245,0.65)",
                    lineHeight: 1.5,
                    letterSpacing: "0.01em",
                  }}
                >
                  {item.period}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2.5 mb-0.5 flex-wrap">
                  <h3
                    style={{
                      fontSize: "1.0625rem",
                      fontWeight: 600,
                      color: item.current ? "#ccd6f6" : "rgba(220,228,245,0.9)",
                      lineHeight: 1.3,
                    }}
                    className="group-hover:!text-[#ccd6f6]"
                  >
                    {item.title}
                  </h3>
                  {item.current && (
                    <span
                      style={{
                        fontSize: "0.6rem",
                        color: "rgba(142,240,215,0.8)",
                        background: "rgba(142,240,215,0.08)",
                        border: "1px solid rgba(142,240,215,0.18)",
                        padding: "2px 8px",
                        borderRadius: 999,
                        fontWeight: 600,
                        letterSpacing: "0.08em",
                      }}
                    >
                      CURRENT
                    </span>
                  )}
                </div>
                <p style={{ fontSize: "0.9375rem", color: "rgba(220,228,245,0.85)", marginBottom: "0.6rem" }}>{item.org}</p>
                <p style={{ fontSize: "0.9375rem", color: "rgba(220,228,245,0.82)", lineHeight: 1.78 }}>{item.desc}</p>
                {(item.tags.length > 0 || item.link) && (
                  <div className="flex flex-wrap items-center gap-2 mt-3">
                    {item.tags.map((t) => (
                      <span
                        key={t}
                        style={{
                          fontFamily: "'JetBrains Mono', monospace",
                          fontSize: "0.75rem",
                          color: "rgba(142,240,215,0.5)",
                          background: "rgba(142,240,215,0.04)",
                          border: "1px solid rgba(142,240,215,0.08)",
                          padding: "2px 9px",
                          borderRadius: 999,
                        }}
                      >
                        {t}
                      </span>
                    ))}
                    {item.link && (
                      <a
                        href={item.link}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="flex items-center gap-1"
                        style={{ fontSize: "0.8125rem", color: "rgba(220,228,245,0.75)" }}
                      >
                        <ExternalLink size={11} /> GitHub
                      </a>
                    )}
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
