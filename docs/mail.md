# 메일 시스템 — 통합 문서

메일 수신·스팸 분류·워커·메일건 연동을 한 문서에서 정리합니다.  
상위 전략은 [strategy.md](strategy.md) Part 1·3, 발송–성과 설계는 [designs.md](designs.md) §1 참고.

---

## 1. 개요·목표

- **목표:** 실무에 가까운 수준의 설계를 두고, 구현 범위(워커 수, 자동화, 관리 UI)는 단계적으로 확장.
- **Store-then-Process:** 수신 API는 **저장 후 즉시 200/201**만 담당. AI 호출 없음 → Mailgun 타임아웃·유실 방지.
- **Decoupling:** 수신(Fast)과 처리(Slow) 분리. 워커 지연/장애가 수신 유실로 이어지지 않음.
- **공급자 추상화:** `domain/hub/mail/` 에서 Mailgun → NormalizedInboundMail 변환. SES 등 교체 시 이 계층만 교체.

---

## 2. 상태 모델 (유지)

- **두 축 분리**
  - **status** = 메일 **도메인** 상태: `RECEIVED` | `REJECTED`
  - **ai_status** = **AI 처리** 상태: `PENDING` | `PROCESSING` | `SUCCESS` | `FAILED`
- **REJECTED 시:** `status=REJECTED`, **ai_status=NULL**, **folder=NULL**, **spam_score=NULL** → 워커 미처리.
- **external_id:** 멱등 전제. UNIQUE INDEX로 중복 저장 방지.
- 코드에서는 `AiStatus`, `MailReceiveStatus` Enum 사용. 문자열 하드코딩 금지.

---

## 3. 아키텍처 요약

| 구분 | 내용 |
|------|------|
| **수신** | Mailgun → `POST /api/mail/receive/webhook/mailgun` (Form, HMAC). 테스트용 `POST /api/mail/receive` (JSON). |
| **저장** | parse_and_verify → _save_inbound. 멱등: external_id 존재 시 200. Resolver 실패 시 REJECTED 저장 후 200. |
| **워커** | PENDING → SELECT FOR UPDATE SKIP LOCKED → PROCESSING commit → AI 실행 → SUCCESS/FAILED commit. |
| **LLaMA** | 워커에서 classify_spam 호출. 타임아웃 명시(예: 15s). 실패 시 FAILED, retry_count, ai_result_raw 기록. |
| **프론트** | aiStatus로 분석 중/완료/실패 표시. inbox vs spam 구분은 **folder** 기준만. |

---

## 4. 메일건 연동

### 4.1 백엔드

- **Webhook URL:** `POST /api/mail/receive/webhook/mailgun`  
  전체 예: `https://<API-도메인>/api/mail/receive/webhook/mailgun`
- **흐름:** Mailgun multipart/form-data → HMAC 검증 → _save_inbound(Store-then-Process) → 워커가 PENDING 처리

### 4.2 메일건 대시보드

1. 로그인 → 도메인 선택 → **Receiving** → **Routes** (또는 Webhooks).
2. **Inbound Webhook / Route:** URL = `https://<API-호스트>/api/mail/receive/webhook/mailgun`, Method POST.
3. **Webhook Signing Key:** Settings → API Keys → "HTTP webhook signing key" 복사.

### 4.3 환경 변수

| 변수 | 설명 |
|------|------|
| `MAILGUN_WEBHOOK_SIGNING_KEY` | 메일건 HTTP webhook signing key (HMAC 검증용) |
| `MAILGUN_SKIP_VERIFY` | `true` 면 HMAC 검증 생략 (로컬/개발). 운영 시 `false` 권장 |
| `MAILGUN_API_KEY` | 메일건 API Key (발송용). 대시보드 API Keys → Mail 키 |
| `MAILGUN_DOMAIN` | 발송 도메인 (예: mg.kanggyeonggu.store). 외부 발송 시 From 도메인 |

**발송 정책:** 수신자가 직원/사내 주소록이면 DB만 사용(보낸함+받은함 생성). 외부 주소면 위 두 값이 있을 때 메일건 API로 실제 발송.

### 4.4 DNS (가비아 등)

- **SPF:** `mg` 호스트 TXT `v=spf1 include:mailgun.org ~all`
- **DKIM:** `mailo._domainkey.mg` TXT (메일건에서 제공하는 공개키)
- **MX (수신):** `mg` → `mxa.mailgun.org.`, `mxb.mailgun.org.` (우선순위 10, 값 끝에 점 포함)

### 4.5 연동 체크리스트

- [ ] 메일건 도메인 준비, SPF/DKIM Verified
- [ ] Routes에 Webhook URL 등록
- [ ] `MAILGUN_WEBHOOK_SIGNING_KEY` 설정, 운영 시 `MAILGUN_SKIP_VERIFY=false`
- [ ] 주소록: 수신할 주소(`xxx@mg.<도메인>`)를 `employees.email` 또는 `internal_addresses.email`에 등록 (없으면 REJECTED)
- [ ] 워커 `python -m workers.mail_pending` 기동

---

## 5. 운영 로드맵 요약

| 단계 | 내용 |
|------|------|
| **1. DB** | ai_status, status, spam_score, processed_at, retry_count, last_failed_at, ai_result_raw. (ai_status, processed_at) 복합 인덱스. |
| **2. 수신** | HMAC, Store-then-Process(스팸 판정 제거), 멱등, REJECTED 저장 시 ai_status/folder/spam_score NULL. |
| **3. 워커** | PENDING 폴링, FOR UPDATE SKIP LOCKED, PROCESSING commit 후 AI 실행, SUCCESS/FAILED. |
| **4. LLaMA** | 워커에서 classify_spam, 타임아웃·실패 시 FAILED + ai_result_raw. |
| **5. UX** | API에 aiStatus/spamScore/status, 프론트 folder·aiStatus 표시, 폴링. |

상세 갭 분석·실행 순서는 이 요약으로 대체해 두었음.

---

## 6. 작업 체크리스트 요약

| # | 구분 | 항목 |
|---|------|------|
| 0 | DB | external_id UNIQUE 확인 |
| 1 | DB | Enum AiStatus, MailReceiveStatus / 마이그레이션 027 / ORM·상태 전이 문서 |
| 2 | 수신 | NormalizedInboundMail, parse_and_verify 단일 진입점, Mailgun 어댑터, repository 확장, 수신 라우터(스팸 제거·멱등·REJECTED 정책) |
| 3 | 워커 | mail_pending: FOR UPDATE → PROCESSING commit → AI → SUCCESS/FAILED. inbox일 때만 성과/역량 연쇄 |
| 4 | LLaMA | classify_spam + 타임아웃, 실패 시 FAILED + retry_count + ai_result_raw |
| 5 | 프론트 | aiStatus/spamScore/status 반영, folder 기준 inbox/spam, aiStatus 기준 아이콘, 폴링 |

상세 작업 목록은 코드·마이그레이션·워커 구현을 참고하면 됨.

---

## 7. LLaMA 스팸

- **목적:** 수신 메일을 LLaMA로 스팸/햄 분류 → folder=inbox vs spam.
- **데이터:** ExaOne 합성 SFT (한국어 스팸 15종 + 햄). `app/data/spam/sft/` train·val.
- **학습:** `python -m app.training.models.llama.spam_classifier.finetune` → 어댑터는 `app/artifacts/fine_tuned/llama/spam_adapters/final_model/`.
- **런타임:** `llama_use_spam_adapter=True`(기본)이면 LlamaManager가 위 어댑터 로드. 분류는 항상 SFT 모델이 내용을 보고 스팸 확률을 생성한 뒤 파싱하여 inbox/spam 결정.

상세(데이터셋, 15종 정의, 학습 옵션)는 [strategy.md](strategy.md) Part 3 참고.

---

## 8. 확장·참고

- **확장:** 워커 수 2개 이상(동일 코드, SKIP LOCKED), FAILED 자동 재시도(retry_count 상한), 관리 UI(미배정/FAILED 목록, 재처리 버튼).
- **참고:** [strategy.md](strategy.md) Part 1(메일 전략), Part 3(LLaMA 스팸), [designs.md](designs.md) §1(발송–성과 연동).
