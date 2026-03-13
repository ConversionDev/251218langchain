"use client";

/**
 * 깃털 SVG — Potrace(feather2_potrace.svg) 또는 OpenCV contour 사용.
 * Potrace: python -m app.opencv.feather_potrace --image2 --potrace-exe "C:\dev\tools\potrace\potrace.exe" -o app/opencv/feather2_potrace.svg
 * OpenCV: python -m app.opencv.feather_contour --image2 -o app/opencv/feather2_out.svg
 */
const VIEW_W = 444;
const VIEW_H = 372;
/** 오른손 쓰는 각도: 위는 왼쪽, 촉은 오른쪽(반시계 기울기). IntroAnimation nib 위치 계산에도 사용 */
export const PENCIL_WRITE_ANGLE_DEG = -22;
const WRITE_ANGLE_DEG = PENCIL_WRITE_ANGLE_DEG;
const STROKE = "#e2e8f4";
const STROKE_WIDTH = 1.2;

/** Potrace 1.16 출력 (feather2_potrace.svg) — path + transform 그대로 사용 */
const POTRACE_PATH =
  "M3300 2481 c-223 -87 -366 -160 -575 -296 -336 -218 -690 -574 -942 -950 -127 -189 -321 -552 -370 -693 -16 -46 -16 -54 -3 -62 25 -16 30 -12 52 43 37 90 141 289 197 376 l54 83 18 -23 c10 -13 25 -33 34 -44 16 -19 16 -19 10 9 -20 94 -23 86 31 86 48 0 220 41 253 60 11 7 -1 10 -44 10 l-60 1 55 18 c77 25 155 66 222 117 59 46 128 124 108 124 -6 0 31 28 82 62 128 84 274 234 358 366 180 285 430 574 622 719 35 26 47 44 31 42 -5 0 -64 -22 -133 -48z m-96 -139 c-175 -174 -304 -336 -444 -558 -30 -48 -96 -131 -147 -184 -159 -166 -321 -265 -601 -366 -73 -26 -132 -51 -132 -56 0 -16 99 -8 186 16 155 42 142 40 119 21 -63 -52 -215 -109 -339 -126 -100 -14 -110 -31 -20 -39 l59 -5 -49 -7 c-27 -5 -62 -8 -77 -8 -16 0 -29 -4 -29 -10 0 -5 -6 -10 -14 -10 -13 0 -86 -102 -120 -169 -10 -18 -20 -30 -23 -27 -14 14 195 359 326 538 55 75 58 78 126 98 73 23 235 94 235 105 0 3 -12 -1 -27 -9 -44 -22 -203 -76 -225 -76 -16 0 -11 10 31 61 130 155 154 179 206 195 64 21 149 64 141 71 -3 3 -11 1 -18 -4 -17 -14 -118 -46 -124 -40 -3 2 39 46 93 96 81 75 108 94 153 107 54 16 150 60 150 69 0 3 -23 -4 -51 -16 -95 -37 -89 -17 18 63 173 129 369 243 566 329 61 26 118 49 126 49 7 0 -36 -49 -95 -108z m-1009 -1078 c-27 -13 -57 -24 -65 -23 -19 0 80 47 100 47 8 0 -7 -10 -35 -24z";

export function FeatherPenSVG({
  width,
  left,
  visible,
  className = "",
}: {
  width: number;
  left: number;
  visible: boolean;
  className?: string;
}) {
  const height = width * (VIEW_H / VIEW_W);

  return (
    <div
      className={className}
      style={{
        position: "absolute",
        top: "50%",
        left,
        width,
        height,
        transform: `translateY(-62%) rotate(${WRITE_ANGLE_DEG}deg)`,
        transformOrigin: "0% 50%",
        opacity: visible ? 1 : 0,
        transition: "opacity 0.4s",
        overflow: "visible",
      }}
      aria-hidden
    >
      <svg
        viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}
        preserveAspectRatio="xMaxYMid meet"
        style={{ width: "100%", height: "100%", display: "block" }}
        shapeRendering="geometricPrecision"
      >
        <g transform="translate(444,0) scale(-1,1)">
          <g
            transform="translate(0,372) scale(0.1,-0.1)"
            fill="none"
            stroke={STROKE}
            strokeWidth={12}
            strokeLinejoin="round"
            strokeLinecap="round"
          >
            <path d={POTRACE_PATH} />
          </g>
        </g>
      </svg>
    </div>
  );
}
