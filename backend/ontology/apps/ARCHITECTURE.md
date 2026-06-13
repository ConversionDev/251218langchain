# 아키텍처 가이드 (FastAPI 앱)

이 문서는 `backend/ontology/apps`(FastAPI AI 서비스)의 구조를 한눈에 파악하기 위한 지도입니다.
스타일: **헥사고날 라이트** + **중앙 허브·스타 토폴로지(MCP)**.

---

## 1. 전체 런타임 토폴로지 (3개 독립 서비스)

```
                         [사용자 브라우저]
                                │
               ┌────────────────┴─────────────────┐
               ▼                                   ▼
        www.kanggyeonggu.store             api.kanggyeonggu.store
        (Vercel · Next.js)                 (EC2 nginx :443, SSL)
           프론트엔드                            │
                                   ┌─────────────┴──────────────┐
                                   ▼ (location /auth/)          ▼ (location /)
                         Spring Gateway :8080          FastAPI :8000
                         (인증·보안: OAuth+JWT)        (이 디렉터리 = AI·RAG·도메인)
```

- **프론트엔드(Vercel)** — UI. 두 백엔드를 HTTPS로 호출.
- **Spring Gateway(`backend/gateway`)** — 유일한 "게이트웨이". OAuth(카카오/네이버/구글) + JWT.
- **FastAPI(`backend/ontology/apps`)** — 본 디렉터리. 직원·메일·공시·채팅·스팸 AI 기능.
- 셋은 systemd로 독립 실행. nginx가 `/auth/`→Spring, 나머지→FastAPI로 분배.

---

## 2. 헥사고날 계층 (의존성 방향: 밖 → 안)

```
api/         →   application/   →   domain/      ←   infrastructure/
(인바운드)        (유스케이스)       (순수 도메인)     (아웃바운드)
```

**핵심 규칙**
- `domain/`은 그 무엇도 import하지 않는다 (DB·LLM·메일을 모른다).
- `api/`는 `infrastructure/`를 직접 쓰지 않고 `application/`을 경유한다.
- 실제 I/O는 전부 `infrastructure/` 어댑터가 수행한다.
- 즉 **"무엇을 하는가(domain/application)"와 "어떻게 하는가(infrastructure)"가 분리**된다.

> **헥사고날 "라이트"**: 계층·방향은 헥사고날이지만 아직 Port(인터페이스)를 두지 않고 구현을 직접 import한다. Port 추상화(Phase 6)는 *의도적 보류* — 트리거(테스트 스위트 착수 / 새 LLM·DB 추가) 발생 시 해당 부분만 도입. 상세: `docs/hexagonal-architecture-milestone.md`.

---

## 3. 폴더 ↔ 개념 매핑

| 폴더 | 역할 | 헥사고날 위치 |
|------|------|---------------|
| `bootstrap/` | 앱 조립(composition root): CORS·라우트 등록 | 진입 wiring |
| `api/rest/` | REST 라우터 (`/api/employees`, `/mail`, `/agent` …) | **인바운드 어댑터** |
| `api/mcp/` | FastMCP **중앙 허브** 서버 (요청 수신·위임) | **인바운드 어댑터** |
| `application/` | 유스케이스 서비스 (EmployeeService, MailService, ChatService …) | 애플리케이션 |
| `domain/models/` | Pydantic 데이터 규격 | **도메인(순수)** |
| `domain/shared/` | 공용 유틸·임베딩 | **도메인(순수)** |
| `domain/spokes/` | ★ 스타 토폴로지 도메인 피처 (`chat`, `spam`) | **도메인(순수)** |
| `infrastructure/persistence/` | ORM 모델 + 레포지토리 (DB) | **아웃바운드 어댑터** |
| `infrastructure/llm/` | EXAONE·Llama·Gemini 어댑터 | **아웃바운드 어댑터** |
| `infrastructure/mail/` | Mailgun 수신/발송 | **아웃바운드 어댑터** |
| `infrastructure/mcp/` | 허브 호출 HTTP 클라이언트 | **아웃바운드 어댑터** |
| `infrastructure/orchestration/` | LangGraph 워크플로우·상태 | **아웃바운드 어댑터** |
| `core/` | 설정(config)·DB 엔진·리소스 매니저 = **플랫폼 계층** | 공통 기반 |
| (운영) `alembic/ data/ scripts/ training/ workers/ artifacts/` | 마이그레이션·데이터·학습 파이프라인 등 | 도메인과 분리된 독립 영역 |

> `core/`는 이름이 다소 일반적이지만 **플랫폼/설정 계층**(Pydantic Settings, SQLAlchemy 엔진, 모델 리소스 매니저)을 의미한다. 표준 명칭이라 유지.

---

## 4. 중앙 허브 + 스타 토폴로지 (AI 처리)

```
        api/mcp/central_control_server   ← 중앙 허브 (FastMCP "교통경찰")
         (모든 MCP 요청 수신, 위임만)
            │ call_tool
    ┌───────┴────────┐
    ▼                ▼
 chat 스포크       spam 스포크
 domain/spokes/    domain/spokes/
   chat/mcp/         spam/{mcp,services,agents,repositories}
    │                 │
    └── 공용 도구 사용 ─┘
   (infrastructure/mcp/http_client 로 허브의 LLM·DB 호출)
```

**규칙**: 허브→스포크 호출 OK, 스포크→허브 도구 사용 OK, **스포크끼리 직접 통신 금지.**
→ 기능 추가 시 새 스포크만 붙이면 되고 서로 엉키지 않는다.

---

## 5. 요청 흐름 예시

**(A) 직원 목록 — 순수 CRUD**
```
브라우저 → nginx → api/rest/employee_router
  → application/employee/EmployeeService
  → infrastructure/persistence/repositories/employee_repository (Neon DB) → 응답
```

**(B) 채팅(AI) — 스타 토폴로지 경유**
```
브라우저 → api/rest/chat_router → application/chat/ChatService
  → infrastructure/orchestration (LangGraph)
  → infrastructure/mcp/http_client → api/mcp(허브) → chat 스포크 → infrastructure/llm(EXAONE)
  → 스트리밍 응답
```

**(C) 로그인 — Spring Gateway (별도 서비스)**
```
브라우저 → nginx(/auth/) → Spring Gateway → OAuth → JWT 발급 → 이후 요청에 Bearer 첨부
```

---

## 6. 새 코드 추가 시 빠른 가이드

- **새 REST 엔드포인트**: `api/rest/`에 라우터 → `application/`에 서비스 → 필요한 I/O는 `infrastructure/`.
- **DB 접근**: 반드시 `infrastructure/persistence/repositories/`를 통해. 라우터/서비스가 ORM 직접 조작 금지.
- **외부 연동(LLM·메일 등)**: `infrastructure/`에 어댑터로. `domain/`에는 절대 두지 않는다.
- **새 AI 도메인 피처**: `domain/spokes/<name>/`에 스포크로. 허브 도구는 `infrastructure/mcp`로 호출.
- **금지**: `domain/`에서 `infrastructure/`·`core/` I/O를 import (순수성 유지). 스포크↔스포크 직접 import.
