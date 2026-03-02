# 실제 운영 가능한 AI 사내 메일 시스템 — 실행 로드맵 전략

> 목표: **안정성 우선** → 그 위에 **AI 엔진**을 얹는 단계적 구축.  
> 이 문서는 제시된 5단계 로드맵에 대한 **실무 관점 검토**와 **갭 분석·실행 전략**을 담습니다.

---

## 1. 로드맵에 대한 실무적 평가

### ✅ 잘 잡힌 점

| 항목 | 평가 |
|------|------|
| **Store-then-Process** | 수신부는 “빠르게 저장 후 200”만 담당. Mailgun 타임아웃·재시도로 인한 유실 방지에 정확히 부합. |
| **Decoupling** | 수신(Fast) vs 처리(Slow) 분리로 부하·장애 격리. 워커 지연/다운이 수신 유실로 이어지지 않음. |
| **HMAC 검증** | 외부 Webhook 위변조·재생 공격 차단. 실서비스 필수. |
| **상태 기반 처리** | `ai_status`(PENDING→PROCESSING→SUCCESS/FAILED)로 재시도·모니터링·디버깅이 명확해짐. |
| **순서** | DB/인프라 → 수신 → 워커 → AI → UX 순서가 합리적. “기록부” 없이 워커·AI를 붙이면 추적이 어렵고, 수신이 느리면 Mailgun이 끊음. |

### ⚠️ 현재 코드와의 갭 (반드시 정리할 부분)

| 단계 | 로드맵 기대 | 현재 코드 상태 | 갭 |
|------|-------------|----------------|------|
| **1. DB** | `ai_status`, `status`, `spam_score`, `external_id` UNIQUE, 상태 전이 정의 | `external_id`, `received_at`만 있음. `ai_status`/`status`/`spam_score` 컬럼·전이 없음 | **마이그레이션 + 도메인 전이 정의** 필요 |
| **2. 수신부** | HMAC 검증, **즉시 저장만**, AI 호출 없음, 주소 매핑 실패 시에도 **DB에 기록 후 200** | HMAC 없음. **수신 경로에서 `run_spam_detection()` 동기 호출** → LLaMA 지연 시 Mailgun 타임아웃 위험. Resolver 실패 시 404, **DB 미저장** | **HMAC 추가**, **Store-then-Process 전환**(스팸 판정 제거), **REJECTED도 저장** 정책 결정 |
| **3. 워커** | PENDING 폴링 → PROCESSING → (더미/실제 AI) → SUCCESS | **별도 워커 프로세스 없음**. `BackgroundTasks`는 inbox 성과/역량 분류만 사용. PENDING 처리 루프 없음 | **워커 진입점·스케줄/폴링 방식** 신규 구현 |
| **4. AI** | 더미 → `llama_manager.classify_spam()` 교체 | `classify_spam` 경로는 존재(hub → llama_adapter → llama_manager). **워커와 연결**만 하면 됨 | 워커에서 호출 포인트 연결 |
| **5. UX** | 목록에 `ai_status` 아이콘, Polling/SSE | API·모델에 `ai_status` 없음. 프론트에 상태 표시 없음 | **API 필드 추가 + 프론트 상태 표시** |

**핵심 결론:**  
- **2단계(수신부)** 가 지금 가장 위험. 수신 시 **동기 스팸 판정**을 하고 있어, “Store-then-Process”와 반대. Mailgun 재시도·타임아웃 시 유실·중복 시나리오가 생길 수 있음.  
- **1단계(DB)** 를 먼저 넣고, **2단계에서 수신부를 “저장만”** 으로 바꾼 뒤, **3단계 워커**가 스팸 판정을 담당하도록 가져가는 것이 실무적으로 맞는 순서입니다.

---

## 2. 단계별 실행 전략

### 📅 1단계: DB 및 기초 인프라 (Day 1)

**목표:** 메일의 “기록부”와 상태 전이를 코드·스키마에 명시.

- **마이그레이션**
  - `mail_items`에 추가:
    - `ai_status`: `PENDING` | `PROCESSING` | `SUCCESS` | `FAILED` (기본값 `PENDING`). nullable이면 기존 행은 `NULL` 또는 `SUCCESS`로 backfill 규칙 명시.
    - `status`: `RECEIVED` | `REJECTED` (주소 매핑 성공/실패). 수신 건만 사용, 기본값 `RECEIVED`.
    - `spam_score`: LLaMA 점수 저장용 (실수 또는 정규화된 0–1). nullable.
  - `external_id` UNIQUE는 이미 있음(024). 인덱스는 `ai_status`(워커 쿼리용) 추가 검토.

- **상태 전이 (코드로 정의)**
  - 수신 직후: `status=RECEIVED` or `REJECTED`, `ai_status=PENDING` (RECEIVED인 경우만 워커가 처리).
  - 워커 진입: `PENDING` → `PROCESSING` (선택: `processed_at` 타임스탬프).
  - 워커 완료: `PROCESSING` → `SUCCESS` or `FAILED`, `spam_score`·`folder`(inbox/spam) 반영.
  - 전이 규칙을 한곳(예: `domain/hub/repositories/mail_item_repository.py` 또는 전용 `mail_state.py`)에 문서화하고, 워커·API는 그 규칙만 사용하도록 유지.

- **실무 포인트**
  - 기존 `mail_items` 행에 대해 `ai_status` backfill 정책 결정 (예: 모두 `SUCCESS` 또는 `NULL`로 “이미 처리됨” 처리).
  - 워커가 “한 번에 하나만 PROCESSING”으로 가져가면 동시성은 단순. 나중에 멀티 워커 시 `SELECT ... FOR UPDATE SKIP LOCKED` 패턴 고려.

---

### 📧 2단계: Mailgun 수신부(Receiver) (Day 2)

**목표:** “유실 없이 받기”. Webhook은 **저장 + 200** 만 책임.

- **HMAC-SHA256 검증**
  - Mailgun이 보내는 `timestamp` + `token`을 API Key로 서명한 값과 요청의 `signature` 비교.
  - 검증 실패 시 **401/403**, DB 저장·AI 호출 없음.
  - 검증 로직을 미들웨어 또는 의존성으로 두고, `/api/mail/receive` 전용으로 적용.

- **Store-then-Process**
  - **수신 핸들러에서 `run_spam_detection()` 제거.**  
  - Resolver(To → owner_employee_id)만 수행:
    - **성공:** `status=RECEIVED`, `ai_status=PENDING`, `folder=inbox`(기본)으로 저장. 201 + body.
    - **실패(주소 없음):** 로드맵대로라면 “결과가 어떻든 DB에 넣은 뒤 200”이므로, `status=REJECTED`, `owner_employee_id`는 null 또는 시스템용 placeholder, 별도 폴더(예: `rejected`) 또는 `folder=inbox` + 플래그로 저장. 정책에 따라 200 또는 202 반환.
  - 저장 후 **어떤 AI 호출도 하지 않음.** 성과/역량 분류도 **워커에서 SUCCESS 이후** 또는 별도 워커 태스크로 이전 권장.

- **Mailgun 페이로드 매핑**
  - Mailgun Webhook 필드(recipient, sender, subject, body-plain, Message-Id 등) → `ReceiveMailBody` 또는 내부 DTO로 매핑. `external_id` = Message-Id. 중복이면 **409** (이미 저장됨) 또는 **200** (멱등) 중 하나로 정책 통일.

- **실무 포인트**
  - “주소 없음 → DB에 넣을지”는 운영 정책. 넣으면 추적·재처리 가능; 안 넣으면 404 유지. 로드맵대로라면 “넣고 200”.
  - 수신 API는 짧은 타임아웃(예: 5초) 목표. DB 쓰기 + HMAC만 수행하도록 유지.

---

### ⚙️ 3단계: 비동기 백그라운드 워커 (Day 3–4)

**목표:** “DB에 쌓인 PENDING을 처리하는 심장”.

- **워커 진입점**
  - 별도 프로세스(스크립트 또는 Celery/ARQ 등)에서 주기적으로:
    - `ai_status=PENDING` and `status=RECEIVED`(및 필요 시 `folder=inbox`)인 행을 1건 또는 N건 조회.
    - 선택: `SELECT ... FOR UPDATE SKIP LOCKED`로 동시 워커 시 중복 처리 방지.
  - 조회 후 즉시 `ai_status=PROCESSING`으로 업데이트 (같은 트랜잭션 또는 바로 다음 업데이트).

- **처리 내용 (Phase 3 시점)**
  - **더미:** 항상 “정상 메일”(folder 유지, spam_score=0 또는 null). `ai_status=SUCCESS`로 업데이트.
  - **Phase 4 이후:** 더미 대신 `llama_manager.classify_spam()`(또는 기존 `run_spam_detection`의 “스팸 판정만” 호출) 호출 → `spam_score`, `folder`(inbox/spam) 반영 후 `ai_status=SUCCESS` or `FAILED`.

- **실패 처리**
  - 예외/타임아웃 시 `ai_status=FAILED`, 필요 시 `updated_at` 또는 별도 `last_error` 컬럼에 요약 저장. 재시도는 다음 폴링에서 PENDING만 다시 가져가도록 하거나, FAILED를 일정 시간 후 PENDING으로 되돌리는 정책 선택.

- **실무 포인트**
  - 워커를 “같은 앱 내 BackgroundTasks”가 아니라 **별도 프로세스**로 두면, 앱 재시작·스케일링과 독립적으로 워커만 늘릴 수 있음.
  - 폴링 간격(예: 5초)과 배치 크기는 부하에 맞게 조정. 초기에는 1건씩 처리해도 무방.

---

### 🤖 4단계: LLaMA AI 모델 완성 (Day 5–7)

**목표:** 워커의 “더미”를 실제 스팸 분류로 교체.

- **데이터·학습**
  - ExaOne 합성 SFT 데이터 정제 후 `train.jsonl`/`val.jsonl` 확정. 기존 경로(`app/data/spam/sft/`, `training.models.llama.spam_classifier.finetune`) 활용.
  - LoRA 파인튜닝 후 어댑터를 `get_llama_adapters_dir()` 등 기존 정책에 맞게 저장.

- **연결**
  - 워커에서 `classify_spam(email_metadata)` 호출 → `spam_score`, `action`(deliver/spam 등) 받아서 `mail_items`의 `spam_score`, `folder` 업데이트 후 `ai_status=SUCCESS`/`FAILED`.

- **실무 포인트**
  - AI 실패(예: LLaMA 다운, 타임아웃)는 `ai_status=FAILED`로 두고, 재시도 또는 수동 재처리 플로우를 두면 운영이 수월함.

---

### 💻 5단계: 실시간 UX 및 프론트 연결 (Day 8)

**목표:** “분석 중/완료”를 사용자에게 보여주기.

- **API**
  - 메일 목록·단건 응답에 `ai_status`(, `spam_score`, `status`) 필드 포함. `mail_item_repository._row_to_dict` 및 라우터 응답 모델에 추가.

- **프론트**
  - 목록에서 `ai_status`에 따라 아이콘: PENDING/PROCESSING → 시계/로딩, SUCCESS → 체크, FAILED → 경고.
  - **Polling:** 3–5초마다 목록 또는 “내 메일 요약” API 호출. 구현 단순, 서버 부하는 간격으로 조절.
  - **SSE(선택):** 상태 변경 시 이벤트를 보내면 즉시 반영 가능. 초기에는 Polling으로 출시하고, 필요 시 SSE 도입해도 됨.

- **실무 포인트**
  - 목록 페이지에서만 폴링해도 충분한 경우가 많음. “메일함” 열려 있을 때만 폴링하고, 탭 비활성화 시 멈추면 리소스 절약.

---

## 3. 리스크와 완화

| 리스크 | 완화 |
|--------|------|
| Mailgun이 재시도 시 동일 메일 중복 전달 | `external_id` UNIQUE로 1건만 저장. 두 번째 요청은 409 또는 200(멱등)으로 처리. |
| 수신부에서 LLaMA 호출로 타임아웃 | 2단계에서 스팸 판정 제거, “저장만” 하도록 전환. |
| 워커 지연으로 “분석 중”이 길어짐 | 5단계에서 시계/로딩 아이콘으로 기대치 관리; 워커 스케일 또는 배치 크기 조정. |
| LLaMA 장애 시 PENDING 쌓임 | `ai_status=FAILED`로 기록하고, 모니터링·알람. 필요 시 수동 재처리 또는 FAILED→PENDING 복구 스크립트. |
| 주소 없음 수신 건 처리 | 2단계에서 “REJECTED로 DB 저장 후 200”으로 정책 고정하면, 나중에 주소록 보강 후 재매핑 가능성 열어둠. |

---

## 4. 순서 요약 (실무 권장)

1. **1단계** — DB 마이그레이션 + `ai_status`/`status`/`spam_score` + 상태 전이 문서화.  
2. **2단계** — HMAC 추가, 수신부에서 **스팸 판정 제거**, Store-then-Process + (선택) REJECTED 저장.  
3. **3단계** — PENDING 폴링 워커, 더미 처리로 SUCCESS까지 흐름 검증.  
4. **4단계** — 더미 → `classify_spam()` 연결, 학습·어댑터 반영.  
5. **5단계** — API에 상태 필드, 프론트 아이콘 + Polling(필요 시 SSE).  

이 순서를 지키면 “수신 유실·타임아웃” 리스크를 먼저 제거한 뒤, 워커와 AI를 붙이는 구조가 되어 실무적으로 안전합니다.

---

## 5. 최종 결과물 (포트폴리오 포인트) — 유지

- **신뢰성:** Mailgun Webhook을 비동기(Store-then-Process)로 처리해 메일 유실률 0% 지향.  
- **보안:** HMAC 서명 검증으로 위변조·재생 공격 차단.  
- **지능화:** ExaOne 합성 + LLaMA LoRA로 도메인 적응 스팸 차단.  
- **확장성:** 수신·스팸 판정·공급자(Mailgun↔SES)를 인터페이스/워커로 분리해 교체 용이.  

이 문서를 실행 시 체크리스트로 사용하면, “실제 운영 가능한 AI 사내 메일 시스템” 목표에 맞게 단계를 밟을 수 있습니다.
