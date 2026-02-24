"""
성과 활동(performance_records) 저장·조회 — 통합 테이블 CRUD.

회의록·보고서·이메일을 한 테이블에서 분기별로 조회.
직원 제출(submit)은 id 자동 생성.
"""

import uuid
from typing import Any, Dict, List, Optional, Tuple

from langchain_core.documents import Document
from sqlalchemy import text as sql_text
from sqlalchemy.orm import Session  # type: ignore[import-untyped]

from domain.models.bases.performance_record import PerformanceRecord  # type: ignore


def _row_to_dict(row: PerformanceRecord) -> Dict[str, Any]:
    """ORM 행 → API용 dict (camelCase)."""
    return {
        "id": row.id,
        "employeeId": row.employee_id,
        "period": row.period,
        "textType": row.text_type,
        "content": row.content,
        "tags": row.tags or [],
        "grade": row.grade,
        "createdAt": row.created_at.isoformat() if row.created_at else None,
    }


def create(db: Session, data: Dict[str, Any]) -> Dict[str, Any]:
    """한 건 삽입. data: id, employeeId, period, textType, content, tags?, grade?."""
    record_id = data.get("id")
    if not record_id:
        raise ValueError("id required")
    existing = db.get(PerformanceRecord, record_id)
    if existing:
        raise ValueError(f"performance record already exists: {record_id}")

    row = PerformanceRecord(
        id=record_id,
        employee_id=data.get("employeeId") or data.get("employee_id", ""),
        period=data.get("period", ""),
        text_type=data.get("textType") or data.get("text_type", ""),
        content=data.get("content") or data.get("text", ""),
        tags=data.get("tags"),
        grade=data.get("grade"),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _row_to_dict(row)


def create_submission(
    db: Session,
    employee_id: str,
    text_type: str,
    content: str,
    period: str,
    tags: List[str] | None = None,
) -> Dict[str, Any]:
    """직원 제출 1건 (id 자동 생성). grade는 미설정(나중에 AI 분석)."""
    raw = (content or "").strip()
    if not raw:
        raise ValueError("content required")
    if text_type not in ("meeting", "report", "email"):
        raise ValueError("textType must be meeting, report, or email")
    record_id = f"SUB-{uuid.uuid4().hex[:14]}"
    row = PerformanceRecord(
        id=record_id,
        employee_id=employee_id,
        period=period,
        text_type=text_type,
        content=raw,
        tags=tags or [],
        grade=None,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _row_to_dict(row)


def list_by_employee(db: Session, employee_id: str, period: str | None = None, limit: int = 100) -> List[Dict[str, Any]]:
    """직원별 성과 기록 목록 (period 선택)."""
    q = db.query(PerformanceRecord).filter(PerformanceRecord.employee_id == employee_id)
    if period:
        q = q.filter(PerformanceRecord.period == period)
    rows = q.order_by(PerformanceRecord.period.desc(), PerformanceRecord.id).limit(limit).all()
    return [_row_to_dict(r) for r in rows]


def get_performance_record_count(db: Session) -> int:
    """전체 성과 기록 건수 (채팅 요약용)."""
    from sqlalchemy import func
    r = db.query(func.count(PerformanceRecord.id)).scalar()
    return int(r) if r is not None else 0


def list_all(db: Session, period: str | None = None, grade: str | None = None, limit: int = 5000) -> List[Dict[str, Any]]:
    """전체 목록 (period/grade 필터)."""
    q = db.query(PerformanceRecord)
    if period:
        q = q.filter(PerformanceRecord.period == period)
    if grade:
        q = q.filter(PerformanceRecord.grade == grade)
    rows = q.order_by(PerformanceRecord.period, PerformanceRecord.employee_id).limit(limit).all()
    return [_row_to_dict(r) for r in rows]


def bulk_insert(db: Session, rows: List[Dict[str, Any]], skip_existing: bool = True) -> tuple[int, int]:
    """JSONL 행들을 bulk insert. 반환: (성공 수, 스킵 수)."""
    ids_in_file = [r.get("id") for r in rows if r.get("id")]
    existing_ids: set = set()
    if skip_existing and ids_in_file:
        existing = db.query(PerformanceRecord.id).filter(PerformanceRecord.id.in_(ids_in_file)).all()
        existing_ids = {x[0] for x in existing}
    to_add = []
    for r in rows:
        record_id = r.get("id")
        if not record_id:
            continue
        if record_id in existing_ids:
            continue
        content = (r.get("content") or r.get("text") or "").strip()
        to_add.append(
            PerformanceRecord(
                id=record_id,
                employee_id=r.get("employeeId") or r.get("employee_id", ""),
                period=r.get("period", ""),
                text_type=r.get("textType") or r.get("text_type", ""),
                content=content,
                tags=r.get("tags"),
                grade=r.get("grade"),
            )
        )
    for row in to_add:
        db.add(row)
    db.commit()
    return len(to_add), len(existing_ids)


def _build_perf_embedding_content(row: PerformanceRecord) -> str:
    """레코드 → 임베딩용 텍스트."""
    parts = []
    if row.employee_id:
        parts.append(f"직원ID: {row.employee_id}")
    if row.period:
        parts.append(f"기간: {row.period}")
    if row.text_type:
        label = {"meeting": "회의록", "report": "보고서", "email": "이메일"}.get(row.text_type, row.text_type)
        parts.append(f"유형: {label}")
    if row.grade:
        parts.append(f"등급: {row.grade}")
    content = (row.content or "")[:1500]
    if content:
        parts.append(content)
    return " | ".join(parts)


def _ensure_embedding_schema(db: Session) -> None:
    """embedding_content, embedding 컬럼이 없으면 추가하고 HNSW 인덱스 생성. 있으면 skip."""
    import logging
    _logger = logging.getLogger(__name__)
    bind = db.get_bind()
    engine = bind if hasattr(bind, "connect") else bind.engine  # type: ignore[union-attr]
    conn = engine.connect()
    try:
        cols = conn.execute(
            sql_text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'performance_records' AND column_name IN ('embedding_content', 'embedding')"
            )
        ).fetchall()
        existing = {row[0] for row in cols}

        if "embedding_content" not in existing:
            conn.execute(sql_text("ALTER TABLE performance_records ADD COLUMN embedding_content TEXT"))
            _logger.info("[perf-schema] 컬럼 추가: embedding_content")
        if "embedding" not in existing:
            conn.execute(sql_text("ALTER TABLE performance_records ADD COLUMN embedding vector(1024)"))
            _logger.info("[perf-schema] 컬럼 추가: embedding (vector 1024)")

        idx = conn.execute(
            sql_text("SELECT 1 FROM pg_indexes WHERE indexname = 'idx_performance_records_embedding_hnsw'")
        ).fetchone()
        if not idx:
            conn.execute(sql_text(
                "CREATE INDEX idx_performance_records_embedding_hnsw "
                "ON performance_records USING hnsw (embedding vector_cosine_ops)"
            ))
            _logger.info("[perf-schema] HNSW 인덱스 생성")

        conn.commit()
    finally:
        conn.close()


def fill_embeddings_for_performance_records(
    db: Session,
    embeddings_model: Any,
    include_existing: bool = False,
    batch_size: int = 32,
) -> int:
    """embedding 컬럼/인덱스 확인 후, NULL(또는 include_existing=True면 전체) 레코드에 임베딩 일괄 생성."""
    import logging
    _logger = logging.getLogger(__name__)

    _ensure_embedding_schema(db)

    q = db.query(PerformanceRecord)
    if not include_existing:
        q = q.filter(PerformanceRecord.embedding.is_(None))
    total = q.count()
    if total == 0:
        return 0
    _logger.info("[perf-embed] 대상 %d건", total)
    updated = 0
    while True:
        bq = db.query(PerformanceRecord).order_by(PerformanceRecord.id)
        if not include_existing:
            bq = bq.filter(PerformanceRecord.embedding.is_(None))
        else:
            bq = bq.offset(updated)
        rows = bq.limit(batch_size).all()
        if not rows:
            break
        texts = []
        for r in rows:
            ec = _build_perf_embedding_content(r)
            r.embedding_content = ec
            texts.append(ec)
        try:
            if hasattr(embeddings_model, "embed_documents"):
                vectors = embeddings_model.embed_documents(texts)
            else:
                vectors = [embeddings_model.embed_query(t) for t in texts]
        except Exception:
            if hasattr(embeddings_model, "embed_query"):
                vectors = [embeddings_model.embed_query(t) for t in texts]
            else:
                vectors = [None] * len(texts)
        for r, vec in zip(rows, vectors):
            if vec is not None:
                r.embedding = vec
        db.commit()
        updated += len(rows)
        _logger.info("[perf-embed] 진행: %d / %d", updated, total)
    return updated


def search_performance_records_hybrid(
    db: Session,
    query_embedding: List[float],
    query_text: str,
    k: int = 10,
    employee_id: Optional[str] = None,
    period: Optional[str] = None,
    text_type: Optional[str] = None,
    vector_weight: float = 0.7,
    bm25_weight: float = 0.3,
) -> List[Tuple[Document, float]]:
    """벡터 + BM25 하이브리드 검색. 결합 점수(낮을수록 유사) 반환."""
    vec_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
    tokens = query_text.strip().split()
    ts_query = " | ".join(tokens) if tokens else query_text.strip()

    where_parts = ["embedding IS NOT NULL"]
    params: Dict[str, Any] = {"vec": vec_str, "k": k, "tsq": ts_query}
    if employee_id:
        where_parts.append("employee_id = :eid")
        params["eid"] = employee_id
    if period:
        where_parts.append("period = :period")
        params["period"] = period
    if text_type:
        where_parts.append("text_type = :tt")
        params["tt"] = text_type
    where_clause = " AND ".join(where_parts)

    sql = (
        f"SELECT id, employee_id, period, text_type, grade, embedding_content, "
        f"(embedding <-> CAST(:vec AS vector)) AS vec_dist, "
        f"ts_rank_cd(tsv, to_tsquery('simple', :tsq), 1) AS bm25_rank "
        f"FROM performance_records WHERE {where_clause} "
        f"ORDER BY ("
        f"  {vector_weight} * (embedding <-> CAST(:vec AS vector)) + "
        f"  {bm25_weight} * (1.0 - ts_rank_cd(tsv, to_tsquery('simple', :tsq), 1))"
        f") LIMIT :k"
    )
    r = db.execute(sql_text(sql), params)
    result: List[Tuple[Document, float]] = []
    for row in r:
        rid, eid, period_val, tt, grade_val, content, vec_dist, bm25_rank = row
        combined = vector_weight * float(vec_dist) + bm25_weight * (1.0 - float(bm25_rank))
        doc = Document(
            page_content=content or "",
            metadata={
                "table": "performance_records",
                "id": rid,
                "employee_id": eid or "",
                "period": period_val or "",
                "text_type": tt or "",
                "grade": grade_val or "",
            },
        )
        result.append((doc, combined))
    return result


def search_performance_records_with_filter(
    db: Session,
    query_embedding: List[float],
    k: int = 5,
    employee_id: Optional[str] = None,
    period: Optional[str] = None,
    text_type: Optional[str] = None,
) -> List[Tuple[Document, float]]:
    """
    performance_records 테이블에서 벡터 유사도 검색. pgvector HNSW 사용.
    반환: (Document, distance) 리스트. 코사인 거리(작을수록 유사).
    """
    vec_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
    where_parts = ["embedding IS NOT NULL"]
    params: Dict[str, Any] = {"vec": vec_str, "k": k}
    if employee_id:
        where_parts.append("employee_id = :eid")
        params["eid"] = employee_id
    if period:
        where_parts.append("period = :period")
        params["period"] = period
    if text_type:
        where_parts.append("text_type = :tt")
        params["tt"] = text_type
    where_clause = " AND ".join(where_parts)
    sql = (
        f"SELECT id, employee_id, period, text_type, grade, embedding_content, "
        f"(embedding <-> CAST(:vec AS vector)) AS distance "
        f"FROM performance_records WHERE {where_clause} "
        f"ORDER BY embedding <-> CAST(:vec AS vector) LIMIT :k"
    )
    r = db.execute(sql_text(sql), params)
    result = []
    for row in r:
        rid, eid, period_val, tt, grade_val, content, distance = row
        doc = Document(
            page_content=content or "",
            metadata={
                "table": "performance_records",
                "id": rid,
                "employee_id": eid or "",
                "period": period_val or "",
                "text_type": tt or "",
                "grade": grade_val or "",
            },
        )
        result.append((doc, float(distance)))
    return result
