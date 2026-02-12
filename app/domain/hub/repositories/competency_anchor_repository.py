"""
역량 anchor 저장·조회 — competency_anchors 단일 테이블.

- save_batch_upsert: ON CONFLICT (unique_id) DO UPDATE (INGEST_STRATEGY.md §1).
- category/level Optional 필터로 검색.
"""

import json
from typing import Any, List, Optional, Tuple

from langchain_core.documents import Document
from tqdm import tqdm
from sqlalchemy import func, text as sql_text  # type: ignore[import-untyped]
from sqlalchemy.orm import Session  # type: ignore[import-untyped]
from sqlalchemy.dialects.postgresql import insert as pg_insert  # type: ignore[import-untyped]

from domain.models.bases.competency_anchor import CompetencyAnchor  # type: ignore

# 배치: INSERT 100~500 권장 (전략 §2)
DEFAULT_INSERT_BATCH = 200
# 4060 Ti 16GB: inference 128로 GPU 풀가동, 11만 건 연산 시간 단축 (32→128)
FILL_EMBEDDINGS_BATCH = 128
# commit 1024건마다: SSL/타임아웃 원천 차단, commit 횟수 ~110회
COMMIT_EVERY_EMBEDDING_ROWS = 1024
# NULL 채울 때 한 번에 가져오는 행 수. 세션 부담·속도 저하 방지 (Gemini 제안 반영)
FETCH_CHUNK_EMBEDDING = 2000


def _build_embedding_content(row: dict[str, Any]) -> str:
    """[category] [section_title]: content 형태. INGEST_STRATEGY.md §2."""
    category = (row.get("category") or "").strip()
    section_title = (row.get("section_title") or "").strip()[:200]
    content = (row.get("content") or "").strip()
    return f"[{category}] {section_title}: {content}".strip() or content


def _normalize_embedding(val: Any) -> Optional[List[float]]:
    """DB vector 컬럼용: list[float] 또는 None으로 통일. 문자열/ndarray 등 변환."""
    if val is None:
        return None
    if hasattr(val, "tolist"):
        return getattr(val, "tolist")()
    if isinstance(val, list):
        try:
            return [float(x) for x in val]
        except (TypeError, ValueError):
            return None
    if isinstance(val, str):
        try:
            parsed = json.loads(val)
            return _normalize_embedding(parsed)
        except (json.JSONDecodeError, TypeError):
            return None
    return None


def _normalize_metadata(val: Any) -> dict:
    """JSONB 컬럼용: 항상 dict. 문자열이면 json.loads."""
    if val is None:
        return {}
    if isinstance(val, dict):
        return val
    if isinstance(val, str):
        try:
            return json.loads(val) if val.strip() else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}


def save_batch_upsert(
    db: Session,
    rows: List[dict[str, Any]],
    batch_size: int = DEFAULT_INSERT_BATCH,
) -> int:
    """
    통합 스키마 dict 리스트를 competency_anchors에 Upsert.
    ON CONFLICT (unique_id) DO UPDATE. unique_id가 None인 행은 INSERT만.
    """
    if not rows:
        return 0
    table = CompetencyAnchor.__table__
    # "metadata" 컬럼은 table.c에서 예약어 충돌 방지로 키로 접근
    meta_col = table.c["metadata"]
    inserted = 0
    batch_range = range(0, len(rows), batch_size)
    for i in tqdm(batch_range, desc="Upsert (competency_anchors)", unit="batch", total=len(batch_range)):
        batch = rows[i : i + batch_size]
        values = []
        for r in batch:
            embedding_content = r.get("embedding_content") or _build_embedding_content(r)
            values.append({
                "content": (r.get("content") or "").strip() or "(no text)",
                "embedding_content": embedding_content,
                "category": r.get("category"),
                "level": r.get("level"),
                "section_title": r.get("section_title") or "",
                "source": r.get("source"),
                "source_type": r.get("source_type"),
                "metadata": _normalize_metadata(r.get("metadata")),
                "unique_id": r.get("unique_id"),
                "embedding": _normalize_embedding(r.get("embedding")),
            })
        stmt = pg_insert(table).values(values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["unique_id"],
            index_where=table.c.unique_id.isnot(None),
            set_={
                table.c.content: stmt.excluded.content,
                table.c.embedding_content: stmt.excluded.embedding_content,
                table.c.category: stmt.excluded.category,
                table.c.level: stmt.excluded.level,
                table.c.section_title: stmt.excluded.section_title,
                table.c.source: stmt.excluded.source,
                table.c.source_type: stmt.excluded.source_type,
                meta_col: stmt.excluded["metadata"],
                # NULL로 덮어쓰지 않음: 재적재 시 이미 채운 embedding 유지
                table.c.embedding: func.coalesce(stmt.excluded.embedding, table.c.embedding),
            },
        )
        db.execute(stmt)
        inserted += len(batch)
    db.flush()
    db.commit()
    return inserted


def fill_embeddings_for_anchors(
    db: Session,
    embeddings_model: Any,
    batch_size: int = FILL_EMBEDDINGS_BATCH,
    fetch_chunk: int = FETCH_CHUNK_EMBEDDING,
) -> int:
    """embedding이 null인 행만 chunk 단위로 가져와 임베딩 후 bulk_update.
    세션에 11만 건 쌓이지 않게 fetch_chunk(2000)씩만 유지 → 속도·안정성 (9 doc/s 급락 방지)."""
    processed = 0
    pbar = tqdm(desc="Embedding (competency_anchors)", unit="doc", unit_scale=False)
    while True:
        rows = (
            db.query(CompetencyAnchor)
            .filter(CompetencyAnchor.embedding.is_(None))
            .limit(fetch_chunk)
            .all()
        )
        if not rows:
            break
        texts = [r.embedding_content or r.content for r in rows]
        all_vectors: List[Optional[List[float]]] = []
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            try:
                vectors = embeddings_model.embed_documents(batch_texts)
            except Exception:
                if hasattr(embeddings_model, "embed_query"):
                    vectors = [embeddings_model.embed_query(t) for t in batch_texts]
                else:
                    all_vectors.extend([None] * len(batch_texts))
                    continue
            for v in vectors if isinstance(vectors, list) else []:
                all_vectors.append(list(v) if v is not None else None)
        if len(all_vectors) < len(rows):
            all_vectors.extend([None] * (len(rows) - len(all_vectors)))
        update_mappings = [
            {"id": r.id, "embedding": vec}
            for r, vec in zip(rows, all_vectors)
            if vec is not None
        ]
        if update_mappings:
            db.bulk_update_mappings(CompetencyAnchor, update_mappings)
        db.commit()
        db.expunge_all()
        processed += len(rows)
        pbar.update(len(rows))
    pbar.close()
    return processed


def search_competency_anchors_with_filter(
    db: Session,
    query_embedding: List[float],
    k: int = 5,
    category: Optional[str] = None,
    level: Optional[int] = None,
) -> List[Tuple[Document, float]]:
    """
    competency_anchors에서 벡터 유사도 검색.
    category/level이 None이면 해당 조건 없음(전체 검색). 있으면 btree 인덱스 활용.
    반환: (Document, distance) 리스트. 코사인 거리(작을수록 유사).
    """
    vec_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
    conditions = ["embedding IS NOT NULL"]
    params: Any = {"vec": vec_str, "k": k}
    if category is not None:
        conditions.append("category = :category")
        params["category"] = category
    if level is not None:
        conditions.append("level = :level")
        params["level"] = level
    where = " AND ".join(conditions)
    sql = (
        f"SELECT id, content, category, level, section_title, source, source_type, unique_id, "
        f"(embedding <-> CAST(:vec AS vector)) AS distance "
        f"FROM competency_anchors WHERE {where} "
        f"ORDER BY embedding <-> CAST(:vec AS vector) LIMIT :k"
    )
    r = db.execute(sql_text(sql), params)
    result: List[Tuple[Document, float]] = []
    for row in r:
        (doc_id, content, cat, lv, section_title, source, source_type, unique_id, distance) = row
        doc = Document(
            page_content=content or "",
            metadata={
                "id": doc_id,
                "category": cat or "",
                "level": lv,
                "section_title": section_title or "",
                "source": source or "",
                "source_type": source_type or "",
                "unique_id": unique_id or "",
            },
        )
        result.append((doc, float(distance)))
    return result


def get_anchor_doc_count(db: Session) -> int:
    """embedding이 채워진 anchor 개수."""
    return db.query(CompetencyAnchor).filter(CompetencyAnchor.embedding.isnot(None)).count()
