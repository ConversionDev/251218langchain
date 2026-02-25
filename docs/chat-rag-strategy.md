# 채팅 RAG 전략 및 정상화 요약

채팅(AI 질의)이 정상적으로 동작하도록 적용한 전략, 구조 변경, GPU 메모리 대응, 공시·역량·직원·성과 통합 답변 방식을 정리한 문서입니다.

---

## 1. 개요: 채팅 정상화 상태

- **목표**: 직원 명단/수, 개인 정보·성과, 지표·고성과자, 공시 기준, 역량·복합, RAG 적재 상태, 범위 밖 질문까지 **일관되게 올바른 답변** + **스트리밍 유지**.
- **검증**: 프론트 추천 질문 18개(2개씩 9그룹)로 직원 목록/수, 개인 정보/성과, 지표/고성과, 공시 기준, 역량/복합, 요약/범위 밖, 전체 명단/부서, 고성과/신입, RAG/비율 시나리오를 커버.
- **핵심 변경**: 1턴 구조(LLM 1회 호출), 강제 도구 결정(`_build_forced_tool_calls`), RAG 전 테이블 검색·차등 임계값, 컨텍스트 상한(30명), GPU 메모리 즉시 해제, 공시 카운트 정책 수정.

---

## 2. 아키텍처: 그래프 흐름

```
[사용자 질문]
      ↓
  rag_node     ← RAG 검색(4테이블) + prefetch(요약/명단) → context, rag_sources
      ↓
  model_node   ← 1턴: 도구 필요 시 forced_tool_calls 생성(LLM 호출 없음)
                 도구 불필요 시 LLM stream 1회
      ↓
  tool_node    ← 도구 실행 (get_hr_summary, list_employees, get_employee_info 등)
      ↓
  model_node   ← 2번째 진입: 도구 결과 + context 로 LLM stream → 최종 답변
      ↓
  [스트리밍 응답]
```

- **진입점**: `rag` → `model` (RAG는 항상 사용).
- **조건부 라우팅**: `model`에서 `tool_calls` 있으면 `tools` → 다시 `model`; 없으면 `END`.
- **다른 페이지 이동 시**: `ChatPanel`은 마운트 유지(화면 밖 렌더링)로 스트리밍이 끊기지 않음.

---

## 3. 1턴 최적화 (LLM 호출 1회)

### 문제
- 기존: 첫 턴에서 `llm_with_tools.invoke()`로 tool_calls 수집 → 도구 실행 → 두 번째 턴에서 `stream()`으로 답변. **LLM 2회 호출**.
- GPU 16GB 환경에서 2회 호출 + 긴 컨텍스트 시 VRAM 부족(OOM) 발생.

### 전략
- **첫 턴에서 LLM invoke 제거.** `_build_forced_tool_calls(user_query)`로 키워드 기반 도구 결정만 수행.
- 도구가 필요하면 `AIMessage(content="", tool_calls=forced_calls)` 반환 → `tool_node` 실행 → 두 번째 `model_node`에서만 **LLM stream 1회**.
- 도구가 불필요한 질문(OOS 등)은 첫 턴에서 바로 `llm_with_tools.stream(messages)` 1회로 답변.

### 결과
- 18개 추천 질문은 모두 키워드로 도구가 결정되므로 **동일 답변 품질**, **LLM 호출 1회**로 GPU 부하 절반 감소.

---

## 4. RAG 전략

### 4.1 라우팅 키워드
- **employees**: 직원, 임직원, 인력, 명단, 목록, 누가, 누구, 부서, 신입, 고성과, RAG, 문서등록, 적재 등.
- **performance_records**: 성과, 활동, 실적, 회의록, 보고서, 성과등급, 고성과자, 분기별, 연간 성과, 프로젝트 등.
- **competency_anchors**: 직업, 역량, 능력, 직무, 문제해결, 의사소통, 리더십, 협업, 적응력 등.
- **disclosures**: IFRS, OECD, ISO30414, 기후, 탄소, 인적자본, 공시 등. "공시" 단독 시 전체 표준 검색.

### 4.2 전 테이블 검색 + 차등 임계값
- **항상** disclosures, competency_anchors, employees, performance_records 네 테이블 검색.
- **라우트 감지 테이블**: `RAG_DISTANCE_THRESHOLD`(0.8) 이하만 컨텍스트에 포함.
- **라우트 미감지 테이블**: `RAG_STRICT_THRESHOLD`(0.5) 이하만 포함(엉뚱한 문서 방지).
- competency_anchors / performance_records는 임계값 미통과 시 **fallback**: 최소거리 1건이 `RAG_ANCHOR_FALLBACK_MAX_DISTANCE`(0.9) 이내면 1건 포함.

### 4.3 하이브리드 검색
- disclosures, competency_anchors, performance_records: **벡터 + Full-Text Search(tsvector)** 조합(hybrid). 실패 시 기존 벡터 검색으로 fallback.
- employees: pgvector HNSW만 사용. `RAG_EMPLOYEE_DISTANCE_THRESHOLD`(0.6) 이하만 포함.

### 4.4 OOS(범위 밖) 조기 반환
- `not any(routes.values())` 이면 **검색 없이** 즉시 OOS 컨텍스트 반환. "[시스템 안내] 이 질문은 현재 데이터 범위 밖의 질문입니다." 문구로 LLM에 지시.

### 4.5 Prefetch
- 총원/적재 상태 질문: `get_hr_summary`와 동일한 요약(전체·일반·신입 수, 성과/공시/역량 문서 건수)을 prefetch로 context에 주입.
- 명단/목록 질문: `list_for_chat` 기반으로 직원 목록 prefetch. **표시는 최대 30명**으로 제한(GPU OOM 방지).

---

## 5. 도구·컨텍스트 전략

### 5.1 강제 도구 결정 (`_build_forced_tool_calls`)
- **get_hr_summary**: 직원수, 적재상태, RAG 문서, 공시 완성도 등 키워드.
- **list_employees**: 명단, 목록, 누가, 누구, 보여, 고성과, 신입 등. employment_type/performance_tier/department/job_title 추론. **고성과자 질의 시** limit 500으로 전체 스캔 후 successDna 기준 필터.
- **get_employee_info** / **get_employee_performance**: 질문에서 이름 추출(`_extract_employee_name_from_query`) + 직급/부서/성과 키워드.

### 5.2 명단 표시 상한 (GPU OOM 방지)
- **list_employees** 도구 출력: 통계(전체/신입/일반/고성과/비율)는 **전체 데이터 기준**으로 정확히 계산. **LLM에 넘기는 명단은 최대 30명**으로 자른 뒤 "… 외 N명 더 있음" 안내.
- **prefetch** 역시 직원 목록 **최대 30명**만 context에 포함.
- "고성과자 수와 전체 직원 대비 비율"처럼 **숫자/비율만 필요한 질문**도 정확한 값이 요약 줄에 포함되므로 30명 제한만으로도 올바른 답변 가능.

### 5.3 직원 통계 정확도
- `count_for_chat`, `count_all`로 **limit과 무관하게** 신입/일반 인원 수 계산.
- 고성과자 수는 `list_for_chat`으로 가져온 rows에서 successDna 평균 80 이상인 인원만 집계(고성과자 전용 질의 시 limit 500 적용).

---

## 6. GPU 메모리 전략

### 6.1 즉시 해제
- **ExaoneLangChainWrapper** `_generate` / `_stream` / **ExaoneLLM.invoke** 완료 후:
  - `input_ids`, `outputs`(생성 결과) 텐서 `del` 후 `torch.cuda.empty_cache()` 호출.
- 매 답변 후 VRAM이 누적되지 않도록 함.

### 6.2 1턴 + 컨텍스트 상한
- 1턴으로 LLM 호출 1회로 감소.
- 명단 30명 상한으로 입력 토큰 수 감소 → logits·KV 캐시 사용량 감소 → 16GB 환경에서 OOM 회피.

---

## 7. 공시(Disclosure) 관련

### 7.1 카운트 정책
- **get_disclosure_doc_count**: **전체 행** 카운트(embedding 유무 무관). RAG 요약/채팅에서 "공시 문서 N건"이 실제 적재 건수와 일치하도록 함.
- **get_disclosure_embedded_count**: embedding이 채워진 행만 카운트(별도 함수). 필요 시 상태 API 등에서 사용.

### 7.2 임베딩
- 공시 문서 임베딩은 서버 기동 시 로드한 **BGE-m3 싱글톤**(`get_disclosure_embedding_model`) 재사용. 버튼/API 호출 시 별도 모델 로드 없음.
- `POST /api/disclosure/embedding/run`: `fill_embeddings_for_disclosures()` 실행. embedding이 null인 행만 배치로 임베딩 후 저장. (프론트 RAG 관리 UI는 제거됨. API는 스크립트/재실행용으로 유지 가능.)

---

## 8. 프롬프트·출처

- **chat_orchestrator**: `_HR_TOOLS_GUIDE`에 **명단/목록 질문 규칙** 명시 — "이름·부서·직급을 그대로 나열", 요약만 하지 말 것.
- RAG·도구 결과에 **[출처: table=..., id=..., source=...]** 형식으로 메타데이터 포함. 프론트에서 참고 문서로 표시.

---

## 9. 검증·추천 질문

- **18개 추천 질문**으로 다음 시나리오 검증:
  - 직원 목록/수, 개인 정보/성과, 지표/고성과, 공시 기준, 역량/복합, 요약/범위 밖, 전체 명단/부서, 고성과/신입, RAG/비율.
- 평가 스크립트: `app/scripts/run_chat_eval.py`, 샘플 `chat_eval_sample.jsonl`.

---

## 10. 향후 보강 (선택)

- **대명사/맥락 참조**: "그 사람 성과는?" → 이전 턴의 ToolMessage에서 직원 이름 추출해 `get_employee_performance(name)` 인자로 대입. `_build_forced_tool_calls`에서 messages 역순 탐색으로 구현 가능(20~30줄 수준).
- **공시 임베딩 UI**: 필요 시 설정 등에 "공시 임베딩 실행" 버튼을 다시 노출해 `POST /api/disclosure/embedding/run` 호출 가능.

---

## 11. 참고 파일

| 구분 | 경로 |
|------|------|
| 그래프·도구·RAG 노드 | `app/domain/hub/orchestrators/graph_orchestrator.py` |
| 채팅 오케스트레이터·프롬프트 | `app/domain/hub/orchestrators/chat_orchestrator.py` |
| ExaOne 래퍼·메모리 해제 | `app/domain/models/bases/exaone_model.py` |
| 공시 레포·카운트·임베딩 | `app/domain/hub/repositories/disclosure_repository.py` |
| 직원 레포·list_for_chat·count_for_chat | `app/domain/hub/repositories/employee_repository.py` |
| 공시 API·status·embedding/run | `app/api/routers/disclosure_router.py` |
| 채팅 평가 | `app/scripts/run_chat_eval.py`, `app/scripts/chat_eval_sample.jsonl` |
