"""
Soccer 임베딩 서비스 (단일 테이블 가이드).

베이스 테이블(players, teams, schedules, stadiums)의 embedding, embedding_content 컬럼에
BGE-m3 임베딩을 채움. 업로드 직후 또는 수동 동기화 시 호출.
"""

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session  # type: ignore[import-untyped]

from domain.models.bases.soccer import Player, Schedule, Stadium, Team  # type: ignore

logger = logging.getLogger(__name__)

SYNC_ENTITY_TYPES = ["players", "teams", "schedules", "stadiums"]

# (BaseModel, entity_type for to_embedding_text)
_ENTITY_MAP = {
    "players": (Player, "player"),
    "teams": (Team, "team"),
    "schedules": (Schedule, "schedule"),
    "stadiums": (Stadium, "stadium"),
}

_ENTITY_LABELS = {"player": "선수", "team": "팀", "schedule": "경기 일정", "stadium": "경기장"}

EXAONE_CONTENT_MAX_WORKERS = 8


def _record_to_dict(row: Any) -> dict:
    if hasattr(row, "to_dict"):
        return row.to_dict()
    return {c.key: getattr(row, c.key) for c in row.__table__.columns}


def _get_to_embedding_text():
    try:
        from domain.models.bases.soccer_embeddings import to_embedding_text  # type: ignore
        return to_embedding_text
    except Exception:
        from domain.hub.shared.data_loader import (  # type: ignore
            player_to_text,
            schedule_to_text,
            stadium_to_text,
            team_to_text,
        )
        _text_fns = {"player": player_to_text, "team": team_to_text, "schedule": schedule_to_text, "stadium": stadium_to_text}

        def _fallback(record: Dict[str, Any], entity_type: str) -> str:
            fn = _text_fns.get(entity_type)
            if fn is None:
                raise ValueError(f"지원하지 않는 entity_type: {entity_type!r}")
            return fn(record)
        return _fallback


def _to_embedding_text_exaone(record: Dict[str, Any], entity_type: str) -> Optional[str]:
    label = _ENTITY_LABELS.get(entity_type, entity_type)
    prompt = (
        f"다음 {label} 데이터를 RAG와 벡터 검색에 쓸 한 줄 한국어 문장으로 요약해줘. "
        "다른 설명 없이 해당 문장만 출력해줘.\n"
        f"데이터: {json.dumps(record, ensure_ascii=False)}"
    )
    try:
        from domain.hub.llm import generate_text  # type: ignore
        out = generate_text(prompt, max_tokens=256, temperature=0.3)
        out = (out or "").strip()
        if not out or out.startswith("[ExaOne"):
            return None
        return out
    except Exception as e:
        logger.warning("[embedding] ExaOne content 생성 실패: %s", e)
        return None


def fill_embeddings_for_entity(
    db: Session,
    embeddings_model: Any,
    table_key: str,
    batch_size: int = 32,
) -> Dict[str, Any]:
    """
    베이스 테이블에서 embedding이 null인 행만 읽어서
    content 생성 → 임베딩 계산 → 같은 행의 embedding, embedding_content 업데이트.
    """
    if table_key not in _ENTITY_MAP:
        return {"processed": 0, "failed": 0, "error": f"알 수 없는 엔티티: {table_key}"}
    to_embedding_text = _get_to_embedding_text()
    BaseModel, entity_type = _ENTITY_MAP[table_key]
    try:
        # embedding 이 null 인 행만
        rows = db.query(BaseModel).filter(BaseModel.embedding.is_(None)).all()
        if not rows:
            return {"processed": 0, "failed": 0}
        row_data = [(_record_to_dict(row), entity_type, row) for row in rows]

        def _content_for_row(rec: Dict[str, Any], entity_type: str) -> tuple:
            content = _to_embedding_text_exaone(rec, entity_type)
            if not content:
                content = to_embedding_text(rec, entity_type)
            return (content,)

        texts = []
        row_refs = []
        with ThreadPoolExecutor(max_workers=EXAONE_CONTENT_MAX_WORKERS) as executor:
            future_to_idx = {}
            for i, (rec, et, row) in enumerate(row_data):
                future_to_idx[executor.submit(_content_for_row, rec, et)] = (i, row)
            results: List[Optional[tuple]] = [None] * len(row_data)
            for future in as_completed(future_to_idx):
                idx, row = future_to_idx[future]
                try:
                    results[idx] = future.result()
                except Exception as e:
                    rec, et, _ = row_data[idx]
                    logger.warning("[embedding] ExaOne/폴백 실패 idx=%s: %s", idx, e)
                    results[idx] = (to_embedding_text(rec, et),)
            for i, r in enumerate(results):
                if r:
                    content = r[0]
                    row = row_data[i][2]
                    row_refs.append((row, content))
                    texts.append(content)
        processed = 0
        failed = 0
        first_row_error: Optional[str] = None
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            batch_refs = row_refs[i : i + batch_size]
            try:
                vectors = embeddings_model.embed_documents(batch_texts)
            except Exception as e:
                logger.warning("[embedding] embed_documents 실패: %s", e)
                if hasattr(embeddings_model, "embed_query"):
                    vectors = [embeddings_model.embed_query(t) for t in batch_texts]
                else:
                    failed += len(batch_texts)
                    continue
            n = min(len(batch_refs), len(vectors))
            if n < len(batch_refs):
                failed += len(batch_refs) - n
            for (row, content), vec in zip(batch_refs[:n], vectors[:n]):
                if vec is None:
                    failed += 1
                    continue
                try:
                    row.embedding_content = content
                    row.embedding = vec
                    db.merge(row)
                    processed += 1
                except Exception as e:
                    if first_row_error is None:
                        first_row_error = str(e)
                    logger.warning("[embedding] row 저장 실패 id=%s: %s", getattr(row, "id", None), e)
                    failed += 1
        db.commit()
        out: Dict[str, Any] = {"processed": processed, "failed": failed}
        if first_row_error:
            out["error"] = first_row_error
        return out
    except Exception as e:
        db.rollback()
        logger.exception("[embedding] %s 처리 중 오류: %s", table_key, e)
        return {"processed": 0, "failed": 0, "error": str(e)}


def run_embedding_sync_single_entity(
    db: Session,
    embeddings_model: Any,
    table_key: str,
    batch_size: int = 32,
) -> Dict[str, Any]:
    """
    단일 엔티티에 대해 베이스 테이블의 embedding null 행을 채움.
    (기존 run_embedding_sync_single_entity와 동일 시그니처, 내부만 단일 테이블로 변경.)
    """
    return fill_embeddings_for_entity(db, embeddings_model, table_key, batch_size=batch_size)
