# 프로젝트 기술 스택

프로젝트에서 사용하는 기술·라이브러리를 영역별로 정리한다. 버전·설정은 `app/requirements.txt`, `frontend/package.json`, `app/core/config.py` 참고.

---

## 1. 백엔드·서버

### FastAPI / Uvicorn

- **FastAPI**: 비동기 API·라우팅·의존성 주입. 채팅 스트리밍, 에이전트 호출, MCP 마운트 등 REST 엔드포인트 제공.
- **Uvicorn**: ASGI 서버. `uvicorn[standard]`으로 프로덕션·개발 서버 실행. 호스트/포트는 `core.config` (기본 127.0.0.1:8000).

### Pydantic

- **pydantic / pydantic-settings**: 요청·응답 스키마, 환경 변수 기반 설정(`Settings`). `core.config`에서 DB·LLM·임베딩·MCP URL 등 일괄 관리. 타입 검증·직렬화(JSON)에 사용.

---

## 2. 데이터베이스·벡터

### PostgreSQL / psycopg2

- **PostgreSQL**: 메인 DB. 도메인 테이블(disclosures, competency_anchors, soccer 엔티티 등)과 벡터 컬럼을 한 DB에서 관리.
- **psycopg2-binary**: PostgreSQL 어댑터. SQLAlchemy·Alembic이 사용. 연결 문자열은 `DATABASE_URL` 또는 `POSTGRES_CONNECTION_STRING` (config).

### pgvector

PostgreSQL 확장으로 **벡터(embedding) 타입**과 **유사도 검색**을 DB 안에서 지원한다.  
`vector(1024)` 컬럼, `<->`(L2)·`<=>`(코사인 거리) 연산자, HNSW·IVFFlat 인덱스 제공. 별도 벡터 DB 없이 RAG 검색에 사용.

### SQLAlchemy / Alembic

- **SQLAlchemy**: ORM·엔진. 도메인 모델과 매핑, 세션·쿼리. pgvector 타입과 연동.
- **Alembic**: 마이그레이션. 스키마 변경을 리비전으로 관리, `upgrade`/`downgrade`/`stamp`로 적용. 서버 기동 시 `auto_migrate`로 자동 적용 가능. 통합 스쿼시(001) + disclosures(002~005) 구조.

### HNSW (Hierarchical Navigable Small World)

**근사 최근접 이웃(ANN)** 인덱스. 벡터를 여러 층의 그래프로 쌓아 전수 조회 없이 유사 벡터를 빠르게 찾는다.

- **동작**: 상위 층에서 대략 위치 파악 후 하위로 내려가며 이웃 탐색. 복잡도 약 O(log N).
- **특징**: **사전 학습 없음**. 빈 테이블에도 인덱스 정의 가능, 행 추가 시 그래프에 노드만 추가해 실시간·증분 적재에 유리.
- **IVFFlat과 비교**: IVFFlat은 centroid 학습 필요, 데이터가 쌓인 뒤 인덱스 생성. HNSW는 구축·메모리 비용 대신 검색 속도·재현율이 좋음.
- **파라미터**: `m`(레이어당 최대 이웃), `ef_construction`(구축 시 탐색 폭), `ef_search`(쿼리 시 탐색 폭). 본 프로젝트는 `m=24`, `ef_construction=128`, 검색 시 `ef_search=100` 권장.

### B-tree 인덱스

PostgreSQL 기본 인덱스. 키 값 순서로 정렬된 트리로, 등호·범위·정렬(`=`, `<`, `>`, `ORDER BY`)에 적합.

- **용도**: 일반 컬럼 검색·필터. disclosures에서 `standard_type`, `(standard_type, page)`, `unique_id`에 B-tree를 걸어 표준·페이지·문서 ID로 빠른 조회.
- **벡터와 구분**: 유사도 검색은 HNSW, 값/구간 조회는 B-tree.

---

## 3. LLM·채팅·임베딩

### LangChain / LangGraph

- **LangChain**: 메시지·도구·BaseChatModel·벡터 스토어 등 추상화. 채팅은 LangGraph 에이전트 단일 진입만 사용하고, 나머지는 메시지/도구/모델 연동용 라이브러리로 활용.
- **LangGraph**: 에이전트 오케스트레이션. 상태 그래프, 노드(라우팅·도구 호출·LLM), 체크포인트. 채팅 플로우는 그래프 오케스트레이터가 LangGraph로 구성.
- **langchain-huggingface / langchain-text-splitters**: HF 모델 래핑, 텍스트 분할(청킹) 등.

### ExaOne 3.5

LG AI Research 한국어 특화 LLM. 역량·RAG 채팅의 메인 모델.

- **역할**: `ExaoneLangChainWrapper`로 LangChain BaseChatModel 구현. 시스템 프롬프트 + 도구 바인딩(`bind_tools`), JSON 기반 툴 콜.
- **최적화**: bitsandbytes **4-bit 양자화**(`exaone_use_4bit`), 선택 시 `torch.compile()`(`exaone_use_compile`). 역량 SFT 어댑터는 `artifacts/fine_tuned/exaone/competency_adapters`에서 로드(`exaone_use_competency_adapter`).
- **설정**: `llm_provider="exaone"`, 모델/어댑터 경로는 HF 캐시 및 `core.paths` 출력 경로 사용.

### Gemini (Google Generative AI)

멀티모달(이미지 + 텍스트) 채팅용. RAG 컨텍스트와 함께 이미지를 Gemini에 보내 스트리밍/일괄 응답.

- **역할**: `domain/hub/llm/gemini_adapter.py`. 이미지 첨부·도메인 비전(이미지→텍스트) 처리.
- **설정**: `GEMINI_API_KEY`, `gemini_model`(기본 `gemini-2.5-flash`). `google-generativeai` 패키지 사용.

### BGE-m3 (FlagEmbedding)

**임베딩 모델**. 문장·문단을 고정 차원 벡터로 변환해 유사도 검색에 사용.

- **차원**: 1024. pgvector에는 `vector(1024)`로 저장.
- **거리**: 코사인 유사도/거리(`<=>`). RAG에서 쿼리와 가까운 문서를 찾을 때 사용.
- **설정**: `default_embedding_model="BAAI/bge-m3"`, `embedding_device`(cuda/cpu). Disclosure·competency_anchors·Soccer 임베딩 공용.

### HuggingFace 생태계

- **transformers / tokenizers / safetensors**: ExaOne·Llama 등 모델 로드, 토크나이저, 가중치 포맷.
- **accelerate / datasets**: 분산·학습 파이프라인, 데이터셋.
- **sentence-transformers**: 임베딩 파이프라인 연동(필요 시).
- **unsloth_zoo**: 학습·최적화용(예: LoRA 훈련).

### PEFT / TRL / bitsandbytes

- **PEFT**: LoRA 등 파라미터 효율 미세조정. 역량 어댑터·이메일 SFT 등.
- **TRL**: RLHF·학습 루프. SFT 파이프라인에서 활용.
- **bitsandbytes**: 4-bit/8-bit 양자화. ExaOne 로딩 시 GPU 메모리 절감.

---

## 4. 문서·데이터 추출

### PyMuPDF (fitz)

PDF에서 텍스트를 **빠르게** 추출. 공시 문서(IFRS, OECD 등) 대량 처리용 **FastExtract** 전략.

- **위치**: `domain/shared/strategy_imples/py_mu_pdf.py` — `PyMuPdfStrategy.extract()` 한 곳에서만 fitz 호출.

### pdfplumber

PDF에서 **표(테이블)** 구조를 인식해 추출. NCS 역량 PDF 등 표가 중요한 문서용 **Structural** 전략.

- **위치**: `domain/shared/strategy_imples/pdf_plumber.py`.

### openpyxl / python-docx

- **openpyxl**: O*NET 등 Excel(.xlsx) 추출. competency_anchors 4종 xlsx, `OnetXlsxStrategy`.
- **python-docx**: Word(.docx) 추출. `document_extract` 등에서 사용.

### pandas

O*NET xlsx 읽기·테이블 처리, 학습 데이터 가공, 클러스터링·SFT 파이프라인 등에서 사용.

---

## 5. 학습·시각화

### PyTorch

- **torch / torchvision / torchaudio**: CUDA(cu118) 기준. ExaOne·Llama·임베딩 모델 로드·추론.
- **torchao**: 양자화·최적화(선택).

### UMAP / Plotly

- **umap-learn**: 역량 등 임베딩을 저차원으로 줄여 클러스터 시각화(`run_competency_visualization.py`).
- **plotly**: 시각화 차트·인터랙티브 그래프.

### scikit-learn / numpy / scipy

클러스터링·거리 계산·전처리 등 수치·ML 유틸.

---

## 6. 인프라·비동기·MCP

### HTTP·비동기

- **httpx**: 동기/비동기 HTTP. 외부 API·MCP 서버 호출.
- **aiohttp / websockets**: 비동기 소켓·웹소켓(스트리밍 등).

### Upstash Redis

- **역할**: 임베딩 job 큐 등(선택). `UPSTASH_REDIS_REST_URL` / `UPSTASH_REDIS_REST_TOKEN`으로 REST API 사용.

### 스타 토폴로지 (Hub-Spoke)

MCP·오케스트레이션 레이어는 **스타(허브-스포크) 토폴로지**로 구성된다. config 주석에서는 "Fractal Star 아키텍처"로 부른다.

- **구조**: **중앙 허브(Hub)** 하나가 모든 도구 호출을 받고, **도메인별 MCP**로만 `call_tool`을 위임한다. 허브는 무거운 모델·DB를 직접 호출하지 않고, 각 도메인 MCP가 자신의 **Spoke**에게 실제 작업(Llama·ExaOne·DB 등)을 맡긴다.
- **데이터 흐름**:  
  `클라이언트/그래프 오케스트레이터` → **HTTP** → `Hub (Central MCP)` → **call_tool** → `도메인 MCP (Chat / Spam / Soccer)` → **call_tool** → `Spoke` → LLM·DB·외부 API.
- **역할 정리**:
  - **Hub**: FastMCP 중앙 서버(NEXUS). 교통경찰처럼 요청을 Chat/Spam/Soccer MCP로만 라우팅. `/mcp`에 마운트.
  - **Spoke 호출자**: Hub를 HTTP로 호출하는 쪽은 "Hub를 쓰는 서비스"(예: 동일 FastAPI 앱 내부). Hub가 도메인 MCP를 호출하고, 도메인 MCP가 Spoke를 호출.
  - **도메인 MCP**: Chat MCP(채팅·검색·계산), Spam MCP(이메일 분석·스팸 분류), Soccer MCP(라우팅·soccer_call). 각각 자신의 Spoke URL로 `call_tool`.
  - **Spoke**: 실제 Llama·ExaOne·RAG·Soccer 백엔드. 도메인 MCP가 FastMCP Client로 Spoke의 MCP 서버를 호출.
- **URL (config)**: `hub_service_url`(Hub 베이스, 기본 8000). `chat_mcp_url` / `chat_spoke_mcp_url`, `spam_mcp_url` / `spam_spoke_mcp_url`(9021/9022), `soccer_mcp_url` / `soccer_spoke_mcp_url`(9031/9032). 기본값은 동일 프로세스(8000)에 마운트; Spam/Soccer는 별도 포트 예시.
- **이점**: 도메인별로 MCP·Spoke를 나누어 채팅·스팸·축구를 독립 배포·확장 가능하게 하고, 허브는 경량으로 두어 단일 진입점·라우팅만 담당하게 한다.

### MCP (FastMCP)

- **fastmcp** (v2): MCP 프로토콜 구현. 위 **스타 토폴로지**의 Hub-Spoke를 FastMCP로 구현.
- **구성**: `/mcp`에 중앙 MCP 앱(Central Control Server) 마운트. `/internal/mcp/chat`, `/internal/mcp/chat-spoke`, Spam(9021/9022), Soccer(9031/9032) 등 도메인별 MCP URL. 오케스트레이터가 `call_tool`로 Hub → 도메인 MCP → Spoke HTTP 호출.
- **용도**: Llama·ExaOne 엔드포인트, 채팅·스팸·축구 도메인 도구 분리. Hub는 `domain/hub/mcp/central_control_server.py`, Spoke 호출은 `domain/hub/mcp/http_client.py`(spokes가 Hub를 HTTP로 호출할 때).

### FAISS

- **faiss-cpu**: 로컬 벡터 검색(필요 시). Windows에서는 faiss-gpu wheel 없음으로 faiss-cpu 사용. Linux에서 GPU 쓰려면 conda로 faiss-gpu 설치 가능.

---

## 7. 프론트엔드

### Next.js / React

- **Next.js 16**: App Router, API 라우트, 터보. 포트 3000 개발 서버.
- **React 19**: UI 컴포넌트, 채팅 패널·폼·대시보드.

### TypeScript

타입 안정성, API·상태 타입 정의(`modules/chat/types.ts` 등).

### 스타일·UI

- **Tailwind CSS**: 유틸리티 기반 스타일. `tailwindcss-animate`, `tailwind-merge`, `class-variance-authority`, `clsx`로 조건부 스타일.
- **Radix UI**: 다이얼로그·라벨·슬롯 등 접근성 좋은 컴포넌트.
- **Framer Motion**: 애니메이션.
- **lucide-react**: 아이콘.

### 상태·차트·기타

- **Zustand**: 클라이언트 전역 상태.
- **Recharts**: 차트(역량 방사형 등).
- **react-markdown**: 마크다운 렌더링(채팅 메시지 등).
- **pdfjs-dist**: PDF 미리보기.
- **sonner**: 토스트 알림.

### PWA

- **workbox-build**: 서비스 워커·오프라인 캐시. `next build && node scripts/generate-sw.js`로 빌드 시 SW 생성.

---

## 8. 요약 표

| 영역 | 기술 |
|------|------|
| 서버 | FastAPI, Uvicorn, Pydantic |
| DB·벡터 | PostgreSQL, psycopg2, pgvector, SQLAlchemy, Alembic, HNSW, B-tree |
| LLM·임베딩 | LangChain, LangGraph, ExaOne 3.5, Gemini, BGE-m3, HuggingFace, PEFT, TRL, bitsandbytes |
| 문서 | PyMuPDF, pdfplumber, openpyxl, python-docx, pandas |
| 학습·시각화 | PyTorch, UMAP, Plotly, scikit-learn |
| 인프라 | httpx, aiohttp, websockets, Upstash Redis, 스타 토폴로지(Hub-Spoke), FastMCP, FAISS |
| 프론트 | Next.js 16, React 19, TypeScript, Tailwind, Radix, Zustand, Recharts, PWA(workbox) |
