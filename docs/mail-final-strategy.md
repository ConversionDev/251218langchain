# 메일 시스템 전환 — 최종 전략 정리

코드 전환을 실행하기 **전**에, 지금까지 논의한 내용을 한 번에 볼 수 있도록 정리한 문서입니다.  
실제 작업 순서·체크리스트는 `mail-operational-tasks.md`를 참고하고, 여기서는 **무엇을 왜 하는지**와 **확정된 선택**을 설명합니다.

---

## 1. 목표와 원칙

- **목표:** 개인 프로젝트이되 **실무 운영에 가깝게** 만든다.  
  설계·패턴은 실서비스 수준으로 두고, 구현 범위(워커 수, 자동화, 관리 UI)는 단계적으로 확장.

- **핵심 아키텍처**
  - **Store-then-Process:** 수신 API는 “저장 후 즉시 200/201”만 담당. AI 호출은 하지 않음.  
    → Mailgun 타임아웃·유실 방지.
  - **Decoupling:** 수신(Fast)과 처리(Slow) 분리. 워커 지연/장애가 수신 유실로 이어지지 않음.
  - **공급자 추상화:** `domain/hub/mail/` 에서 Mailgun → NormalizedInboundMail로 변환.  
    나중에 SES 등으로 바꿀 때 이 계층만 교체.

---

## 2. 상태 모델 (반드시 유지)

- **두 축을 섞지 않는다.**
  - **status** = 메일 **도메인** 상태 (수신 결과): `RECEIVED` | `REJECTED`
  - **ai_status** = **AI 처리** 상태: `PENDING` | `PROCESSING` | `SUCCESS` | `FAILED`

- **REJECTED:** 주소 매핑 실패 시  
  `status = REJECTED`, **ai_status = NULL**, **folder = NULL**, **spam_score = NULL**  
  → 워커 미처리. 프론트 조건 분기 명확.
- **external_id:** 멱등 전제. **024에서 UNIQUE INDEX 있음.** 적용 여부 확인.
- **ai_status:** 수신 성공 시 항상 PENDING → DB **DEFAULT 'PENDING'**. REJECTED만 명시적으로 NULL.

- **코드에서:** `AiStatus`, `MailReceiveStatus` Enum 사용. 문자열 하드코딩 금지.

---

## 3. 단계별 요약

| 단계 | 내용 |
|------|------|
| **1. DB·ORM** | ai_status, status, spam_score, processed_at, retry_count, last_failed_at, ai_result_raw 추가. Enum 정의. (ai_status, processed_at) 복합 인덱스. **processed_at = 처리 완료 시각**으로 통일. |
| **2. 수신** | **parse_and_verify(request)** 단일 진입점 (verify 분리 금지). HMAC + form 파싱 → NormalizedInboundMail. 멱등: external_id 존재 시 200 OK. 수신 시 스팸 판정 제거. REJECTED 시 folder/spam_score NULL. Mailgun=/webhook/mailgun, JSON=/receive 테스트용. |
| **3. 워커** | **순서 필수:** SELECT FOR UPDATE → PROCESSING **commit** → AI 실행 → SUCCESS/FAILED commit. (PROCESSING 먼저 커밋해야 워커 죽어도 중복 처리 안 됨.) 성과/역량은 folder=inbox일 때만 연쇄. |
| **4. LLaMA** | **타임아웃 명시(예: 15s).** 실패 시 ai_status=FAILED, retry_count+=1, last_failed_at, **ai_result_raw=traceback 또는 에러 메시지** (디버깅용). |
| **5. 프론트** | aiStatus로 “분석 중/완료/실패” 아이콘. **inbox vs spam 구분은 folder 기준만.** 폴링(받은편지함/스팸함). |

---

## 4. 확정된 전략 선택

구현 전에 “이렇게 하기로 했다”고 정해 둔 것들입니다.

| 항목 | 선택 |
|------|------|
| **Resolver 실패(주소 없음)** | REJECTED로 **DB에 저장**. 일반 메일함에는 노출하지 않음(owner_employee_id로 필터되므로 자동 제외). 관리자용 “미배정” 목록은 확장 시 추가. |
| **기존 메일(레거시)** | ai_status=NULL → **“이미 처리된 레거시”**로 간주. 프론트에서는 완료(체크)로 표시. 워커는 RECEIVED + PENDING만 처리하므로 기존 행 미처리. |
| **수신 경로** | Mailgun → **POST /api/mail/receive/webhook/mailgun** (Form, HMAC). 테스트 → **POST /api/mail/receive** (JSON). 경로 분리로 HMAC·로깅 명확화. |
| **processed_at** | **처리 완료 시각**으로 통일. SLA·지표용. |
| **성과/역량 분류 실패** | 메일은 **ai_status=SUCCESS 유지**. 실패는 로그만. 재시도는 수동 또는 별도 배치. |
| **개발 환경 HMAC** | **환경 변수로 검증 스킵** (예: MAILGUN_SKIP_VERIFY=true). 로컬에서 JSON/curl 테스트 용이. |
| **FAILED 재처리** | **우선 수동** (관리 API 또는 관리 UI “재처리” 버튼). 자동 재시도는 확장 단계에서. |
| **워커 개수** | **초기 1개.** 쿼리는 항상 FOR UPDATE SKIP LOCKED로 구현해 두고, 필요 시 프로세스만 2개 이상 띄워서 스케일 아웃. |

---

## 5. 확장 범위 (나중에 할 수 있는 것)

실무에 더 가깝게 가져가려면, 기본 전환 후 아래를 추가할 수 있습니다.

- **워커 수:** 동일 코드로 워커 프로세스 2개 이상 기동. 이미 SKIP LOCKED로 안전.
- **자동화:** FAILED 건을 주기적으로 PENDING으로 되돌리기(retry_count < N, last_failed_at 경과). PENDING 적체·워커 헬스 알람.
- **관리 UI:** 미배정(REJECTED) 목록, FAILED 목록 + “재처리” 버튼, PENDING/FAILED 개수·마지막 처리 시각.

---

## 6. 참고 문서

- **작업 순서·체크리스트:** `mail-operational-tasks.md`
- **로드맵·갭 분석:** `mail-operational-roadmap.md` (있다면)

이 문서와 작업 문서를 기준으로 1단계(DB)부터 순서대로 코드 전환을 진행하면 됩니다.
