# 백엔드 상세 문서

이 문서는 RAG 프로젝트 **백엔드(app)** 의 구조, 진입점, API, 도메인, DB, MCP, 설정을 한곳에 정리합니다.

**기능별 구현 상태**(구현됨/부분/스텁/미구현, 프론트 연동 여부)는 [implementation-status.md](implementation-status.md)에 정리되어 있으며, Gemini 등 AI가 현재 프로젝트의 기능 상태를 인식할 때 참고하도록 작성되어 있다.

---

## 1. 개요

### 1.1 역할

백엔드는 **FastAPI** 기반 REST API 서버이며, 다음을 담당합니다.

- **REST API**: 직원·성과 활동·채팅·공시·이력서·감사 로그·문서·이메일 등 도메인별 CRUD 및 비즈니스 로직
- **LangGraph 에이전트**: 스트리밍 채팅, RAG(disclosures·competency_anchors·employees 검색), 도구 호출(get_hr_summary, get_employee_info 등)
- **RAG**: PostgreSQL(pgvector)에 저장된 disclosure·competency_anchor·employee 임베딩 검색 (LangChain 전용 PG 테이블은 사용하지 않음)
- **MCP(Hub-Spoke)**: 중앙 Hub가 Chat MCP / Spam MCP로 `call_tool` 위임, 각 MCP가 Spoke(실제 LLM·DB) 호출
- **DB**: PostgreSQL + Alembic 마이그레이션으로 스키마 관리

### 1.2 아키텍처 요약

```
[클라이언트]
     │
     ▼
[FastAPI app] ← CORS (gateway)
     │
     ├─ /api/*          → activity_router, audit_router, chat_router, disclosure_router,
     │                     document_router, email_router, employee_router, resume_router
     ├─ /internal/*     → hub_llm_router (Llama/ExaOne 프록시)
     ├─ /mcp            → MCP 앱 (Central Control Server)
     └─ /internal/mcp/* → Chat MCP, Chat Spoke (동일 프로세스 마운트)
     │
     ▼
[도메인 레이어]
  - domain.hub.orchestrators  (chat, spam, graph, disclosure)
  - domain.hub.repositories   (disclosure, competency_anchor, employee, performance_record, audit_log)
  - domain.hub.llm            (ExaOne, Llama, Gemini)
  - domain.spokes.chat / spam (MCP 서버)
     │
     ▼
[PostgreSQL] + [Alembic migrations]
```

---

## 2. 기술 스택

| 구분 | 기술 | 설명 |
|------|------|------|
| 웹 프레임워크 | FastAPI | REST API, lifespan, 의존성 주입 |
| DB | PostgreSQL | 메인 저장소, pgvector 확장으로 벡터 검색 |
| ORM·마이그레이션 | SQLAlchemy, Alembic | 스키마 버전 관리, `alembic upgrade head` |
| 벡터 | pgvector, FlagEmbedding BGE-m3 | embedding 컬럼 HNSW 인덱스, 1024차원 |
| LLM | ExaOne, LLaMA, Gemini | 채팅·RAG는 ExaOne, 스팸 분류는 LLaMA, 멀티모달은 Gemini |
| MCP | FastMCP | Hub-Spoke 프로토콜, `/mcp`, `/internal/mcp/*` |
| 설정 | pydantic-settings | `.env` + 환경 변수, `core.config.Settings` |
| 캐시·job 상태 | Upstash Redis (선택) | 임베딩 job 상태 등 |

---

## 3. 디렉터리 구조

```
app/
├── fastapi_server.py      # 진입점: FastAPI 앱, lifespan, init_db, init_v1, 라우터 등록
├── alembic.ini            # Alembic 설정
├── alembic/
│   ├── env.py             # 마이그레이션 환경, Base.metadata, connection_string
│   └── versions/          # 001 ~ 021 마이그레이션 파일
├── api/
│   ├── routers/           # REST 라우터 (아래 4. 참고)
│   │   ├── __init__.py    # 라우터 통합 export, register_router 미포함
│   │   ├── register_router.py  # register_routes(): /api, /mcp, /internal 마운트
│   │   ├── activity_router.py
│   │   ├── audit_router.py
│   │   ├── chat_router.py
│   │   ├── disclosure_router.py
│   │   ├── document_router.py
│   │   ├── email_router.py
│   │   ├── employee_router.py
│   │   ├── resume_router.py
│   │   └── hub_llm_router.py   # /internal/llama, /internal/exaone 등
│   ├── services/          # resume_analyzer, resume_sample_generator 등
│   └── shared/            # upload_store, redis, embedding_sync
├── core/
│   ├── config.py          # Settings (환경 변수), get_settings()
│   ├── database/          # 세션, 엔진, Base, wait_for_postgres
│   ├── paths.py           # 프로젝트/데이터/아티팩트 경로
│   ├── faiss_store.py     # FAISS 인덱스 로드 (disclosures·competency, 선택)
│   └── resource_manager/  # ExaOne, LLaMA 리소스 관리
├── domain/
│   ├── models/            # bases(ORM·Pydantic), states(LangGraph 상태), enums
│   ├── hub/               # 중앙 오케스트레이션
│   │   ├── orchestrators/ # chat, spam, graph, disclosure
│   │   ├── repositories/  # disclosure, competency_anchor, employee, performance_record, audit_log
│   │   ├── llm/           # ExaOne, Llama, Gemini 어댑터
│   │   ├── mcp/           # central_control_server, http_client, mcp_utils, utils
│   │   ├── service/       # Hub 공통 서비스 (현재 re-export만)
│   │   └── shared/        # utils (email 포맷, jsonl 등)
│   └── spokes/            # 도메인별 MCP 서버
│       ├── chat/          # Chat MCP, Chat Spoke
│       └── spam/          # Spam MCP, Spam Spoke
├── gateway/               # CORS 등 미들웨어
├── data/                  # 도메인별 raw/prepared/sft 데이터 (disclosure, email 등)
└── training/              # 학습·파이프라인·클러스터링 (별도 실행 스크립트)
```

---

## 4. 진입점 및 라이프사이클

### 4.1 진입점

- **실행**: `python main.py` 또는 `uvicorn fastapi_server:app` (실제 진입은 프로젝트 루트의 `main.py` 등에서 `app`을 참조할 수 있음)
- **앱 생성**: `fastapi_server.py`의 `app = FastAPI(..., lifespan=_app_lifespan)`

### 4.2 Lifespan 동작

1. **yield 전**: 서버를 먼저 띄우기 위해 `yield`를 즉시 수행하고, **백그라운드 태스크**에서 아래를 순서대로 실행한다.
2. **init_v1()**:  
   - PostgreSQL 연결 대기  
   - LLM 프로바이더 설정 (ExaOne lazy load)  
   - **ensure_rag_initialized()**: Embedding(BGE-m3) 초기화, RAG 임베딩 준비, FAISS 인덱스 로드(선택)
3. **init_db()**:  
   - PostgreSQL 대기  
   - `AUTO_MIGRATE=true`이면 `alembic upgrade` 실행 (`migration_revision`, 기본 `head`)  
   - 실패 시 로그 후 예외 재발생
4. **yield 후 (종료 시)**: 초기화 태스크 취소 대기, Gemini 클라이언트 정리

이렇게 하면 Windows/uvicorn에서 lifespan에서 초기화를 기다릴 때 서버가 바로 꺼지는 현상을 피할 수 있다.

### 4.3 CORS

- `gateway.add_cors_middleware(app)`로 전역 CORS 적용.
- `CORS_ORIGINS`가 있으면 해당 오리진만 허용, 없으면 `*` (전체 허용).

---

## 5. API 라우터 상세

모든 REST API는 **prefix `/api`** 로 일원화되어 등록된다. (`register_router.py`의 `app.include_router(..., prefix="/api")`)

| 라우터 | prefix (라우터 내부) | 최종 경로 예시 | 설명 |
|--------|----------------------|----------------|------|
| activity_router | `/activity-records` | `/api/activity-records` | 성과 활동: 목록, by-employee, 단건, submit, my |
| audit_router | (prefix 없음, 경로 직접) | `/api/audit/logs` | 감사 로그 조회 |
| chat_router | `/agent` | `/api/agent/upload`, `/api/agent/chat/stream`, `/api/agent/threads/*`, `/api/agent/tools`, `/api/agent/health` | 채팅 업로드, 스트리밍, 스레드, 도구 목록, 헬스 |
| disclosure_router | `/disclosure` | `/api/disclosure/*` | 공시 문서 적재·검증·학습 상태 |
| document_router | (문서 관련) | `/api/document/*` | 문서 추출 등 |
| email_router | `/mail` | `/api/mail/receive`, `/api/mail/send`, `/api/mail/filter`, `/api/mail/classify`, 목록·단건·draft·trash | 수신·스팸·AI분석(비동기), 전송(스텁), 스팸 필터 |
| employee_router | (직원) | `/api/employees`, `/api/employees/{id}`, `/api/employees/embedding` 등 | 직원 CRUD, 이력서 분석, 임베딩 갱신, 프로필 백필 |
| resume_router | `/resume` | `/api/resume/analyze` 등 | 이력서 분석 |
| hub_llm_router | (내부) | `/internal/llama/*`, `/internal/exaone/*` | Llama·ExaOne 내부 API (Spokes가 Hub 호출 시 사용) |

추가로 **등록되는 경로**:

- **`/mcp`**: MCP 앱 마운트 (Central Control Server)
- **`/internal/mcp/chat`**, **`/internal/mcp/chat-spoke`**: Chat MCP / Chat Spoke (동일 프로세스)
- **`/api/clustering/map`**: 데이터 지도 HTML (competency_map.html)
- **`/static/clustering`**: 클러스터링 정적 파일 (해당 디렉터리 존재 시)

---

## 6. 도메인 레이어

### 6.1 Hub Orchestrators

- **chat_orchestrator**: `run_agent`, `run_agent_stream`, `get_thread_history`, `clear_thread_history` — 채팅 그래프 실행.
- **graph_orchestrator**: `build_agent_graph`, `TOOLS`, `TOOL_MAP` — RAG·도구·라우팅 구성. 도구: `search_documents`, `get_hr_summary`, `get_employee_info` 등.
- **spam_orchestrator**: `run_spam_detection`, `SpamGatewayService`, 스팸 감지 그래프.
- **disclosure_orchestrator**: `run_disclosure_ingest_orchestrate`, disclosure RAG 적재 그래프.

채팅 라우터는 `domain.hub.orchestrators.chat_orchestrator`에서 `run_agent_stream` 등을, `domain.hub.orchestrators`에서 `TOOLS`를 가져와 사용한다.

### 6.2 Hub Repositories

- **disclosure_repository**: 공시 저장·검색·임베딩 채우기.
- **competency_anchor_repository**: 역량 앵커 검색·배치 업서트.
- **employee_repository**: 직원 CRUD, 페이지네이션, 이름/ID 검색, 벡터 검색, 임베딩 갱신.
- **performance_record_repository**: 성과 활동 CRUD, 직원별 목록, 제출.
- **audit_log_repository**: 감사 로그 생성·목록.

모두 **SQLAlchemy 세션**과 **domain.models.bases**의 ORM 모델(Disclosure, CompetencyAnchor, Employee, PerformanceRecord, AuditLog)을 사용한다.

### 6.3 도메인 모델 (domain.models)

- **bases**: `CompetencyAnchor`, `EmailMetadata`, `EmailRequest`, `EmailResponse`, `VectorSearchQuery`, `VectorSearchResult`, `ExaoneResult`, `ExaoneConfig` 등. (ORM은 별도: Disclosure, Employee, PerformanceRecord, AuditLog 등이 각 모듈에서 import됨)
- **states**: `ChatState`, `SpamState`, `DatabaseResult` — LangGraph 상태.
- **enums**: 스팸 정책, 전략 타입 등.

Alembic `env.py`에서는 `CompetencyAnchor`, `Disclosure`, `Employee`, `PerformanceRecord`를 import해 `Base.metadata`에 반영한다.

### 6.4 Hub LLM

- **ExaOne**: 채팅·RAG 메인 모델 (`exaone_provider`, `exaone_adapter`).
- **Llama**: 스팸 분류 등 (`llama_adapter`, `llama_classifier`).
- **Gemini**: 멀티모달(이미지) 채팅 (`gemini_adapter`).

설정은 `core.config` (예: `llm_provider`, `exaone_use_4bit`, `gemini_api_key` 등)에서 읽는다.

---

## 7. 데이터베이스 및 Alembic

### 7.1 연결

- **연결 문자열**: `core.config.Settings.connection_string` (computed). `DATABASE_URL` 또는 `POSTGRES_CONNECTION_STRING` 사용, 없으면 기본 Neon URL.
- **세션**: `core.database.get_db` (FastAPI Depends용). 라우터에서 `Session = Depends(get_db)`로 주입.

### 7.2 마이그레이션

- **위치**: `app/alembic/`, `script_location = app/alembic`.
- **자동 실행**: `AUTO_MIGRATE=true`(기본)이면 기동 시 `alembic upgrade`를 `migration_revision`(기본 `head`)까지 실행.
- **수동**: 새 리비전은 `alembic revision --autogenerate -m "설명"`으로 생성.

### 7.3 마이그레이션 체인 요약

| 리비전 | 요약 |
|--------|------|
| 001_initial_squashed | 통합 초기 (disclosures, competency_anchors, employees 등 + pgvector 컬럼) |
| 002~005 | disclosure 메타데이터, B-tree/HNSW 인덱스 |
| 006 | competency_anchors 테이블 |
| 007~015 | employees 테이블 및 컬럼 (status, application_date, resume_file_hash 등) |
| 016~018 | meetings 테이블 추가 후 제거 |
| 017 | performance_records 테이블 |
| 019 | audit_logs 테이블 |
| 020 | disclosures, competency_anchors, performance_records에 tsvector + GIN (full-text) |
| 021 | Soccer 도메인 테이블·인덱스 제거 (players, teams, stadiums, schedules) |

현재 **주요 테이블**: disclosures, competency_anchors, employees, performance_records, audit_logs. 벡터 검색은 disclosures·competency_anchors·employees의 `embedding` 컬럼(pgvector) + HNSW 인덱스를 사용한다.

---

## 8. MCP (Hub-Spoke)

### 8.1 구조

- **Hub (Central Control Server)**: `domain.hub.mcp.central_control_server`. FastMCP 앱으로 `/mcp`에 마운트. 요청을 **Chat MCP** / **Spam MCP**로만 위임.
- **Chat MCP / Chat Spoke**: 동일 프로세스에서 `/internal/mcp/chat`, `/internal/mcp/chat-spoke`로 마운트. 채팅은 ExaOne만 사용(LLaMA 제거).
- **Spam MCP / Spam Spoke**: 별도 포트(9021/9022) 예시. 이메일 분석·스팸 분류.

Hub는 무거운 모델을 직접 부르지 않고, 각 도메인 MCP가 자신의 Spoke URL로 `call_tool`한다.

### 8.2 설정

- **hub_service_url**: Hub 베이스 URL (기본 `http://127.0.0.1:8000`).
- **chat_mcp_url**, **chat_spoke_mcp_url**: 기본값은 동일 프로세스(8000)의 `/internal/mcp/chat/server`, `/internal/mcp/chat-spoke/server`.
- **spam_mcp_url**, **spam_spoke_mcp_url**: 기본 9021/9022 (별도 프로세스 예시).

### 8.3 HTTP 클라이언트

- **domain.hub.mcp.http_client**: Spokes가 Hub를 HTTP로 호출할 때 사용. `llama_classify_spam`, `exaone_generate`, `exaone_analyze_email`, `chat_call`, `spam_call` 등.
- **domain.hub.mcp.mcp_utils / utils**: `get_chat_mcp_url`, `get_spam_mcp_url`, `get_chat_spoke_mcp_url`, `get_spam_spoke_mcp_url`, `result_to_str`.

---

## 9. 설정 (환경 변수)

`core.config.Settings`가 `.env` 및 환경 변수를 읽는다. 주요 항목만 정리한다.

| 분류 | 변수 예시 | 설명 |
|------|-----------|------|
| DB | `DATABASE_URL`, `POSTGRES_CONNECTION_STRING`, `AUTO_MIGRATE`, `MIGRATION_REVISION` | 연결·마이그레이션 |
| LLM | `LLM_PROVIDER` (exaone), `EXAONE_USE_4BIT`, `EXAONE_USE_COMPETENCY_ADAPTER` | ExaOne 등 |
| 임베딩 | `DEFAULT_EMBEDDING_MODEL`, `EMBEDDING_DEVICE` | BGE-m3, cuda/cpu |
| 서버 | `HOST`, `PORT`, `CORS_ORIGINS` | 127.0.0.1, 8000, CORS |
| API 키 | `OPENAI_API_KEY`, `GEMINI_API_KEY` | 선택 |
| 업로드 | `UPLOAD_DIR`, `UPLOAD_MAX_FILES`, `UPLOAD_MAX_FILE_SIZE_MB` | 채팅 첨부 |
| Redis | `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN` | 임베딩 job 상태 등 (선택) |
| MCP | `HUB_SERVICE_URL`, `CHAT_MCP_URL`, `CHAT_SPOKE_MCP_URL`, `SPAM_MCP_URL`, `SPAM_SPOKE_MCP_URL` | Hub-Spoke URL |

`.env` 파일은 `core.paths.get_project_root()` 기준 프로젝트 루트의 `.env`를 사용한다.

---

## 10. 실행 및 배포

### 10.1 로컬 실행

1. **DB**: PostgreSQL(Neon 등) 접속 가능하고, `DATABASE_URL` 또는 `POSTGRES_CONNECTION_STRING` 설정.
2. **실행**: 프로젝트 루트에서 `app`을 기준으로 실행.  
   - `cd app && python main.py` — `main.py`가 `core.config`로 host/port를 읽고 `uvicorn.run(fastapi_server.app, ...)` 실행.  
   - 또는 `cd app && uvicorn fastapi_server:app --host 0.0.0.0 --port 8000`
3. 기동 시 `AUTO_MIGRATE=true`이면 마이그레이션이 자동 적용되고, init_v1/init_db가 백그라운드에서 실행된다.

### 10.2 헬스 체크

- **GET /** : API 상태 및 `/docs` 안내.
- **GET /health** : `status`, `local_embeddings` 상태.
- **GET /api/agent/health** : 채팅 에이전트·프로바이더·도구 호출 지원 여부.

### 10.3 배포 시 참고

- **CORS**: 프로덕션에서는 `CORS_ORIGINS`로 허용 오리진을 제한하는 것이 좋다.
- **마이그레이션**: 기동 전에 별도로 `alembic upgrade head`를 실행해 두고 `AUTO_MIGRATE=false`로 두는 구성도 가능하다.
- **비밀/키**: `DATABASE_URL`, API 키 등은 환경 변수로만 주입하고 코드에 넣지 않는다.

---

## 11. DB·마이그레이션

- **Alembic**: `cd app` → `alembic upgrade head`. 새 환경은 한 번에 전체 스키마 적용. 이미 테이블 있으면 `alembic stamp 001_initial` 후 필요 시 수동 정리.
- **스키마 변경**: `alembic revision --autogenerate -m "설명"` → `alembic upgrade head`. 명령: `alembic current`, `alembic history`, `alembic downgrade -1`.
- **disclosures 재생성**: DROP 후 `alembic stamp 001_initial` → `alembic upgrade head`. 적재: `app/data/disclosure/prepared/`, `python -m training.pipelines.ingest.run_disclosure_ingest`. 직원 임베딩: `POST /api/employees/embedding`.

---

## 12. RAG·벡터

- **저장소**: disclosures, competency_anchors, employees의 **embedding** 컬럼. LangChain 전용 테이블 미사용.
- **적재**: disclosure는 `get_data_dir()/disclosure/prepared/` → BGE-m3 임베딩. 직원은 `POST /api/employees/embedding` (전체 또는 id).
- **검색**: 공시 질문 → disclosures, 역량/직무 → competency_anchors, 직원/인력 → employees(거리 0.6 이하). 복합 질문은 disclosures+employees 융합.
- **HNSW**: BGE-m3 1024차원, 코사인 거리. 004(disclosures), 006(competency_anchors), 007(employees). `m=24`, `ef_construction=128`, 검색 시 `ef_search=100` 권장.

---

이 문서는 백엔드 진입점, API, 도메인, DB, MCP, 설정을 한 문서에 모은 것이다. 세부 엔드포인트 스펙은 FastAPI `/docs`(Swagger)와 각 라우터·리포지토리 코드를 참고하면 된다.
