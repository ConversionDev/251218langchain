# 프로젝트 — 맥락·비전·실행

프로젝트 개요, 비전·목표, **실행·데이터 경로**를 한 문서에 둡니다.  
기능별 구현 상태는 [implementation-status.md](implementation-status.md), 백엔드 상세는 [backend.md](backend.md), 도메인 전략은 [strategy.md](strategy.md) 참고.

---

## 1. 비전·목적

- **비전**: 역량·공시 데이터와 LLM을 결합해 **인사·성과·공시까지 이어지는 AI 플랫폼**을 구축한다.
- **제품 목표**: **ATS·HCM**에 가까운 프로그램. **핵심 도메인**: 역량(competency_anchors)·공시(disclosures)·LLM(ExaOne 중심)·플랫폼(채팅, 이력서→Success DNA, 성과 대시보드, 역량 지도, 직원/신입 관리, 활동 기록, 역량 진단, 자격 검증, 메일·스팸).

### Success DNA (5대 역량)

| 역량 | 설명 |
|------|------|
| 리더십 | 팀·과제 리드, 의사결정·책임 |
| 기술력 | 직무 관련 기술·도구 숙련도 |
| 창의성 | 아이디어·혁신·문제 해결 접근 |
| 협업 | 소통·협력·조직 기여 |
| 적응력 | 변화 대응, 학습·유연성 |

- **산출**: 이력서 원문을 LLM으로 분석해 각 역량 **0–100** 점수. **활용**: Core 직원 등록·신입 관리·성과 대시보드·방사형 차트·직무 전환 분석.

---

## 2. 기술 스택 요약

| 영역 | 기술 |
|------|------|
| 서버 | FastAPI, Uvicorn, Pydantic |
| DB·벡터 | PostgreSQL, pgvector, SQLAlchemy, Alembic, HNSW, B-tree |
| LLM·임베딩 | LangChain, LangGraph, ExaOne 3.5, Gemini(멀티모달), BGE-m3 |
| 인프라 | 스타 토폴로지(Hub-Spoke), FastMCP |
| 프론트 | Next.js, React, TypeScript, Tailwind, PWA |

상세: [backend.md](backend.md) §기술 스택·DB·RAG.

---

## 3. 데이터·인프라 요약

- **주요 테이블**: employees, disclosures, competency_anchors, performance_records, mail_items, audit_logs.
- **RAG**: disclosures·competency_anchors·employees의 embedding 컬럼. 직원 임베딩 갱신 `POST /api/employees/embedding`.
- **데이터 폴더**: [backend.md](backend.md) §실행·데이터 또는 아래 §5 참고.

---

## 4. 백엔드·프론트 구현 현황 요약

- **API**: 직원·성과 활동·채팅·공시·이력서·감사·문서·메일 라우터 구현. 내부 hub_llm_router(Llama/ExaOne).
- **채팅**: LangGraph, RAG(4테이블), 도구(get_hr_summary, get_employee_info 등), ExaOne 스트리밍.
- **프론트**: 랜딩·대시보드·채팅·데이터 지도·신입/기존 직원·활동기록·성과·역량 진단·자격 검증·감사·워크스페이스·apply·resumes·careers. 워크스페이스 메일 UI는 백엔드 미연동(샘플만).

상세: [implementation-status.md](implementation-status.md), [frontend.md](frontend.md).

---

## 5. 실행·데이터 (runbook)

### 프론트엔드

- **실행**: `cd frontend` → `pnpm install` → `pnpm dev`. [http://localhost:3000](http://localhost:3000)
- **환경 변수**: `.env.local`에 `NEXT_PUBLIC_API_URL=http://localhost:8000`. 배포 시 백엔드 URL로 설정.
- **빌드**: `pnpm build` / `pnpm start`

### 데이터 폴더 (app/data)

도메인별 **raw** → **prepared** → **sft** 3단계. `core.paths.get_data_dir()` = `app/data`.

| 단계 | 용도 |
|------|------|
| **raw** | 원본/수집 데이터 |
| **prepared** | 전처리·정제 결과 |
| **sft** | 학습용 SFT, processed/filtered 등 |

**도메인**: disclosure/, spam/sft(exaone_synthetic.jsonl 등). **학습 출력**: `app/artifacts/fine_tuned/` (ExaOne LoRA, LLaMA 어댑터).  
**ExaOne 학습**: 역량 SFT만 사용 — `training.pipelines.sft.run_sft_training` (competency_adapters).

### 배포

- **프론트**: `NEXT_PUBLIC_API_URL` 설정 후 빌드 (예: `https://api.kanggyeonggu.store`, 포트 없음).
- **백엔드**: `CORS_ORIGINS`(쉼표 구분). 비우면 `*`. www에서 API 호출 시 프론트 도메인을 넣어야 CORS 오류가 나지 않음.
- **DB**: `DATABASE_URL` 또는 `POSTGRES_CONNECTION_STRING`. `AUTO_MIGRATE=true`면 기동 시 `alembic upgrade head`.
- **스타트업**: DB 연결만 확인. Embedding·FAISS·Adapter는 첫 요청 시 lazy 로드(t3.small 등 소형 인스턴스 안정화). RAG는 pgvector만 사용(FAISS 미로드).

---

## 6. 구현 예정·확장 포인트

- **ATS·HCM**: 신입 파이프라인 강화, 역량·공시 시계열, 직무·역할 매핑, 리포팅·공시 산출.
- **데이터·RAG**: 직원 임베딩 커버리지, disclosure·competency 적재 운영, 메일–성과 연동, 사내 주소록 확장.
- **UX·운영**: PWA·오프라인, 모니터링·로깅.

설계안: [designs.md](designs.md).
