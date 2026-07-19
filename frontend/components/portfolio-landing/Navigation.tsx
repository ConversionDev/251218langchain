"use client";

import { motion } from "framer-motion";
import { Mail, Phone, AtSign, PenSquare, User, FolderKanban, Layers, Briefcase, FileText } from "lucide-react";
import { Jua, Nanum_Brush_Script, Nunito } from "next/font/google";

const jua = Jua({ weight: "400", subsets: ["latin"], display: "swap" });
const nanumBrush = Nanum_Brush_Script({ weight: "400", subsets: ["latin"], display: "swap" });
const nunito = Nunito({ weight: ["400", "600"], subsets: ["latin"], display: "swap" });

const NAV = [
  { id: "about", label: "About", icon: User },
  { id: "projects", label: "Projects", icon: FolderKanban },
  { id: "strengths", label: "Tech Stack", icon: Layers },
  { id: "timeline", label: "Career", icon: Briefcase },
  { id: "resume", label: "Resume", icon: FileText, href: "/resume", openInNewTab: true },
  { id: "contact", label: "Contact", icon: Mail },
] as const;

/** 보내주신 사진과 유사: 한쪽 톱니, 한쪽 부드러운 곡선, 중앙 깃대. 반전해 펜끝이 문장(오른쪽) 향함 */
function QuillFeatherIcon({ size = 20 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className="shrink-0 opacity-90"
      style={{ color: "#ffffff", transform: "rotate(-90deg)" }}
      aria-hidden
    >
      {/* 깃털: 펜끝 우하, 오른쪽=부드러운 곡선, 왼쪽=톱니 형태 */}
      <path
        fill="currentColor"
        d="M12 22 L14 18 L15 13 L14.5 8 L13 4 L12 2 L10.5 3.5 L9 6 L9.5 9 L8 11 L9 14 L7.5 16 L9 18.5 L10.5 20 L12 22 Z"
      />
      {/* 중앙 깃대 */}
      <path
        stroke="currentColor"
        strokeWidth="0.55"
        strokeLinecap="round"
        strokeOpacity="0.8"
        d="M12 2 L12 21"
      />
    </svg>
  );
}

/** GitHub 공식 마크 (옥토캣) - 라이트 톤 */
function GitHubLogo({ size = 22 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="currentColor"
      aria-hidden
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.166 6.839 9.489.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.604-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.464-1.11-1.464-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.578 9.578 0 0112 6.836c.85.004 1.705.114 2.504.336 1.909-1.294 2.747-1.025 2.747-1.025.546 1.376.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.578.688.48C19.138 20.163 22 16.418 22 12c0-5.523-4.477-10-10-10z"
      />
    </svg>
  );
}

/** 내비 하단 연락처 행 — 메뉴와 같은 구조, 한 단계 작은 타이포 */
const INFO_LINKS = [
  { kind: "icon" as const, icon: Phone, href: "tel:010-4739-2339", label: "010-4739-2339", newTab: false },
  { kind: "icon" as const, icon: AtSign, href: "mailto:rkdrudrn1031@gmail.com", label: "rkdrudrn1031@gmail.com", newTab: false },
  { kind: "github" as const, href: "https://github.com/ConversionDev", label: "github.com/ConversionDev", newTab: true },
  { kind: "icon" as const, icon: PenSquare, href: "https://kku1031.tistory.com", label: "kku1031.tistory.com", newTab: true },
];

/** 좌측 슬라이드 전부 어두운 틸로 통일 */
const ACTIVE_TEAL = "#5eead4";
const ACTIVE_COLORS: Record<string, string> = {
  about: ACTIVE_TEAL,
  projects: ACTIVE_TEAL,
  strengths: ACTIVE_TEAL,
  timeline: ACTIVE_TEAL,
  resume: ACTIVE_TEAL,
  contact: ACTIVE_TEAL,
};

type NavigationProps = {
  activeSection: string;
};

export function Navigation({ activeSection }: NavigationProps) {
  const go = (id: string) =>
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });

  const iconColorDefault = "rgba(220,228,245,0.6)";
  const iconSize = 26;

  return (
    <header
      className={`
        relative z-10
        hidden
        md:sticky md:top-0 md:h-screen
        md:w-[280px] lg:w-[300px] xl:w-[340px] md:shrink-0
        md:flex md:flex-col md:justify-between
        md:py-20 lg:py-24
        ${jua.className}
      `}
    >
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, ease: [0.25, 0, 0, 1] }}
      >
        <div className="flex items-center gap-2">
          <h1
            className={nunito.className}
            style={{
              fontSize: "clamp(2.5rem, 4.2vw, 3.2rem)",
              fontWeight: 600,
              lineHeight: 1.02,
              letterSpacing: "0.02em",
              color: "rgba(204,214,246,0.95)",
            }}
          >
            강경구
          </h1>
        </div>
        <p
          className={`${nunito.className} mt-6 mb-6`}
          style={{
            fontSize: "clamp(0.95rem, 1.4vw, 1.1rem)",
            fontWeight: 500,
            letterSpacing: "0.2em",
            color: "rgba(220,228,245,0.72)",
            textTransform: "uppercase",
          }}
        >
          AI Engineer
        </p>
        <span
          className={`flex items-center gap-2 mt-6 ${nanumBrush.className}`}
          style={{
            fontSize: "clamp(1.35rem, 2.2vw, 2.65rem)",
            lineHeight: 1.5,
            color: "#ffffff",
            fontWeight: 400,
            whiteSpace: "nowrap",
          }}
        >
          <span>&quot;한 줄의 코드가 세상을 바꾼다&quot;</span>
        </span>
        <nav className="mt-12 relative">
          <div
            className="absolute left-0 top-1 bottom-1 w-px"
            style={{ background: "rgba(255,255,255,0.32)", boxShadow: "0 0 6px rgba(255,255,255,0.06)" }}
          />
          <div className="pl-5 space-y-1.5">
            {NAV.map((item) => {
              const { id, label, icon: Icon } = item;
              const href = "href" in item ? item.href : undefined;
              const openInNewTab = "openInNewTab" in item && item.openInNewTab;
              const isLink = Boolean(href);
              const isActive = activeSection === id;
              const activeColor = ACTIVE_COLORS[id] ?? "#8ef0d7";
              const content = (
                <>
                  <Icon
                    size={iconSize}
                    className={`mr-7 shrink-0 opacity-90 ${isActive ? "group-hover:!text-[#8ef0d7]" : ""}`}
                    style={{ color: isActive ? activeColor : iconColorDefault }}
                  />
                  <span
                    style={{
                      fontSize: "1.0625rem",
                      fontWeight: isActive ? 700 : 400,
                      letterSpacing: "0.1em",
                      textTransform: "uppercase",
                      color: isActive ? activeColor : "rgba(220,228,245,0.65)",
                      transition: "color 0.25s, background 0.2s",
                    }}
                    className={isActive ? "group-hover:!text-[#8ef0d7]" : "group-hover:!text-[rgba(220,228,245,0.9)]"}
                  >
                    {label}
                  </span>
                </>
              );
              const activeStyle = isActive
                ? {
                    background: "rgba(255,255,255,0.06)",
                    borderLeft: `3px solid ${activeColor}`,
                    marginLeft: "-3px",
                    paddingLeft: "3px",
                    borderRadius: "0 8px 8px 0",
                  }
                : {};
              if (isLink && href) {
                return (
                  <a
                    key={id}
                    href={href}
                    target={openInNewTab ? "_blank" : undefined}
                    rel={openInNewTab ? "noopener noreferrer" : undefined}
                    className="group relative flex items-center py-3 w-full text-left pl-5 -ml-5 pr-2 rounded-r-lg"
                    style={activeStyle}
                  >
                    {content}
                  </a>
                );
              }
              return (
                <button
                  key={id}
                  type="button"
                  onClick={() => go(id)}
                  className="group relative flex items-center py-3 w-full text-left pl-5 -ml-5 pr-2 rounded-r-lg"
                  style={activeStyle}
                >
                  {content}
                </button>
              );
            })}
            {/* CONTACT 아래 연락처 행들 — 메뉴와 같은 구조, 한 단계 작은 타이포 */}
            {INFO_LINKS.map((item) => (
              <a
                key={item.label}
                href={item.href}
                target={item.newTab ? "_blank" : undefined}
                rel={item.newTab ? "noopener noreferrer" : undefined}
                className="group relative flex items-center py-2 w-full text-left pl-5 -ml-5 pr-2 rounded-r-lg"
              >
                {item.kind === "github" ? (
                  <span className="mr-7 shrink-0 opacity-90 flex justify-center" style={{ width: iconSize, color: iconColorDefault }}>
                    <GitHubLogo size={22} />
                  </span>
                ) : (
                  <item.icon
                    size={22}
                    className="mr-7 shrink-0 opacity-90"
                    style={{ color: iconColorDefault, width: iconSize }}
                  />
                )}
                <span
                  style={{
                    fontSize: "0.9375rem",
                    fontWeight: 400,
                    letterSpacing: "0.05em",
                    color: "rgba(220,228,245,0.6)",
                    transition: "color 0.25s",
                  }}
                  className="group-hover:!text-[#8ef0d7]"
                >
                  {item.label}
                </span>
              </a>
            ))}
          </div>
        </nav>
      </motion.div>
    </header>
  );
}
