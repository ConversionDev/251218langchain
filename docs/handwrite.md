# 붓글씨(손글씨) 인트로 연출 — 전략·구현 정리

인트로 문장 **"한 줄의 코드가 세상을 바꾼다"** 가 깃털펜으로 쓰여지는 것처럼 보이는 효과를 위한 작업 정리.

---

## 1. 목표

- **깃털이 연필 역할**을 하며, 글자가 **그려지면서 나타나는** 느낌
- 글자 위를 깃털이 따라가며 쓰는 연출 (단순히 이미 써진 글자 위를 지나가는 것이 아님)

---

## 2. 시도한 전략

| 단계 | 방식 | 내용 |
|------|------|------|
| 1 | **clipPath + 선형 progress** | 텍스트는 `<p>` 그대로 두고, `clipPath: inset(0, clipRight%, 0, 0)` 로 좌→우 reveal. 깃털 위치는 `progress * textWidth` 로 선형 이동. **가장 단순**하지만 "쓰여지는" 느낌은 약함. |
| 2 | **텍스트 → SVG path + stroke-dashoffset** | 폰트를 path로 변환 후 `stroke-dashoffset` 으로 "선이 그려지는" 효과. **웹에서 손글씨 효과의 정석**에 가까운 방식. |
| 3 | **path + stroke만 쓰면** | path가 글자 **윤곽선**이라 stroke만 주면 속이 비어 톱날처럼 보임 → **실제 채움은 fill로**, reveal만 clipPath로 처리하도록 변경. |
| 4 | **path 구조** | 문장 전체를 **path 하나**로 유지 (`font.getPath(문장)` 한 번). 글자마다 path 여러 개로 나누면 stroke 순서·깃털 동기화가 훨씬 복잡해지므로, **single path** 로 난이도 확 낮춤. |
| 5 | **Y축 반전 제거** | opentype 좌표(Y 위로 증가) ↔ SVG viewBox(Y 아래로 증가) 맞추려고 `scale(1,-1)` 등 transform을 쓰면 **글자가 뒤집혀 보이는** 문제 발생 → transform 제거하고 viewBox만으로 배치. |

---

## 3. 설치한 라이브러리·리소스

| 항목 | 용도 |
|------|------|
| **animejs** (`^4.3.6`) | 쓰기 진행률 `progress` 0→1 애니메이션 (duration, cubicBezier 이징). 깃털 위치·clipPath reveal 모두 이 progress 기반. |
| **opentype.js** (`^1.3.4`) | TTF 폰트 로드 후 **텍스트 → SVG path** 변환. `font.getPath(text, x, y, fontSize)` → `path.toPathData()` 로 path `d` 문자열 생성. |
| **framer-motion** | 인트로 전체 fade out, 이름·구분선 등 등장 transition (기존 사용). |
| **Nanum Brush Script** | `public/fonts/NanumBrushScript-Regular.ttf` — opentype으로 로드해 path 생성용. 없으면 path 모드 비활성화, 기존 clipPath 텍스트만 사용. |

- 타입: `frontend/opentype.d.ts` 에 `opentype.js` 모듈 선언 추가.

---

## 4. 최종 구현 구조

- **진입:** `opentype.load("/fonts/NanumBrushScript-Regular.ttf")` 로 폰트 로드.
- **path 생성:** `font.getPath(\`"${TAGLINE}"\`, 0, 0, 72)` → `path.getBoundingBox()`, `path.toPathData(2)` → `pathData` (pathD, bbox) 저장.
- **렌더:**  
  - SVG `viewBox` = bbox.  
  - `<path d={pathData.pathD} fill="#ffffff" />` 로 **채운 글자** 표시.  
  - **clipPath** 로 `rect` width를 `progress` 비율만큼만 보이게 해서 **좌→우 reveal**.
- **깃털 위치:** `pathRef.current.getPointAtLength(progress * pathLength)` 로 path 위 한 점 구한 뒤, bbox와 `textWidth`로 픽셀 좌표로 변환 → `penLeft` 로 `FeatherPenSVG`에 전달.
- **progress 애니메이션:** anime.js `animate(progressRef.current, { p: 1, duration, ease, onUpdate })` → 매 프레임 `setProgress(progressRef.current.p)`.

정리하면:

```
텍스트 "한 줄의 코드가 세상을 바꾼다"
  → opentype.js (single path)
  → SVG path (fill) + clipPath(progress) 로 reveal
  → getPointAtLength(progress) 로 깃털 위치
  → anime.js progress 0→1
```

---

## 5. 현재 상태

- **동작:** 메인 페이지(`/`) 인트로에서, 폰트 로드 성공 시 **path 모드**로 문장이 좌→우로 드러나며 깃털이 그 진행에 맞춰 이동. 폰트 미로드 시 **fallback** 으로 기존 clipPath 텍스트 방식만 사용.
- **난이도:** path 하나 + clipPath reveal + getPointAtLength 조합으로, 웹 애니메이션 기준 **중급** 수준 구현.

**알려진 한계**

- reveal은 **clipPath(직선 좌→우)** 이고, 깃털 위치는 **path의 실제 길이 기준 getPointAtLength** 라서, path가 굴곡지면 **진행도가 아주 조금 어긋나 보일 수 있음**.
- 이후 **stroke-dashoffset** 으로 “그리는” 진행과 `getPointAtLength` 를 같은 progress로 맞추면, 깃털 위치와 글씨 진행이 완전히 일치함.

---

## 6. 참고 파일

| 파일 | 역할 |
|------|------|
| `frontend/components/portfolio-landing/IntroAnimation.tsx` | 인트로 전체: opentype 로드, path 생성, SVG path + clipPath, anime progress, 깃털 위치. |
| `frontend/components/portfolio-landing/FeatherPenSVG.tsx` | 깃털 SVG, `left`/`width`/`visible` props. |
| `frontend/public/fonts/NanumBrushScript-Regular.ttf` | path 생성용 폰트 (Google Fonts에서 다운로드 후 배치). |
| `frontend/public/fonts/README.md` | 폰트 다운로드·배치 안내. |
