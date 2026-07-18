"use client";

import { useRef, useState } from "react";
import { motion, useInView } from "framer-motion";
import {
  Mail,
  PenSquare,
  ArrowUpRight,
  Copy,
  Check,
} from "lucide-react";
import { SectionHeader } from "./SectionHeader";

function GitHubLogo({ size = 18 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" aria-hidden>
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.166 6.839 9.489.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.604-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.464-1.11-1.464-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.578 9.578 0 0112 6.836c.85.004 1.705.114 2.504.336 1.909-1.294 2.747-1.025 2.747-1.025.546 1.376.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.578.688.48C19.138 20.163 22 16.418 22 12c0-5.523-4.477-10-10-10z"
      />
    </svg>
  );
}

const LINKS = [
  { type: "github" as const, label: "GitHub", href: "https://github.com/ConversionDev", download: false },
  { type: "icon" as const, icon: PenSquare, label: "Blog", href: "https://kku1031.tistory.com", download: false },
];

export function ContactSection() {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: "-60px" });
  const [copied, setCopied] = useState(false);

  const copy = () => {
    navigator.clipboard.writeText("rkdrudrn1031@gmail.com");
    setCopied(true);
    setTimeout(() => setCopied(false), 2200);
  };

  return (
    <section
      id="contact"
      ref={ref}
      className="pt-10 pb-28 scroll-mt-14 md:scroll-mt-0"
    >
      <SectionHeader num="05" label="Contact" />
      <div className="max-w-[400px]">
        <motion.p
          initial={{ opacity: 0, y: 12 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.55 }}
          style={{
            fontSize: "1.2rem",
            color: "rgba(220,228,245,0.85)",
            lineHeight: 1.85,
            marginBottom: "2rem",
          }}
        >
          성능 최적화, AI 시스템 설계, 또는 흥미로운 기술적 도전이 있다면
          언제든 연락 주세요.
        </motion.p>
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.55, delay: 0.1 }}
          className="flex flex-wrap items-center gap-3 mb-10"
        >
          <a
            href="mailto:rkdrudrn1031@gmail.com"
            className="group inline-flex items-center gap-3 rounded-xl transition-all duration-300"
            style={{
              padding: "14px 22px",
              background: "rgba(142,240,215,0.06)",
              border: "1px solid rgba(142,240,215,0.15)",
              color: "#8ef0d7",
              fontSize: "1.2rem",
              fontWeight: 500,
            }}
            onMouseEnter={(e) => {
              const el = e.currentTarget as HTMLAnchorElement;
              el.style.background = "rgba(142,240,215,0.1)";
              el.style.borderColor = "rgba(142,240,215,0.28)";
            }}
            onMouseLeave={(e) => {
              const el = e.currentTarget as HTMLAnchorElement;
              el.style.background = "rgba(142,240,215,0.06)";
              el.style.borderColor = "rgba(142,240,215,0.15)";
            }}
          >
            <Mail size={16} />
            rkdrudrn1031@gmail.com
            <ArrowUpRight
              size={14}
              className="opacity-55 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform duration-300"
            />
          </a>
          <button
            type="button"
            onClick={(e) => {
              e.preventDefault();
              copy();
            }}
            className="inline-flex items-center gap-1.5 rounded-lg transition-all duration-300 shrink-0"
            style={{
              padding: "10px 14px",
              fontSize: "0.9375rem",
              fontWeight: 500,
              color: copied ? "rgba(142,240,215,0.8)" : "rgba(220,228,245,0.7)",
              background: "rgba(255,255,255,0.04)",
              border: "1px solid rgba(255,255,255,0.1)",
            }}
            onMouseEnter={(e) => {
              if (!copied) {
                (e.currentTarget as HTMLButtonElement).style.color = "rgba(220,228,245,0.95)";
                (e.currentTarget as HTMLButtonElement).style.borderColor = "rgba(255,255,255,0.18)";
              }
            }}
            onMouseLeave={(e) => {
              if (!copied) {
                (e.currentTarget as HTMLButtonElement).style.color = "rgba(220,228,245,0.7)";
                (e.currentTarget as HTMLButtonElement).style.borderColor = "rgba(255,255,255,0.1)";
              }
            }}
          >
            {copied ? <Check size={14} /> : <Copy size={14} />}
            {copied ? "복사됐어요!" : "주소 복사"}
          </button>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.55, delay: 0.26 }}
          className="flex flex-wrap gap-2.5"
        >
          {LINKS.map((item) => (
            <a
              key={item.label}
              href={item.href}
              download={item.download || undefined}
              target={!item.download ? "_blank" : undefined}
              rel={!item.download ? "noopener noreferrer" : undefined}
              className="flex items-center gap-2.5 rounded-lg transition-all duration-300"
              style={{
                fontSize: "1.0625rem",
                fontWeight: 500,
                color: "rgba(220,228,245,0.82)",
                background: "rgba(142,240,215,0.02)",
                border: "1px solid rgba(142,240,215,0.07)",
                padding: "10px 18px",
              }}
              onMouseEnter={(e) => {
                const el = e.currentTarget as HTMLAnchorElement;
                el.style.color = "#8ef0d7";
                el.style.borderColor = "rgba(142,240,215,0.18)";
                el.style.background = "rgba(142,240,215,0.06)";
              }}
              onMouseLeave={(e) => {
                const el = e.currentTarget as HTMLAnchorElement;
                el.style.color = "rgba(220,228,245,0.82)";
                el.style.borderColor = "rgba(142,240,215,0.07)";
                el.style.background = "rgba(142,240,215,0.02)";
              }}
            >
              {item.type === "github" ? (
                <GitHubLogo size={20} />
              ) : (
                <item.icon size={20} />
              )}
              {item.label}
            </a>
          ))}
        </motion.div>
        <motion.div
          initial={{ opacity: 0 }}
          animate={inView ? { opacity: 1 } : {}}
          transition={{ duration: 0.6, delay: 0.5 }}
          className="mt-20 pt-7"
          style={{ borderTop: "1px solid rgba(255,255,255,0.32)" }}
        >
          <p
            style={{
              fontSize: "0.9375rem",
              color: "rgba(220,228,245,0.6)",
              letterSpacing: "0.04em",
              lineHeight: 1.5,
            }}
          >
            © 2026 Kang Gyeonggu · Designed & Built in React
          </p>
        </motion.div>
      </div>
    </section>
  );
}
