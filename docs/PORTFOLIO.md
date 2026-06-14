# HR Ontology RAG Platform — 포트폴리오 상세

ㅈㅈ

관련 문서: [ARCHITECTURE.md](ARCHITECTURE.md) · [FEATURES.md](FEATURES.md) · [MODEL_COMPARISON.md](MODEL_COMPARISON.md)

---

## 1. 주요 기능

### 1) 비정형 문서 처리 및 초기 역량 정량화
멀티 포맷(Word·PDF·이미지) 문서 파싱 → **텍스트 레이어 추출 + 스캔본 Gemini 비전 OCR** → LLM 의미 분석 → 5대 핵심 역량(리더십·기술력·창의성·협업·적응력) 정량화
- 추출: pymupdf/pdfplumber(PDF), python-docx(Word). 텍스트 레이어가 없는 스캔/이미지는 pymupdf 렌더 → **Gemini 비전 OCR** 폴백
- 분석: 로컬=학습 EXAONE(GPU) / 배포 폼추출=Gemini flash-lite(~1s) / 역량 점수=학습 EXAONE
- 견고한 JSON 파싱(코드블록·trailing comma·잘린 응답) + 전화·이메일·생년월일 regex 후보정

### 2) 커뮤니케이션 데이터 기반 역량 추적 파이프라인
Mailgun 웹훅 수신 → **LLaMA LoRA 스팸·위험 메일 분류·정제** → 성과 데이터 통합 → 5대 역량 **초기(이력서) 대비 현재(이력서+성과) 성장 추이 도출**
- 수신 즉시 인라인 분류(rate-limit 무관, 별도 워커 불요). 등록 수신자만 저장(미등록=rejected)
- 1차 분류 환경 분기: 로컬=학습 LLaMA SFT 어댑터 / 배포=Gemini(CPU에서 무거운 LLaMA 미로드)
- 성장: 초기 점수=이력서만 산출(1회 저장), 현재=이력서+성과. 차등 분석으로 성장 도출

### 3) SSE 스트리밍 채팅형 인사 조회
LangGraph 기반 RAG 에이전트, 직원·성과·공시·역량 단일·복합 질의 → **12개 시나리오 RAG·Tool Calling 검증(평균 0.95)**
- LangGraph StateGraph(rag→model→tools), 키워드 기반 도구 라우팅(1턴 LLM 1회 최적화)
- 도구 9종: get_hr_summary, list_employees, get_employee_info, get_employee_performance, search_documents, analyze_with_exaone 등
- RAG: pgvector(HNSW) — disclosures·competency_anchors·employees

### 4) 채팅 첨부 RAG·멀티모달
파일 업로드 텍스트 추출·멀티모달 입력 변환 → 질의 컨텍스트 반영 → RAG·LLM 응답
- 이미지 첨부 시 Gemini 멀티모달, 문서 첨부 시 텍스트 추출 후 RAG 컨텍스트 결합

### 5) 역량 온톨로지·지식베이스 구축
직무역량 원천(O*NET·NCS 등) **11.8만 건** → BGE-M3 임베딩 → **FAISS K-Means 클러스터링 + UMAP** → **파인튜닝 EXAONE 자동 라벨링** → 채팅 RAG 근거 지식베이스
- **하이브리드 벡터 검색 설계**(문제 해결): 11.8만 건을 Neon(서버리스) pgvector에 임베딩하려다 부하·타임아웃으로 2천 건에서 막힘 → **대용량 정적 코퍼스(역량 118,161·공시 1,764)를 FAISS 로컬 인덱스로 분리**(전량 임베딩·인메모리 검색), 소량 동적(직원 601)만 pgvector(HNSW) 유지 → Neon 부하 0, 전량 검색
- 채팅 답변에 `[근거: ...]` 출처 표기 — RAG 그라운딩이 지식베이스에서 나옴을 증명

---

## 2. 아키텍처 설계

- **Hybrid Stack**: Spring Boot(인증 게이트웨이) + FastAPI(AI 연산)로 업무 API와 AI 로직 분리
- **Hexagonal(라이트)**: domain/application/infrastructure 레이어 분리로 확장성·유지보수성 확보
- **Hub-and-Spoke (FastMCP)**: 중앙 허브(/mcp) → Chat·Spam 도메인 MCP → Spoke `call_tool` 위임. 허브는 라우팅만, 무거운 모델은 Spoke에서
- **작업 특성별 모델 분기**: 학습 EXAONE(GPU)·llama.cpp(CPU 배포)·Gemini(스팸·이력서폼·OCR·배포 채팅)를 적재적소 배치 — **핵심 역량 판정은 자체 파인튜닝 모델, 빠른 추출·분류·응답은 관리형 API**
- **하이브리드 벡터 검색**: 대용량 정적 코퍼스(역량 11.8만·공시 1.7천)=**FAISS**(인메모리), 소량 동적(직원)=**pgvector(HNSW)** — 서버리스 DB 부하 회피

---

## 2.5 AI 적용 지점 & Agentic RAG

### A. 직접 파인튜닝한 모델 (차별점)
1. **EXAONE 7.8B + competency 어댑터(QLoRA)** — 이력서 5대 역량 점수(Success DNA)
2. **Llama 3.2 + spam 어댑터(Unsloth)** — 스팸 분류(로컬)
3. **EXAONE 클러스터 라벨링** — 역량 군집 주제명 부여(오프라인)

### B. LLM 추론 지점 (12)
| # | 기능 | 모델 |
|---|---|---|
| 1 | 이력서 → 5대 역량 점수 | EXAONE(로컬·배포, 쇼케이스) |
| 2 | 이력서 기본정보·학력·경력 추출 | 배포 Gemini / 로컬 EXAONE |
| 3 | 스캔·이미지 이력서 OCR | Gemini 비전 |
| 4 | 메일 → 성과·역량 분류·기록 | EXAONE(비동기) |
| 5 | 초기 대비 현재 성장(2지점) | EXAONE 차등 분석 |
| 6 | 스팸 1차 분류 | 로컬 LLaMA / 배포 Gemini |
| 7 | 스팸 애매케이스 judge | EXAONE / Gemini |
| 8 | 채팅 RAG 에이전트 답변 | 로컬 EXAONE / 배포 Gemini |
| 9 | 채팅 이미지 멀티모달 | Gemini |
| 10 | 이미지 → RAG 검색 캡션 | Gemini |
| 11 | 공시 기여도 예측 | RAG + LLM |
| 12 | 직원 RAG 페르소나 생성 | EXAONE |

### C. RAG·벡터 인프라
- 임베딩: BGE-M3 (dense)
- **하이브리드 벡터 검색**: FAISS(역량 **118,161** · 공시 **1,764** — 정적 대용량, 인메모리) + pgvector HNSW(직원 601 — 동적)
- 클러스터링: FAISS K-Means + UMAP → competency_anchors 역량 지식베이스(EXAONE 라벨링)

> **숫자 주의**: competency_anchors 테이블 11.8만 건 전량이 FAISS에 임베딩·검색됨. (pgvector엔 2천 건만 — 초기 Neon 부하 한계로 남은 잔재, RAG 경로 아님)

### Agentic RAG 판정 — defensible
- **그래프**: LangGraph StateGraph `rag → model → tools → (조건부 루프) → 답변`
- **Tool Calling**: 9개 도구 `bind_tools`(get_hr_summary·list_employees·search_documents 등)
- **멀티스텝**: `should_use_tools` 조건부 분기로 도구 실행 후 재호출
- **RAG**: pgvector 검색을 도구·컨텍스트로 결합

→ 단순 RAG(1패스)가 아닌 **도구·멀티스텝 에이전트 그래프 = Agentic RAG**.
**정직 포인트(면접 방어)**: 도구 선택은 **키워드 라우팅(1턴 최적화) + LLM tool-calling 폴백 하이브리드** — 순수 reasoning agent가 아니라 *속도를 위해 키워드 라우터를 앞에 둔 하이브리드*. (불필요한 LLM 왕복 제거 = 엔지니어링 판단으로 어필)

> 이력서 표현: "LangGraph 기반 Agentic RAG — pgvector 검색 + 9개 Tool Calling 멀티스텝 오케스트레이션, 키워드 라우팅+LLM tool-calling 하이브리드로 1턴 최적화"

---

## 3. 기술 스택 (계층별)

| 계층 | 기술 |
|---|---|
| 모델 | EXAONE 3.5 7.8B(LG, 파인튜닝) · Llama 3.2 3B(Meta, 파인튜닝) · Gemini(Google) · BGE-M3(임베딩) |
| 학습·최적화 | PyTorch · PEFT(LoRA) · **QLoRA(bitsandbytes NF4)=EXAONE** · **Unsloth=Llama** · TRL SFTTrainer |
| 추론·서빙 | transformers(로컬 GPU) · **llama.cpp(GGUF, CPU 배포)** |
| 에이전트 | LangChain · LangGraph(멀티스텝 그래프) · FastMCP(허브 오케스트레이션) |
| 검색·벡터 | pgvector(운영 HNSW) · FAISS(로컬 인덱스·클러스터링) |
| 백엔드·인프라 | FastAPI · Spring Boot · PostgreSQL/Neon · Upstash Redis · AWS EC2(비-Docker) · Next.js+PWA(Vercel) |

> 학습: **EXAONE=표준 QLoRA(bitsandbytes+PEFT)**, **Llama=Unsloth 가속**. EXAONE는 Unsloth 미지원 아키텍처라 표준 경로로 분기(엔지니어링 판단).

---

## 4. 기능 구현 현황 (라이브 검증 기준, 정직)

| 기능 | 상태 | 비고 |
|---|---|---|
| 이력서 분석·역량 정량화(+OCR) | ✅ 구현·배포 | 라이브 ~2s, 스캔본 OCR 검증 완료 |
| 초기 대비 성장(2지점) | ✅ 구현·배포 | 초기 vs 현재 차등 산출 검증 |
| 메일 수신·인라인 스팸 분류 | ✅ 구현·배포 | 웹훅→폴더 배치 ~1s |
| 메일 CRUD(발송·답장·전달·임시저장·별표·검색) | ✅ 구현·배포 | 서버측 검색 |
| 채팅 RAG 에이전트(SSE·도구·멀티모달) | ✅ 구현·배포 | 답변 LLM 환경분기: 로컬 EXAONE / 배포 Gemini(웜 ~2s). 도구·RAG는 동일 |
| 역량 지식베이스(FAISS 하이브리드) | ✅ 구현·검증 | 역량 11.8만·공시 1.7천 FAISS 전량 임베딩·검색, 클러스터링·EXAONE 라벨링 |
| 공시 기여도 예측(RAG+LLM) | ◐ 부분 | RAG ingest·API는 됨. **배포 예측 작업이 pending에서 미완료(EXAONE CPU)** — 데모 헤드라인 비추천 |
| FastMCP 허브 오케스트레이션 | ✅ 구현 | 중앙→도메인 MCP→Spoke |
| 직무 전환 인텔리전스 | ◐ 부분 | 채팅 API 재사용, 전용 백엔드 없음 |
| 역량 클러스터 지도(/data-map) | ◐ 개발 전용 | 페이지가 prod에서 notFound()(의도). 클러스터 HTML은 수동 viz 스크립트 |
| 자격검증(credential) | ◐ 데모 | 블록체인 시뮬레이션(클라이언트) |
| 임베딩 동기화 job | ◐ 스텁 | 도메인 제거로 호환용 no-op |
| Flutter 모바일 | ✗ 미구현 | 스캐폴드만 |

## 5. 알려진 한계 / 개선 여지

- **배포 채팅 속도(해소)**: 답변 생성을 환경 분기 — 로컬=학습 EXAONE(쇼케이스), 배포=Gemini(`CHAT_LLM=gemini`, 웜 ~2s, 40s+→2s). 도구·RAG는 키워드 라우팅이라 동일.
- **메일함 소유자 인증 미연동**: 현재 프론트 직원ID 입력 기반(포트폴리오 단순화). 실서비스 전환 시 로그인 세션→사번 + 서버측 소유권 검증 필요.
- **성장 추이는 2지점**: 초기 vs 현재. 풀 시계열(분기별 스냅샷)은 별도 테이블 필요.
- **클러스터 지도**: `/data-map`은 개발 모드 전용(prod notFound). 노출하려면 viz HTML 생성 + 페이지 게이트 해제 필요.

## 6. 라이브 검증(2026-06-14)

배포 백엔드(api.kanggyeonggu.store) 전 엔드포인트 200 확인: health, agent(health/providers/tools), employees(목록·검색), mail, address-book, disclosure, audit, activity-records, document/supported-extensions, resume/analyze, mail/filter(스팸 reject 0.99). 프론트(Vercel) 전 페이지 200. 세션 중 `/api/agent/tools` 500 1건 발견·수정(TOOLS import 경로).
