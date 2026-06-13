# 헥사고날 아키텍처 마이그레이션 마일스톤

> 작성일: 2026-05-18 (리뷰 반영 업데이트)  
> 대상 프로젝트: HR Ontology RAG Platform (`backend/ontology/apps/`)  
> Python 3.11 / FastAPI / LangGraph / EXAONE / pgvector

---

## 0. 이 마이그레이션을 해야 하는가? (ROI 판단)

### 해야 하는 이유

| 현재 문제 | 실제 피해 |
|-----------|-----------|
| 라우터가 레포지토리를 직접 호출 | 비즈니스 로직 테스트 불가 |
| ORM 모델이 `domain/models/` 에 있음 | 도메인이 SQLAlchemy에 결합됨 |
| `domain/hub/` + `domain/spokes/` 이중 구조 | 어디에 뭘 쓸지 팀원 혼란 |
| Application Service 계층 부재 | 채용 흐름·메일 라우팅 등 로직이 라우터에 산재 |

### 하지 말아야 하는 이유 (주의)

- **LangGraph 포트 추상화는 독이다**: StateGraph / 노드 / 엣지를 포트로 감싸면 LangGraph 장점이 사라지고 보일러플레이트만 쌓임. LangGraph는 인프라 어댑터로 취급하고 포트 추상화 대상에서 **제외**할 것.
- **마이그레이션 중 절반 상태가 가장 위험**: 두 패턴이 공존하면 새 코드를 어디 쓸지 아무도 모름. 한 도메인씩 완전히 끝내고 다음으로 넘어갈 것.

### 결론: "헥사고날 라이트"를 권장

**핵심 3가지만** 완전히 달성하면 동일한 이점을 얻는다:

1. **Application Service Layer** 추가 (라우터 ↔ 레포지토리 사이의 빈 계층)
2. **ORM 모델을 인프라 계층으로 이동** (도메인엔 순수 Pydantic만)
3. **`hub/spokes/` 이중 구조 통합** (하나의 Bounded Context 구조로)

**실행 권장**: 전체를 한 번에 밀지 말고 **Phase 1 + Phase 3a (Employee)** 한 세트만 먼저 끝까지 가보기. 한 도메인만 완전히 헥사고날 라이트로 만들면 나머지 도메인은 그 패턴 복제만 하면 됨.

---

## 1. 현재 구조 (AS-IS)

```
apps/
├── api/
│   ├── routers/          # HTTP 라우터 (비즈니스 로직 포함 ← 문제)
│   ├── services/         # resume_analyzer (LLM 호출 포함)
│   └── shared/           # upload_store, redis
├── application/          # ✅ Phase 3에서 신규 생성 완료 (EmployeeService, MailService, DisclosureService)
├── core/
│   ├── config.py         # ✅ Pydantic Settings
│   ├── database/         # ✅ SQLAlchemy engine/session
│   └── llm/              # ⚠️ exaone_model.py가 사용 중 — 삭제 전 grep 재확인 필요
├── domain/
│   ├── hub/
│   │   ├── llm/          # ✅ exaone_adapter, llama_adapter (어댑터 패턴)
│   │   ├── mail/         # ✅ Mailgun provider 분리
│   │   ├── orchestrators/ # ⚠️ LangChain/LangGraph 직접 의존 (인프라가 도메인에)
│   │   ├── repositories/ # ✅ Repository 패턴 (함수형, 현재 구조 유지)
│   │   └── service/      # ⚠️ 비어있음
│   ├── models/
│   │   └── bases/        # ❌ ORM + Pydantic DTO 혼재 (12개 파일, 아래 분류표 참조)
│   ├── shared/           # 유틸리티
│   └── spokes/           # ⚠️ chat/spam — hub/과 이중 구조
└── gateway/              # ✅ CORS, 라우터 등록
```

---

## 2. Phase 1 시작 전: `domain/models/bases/` 파일 분류표

**Phase 1 작업 전에 이 표를 완성해야 한다.** 분류 없이 시작하면 "이건 어디로?" 반복.

| 파일 | 현재 내용 | 분류 | 이동 목적지 |
|------|-----------|------|-------------|
| `employee.py` | SQLAlchemy ORM (`Column`, `relationship`) | **ORM** | `infrastructure/persistence/models/employee_orm.py` |
| `mail_item.py` | SQLAlchemy ORM | **ORM** | `infrastructure/persistence/models/mail_item_orm.py` |
| `disclosure.py` | SQLAlchemy ORM | **ORM** | `infrastructure/persistence/models/disclosure_orm.py` |
| `audit_log.py` | SQLAlchemy ORM | **ORM** | `infrastructure/persistence/models/audit_log_orm.py` |
| `competency_anchor.py` | SQLAlchemy ORM | **ORM** | `infrastructure/persistence/models/competency_anchor_orm.py` |
| `internal_address.py` | SQLAlchemy ORM | **ORM** | `infrastructure/persistence/models/internal_address_orm.py` |
| `performance_record.py` | SQLAlchemy ORM | **ORM** | `infrastructure/persistence/models/performance_record_orm.py` |
| `email_model.py` | Pydantic DTO (EmailRequest, EmailResponse) | **API 스키마** | `api/schemas/email_schema.py` 또는 현위치 유지 |
| `exaone_result_model.py` | Pydantic DTO (ExaoneResult) | **LLM 결과 DTO** | `infrastructure/llm/schemas/exaone_result.py` |
| `spam_model.py` | Pydantic DTO (EmailMetadata, LLaMAResult) | **API 스키마** | `api/schemas/spam_schema.py` 또는 현위치 유지 |
| `vector_model.py` | Pydantic DTO (VectorSearchQuery) | **검색 DTO** | `infrastructure/persistence/schemas/vector_schema.py` 또는 현위치 유지 |
| `exaone_model.py` | HuggingFace EXAONE 모델 구현 + `core.llm` 사용 | **LLM 구현체** | `infrastructure/llm/exaone_hf_model.py` |

**Phase 1에서 반드시 이동하는 것**: 7개 ORM 파일 (위 표 상단)  
**Phase 1에서 판단 보류 가능**: 5개 Pydantic/LLM 파일 — 위치보다 타입 분류가 더 중요, 급하지 않음

> `core/llm/` 삭제 주의: `exaone_model.py`가 `from core.llm` 을 import 중임이 grep으로 확인됨.  
> Phase 5에서 `exaone_model.py`를 `infrastructure/llm/`으로 이동할 때 같이 처리할 것.  
> 지금 당장 `core/llm/` 삭제 금지.

---

## 3. 목표 구조 (TO-BE)

```
apps/
├── api/                          # 인바운드 어댑터 (HTTP)
│   ├── routers/                  # FastAPI 라우터 — 얇게 유지
│   └── shared/
│
├── application/                  # ← Phase 3에서 생성 (Application Service Layer)
│   ├── employee/
│   │   └── employee_service.py   # ✅ 생성 완료
│   ├── mail/
│   │   └── mail_service.py       # ✅ 생성 완료
│   ├── disclosure/
│   │   └── disclosure_service.py # ✅ 생성 완료
│   └── chat/
│       └── chat_service.py       # Phase 3b에서 추가 예정
│
├── domain/                       # 도메인 계층 — 인프라 의존 없음
│   └── ...                       # 순수 비즈니스 규칙
│
├── infrastructure/               # ← Phase 1-4에서 생성 (아웃바운드 어댑터)
│   ├── persistence/
│   │   ├── models/               # ← ORM 이동 (Phase 1)
│   │   └── repositories/         # ← 레포지토리 이동 (Phase 2)
│   ├── llm/                      # ← domain/hub/llm/ 이동 (Phase 4)
│   ├── mail/                     # ← domain/hub/mail/ 이동 (Phase 4)
│   ├── mcp/                      # ← domain/hub/mcp/ 이동 (Phase 5)
│   └── orchestration/            # ← domain/hub/orchestrators/ 이동 (Phase 4)
│       └── states/               # ← domain/models/states/ 이동 (Phase 4)
│
└── core/                         # 크로스커팅 (현재 구조 유지)
```

### 의존성 방향 (목표)

```
[HTTP] api/routers
         ↓
[앱]  application/services    ← 비즈니스 규칙 (유스케이스)
         ↓
[도메인] domain/              ← 순수 Python (외부 의존 없음)
         ↑ (구현 주입)
[인프라] infrastructure/      ← SQLAlchemy, LangGraph, Mailgun
```

---

## 4. DI 패턴 통일 규칙 (전 팀 공유 필수)

**모든 Application Service는 생성자에 Session을 주입한다.**

```python
# 표준 패턴
class EmployeeService:
    def __init__(self, db: Session) -> None:
        self.db = db
```

```python
# 라우터에서 사용법
@router.post("...")
def endpoint(db: Session = Depends(get_db)):
    return EmployeeService(db).some_method(...)
```

```python
# 백그라운드 태스크에서 사용법 (Depends 불가)
def background_task(...):
    db = SessionLocal()
    try:
        EmployeeService(db).some_method(...)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
```

**금지 패턴**:
- `Service.create()` 팩토리 메서드 → 생성자 주입으로 통일
- `FastAPI Depends` 컨테이너 주입 → 단순 생성자가 테스트에 더 유리
- 서비스 내부에서 `SessionLocal()` 직접 생성 → 호출 측이 세션 수명 관리

---

## 5. 반환 타입 정책

선택 가능한 옵션은 3가지였다:

| 옵션 | 방식 | 비고 |
|------|------|------|
| **(A)** | dict 유지, Phase 6에서 Entity 도입 | 실용적, 지금 선택 |
| (B) | Phase 3과 동시에 도메인 Pydantic Entity 도입 | 더 깔끔하지만 Phase 3 비용 2배 이상 증가 |
| (C) | ORM 반환 후 Application Service에서 Pydantic 변환 | 자주 쓰이는 절충안이지만 중간 매핑 레이어 추가 공수 |

**현재 결정: (A) 당분간 dict 유지**

(B)를 기각한 이유: 폴더 구조 마이그레이션과 타입 시스템 변경을 동시에 진행하면 PR 단위가 커지고, 중간에 멈췄을 때 절반 상태(dict 반환과 Entity 반환이 공존)가 더 위험함.  
(C)를 기각한 이유: 현재 레포지토리가 이미 dict를 잘 반환 중이므로 ORM 객체를 한 번 더 변환하는 레이어를 추가할 실익이 없음.

Repository 함수가 `dict`를 반환하는 현재 구조를 유지한다. Application Service도 `dict`를 받아 `dict`를 반환한다.

Phase 6 (선택적) 에서만 도메인 Pydantic Entity 도입을 검토한다:
```python
# Phase 6 이후 예시 (지금은 구현 금지)
class Employee(BaseModel):
    id: str
    name: str
    employment_type: EmploymentType
    status: HiringStatus
    success_dna: Optional[SuccessDna] = None
```

**주의**: 팀원마다 다르게 짜는 걸 막으려면 이 규칙을 CLAUDE.md 또는 기술서에 명시할 것.

---

## 6. 마이그레이션 단계별 계획

### Phase 1 — ORM 모델 이동 (✅ 완료, 2026-06-13)

**목표**: `domain/models/bases/`의 7개 ORM 파일을 `infrastructure/persistence/models/`로 이동

**이동 대상** (위 분류표의 ORM 항목):

```
domain/models/bases/employee.py          → infrastructure/persistence/models/employee_orm.py
domain/models/bases/mail_item.py         → infrastructure/persistence/models/mail_item_orm.py
domain/models/bases/disclosure.py        → infrastructure/persistence/models/disclosure_orm.py
domain/models/bases/audit_log.py         → infrastructure/persistence/models/audit_log_orm.py
domain/models/bases/competency_anchor.py → infrastructure/persistence/models/competency_anchor_orm.py
domain/models/bases/internal_address.py  → infrastructure/persistence/models/internal_address_orm.py
domain/models/bases/performance_record.py → infrastructure/persistence/models/performance_record_orm.py
```

**연쇄 수정 필요**:
- `alembic/env.py`: `Base` import 경로 업데이트
- `domain/hub/repositories/*.py`: ORM import 경로 업데이트
- `domain/models/__init__.py`: re-export 경로 업데이트

**완료 기준**:
- [x] `domain/` 하위에 SQLAlchemy `Column`, `relationship` import 없음 (모델 정의 0건. 단 `domain/hub/shared/mail_owner_resolver.py`는 아직 `Session`/`func`로 쿼리 — 모델 정의는 아니므로 본 기준 충족, 추후 infrastructure로 이동 권장)
- [x] `alembic` metadata 집합 변경 없음 — baseline 6개 테이블(`competency_anchors, disclosures, employees, internal_addresses, mail_items, performance_records`)과 동일 확인
- [x] import 스모크(라우터·리졸버·repo·env 경로) 통과 / [ ] 실서버 API 동작은 이번 배포로 검증

**실제 이동(7개, `_orm` 접미사)**:
`employee→employee_orm, mail_item→mail_item_orm, disclosure→disclosure_orm, audit_log→audit_log_orm, competency_anchor→competency_anchor_orm, internal_address→internal_address_orm, performance_record→performance_record_orm`. importer 10개 파일 경로 갱신, `bases/__init__.py`에서 ORM(CompetencyAnchor) 재노출 제거. `infrastructure/persistence/models/__init__.py`는 의도적으로 모델 일괄 import 안 함(metadata 집합 보존).

---

### Phase 2 — Repository 이동 (✅ 완료, 2026-06-13)

**목표**: `domain/hub/repositories/` → `infrastructure/persistence/repositories/`

**이동 매핑**:
```
domain/hub/repositories/*.py → infrastructure/persistence/repositories/*.py
```

**import 업데이트 규칙**:
```python
# Before
from domain.hub.repositories.employee_repository import get_by_id

# After
from infrastructure.persistence.repositories.employee_repository import get_by_id
```

**완료 기준**:
- [x] `domain/hub/repositories/` 폴더 삭제 → `infrastructure/persistence/repositories/`로 이동
- [x] 전체 라우터/서비스 import 경로 업데이트 (16개 파일: 라우터2·application5·orchestration3·training5·worker1)
- [x] import 스모크 테스트 통과 (repo 패키지·employee_service·audit_service 임포트 OK)

---

### Phase 3 — Application Service Layer (2.5주, 리스크: 높음 — 핵심)

**도메인별로 순차 실행. PR 머지 조건: 해당 라우터에서 `domain.*` import 0개.**

> "해당 라우터에서 `domain.*` import가 0개인 걸 PR 머지 조건으로 잡으면 깔끔합니다." — 리뷰어 원문  
> `domain.models.enums.*` 같은 순수 Pydantic/Enum은 예외로 허용. 레포지토리·오케스트레이터 import가 0개여야 한다는 의미로 해석.

#### Phase 3a: Employee (✅ 완료)

- `application/employee/employee_service.py` — CRUD 전체 + analyze + embedding + backfill 메서드
- `employee_router.py` — `domain.*` import 0개 확인
- `employee_analysis_router.py` — `domain.*` import 0개 확인
- `employee_embedding_router.py` — `domain.*` import 0개 확인

**PR 머지 조건**: ✅ 3개 라우터 모두 `domain.hub.repositories.*` import 0개 달성

#### Phase 3b: Chat (0.5주)

대상: `chat_router.py`, `chat_thread_router.py`

```python
# application/chat/chat_service.py

class ChatService:
    """LangGraph 오케스트레이터 위임. 직접 비즈니스 로직 없음 — 얇은 퍼사드."""

    def run_stream(self, user_text, provider, system_prompt, chat_history, thread_id, images):
        from infrastructure.orchestration.chat_orchestrator import run_agent_stream
        return run_agent_stream(...)

    def get_thread_history(self, thread_id: str):
        from infrastructure.orchestration.chat_orchestrator import get_thread_history
        return get_thread_history(thread_id)

    def clear_thread(self, thread_id: str) -> bool:
        from infrastructure.orchestration.chat_orchestrator import clear_thread_history
        return clear_thread_history(thread_id)
```

**PR 머지 조건**: `chat_router.py`, `chat_thread_router.py`에서 `domain.hub.orchestrators.*` import 0개

#### Phase 3c: Mail (✅ 완료)

**완료된 것**:
- `application/mail/mail_service.py` 생성
- `email_router.py` → `MailService.*` 위임 완료
- `application/address_book/address_book_service.py` 생성 (직원 + 공용함·그룹 통합)
- `address_book_router.py` → `AddressBookService.*` 위임 완료

**PR 머지 조건**: `email_router.py`, `address_book_router.py`에서 `domain.hub.repositories.*` import 0개 ✅

#### Phase 3d: Disclosure (⚠️ 진행 중 — 서비스/라우터 완료, import 조건 재확인 필요)

**완료된 것**:
- `application/disclosure/disclosure_service.py` 생성
- `disclosure_router.py` → `DisclosureService.*` 위임 완료

**PR 머지 조건**: `disclosure_router.py`에서 `domain.hub.repositories.*` import 0개

#### Phase 3e: Audit 정리 (✅ 완료)

`api/routers/_employee_shared.py` → `application/shared/audit_service.py`로 이동 완료.  
`entity_type="employee"` 하드코딩 제거, 파라미터화하여 Mail, Disclosure 감사로그도 동일 함수 사용 가능.  
`_employee_shared.py` 파일 삭제 완료.

```python
# _employee_shared.py → application/shared/audit_service.py 로 이동
def write_audit_log(
    db: Session,
    *,
    request: Request,
    entity_type: str,      # "employee" | "mail" | "disclosure" 등
    action: str,
    entity_id: str,
    before_data=None,
    after_data=None,
    reason=None,
) -> None: ...
```

---

### Phase 4 — 인프라 어댑터 이동 (✅ 완료, 리스크: 중)

**목표**: LLM·메일·오케스트레이터를 `infrastructure/`로 이동

**이동 매핑**:

| 현재 | 이동 후 | 비고 |
|------|---------|------|
| `domain/hub/llm/exaone_adapter.py` | `infrastructure/llm/exaone_adapter.py` | 로직 변경 없음, 위치만 이동 |
| `domain/hub/llm/llama_adapter.py` | `infrastructure/llm/llama_adapter.py` | 로직 변경 없음 |
| `domain/hub/llm/gemini_adapter.py` | `infrastructure/llm/gemini_adapter.py` | 로직 변경 없음 |
| `domain/hub/llm/__init__.py` | `infrastructure/llm/__init__.py` | `get_provider_name` 등 팩토리 함수 — **로직 변경 없음, 위치만 이동** |
| `domain/hub/mail/providers/mailgun.py` | `infrastructure/mail/mailgun_adapter.py` | 로직 변경 없음 |
| `domain/hub/orchestrators/chat_orchestrator.py` | `infrastructure/orchestration/chat_orchestrator.py` | LangGraph 그래프 — 인프라로 분류 |
| `domain/hub/orchestrators/email_classify_orchestrator.py` | `infrastructure/orchestration/email_orchestrator.py` | 로직 변경 없음 |
| `domain/hub/orchestrators/spam_orchestrator.py` | `infrastructure/orchestration/spam_orchestrator.py` | 로직 변경 없음 |
| `domain/models/states/langgraph_state.py` | `infrastructure/orchestration/states/langgraph_state.py` | LangGraph TypedDict — 인프라 상태 |
| `domain/models/bases/exaone_model.py` | `infrastructure/llm/exaone_hf_model.py` | HuggingFace 구현체 + `core.llm` 의존 |

> **`domain/hub/llm/__init__.py` 주의**: Phase 4에서 위치는 `infrastructure/llm/__init__.py`로 이동한다.  
> 하지만 `get_provider_name`, `get_llm`, `list_providers` 등의 **로직은 변경하지 않는다**.  
> "건드리지 말 것"의 의미는 위치가 아닌 로직을 건드리지 말라는 것이다.

**핵심 결정: LangGraph는 포트로 추상화하지 않는다**

LangGraph StateGraph, 조건부 엣지, 체크포인터는 프레임워크 특화 개념이다.  
구현체가 하나인 포트는 의미없는 보일러플레이트다.  
`infrastructure/orchestration/`에 두고, `application/chat/chat_service.py`에서 직접 import.

**완료 기준**:
- [ ] `domain/` 하위에 `langchain`, `langgraph`, `langchain_core` import 없음
- [ ] `domain/` 하위에 LLM 로딩 코드 없음
- [ ] `domain/models/states/langgraph_state.py` 이동 완료

---

### Phase 5 — 스타 토폴로지 경계 정리 (✅ 완료, 리스크: 낮음)

**방향 변경**: spokes를 통합하지 않고 **스타 토폴로지를 유지**한다.
- hub(infrastructure)는 중앙 — LLM·DB·Mail 공용 도구 제공
- spokes는 도메인 피처 — hub 도구를 사용, 스포크끼리 직접 통신 금지
- hub → spoke 호출은 허용 (오케스트레이터가 스포크 서비스 호출)
- spoke → hub 도구 사용은 허용 (spoke가 LLM·DB 사용)
- spoke → spoke 직접 import 금지

**완료된 작업**:
- `domain/spokes/soccer/` 삭제 (테이블 드롭 완료, 전체 죽은 코드)
- `domain/spokes/chat/agents/`, `services/`, `retrievers/` 삭제 (1줄 stub + 빈 폴더)
- `domain/spokes/chat/mcp/chat_server.py` 유지 (허브 도구 사용하는 실제 구현)
- `domain/spokes/spam/` 전체 유지 (완전한 도메인 피처 구현)
- `infrastructure/llm/llama_classifier.py` (LLaMAGate) 유지 — hub→spoke 올바른 방향

**현재 spokes 구조**:
```
spokes/
  chat/mcp/chat_server.py     ← hub MCP 도구 사용하는 채팅 스포크
  spam/services/              ← LLaMA 분류기, 룰/정책 서비스
  spam/repositories/          ← 룰·정책 DB 접근
  spam/agents/                ← 스팸 에이전트
  spam/mcp/                   ← 스팸 MCP 서버
```

**삭제 대상 (잔여)**:
- `domain/hub/service/` (현재 비어있는 폴더)
- `core/llm/` (Phase 4 완료 후 삭제 가능 — 먼저 의존 확인 필요)

#### 5b. MCP 별도 처리 (주의)

`domain/hub/mcp/central_control_server.py`, `http_client.py` 등은 단순 폴더 이동이 아니다.  
MCP 서버는 별도 인바운드 어댑터(FastAPI lifespan에서 마운트됨)이므로:

- 이동 목적지: `infrastructure/mcp/` (아웃바운드) 또는 `api/mcp/` (인바운드)
- `fastapi_server.py`의 lifespan 마운트 코드도 함께 수정 필요
- 라이프사이클 관리 (`@asynccontextmanager`) 재검토 필요

**MCP 이동 시 체크리스트**:
- [ ] `central_control_server.py` 역할: 인바운드 어댑터 (MCP 프로토콜 서버)
- [ ] `http_client.py` 역할: 아웃바운드 어댑터 (MCP 도구 호출 클라이언트)
- [ ] 두 파일의 이동 목적지가 다를 수 있음 — 역할 확인 후 결정

---

### Phase 6 — Port 인터페이스 정의 (⏸️ 의도적 보류, 2026-06-14)

**보류 결정 근거**: 고려 조건이 현재 충족되지 않음 —
- DB 전환 계획 없음(Neon Postgres 고정)
- 테스트 스위트가 아직 없음(무-DB Service 테스트 수요 없음)
- 멀티 LLM 제공자는 **이미 함수형 provider 패턴으로 구현됨**(`llm_provider` + `get_provider_name`/`list_providers`/`supports_tool_calling`)

→ 지금 Port(ABC/Protocol)를 도입하면 실익 없이 추상화·DI 배선만 늘어남(YAGNI). **트리거 발생 시 해당 부분만 도입**:
- 테스트 스위트 착수 → 그 Service 의존만 Port화(mock 주입)
- 새 LLM 제공자/DB 실제 추가 → 해당 어댑터만 Port화

**현실적 조언**: 팀이 작거나 단일 DB/LLM 환경이면 Phase 6는 불필요.  
다음 조건 중 하나라도 해당하면 고려:
- PostgreSQL → 다른 DB 전환 가능성
- 단위 테스트에서 실제 DB 없이 Service 테스트가 필요
- 여러 LLM 제공자를 런타임에 선택 (현재 일부 구현됨)

**Repository 클래스화 여부**: 현재 함수형 레포지토리(`create(db, data)`)가 잘 동작 중이면 굳이 클래스화 불필요. Port 인터페이스만 ABC로 정의하고, 구현체는 함수형 래퍼로도 가능.

---

## 7. 마이그레이션 불필요 영역

다음은 현재 구조가 이미 적절하므로 **건드리지 말 것**:

| 항목 | 이유 |
|------|------|
| `core/config.py` | Pydantic Settings — 완벽한 위치 |
| `core/database/` | SessionLocal, get_db — 올바른 인프라 계층 |
| `gateway/middleware.py` | CORS/라우터 등록 분리 — 이미 올바름 |
| `domain/hub/llm/` (로직) | 어댑터 패턴 — 위치는 Phase 4에서 변경, 로직 불변 |
| `alembic/` | 마이그레이션 파일 자체는 건드리지 않음 (env.py import만 수정) |
| `training/` | 학습 파이프라인은 도메인과 분리된 독립 영역 |

---

## 8. 최종 의존성 규칙

```
api/     →  application/  →  domain/     ←  infrastructure/
(얇게)      (유스케이스)    (순수 엔티티)   (ORM, LLM, 외부 API)
```

- `domain/`은 `infrastructure/`를 import하지 않는다
- `api/`는 `infrastructure/`를 직접 import하지 않는다 (application/ 경유)
- `application/`은 `domain/ports/`를 통해 `infrastructure/`를 간접 사용 (Phase 6 구현 시)

---

## 9. 실행 순서 체크리스트

```
[ ] Phase 1: ORM 모델 이동 (7개 파일 — 분류표 확인 필수)
[ ] Phase 2: Repository 이동 (domain/hub/repositories → infrastructure/persistence/repositories)
[ ] Phase 3a: EmployeeService (✅ 완료)
[ ] Phase 3b: ChatService (chat_router + chat_thread_router)
[✅] Phase 3c: MailService + AddressBookService (완료)
[✅] Phase 3d: DisclosureService (완료)
[✅] Phase 3e: AuditService 정리 (entity_type 파라미터화, _employee_shared.py 삭제)
[✅] Phase 4: 인프라 어댑터 이동 (llm, mail, orchestrators, langgraph_state) — re-export stub 방식으로 backward-compat 유지
[✅] Phase 5a: 스타 토폴로지 유지 — 죽은 코드 정리 (soccer 삭제, chat 빈 폴더 삭제)
[ ] Phase 5b: MCP 별도 처리 (역할 확인 후 결정)
[ ] Phase 6: Port 인터페이스 정의 (선택)
```

**Phase 3 (Application Service)가 핵심이다.** Phase 3만 완료해도 테스트 가능성과 유지보수성이 크게 향상된다. 나머지 Phase는 폴더 재구성이지만, Phase 3은 실제 비즈니스 로직을 재구성하는 단계다.
