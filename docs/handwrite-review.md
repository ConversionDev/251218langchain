# IntroAnimation GSAP 버전 검토

제공해주신 코드(anime → GSAP, stroke-dashoffset 도입) 검토 요약.

---

## 잘된 점

1. **stroke-dashoffset으로 실제 “그리기”**  
   clipPath 대신 path의 `strokeDasharray` / `strokeDashoffset` 을 쓰면, 글씨 진행과 깃털 위치를 **같은 progress** 로 맞출 수 있어서 방향이 맞음.

2. **GSAP으로 progress 동기화**  
   `strokeDashoffset` 애니메이션의 `onUpdate` 에서 `getPointAtLength` 로 깃털 위치를 갱신하면, reveal와 깃털이 한 타임라인으로 묶임.

3. **ref로 펜 위치만 갱신**  
   매 프레임 `setState` 하지 않고 `penRef.current.style.left/top` 만 바꾸면 리렌더 비용이 줄어듦.

4. **FeatherPenSVG를 감싼 div에 left/top**  
   `penRef` 로 감싸고 그 div에 `left/top` 을 주고, `FeatherPenSVG` 에는 `left={0}` 을 주는 구조는 타당함.

---

## 반드시 고칠 점

### 1. 깃털 위치 좌표 단위 (치명적)

`getPointAtLength` 의 `pt.x`, `pt.y` 는 **path(SVG viewBox) 좌표**입니다.  
지금처럼 그대로 `px` 로 쓰면, viewBox 범위(수백 단위)가 그대로 픽셀처럼 들어가서 **깃털이 화면 밖으로 나가거나 잘못된 위치**에 그려집니다.

**해야 할 것:** viewBox ↔ 컨테이너 픽셀 비율로 변환.

```ts
// onUpdate 안에서
const pt = pathRef.current.getPointAtLength(progress * length);
const bbox = pathData.bbox; // pathData는 effect 클로저에서 참조 가능해야 함
const w = bbox.x2 - bbox.x1;
const h = bbox.y2 - bbox.y1;

// 컨테이너 픽셀: textRef.current 또는 wrapper ref로 너비·높이 사용
const containerW = textRef.current?.offsetWidth ?? textWidth;
const containerH = textRef.current?.offsetHeight ?? 200; // 또는 실제 측정

const nibX_px = w > 0 ? ((pt.x - bbox.x1) / w) * containerW : 0;
const nibY_px = h > 0 ? ((pt.y - bbox.y1) / h) * containerH : 0;

penEl.style.left = `${nibX_px - PENCIL_W * Math.cos(angleRad)}px`;
penEl.style.top = `${nibY_px}px`;
```

- `pathData` 는 effect 의존성에 넣거나, ref 로 넣어두고 위처럼 bbox 를 써서 변환해야 함.
- `textWidth` 말고도 **높이**가 필요하면 `textRef.current.offsetHeight` 또는 wrapper ref 로 높이를 쓰면 됨.

### 2. 폰트 미로드 시 fallback 없음

`pathData` 가 null 이면:

- `taglinePathSvg` 가 null → **문장이 아예 안 그려짐**
- effect 에서 `!pathRef.current` 이라 바로 return → **애니메이션도 안 돌아감**

지금처럼 **path 모드만** 두면, TTF 로드 실패 시 인트로 문장과 쓰기 연출이 둘 다 사라짐.

**해야 할 것:**

- `pathData === null` 일 때는 기존처럼 **일반 `<p>` + clipPath reveal** 를 그리거나,
- path 모드가 아닐 때만 **간단한 progress(0→1) 애니메이션** (예: GSAP 또는 setState 한 번에 한 번) 으로 clipPath 만 움직이도록 fallback 유지.

---

## 추가로 보면 좋은 점

### 3. stroke만 쓰면 “톱날”처럼 보일 수 있음

지금 제안하신 것처럼 `fill="none"` + `stroke="#ffffff"` 만 쓰면, path 가 글자 **윤곽선**이라서 stroke 두께만큼만 선이 그려져 **속이 비어 보일** 수 있음.  
원하면:

- **stroke만** 쓰고 두께를 키우거나,
- **stroke로 그리기 연출**만 하고, **같은 path를 fill 로 한 번 더 그려서** 위에 겹쳐 “채워진 글자”처럼 보이게 하는 식으로 조정 가능.

### 4. FeatherPenSVG 의 top 정렬

`FeatherPenSVG` 내부에 `top: "50%"` 가 있어서, `penRef` div 에 `top` 만 줘도 “nib 기준”으로는 세로가 반쯤 어긋날 수 있음.  
필요하면 `FeatherPenSVG` 에 `top` prop 을 넘기거나, wrapper 에 `transform: translateY(-50%)` 같은 걸로 촉 위치를 맞추면 됨. (좌표 변환을 먼저 맞춘 뒤에 조정해도 됨.)

### 5. cleanup

GSAP 트윈은 effect return 에서 `kill()` 해 주는 게 안전함.

```ts
const tween = gsap.to(pathEl, { ... });
return () => { tween.kill(); };
```

---

## 요약

| 항목 | 상태 | 조치 |
|------|------|------|
| stroke-dashoffset + GSAP | 좋음 | 유지 |
| 깃털 위치 pt.x / pt.y | 버그 | viewBox → 픽셀 변환 (bbox + container 크기) |
| pathData null 시 | 누락 | clipPath fallback 또는 단순 progress 애니 메이션 추가 |
| stroke만 쓰는 연출 | 선택 | 필요 시 fill 병행 또는 stroke 두께 조정 |
| GSAP cleanup | 권장 | effect return 에서 tween.kill() |

**적용 순서 제안:**  
1) 깃털 좌표를 **반드시** viewBox → 픽셀 변환하도록 수정,  
2) **pathData null** 일 때 fallback(문장 표시 + 최소한의 쓰기 연출) 유지,  
3) 그 다음 stroke/fill 비주얼과 cleanup 정리.

이렇게 반영한 뒤에 코드 적용하시면 됩니다.
