# 포트폴리오 — GSAP 관련 작업 정리

포트폴리오(랜딩·인트로)에서 **GSAP**를 사용한 부분만 정리한 문서입니다.

---

## 1. 사용 위치

| 구분 | 경로 | 용도 |
|------|------|------|
| 인트로 애니메이션 | `frontend/components/portfolio-landing/IntroAnimation.tsx` | 태그라인 **글씨 쓰기** 진행률 애니메이션, 깃털 펜 위치 보간 |

- **의존성**: `package.json` — `gsap: ^3.14.2`
- **역할**: 인트로 화면에서 `"한 줄의 코드가 세상을 바꾼다"` 문구가 **한 획씩 쓰여지는 것처럼** 보이도록 **진행률(0→1)** 을 GSAP로 제어합니다.

---

## 2. 구현 요약

### 2.1 GSAP로 하는 일

- **진행률 애니메이션**  
  `progressRef.current.p`를 `0` → `1`로 **2초 동안** `ease: "none"`으로 선형 이동.
- **두 가지 모드**
  1. **Path 모드** (opentype.js로 폰트 경로 생성 성공 시)  
     - SVG path 상의 현재 위치를 `getPointAtLength(progress * length)`로 계산.  
     - **onUpdate**에서 매 프레임마다:
       - `setProgress(p)` 로 리액트 상태 동기화
       - path 위의 점을 구한 뒤, 그 점을 기준으로 **깃털 펜(penRef)** 의 `left`/`top`을 업데이트
       - 펜 위치는 `PEN_SMOOTH`(0.14)로 **부드럽게 따라가도록** 보간
     - 글자 노출은 `<clipPath>`의 `width`를 `progress * (bbox 폭)`으로 넓혀서 “쓰여지는” 효과.
  2. **Fallback 모드** (path 미사용 시)  
     - `gsap.to(progressRef.current, { p: 1, ... })` 로 진행률만 애니메이션.  
     - 글자 노출은 `clipPath: inset(0 (1-progress)*100% 0 0)` 형태로 처리.

- **정리**  
  - **타임라인 제어**: GSAP  
  - **진행률에 따른 시각 요소**: React state(`progress`) + clipPath / path 좌표  
  - **펜 위치 보간**: GSAP onUpdate 내부에서 매 프레임 계산 후 DOM 직접 갱신.

### 2.2 연동된 요소

- **opentype.js**: `NanumBrushScript-Regular.ttf` 로 태그라인 텍스트의 SVG path 생성 → path 길이·좌표 제공.
- **Framer Motion**: 인트로 전체 컨테이너·이름·밑줄의 등장/퇴장(opacity, y, scaleX)은 **Framer Motion**으로 처리. GSAP는 **쓰기 진행률과 펜 위치**만 담당.

---

## 3. 코드 상 참고 위치

| 내용 | 위치 (IntroAnimation.tsx) |
|------|---------------------------|
| GSAP progress 애니메이션 (path 모드) | `gsap.to(progressRef.current, { p: 1, duration: WRITE_DURATION, onUpdate: ..., onComplete: finish })` (path 분기) |
| GSAP progress 애니메이션 (fallback) | `gsap.to(progressRef.current, { p: 1, duration: WRITE_DURATION, onUpdate: () => setProgress(...), onComplete: finish })` |
| 클린업 | 각 분기에서 `return () => { tween.kill(); }` |
| 상수 | `WRITE_DURATION = 2`, `PEN_SMOOTH = 0.14` |

---

## 4. 참고

- 포트폴리오 랜딩의 **그 외 애니메이션**(섹션 등장, 네비게이션, 프로젝트 카드 등)은 **Framer Motion**으로 구현되어 있습니다.  
- 전체 구현 현황은 [전체-프로젝트-구현현황.md](전체-프로젝트-구현현황.md), 프론트 구조는 [frontend.md](frontend.md)를 참고하면 됩니다.
