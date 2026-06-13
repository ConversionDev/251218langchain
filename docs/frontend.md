# 프론트엔드

라우트·플로우, 상태 관리, **백엔드 API 매핑**, 그리고 포트폴리오 인트로의 **GSAP 붓글씨 연출**을 정리합니다.

도메인별 구현 현황은 [IMPLEMENTATION.md](IMPLEMENTATION.md), 시스템 구조는 [ARCHITECTURE.md](ARCHITECTURE.md) 참고.

---

## 1. 기술 스택·구조

- **프레임워크**: Next.js (App Router), TypeScript
- **스타일**: Tailwind CSS, 다크 모드(테마 스크립트 + `dark` 클래스)
- **상태**: Zustand(`useStore`, `useDemoRoleStore`). 서버 상태는 fetch 기반
- **공통**: Toaster(sonner), PWA(RegisterSw), RoleSwitcher(우측 하단 데모 역할)
- **API 베이스**: `NEXT_PUBLIC_API_URL ?? "http://localhost:8000"`

> 렌더링은 **CSR 중심의 Next.js App Router 하이브리드 웹앱**. 클라이언트 컴포넌트 위주로 대시보드·채팅을 구성.

---

## 2. 라우트·레이아웃

| 영역 | 경로 | 비고 |
|------|------|------|
| 메인 | `/`, `/login`, `/signup`, `/demo` | 랜딩, 데모 역할 선택 |
| 채용 | `/careers`, `/careers/recruit`, `/apply`, `/resumes` | 지원·지원내역 |
| 직원 포털 | `/workspace`, `/workspace/submit`, `/workspace/mail`, `/workspace/my-activities` | 업무 제출·메일(샘플)·내 활동 |
| 관리자 | `/(dashboard)/dashboard`, `/chat`, `/data-map`, `/core/new-hires`, `/core/employees`, `/performance/*`, `/risk`, `/intelligence`, `/credential`, `/settings` | 사이드바 메뉴 |

- **워크스페이스 메일**(`/workspace/mail`): UI만 구현, **백엔드 미연동**(샘플 데이터). 백엔드 `/api/mail/receive`·list·filter는 구현됨.
- **공용 헤더**: `min-h-[4.5rem]`, 민트 계열(#e8f5ef, #a8d5c4) 통일.

---

## 3. 프론트–백엔드 API 매핑

| 프론트 호출 | 백엔드 경로 | 메서드 |
|------------|-------------|--------|
| fetchEmployees(Paginated), fetchNextEmployeeId, checkResumeHashApi, create/update/deleteEmployeeApi, analyzeEmployeeResumeApi, refreshEmployeeEmbeddingsApi, backfillEmployeeProfilesApi | `/api/employees`, `/next-id`, `/check-resume-hash`, `/{id}`, `/embedding`, `/profile-backfill` | GET/POST/PUT/DELETE |
| fetchActivityRecords, fetchActivitiesByEmployee, fetchActivityById, fetchMyActivities, submitActivity | `/api/activity-records`, `/by-employee/{id}`, `/my`, `/submit` | GET/POST |
| uploadChatFiles, getThreadHistory, deleteThread, sendChatMessageStream | `/api/agent/upload`, `/threads/{id}/history`, `/chat/stream` | GET/POST/DELETE |
| analyzeResumeFile | `/api/resume/analyze` | POST (FormData key `file`) |
| 감사 로그 | `/api/audit/logs?limit=&action=&entityId=` | GET |
| 클러스터 맵 | `/api/clustering/map?theme=` | GET |

**결론**: 직원·활동·채팅·이력서·감사·데이터 지도는 경로·메서드·쿼리/바디·camelCase **매핑 일치**.

### 백엔드에만 있고 프론트 미사용

- `/api/mail/receive`, `/api/mail/filter`, 목록·단건 — 구현됨이나 워크스페이스 메일은 샘플만 사용.
- `/api/disclosure/*` — 공시; 프론트 직접 호출 여부 별도 확인.

---

## 4. 현재 상황 요약

| 구분 | 내용 |
|------|------|
| 인증 | 실제 로그인/세션은 Spring Gateway(OAuth+JWT). 데모는 역할만 선택해 영역 이동. |
| 워크스페이스 메일 | UI만(폴더·목록·읽기·쓰기). 전송/수신 샘플, `/api/mail` 미호출. |
| 회원가입/로그인 | 폼·유효성 위주. |

---

## 5. 포트폴리오 인트로 — GSAP 붓글씨 연출

메인 페이지(`/`) 인트로에서 **"한 줄의 코드가 세상을 바꾼다"** 문구가 깃털펜으로 **한 획씩 쓰여지는** 효과.

### 5.1 목표

- 깃털이 연필 역할을 하며 글자가 **그려지면서 나타나는** 느낌(이미 써진 글자 위를 지나가는 것이 아님).

### 5.2 구현 구조

```
텍스트 "한 줄의 코드가 세상을 바꾼다"
  → opentype.js (single path 변환)
  → SVG path(fill) + clipPath(progress) 로 좌→우 reveal
  → getPointAtLength(progress) 로 깃털 위치 계산
  → GSAP progress 0→1 (2초, ease none)
```

- **opentype.js**: `NanumBrushScript-Regular.ttf` 로드 → `font.getPath(문장)` → SVG path `d` 생성. 문장 전체를 **path 하나(single path)**로 유지해 깃털 동기화 난이도를 낮춤.
- **GSAP**: `progressRef.current.p`를 0→1로 애니메이션. `onUpdate`마다 path 위 점(`getPointAtLength`)을 구해 깃털 위치를 `PEN_SMOOTH`(0.14)로 보간하며 DOM 직접 갱신(리렌더 비용 절감).
- **reveal**: `<clipPath>` rect width를 `progress` 비율만큼 넓혀 글자 노출.
- **Framer Motion**: 인트로 컨테이너·이름·밑줄의 등장/퇴장 transition 담당. GSAP는 쓰기 진행률·펜 위치만.
- **Fallback**: 폰트 미로드 시 path 모드 대신 clipPath 텍스트 + 단순 progress 애니메이션 유지.

### 5.3 구현 시 핵심 이슈 (검토에서 도출)

- **좌표 단위 변환(치명적)**: `getPointAtLength`의 `pt.x/pt.y`는 **SVG viewBox 좌표**. 그대로 px로 쓰면 깃털이 화면 밖으로 나감 → bbox + 컨테이너 픽셀 크기 비율로 변환 필요.
- **stroke vs fill**: path가 윤곽선이라 stroke만 주면 속이 비어 톱날처럼 보임 → fill로 채우고 reveal만 clipPath(또는 stroke-dashoffset)로 처리.
- **Y축 반전**: opentype 좌표(Y↑)와 SVG viewBox(Y↓)를 `scale(1,-1)`로 맞추면 글자가 뒤집힘 → transform 제거하고 viewBox만으로 배치.
- **cleanup**: GSAP 트윈은 effect return에서 `tween.kill()`.

### 5.4 참고 파일

| 파일 | 역할 |
|------|------|
| `frontend/components/portfolio-landing/IntroAnimation.tsx` | opentype 로드, path 생성, SVG + clipPath, GSAP progress, 깃털 위치 |
| `frontend/components/portfolio-landing/FeatherPenSVG.tsx` | 깃털 SVG (`left`/`width`/`visible` props) |
| `frontend/public/fonts/NanumBrushScript-Regular.ttf` | path 생성용 폰트 |

> 포트폴리오 랜딩의 그 외 애니메이션(섹션 등장·네비·프로젝트 카드)은 Framer Motion으로 구현.
