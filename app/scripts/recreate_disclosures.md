# disclosures 테이블 재생성 (테이블을 DROP 한 경우)

테이블을 직접 DROP 했을 때, 같은 스키마로 다시 만들기 위한 절차.

## 1. app 디렉터리에서 실행

```bash
cd app
```

## 2. 마이그레이션 버전을 001로 되돌리기

(002~005를 "아직 안 올린 상태"로 표시)

```bash
alembic stamp 001_initial
```

## 3. 최신까지 다시 적용 (disclosures + 인덱스 생성)

```bash
alembic upgrade head
```

- 002: `disclosures` 테이블 생성 (content, embedding_content, embedding, source, page, created_at)
- 003: standard_type, section_title, metadata, unique_id 컬럼 추가
- 004: embedding 컬럼에 HNSW 인덱스
- 005: standard_type, (standard_type, page), unique_id B-tree 인덱스

## 4. 적재 경로 및 실행

- **입력 경로**: `app/data/disclosure/prepared/` (core.paths: `get_data_dir() / "disclosure" / "prepared"`)
- **저장**: `disclosures` 테이블 (BGE-m3 임베딩 채움)
- **실행** (app 디렉터리에서):
  ```bash
  cd app
  python -m training.pipelines.ingest.run_disclosure_ingest
  ```
- RAG 채팅에서 IFRS/OECD 등 질의로 검색·참조 문서 확인
