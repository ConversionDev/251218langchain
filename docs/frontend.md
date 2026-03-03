# 프론트엔드 — 플로우·상태·API 매핑

프론트엔드 기술 스택, 라우트·플로우, **백엔드 API 매핑**을 한 문서에 통합했습니다.

---

## 1. 기술 스택·구조

- **프레임워크**: Next.js (App Router), TypeScript
- **스타일**: Tailwind CSS, 다크 모드(테마 스크립트 + `dark` 클래스)
- **상태**: Zustand (useStore, useDemoRoleStore), 서버 상태는 fetch 기반
- **공통**: Toaster(sonner), PWA(RegisterSw), RoleSwitcher(우측 하단 데모 역할)
- **API 베이스**: `NEXT_PUBLIC_API_URL ?? "http://localhost:8000"` (배포 시 환경에 맞게 설정)

---

## 2. 라우트·레이아웃 요약

| 영역 | 경로 | 비고 |
|------|------|------|
| 메인 | `/`, `/login`, `/signup`, `/demo` | 랜딩, 데모 역할 선택 |
| 채용 | `/careers`, `/careers/recruit`, `/apply`, `/resumes` | 지원·지원내역 |
| 직원 포털 | `/workspace`, `/workspace/submit`, `/workspace/mail`, `/workspace/my-activities` | 업무 제출·메일(샘플)·내 활동 |
| 관리자 | `/(dashboard)/dashboard`, `/chat`, `/data-map`, `/core/new-hires`, `/core/employees`, `/performance/*`, `/risk`, `/intelligence`, `/credential`, `/settings` | 사이드바 메뉴 |

- **워크스페이스 메일** (`/workspace/mail`): UI만 구현, **백엔드 미연동**(샘플 데이터). 백엔드 `/api/mail/receive`, list, filter는 구현됨.
- **공용 헤더**: `min-h-[4.5rem]`, 민트 계열(#e8f5ef, #a8d5c4) 통일.

---

## 3. 프론트–백엔드 API 매핑 (일치함)

| 프론트 호출 | 백엔드 경로 | 메서드 | 비고 |
|------------|-------------|--------|------|
| fetchEmployees, fetchEmployeesPaginated, fetchNextEmployeeId, checkResumeHashApi, createEmployeeApi, updateEmployeeApi, deleteEmployeeApi, analyzeEmployeeResumeApi, refreshEmployeeEmbeddingsApi, backfillEmployeeProfilesApi | `/api/employees`, `/api/employees/next-id`, `/api/employees/check-resume-hash`, `/api/employees/{id}`, `/api/employees/embedding`, `/api/employees/profile-backfill` | GET/POST/PUT/DELETE | 쿼리·Body camelCase 일치 |
| fetchActivityRecords, fetchActivitiesByEmployee, fetchActivityById, fetchMyActivities, submitActivity | `/api/activity-records`, `/api/activity-records/by-employee/{id}`, `/api/activity-records/my`, `/api/activity-records/submit` | GET/POST | textType, employeeId 등 일치 |
| uploadChatFiles, getThreadHistory, deleteThread, sendChatMessageStream | `/api/agent/upload`, `/api/agent/threads/{id}/history`, `/api/agent/chat/stream` | GET/POST/DELETE | FormData key `files`, 스트리밍 |
| analyzeResumeFile | `/api/resume/analyze` | POST | FormData key `file` |
| 감사 로그 | `/api/audit/logs?limit=&action=&entityId=` | GET | 일치 |
| 클러스터 맵 | `/api/clustering/map?theme=` | GET | 일치 |

**결론**: 직원·활동·채팅·이력서·감사·데이터 지도 → 경로·메서드·쿼리/바디·camelCase **매핑 일치**.

---

## 4. 백엔드에만 있고 프론트 미사용 API

- **/api/mail/receive**, **/api/mail/filter**, 목록·단건 등 — 구현됨. 워크스페이스 메일 페이지는 아직 호출하지 않고 샘플만 사용.
- **/api/disclosure/\*** — 공시; 프론트 직접 호출 여부는 별도 확인.

---

## 5. 현재 상황 요약

| 구분 | 내용 |
|------|------|
| 인증 | 실제 로그인/세션 없음. 데모는 역할만 선택해 해당 영역으로 이동. |
| 워크스페이스 메일 | UI만(폴더·목록·읽기·쓰기). 전송/수신은 샘플, `/api/mail` 미호출. |
| 회원가입/로그인 | 폼·유효성만, 실제 인증 API 미연동. |

세부 라우트 트리·플로우는 이 문서에 통합해 두었습니다. 코드 상세는 `frontend/` 모듈과 [implementation-status.md](implementation-status.md)를 참고하면 됩니다.
