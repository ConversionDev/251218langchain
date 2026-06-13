# 구현 현황

도메인별 **무엇이 동작하는가**(API·프론트 연동), 데이터·RAG, 학습 파이프라인을 정리합니다. **전체 기능 분류(에이전트 vs 플랫폼)** 는 [FEATURES.md](FEATURES.md) 참고.

- **상태**: 구현됨(실제 동작·DB/외부 연동) / 부분 구현(핵심만·데이터 의존) / 스텁(고정 응답·no-op) / 미구현
- **프론트 연동**: 연동됨(프론트가 호출) / 미연동(백엔드만)
- API 상세 스펙은 서버 실행 후 FastAPI `/docs`(Swagger), 시스템 구조는 [ARCHITECTURE.md](ARCHITECTURE.md), 프론트는 [FRONTEND.md](FRONTEND.md) 참고.

---

## 1. 기술 스택

### 1.1 백엔드 (FastAPI)

| 구분 | 기술 |
|------|------|
| 웹·검증 | FastAPI, Uvicorn, Pydantic, pydantic-settings |
| DB·벡터 | PostgreSQL, pgvector, psycopg2-binary, SQLAlchemy, Alembic |
| LLM·에이전트 | LangChain, LangGraph, EXAONE 3.5/7.8B, LLaMA 3, Gemini 2.5 Flash |
| 임베딩 | FlagEmbedding (BGE-M3) |
| 학습 | Hugging Face(transformers, datasets), PyTorch, PEFT, TRL, bitsandbytes, llama.cpp |
| MCP | FastMCP |
| 문서 처리 | PyMuPDF, pdfplumber, openpyxl, python-docx, pyhwp |
| 분석·시각화 | pandas, numpy, scipy, scikit-learn, umap-learn, plotly |
| 캐시 | Upstash Redis (선택) |

### 1.2 프론트엔드 (Next.js)

| 구분 | 기술 |
|------|------|
| 프레임워크 | Next.js 16, React 19, TypeScript |
| 스타일 | Tailwind CSS, tailwindcss-animate |
| 상태·UI | Zustand, Radix UI, Framer Motion, GSAP, Lucide React |
| 차트·문서 | Recharts, react-markdown, pdfjs-dist |
| PWA·기타 | Workbox, sonner, clsx, tailwind-merge |

### 1.3 Spring Gateway

Spring Boot (Java 21), Spring Security, Spring Data JPA, Spring Data Redis, OAuth2(카카오/네이버/구글), JWT.

---

## 2. 도메인별 구현 현황

### 2.1 직원 (Employees)

| 항목 | 상태 | 프론트 |
|------|------|--------|
| 목록·단건·생성·수정·삭제 (GET/POST/PUT/DELETE `/api/employees`) | 구현됨 | 연동됨 |
| 다음 ID (`/api/employees/next-id`), 이력서 해시 중복 확인 (`/check-resume-hash`) | 구현됨 | 연동됨 |
| 직원별 이력서 분석 (`POST /api/employees/{id}/analyze`) | 구현됨 | 연동됨 |
| 직원 임베딩 갱신 (`POST /api/employees/embedding`) | 구현됨 | 연동됨 |
| 직원 프로필 백필 (`POST /api/employees/profile-backfill`, dryRun·seed) | 구현됨 | 연동됨 |
| 감사 로그 기록 (생성/수정/삭제 시, x-actor 헤더) | 구현됨 | (내부) |

목록은 페이지네이션 + employmentType 필터. 생성은 camelCase 페이로드, 409 시 기존 직원 안내.

### 2.2 성과 활동 (Activity Records)

| 항목 | 상태 | 프론트 |
|------|------|--------|
| 활동 목록·직원별·단건·내 활동 (GET `/api/activity-records*`) | 구현됨 | 연동됨 |
| 업무 제출 (`POST /api/activity-records/submit`, meeting/report/email) | 구현됨 | 연동됨 |

### 2.3 채팅 (Agent / LangGraph)

| 항목 | 상태 | 프론트 |
|------|------|--------|
| 파일 업로드 (`POST /api/agent/upload`, 이미지·PDF·Word·Excel) | 구현됨 | 연동됨 |
| 스트리밍 채팅 (`POST /api/agent/chat/stream`, SSE) | 구현됨 | 연동됨 |
| 스레드 이력·삭제 (GET/DELETE `/api/agent/threads/{id}`) | 구현됨 | 연동됨 |
| 프로바이더·도구 목록, 에이전트 헬스 | 구현됨 | (선택) |

RAG(disclosures·competency_anchors·employees) + 도구(get_hr_summary 등) + EXAONE 스트리밍 + Gemini 멀티모달(이미지). 그래프·라우팅 상세는 [ARCHITECTURE.md §5](ARCHITECTURE.md).

### 2.4 이력서 분석 (Resume)

| 항목 | 상태 | 프론트 |
|------|------|--------|
| 이력서 분석 (`POST /api/resume/analyze`) | 구현됨 | 연동됨 |

PDF/TXT/Word/HWP → 텍스트 추출 → LLM 분석 → name, jobTitle, department, email, **successDna(5대 역량)** 반환. Core 신입 관리에서 이력서 업로드 시 호출.

### 2.5 감사 로그 (Audit)

| 항목 | 상태 | 프론트 |
|------|------|--------|
| 감사 로그 조회 (`GET /api/audit/logs`, entityType/Id·action·actor·기간·limit) | 구현됨 | 연동됨 |

### 2.6 공시 (Disclosure)

| 항목 | 상태 | 프론트 |
|------|------|--------|
| 적재 상태 (`GET /api/disclosure/status`) | 구현됨 | 미연동 가능 |
| 기여도 예측 동기 (`POST /api/disclosure/check`) | 구현됨 | 미연동 가능 |
| 기여도 예측 비동기 (job_id 반환 → `GET /check/result/{job_id}` 폴링) | 구현됨 | 미연동 가능 |
| 공시 임베딩 실행 (`POST /api/disclosure/embedding/run`) | 구현됨 | (관리) |
| 공시 문서 적재 파이프라인 (disclosure ingest) | 구현됨 | CLI/수동 |

### 2.7 이메일 / 메일 (Mail)

| 항목 | 상태 | 프론트 |
|------|------|--------|
| 수신 (`POST /api/mail/receive`, Webhook·HMAC·멱등·Resolver·스팸 판정) | 구현됨 | 미연동 |
| 수신 메일 AI 분석 (inbox 저장 후 비동기 성과/역량 분류) | 구현됨 | — |
| 스팸 필터 (`POST /api/mail/filter`, action·routing·reason_codes 반환) | 구현됨 | 미연동 |
| 이메일 전송 (`POST /api/mail/send`) | 스텁 | 미연동 |
| 워크스페이스 메일 UI (`/workspace/mail`) | 부분 구현 | 샘플만, 백엔드 미연동 |

수신·스팸·AI 분석은 구현됨. send는 메타데이터 저장만(외부 SMTP 미구현). 설계·흐름은 [ARCHITECTURE.md §6~7](ARCHITECTURE.md).

### 2.8 데이터 지도 (Clustering Map)

| 항목 | 상태 | 프론트 |
|------|------|--------|
| 지도 HTML 서빙 (`GET /api/clustering/map`, theme=dark) | 구현됨 | 연동됨 |
| competency_map.html 생성 | 부분 구현 | 수동 스크립트 필요(미실행 시 404) |

`python -m training.pipelines.clustering.run_competency_visualization`로 사전 생성(역량 임베딩 + UMAP + K-Means).

### 2.9 내부 API (Hub LLM) · MCP

| 항목 | 상태 | 호출 주체 |
|------|------|-----------|
| LLaMA 스팸 분류 (`POST /internal/llama/classify_spam`) | 구현됨 | 스포크·email_router |
| EXAONE 생성·이메일 분석 (`POST /internal/exaone/*`) | 구현됨 | 스포크 |
| `/mcp` 허브 마운트, Chat/Spam 스포크 위임 | 구현됨 | 허브 |

프론트는 직접 호출하지 않음(MCP·스팸 플로우 내부용). 채팅은 EXAONE만, 스팸만 LLaMA 사용.

### 2.10 기타·인프라

| 항목 | 상태 |
|------|------|
| CORS, DB 마이그레이션(AUTO_MIGRATE), RAG 초기화, `GET /`·`/health` | 구현됨 |
| 임베딩 동기화 (`run_embedding_sync_task`) | 스텁 (호출처 없음) |

---

## 3. 데이터·RAG

- **데이터 폴더**: `data/` — 도메인별 **raw**(원본·입력 샘플) → **prepared**(전처리) → **sft**(학습용) 3단계.
- **학습 출력**: `artifacts/fine_tuned/` (EXAONE 역량 LoRA, LLaMA 스팸 어댑터). `.gitignore` 대상 — 저장소에 포함되지 않음.
- **RAG 저장소**: disclosures·competency_anchors·employees의 `embedding` 컬럼(pgvector). LangChain 전용 PG 테이블은 미사용.
- **적재**: 공시는 `data/disclosure/prepared/` → BGE-M3 임베딩(`run_disclosure_ingest`). 직원은 `POST /api/employees/embedding`.

---

## 4. 학습 파이프라인

### 4.1 EXAONE 역량 LoRA

- 런타임에서 사용하는 EXAONE 어댑터는 **역량 SFT(competency_adapters)** 만. `training.pipelines.sft.run_sft_training`(4에포크).
- 배포본은 LoRA 병합 → GGUF Q4_K_M 변환(CPU 추론). 변환 파이프라인·난제는 [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

### 4.2 LLaMA 스팸 분류 (한국어 중심)

- **데이터 생성(ETL)**: EXAONE이 한국어 스팸 **15종** + 햄 **7종**(Hard Negative 포함)을 합성. `run_exaone_generate_spam_sft`(`--full` 2,000 / `--large` 3,600 / `--max` 5,000건). 참고 데이터(3곳) few-shot 기본 적용.
  - 스팸 15종: 피싱, 당첨, 광고, 가짜경고, 성인/도박, 택배사칭, 정부기관사칭, 대출/금융, 결제위장, 계정보안알림, 투자권유, 구직·채용사칭, 설문·리워드, 친구·지인사칭, 기타.
  - 햄 7종: 업무, 개인, 뉴스레터 + Hard Negative(업무마케팅, 인사/IT공지, 실제배송, 구독뉴스레터).
  - 출력: `exaone_synthetic.jsonl` + train(90%)/val(10%).
- **학습**: `python -m training.models.llama.spam_classifier.finetune`. 출력 → `artifacts/fine_tuned/llama/spam_adapters/`.
- **런타임**: `llama_use_spam_adapter=True`면 LlamaManager가 베이스 + PEFT 어댑터 로드.
- **예상 성능**: 2,000건 + 15종 + 참고 시 검증 정확도 82~88%, 3,600/5,000건은 88%+ 기대.
- **GPU 권장 실행**(RTX 4060 Ti 16GB 등): `--max --fast`. 스크립트가 `TOKENIZERS_PARALLELISM=false`, `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` 자동 적용.

---

## 5. 성능·비용·UX 개선 (구현 완료)

| 구분 | 구현 내용 |
|------|-----------|
| **시간 감소** | 임베딩 배치 처리(32·512), 채팅 SSE 스트리밍(첫 토큰 대기 단축), 이력서 분석 세션 캐시(동일 파일 즉시 반환) |
| **인프라 비용** | Lazy 로딩(스타트업 시 DB만, 모델은 첫 요청 시), FAISS 미로드·pgvector만 사용 |
| **리소스** | 임베딩 모델 싱글톤·캐시, 추론 후 `torch.cuda.empty_cache()`, 스팸 분류 배치(batch_size=32) |
| **로딩·UX** | 직원·신입 목록 페이지네이션(20건), 로딩 UI(버튼 disabled), 토스트 알림 |

---

## 6. 실행 (runbook)

### 프론트엔드

```bash
cd frontend && pnpm install && pnpm dev   # http://localhost:3000
```

`.env.local`에 `NEXT_PUBLIC_API_URL=http://localhost:8000`. 빌드: `pnpm build` / `pnpm start`.

### 백엔드 (FastAPI)

```bash
cd backend/ontology/apps
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
python main.py   # 또는 uvicorn fastapi_server:app --host 0.0.0.0 --port 8000
```

`DATABASE_URL`/`POSTGRES_CONNECTION_STRING` 설정, `AUTO_MIGRATE=true`면 기동 시 마이그레이션 자동 적용. 환경변수 전체는 [ARCHITECTURE.md §9.4](ARCHITECTURE.md).

### 확장 예정

ATS·HCM 강화(신입 파이프라인, 역량·공시 시계열, 직무·역할 매핑), 데이터·RAG 커버리지 확대, 사내 주소록 확장(person/shared/group), 메일–성과 연동(`save_to_performance`), PWA·오프라인·모니터링.
