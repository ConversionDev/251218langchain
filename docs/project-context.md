# 프로젝트 맥락 — 기능 구현 현황 및 구현 예정

이 문서는 **현재 프로젝트의 전체 맥락**을 정리합니다. 비전·기술 스택·**이미 구현된 부분**과 **앞으로 구현해야 할 부분**을 한 곳에서 파악할 수 있도록 구성했습니다.

- 관련 상세 문서: [README](README.md)(목차), [vision-and-goals](vision-and-goals.md), [technologies](technologies.md), [runbook](runbook.md).

---

## 1. 프로젝트 개요

### 1.1 비전·목적

- **비전**: 역량·공시 데이터와 LLM을 결합해 **인사·성과·공시까지 이어지는 AI 플랫폼**을 구축한다.
- **제품 목표**: **실제 ATS(Applicant Tracking System)·HCM(Human Capital Management)** 에 가까운 프로그램을 만드는 것이 목적이다.
- **핵심 도메인**:
  - **역량(Competency)**: NCS, O*NET 등 표준 역량·수행준거를 한 스키마로 통합, RAG·채점·시각화에 재사용.
  - **공시(Disclosure)**: IFRS S1/S2, ISO 30414, OECD 등 공시·지침 문서를 벡터 저장해 질의응답·요약·검증에 활용.
  - **LLM**: 한국어 특화 ExaOne을 중심으로, 도구 호출·RAG·이력서 분석·직무 전환 분석을 하나의 에이전트 체인으로 운영.
  - **플랫폼**: 채팅(역량·공시 Q&A), 이력서→Success DNA, 성과·공시 대시보드, 역량 지도, 직원/신입 관리(ATS), 활동 기록, 역량 진단·직무 전환 분석, 자격 검증 등을 **한 프로젝트**에서 제공.

### 1.2 Success DNA 정의

| 역량 | 설명 |
|------|------|
| 리더십 (leadership) | 팀·과제 리드, 의사결정·책임 |
| 기술력 (technical) | 직무 관련 기술·도구 숙련도 |
| 창의성 (creativity) | 아이디어·혁신·문제 해결 접근 |
| 협업 (collaboration) | 소통·협력·조직 기여 |
| 적응력 (adaptability) | 변화 대응, 학습·유연성 |

- **산출**: 이력서 원문을 LLM으로 분석해 각 역량을 **0–100** 점수로 출력.
- **활용**: Core 직원 등록·신입 관리(ATS)·성과 대시보드·방사형 차트·공시·직무 전환 분석 입력으로 사용.

---

## 2. 기술 스택 요약

| 영역 | 기술 |
|------|------|
| 서버 | FastAPI, Uvicorn, Pydantic |
| DB·벡터 | PostgreSQL, pgvector, SQLAlchemy, Alembic, HNSW, B-tree |
| LLM·임베딩 | LangChain, LangGraph, ExaOne 3.5, Gemini(멀티모달), BGE-m3 |
| 문서 추출 | PyMuPDF, pdfplumber, openpyxl, python-docx |
| 인프라 | 스타 토폴로지(Hub-Spoke), FastMCP, httpx |
| 프론트 | Next.js 16, React 19, TypeScript, Tailwind, Radix, Zustand, Recharts, PWA(workbox) |

상세: [technologies.md](technologies.md).

---

## 3. 데이터·인프라

### 3.1 DB·마이그레이션

- **Alembic** 통합 스쿼시 + 도메인별 리비전. `cd app` → `alembic upgrade head`.
- **주요 테이블**:
  - **employees**: 직원 ID, 이름, 직급, 부서, 이메일, 지원일, 입사일, **status**(pending/screening/hired/rejected), **success_dna**, success_dna_reason, rejection_reason, behavioral_dna, **disclosure_metrics**(JSONB), 교육훈련 시간, 이력서(resume), **embedding_content**, **embedding**(vector 1024), HNSW·B-tree.
  - **disclosures**: content, embedding_content, embedding(vector 1024), source, page, standard_type, section_title, unique_id. 공시 표준 문서 청크.
  - **competency_anchors**: content, category, level, section_title, source, source_type, embedding. O*NET·NCS 역량 통합 스키마.
  - **performance_records**: 직원별 분기·텍스트 유형(meeting/report/email)·content·tags·grade. 성과 활동 통합.
  - 기타: stadiums, teams, players, schedules(축구 데모).

상세: [db-and-migrations.md](db-and-migrations.md).

### 3.2 RAG·벡터

- **저장소**: disclosures, competency_anchors, **employees** 테이블의 embedding 컬럼. LangChain 전용 테이블 미사용.
- **RAG 질의 분류** (graph_orchestrator):
  - 공시 기준 질문(IFRS/OECD/ISO 등) → disclosures 검색.
  - 역량·직무 질문 → competency_anchors 검색.
  - 직원·인력 질문 → employees 검색(거리 임계값 0.6).
  - 복합 질문 → disclosures + employees 등 융합.
- **직원 임베딩 갱신**: `POST /api/employees/embedding` (전체 또는 단건 id).

상세: [rag-and-vector.md](rag-and-vector.md).

### 3.3 데이터 폴더 (app/data)

| 폴더 | 용도 |
|------|------|
| disclosure/raw, prepared | 공시 PDF → prepared txt → disclosures 적재 |
| competency_anchors/raw, prepared | O*NET xlsx·NCS PDF → competency_rows.jsonl → 적재 |
| resume/samples, performance/samples | 신입·성과 샘플 JSONL (임포트·학습용) |
| email/sft 등 | 이메일 SFT 등 학습 데이터 |

---

## 4. 백엔드 — API·도메인 (구현 현황)

### 4.1 API 라우터 (prefix `/api` 적용)

| 라우터 | prefix | 용도 | 구현 상태 |
|--------|--------|------|-----------|
| employee_router | /employees | 직원 CRUD, 페이징(기존/신입), 임베딩 갱신, ID 제안 | ✅ 구현됨 |
| activity_router | /activity-records | 성과 활동 기록 CRUD, 분기/유형/등급 필터 | ✅ 구현됨 |
| chat_router | /agent | 채팅 스트림(upload, chat/stream), providers, tools, health, thread history | ✅ 구현됨 |
| disclosure_router | /disclosure | 공시 문서 적재·검증·학습 상태 | ✅ 구현됨 |
| resume_router | /resume | 이력서 업로드 → 텍스트 추출·Success DNA 분석 | ✅ 구현됨 |
| document_router | /document | 문서 관련 | ✅ 구현됨 |
| audit_router | /audit | 감사 로그 조회 | ✅ 구현됨 |
| email_router | /mail | 이메일 관련 | ✅ 구현됨 |
| soccer_router | /soccer | 축구 데모(팀·선수·일정·임베딩) | ✅ 구현됨 |

내부: hub_llm_router (Llama/ExaOne/채팅/스팸 프록시), internal_soccer_router.

### 4.2 채팅 에이전트 (LangGraph)

- **그래프**: rag → model → (조건) tools → model … → END. RAG 항상 사용.
- **도구**: search_documents, define, get_current_time, calculate, **get_hr_summary**, **get_employee_info(name)**. (analyze_with_exaone: 이메일 분석)
- **시스템 프롬프트**: HR 질문 시 get_hr_summary(직원 수·공시/RAG 적재), get_employee_info(이름) 호출 유도.
- **RAG**: disclosures / competency_anchors / employees 벡터 검색, 컨텍스트 융합 후 ExaOne에 전달. 스트리밍·첨부(이미지·문서) 지원.

### 4.3 도메인·리포지토리

- **employee_repository**: CRUD, list_all, list_paginated(employment_type), find_by_name, get_by_id, search_employees_with_filter(벡터), 임베딩 갱신.
- **disclosure_repository**: save_batch, fill_embeddings, search_disclosures_with_filter(standard_types).
- **competency_anchor_repository**: 검색·적재.
- **performance_record_repository**: 성과 활동 CRUD·필터.

---

## 5. 프론트엔드 — 페이지·기능 (구현 현황)

### 5.1 라우트 구조

| 경로 | 설명 | 구현 상태 |
|------|------|-----------|
| / | 랜딩(히어로, 관리자 시작/이력서 지원하기/직원 서비스, 기능 카드) | ✅ 구현됨 |
| /dashboard | 전사 현황(전환 준비도, 직원 수 등 요약) | ✅ 구현됨 |
| /chat | HRInsight AI 채팅(스트리밍, RAG·도구, 공시 모드) | ✅ 구현됨 |
| /data-map | 역량 데이터 지도(클러스터·UMAP, iframe) | ✅ 구현됨 |
| /core/new-hires | 신입 관리(ATS: pending/screening/hired/rejected, 상태 변경·사유) | ✅ 구현됨 |
| /core/employees | 기존 직원 목록·상세·편집(EmployeeFormModal) | ✅ 구현됨 |
| /core | Core 진입(기존 직원/신입 관리 링크) | ✅ 구현됨 |
| /performance/activities | 활동기록(분기·유형·등급 필터, 목록) | ✅ 구현됨 |
| /performance | 성과·가치(전환 준비도·시뮬레이션·ValueSummaryCard) | ✅ 구현됨 |
| /intelligence | 역량 진단(5대 역량, 직무 전환 분석·엑사원 문구 생성) | ✅ 구현됨 |
| /credential | 자격 검증(IFRS 지표·검증 플로우) | ✅ 구현됨 |
| /risk | 감사 로그 | ✅ 구현됨 |
| /settings | 설정 | ✅ 구현됨 |
| /workspace | 직원 업무 공간(업무 제출, 보고서, 제출함, 이력서 지원 접수) | ✅ 구현됨 |
| /workspace/submit | 업무 제출 폼 | ✅ 구현됨 |
| /workspace/my-activities | 제출함 목록 | ✅ 구현됨 |
| /apply | 이력서 지원 폼(입사 지원) | ✅ 구현됨 |
| /resumes | 지원내역 목록 | ✅ 구현됨 |
| /careers | 채용 진입(숲 배경, 채용/공지/질의/지원내역) | ✅ 구현됨 |
| /careers/recruit | 채용 공고 | ✅ 구현됨 |
| /careers/notice, /careers/faq | 공지·질의 | ✅ 구현됨 |
| /soccer | 축구 데모 | ✅ 구현됨 |
| /performance/report | 성과 보고서(클라이언트) | ✅ 구현됨 |

### 5.2 사이드바 메뉴 (관리자 대시보드)

- 메인, 전사 현황, 채팅, 데이터 지도, 신입 관리, 기존 직원, 활동기록, 감사 로그, 역량 진단, 자격 검증, 성과·가치, 설정.

### 5.3 주요 모듈·기능

- **역량 진단(intelligence)**: 선택 직원 기준 5대 역량 요약, DNA 성장(이력 없음 시 빈 배열), **직무 전환 분석** — 숫자(전환 가능성·전환 준비도·스킬 갭)는 DB/계산, 문구는 **엑사원 스트리밍**으로 생성(「엑사원으로 분석하기」 버튼).
- **성과·가치(performance)**: 전환 준비도·시뮬레이션·ValueSummaryCard, disclosure_metrics 연동.
- **공시·지표(disclosureMetrics)**: getIfrsMetricsView(transitionReadyScore, skillGap, humanCapitalROI), 레거시·items[] 호환.
- **Core(직원)**: 목록 페이징, EmploymentType(기존/신입), 신입 ATS 상태·사유, 직원 모달(Success DNA·disclosure_metrics·이력서 등).
- **채팅**: 파일 업로드→file_ids, 스트림 응답, context_preview·sources, 공시 모드.

---

## 6. 학습·파이프라인 (구현 현황)

| 파이프라인 | 용도 | 구현 상태 |
|------------|------|-----------|
| run_disclosure_ingest | raw PDF → prepared txt → disclosures 적재(BGE-m3) | ✅ 구현됨 |
| run_competency_ingest | raw xlsx/PDF → prepared JSONL → 검증 → competency_anchors 적재 | ✅ 구현됨 |
| run_competency_visualization | 역량 임베딩 → K-Means·UMAP → 시각화(데이터 지도) | ✅ 구현됨 |
| run_competency_clustering, run_cluster_labeling | 클러스터링·라벨링 | ✅ 구현됨 |
| run_import_new_hire_samples | 신입 샘플 JSONL → DB | ✅ 구현됨 |
| run_import_performance_samples | 성과 샘플 JSONL → performance_records | ✅ 구현됨 |
| run_sft_training, run_sft_data_generation, run_qa_to_chat_format | SFT·QA→채팅 형식 | ✅ 구현됨 |
| apply_ats_flow_to_jsonl, apply_recruit_strategy_to_jsonl | 신입 JSONL 후처리 | ✅ 구현됨 |

---

## 7. 기능 구현 현황 요약

### 7.1 구현 완료로 볼 수 있는 부분

- **메인·진입**: 랜딩, 메인→숲(careers)→채용/이력서 지원 흐름, 관리자/직원/이력서 지원 버튼.
- **ATS·직원**: 신입 관리(상태·사유), 기존 직원 CRUD, 페이징, 직원별 Success DNA·disclosure_metrics·이력서.
- **이력서·Success DNA**: 지원 폼(/apply), 이력서 업로드→분석 API, Success DNA·기본 정보 추출, 직원 등록 연동.
- **채팅**: 스트리밍, RAG(disclosures/competency_anchors/employees), 도구(get_hr_summary, get_employee_info 등), 시스템 프롬프트(HR 도구 유도), 첨부(이미지·문서).
- **역량 진단**: 5대 역량 요약·방사형·성장(이력 없음 시 빈 배열), **직무 전환 분석** — 지표(숫자) + 엑사원 생성 문구(버튼 호출).
- **성과·공시**: 활동기록 CRUD·필터, 성과·가치 페이지(전환 준비도·시뮬레이션), 전환 준비도 추이(실제 DB만, 분기 시계열은 “현재” 1점).
- **데이터 지도**: competency_anchors 기반 클러스터·UMAP iframe.
- **공시**: disclosure 적재·검증, disclosure_metrics 설계(레거시 3지표·items[]).
- **자격 검증**: IFRS 지표·검증 플로우 UI.
- **감사 로그, 설정, 워크스페이스(업무 제출/제출함), 채용(공지/FAQ), 축구 데모.**

### 7.2 부분 구현·데이터 의존

- **전환 준비도 시계열**: UI는 있으나 “현재” 1점만 표시. 분기별 시계열 데이터가 쌓여야 추이 확장 가능.
- **직무 전환 분석**: 문구는 엑사원 생성(완료). 직무·산업별 목표 역량 정의·시계열 데이터는 확장 시 반영 예정.
- **DNA 성장 이력/궤적**: 스키마에 시계열 없어 빈 배열 반환. 이력 쌓이면 확장.
- **데이터 지도**: competency_anchors 적재 후 클러스터·UMAP 실행 필요.

### 7.3 문서·설계상 언급·미구현

- **Intelligent 추출(LlamaParse)**: ESG·지속가능경영보고서 등 — 문서상 “미구현 시 FastExtract fallback”.
- **역량 SFT 어댑터**: ExaOne 역량 어댑터 로드 옵션 존재, 실제 학습·배포는 별도 파이프라인.
- **블록체인 기록**: 자격 검증 화면에서 “블록체인에 기록” 문구 있음. 실제 블록체인 연동 여부는 구현 확인 필요.

---

## 8. 구현해야 할 부분 (우선순위·확장 포인트)

### 8.1 ATS·HCM 제품화 관점

- **신입 파이프라인 강화**: 이력서→자동 스크리닝·매칭 점수, 워크플로(단계별 상태)·알림, 이의 제기·감사 대응(rejection_reason 활용).
- **역량·공시 시계열**: 직원별 분기별 전환 준비도·역량 점수 저장·조회 → 추이 차트·직무 전환 분석 품질 향상.
- **직무·역할 매핑**: 직무별 목표 역량 정의, 스킬 인벤토리·갭 분석 자동화.
- **리포팅·공시 산출**: ISO 30414·IFRS S1/S2 기준 보고서 자동 생성·검증, disclosure_metrics items[] 확장 반영.

### 8.2 데이터·RAG

- **직원 임베딩 커버리지**: 신입/기존 직원 등록·수정 시 임베딩 갱신 호출 정책화, RAG 품질 확보.
- **disclosure·competency 적재 운영**: 정기 적재·버전 관리, 표준 추가 시 standard_type·스키마 확장.

### 8.3 학습·품질

- **엑사원**: 직무 전환·ATS 문구는 **일반(베이스) 엑사원 + 프롬프트 + RAG**로 충분하다는 전제. 필요 시 학습된 엑사원(용어·톤 통제) 검토.
- **역량 SFT/어댑터**: 일관된 역량 채점·리포트를 위해 학습 파이프라인·배포 정리.

### 8.4 UX·운영

- **PWA·오프라인**: 서비스 워커·캐시 전략 검토.
- **다국어·접근성**: 필요 시 확장.
- **모니터링·로깅**: 채팅·에이전트·API 사용량·에러 추적.

---

## 9. 참고 문서

| 문서 | 내용 |
|------|------|
| [README](README.md) | 문서 목차 |
| [vision-and-goals](vision-and-goals.md) | 비전·목표·Success DNA·도메인별 방향 |
| [technologies](technologies.md) | 기술 스택·스타 토폴로지 |
| [rag-and-vector](rag-and-vector.md) | RAG·벡터·HNSW |
| [db-and-migrations](db-and-migrations.md) | DB·마이그레이션 |
| [disclosure-metrics-design](disclosure-metrics-design.md) | 공시 지표 구조·레거시 매핑 |
| [extraction-and-data](extraction-and-data.md) | PDF/엑셀 추출·competency 스키마 |
| [exaone-tool-calling-design](exaone-tool-calling-design.md) | 도구 바인딩·답변 품질 |
| [runbook](runbook.md) | 실행·데이터 경로 |
| [apply-form](apply-form.md) | 입사 지원 페이지·템플릿 |
