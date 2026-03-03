# 도메인 전략 (통합)

메일·채팅 RAG·LLaMA 스팸 전략을 한 문서에 둡니다.

---

# Part 1. 메일 전략

## 1.1 목적과 범위

- **받은편지함·보낸편지함·임시보관·휴지통**을 **한 테이블(`mail_items`)** 로 통합 관리.
- **수신**은 **Webhook만** 사용. **수신자(To)가 주소록에 없으면 저장하지 않고 거부**.

## 1.2 테이블: mail_items

- **스키마**: id, folder(inbox|sent|draft|trash|spam), owner_employee_id, from_employee_id, from_display, from_email, to_address_id, to_display, to_email, subject, body, sent_at, **received_at**, **external_id**(UNIQUE), is_starred, is_unread, created_at, updated_at.
- **폴더**: inbox(받은편지함), sent(보낸편지함), draft(임시보관), trash(휴지통), spam(스팸함).
- **직원 ID**: owner_employee_id, from_employee_id는 **employees 테이블 id**만 사용. internal_addresses와 동일 정책.

## 1.3 API

- GET /api/mail?folder=...&ownerEmployeeId=... (목록), GET /api/mail/{id} (단건), POST /api/mail/send, POST /api/mail/draft, **POST /api/mail/receive**(Webhook), PUT /api/mail/{id}, DELETE /api/mail/{id}.

## 1.4 수신 계약 (POST /api/mail/receive)

1. external_id 중복 → 409.  
2. **Resolver**(To → owner_employee_id): employees → internal_addresses. 실패 시 4xx, 저장 안 함.  
3. **스팸 판정** → folder=inbox vs spam.  
4. 저장 (received_at 설정).  
- **external_id**: Message-ID, UNIQUE. 재전송 시 1건만 유지.

## 1.5 성과/역량 연동 (AI 분석)

- **folder=inbox** 인 경우만 저장 후 **BackgroundTasks**로 `run_email_classify_and_record` 비동기 실행 → 성과로 판단되면 performance_records, 역량 태깅. 실패 시 로그만, 수신은 2xx 유지.

## 1.6 테스트 (curl)

- 수신: `curl -X POST "http://localhost:8000/api/mail/receive" -H "Content-Type: application/json" -d '{"to_email":"hr@company.com", ...}'`
- 스팸: action=deliver → inbox, 그 외 → spam. LLaMA 직접: `POST /internal/llama/classify_spam`.

---

# Part 2. 채팅 RAG 전략

## 2.1 개요

- **목표**: 직원 명단/수, 개인 정보·성과, 공시 기준, 역량·복합, RAG 적재 상태, 범위 밖 질문까지 **일관된 답변** + **스트리밍**.
- **핵심**: 1턴 구조(LLM 1회), `_build_forced_tool_calls`(키워드 기반 도구 결정), RAG 전 테이블 검색·차등 임계값, 명단 30명 상한, GPU 메모리 즉시 해제.

## 2.2 그래프 흐름

rag_node → model_node(도구 필요 시 forced_tool_calls, 불필요 시 LLM 1회) → tool_node → model_node(도구 결과+context로 LLM stream) → 응답.

## 2.3 RAG

- **라우팅 키워드**: employees(직원·명단·부서…), performance_records(성과·활동…), competency_anchors(역량·직무…), disclosures(IFRS·공시…).
- **전 테이블 검색** + 라우트 감지 테이블 RAG_DISTANCE_THRESHOLD(0.8), 미감지 RAG_STRICT_THRESHOLD(0.5). competency/performance fallback 1건.
- **하이브리드**: disclosures·competency_anchors·performance_records는 벡터+tsvector. employees는 pgvector HNSW, RAG_EMPLOYEE_DISTANCE_THRESHOLD(0.6).
- **OOS**: 라우트 없으면 검색 없이 "[시스템 안내] 이 질문은 현재 데이터 범위 밖…" 반환.
- **Prefetch**: 요약·명단 질문 시 get_hr_summary/ list_for_chat 기반 context 주입. 명단 **최대 30명**.

## 2.4 도구·GPU

- **get_hr_summary**, **list_employees**(고성과 시 limit 500 후 successDna 필터), **get_employee_info**/ **get_employee_performance**(이름 추출).
- **GPU**: ExaOne 생성 후 `torch.cuda.empty_cache()`. 1턴+30명 상한으로 OOM 방지.

## 2.5 공시·프롬프트

- **get_disclosure_doc_count**: 전체 행 카운트(embedding 무관). RAG 요약과 일치.
- **출처**: [출처: table=..., id=..., source=...] 형식. 추천 질문 18개로 검증.

---

# Part 3. LLaMA 스팸 관리 (한국어 스팸 메일 중심)

- **경로**: `get_llama_adapters_dir()` → `app/artifacts/fine_tuned/llama/spam_adapters/`. 학습·런타임 공통.
- **설정**: `llama_model_id`(베이스), `llama_use_spam_adapter`(True 시 어댑터 로드). 환경 변수 LLAMA_MODEL_ID, LLAMA_USE_SPAM_ADAPTER.
- **로딩**: LlamaManager가 베이스+토크나이저 로드, 어댑터 유효 시 PEFT 부착.
- **학습**: SFT 데이터 `app/data/spam/sft/`. `python -m training.models.llama.spam_classifier.finetune --train_path <path>`. 출력 미지정 시 get_llama_adapters_dir()에 저장.
- **데이터 생성**: ExaOne이 **한국어** 스팸 **15종** + 햄(Hard Negative 포함) 합성 SFT 생성. **참고 데이터(3곳)는 기본 사용**(학습 정확도). `run_exaone_generate_spam_sft` (기본 1,050건, `--full` 2,000 / `--large` 3,600 / `--max` 5,000건). 검증 정확도 82~88%+ 기대.

## 3.1 한국어 스팸 데이터셋 참고

구글에서 "한국어 스팸 메일 데이터셋"으로 검색해 공유 데이터·논문용 데이터를 참고할 수 있다.

- **공공데이터포털(data.go.kr)**: 불법 스팸 URL, 피싱사이트, 상용메일 차단 데이터 등 (CSV 등).
- **GitHub**: KoreanSpamDataPool, KOR_phishing_Detect-Dataset, LLM-spam-detection(성균관대) 등.
- 수동 다운로드 후 subject/sender/body 형식으로 정리하면 ExaOne few-shot 참고용으로 활용 가능.

---

## 3.2 전체 상황 정리 및 전략

### 전체 상황 (As-Is)

| 구분 | 내용 |
|------|------|
| **목적** | 수신 메일을 LLaMA로 스팸/햄 분류 → folder=inbox vs spam 저장 |
| **데이터** | ExaOne이 한국어 스팸/햄 합성 SFT 생성(ETL). 참고 데이터(3곳) 기본 사용 |
| **학습** | LLaMA 스팸 어댑터 파인튜닝. 입력: spam/sft/train.jsonl·val.jsonl |
| **런타임** | POST /api/mail/receive → LLaMA classify_spam → action에 따라 inbox/spam 저장 |

### 데이터 파이프라인 (ETL)

1. **Extract·Transform·Load**: `run_exaone_generate_spam_sft` 한 번에 수행.
2. **스팸 15종**: 피싱, 당첨, 광고, 가짜경고, 성인/도박, 택배사칭, 정부기관사칭, 대출/금융, 결제위장, 계정보안알림, 투자권유, 구직·채용사칭, 설문·리워드, 친구·지인사칭, 기타.
3. **햄 7종**: 업무, 개인, 뉴스레터 + Hard Negative(업무마케팅, 인사/IT공지, 실제배송, 구독뉴스레터).
4. **출력**: exaone_synthetic.jsonl + train.jsonl(90%)·val.jsonl(10%).

### 단계별 전략

| 단계 | 내용 | 명령/설정 |
|------|------|-----------|
| **1. 양** | 최소 2,000건, 권장 3,600~5,000건 | `--full` 2,000 / `--large` 3,600 / `--max` 5,000 |
| **2. 다양성** | 스팸 15종 + 햄 Hard Negative | 코드 반영 완료 |
| **3. 실제 데이터 혼합** | 3곳 참고 → few-shot | **기본 사용** (`--no-references` 시에만 생략) |
| **4. Hard Negative** | 햄 중 스팸 유사 케이스 | HAM_CATEGORIES 7종 반영 |
| **5. 운영 후** | 오탐/미탐 수집 → 재학습(Active Learning) | 장기 과제 |

### BP 권장 목표

| 항목 | 권장 |
|------|------|
| 총 데이터 | 2,000~5,000건 |
| 스팸 유형 | 15종 |
| 스팸:햄 비율 | full 6:4, large/max 유사 |
| 참고 데이터 | **기본 사용** (3곳 few-shot). `--no-references` 시에만 생략 |
| Hard Negative | 햄 7종에 포함 |

### 예상 성능

| 조건 | 검증 정확도 | 비고 |
|------|-------------|------|
| 2,000건 + 15종 + 참고 | 82~88% | 실서비스 75~85% 수준 가정 |
| 3,600건 / 5,000건 | 88%+ 기대 | 양·다양성 증가 시 |

### 실행 순서 (권장)

1. **JSONL 생성**: `python -m training.pipelines.spam_sft.run_exaone_generate_spam_sft --large` (또는 `--max --fast`). 참고 데이터는 기본 적용.
2. **학습**: `python -m training.models.llama.spam_classifier.finetune` (기본 경로: spam/sft/exaone_synthetic 또는 train/val).
3. **적용**: 어댑터 저장 경로 `get_llama_adapters_dir()`, 런타임에 LlamaManager 로드 후 classify_spam 호출.

### GPU 최대 활용·안정 (예: RTX 4060 Ti 16GB + i5-8600)

- **스크립트**: 실행 시 `TOKENIZERS_PARALLELISM=false`, `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`, `CUDA_VISIBLE_DEVICES=0` 자동 적용.
- **권장 실행**: `--max --fast` (5,000건, 품질 유지·속도 우선).
- **환경**: 다른 GPU 사용 앱 종료, 전원 옵션 '고성능', 방열 유지 시 장시간(수 시간) 안정.
