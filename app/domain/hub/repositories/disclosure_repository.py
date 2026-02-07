"""
공시(Disclosure) 저장·조회 — disclosures 단일 테이블.

- save_batch: sources_to_replace 지정 시 해당 source 기존 행 삭제 후 INSERT (재적재).
- embedding_content = [Standard] [Section]: Content 형태로 저장.
"""

from typing import Any, List, Optional

from langchain_core.documents import Document
from sqlalchemy.orm import Session  # type: ignore[import-untyped]

from domain.models.bases.disclosure import Disclosure  # type: ignore


def _build_embedding_content(doc: Document) -> str:
    """[Standard Name] [Section Title]: [Content] 형태. section_title 길이 제한 200자."""
    meta = doc.metadata or {}
    standard_type = meta.get("standard_type") or ""
    section_title = (meta.get("section_title") or "")[:200]
    return f"{standard_type} {section_title}: {doc.page_content}".strip()


def delete_by_sources(db: Session, sources: List[str]) -> int:
    """지정한 source(파일 식별자)에 해당하는 행 삭제. 재적재 전 정리용."""
    if not sources:
        return 0
    deleted = db.query(Disclosure).filter(Disclosure.source.in_(sources)).delete()
    return deleted  # type: ignore


def save_batch(
    db: Session,
    documents: List[Document],
    embeddings_model: Any,
    sources_to_replace: Optional[List[str]] = None,
) -> int:
    """
    Document 리스트를 disclosures에 저장하고 embedding 채움.
    sources_to_replace가 있으면 해당 source 기존 행 삭제 후 INSERT(재적재).
    """
    if not documents:
        return 0
    if sources_to_replace:
        delete_by_sources(db, sources_to_replace)
        db.flush()
    for doc in documents:
        meta = doc.metadata or {}
        embedding_text = _build_embedding_content(doc)
        metadata_json = {
            "page": meta.get("page"),
            "source": meta.get("source"),
            "section_title": meta.get("section_title"),
        }
        row = Disclosure(
            content=doc.page_content,
            embedding_content=embedding_text,
            source=meta.get("source"),
            page=meta.get("page"),
            standard_type=meta.get("standard_type"),
            section_title=meta.get("section_title"),
            metadata_=metadata_json,
            unique_id=meta.get("unique_id"),
        )
        db.add(row)
    db.flush()
    filled = fill_embeddings_for_disclosures(db, embeddings_model)
    db.commit()
    return filled


def fill_embeddings_for_disclosures(db: Session, embeddings_model: Any, batch_size: int = 32) -> int:
    """embedding이 null인 행만 읽어 임베딩 계산 후 업데이트."""
    rows = db.query(Disclosure).filter(Disclosure.embedding.is_(None)).all()
    if not rows:
        return 0
    texts = [r.embedding_content or r.content for r in rows]
    processed = 0
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i : i + batch_size]
        batch_rows = rows[i : i + batch_size]
        try:
            vectors = embeddings_model.embed_documents(batch_texts)
        except Exception:
            if hasattr(embeddings_model, "embed_query"):
                vectors = [embeddings_model.embed_query(t) for t in batch_texts]
            else:
                continue
        for row, vec in zip(batch_rows, vectors):
            if vec is not None:
                row.embedding = vec
                processed += 1
    return processed


def get_disclosure_doc_count(db: Session) -> int:
    """embedding이 채워진 공시 문서(청크) 개수."""
    return db.query(Disclosure).filter(Disclosure.embedding.isnot(None)).count()


def search_disclosures(db: Session, query_embedding: List[float], k: int = 5) -> List[str]:
    """벡터 유사도로 공시 청크 검색. content 문자열 리스트 반환."""
    from sqlalchemy import text as sql_text  # type: ignore[import-untyped]
    # pgvector: 파라미터는 리스트로 전달 (드라이버가 vector로 변환)
    vec_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
    r = db.execute(
        sql_text(
            "SELECT content FROM disclosures "
            "WHERE embedding IS NOT NULL ORDER BY embedding <-> CAST(:vec AS vector) LIMIT :k"
        ),
        {"vec": vec_str, "k": k},
    )
    return [row[0] for row in r]
