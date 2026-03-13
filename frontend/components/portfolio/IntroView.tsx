"use client";

import { useEffect, useState, useCallback } from "react";
import { motion } from "framer-motion";

type Phase = "draw" | "split" | "hold" | "fadeout";

export function IntroView({ onComplete }: { onComplete: () => void }) {
  const [phase, setPhase] = useState<Phase>("draw");

  const advancePhase = useCallback(() => {
    setPhase((prev) => {
      if (prev === "draw") return "split";
      if (prev === "split") return "hold";
      if (prev === "hold") return "fadeout";
      return prev;
    });
  }, []);

  useEffect(() => {
    const timers: ReturnType<typeof setTimeout>[] = [];
    timers.push(setTimeout(() => advancePhase(), 1400));
    timers.push(setTimeout(() => advancePhase(), 3200));
    timers.push(setTimeout(() => advancePhase(), 4200));
    timers.push(setTimeout(() => onComplete(), 4900));
    return () => timers.forEach(clearTimeout);
  }, [advancePhase, onComplete]);

  const isSplitting = phase === "split" || phase === "hold" || phase === "fadeout";
  const isFading = phase === "fadeout";

  const lineStroke = "rgba(255,255,255,0.15)";
  const lineWidth = 1.5;
  const curtainX = "55%";
  const curtainDuration = 1.6;
  const curtainEase = [0.76, 0, 0.24, 1] as [number, number, number, number];

  return (
    <motion.div
      className="fixed inset-0 z-[200] flex items-center justify-center overflow-hidden"
      style={{ backgroundColor: "#0a0a0f" }}
      initial={{ opacity: 1 }}
      animate={{ opacity: isFading ? 0 : 1 }}
      transition={{ duration: 0.7, ease: "easeInOut" }}
    >
      <div className="relative z-10 text-center px-6 select-none">
        <motion.h1
          className="text-white"
          style={{
            fontSize: "clamp(1.4rem, 3.5vw, 2.4rem)",
            fontWeight: 600,
            lineHeight: 1.4,
            letterSpacing: "-0.01em",
          }}
          initial={{ opacity: 0, scale: 0.96 }}
          animate={
            isSplitting
              ? { opacity: 1, scale: 1 }
              : { opacity: 0, scale: 0.96 }
          }
          transition={{ duration: 1.2, ease: "easeOut" }}
        >
          강경구의 포트폴리오 홈페이지에
          <br />
          오신걸 환영합니다
        </motion.h1>

        <motion.div
          className="flex items-center justify-center gap-2 mt-6"
          initial={{ opacity: 0 }}
          animate={isSplitting ? { opacity: 1 } : { opacity: 0 }}
          transition={{ duration: 0.8, delay: isSplitting ? 0.6 : 0 }}
        >
          {[0, 0.2, 0.4].map((delay, i) => (
            <motion.div
              key={i}
              className="w-1.5 h-1.5 rounded-full bg-white/30"
              animate={{ opacity: [0.3, 0.8, 0.3] }}
              transition={{ duration: 1.4, repeat: Infinity, delay }}
            />
          ))}
        </motion.div>
      </div>

      <motion.div
        className="absolute top-0 left-0 w-1/2 h-full z-20"
        style={{ backgroundColor: "#0a0a0f" }}
        initial={{ x: 0 }}
        animate={{ x: isSplitting ? `-${curtainX}` : 0 }}
        transition={{ duration: curtainDuration, ease: curtainEase }}
      >
        <svg className="absolute inset-0 w-[200%] h-full pointer-events-none" preserveAspectRatio="none">
          <motion.line
            x1="0%"
            y1="0%"
            x2="50%"
            y2="50%"
            stroke={lineStroke}
            strokeWidth={lineWidth}
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 1.2, ease: "easeOut" }}
          />
        </svg>
        <svg className="absolute inset-0 w-[200%] h-full pointer-events-none" preserveAspectRatio="none">
          <motion.line
            x1="0%"
            y1="100%"
            x2="50%"
            y2="50%"
            stroke={lineStroke}
            strokeWidth={lineWidth}
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 1.2, ease: "easeOut", delay: 0.1 }}
          />
        </svg>
        <motion.div
          className="absolute top-0 right-0 w-px h-full"
          style={{
            background: "linear-gradient(to bottom, transparent 10%, rgba(255,255,255,0.06) 50%, transparent 90%)",
          }}
          initial={{ opacity: 0 }}
          animate={{ opacity: isSplitting ? 1 : 0 }}
          transition={{ duration: 0.3 }}
        />
      </motion.div>

      <motion.div
        className="absolute top-0 right-0 w-1/2 h-full z-20"
        style={{ backgroundColor: "#0a0a0f" }}
        initial={{ x: 0 }}
        animate={{ x: isSplitting ? curtainX : 0 }}
        transition={{ duration: curtainDuration, ease: curtainEase }}
      >
        <svg className="absolute inset-0 w-[200%] h-full pointer-events-none" style={{ left: "-100%" }} preserveAspectRatio="none">
          <motion.line
            x1="100%"
            y1="0%"
            x2="50%"
            y2="50%"
            stroke={lineStroke}
            strokeWidth={lineWidth}
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 1.2, ease: "easeOut", delay: 0.05 }}
          />
        </svg>
        <svg className="absolute inset-0 w-[200%] h-full pointer-events-none" style={{ left: "-100%" }} preserveAspectRatio="none">
          <motion.line
            x1="100%"
            y1="100%"
            x2="50%"
            y2="50%"
            stroke={lineStroke}
            strokeWidth={lineWidth}
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 1.2, ease: "easeOut", delay: 0.15 }}
          />
        </svg>
        <motion.div
          className="absolute top-0 left-0 w-px h-full"
          style={{
            background: "linear-gradient(to bottom, transparent 10%, rgba(255,255,255,0.06) 50%, transparent 90%)",
          }}
          initial={{ opacity: 0 }}
          animate={{ opacity: isSplitting ? 1 : 0 }}
          transition={{ duration: 0.3 }}
        />
      </motion.div>

      <motion.div
        className="absolute inset-0 z-30 pointer-events-none flex items-center justify-center"
        initial={{ opacity: 0 }}
        animate={{ opacity: isSplitting ? [0, 0.5, 0] : 0 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
      >
        <div
          className="w-px h-[60%]"
          style={{
            background: "linear-gradient(to bottom, transparent, rgba(212,165,116,0.3), transparent)",
          }}
        />
      </motion.div>
    </motion.div>
  );
}
