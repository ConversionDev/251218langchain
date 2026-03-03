# 과거 문제점 및 해결 방안

이 문서는 **지금까지 발생한 문제점**과 **적용한 해결 방안**을 한곳에 정리합니다.  
과거 이슈는 여기서 레거시로 관리하고, **현재 코드·문서는 이 해결 기준으로 정리**합니다.

---

## 1. 스팸 수신 시 모두 받은편지함으로 저장되던 문제

### 문제

- 수신 API(`POST /api/mail/receive`)에서 스팸 판정 후에도 **스팸 메일이 받은편지함(inbox)**으로 저장됨.
- **원인**: 라우팅이 `policy`(ExaOne)로 가면 ExaOne이 `deliver`를 반환해, LLaMA가 스팸으로 판단해도 최종 `action`이 deliver로 덮어써짐.

### 해결 방안

- **SpamGatewayService.read()**에서 LLaMA 결과가 있으면 **`routing_strategy`를 항상 `"rule"`**로 설정.
- 최종 결정을 **LLaMA 기준으로만** 내리도록 하여, 스팸 판별 시 `folder=spam`으로 저장.
- 스팸 감지 실패(LLaMA 미로드·타임아웃) 시에는 수신을 막지 않고 **기본값 `folder=inbox`**로 저장(장애 시 수신 차단 방지).

### 참고

- 판정 기준: `action`이 **`deliver`** → `folder=inbox`, 그 외 → `folder=spam`.
- 검증: [strategy.md](strategy.md) Part 1 §11 스팸 판정 테스트(5단계) curl 예시로 확인.

---

## 2. 이메일 SFT 데이터 = 전부 스팸 판정용

### 문제

- **app/data/email** 아래 SFT 데이터(processed/filtered의 train.jsonl, val.jsonl) 내용이 전부 **「스팸 여부 판정」**용(instruction: "다음 이메일 내용을 분석하여 스팸 여부를 판정하고…", output: BLOCK/ALLOW 등).
- 도메인명이 "email"이라 일반 메일 답장 생성용으로 오인할 수 있고, **스팸 vs 이메일** 데이터 소스가 이원화됨.

### 해결 방안

- **데이터 정책**: email 폴더 데이터는 **삭제하고**, 스팸 SFT는 **ExaOne이 생성한 데이터만** 사용하기로 함.
- **학습·경로**: ExaOne이 생성한 `app/data/spam/sft/exaone_synthetic.jsonl` 등만 사용. LLaMA 스팸 파인튜닝도 해당 데이터(또는 동일 스키마 변환) 기준.
- **코드**: 기존 `get_data_dir() / "email" / "sft"` 참조는 **`"spam"`**으로 변경 예정(통일 시).  
- **정확도**: ExaOne 생성 데이터의 양·다양성만 확보하면, 레거시 email 데이터 없이도 실용적으로 충분하다는 전제.

---

## 3. ExaOne 학습 파이프라인 중복

### 문제

- ExaOne(이메일/정책) 학습용으로 **여러 진입점**이 공존: `load_model.py`, `lora_adapter.py`, `optimized_training_pipeline.py` 등.
- 어떤 스크립트를 써야 할지 불명확하고, 유지보수·문서화가 어려움.

### 해결 방안

- **ExaOne 학습**: 런타임에서 사용하는 건 **역량 SFT(competency_adapters)** 만. `training.pipelines.sft.run_sft_training` 사용.
- **제거됨**: `policy_solver`(2에포크 LoRA, exaone/adapters)는 로드되지 않아 제거. 역량 SFT(4에포크, competency_adapters)만 유지.

---

## 4. 채팅에서 LLaMA 사용

### 문제

- 채팅 RAG/에이전트에서 **LLaMA**를 분류·생성에 혼용하고, 코드·설정이 ExaOne과 뒤섞여 있음.
- 스팸은 LLaMA 전용으로 두고, **채팅은 ExaOne만** 쓰는 정책으로 정리 필요.

### 해결 방안

- **채팅**: `classify_with_llama`, `classify`, `llama_classify` 제거. **ExaOne만** 사용(생성·도구 호출·RAG).
- **스팸**: LLaMA 스팸 분류만 유지 (`/internal/llama/classify_spam`, Spam MCP).
- **Central Control Server / Hub MCP**: `classify_with_llama` 제거. 채팅 관련 문서를 "채팅 ExaOne만, LLaMA는 스팸만"으로 수정.

---

## 5. app/data 디렉터리 구조 불일치

### 문제

- runbook에는 **raw → prepared → sft** 3단계 통일이라고 되어 있으나, 실제는 도메인마다 상이.
  - **email**: sft/processed, sft/filtered만 있고 raw/prepared 없음.
  - **spam**: sft/만 있음.
  - **performance / resume / address_book**: **samples/** 만 있고 raw/prepared/sft 구분 없음.
  - **env_mapping**: 단계 구분 없이 루트에 csv·스크립트.
- **samples** vs **sft** 역할이 문서와 혼재(입력용 샘플 vs 학습용 SFT).

### 해결 방안

- **통일 규칙**: 도메인별로 **raw / prepared / sft** 세 단계만 사용. **samples 폴더는 구분하지 않고**, 입력용 샘플은 **raw/** 에 둠.
- **역할 정의**  
  - **raw**: 원본·수집 데이터, 파이프라인 입력용 샘플(타임스탬프 파일 등) 전부.  
  - **prepared**: 전처리·정규화 결과.  
  - **sft**: 학습용 SFT 데이터(train/val, synthetic 등).
- **이동**: performance_samples_*.jsonl, new_hire_samples_*.jsonl, internal_addresses.jsonl 등은 **raw/** 로 정리(통일 적용 시).
- **core.paths**: 도메인별 `get_*_data_dir()` 등이 위 규칙과 일치하도록 유지·보강.

---

## 6. EXAONE 도구 바인딩 시 답변 품질 이슈

### 문제

- ExaOne을 `bind_tools`로 감싼 상태에서, **질문에 직접 답하지 않고** 도구 설명·제안 위주로 응답하는 현상.
- **원인**: 도구 프롬프트 비중 과다, "역량 전문가로 답변" vs "도구 호출 시 JSON만" 지시 충돌, 도구 목록 상시 노출로 도구 편향.

### 해결 방안(후보)

- **프롬프트**: 역량 프롬프트 유지, 도구 섹션은 짧게. **"직접 답변 우선, 필요할 때만 도구 사용"** 명시.
- **조건부 도구 프롬프트**: 질문 유형에 따라 도구 프롬프트 생략/축소.
- **분리된 래퍼**: 도구 필수/선택 경로를 나누고, RAG 답변 경로에서는 도구 프롬프트 최소화.

상세: [exaone-tool-calling-design.md](exaone-tool-calling-design.md).

---

## 7. 채팅 1턴에서 LLM 2회 호출·GPU OOM

### 문제

- 첫 턴에서 `llm_with_tools.invoke()`로 tool_calls 수집 → 도구 실행 → 두 번째 턴에서 `stream()`으로 답변. **LLM 2회 호출**.
- GPU 16GB 환경에서 2회 호출 + 긴 컨텍스트 시 **VRAM 부족(OOM)** 발생.

### 해결 방안

- **1턴 최적화**: 첫 턴에서 LLM invoke 제거. **`_build_forced_tool_calls(user_query)`** 로 키워드 기반 도구 결정만 수행.
- 도구 필요 시 `AIMessage(content="", tool_calls=forced_calls)` 반환 → tool_node 실행 → **두 번째 model_node에서만 LLM stream 1회**.
- 도구 불필요 질문(OOS 등)은 첫 턴에서 바로 `llm_with_tools.stream(messages)` 1회로 답변.
- **결과**: LLM 호출 1회로 GPU 부하 절반 감소, 동일 답변 품질 유지.

상세: [chat-rag-strategy.md](chat-rag-strategy.md).

---

## 8. 임베딩 동기화 스텁·호출처 없음

### 문제

- **run_embedding_sync_task**(api.shared.embedding_sync)는 Redis에 job 상태만 "completed"로 설정하고, **실제 임베딩 갱신 로직 없음**.
- **호출하는 코드가 없음**.

### 해결 방안

- 현재는 **스텁으로 유지**. 필요 시 다른 도메인(예: 메일·성과)에서 "임베딩 일괄 갱신" 요청 시 해당 태스크를 구현해 연결.
- 문서(implementation-status, backend)에 "임베딩 동기화: 스텁, 호출처 없음"으로 명시해 AI·개발자가 현재 상태를 인지하도록 함.

---

## 9. 메일 API·워크스페이스 메일 문서 레거시

### 문제

- **implementation-status** 등에 "이메일 전송: 스텁", "워크스페이스 메일: 샘플 데이터만, 백엔드 미연동"이라고만 되어 있음.
- 실제로는 **수신(receive), 스팸 판정, 저장(inbox/spam), AI 분석 연결(수신 메일 → 성과/역량 분류)** 가 구현됨.  
  **send** 는 메타데이터 저장만 하고 외부 발송은 미구현인 스텁에 가깝고, **filter** 는 구현됨.

### 해결 방안

- **문서를 현재 코드 기준으로 수정**  
  - 수신: `POST /api/mail/receive` 구현됨. Resolver, external_id, 스팸 판정, 저장, inbox 시 비동기 성과/역량 분류까지 반영.  
  - 스팸 필터: `POST /api/mail/filter` 구현됨.  
  - send: 스텁(메타데이터 저장만, 실제 SMTP 등 미구현).  
  - 워크스페이스 메일 UI: 프론트가 **아직** receive/send/list를 백엔드와 연동하지 않고 샘플만 쓸 수 있음 → "미연동" 명시 유지하되, 백엔드 receive·list·스팸은 구현됨이라고 구분해 기입.

---

## 10. LLaMA 스팸 학습 데이터·경로

### 문제

- LLaMA 스팸 파인튜닝 시 **학습 데이터 경로**가 여러 소스(email/sft/processed, spam/sft 등)에 흩어져 있고, 기본값이 불명확함.

### 해결 방안

- **core.paths**: `get_llama_adapters_dir()` → `artifacts/fine_tuned/llama/spam_adapters`.
- **core.config**: `llama_model_id`, `llama_use_spam_adapter` 추가.
- **LlamaManager**: model_id는 설정에서, 어댑터 경로는 `get_llama_adapters_dir()`(및 final_model fallback) 사용.
- **파인튜닝 스크립트**: 기본 출력을 `get_llama_adapters_dir()`로, **기본 train 경로는 스팸 SFT 우선**(exaone_synthetic.jsonl → 없으면 email/sft/processed)으로 통일.
- **문서**: [strategy.md](strategy.md) Part 3 에 경로·설정·실행 방법 정리.

---

## 11. 수신 메일 → 성과/역량 자동 반영 (AI 분석 연결)

### 문제

- 설계상 "수신 메일 저장 후 비동기로 성과/역량 분류 → performance_records·역량 반영"이 **구현 우선순위 6번**이었으나 미구현 상태였음.

### 해결 방안

- **receive_mail_api** 에서 저장 후 **folder=inbox** 인 경우에만 **BackgroundTasks** 로 비동기 실행.
- **`_run_inbox_classify_after_receive(subject, body, owner_employee_id)`**: 전용 DB 세션(SessionLocal)으로 **run_email_classify_and_record** 호출 → 성과로 판단되면 performance_records에 기록, 역량 태깅.
- 실패 시 **로그만 남기고** 수신 응답은 이미 2xx로 반환된 상태 유지.
- [strategy.md](strategy.md) Part 1 §6, §7에 "AI 분석 연결 구현됨(inbox만)" 반영.

---

## 문서·코드 정리 원칙

- **과거 이슈**: 이 문서(issues-and-resolutions.md)에 문제·해결을 기록하고, 필요 시 "레거시 이슈"로 참조.
- **현재 문서**: runbook, implementation-status, backend, project-context 등은 **위 해결이 반영된 현재 코드 기준**으로만 서술.  
  "예정", "미구현"은 남기되, "이미 해결된 문제"는 이 문서로만 유지.
- **통합**: 문서 수를 줄이기 위해 설계·이슈는 이 파일과 상세 문서(strategy, designs, mail 등)로만 링크하고, 중복 설명은 제거.
