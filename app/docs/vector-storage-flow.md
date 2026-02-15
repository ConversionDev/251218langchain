# 벡터 저장·검색 흐름 (RAG)

벡터는 **도메인 테이블의 embedding 컬럼**에만 저장된다. LangChain 전용 테이블(`langchain_pg_collection`, `langchain_pg_embedding`)은 사용하지 않는다.

## 현재 구조

| 구분 | 내용 |
|------|------|
| **벡터 저장소** | disclosures + competency_anchors + soccer 엔티티 테이블만 (PGVector 전용 테이블 없음) |
| **Disclosure 적재** | disclosures 테이블에만 저장. 컬렉션/connection 인자 없음. 입력: `get_data_dir()/disclosure/prepared/` |
| **RAG 검색** | ① disclosures 테이블 → ② competency_anchors 사용 |
| **Soccer** | vector_store 인자 없음. 엔티티 테이블 + embedding_service만 사용 |
| **설정** | `collection_name`, `disclosure_collection_name` 제거됨 |

요약: **벡터는 모두 "도메인 테이블 + embedding 컬럼" 한 종류로만 저장·검색**하며, LangChain 전용 컬렉션/테이블 계층은 제거된 상태다.
