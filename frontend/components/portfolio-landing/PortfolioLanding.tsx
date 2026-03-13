"use client";

import { useState, useEffect } from "react";
import { AnimatePresence } from "framer-motion";
import { Navigation } from "./Navigation";
import { AboutSection } from "./AboutSection";
import { ProjectsSection } from "./ProjectsSection";
import { StrengthsTechSection } from "./StrengthsTechSection";
import { TimelineSection } from "./TimelineSection";
import { ContactSection } from "./ContactSection";
import { IntroAnimation } from "./IntroAnimation";
import { ResumePanel } from "@/components/portfolio/ResumePanel";

const SECTIONS = ["about", "projects", "strengths", "timeline", "contact"] as const;

export function PortfolioLanding() {
  const [showIntro, setShowIntro] = useState(true);
  const [introComplete, setIntroComplete] = useState(false);
  const [activeSection, setActiveSection] = useState("about");
  const [resumeOpen, setResumeOpen] = useState(false);

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

  return (
    <div
      className="min-h-screen [overflow-x:clip]"
      style={{
        background: "#0f172a",
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
              background: "#0f172a",
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
              onOpenResume={() => setResumeOpen(true)}
            />
            <main className="flex-1 min-w-0 max-w-[720px] pt-14 md:pt-0 pb-40">
              <AboutSection />
              <ProjectsSection />
              <StrengthsTechSection />
              <TimelineSection />
              <ContactSection />
            </main>
          </div>
          <ResumePanel open={resumeOpen} onClose={() => setResumeOpen(false)} />
        </>
      )}
    </div>
  );
}
