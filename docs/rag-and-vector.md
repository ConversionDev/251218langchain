# RAG·벡터 저장·검색

## 현재 구조

- 벡터는 **도메인 테이블의 embedding 컬럼**에만 저장한다. LangChain 전용 테이블(`langchain_pg_collection`, `langchain_pg_embedding`)은 사용하지 않는다.
- **저장소**: disclosures, competency_anchors, **employees**, soccer 엔티티 테이블. PGVector 전용 테이블은 없음.
- **Disclosure 적재**: 입력 경로 `get_data_dir()/disclosure/prepared/`, disclosures 테이블에 BGE-m3 임베딩 저장. 컬렉션/connection 인자 없음.
- **RAG 검색**: ① disclosures(공시 기준 질문) → ② competency_anchors(역량/직무 질문) → ③ **employees**(직원/인력 질문). 직원은 **Neon pgvector(HNSW) 전용**(FAISS 미사용, 실시간 반영). Soccer는 vector_store 없이 엔티티 테이블 + embedding_service만 사용.
- **직원 임베딩 갱신**: `POST /api/employees/embedding` (body `{}`: 전체, `{"id":"E001"}`: 단건). 직원 등록/수정 후 호출하면 RAG 검색에 반영됨.

## HNSW 인덱스 (pgvector)

- **임베딩**: BGE-m3, 벡터 차원 1024 (`vector(1024)`). 코사인 거리 사용. (각 기술 설명은 [technologies.md](technologies.md) 참고.)
- HNSW는 계층형 그래프로 근사 최근접 이웃(ANN) 검색. IVFFlat 대비 **사전 학습 불필요**, 빈 테이블에도 인덱스 정의 가능. 검색 속도·재현율(recall) 우수, 대신 구축·메모리 비용이 더 든다.
- **적용**: 004에서 disclosures, stadiums, teams, players, schedules; 006에서 competency_anchors; **007에서 employees**의 `embedding` 컬럼에 HNSW 생성.
- **파라미터**: `m=24`, `ef_construction=128` (문서 규모·recall 고려). 검색 정확도 우선 시 세션에서 `SET hnsw.ef_search = 100` 권장.

```sql
CREATE INDEX ON disclosures USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
```

- `m`: 레이어당 최대 이웃 수. `ef_construction`: 구축 시 탐색 폭. `ef_search`: 쿼리 시 탐색 폭(클수록 정확, 느려짐).

## RAG 질의 분류 (LangGraph)

- **공시 기준 질문**: IFRS/OECD/ISO 30414 등 키워드 → disclosures 검색.
- **역량·직무 질문**: 직업/역량/능력/O*NET 등 키워드 → competency_anchors 검색.
- **직원·인력 질문**: 직원/이력서/부서/누가 등 키워드 → employees 검색. **직원만** 거리 임계값 0.6 이하로 엄격 필터(엉뚱한 인물 방지).
- **복합 질문**(예: "직원 중 ISO 30414 교육 지표 만족하는 사람") → disclosures + employees 둘 다 검색 후 컨텍스트 융합.
