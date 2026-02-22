# DB·마이그레이션

## Alembic (통합 스쿼시)

- **초기 마이그레이션**: `versions/001_initial_squashed.py` (revision: `001_initial`). pgvector 확장, stadiums, teams, players, schedules, 각 embedding 테이블(vector 1024).
- **새 환경 / 테이블 전부 없는 DB**: `cd app` 후 `alembic upgrade head` → 한 번에 전체 스키마 적용.
- **이미 테이블이 있고 스키마만 수동으로 맞춘 경우**: `alembic stamp 001_initial`로 현재 리비전만 표시(실제 적용 없음).
- **스키마 변경 시**: `cd app` → `alembic revision --autogenerate -m "설명"` → `alembic upgrade head`. 서버 기동 시에는 upgrade만 실행하며, 새 마이그레이션 파일은 수동으로 생성해야 한다.

**주요 명령**: `alembic current` (현재 리비전), `alembic history` (목록), `alembic downgrade -1` (마지막 1개 롤백).

**참고**: 기존 DB에 `alembic_version`에 예전 리비전이 남아 있으면, 통합 전환 시 `alembic stamp 001_initial`로 맞춘 뒤 필요 시 스키마를 수동 정리. 프로덕션 적용 전 마이그레이션 파일 검토·백업 권장.

## disclosures 테이블 재생성 (DROP 한 경우)

테이블을 직접 DROP 했을 때 같은 스키마로 다시 만드는 절차.

1. `cd app`
2. `alembic stamp 001_initial` — 002~005를 "아직 안 올린 상태"로 표시.
3. `alembic upgrade head` — 최신까지 적용.
   - 002: disclosures 테이블 생성 (content, embedding_content, embedding, source, page, created_at)
   - 003: standard_type, section_title, metadata, unique_id 컬럼 추가
   - 004: embedding 컬럼에 HNSW 인덱스 (disclosures, stadiums, teams, players, schedules)
   - 005: disclosures용 B-tree 인덱스 (standard_type, standard_type+page, unique_id)
   - 006: competency_anchors 테이블 + HNSW·btree·unique_id
   - 007: **employees** 테이블 (직원 CRUD·직무 처리). disclosure_metrics(JSONB), **embedding_content**, **embedding** vector(1024), **HNSW** + **B-tree**(department, name, job_title, department+name). 직원 RAG는 Neon pgvector(HNSW) 전용(FAISS 미사용).
4. **적재**: 입력 `app/data/disclosure/prepared/`. 실행: `python -m training.pipelines.ingest.run_disclosure_ingest`. RAG 채팅에서 IFRS/OECD 등으로 검색해 참조 문서 확인.
5. **직원 임베딩**: 직원 등록/수정 후 RAG 검색에 반영하려면 `POST /api/employees/embedding` 호출(전체 또는 `{"id":"E001"}`). [rag-and-vector.md](rag-and-vector.md) 참고.
