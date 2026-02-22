# 프로젝트 방향성과 목표

이 문서는 본 프로젝트의 **비전**, **방향성**, **목표**를 정리한다. 기술 스택·아키텍처는 [technologies.md](technologies.md), 실행·데이터는 [runbook.md](runbook.md) 참고.

---

## 1. 비전

**“역량·공시 데이터와 LLM을 한데 엮어, 인사·성과·공시까지 이어지는 AI 플랫폼을 만든다.”**

- **역량 데이터**: NCS, O*NET 등 표준 역량·수행준거를 한 스키마로 모으고, RAG·채점·시각화에 재사용한다.
- **공시 데이터**: IFRS S1/S2, ISO 30414, OECD 등 공시·지침 문서를 벡터 저장해, 질의응답·요약·검증에 쓴다.
- **LLM**: 한국어 특화 ExaOne을 중심으로, 도구 호출·RAG·이메일 분석·이력서 분석을 하나의 에이전트 체인으로 운영한다.
- **플랫폼**: 채팅(역량·공시 Q&A), 이력서→Success DNA, 성과·공시 대시보드, 역량 군집 지도, 이메일 정책 분석 등을 **한 프로젝트**에서 제공한다.

---

## 2. 방향성

| 원칙 | 설명 |
|------|------|
| **데이터 일원화** | 역량은 competency_anchors 한 테이블, 공시는 disclosures 한 테이블. O*NET·NCS·IFRS·OECD 등 출처는 `source`/`source_type`으로 구분해 동일 파이프라인으로 적재·검색한다. |
| **RAG 우선** | 답변은 “검색한 문서 + LLM” 조합으로 생성. 도구는 검색·계산·이메일 분석 등 보조만 담당하고, 직접 답변을 우선하도록 프롬프트와 그래프를 설계한다. ([exaone-tool-calling-design.md](exaone-tool-calling-design.md)) |
| **도메인 분리·확장** | 채팅·스팸·축구 등 도메인은 MCP Spoke로 나누고, Hub는 라우팅만 담당하는 **스타 토폴로지**로 확장·배포를 쉽게 한다. ([technologies.md](technologies.md)#스타-토폴로지-hub-spoke) |
| **한국어·역량 특화** | 메인 LLM은 ExaOne. 역량 SFT 어댑터, 군집 기반 프롬프트, NCS/O*NET 기반 채점·리포트를 통해 “역량 전문가” 역할을 강화한다. |
| **문서→구조화 재사용** | PDF/Excel/Word 추출 전략(FastExtract·Structural·Intelligent)을 도메인별로 선택하고, 추출 결과는 임베딩·RAG·학습 데이터로 재사용한다. ([extraction-and-data.md](extraction-and-data.md)) |

---

## 3. 목표

### 3.1 사용자·비즈니스 관점

- **역량 Q&A**: 사용자가 질문하면 RAG로 disclosures·competency_anchors를 검색하고, ExaOne이 역량·공시 기준에 맞춰 답변한다. (IFRS, OECD, NCS 등 용어 설명·검색 포함.)
- **이력서 → Success DNA**: 이력서 업로드 시 텍스트 추출 후 LLM으로 **Success DNA**(리더십·기술력·창의성·협업·적응력 5대 역량, 0–100)와 기본 인적 정보를 추출해, Core 직원 등록·성과 대시보드에 연동한다.
- **성과·공시 대시보드**: 직원/전사 단위로 Human Capital ROI, 지속가능성 영향, 성과 지수, 공시 요약(IFRS S1/S2) 등을 시각화하고, 필요 시 시뮬레이션·보고서로 활용한다.
- **역량 데이터 지도**: competency_anchors 임베딩을 군집화·UMAP 축소해 “역량 지도”로 보여 주어, 역량 구조·유사도 탐색에 쓴다.
- **이메일·정책**: 이메일 분석(ExaOne), 스팸·정책 분류(Llama)를 MCP Spoke로 제공해, 업무 자동화·정책 적용에 활용한다.

### 3.2 기술·플랫폼 관점

- **단일 진입점**: 채팅·이력서·성과·데이터 지도·이메일 등 기능을 하나의 백엔드( FastAPI )·프론트( Next.js PWA )에서 제공하고, 필요 시 도메인만 MCP로 분리·확장한다.
- **재현 가능한 파이프라인**: disclosure·competency ingest, SFT·LoRA 학습, 클러스터링·시각화를 스크립트·설정으로 고정해, 데이터만 바꿔서 재실행 가능하게 한다.
- **품질·유지보수**: 도구 바인딩 시 “직접 답변 우선” 유지, 프롬프트·어댑터 버전 관리, 문서(공시·역량) 출처 추적을 통해 답변 품질과 신뢰를 관리한다.

---

## 4. 도메인별 방향

| 도메인 | 방향 | 관련 문서/구성요소 |
|--------|------|---------------------|
| **역량(Competency)** | NCS·O*NET을 통합 스키마로 적재하고, RAG·채점·방사형 차트·데이터 지도에서 공통 사용. 레벨 1~8 통일, category/source로 구분. | [extraction-and-data.md](extraction-and-data.md), competency_anchors, run_competency_ingest, run_competency_visualization |
| **공시(Disclosure)** | IFRS·ISO·OECD 등 공시 지침을 disclosures 테이블에 임베딩 저장. RAG 검색·용어 정의·공시 요약·검증에 사용. | [rag-and-vector.md](rag-and-vector.md), [db-and-migrations.md](db-and-migrations.md), disclosure ingest |
| **채팅(Chat)** | LangGraph 에이전트, ExaOne(+ 역량 어댑터)·Gemini(멀티모달). 도구: search_documents, define, analyze_with_exaone, calculate, get_current_time. 스트리밍·첨부 지원. | graph_orchestrator, chat_orchestrator, [exaone-tool-calling-design.md](exaone-tool-calling-design.md) |
| **이력서·Success DNA** | 이력서 파일 → 문서 추출 → LLM 분석 → Success DNA(5대 역량 0–100) + 기본 정보. Core 직원 등록·성과 페이지 입력으로 연동. | resume_analyzer, document_extract, Core/EmployeeFormModal |
| **성과·공시(Performance)** | Human Capital ROI, 지속가능성 영향, 성과 지수, IFRS S1/S2 요약. 직원/전사 집계, 시뮬레이션·보고서. | performance 모듈, DisclosureSection, ImpactAnalysisChart |
| **데이터 지도(Data Map)** | competency_anchors 임베딩 → K-Means 클러스터링 → UMAP 2차원 → 군집별 시각화. 역량 유사도·구조 탐색. | data-map 페이지, /api/clustering/map |
| **이메일·스팸** | 이메일 메타/본문 → ExaOne 분석·Llama 스팸/정책 분류. MCP Spoke로 제공, Hub 경유 호출. | Spam MCP, spam_call, analyze_with_exaone |
| **학습·클러스터링** | 역량 SFT/LoRA(ExaOne), 이메일 SFT, Llama 스팸/rule_policy. 클러스터 라벨링·시각화. 데이터는 raw → prepared → sft. | [runbook.md](runbook.md), training/pipelines, training/models |
| **인프라** | 스타 토폴로지(Hub-Spoke), FastMCP, 단일 FastAPI 앱에 REST·MCP 마운트. DB·마이그레이션·벡터 인덱스 일원화. | [technologies.md](technologies.md), [db-and-migrations.md](db-and-migrations.md) |

---

## 5. Success DNA 정의

프로젝트에서 **Success DNA**는 “이력서·역량 데이터 기반 5대 핵심 역량 점수”를 의미한다.

| 역량 | 설명 (예시) |
|------|-------------|
| **리더십 (leadership)** | 팀·과제 리드, 의사결정·책임 |
| **기술력 (technical)** | 직무 관련 기술·도구 숙련도 |
| **창의성 (creativity)** | 아이디어·혁신·문제 해결 접근 |
| **협업 (collaboration)** | 소통·협력·조직 기여 |
| **적응력 (adaptability)** | 변화 대응, 학습·유연성 |

- **산출**: 이력서 원문을 LLM(역량 전문가 프롬프트 + 군집 데이터)으로 분석해, 각 역량을 **0–100** 점수로 출력.  
- **활용**: Core 직원 등록 시 baseline, 성과 대시보드·방사형 차트(DNABadge), 공시·시뮬레이션 지표 입력으로 사용.  
- **데이터 기반**: competency_anchors·disclosures 등 군집·공시 데이터를 컨텍스트로 넣어 객관성·일관성을 높인다.

---

## 6. 관련 문서

| 문서 | 내용 |
|------|------|
| [README.md](README.md) (docs 목차) | 문서 인덱스 |
| [technologies.md](technologies.md) | 기술 스택·스타 토폴로지 |
| [rag-and-vector.md](rag-and-vector.md) | RAG·벡터·HNSW |
| [db-and-migrations.md](db-and-migrations.md) | DB·마이그레이션 |
| [extraction-and-data.md](extraction-and-data.md) | 문서·역량 추출·스키마 |
| [exaone-tool-calling-design.md](exaone-tool-calling-design.md) | 도구 바인딩 답변 품질 |
| [runbook.md](runbook.md) | 실행·데이터 경로 |
