# 문서 목차

`docs/` 에 있는 프로젝트 문서입니다. **과거 문제·해결**은 [issues-and-resolutions.md](issues-and-resolutions.md)에서 통합 관리합니다.

---

## 문서 구성 (8개)

| 문서 | 설명 |
|------|------|
| [project.md](project.md) | **프로젝트** — 맥락·비전·Success DNA·실행·데이터 폴더(runbook) |
| [backend.md](backend.md) | **백엔드** — 진입점, API, 도메인, DB, MCP, 설정, DB·마이그레이션, RAG·벡터 |
| [frontend.md](frontend.md) | **프론트** — 라우트·플로우·API 매핑·현재 상황 |
| [implementation-status.md](implementation-status.md) | **기능별 구현 상태** — API·도메인별 구현됨/스텁/미구현, 프론트 연동 (AI 인식용) |
| [issues-and-resolutions.md](issues-and-resolutions.md) | **과거 문제·해결** — 스팸 수신, 데이터 구조, ExaOne/LLaMA 정리 등 |
| [strategy.md](strategy.md) | **도메인 전략** — 메일(수신·스팸·AI 분석), 채팅 RAG(1턴·도구·GPU), LLaMA 스팸 관리 |
| [designs.md](designs.md) | **확장·설계안** — 메일–성과 연동, 주소록, 공시 지표, 추출·역량, ExaOne 도구 품질, Apply |
| (이 파일) | 목차 |

---

## 원칙

- **문제·해결**: [issues-and-resolutions.md](issues-and-resolutions.md)에만 상세 기술. 나머지 문서는 현재 동작만 서술.
- **참고**: 세부 API 스펙은 FastAPI `/docs`(Swagger)와 코드 참고.
