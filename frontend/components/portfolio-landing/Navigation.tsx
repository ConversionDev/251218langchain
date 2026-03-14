"use client";

import { motion } from "framer-motion";
import { Mail, PenSquare, User, FolderKanban, Layers, Briefcase, FileText } from "lucide-react";
import { Jua, Nanum_Pen_Script, Nanum_Brush_Script } from "next/font/google";
import Image from "next/image";

const jua = Jua({ weight: "400", subsets: ["latin"], display: "swap" });
const nanumPen = Nanum_Pen_Script({ weight: "400", subsets: ["latin"], display: "swap" });
const nanumBrush = Nanum_Brush_Script({ weight: "400", subsets: ["latin"], display: "swap" });

/** 이력서 PDF: public/resume/강경구_커스텀이력서.pdf 에 두면 /resume/강경구_커스텀이력서.pdf 로 서빙됨 */
const RESUME_PDF_URL = "/resume/강경구_커스텀이력서.pdf";

const NAV = [
  { id: "about", label: "About", icon: User },
  { id: "projects", label: "Projects", icon: FolderKanban },
  { id: "strengths", label: "Tech Stack", icon: Layers },
  { id: "timeline", label: "Career", icon: Briefcase },
  { id: "resume", label: "Resume", icon: FileText, openPdf: true },
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

const SOCIALS = [
  { type: "github" as const, href: "https://github.com/ConversionDev", label: "GitHub" },
  { type: "icon" as const, icon: PenSquare, href: "https://kku1031.tistory.com", label: "Blog" },
  { type: "icon" as const, icon: Mail, href: "mailto:kanggyeonggu@gmail.com", label: "Email" },
];

type NavigationProps = {
  activeSection: string;
  /** 사이드바 상단 로고/프로필 사진 URL. 있으면 이름 위에 크게 표시 */
  logoImageSrc?: string;
  /** Resume 클릭 시 내부 창(모달)으로 이력서 열기 */
  onOpenResumeModal?: () => void;
};

export function Navigation({ activeSection, logoImageSrc, onOpenResumeModal }: NavigationProps) {
  const go = (id: string) =>
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });

  const iconColor = "rgba(220,228,245,0.6)";
  const iconSize = 14;

  return (
    <header
      className={`
        hidden
        md:sticky md:top-0 md:h-screen
        md:w-[240px] lg:w-[260px] xl:w-[300px] md:shrink-0
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
        {logoImageSrc && (
          <div className="mb-4 flex justify-start">
            <div className="relative w-28 h-28 sm:w-32 sm:h-32 rounded-full overflow-hidden ring-2 ring-[#8ef0d7]/30">
              <Image src={logoImageSrc} alt="강경구" fill className="object-cover" sizes="128px" priority />
            </div>
          </div>
        )}
        <div className="flex items-center gap-2">
          <h1
            className={nanumPen.className}
            style={{
              fontSize: "clamp(2.2rem, 3.4vw, 2.9rem)",
              fontWeight: 500,
              lineHeight: 1.02,
              letterSpacing: "-0.02em",
              color: "rgba(204,214,246,0.92)",
            }}
          >
            강경구
          </h1>
          <span
            className="shrink-0 w-1.5 h-1.5 rounded-full"
            style={{
              background: "#8ef0d7",
              boxShadow: "0 0 8px rgba(142,240,215,0.5)",
            }}
            aria-hidden
          />
        </div>
        <span
          className={`flex items-center gap-2 mt-3 ${nanumBrush.className}`}
          style={{
            fontSize: "clamp(1rem, 1.5vw, 1.2rem)",
            lineHeight: 1.5,
            color: "#ffffff",
            fontWeight: 400,
          }}
        >
          <span>&quot;한 줄의 코드가 세상을 바꾼다&quot;</span>
        </span>
        <nav className="mt-12 relative">
          <div
            className="absolute left-0 top-1 bottom-1 w-px"
            style={{ background: "rgba(142,240,215,0.08)" }}
          />
          <div className="pl-5 space-y-1.5">
            {NAV.map((item) => {
              const { id, label, icon: Icon } = item;
              const openPdf = "openPdf" in item && item.openPdf;
              return (
              <button
                key={id}
                type="button"
                onClick={() => openPdf ? (onOpenResumeModal?.() ?? window.open(RESUME_PDF_URL, "_blank", "noopener,noreferrer")) : go(id)}
                className="group relative flex items-center py-3 w-full text-left"
              >
                {activeSection === id && !openPdf && (
                  <motion.span
                    layoutId="navDot"
                    className="absolute -left-[5.5px] w-2.5 h-2.5 rounded-full"
                    style={{
                      background: "#8ef0d7",
                      boxShadow: "0 0 10px rgba(142,240,215,0.6)",
                    }}
                    transition={{
                      type: "spring",
                      stiffness: 380,
                      damping: 28,
                    }}
                  />
                )}
                <Icon size={iconSize} className="mr-2 shrink-0 opacity-70" style={{ color: iconColor }} />
                <span
                  style={{
                    fontSize: "1.05rem",
                    fontWeight: activeSection === id ? 600 : 400,
                    letterSpacing: "0.1em",
                    textTransform: "uppercase",
                    color: activeSection === id ? "#8ef0d7" : "rgba(220,228,245,0.65)",
                    transition: "color 0.25s",
                  }}
                  className={activeSection !== id ? "group-hover:!text-[rgba(220,228,245,0.9)]" : ""}
                >
                  {label}
                </span>
              </button>
            );
            })}
          </div>
        </nav>
      </motion.div>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.7, delay: 0.3 }}
        className="mt-12 lg:mt-0 flex items-center gap-5"
      >
        {SOCIALS.map((item) => (
          <a
            key={item.label}
            href={item.href}
            target={item.href.startsWith("mailto") ? undefined : "_blank"}
            rel="noopener noreferrer"
            aria-label={item.label}
            className="transition-colors duration-300 flex items-center justify-center"
            style={{ color: "rgba(220,228,245,0.7)" }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLAnchorElement).style.color = "#8ef0d7";
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLAnchorElement).style.color =
                "rgba(220,228,245,0.7)";
            }}
          >
            {item.type === "github" ? (
              <GitHubLogo size={32} />
            ) : (
              <item.icon size={32} />
            )}
          </a>
        ))}
      </motion.div>
    </header>
  );
}
