# 시스템 아키텍처

이 문서는 **3개 독립 서비스 토폴로지**, **헥사고날 계층**, **MCP 중앙 허브·스타 토폴로지**, 그리고 채팅·스팸·메일 파이프라인과 배포(systemd·nginx·CI/CD) 구조를 한곳에 정리합니다.

개요·기술스택은 루트 [README.md](../../README.md), 도메인별 구현 현황은 [IMPLEMENTATION.md](IMPLEMENTATION.md), 프론트엔드는 [FRONTEND.md](FRONTEND.md)를 참고하세요.

---

## 1. 런타임 토폴로지 (3개 독립 서비스)

프론트(Vercel) 1개 + 백엔드(EC2) 2개로 구성되며, nginx가 경로 기준으로 분배합니다.

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
                         (인증·보안: OAuth+JWT)        (AI·RAG·도메인)
```

| 서비스 | 위치 | 역할 |
|--------|------|------|
| **프론트엔드** | Vercel · `frontend/` | Next.js UI. 두 백엔드를 HTTPS로 호출 |
| **Spring Gateway** | EC2 · `backend/gateway/` | 유일한 인증 게이트웨이. OAuth2(카카오/네이버/구글) + JWT |
| **FastAPI** | EC2 · `backend/ontology/apps/` | 직원·메일·공시·채팅·스팸 AI 기능 |

세 서비스는 systemd로 독립 실행되고, nginx가 `/auth/`→Spring(:8080), 그 외 → FastAPI(:8000)로 라우팅합니다.

---

## 2. 헥사고날 계층 (FastAPI 앱)

스타일: **헥사고날 라이트** — 계층·의존성 방향은 헥사고날을 따르되, Port(인터페이스) 추상화는 의도적으로 보류(필요 트리거 발생 시 도입).

```
api/         →   application/   →   domain/      ←   infrastructure/
(인바운드)        (유스케이스)       (순수 도메인)     (아웃바운드)
```

**핵심 규칙**

- `domain/`은 그 무엇도 import하지 않는다 (DB·LLM·메일을 모른다).
- `api/`는 `infrastructure/`를 직접 쓰지 않고 `application/`을 경유한다.
- 실제 I/O는 전부 `infrastructure/` 어댑터가 수행한다.
- 즉 **"무엇을 하는가(domain/application)"와 "어떻게 하는가(infrastructure)"가 분리**된다.

### 2.1 폴더 ↔ 개념 매핑

| 폴더 | 역할 | 헥사고날 위치 |
|------|------|---------------|
| `bootstrap/` | 앱 조립(composition root): CORS·라우트 등록 | 진입 wiring |
| `api/rest/` | REST 라우터 (`/api/employees`, `/mail`, `/agent` …) | **인바운드 어댑터** |
| `api/mcp/` | FastMCP **중앙 허브** 서버 (요청 수신·위임) | **인바운드 어댑터** |
| `application/` | 유스케이스 서비스 (EmployeeService, MailService, ChatService …) | 애플리케이션 |
| `domain/models/` | Pydantic 데이터 규격·상태·Enum | **도메인(순수)** |
| `domain/shared/` | 공용 유틸·임베딩 | **도메인(순수)** |
| `domain/spokes/` | 스타 토폴로지 도메인 피처 (`chat`, `spam`) | **도메인(순수)** |
| `infrastructure/persistence/` | ORM 모델(`*_orm.py`) + 레포지토리 (DB) | **아웃바운드 어댑터** |
| `infrastructure/llm/` | EXAONE·Llama·Gemini 어댑터 | **아웃바운드 어댑터** |
| `infrastructure/mail/` | Mailgun 수신/발송 | **아웃바운드 어댑터** |
| `infrastructure/mcp/` | 허브 호출 HTTP 클라이언트 | **아웃바운드 어댑터** |
| `infrastructure/orchestration/` | LangGraph 워크플로우·상태 (chat·spam·disclosure·email) | **아웃바운드 어댑터** |
| `core/` | 설정(Pydantic Settings)·DB 엔진·리소스 매니저 | 플랫폼 계층 |
| `alembic/ data/ scripts/ training/ workers/ artifacts/` | 마이그레이션·데이터·학습 등 | 독립 운영 영역 |

> **마이그레이션 현황**: ORM 모델·레포지토리는 `infrastructure/persistence/`로 이동 완료, 라우터는 `api/rest/`, 유스케이스는 `application/`(employee·chat·mail·address_book·disclosure·shared)으로 분리 완료. 상세 단계별 이력은 [archive/hexagonal-architecture-milestone.md](archive/hexagonal-architecture-milestone.md) 참고.

---

## 3. MCP 중앙 허브 + 스타 토폴로지 (AI 처리)

중앙 **허브**(FastMCP "교통경찰")가 모든 MCP 요청을 받아 도메인별 **스포크**로만 위임합니다. 허브는 무거운 모델을 직접 로드하지 않습니다.

```
        api/mcp/central_control_server   ← 중앙 허브 (요청 수신, 위임만)
            │ call_tool
    ┌───────┴────────┐
    ▼                ▼
 chat 스포크       spam 스포크
 domain/spokes/    domain/spokes/
   chat/             spam/{mcp,services,agents,repositories}
    │                 │
    └── 공용 도구 사용 ─┘
   (infrastructure/mcp/http_client 로 허브의 LLM·DB 호출)
```

**규칙**: 허브→스포크 호출 OK, 스포크→허브 도구 사용 OK, **스포크끼리 직접 통신 금지.**
→ 기능 추가 시 새 스포크만 붙이면 되고 서로 엉키지 않는다.

| 구성요소 | 역할 |
|----------|------|
| **허브 (Central Control)** | `/mcp` 마운트. Chat MCP / Spam MCP로만 라우팅. 모델 직접 로드 없음. |
| **Chat 스포크** | 동일 프로세스(`/internal/mcp/chat`). 채팅·RAG는 **EXAONE만** 사용. |
| **Spam 스포크** | 이메일 분석·스팸 분류. 허브 내부 API(`/internal/llama`)로 LLaMA 호출. |

---

## 4. 요청 흐름 예시

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
  → SSE 스트리밍 응답
```

**(C) 로그인 — Spring Gateway (별도 서비스)**

```
브라우저 → nginx(/auth/) → Spring Gateway → OAuth → JWT 발급 → 이후 요청에 Bearer 첨부
```

---

## 5. 채팅 RAG·에이전트

LangGraph 기반 에이전트. **1턴 구조(LLM 1회 호출)**로 GPU 부하를 절반으로 줄인 것이 핵심.

### 5.1 그래프 흐름

```
rag_node
  → model_node (도구 필요 시 forced_tool_calls, 불필요 시 LLM 1회)
  → tool_node
  → model_node (도구 결과 + context로 LLM stream)
  → 응답
```

- **1턴 최적화**: 첫 턴에서 LLM invoke를 제거하고 `_build_forced_tool_calls(user_query)`로 **키워드 기반 도구 결정**만 수행. 도구 결과 + RAG context로 두 번째 model_node에서만 LLM을 1회 stream.
- **도구**: `get_hr_summary`, `list_employees`(고성과 필터), `get_employee_info`, `get_employee_performance`, `search_documents`.
- **GPU**: ExaOne 생성 후 `torch.cuda.empty_cache()`. 1턴 + 명단 30명 상한으로 OOM 방지.

### 5.2 RAG 라우팅

- **라우팅 키워드** → 테이블: employees(직원·명단·부서), performance_records(성과·활동), competency_anchors(역량·직무), disclosures(IFRS·공시).
- **임계값**: 라우트 감지 테이블 `RAG_DISTANCE_THRESHOLD`(0.8), 미감지 `RAG_STRICT_THRESHOLD`(0.5), 직원 `RAG_EMPLOYEE_DISTANCE_THRESHOLD`(0.6).
- **하이브리드**: disclosures·competency_anchors·performance_records는 벡터 + tsvector(full-text). employees는 pgvector HNSW.
- **OOS**: 라우트 없으면 검색 없이 "[시스템 안내] 이 질문은 현재 데이터 범위 밖…" 반환.
- **출처**: `[출처: table=..., id=..., source=...]` 형식.

---

## 6. 메일 시스템

### 6.1 설계 원칙

- **Store-then-Process**: 수신 API는 **저장 후 즉시 200/201**만 담당(AI 호출 없음) → Mailgun 타임아웃·유실 방지.
- **Decoupling**: 수신(Fast)과 AI 처리(Slow) 분리. 워커 지연/장애가 수신 유실로 이어지지 않음.
- **공급자 추상화**: `infrastructure/mail/`에서 Mailgun → NormalizedInboundMail 변환. SES 등 교체 시 이 계층만 교체.

### 6.2 상태 모델 (두 축 분리)

- **status** = 메일 도메인 상태: `RECEIVED` | `REJECTED`
- **ai_status** = AI 처리 상태: `PENDING` | `PROCESSING` | `SUCCESS` | `FAILED`
- **REJECTED 시**: `ai_status=NULL`, `folder=NULL`, `spam_score=NULL` → 워커 미처리.
- **external_id**(Message-ID): UNIQUE INDEX로 멱등 보장(중복 저장 방지).
- 코드에서는 `AiStatus`, `MailReceiveStatus` Enum 사용(문자열 하드코딩 금지).

### 6.3 수신·처리 흐름

| 구분 | 내용 |
|------|------|
| **수신** | Mailgun → `POST /api/mail/receive/webhook/mailgun`(Form, HMAC). 테스트용 `POST /api/mail/receive`(JSON). |
| **저장** | parse_and_verify → 저장. external_id 중복 시 200. Resolver(To→owner_employee_id) 실패 시 REJECTED 저장 후 4xx/200. |
| **워커** | PENDING → `SELECT FOR UPDATE SKIP LOCKED` → PROCESSING commit → AI 실행 → SUCCESS/FAILED commit. |
| **성과 연동** | `folder=inbox`인 경우만 BackgroundTasks로 `run_email_classify_and_record` → 성과로 판단되면 performance_records 기록 + 5대 역량 태깅. |

`mail_items` 테이블 하나로 inbox/sent/draft/trash/spam 폴더를 통합 관리합니다.

### 6.4 Mailgun·DNS

| 항목 | 값 |
|------|------|
| Webhook URL | `https://<API-도메인>/api/mail/receive/webhook/mailgun` (POST) |
| 환경변수 | `MAILGUN_WEBHOOK_SIGNING_KEY`(HMAC), `MAILGUN_SKIP_VERIFY`, `MAILGUN_API_KEY`, `MAILGUN_DOMAIN` |
| SPF | `mg` TXT `v=spf1 include:mailgun.org ~all` |
| DKIM | `mailo._domainkey.mg` TXT (메일건 공개키) |
| MX | `mg` → `mxa/mxb.mailgun.org.` (우선순위 10) |

**발송 정책**: 수신자가 직원/사내 주소록이면 DB만 사용(보낸함+받은함 생성), 외부 주소면 `MAILGUN_API_KEY`/`MAILGUN_DOMAIN`이 있을 때 메일건 API로 실제 발송.

---

## 7. 스팸 분류 + Gemini 에스컬레이션

수신 메일을 분류해 `folder=inbox`(정상) vs `spam`으로 저장합니다.

### 7.1 1차 분류 (LLaMA 3 SFT)

- 학습한 LLaMA 스팸 분류기가 스팸 확률을 생성 → 파싱하여 inbox/spam 결정.
- **결정 정책**: `SpamGatewayService`에서 LLaMA 결과가 있으면 `routing_strategy="rule"`로 고정해 LLaMA 기준으로만 최종 판정. 분류 실패(미로드·타임아웃) 시에는 수신을 막지 않고 기본 `folder=inbox`로 저장(장애 시 수신 차단 방지).

### 7.2 에스컬레이션 (애매한 케이스 → 환경별 LLM 판정)

명확한 메일은 1차 분류로 끝나고, **애매한 메일만** "증거 수집 + LLM 판정" 방식으로 에스컬레이션합니다(도구 호출(tool-calling)을 쓰지 않아 CPU 배포에서도 견고).

| 환경 | 판정 LLM | 비고 |
|------|----------|------|
| **로컬** | `SPAM_AGENT_LLM=auto` → EXAONE(GPU) | `_resolve_llm_choice()`로 결정 |
| **배포(EC2)** | `SPAM_AGENT_LLM=gemini` → Gemini | raw SDK, 신규 의존성 0, CPU에서 견고 |

- LLaMA 1차 분류 결과(`llama_result`) + 규칙 + EXAONE 심층분석을 **증거**로 모아 judge LLM이 최종 판정.
- 로그: `[SPAM-ESCALATION] judge LLM=gemini` (또는 exaone). 판정/실행 실패 시 기존 판정 유지(안전).
- 플래그: `SPAM_AGENT_ESCALATION=true`, `SPAM_AGENT_LLM=gemini`.

---

## 8. 데이터베이스

- **DB**: PostgreSQL(Neon) + `pgvector`. 연결: `DATABASE_URL` 또는 `POSTGRES_CONNECTION_STRING`.
- **주요 테이블**: employees, disclosures, competency_anchors, performance_records, mail_items, internal_addresses, audit_logs.
- **벡터 검색**: disclosures·competency_anchors·employees의 `embedding` 컬럼 + **HNSW 인덱스**. BGE-M3 1024차원, 코사인 거리. `m=24`, `ef_construction=128`, 검색 `ef_search=100`.
- **마이그레이션**: Alembic. `AUTO_MIGRATE=true`면 기동 시 `alembic upgrade head`. 새 리비전은 `alembic revision --autogenerate -m "설명"`.

---

## 9. 배포 (systemd · nginx · CI/CD)

### 9.1 인프라

- **EC2**: t4g.large (ARM Graviton2, 2 vCPU, 8GB RAM, 서울 $0.0832/hr) + **Elastic IP 43.201.214.82** 고정. 세 서비스 systemd 독립 실행. 평시 중지·필요 시 기동 운영 (상세: [INFRA.md](INFRA.md)). — 2026-07 이전 (구: m7i-flex.large x86)
- **CI/CD**: GitHub Actions — `rsync`로 코드 전송 후 `ssh nohup`(또는 systemd 재시작). `.github/workflows/deploy.yml`에서 `printf`로 `.env`를 생성해 환경변수 유지.
- **SSL**: Let's Encrypt(Certbot). `certbot.timer`로 자동 갱신.

### 9.2 nginx 라우팅 (`nginx_default.conf`)

| 경로 | 프록시 대상 | 특이사항 |
|------|-------------|----------|
| `/api/agent/chat/stream` | FastAPI :8000 | **SSE 전용**: `proxy_buffering off`, `proxy_read_timeout 600s` (CPU 추론 장시간 허용) |
| `/` (그 외) | FastAPI :8000 | `proxy_read_timeout 120s` |
| `/auth/` | Spring Gateway :8080 | OAuth |
| `:80` | — | `301` HTTPS 리다이렉트 |

### 9.3 기동(Lazy 로딩) 전략

스타트업 시 **DB 연결만 확인**하고, EXAONE·Embedding(BGE-M3)·FAISS·스팸 LLaMA는 **첫 요청 시 lazy 로드**합니다. RAG 검색은 FAISS 인덱스를 로드하지 않고 **pgvector(HNSW)만** 사용 → 소형 인스턴스에서 스타트업 OOM 방지.

### 9.4 주요 환경변수

| 분류 | 변수 |
|------|------|
| DB | `DATABASE_URL` / `POSTGRES_CONNECTION_STRING`, `AUTO_MIGRATE`, `MIGRATION_REVISION` |
| LLM | `LLM_PROVIDER`(`exaone` GPU / `llama_cpp` CPU), `EXAONE_GGUF_PATH`, `EXAONE_GGUF_N_CTX`(배포 2048), `EXAONE_USE_COMPETENCY_ADAPTER` |
| 임베딩 | `DEFAULT_EMBEDDING_MODEL`, `EMBEDDING_DEVICE` |
| 서버 | `HOST`, `PORT`, `CORS_ORIGINS`(쉼표 구분, 비우면 `*`) |
| Redis | `UPSTASH_REDIS_URL`(`rediss://default:TOKEN@HOST:6379` — Gateway·FastAPI 공통, REST URL·TOKEN 자동 추출) |
| 메일 | `MAILGUN_*` (§6.4) |
| 스팸 | `SPAM_AGENT_ESCALATION`, `SPAM_AGENT_LLM`, `GEMINI_API_KEY` |
| MCP | `HUB_SERVICE_URL`, `CHAT_MCP_URL`, `SPAM_MCP_URL` 등 |

> **CORS 주의**: Vercel(www)에서 API를 호출하려면 EC2 앱에 `CORS_ORIGINS=https://www.kanggyeonggu.store,https://kanggyeonggu.store`를 넣어야 한다.

배포 중 발생한 핵심 난제(GGUF 변환, OOM, SSL 만료, MCP 순환 의존 등)는 [TROUBLESHOOTING.md](TROUBLESHOOTING.md) 참고.
