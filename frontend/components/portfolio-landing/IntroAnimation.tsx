"use client";

import { useEffect, useLayoutEffect, useState, useRef } from "react";
import { motion } from "framer-motion";
import { animate, cubicBezier } from "animejs";
import opentype from "opentype.js";
import { Nanum_Brush_Script, Noto_Serif_KR } from "next/font/google";
import { FeatherPenSVG, PENCIL_WRITE_ANGLE_DEG } from "./FeatherPenSVG";

const nanumBrush = Nanum_Brush_Script({
  weight: "400",
  subsets: ["latin"],
  display: "swap",
});
const notoSerifKR = Noto_Serif_KR({
  weight: ["700"],
  subsets: ["latin"],
  display: "swap",
});

const TAGLINE = "한 줄의 코드가 세상을 바꾼다";
const PENCIL_W = 200;

/** 글씨가 쓰여지는 걸 눈으로 따라갈 수 있도록 충분한 시간 */
const WRITE_DURATION = 5.2;

/** 손으로 쓰는 듯한 리듬: 처음·끝 살짝 느리고 중간이 조금 빠름 */
const WRITE_EASE = [0.22, 0.12, 0.3, 1] as const;

type PathData = {
  pathD: string;
  bbox: { x1: number; y1: number; x2: number; y2: number };
};

export function IntroAnimation({ onComplete }: { onComplete: () => void }) {
  const [showName, setShowName] = useState(false);
  const [showLine, setShowLine] = useState(false);
  const [writingStarted, setWritingStarted] = useState(false);
  const [isOut, setIsOut] = useState(false);
  const [progress, setProgress] = useState(0);

  const progressRef = useRef({ p: 0 });
  const lastLogStepRef = useRef(-1);
  const textRef = useRef<HTMLParagraphElement>(null);
  const pathRef = useRef<SVGPathElement | null>(null);
  const wrapperRef = useRef<HTMLDivElement | null>(null);

  const [textWidth, setTextWidth] = useState(500);
  const [pathData, setPathData] = useState<PathData | null>(null);
  const [pathLength, setPathLength] = useState<number | null>(null);

  const usePathMode = pathData !== null && pathLength !== null;

  useEffect(() => {
    opentype.load("/fonts/NanumBrushScript-Regular.ttf", (err, font) => {
      if (err || !font) return;
      try {
        const path = font.getPath(`"${TAGLINE}"`, 0, 0, 72);
        const bbox = path.getBoundingBox();
        setPathData({
          pathD: path.toPathData(2),
          bbox: {
            x1: bbox.x1,
            y1: bbox.y1,
            x2: bbox.x2,
            y2: bbox.y2,
          },
        });
      } catch {
        // path 생성 실패 시 기존 clipPath 방식 사용
      }
    });
  }, []);

  useEffect(() => {
    const t1 = setTimeout(() => setShowName(true), 300);
    const t2 = setTimeout(() => setShowLine(true), 900);
    const t3 = setTimeout(() => {
      setTextWidth(textRef.current?.offsetWidth ?? 500);
      setWritingStarted(true);
    }, 1450);

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
    };
  }, []);

  useLayoutEffect(() => {
    if (!pathData || !pathRef.current) return;
    setPathLength(pathRef.current.getTotalLength());
  }, [pathData]);

  useEffect(() => {
    if (!writingStarted) return;
    let cancelled = false;

    progressRef.current.p = 0;
    setProgress(0);

    const anim = animate(progressRef.current, {
      p: 1,
      duration: WRITE_DURATION * 1000,
      ease: cubicBezier(
        WRITE_EASE[0],
        WRITE_EASE[1],
        WRITE_EASE[2],
        WRITE_EASE[3]
      ),
      onUpdate: () => {
        if (!cancelled) {
          const p = progressRef.current.p;
          setProgress(p);

          if (process.env.NODE_ENV === "development") {
            const step = Math.floor(p * 5);
            if (step !== lastLogStepRef.current) {
              lastLogStepRef.current = step;
              console.log("[anime.js] write progress", step * 20 + "%");
            }
          }
        }
      },
    });

    const t1 = setTimeout(() => {
      if (!cancelled) setIsOut(true);
    }, (WRITE_DURATION + 1.6) * 1000);

    const t2 = setTimeout(() => {
      if (!cancelled) onComplete();
    }, (WRITE_DURATION + 2.3) * 1000);

    return () => {
      cancelled = true;
      anim.cancel();
      clearTimeout(t1);
      clearTimeout(t2);
    };
  }, [writingStarted, onComplete]);

  const angleRad = (PENCIL_WRITE_ANGLE_DEG * Math.PI) / 180;
  let nibX: number;

  if (usePathMode && pathRef.current && pathLength !== null) {
    const len = progress * pathLength;
    const pt = pathRef.current.getPointAtLength(len);
    const bbox = pathData!.bbox;
    const w = bbox.x2 - bbox.x1;
    nibX = w > 0 ? ((pt.x - bbox.x1) / w) * textWidth : 0;
  } else {
    nibX = progress * (textWidth + PENCIL_W * 0.5);
  }

  const penLeft = nibX - PENCIL_W * Math.cos(angleRad);
  const streakWidth = Math.min(textWidth, Math.max(0, nibX));
  const clipRight = Math.max(
    0,
    Math.min(100, (1 - nibX / textWidth) * 100)
  );
  const pencilVisible = progress > 0.01 && progress < 0.99;

  const taglinePathSvg =
    pathData !== null ? (
      <svg
        className="absolute inset-0 w-full h-full"
        style={{ overflow: "visible" }}
        viewBox={`${pathData.bbox.x1} ${pathData.bbox.y1} ${
          pathData.bbox.x2 - pathData.bbox.x1
        } ${pathData.bbox.y2 - pathData.bbox.y1}`}
        preserveAspectRatio="xMidYMid meet"
      >
        <defs>
          <clipPath id="introPathReveal">
            <rect
              x={pathData.bbox.x1}
              y={pathData.bbox.y1}
              width={(pathData.bbox.x2 - pathData.bbox.x1) * progress}
              height={pathData.bbox.y2 - pathData.bbox.y1}
            />
          </clipPath>
        </defs>
        <g clipPath="url(#introPathReveal)">
          <g>
            <path
              ref={pathRef}
              d={pathData.pathD}
              fill="#ffffff"
              style={{ transition: "none", opacity: pathLength !== null ? 1 : 0 }}
            />
          </g>
        </g>
      </svg>
    ) : null;

  return (
    <motion.div
      className="fixed inset-0 z-[200] flex flex-col items-center justify-center overflow-hidden"
      style={{
        background:
          "radial-gradient(ellipse 120% 100% at 50% 50%, #0d1c42 0%, #060c28 55%, #010511 100%)",
      }}
      animate={{ opacity: isOut ? 0 : 1 }}
      transition={{ duration: 0.8, ease: [0.4, 0, 0.2, 1] }}
    >
      <div className="relative flex flex-col items-center select-none px-6 w-full max-w-4xl">
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
          }}
        >
          강경구
        </motion.h1>

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

        <div
          ref={wrapperRef}
          className="relative inline-block"
          style={{ overflow: "hidden" }}
        >
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
            "{TAGLINE}"
          </p>

          {taglinePathSvg}

          {!pathData && (
            <p
              className={`absolute inset-0 ${nanumBrush.className}`}
              style={{
                fontSize: "clamp(3.2rem, 8.5vw, 6rem)",
                color: "#ffffff",
                lineHeight: 1.4,
                whiteSpace: "nowrap",
                paddingBottom: "0.35em",
                clipPath: `inset(-80px ${clipRight.toFixed(2)}% -80px 0)`,
              }}
            >
              "{TAGLINE}"
            </p>
          )}

          {writingStarted && (
            <div
              className="absolute pointer-events-none"
              style={{ inset: 0, overflow: "visible" }}
            >
              <div
                style={{
                  position: "absolute",
                  bottom: "0.28em",
                  left: 0,
                  width: streakWidth,
                  height: 2,
                  background:
                    "linear-gradient(90deg, transparent 0%, rgba(226,232,244,0.5) 30%, rgba(226,232,244,0.85) 100%)",
                  transition: "none",
                }}
              />
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
