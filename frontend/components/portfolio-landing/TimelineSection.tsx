"use client";

import { useRef } from "react";
import { motion, useInView } from "framer-motion";
import { SectionHeader } from "./SectionHeader";
import { renderEmphasis } from "./emphasis";

const ITEMS = [
  { period: "2026.05 — 2026.07", title: "하이미디어 심화 생성형 AI 과정", org: "심화 생성형 AI 활용 인재 양성 과정", desc: "AI 모델 운영을 위한 하네스 시스템 설계와 AI 서비스 구현. 팀 프로젝트 **ClickMe**(광고 운영 플랫폼)·**FOM**(댄스 동작 분석) 진행 — **LangGraph 딥에이전트, Ragas 기반 RAG 품질 평가**에 집중.", current: true },
  { period: "2025.09 — 2026.04", title: "삼정KPMG AX Academy 3기", org: "ESG 데이터 활용 AX Academy with AI Agent", desc: "AI 풀스택 개발, 클라우드 인프라, 데이터 기반 플랫폼 구축 역량 학습. 개인 프로젝트 **HR Insight(Success DNA)**와 ESG 공급망 리스크 관리 시스템(AIFIX) 개발.", current: false },
  { period: "2023.04 — 2023.10", title: "제로베이스 백엔드 스쿨 15기", org: "온라인 부트캠프 · 원격 협업 경험", desc: "Spring 기반 백엔드 개발 및 REST API 설계·구현. 팀 프로젝트 KeyWord 원격 협업 — **ElasticSearch 기반 회원 검색** 기능 담당.", current: false },
  { period: "2022.09 — 2022.12", title: "의료 IT / 인터페이스팀", org: "(주)화산시스템 · 대학병원 LIS 전문 기업", desc: "진단검사의학과 LIS 시스템 유지보수·운영 지원. 의료 장비-LIS 데이터 인터페이스 연동 점검 및 **장애 대응**, 로그 분석·네트워크 점검·백업 관리.", current: false },
  { period: "2022.03 — 2022.09", title: "응용 SW 엔지니어링(Java) 수료", org: "대구중앙직업전문학교", desc: "Java/JSP 기반 웹 애플리케이션 및 통합 시스템 개발 학습. 개발자로의 전환 시작.", current: false },
  { period: "2018 — 2020", title: "한국 YMCA 국제개발협력팀 / 대구 YMCA 청소년 쉼터", org: "비개발 경력 · 소통과 리더십의 기반", desc: "국내외 다양한 대상자와의 소통으로 상황에 맞는 커뮤니케이션·조율 능력 체득. 현장 중심 문제 해결 경험으로 팀 협업과 조직 목표 달성에 기여.", current: false },
  { period: "2017 졸업", title: "영남대학교 중어중문학과", org: "학력", desc: "재학 중 필리핀 해외 자원봉사 6개월 등 다양한 현장 소통 경험.", current: false },
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
              <div className="sm:w-[11rem] sm:min-w-[11rem] shrink-0 mb-2 sm:mb-0">
                <span
                  style={{
                    fontFamily: '"Segoe UI", system-ui, -apple-system, BlinkMacSystemFont, sans-serif',
                    fontSize: "1.0625rem",
                    fontWeight: 500,
                    color: item.current ? "rgba(142,240,215,0.9)" : "rgba(220,228,245,0.78)",
                    lineHeight: 1.5,
                    letterSpacing: "0.04em",
                    whiteSpace: "nowrap",
                  }}
                >
                  {item.period}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2.5 mb-0.5 flex-wrap">
                  <h3
                    style={{
                      fontSize: "1.2rem",
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
                <p style={{ fontSize: "1.0625rem", color: "rgba(220,228,245,0.85)", marginBottom: "0.6rem" }}>{item.org}</p>
                <p style={{ fontSize: "1.0625rem", color: "rgba(220,228,245,0.82)", lineHeight: 1.78 }}>{renderEmphasis(item.desc)}</p>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
