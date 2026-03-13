# 인트로 Lottie 적용 방법

인트로 화면의 깃털+밑줄 애니메이션을 **Lottie**로 바꾸면 디자이너가 만든 연출을 그대로 쓸 수 있고, 더 자연스럽게 보입니다.

## 흐름

```
After Effects (애니 제작)
        ↓
Bodymovin 플러그인 (JSON 내보내기)
        ↓
feather.json
        ↓
React (lottie-react) 재생 → 한 번만 재생 후 onComplete
```

---

## 1. After Effects에서 애니메이션 만들기

1. **참고 이미지**: `frontend/components/portfolio/깃털만.png`, `깃털붓.png`  
   - 깃털 펜 + 펜촉에서 나오는 **빛 줄기(밑줄)** 를 벡터/도형으로 재구성합니다.
2. **구성 제안**
   - 레이어 1: 깃털 펜 (이미지 또는 벡터)
   - 레이어 2: 빛 나는 푸른 선(밑줄) — 왼쪽이 두껍고 밝고, 오른쪽으로 갈수록 얇고 흐려지게
3. **타이밍**: 약 2~3초 분량 (인트로가 너무 길지 않게).
4. **캔버스**: 가로 400~600px, 세로 100~200px 정도면 충분 (태그라인 영역에 맞춤).
5. **배경**: 투명 유지 (알파 채널).

---

## 2. Bodymovin으로 Lottie JSON 내보내기

1. [Bodymovin](https://aescripts.com/bodymovin/) (After Effects용 플러그인) 설치.
2. AE에서 **Window → Extensions → Bodymovin** 실행.
3. 컴포지션 선택 후 **Export** (또는 Render).
4. 생성된 JSON 파일을 **이름을 `feather.json`으로** 저장.

---

## 3. 프로젝트에 JSON 넣기

내보낸 `feather.json`을 아래 경로에 넣습니다.

```
frontend/public/lottie/feather.json
```

- 이 경로에 **레이어가 1개 이상 있는** Lottie JSON이 있으면 → 인트로가 **Lottie 모드**로 동작합니다.
- 파일이 없거나 `layers`가 비어 있으면 → 기존 PNG 기반 인트로가 그대로 재생됩니다.

**기본 포함:** 프로젝트에는 **미리 만든 Lottie 스타일 JSON**이 들어 있습니다.  
- 테일(#22d3ee) 색의 **밑줄이 그려지는** Trim Path 애니메이션(약 1.5초)이 재생됩니다.  
- AE에서 깃털+빛 줄기를 만들어 내보내면, 이 파일만 교체하면 됩니다.

---

## 4. React 쪽 동작 (이미 구현됨)

- `IntroAnimation`이 `/lottie/feather.json`을 불러옵니다.
- 로드된 JSON에 `layers`가 있으면:
  - 이름 "강경구", 구분선, 태그라인 "한 줄의 코드가 세상을 바꾼다"는 **React로 그대로** 표시하고,
  - **깃털+밑줄만** Lottie로 재생합니다.
- `loop={false}`, 재생이 끝나면 `onComplete()`가 호출되어 인트로가 닫힙니다.

**코드 위치**: `frontend/components/portfolio-landing/IntroAnimation.tsx`

---

## 5. 참고

- **텍스트는 Lottie에 넣지 말고 React에서만** 쓰는 것을 권장합니다. (한글/폰트 이슈 방지)
- Lottie 파일이 커지면 `public` 대신 동적 import로 JSON을 불러와도 됩니다.
- 수정이 필요하면 AE에서 다시 만든 뒤, `feather.json`만 교체하면 됩니다.
