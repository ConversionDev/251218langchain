# 메일 시스템 전환 — 남은 작업 순서 (상세)

기본 폴더·빈 .py는 만들어 둔 상태를 기준으로, **실행 순서에 맞게** 남은 작업을 정리했습니다.  
의존 관계: 1 → 2 → 3 → 4 → 5 순으로 진행하는 것이 안전합니다.

---

## 보완 원칙 (반드시 유지)

- **external_id UNIQUE:** 멱등 처리의 전제. **024 마이그레이션에서 이미 `external_id` UNIQUE INDEX 있음.** 027 적용 전 024가 적용돼 있는지 확인. 없으면 027 또는 별도 마이그레이션에서 UNIQUE 보장.
- **status vs ai_status 분리**  
  - **status** = 메일 **도메인** 상태 (수신 성공/실패): `RECEIVED` | `REJECTED`  
  - **ai_status** = **AI 처리** 상태: `PENDING` | `PROCESSING` | `SUCCESS` | `FAILED`  
  두 개념을 섞지 말 것. REJECTED 건은 AI를 타지 않으므로 `ai_status = NULL`.
- **REJECTED 시:** `status = REJECTED`, `ai_status = NULL`, **`folder = NULL`**, **`spam_score = NULL`** (프론트 조건 분기 명확).

---

## 1단계: DB 및 기초 인프라

### 1.1 Enum 정의 (상태 전이 엄격화)

- **파일:** `app/domain/models/enums/mail_enums.py` (또는 기존 enums 폴더에)
- **내용:**
  - **AiStatus** (enum.Enum): `PENDING`, `PROCESSING`, `SUCCESS`, `FAILED`  
    코드 전반에서 문자열 대신 이 Enum 사용 → 오타 방지.
  - **MailReceiveStatus** (enum.Enum): `RECEIVED`, `REJECTED`  
    수신 도메인 상태 전용.
  - DB/마이그레이션에는 `.value`(문자열)로 저장.

### 1.2 마이그레이션 파일 추가

- **파일:** `app/alembic/versions/027_mail_items_ai_status_status_spam_score.py` (또는 다음 번호)
- **down_revision:** `026_internal_addr_owner` (현재 최신)
- **내용:**
  - `mail_items` 테이블에 컬럼 추가:
    - `ai_status`: VARCHAR(16), nullable=True, **server_default='PENDING'**.  
      값: `PENDING` | `PROCESSING` | `SUCCESS` | `FAILED` (Enum value).  
      수신 성공 시 항상 PENDING이면 기본값으로 두고, REJECTED는 명시적으로 NULL 저장 → 저장 로직 단순.
    - `status`: VARCHAR(16), nullable=True.  
      값: `RECEIVED` | `REJECTED` (수신 건만 사용)
    - `spam_score`: Float 또는 Numeric(5,4), nullable=True.
    - `processed_at`: DateTime, nullable=True.  
      워커가 PROCESSING으로 바꾼 시각 (또는 처리 완료 시각). 워커 쿼리·인덱스용.
    - **운영/장애 대응용:**
      - `retry_count`: Integer, default 0. AI 실패 시 +1.
      - `last_failed_at`: DateTime, nullable. 마지막 실패 시각.
      - `ai_result_raw`: Text, nullable. 실패 시 에러 메시지 또는 AI 원시 응답 저장.
  - **인덱스:**  
    - `(ai_status, processed_at)` **복합 인덱스**  
      워커가 `WHERE ai_status = 'PENDING'` 조회 시 전체 테이블 스캔 방지.
  - **기존 데이터:** 기존 행은 `ai_status = 'SUCCESS'` 또는 `NULL`, `status = NULL` backfill.

### 1.3 ORM 모델 수정

- **파일:** `app/domain/models/bases/mail_item.py`
- **내용:**
  - `ai_status`, `status`, `spam_score`, `processed_at`, `retry_count`, `last_failed_at`, `ai_result_raw` 컬럼 추가.
  - 코드에서는 `domain.models.enums.mail_enums.AiStatus`, `MailReceiveStatus`를 import해 사용하고, DB에는 `.value` 저장.

### 1.4 상태 전이 정리 (문서/상수)

- **위치:** `app/domain/hub/repositories/mail_item_repository.py` 상단 docstring 또는 `app/domain/hub/mail/constants.py`
- **내용:**
  - **수신 직후:**  
    - Resolver 성공 → `status=RECEIVED`, `ai_status=PENDING`  
    - Resolver 실패 → `status=REJECTED`, **`ai_status=NULL`** (워커 미처리)
  - **워커:** `PENDING` → `PROCESSING` (processed_at 설정) → `SUCCESS` or `FAILED`  
    FAILED 시 `retry_count += 1`, `last_failed_at`, `ai_result_raw` 기록.

---

## 2단계: 수신 공급자 계층 + Store-then-Process

### 2.1 정규화 스키마 (Normalized Inbound Mail)

- **파일:** `app/domain/hub/mail/schemas.py` (없으면 생성)
- **내용:**
  - `NormalizedInboundMail` (TypedDict 또는 Pydantic):  
    `to_email`, `from_display`, `from_email`, `subject`, `body`, `message_id`, `received_at` (datetime 또는 ISO 문자열)  
    공급자(Mailgun/SES)와 무관한 우리 도메인 기준 필드만 정의.

### 2.2 공급자 추상화

- **파일:** `app/domain/hub/mail/providers/base.py`
- **내용:**  
  **verify와 parse를 나누지 말고 `parse_and_verify(request) -> NormalizedInboundMail` 하나로만 둔다.**  
  실패 시 예외. 호출부에서 verify를 빠뜨리는 실수를 방지.

### 2.3 Mailgun 어댑터 구현 (Mailgun 특수성)

- **파일:** `app/domain/hub/mail/providers/mailgun.py`
- **중요:** Mailgun은 JSON이 아니라 **multipart/form-data**로 전송합니다.
- **내용:**
  - **진입점은 `parse_and_verify(request)` 하나.**  
    내부에서 form 파싱 + HMAC-SHA256 검증 후 `NormalizedInboundMail` 반환. 실패 시 예외.
  - **파싱:** FastAPI 라우터에서 `Form(...)` 또는 `Request` body를 파싱해 dict로 넘기거나, Request를 그대로 넘겨 어댑터에서 파싱.  
    필드: `recipient`, `sender`, `subject`, `body-plain`, `Message-Id`, `timestamp`, `token`, `signature` 등.
  - 성공 시에만 `NormalizedInboundMail` 반환.
- **설정:** `app/core/config.py`에 `mailgun_webhook_signing_key: Optional[str]` (환경 변수) 추가.  
  Mailgun 대시보드에서 “Webhook Signing Key” 값 사용.

### 2.4 메일 수신 패키지 init

- **파일:** `app/domain/hub/mail/__init__.py`, `app/domain/hub/mail/providers/__init__.py`
- **내용:**  
  `schemas`, `providers.base`, `providers.mailgun` 노출.  
  라우터에서 `from domain.hub.mail import ...` 로 사용 가능하게.

### 2.5 Repository 확장 (저장·조회)

- **파일:** `app/domain/hub/repositories/mail_item_repository.py`
- **내용:**
  - **create:**  
    인자 추가: `ai_status`, `status`, `spam_score` (선택).  
    수신 건은 `ai_status='PENDING'`, `status='RECEIVED'` or `'REJECTED'` 로 저장.
  - **update:**  
    `ai_status`, `spam_score`, `folder` 업데이트 가능하도록 인자 추가 (워커에서 사용).
  - **_row_to_dict:**  
    응답에 `aiStatus`, `status`, `spamScore` 포함 (camelCase).
  - **list_pending_for_worker (신규, 필수):**  
    `ai_status='PENDING'` and `status='RECEIVED'` 인 행을 limit 건 조회할 때  
    **반드시 `SELECT ... FOR UPDATE SKIP LOCKED`** 사용.  
    여러 워커가 동시에 떠 있어도 한 행을 한 워커만 가져가도록 하여 중복 처리·경쟁 제거.
  - **set_processing / set_success / set_failed:**  
    상태 전이 + `processed_at`, `retry_count`, `last_failed_at`, `ai_result_raw` 반영 전용 함수 권장.

### 2.6 수신 API 전환 (Store-then-Process)

- **파일:** `app/api/routers/email_router.py`
- **내용:**
  - **수신 경로에서 `run_spam_detection()` 호출 제거.**  
    수신은 “저장만” 하고, 스팸 판정은 워커가 담당.
  - **멱등성(Idempotency):**  
    `external_id`(Message-Id)로 이미 DB에 존재하면 **에러가 아닌 200 OK** 반환.  
    Mailgun이 네트워크 문제로 같은 메일을 재전송해도 재시도를 멈추게 함.
  - **Resolver 성공:** `status=RECEIVED`, `ai_status=PENDING`, `folder=inbox` 저장 후 201.
  - **Resolver 실패:** `status=REJECTED`, **`ai_status=NULL`**, **`folder=NULL`**, **`spam_score=NULL`** 로 저장 후 200.  
    (주소 없음도 DB에 남기기로 한 정책 시, `owner_employee_id` nullable 또는 placeholder)
  - **Mailgun 전용 경로:**  
    `POST /api/mail/receive/webhook/mailgun`  
    Request body는 **multipart/form-data**이므로 FastAPI에서 `Form(...)` 또는 `Request`로 받아  
    `domain.hub.mail.providers.mailgun`에 넘겨 verify+parse → 동일 저장 로직 호출.
  - **기존 POST /mail/receive (JSON):** 테스트용 유지 시, 위와 동일하게 스팸 판정 제거·멱등·REJECTED 시 ai_status=NULL 적용.
  - **성과/역량 분류:** 수신 API의 BackgroundTasks에서는 제거. 3단계 워커에서 스팸이 아닐 때만 연쇄 실행.

### 2.7 REJECTED 저장 시 스키마

- **도메인 의미:** REJECTED는 **도메인 상태(status)** 이며, AI는 타지 않음.  
  **반드시:** `status = REJECTED`, `ai_status = NULL`, **`folder = NULL`**, **`spam_score = NULL`**.  
  이렇게 하면 프론트에서 “수신 실패/미배정” 조건 분기가 깔끔해짐.
- **스키마:** 주소 없음도 DB에 넣기로 하면 `owner_employee_id`가 없는 행이 생김.  
  마이그레이션에서 `owner_employee_id` nullable 허용 또는 시스템용 placeholder(`__rejected__`) 사용 중 하나로 정책 확정.

---

## 3단계: 비동기 워커

### 3.1 워커 패키지

- **파일:** `app/workers/__init__.py`  
  (필요 시 `app/workers/tasks/__init__.py`, `app/workers/tasks/mail_pending.py` 등으로 분리 가능)

### 3.2 PENDING 처리 루프 (안전한 상태 변경)

- **파일:** `app/workers/mail_pending.py` (또는 `tasks/mail_pending.py`)
- **상태 변경 순서 (필수):**
  1. **SELECT ... FOR UPDATE SKIP LOCKED** 로 PENDING 1건(또는 N건) 조회  
  2. 해당 행 **`ai_status=PROCESSING`**, `processed_at=now()` 설정 후 **즉시 commit**  
  3. **그 다음** AI 실행 (classify_spam 등)  
  4. 결과에 따라 **SUCCESS 또는 FAILED로 업데이트** 후 commit  
  → PROCESSING을 먼저 커밋해야 워커가 죽었을 때 다른 워커가 같은 행을 다시 가져가서 중복 처리하는 일이 없다.
- **내용:**
  - **조회 시 반드시 `SELECT ... FOR UPDATE SKIP LOCKED`** (`list_pending_for_worker` 내부).
  - **(Phase 3)** 더미 처리 후 `ai_status=SUCCESS`  
  - **(Phase 4)** 더미 제거 후 `classify_spam` 호출 → `spam_score`, `folder` 반영, SUCCESS/FAILED
  - 예외 시: 해당 행 `ai_status=FAILED`, `retry_count += 1`, `last_failed_at`, `ai_result_raw` 기록 (4단계에서 상세화).
  - **유휴 시 부하 방지:** PENDING이 0건이면 **`time.sleep(1)`** (또는 env `MAIL_WORKER_POLL_INTERVAL_SEC`, 기본 1) 후 다시 조회. 처리한 건이 있을 때는 sleep 없이 다음 건 처리 → 백로그 있을 때는 빠르게, 비었을 때만 DB·CPU 절약.
- **실행:**  
  `python -m workers.mail_pending` (프로젝트 루트에서 `PYTHONPATH=app` 또는 `app` 패키지 환경)  
  또는 `uv run python -m workers.mail_pending`.

### 3.3 성과/역량 분류 위치 (연쇄 실행)

- **권장:** 스팸 워커의 **마지막 단계**에서, **스팸이 아닐 때만** 성과/역량 분류를 **연쇄(Chained)** 로 실행.
- **구현:**  
  스팸 처리로 `ai_status=SUCCESS`, `folder=inbox`로 확정된 뒤, 같은 워커 루프 안에서  
  `run_email_classify_and_record(db, subject=..., body=..., employee_id=owner_employee_id, ...)` 호출.  
  데이터 정합성(같은 트랜잭션/세션으로 “수신 → 스팸 판정 → inbox 확정 → 성과 분류”)을 한 흐름에서 유지.
- 수신 API의 BackgroundTasks 성과/역량 분류는 제거 (2.6에서 제거).

---

## 4단계: LLaMA 연동 (장애 대응)

### 4.1 워커에서 더미 제거 + 예외/타임아웃 처리

- **파일:** `app/workers/mail_pending.py`
- **내용:**
  - 더미 제거 후 `classify_spam` 호출.  
    **AI 타임아웃 명시 (예: 15초).** 무제한이면 워커가 멈춘다.
  - **try/except:**  
    성공 시: `spam_score`, `folder`(inbox/spam) 반영, `ai_status=SUCCESS`.  
    **실패 시(타임아웃·예외) 반드시:**
    - `ai_status = FAILED`
    - `retry_count += 1`
    - `last_failed_at = now()`
    - **`ai_result_raw = traceback 또는 error message`** (디버깅 가능하도록)
  - DB 컬럼 `ai_result_raw`, `retry_count`, `last_failed_at`은 1단계 마이그레이션에 포함.

### 4.2 실패 재시도 정책 (선택)

- **FAILED** 건을 일정 시간 후 `PENDING`으로 되돌릴지, 수동 재처리 API만 둘지 결정.  
  재시도 시 `retry_count` 상한으로 무한 재시도 방지 고려.  
  `mail_item_repository.reset_failed_to_pending(retry_max=N)` 등 추가 가능.

---

## 5단계: 실시간 UX 및 프론트

### 5.1 API 응답에 상태 필드 포함

- **파일:** `app/domain/hub/repositories/mail_item_repository.py`
- **확인:**  
  `_row_to_dict`에 `aiStatus`, `spamScore`, `status` 이미 추가했는지 확인.  
  없으면 추가 (1.2·2.5에서 반영했다고 가정).

### 5.2 프론트 타입·매핑

- **파일:** `frontend/app/workspace/mail/page.tsx`
- **내용:**
  - `MailApiItem`에 `aiStatus?`, `spamScore?`, `status?` 추가.
  - `MailItem`에 `aiStatus?` 추가.
  - `apiMailToMailItem`에서 `api.aiStatus` 등 매핑.

### 5.3 목록 행에 상태·폴더 표시

- **파일:** 동일 `page.tsx`
- **중요:**  
  **INBOX / SPAM 구분은 `folder` 값 기준으로만** 표시 (아이콘·배지).  
  **`ai_status`는 “분석 중 / 완료 / 실패” 표시용**으로만 사용 (시계·로딩·체크·경고).
- **내용:**  
  - 폴더: `folder === 'inbox'` vs `folder === 'spam'` 로 받은편지함/스팸함 아이콘·라벨 구분.  
  - 분석 상태: `aiStatus`가 PENDING/PROCESSING → 시계/로딩, SUCCESS → 체크, FAILED → 경고.  
  (Loader2, CheckCircle2, ShieldAlert 등 기존 import 활용)

### 5.4 폴링

- **파일:** 동일 `page.tsx`
- **내용:**  
  받은편지함/스팸함이 보일 때만 3~5초 간격으로 `fetchMailFolder` 호출.  
  탭 비활성화 시 폴링 중지, 포커스 시 재개(선택).

### 5.5 스팸 테스트 안내

- **파일:** 동일 `page.tsx` (스팸 테스트 패널)
- **내용:**  
  “전송됨. 분석 중입니다.” 메시지 + 폴링 또는 새로고침으로 결과 확인하도록 문구 정리.

---

## 체크리스트 요약 (순서)

| # | 작업 | 상태 |
|---|------|------|
| 0 | external_id UNIQUE 확인 (024에 있음. 027 전제) | |
| 1.1 | Enum: AiStatus, MailReceiveStatus (domain/models/enums) | |
| 1.2 | Alembic 027: ai_status(DEFAULT 'PENDING'), status, spam_score, processed_at, retry_count, last_failed_at, ai_result_raw, 복합 인덱스 (ai_status, processed_at) | |
| 1.3 | MailItem ORM + Enum 사용, 새 컬럼 반영 | |
| 1.4 | 상태 전이 문서/상수 (status vs ai_status, REJECTED 시 ai_status=NULL) | |
| 2.1 | domain/hub/mail/schemas.py — NormalizedInboundMail | |
| 2.2 | providers/base.py — **parse_and_verify(request)** 단일 진입점 | |
| 2.3 | providers/mailgun.py — **parse_and_verify** (form + HMAC) → NormalizedInboundMail | |
| 2.4 | domain/hub/mail __init__, providers __init__ | |
| 2.5 | mail_item_repository: create/update/row_to_dict 확장, **list_pending_for_worker (SELECT FOR UPDATE SKIP LOCKED)** | |
| 2.6 | email_router: 스팸 판정 제거, 멱등(200 OK), REJECTED 시 ai_status/folder/spam_score NULL, Mailgun 경로(Form) | |
| 2.7 | REJECTED 저장 시 owner_employee_id 정책, folder/spam_score NULL 명시 | |
| 3.1 | workers/__init__.py | |
| 3.2 | workers/mail_pending.py — **SELECT FOR UPDATE → PROCESSING commit → AI → SUCCESS/FAILED** 순서 준수 | |
| 3.3 | 성과/역량 분류: 스팸 워커 마지막 단계에서 folder=inbox일 때만 연쇄 실행 | |
| 4.1 | 워커: classify_spam + **timeout(예: 15s)**, 실패 시 FAILED + retry_count + last_failed_at + **ai_result_raw=traceback/메시지** | |
| 4.2 | (선택) FAILED 재시도 정책 / retry_max | |
| 5.1 | API 응답에 aiStatus, spamScore, status 등 포함 확인 | |
| 5.2 | 프론트 MailApiItem, MailItem, apiMailToMailItem 확장 | |
| 5.3 | 목록: **folder 기준** inbox/spam 구분, **ai_status 기준** 분석 중/완료/실패 아이콘 | |
| 5.4 | 받은편지함/스팸함 폴링 | |
| 5.5 | 스팸 테스트 패널 문구·동작 정리 | |

이 순서대로 진행하면 Store-then-Process, 멱등성, 동시 워커 안전성, 장애 시 기록까지 포함한 운영 가능한 파이프라인으로 적용할 수 있습니다.
