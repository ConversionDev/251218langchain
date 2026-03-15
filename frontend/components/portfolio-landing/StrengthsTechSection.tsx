"use client";

import { useRef } from "react";
import { motion, useInView } from "framer-motion";
import { Brain, Database, Code2, Cloud, Server, Cpu } from "lucide-react";
import { SectionHeader } from "./SectionHeader";

/** 이력서 PDF(components/portfolio/이력서.pdf) 좌측 스킬란과 동일 */
const TECH = [
  {
    label: "Core Language",
    icon: Cpu,
    items: ["Java", "Python"],
  },
  {
    label: "Frontend",
    icon: Code2,
    items: ["Next.js", "React", "TypeScript", "Tailwind CSS", "Framer", "PWA", "Potrace"],
  },
  {
    label: "Backend",
    icon: Database,
    items: ["FastAPI", "SQLAlchemy", "Alembic", "Spring Boot", "JPA"],
  },
  {
    label: "AI / ML / DL",
    icon: Brain,
    items: ["LangChain", "LangGraph", "Transformers", "BGE-M3", "Llama", "EXAONE"],
  },
  {
    label: "Data Base",
    icon: Cloud,
    items: ["Postgre(Neon DB)", "FAISS", "Redis(Upstash)"],
  },
  {
    label: "DevOps",
    icon: Server,
    items: ["Docker", "Vercel", "GitHub Actions", "CI/CD", "AWS", "NGINX"],
  },
];

export function StrengthsTechSection() {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: "-60px" });

  return (
    <section
      id="strengths"
      className="pt-10 pb-28 scroll-mt-14 md:scroll-mt-0"
    >
      <SectionHeader num="03" label="Tech Stack" />
      <div ref={ref} className="space-y-1">
        {TECH.map((cat, i) => (
          <motion.div
            key={cat.label}
            initial={{ opacity: 0, y: 12 }}
            animate={inView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.5, delay: i * 0.08 }}
            className="group -mx-4 sm:-mx-5 rounded-xl px-4 sm:px-5 py-5 transition-all duration-300"
            style={{ border: "1px solid transparent" }}
            onMouseEnter={(e) => {
              const el = e.currentTarget as HTMLDivElement;
              el.style.background = "rgba(142,240,215,0.02)";
              el.style.borderColor = "rgba(142,240,215,0.06)";
            }}
            onMouseLeave={(e) => {
              const el = e.currentTarget as HTMLDivElement;
              el.style.background = "transparent";
              el.style.borderColor = "transparent";
            }}
          >
            <div className="flex items-center gap-2 mb-3.5">
              <cat.icon size={20} style={{ color: "rgba(142,240,215,0.35)" }} />
              <span
                style={{
                  fontSize: "0.875rem",
                  fontWeight: 600,
                  color: "rgba(220,228,245,0.82)",
                  letterSpacing: "0.15em",
                  textTransform: "uppercase",
                }}
              >
                {cat.label}
              </span>
            </div>
            <div className="flex flex-wrap gap-2">
              {cat.items.map((tech) => (
                <span
                  key={tech}
                  style={{
                    fontSize: "1.0625rem",
                    color: "rgba(142,240,215,0.58)",
                    background: "rgba(142,240,215,0.045)",
                    border: "1px solid rgba(142,240,215,0.08)",
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
                    el.style.color = "rgba(142,240,215,0.58)";
                    el.style.background = "rgba(142,240,215,0.045)";
                    el.style.borderColor = "rgba(142,240,215,0.08)";
                  }}
                >
                  {tech}
                </span>
              ))}
            </div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
