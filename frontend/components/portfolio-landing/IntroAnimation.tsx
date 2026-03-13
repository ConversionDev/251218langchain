"use client";

import { useEffect, useState, useRef } from "react";
import { motion, animate as fmAnimate } from "framer-motion";
import { Nanum_Brush_Script, Noto_Serif_KR } from "next/font/google";
import { FeatherPenSVG, PENCIL_WRITE_ANGLE_DEG } from "./FeatherPenSVG";

const nanumBrush = Nanum_Brush_Script({ weight: "400", subsets: ["latin"], display: "swap" });
const notoSerifKR = Noto_Serif_KR({ weight: ["700"], subsets: ["latin"], display: "swap" });

const PENCIL_W = 200;
const WRITE_DURATION = 3.2;
/** 손으로 쓰는 듯한 리듬: 처음·끝 살짝 느리고 중간이 조금 빠름 */
const WRITE_EASE = [0.22, 0.12, 0.3, 1] as const;

export function IntroAnimation({ onComplete }: { onComplete: () => void }) {
  const [showName, setShowName] = useState(false);
  const [showLine, setShowLine] = useState(false);
  const [writingStarted, setWritingStarted] = useState(false);
  const [isOut, setIsOut] = useState(false);
  const [progress, setProgress] = useState(0);
  const textRef = useRef<HTMLParagraphElement>(null);
  const [textWidth, setTextWidth] = useState(500);

  useEffect(() => {
    const t1 = setTimeout(() => setShowName(true), 300);
    const t2 = setTimeout(() => setShowLine(true), 900);
    const t3 = setTimeout(() => {
      setTextWidth(textRef.current?.offsetWidth ?? 500);
      setWritingStarted(true);
    }, 1450);
    return () => { clearTimeout(t1); clearTimeout(t2); clearTimeout(t3); };
  }, []);

  useEffect(() => {
    if (!writingStarted) return;
    let cancelled = false;
    const controls = fmAnimate(0, 1, {
      duration: WRITE_DURATION,
      ease: WRITE_EASE,
      onUpdate: (v) => { if (!cancelled) setProgress(v); },
    });
    const t1 = setTimeout(() => { if (!cancelled) setIsOut(true); }, (WRITE_DURATION + 1.6) * 1000);
    const t2 = setTimeout(() => { if (!cancelled) onComplete(); }, (WRITE_DURATION + 2.3) * 1000);
    return () => {
      cancelled = true;
      controls.stop();
      clearTimeout(t1);
      clearTimeout(t2);
    };
  }, [writingStarted, onComplete]);

  // 연필 촉이 글자 끝을 따라가며, 촉 바로 앞까지 텍스트가 드러남 (글씨 써지는 느낌)
  const nibX = progress * (textWidth + PENCIL_W * 0.5);
  const angleRad = (PENCIL_WRITE_ANGLE_DEG * Math.PI) / 180;
  const penLeft = nibX - PENCIL_W * Math.cos(angleRad);
  const streakWidth = Math.min(textWidth, Math.max(0, nibX));
  const clipRight = Math.max(0, Math.min(100, (1 - nibX / textWidth) * 100));
  const pencilVisible = progress > 0.01 && progress < 0.99;

  return (
    <motion.div
      className="fixed inset-0 z-[200] flex flex-col items-center justify-center overflow-hidden"
      style={{
        background: "radial-gradient(ellipse 120% 100% at 50% 50%, #0d1c42 0%, #060c28 55%, #010511 100%)",
      }}
      animate={{ opacity: isOut ? 0 : 1 }}
      transition={{ duration: 0.8, ease: [0.4, 0, 0.2, 1] }}
    >
      <div className="relative flex flex-col items-center select-none px-6 w-full max-w-4xl">

        {/* 영어 이름 - 얇은 간격 넓은 대문자 */}
        <motion.p
          initial={{ opacity: 0, y: -12 }}
          animate={{ opacity: showName ? 0.5 : 0, y: showName ? 0 : -12 }}
          transition={{ duration: 0.7 }}
          style={{
            fontSize: "clamp(0.7rem, 1.5vw, 1rem)",
            letterSpacing: "0.55em",
            color: "#b8d4f0",
            fontWeight: 300,
            textTransform: "uppercase",
            marginBottom: "0.55rem",
            fontFamily: "system-ui, -apple-system, sans-serif",
          }}
        >
          Kang Kyung Gu
        </motion.p>

        {/* 한글 이름 - 사이드바와 동일한 Nanum Pen Script */}
        <motion.h1
          initial={{ opacity: 0, y: 28 }}
          animate={{ opacity: showName ? 1 : 0, y: showName ? 0 : 28 }}
          transition={{ duration: 0.75, ease: [0.25, 0, 0, 1] }}
          className={notoSerifKR.className}
          style={{
            fontSize: "clamp(1.8rem, 4vw, 3rem)",
            fontWeight: 700,
            letterSpacing: "0.04em",
            lineHeight: 1.05,
            color: "rgba(180,200,240,0.6)",
            marginBottom: "0.8rem",
            textShadow: "none",
          }}
        >
          강경구
        </motion.h1>

        {/* 구분선 */}
        <motion.div
          initial={{ scaleX: 0, opacity: 0 }}
          animate={{ scaleX: showLine ? 1 : 0, opacity: showLine ? 1 : 0 }}
          transition={{ duration: 0.55, ease: [0.25, 0, 0, 1] }}
          style={{
            height: 1,
            width: "clamp(140px, 26vw, 260px)",
            background: "linear-gradient(90deg, transparent, #4fc3f7, transparent)",
            boxShadow: "0 0 10px rgba(79,195,247,0.5)",
            originX: 0.5,
            marginBottom: "2.2rem",
          }}
        />

        {/* 태그라인 + 깃털 애니메이션 영역 - overflow로 삐져나온 부분 숨김 */}
        <div className="relative inline-block" style={{ overflow: "hidden" }}>

          {/* 레이아웃 크기용 투명 텍스트 (실제 폭 측정) */}
          <p
            ref={textRef}
            className={nanumBrush.className}
            style={{
              fontSize: "clamp(3.2rem, 8.5vw, 6rem)",
              color: "transparent",
              lineHeight: 1.4,
              whiteSpace: "nowrap",
              paddingBottom: "0.35em",
              userSelect: "none",
              pointerEvents: "none",
            }}
            aria-hidden
          >
            &quot;한 줄의 코드가 세상을 바꾼다&quot;
          </p>

          {/* 보이는 태그라인 - clip-path로 좌→우 reveal */}
          <p
            className={`absolute inset-0 ${nanumBrush.className}`}
            style={{
              fontSize: "clamp(3.2rem, 8.5vw, 6rem)",
              color: "#ffffff",
              lineHeight: 1.4,
              whiteSpace: "nowrap",
              paddingBottom: "0.35em",
              clipPath: `inset(-80px ${clipRight.toFixed(2)}% -80px 0)`,
              textShadow: "none",
              transition: "none",
            }}
          >
            &quot;한 줄의 코드가 세상을 바꾼다&quot;
          </p>

          {/* 깃털 + 빛 줄기 오버레이 */}
          {writingStarted && (
            <div
              className="absolute pointer-events-none"
              style={{ inset: 0, overflow: "visible" }}
            >
              {/* 미니멀 밑줄 — 단순한 선만 */}
              <div
                style={{
                  position: "absolute",
                  bottom: "0.28em",
                  left: 0,
                  width: streakWidth,
                  height: 2,
                  background: "linear-gradient(90deg, transparent 0%, rgba(226,232,244,0.5) 30%, rgba(226,232,244,0.85) 100%)",
                  transition: "none",
                }}
              />

              {/* 깃털펜: 레퍼런스 PNG처럼 선만 선명하게, 발광 없음 */}
              <FeatherPenSVG
                width={PENCIL_W}
                left={penLeft}
                visible={pencilVisible}
              />
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
