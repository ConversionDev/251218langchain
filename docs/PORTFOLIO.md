# HR Ontology RAG Platform — 포트폴리오 상세

AI 기반 인적자본(HCM) 플랫폼. 비정형 문서·커뮤니케이션 데이터를 자체 파인튜닝 LLM과 RAG로 분석해 **5대 핵심 역량(리더십·기술력·창의성·협업·적응력)** 을 정량화하고, 채용·배치·성장 추적을 지원한다.

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

---

## 2. 아키텍처 설계

- **Hybrid Stack**: Spring Boot(인증 게이트웨이) + FastAPI(AI 연산)로 업무 API와 AI 로직 분리
- **Hexagonal(라이트)**: domain/application/infrastructure 레이어 분리로 확장성·유지보수성 확보
- **Hub-and-Spoke (FastMCP)**: 중앙 허브(/mcp) → Chat·Spam 도메인 MCP → Spoke `call_tool` 위임. 허브는 라우팅만, 무거운 모델은 Spoke에서
- **작업 특성별 모델 분기**: 학습 EXAONE(GPU)·llama.cpp(CPU 배포)·Gemini(스팸·이력서폼·OCR·배포 채팅)를 적재적소 배치 — **핵심 역량 판정은 자체 파인튜닝 모델, 빠른 추출·분류·응답은 관리형 API**

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
| 공시 기여도 예측(RAG+LLM) | ✅ API 구현 | 프론트 직접 연동은 부분 |
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
