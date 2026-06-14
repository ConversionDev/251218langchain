# 전체 기능 목록

프로젝트의 **전체 기능**을 **에이전트(Agent) 핵심 기능**과 **플랫폼·세부 기능**으로 분류합니다.

- **에이전트**: LLM·LangGraph·MCP 등으로 **추론·판정·생성**을 수행하는 기능 (도구 호출, RAG, 증거 수집+판정, 멀티스텝 오케스트레이션 포함)
- **플랫폼**: CRUD·조회·인증·UI·오프라인 학습 등 에이전트가 아닌 인프라·업무 기능

상태: **구현됨** / **부분** / **스텁** / **미구현** · 프론트: **연동** / **미연동** / **데모**

관련 문서: [ARCHITECTURE.md](ARCHITECTURE.md) · [IMPLEMENTATION.md](IMPLEMENTATION.md) · [FRONTEND.md](FRONTEND.md) · [MODEL_COMPARISON.md](MODEL_COMPARISON.md)

---

## 1. 에이전트 핵심 기능 (메인)

플랫폼의 차별화 축. LangGraph·MCP·RAG·환경별 LLM(EXAONE / Gemini / LLaMA)을 조합합니다.

### 1.1 HR 채팅 에이전트 (LangGraph + RAG)

| 구분 | 내용 | 상태 | 프론트 |
|------|------|------|--------|
| **메인** | 자연어 HR 질의 → RAG·도구·LLM 스트리밍 답변 | 구현됨 | 연동 (`/chat`) |

**세부 기능**

- SSE 스트리밍 채팅 (`POST /api/agent/chat/stream`)
- RAG 벡터 검색 — disclosures · competency_anchors · employees (pgvector HNSW)
- 키워드 기반 도구 라우팅 — `_build_forced_tool_calls` (1턴 LLM 1회 최적화)
- 도구: `get_hr_summary`, `list_employees`, `get_employee_info`, `get_employee_performance`, `search_documents`
- 첨부 업로드 — 이미지·PDF·Word·Excel (`POST /api/agent/upload`)
- 멀티모달 — 이미지 첨부 시 Gemini 분석
- 스레드 이력·삭제 (`/api/agent/threads/{id}`)
- 프로바이더·도구 목록·헬스 (`/api/agent/providers`, `/tools`, `/health`)
- MCP Chat 스포크 경유 (허브 → `/internal/mcp/chat`)
- 런타임: 로컬 EXAONE(GPU) / 배포 llama.cpp GGUF(CPU)

---

### 1.2 스팸 분류·에스컬레이션 에이전트

| 구분 | 내용 | 상태 | 프론트 |
|------|------|------|--------|
| **메인** | 수신·테스트 메일 스팸/햄 판정 + 애매한 케이스 LLM 재판정 | 구현됨 | 연동 (`/workspace/mail` 테스트·수신) |

**세부 기능**

- 1차 분류 — **환경별 분기**(`SPAM_CLASSIFIER`): 로컬 = 학습 LLaMA 3 SFT 스팸 어댑터(GPU), 배포 = Gemini(`gemini-2.5-flash`, CPU에서 무거운 LLaMA 미로드). 동일 스키마 반환(`classify_spam_by_env`)
- 수신 즉시 분류 — Mailgun 웹훅·`POST /api/mail/receive`의 BackgroundTask에서 **등록 수신자(owner 해석된)만** 분류 → folder=spam/inbox, 미등록 수신자는 rejected(사용자 메일함 비노출). 별도 워커 불요(rag-api 인라인)
- 라우팅 정책 — LLaMA 결과 시 `routing_strategy=rule` 고정 (ExaOne policy 덮어쓰기 방지)
- 에스컬레이션 — 애매한 메일만 "증거 수집 + LLM 판정" (tool-calling 미사용)
  - 증거: LLaMA 결과 + 규칙 + EXAONE 심층분석
  - 로컬 judge: EXAONE (`SPAM_AGENT_LLM=auto`)
  - 배포 judge: Gemini raw SDK (`SPAM_AGENT_LLM=gemini`)
- 스팸 필터 API (`POST /api/mail/filter`) — action·routing_path·reason_codes 반환
- MCP Spam 스포크 + `/internal/llama/classify_spam`
- 분류 실패 시 안전 폴백 — 기존 판정 유지 또는 inbox 기본 저장

---

### 1.3 이력서·Success DNA 분석 에이전트

| 구분 | 내용 | 상태 | 프론트 |
|------|------|------|--------|
| **메인** | 이력서 원문 → LLM 분석 → **5대 역량 0–100점** 산출 | 구현됨 | 연동 (`/apply`, `/core/new-hires`) |

**세부 기능**

- 문서 추출 — PDF / TXT / Word / HWP
- 역량 점수 — 리더십 · 기술력 · 창의성 · 협업 · 적응력 (Success DNA)
- 프로필 필드 — name, jobTitle, department, email 등
- API — `POST /api/resume/analyze`, `POST /api/employees/{id}/analyze`
- 세션 캐시 — 동일 파일 재업로드 시 즉시 반환 (프론트)
- EXAONE 역량 LoRA 어댑터(competency_adapters) 연동

---

### 1.4 메일 성과·역량 분류 에이전트 (학습 EXAONE, 비동기)

| 구분 | 내용 | 상태 | 프론트 |
|------|------|------|--------|
| **메인** | 발송 메일 → 학습 EXAONE 비동기 분류 → 5대 역량 태깅·성과 기록·모델 배지 | 구현됨 | 연동 (보낸함 배지) |

**세부 기능**

- 트리거 — 메일 발송(`POST /api/mail/send`) 후 BackgroundTask. 발송은 즉시 반환, 분류는 백그라운드 → UX 안 막힘
- 분류기 — **직접 파인튜닝한 EXAONE competency 어댑터**(로컬 GPU 3~4s / 배포 GGUF CPU). 취업 쇼케이스 목적상 Gemini로 대체하지 않음
- 결과 저장 — 메일 행 `ai_result_raw`(JSON: model·is_performance·competency_labels) → 프론트 보낸편지함에 **역량 라벨 + "EXAONE 파인튜닝" 배지**(4초 폴링 자동 반영)
- 성과 기록 — `run_email_classify_and_record` → 성과 판단 시 `performance_records` 기록 + 5대 역량 태깅
- 실패 시 `ai_status=FAILED`만, 발송 메일엔 영향 없음
- 모델 비교 근거 — [MODEL_COMPARISON.md](MODEL_COMPARISON.md) (학습 EXAONE vs Gemini flash-lite 실측)

---

### 1.5 공시 기여도 예측 에이전트 (RAG + LLM)

| 구분 | 내용 | 상태 | 프론트 |
|------|------|------|--------|
| **메인** | 이름·직급·부서 등 → RAG + LLM → 공시 적합도·제안 | 구현됨 | 미연동 |

**세부 기능**

- 동기 예측 — `POST /api/disclosure/check`
- 비동기 예측 — job_id 발급 → `GET /api/disclosure/check/result/{job_id}` 폴링
- 적재 상태 — `GET /api/disclosure/status` (document/embedded 비율)
- 공시 ingest 파이프라인 — CLI (`disclosure_orchestrator`)
- 임베딩 일괄 실행 — `POST /api/disclosure/embedding/run`

---

### 1.6 직무 전환·역량 인텔리전스 (채팅 에이전트 연동)

| 구분 | 내용 | 상태 | 프론트 |
|------|------|------|--------|
| **메인** | Success DNA·IFRS 지표 기반 직무 전환 분석 + AI 내러티브 | 부분 | 연동 (`/intelligence`) |

**세부 기능**

- Success DNA 방사형·성장 추이·궤적 차트 (직원 데이터)
- 직무 전환 적합도·스킬 갭 (disclosureMetrics 기반 클라이언트 계산)
- AI 전환 분석 — 채팅 스트림 API로 프롬프트 전송·응답 파싱 (전용 백엔드 API 없음)

---

### 1.7 MCP 중앙 허브 (에이전트 오케스트레이션)

| 구분 | 내용 | 상태 | 프론트 |
|------|------|------|--------|
| **메인** | Chat·Spam 요청을 스타 토폴로지로 위임 | 구현됨 | 미연동 (내부) |

**세부 기능**

- `/mcp` FastMCP 허브 마운트
- Chat MCP / Chat Spoke — `/internal/mcp/chat`, `chat-spoke`
- Spam MCP 위임 — `classify_spam`, `analyze_email`
- Hub 내부 LLM API — `/internal/llama/*`, `/internal/exaone/*`
- 스포크 간 직접 통신 금지, HTTP 클라이언트 단방향 호출

---

## 2. 플랫폼 기능 (에이전트 외)

### 2.1 인사·직원 (HCM / ATS)

| 기능 | 상태 | 프론트 |
|------|------|--------|
| 직원 목록·단건·생성·수정·삭제 | 구현됨 | 연동 |
| 페이지네이션·employmentType 필터 | 구현됨 | 연동 |
| 다음 ID 발급 (`/api/employees/next-id`) | 구현됨 | 연동 |
| 이력서 해시 중복 확인 | 구현됨 | 연동 |
| 직원 임베딩 갱신 (RAG용) | 구현됨 | 연동 |
| 프로필 백필 (dryRun·seed) | 구현됨 | 연동 |
| 감사 로그 자동 기록 (CRUD 시) | 구현됨 | (내부) |

**화면**: `/dashboard`, `/core/employees`, `/core/new-hires`, `/apply`, `/resumes`, `/careers/*`

---

### 2.2 성과·활동 (Performance)

| 기능 | 상태 | 프론트 |
|------|------|--------|
| 활동 목록·직원별·단건·내 활동 조회 | 구현됨 | 연동 |
| 업무 제출 (meeting / report / email) | 구현됨 | 연동 |
| 성과 대시보드·임팩트 차트 | 구현됨 | 연동 |
| IFRS 공시 모드·시뮬레이터·보드 리포트 미리보기 | 구현됨 | 연동 (클라이언트 집계) |

**화면**: `/performance`, `/performance/activities`, `/workspace/submit`, `/workspace/my-activities`

---

### 2.3 메일 시스템 (CRUD·수신·발송)

| 기능 | 상태 | 프론트 |
|------|------|--------|
| 메일 목록·단건 (folder·owner 필터) | 구현됨 | 연동 |
| 중요(별표) 폴더 — 폴더 무관 전용 쿼리(`folder=starred`) | 구현됨 | 연동 |
| 수신 API·Mailgun Webhook (HMAC·멱등) + 수신 즉시 스팸 분류 | 구현됨 | 연동 |
| 읽음·별표·수정·삭제(휴지통/영구) | 구현됨 | 연동 |
| 답장(Re: 인용)·전달(Fwd: 인용) | 구현됨 | 연동 |
| 임시저장(draft) — 저장·편집 로드·발송 시 제거 | 구현됨 | 연동 |
| 발송 (`/api/mail/send`) — 사내 DB(보낸함+받은함) / 외부 Mailgun, 발송 후 역량 분류 비동기 | 구현됨 | 연동 |
| 분류 트리거 — rag-api 인라인(수신=스팸, 발송=역량). 상시 워커 불요 | 구현됨 | — |
| AI 재처리 (`POST /api/mail/{id}/retry`) | 구현됨 | — |

> 수신자 게이트: 등록 주소(employees·internal_addresses)만 수신·분류, 미등록은 rejected. 메일함 소유자는 현재 프론트 직원ID 입력 기반(포트폴리오 단순화, 인증 미연동).

**화면**: `/workspace/mail`

---

### 2.4 사내 주소록

| 기능 | 상태 | 프론트 |
|------|------|--------|
| 통합 조회 (직원 + 공용함 + 그룹) | 구현됨 | 연동 |
| 공용·그룹 CRUD | 구현됨 | 연동 |

**화면**: `/workspace/address-book`, 메일 작성 수신자 선택

---

### 2.5 감사·리스크

| 기능 | 상태 | 프론트 |
|------|------|--------|
| 감사 로그 조회 (entity·action·actor·기간) | 구현됨 | 연동 |

**화면**: `/risk`

---

### 2.6 데이터 지도·시각화

| 기능 | 상태 | 프론트 |
|------|------|--------|
| 역량 클러스터 HTML 서빙 (`/api/clustering/map`) | 구현됨 | 연동 |
| competency_map.html 생성 (UMAP + K-Means) | 부분 (수동 스크립트) | — |
| 다크 테마 iframe 주입 | 구현됨 | 연동 |

**화면**: `/data-map`

---

### 2.7 자격 검증 (Credential)

| 기능 | 상태 | 프론트 |
|------|------|--------|
| Success DNA·공시 지표 기반 검증 플로우 UI | 구현됨 | 연동 (데모) |
| 블록체인 트랜잭션 시뮬레이션 | 구현됨 | 연동 (클라이언트) |

**화면**: `/credential` · 전용 백엔드 API 없음

---

### 2.8 인증·사용자 (Spring Gateway)

| 기능 | 상태 | 프론트 |
|------|------|--------|
| OAuth2 로그인 (카카오·네이버·구글) | 구현됨 | 부분 |
| JWT 발급·갱신 (`/api/auth/refresh`) | 구현됨 | — |
| 사용자 조회 (`/api/users/me` 등) | 구현됨 | — |
| Redis 세션/토큰 (Upstash) | 구현됨 | — |

**화면**: `/login`, `/signup` (폼·데모 역할 선택)

---

### 2.9 문서·지원 API

| 기능 | 상태 | 프론트 |
|------|------|--------|
| 지원 확장자 조회 (`/api/document/supported-extensions`) | 구현됨 | (간접) |
| 헬스·CORS·DB 마이그레이션 (`/health`, AUTO_MIGRATE) | 구현됨 | — |
| 임베딩 동기화 job (`run_embedding_sync_task`) | 스텁 | — |

---

### 2.10 ML 학습·배포 파이프라인 (오프라인)

런타임 에이전트가 아닌 **학습·변환·적재** 파이프라인입니다.

| 기능 | 상태 |
|------|------|
| EXAONE 역량 LoRA SFT (`competency_adapters`) | 구현됨 |
| LoRA 병합 → GGUF Q4_K_M CPU 배포 변환 | 구현됨 |
| LLaMA 스팸 SFT — ExaOne 합성 데이터(15종 스팸 + 7종 햄) | 구현됨 |
| 스팸 어댑터 파인튜닝·런타임 PEFT 로드 | 구현됨 |
| 공시 문서 ingest·임베딩 적재 | 구현됨 |
| 역량 클러스터 시각화 스크립트 | 구현됨 |
| 애매 케이스 필터·평가 (`ambiguous_case_filter`, `run_chat_eval`) | 구현됨 |

---

### 2.11 포트폴리오·랜딩 (프론트)

| 기능 | 상태 | 프론트 |
|------|------|--------|
| GSAP 붓글씨 인트로 (opentype + clipPath) | 구현됨 | 연동 |
| Framer Motion 랜딩·섹션 연출 | 구현됨 | 연동 |
| 데모 역할 스위처·PWA | 구현됨 | 연동 |
| 채용 FAQ·공지·문의 | 구현됨 | 연동 |

**화면**: `/`, `/demo`, `/contact`, `/careers/*`

---

### 2.12 모바일 (Flutter)

| 기능 | 상태 |
|------|------|
| Flutter 앱 스캐폴드 | 미구현 (스캐폴드만) |

---

## 3. 기능 맵 (요약)

```
[에이전트 핵심]
  1.1 HR 채팅 에이전트 ─── RAG + 도구 + SSE
  1.2 스팸·에스컬레이션 ── 1차 환경분기(로컬 LLaMA/배포 Gemini) + judge
  1.3 이력서·Success DNA ─ LLM 역량 분석
  1.4 메일 성과·역량 분류 ─ 발송 후 비동기 학습 EXAONE + 모델 배지
  1.5 공시 기여도 예측 ─── RAG + LLM
  1.6 직무 전환 인텔리전스 ─ 채팅 API 연동
  1.7 MCP 허브 ─────────── Chat/Spam 오케스트레이션

[플랫폼]
  2.1 인사·직원 (HCM/ATS)
  2.2 성과·활동
  2.3 메일 CRUD·Webhook
  2.4 주소록
  2.5 감사
  2.6 데이터 지도
  2.7 자격 검증 (데모)
  2.8 OAuth·JWT
  2.9 문서·헬스 API
  2.10 ML 학습·배포 (오프라인)
  2.11 포트폴리오·랜딩
  2.12 모바일 (스캐폴드)
```

---

## 4. 이력서용 한 줄 분류

| 분류 | 대표 기능 |
|------|-----------|
| **Agent / LLM** | HR RAG 채팅, 스팸 에스컬레이션, 이력서 Success DNA, 메일 AI 분류, 공시 예측 |
| **Platform** | 직원·성과·메일·주소록·감사·OAuth |
| **MLOps** | EXAONE LoRA·GGUF, LLaMA 스팸 SFT, 공시 ingest |
| **Frontend** | Next.js 대시보드, GSAP 인트로, 메일·채팅 UI |

---

## 5. 확장 예정 (미구현·로드맵)

- 공시 API 프론트 직접 연동
- 메일함 소유자 인증 연동 (로그인 세션→사번, 서버측 소유권 검증) — 현재 직원ID 수동 입력(포트폴리오 단순화)
- 사내 주소록 그룹·부서 확장
- PWA 오프라인·모니터링
- Flutter 모바일 앱
- OpenAI/Gemini 텍스트 채팅 어댑터 (배포 속도 개선)
