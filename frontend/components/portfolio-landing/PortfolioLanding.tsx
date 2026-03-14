"use client";

import { useState, useEffect, useCallback } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { X, Download } from "lucide-react";
import { Navigation } from "./Navigation";
import { AboutSection } from "./AboutSection";
import { ProjectsSection } from "./ProjectsSection";
import { StrengthsTechSection } from "./StrengthsTechSection";
import { TimelineSection } from "./TimelineSection";
import { ContactSection } from "./ContactSection";
import { IntroAnimation } from "./IntroAnimation";
import { ResumeModalContent } from "./ResumeSection";

const SECTIONS = ["about", "projects", "strengths", "timeline", "contact"] as const;

export function PortfolioLanding() {
  const [showIntro, setShowIntro] = useState(true);
  const [introComplete, setIntroComplete] = useState(false);
  const [activeSection, setActiveSection] = useState("about");
  const [resumeModalOpen, setResumeModalOpen] = useState(false);

  useEffect(() => {
    if (!introComplete) return;
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) setActiveSection(e.target.id);
        });
      },
      { rootMargin: "-20% 0px -60% 0px" }
    );
    SECTIONS.forEach((id) => {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    });
    return () => observer.disconnect();
  }, [introComplete]);

  const handleIntroComplete = () => {
    setShowIntro(false);
    setTimeout(() => setIntroComplete(true), 400);
  };

  const handleResumePdf = useCallback(() => {
    window.print();
  }, []);

  useEffect(() => {
    if (resumeModalOpen) {
      document.body.classList.add("resume-modal-open");
    } else {
      document.body.classList.remove("resume-modal-open");
    }
    return () => document.body.classList.remove("resume-modal-open");
  }, [resumeModalOpen]);

  useEffect(() => {
    if (!resumeModalOpen) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") setResumeModalOpen(false);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [resumeModalOpen]);

  const introBackground =
    "radial-gradient(ellipse 120% 100% at 50% 50%, #0d1c42 0%, #060c28 55%, #010511 100%)";

  return (
    <div
      className="min-h-screen [overflow-x:clip]"
      style={{
        background: introBackground,
        color: "#e8e8f0",
        WebkitFontSmoothing: "antialiased",
      }}
    >
      <AnimatePresence mode="wait">
        {showIntro && <IntroAnimation onComplete={handleIntroComplete} />}
      </AnimatePresence>
      {introComplete && (
        <>
          <div
            className="md:hidden fixed top-0 inset-x-0 z-50 flex items-center justify-between px-6 h-14"
            style={{
              background: "rgba(13, 28, 66, 0.85)",
              backdropFilter: "blur(20px)",
              WebkitBackdropFilter: "blur(20px)",
              borderBottom: "1px solid rgba(168,230,207,0.08)",
            }}
          >
            <span
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: "0.8125rem",
                color: "rgba(142,240,215,0.7)",
                fontWeight: 700,
                letterSpacing: "0.1em",
              }}
            >
              KGG_
            </span>
            <span
              style={{
                fontSize: "0.6rem",
                color: "rgba(255,255,255,0.2)",
                letterSpacing: "0.15em",
                fontWeight: 500,
              }}
            >
              AI DEVELOPER
            </span>
          </div>
          <div className="relative z-10 w-full max-w-[1280px] mx-auto px-8 sm:px-12 lg:px-16 xl:px-24 md:flex md:items-start md:gap-16 lg:gap-24 xl:gap-32">
            <Navigation
              activeSection={activeSection}
              onOpenResumeModal={() => setResumeModalOpen(true)}
            />
            <main className="flex-1 min-w-0 max-w-[720px] pt-14 md:pt-0 pb-40">
              <AboutSection />
              <ProjectsSection />
              <StrengthsTechSection />
              <TimelineSection />
              <ContactSection />
            </main>
          </div>

          {/* 이력서 모달: 모노톤 이력서 뷰 + PDF 다운로드(인쇄) */}
          <AnimatePresence>
            {resumeModalOpen && (
              <motion.div
                key="resume-modal"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="resume-modal-overlay fixed inset-0 z-[100] flex items-center justify-center p-4 sm:p-6"
                role="dialog"
                aria-modal="true"
                aria-label="이력서"
              >
                <div
                  className="absolute inset-0 bg-black/60 backdrop-blur-sm"
                  onClick={() => setResumeModalOpen(false)}
                  aria-hidden
                />
                <motion.div
                  initial={{ opacity: 0, scale: 0.96 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.96 }}
                  transition={{ duration: 0.2 }}
                  className="relative w-full max-w-4xl h-[85vh] sm:h-[90vh] flex flex-col rounded-lg overflow-hidden shadow-2xl bg-white border border-slate-200"
                  onClick={(e) => e.stopPropagation()}
                >
                  <div className="resume-modal-header flex items-center justify-between shrink-0 px-4 py-3 border-b border-slate-200 bg-slate-50">
                    <span className="text-sm font-semibold text-slate-700">이력서</span>
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={handleResumePdf}
                        className="inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium text-slate-700 bg-white border border-slate-300 hover:bg-slate-100 transition-colors"
                      >
                        <Download size={16} />
                        PDF 다운로드
                      </button>
                      <button
                        type="button"
                        onClick={() => setResumeModalOpen(false)}
                        className="p-1.5 rounded-md text-slate-500 hover:bg-slate-200 hover:text-slate-800 transition-colors"
                        aria-label="닫기"
                      >
                        <X size={20} />
                      </button>
                    </div>
                  </div>
                  <div className="flex-1 min-h-0 overflow-hidden">
                    <ResumeModalContent />
                  </div>
                </motion.div>
              </motion.div>
            )}
          </AnimatePresence>
        </>
      )}
    </div>
  );
}
