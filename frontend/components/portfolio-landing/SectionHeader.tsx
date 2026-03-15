"use client";

import { useRef } from "react";
import { motion, useInView } from "framer-motion";

interface SectionHeaderProps {
  num: string;
  label: string;
}

export function SectionHeader({ num, label }: SectionHeaderProps) {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: "-50px" });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0 }}
      animate={inView ? { opacity: 1 } : {}}
      transition={{ duration: 0.5 }}
      className="relative mb-16 overflow-visible"
    >
      <span
        className="absolute select-none pointer-events-none leading-none"
        style={{
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: "6rem",
          fontWeight: 800,
          color: "rgba(142,240,215,0.028)",
          letterSpacing: "-0.06em",
          top: "-1.4rem",
          left: "-0.25rem",
          zIndex: 0,
        }}
      >
        {num.padStart(2, "0")}
      </span>
      <div className="relative z-10 w-full">
        <div className="flex items-center gap-3">
          <span
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: "0.7rem",
              color: "rgba(142,240,215,0.82)",
              fontWeight: 600,
              letterSpacing: "0.08em",
            }}
          >
            {num.padStart(2, "0")}.
          </span>
          <h2
            style={{
              fontSize: "clamp(1.25rem, 2.2vw, 1.55rem)",
              fontWeight: 600,
              color: "#ccd6f6",
              letterSpacing: "0.02em",
              whiteSpace: "nowrap",
            }}
          >
            {label}
          </h2>
        </div>
        <div
          className="w-full h-px mt-3"
          style={{ background: "rgba(255,255,255,0.32)" }}
          aria-hidden
        />
      </div>
    </motion.div>
  );
}
