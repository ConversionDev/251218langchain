# 아키텍처 (포인터)

이 디렉터리(`backend/ontology/apps`, FastAPI AI 서비스)의 아키텍처는 프로젝트 정본 문서로 통합되었습니다.

- **시스템 구조**(3서비스 토폴로지·헥사고날 계층·MCP 스타 토폴로지·채팅/스팸/메일·배포): [`docs/ARCHITECTURE.md`](../../../docs/ARCHITECTURE.md)
- **구현 현황**(도메인별 API·데이터·학습 파이프라인): [`docs/IMPLEMENTATION.md`](../../../docs/IMPLEMENTATION.md)
- **헥사고날 마이그레이션 상세 이력**: [`docs/archive/hexagonal-architecture-milestone.md`](../../../docs/archive/hexagonal-architecture-milestone.md)

> 요약: 스타일은 **헥사고날 라이트**(`api` → `application` → `domain` ← `infrastructure`) + **중앙 허브·스타 토폴로지(MCP)**. `domain/`은 그 무엇도 import하지 않고, 모든 I/O는 `infrastructure/` 어댑터가 수행한다.
