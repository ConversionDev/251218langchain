# HR Ontology RAG Platform

> 파인튜닝된 EXAONE 기반 **HR 도메인 특화 RAG 챗봇 + Agent 플랫폼**
> CPU/GPU 런타임 전환, LangGraph 오케스트레이션, 공시/역량/성과/직원 도메인 통합.

- 운영 데모: <https://www.kanggyeonggu.store>
- API 엔드포인트: <https://api.kanggyeonggu.store>

---

## 1. 프로젝트 개요

- **목적**: 사내 HR 데이터(직원/역량/성과/공시)를 LLM Agent + RAG로 질의응답
- **차별점**
  - 단일 EXAONE 모델을 **두 가지 런타임**으로 서빙 (로컬 GPU `transformers` / 배포 CPU `llama.cpp GGUF`)
  - LangGraph 기반 **조건부 툴 라우팅** (질문 유형에 따라 RAG/툴 선택적 호출)
  - 도메인 데이터를 **`domain/hub/repositories` + `domain/hub/rag`** 두 축으로 분리 (정형 SQL + 벡터)

---

## 2. 기술 스택

| 계층 | 기술 |
|---|---|
| Frontend | Next.js (App Router), TypeScript, TailwindCSS |
| API Gateway | Spring Boot (OAuth2, JWT 인증) |
| Backend | FastAPI (Python 3.11), LangChain, **LangGraph** |
| LLM | EXAONE 7.8B (LoRA 파인튜닝) → GGUF Q4_K_M |
|  | Gemini 2.5 Flash (멀티모달 이미지 분석) |
| Embedding | BGE-M3 |
| Vector DB | PostgreSQL + `pgvector` (Neon) |
| Cache | Upstash Redis |
| Infra | AWS EC2 (m7i-flex.large), Nginx, Let's Encrypt |
| CI/CD | GitHub Actions (rsync + ssh nohup) |

---

## 3. 아키텍처 개요

```
[ Next.js ]
     |
     v
[ Nginx (api.kanggyeonggu.store, HTTPS) ]
     |--- /api/auth/*      → Spring Boot Gateway (:8080)
     |--- /api/agent/*     → FastAPI (:8000)   ← SSE 스트리밍
     |--- /api/**          → FastAPI (:8000)
                              |
                              +-- LangGraph Agent
                              |     +-- Tools: get_employee_info, list_employees, get_hr_summary ...
                              |     +-- RAG node (pgvector + BGE-M3)
                              +-- LLM Provider
                                    +-- exaone (HF transformers, GPU)
                                    +-- llama_cpp (GGUF, CPU)   ← 현재 배포본
```

---

## 4. 주요 기능

- **HR 챗봇**: "강경구의 직급과 부서 알려줘" → `get_employee_info` 툴 호출
- **전사 요약**: "우리 회사 직원 몇 명이야?" → `get_hr_summary`
- **역량/성과 RAG**: 자유서술 질의 → pgvector 유사도 검색 후 답변
- **이력서 분석**: PDF 업로드 → Gemini 멀티모달로 추출
- **이메일 스팸 분류**: LLaMA 3 파인튜닝 (로컬 데모, CPU 배포 제외)

---

## 5. 로컬 실행

### Frontend
```bash
cd frontend
pnpm install
pnpm dev
```

### Backend (FastAPI)
```bash
cd backend/ontology/apps
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### 환경변수 (`.env`)
- `DATABASE_URL` (Neon PostgreSQL)
- `LLM_PROVIDER` = `exaone` (로컬 GPU) | `llama_cpp` (CPU GGUF)
- `EXAONE_GGUF_PATH` (llama_cpp일 때 필수)
- `UPSTASH_REDIS_URL` (`rediss://default:TOKEN@HOST:6379` — Gateway·FastAPI 공통, REST URL·TOKEN 자동 추출)
- `GEMINI_API_KEY` (이미지 분석용)

---

## 6. EC2 CPU 배포 (2025-04)

### 목표
> GPU 없는 **AWS EC2 m7i-flex.large (2 vCPU, 8GB RAM, 월 ~$70)** 환경에 7.8B 파인튜닝 모델 서빙

### 모델 변환 파이프라인

```
EXAONE 7.8B (NF4) + LoRA
        │
        │ scripts/export_exaone_merged_hf_for_gguf.py  (Linear4bit → fp16 역양자화)
        ▼
HF safetensors (fp16)
        │
        │ llama.cpp/convert_hf_to_gguf.py --outtype f16
        ▼
exaone_f16.gguf
        │
        │ llama-quantize.exe ... Q4_K_M
        ▼
exaone_q4_k_m.gguf (tensor만 OK, metadata 손상)
        │
        │ scripts/patch_gguf_from_f16.py  (f16의 KV + Q4의 tensor 결합)
        ▼
exaone_competency_q4_k_m.gguf  (4.5GB, 배포 최종본)
```

### 트러블슈팅 요약 (상세는 [docs/issues-and-resolutions.md §12](docs/issues-and-resolutions.md))

- **bitsandbytes 호환성**: `Linear4bit` 레이어를 fp16으로 직접 역양자화
- **GGUF 메타데이터 손상**: Q4 변환 시 토크나이저 merges 누락 → f16 GGUF의 KV를 Q4 tensor와 재결합하는 패치 스크립트 작성
- **OOM (8GB RAM)**: `n_ctx` 8192 → **2048**, swap 4GB 파일 추가
- **Nginx SSE 타임아웃**: `proxy_buffering off`, `proxy_read_timeout 600s` 로 장시간 스트리밍 허용
- **Agent 프롬프트 토큰 폭주**: 단일 직원 질의 시 `list_employees` 강제 호출 + RAG 문서 주입 스킵 → **3839 → ~300 토큰 (-92%)**
- **DB 연결 누락**: `DATABASE_URL` 값에 `&` 포함 → `.env`에 반드시 따옴표 감싸서 기록

### 현재 운영 상태

| 항목 | 상태 |
|---|---|
| 배포 | ✅ HTTPS 동작 |
| 응답 정확도 | ✅ 한국어, 도메인 답변 |
| 응답 속도 | ⚠️ 30초~1분+ (CPU 2 vCPU 한계) |
| 월 비용 | ~$70 |

### 제약과 트레이드오프
- **속도는 프로덕션급이 아님**. 월 비용 최소화를 위해 CPU 인스턴스 선택의 결과
- 프로덕션 전환 옵션:
  1. GPU 인스턴스 (g4dn.xlarge, 월 ~$380)
  2. OpenAI/Gemini 어댑터 추가 구현 (현재 Gemini는 이미지 전용)
  3. 소형 모델(2~4B)로 교체

---

## 7. 프로젝트 문서

모든 세부 문서는 [`docs/`](docs/) 참조:

- [전체-프로젝트-구현현황.md](docs/전체-프로젝트-구현현황.md)
- [backend.md](docs/backend.md) / [frontend.md](docs/frontend.md) / [mail.md](docs/mail.md)
- [strategy.md](docs/strategy.md) — 도메인 전략
- [issues-and-resolutions.md](docs/issues-and-resolutions.md) — **트러블슈팅 히스토리**
- [implementation-status.md](docs/implementation-status.md)

---

## 8. 라이선스

MIT
