"""
O*NET xlsx 4종 → competency_anchors 테이블 적재.

- INGEST_STRATEGY.md §2: embedding_content = [category] [section_title]: content, Batch 100~500.
- unique_id 생성: source_stem | task_id | element_id 등으로 Upsert 가능하도록.
실행 (app 디렉터리):
  python -m data.competency_anchors.xlsx_ingest          # 전체: 추출 → Upsert → embedding 채우기
  python -m data.competency_anchors.xlsx_ingest --fill-only  # embedding만: NULL인 행만 이어서 채우기
"""
import sys
from pathlib import Path
from typing import Any

from tqdm import tqdm

# app이 PYTHONPATH에 있도록
SCRIPT_DIR = Path(__file__).resolve().parent
APP_ROOT = SCRIPT_DIR.parent.parent
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

def _make_unique_id(row: dict[str, Any], source_stem: str, index: int) -> str:
    """Upsert용 unique_id. source_stem | task_id | element_id 또는 fallback."""
    meta = row.get("metadata") or {}
    task_id = meta.get("task_id")
    element_id = meta.get("element_id")
    onet_soc = meta.get("onet_soc_code") or ""
    if task_id is not None:
        return f"{source_stem}|{task_id}"
    if element_id:
        return f"{source_stem}|{onet_soc}|{element_id}"
    content = (row.get("content") or "")[:200]
    section = (row.get("section_title") or "")[:100]
    return f"{source_stem}|{index}|{abs(hash((content, section))) % 10**10}"


def _prepare_rows(rows: list[dict[str, Any]], source_stem: str) -> list[dict[str, Any]]:
    """embedding_content, unique_id 추가."""
    out = []
    for i, r in enumerate(rows):
        category = (r.get("category") or "").strip()
        section_title = (r.get("section_title") or "").strip()[:200]
        content = (r.get("content") or "").strip()
        embedding_content = f"[{category}] {section_title}: {content}".strip() or content
        unique_id = _make_unique_id(r, source_stem, i)
        out.append({
            **r,
            "embedding_content": embedding_content,
            "unique_id": unique_id,
        })
    return out


# INGEST_STRATEGY §2: INSERT 100~500. embedding 없이 먼저 적재하므로 500 사용
INSERT_BATCH_ROWS = 500


def run_ingest() -> int:
    """원래 전략: xlsx 추출 → embedding 없이 먼저 Upsert → fill_embeddings_for_anchors로 NULL 채우기 (시간 오래 걸림, 안정적)."""
    from domain.shared.strategies import ExcelStrategyFactory  # type: ignore
    from domain.hub.repositories.competency_anchor_repository import (
        save_batch_upsert,
        fill_embeddings_for_anchors,
    )  # type: ignore
    from core.database import SessionLocal  # type: ignore
    from domain.shared.embedding import get_embedding_model  # type: ignore

    xlsx_files = sorted(SCRIPT_DIR.glob("*.xlsx"))
    if not xlsx_files:
        raise FileNotFoundError(f"{SCRIPT_DIR}에 *.xlsx가 없습니다.")

    strategy = ExcelStrategyFactory.get_strategy(SCRIPT_DIR)
    all_rows: list[dict[str, Any]] = []
    for path in tqdm(xlsx_files, desc="Extract xlsx", unit="file"):
        rows = strategy.extract(path)
        source_stem = path.stem
        prepared = _prepare_rows(rows, source_stem)
        n = len(prepared)
        print(f"  {path.name}: 추출 {n}행")
        all_rows.extend(prepared)

    if not all_rows:
        print("[ingest] 추출된 행이 없습니다.")
        return 0
    print(f"[ingest] 파일별 합계: 총 {len(all_rows)}행")

    # 1) embedding 없이 먼저 Upsert (vector/JSONB 부담 없음)
    print(f"[ingest] 배치 {INSERT_BATCH_ROWS}씩 DB Upsert (embedding NULL) ...")
    db = SessionLocal()
    try:
        saved = save_batch_upsert(db, all_rows, batch_size=INSERT_BATCH_ROWS)
        print(f"[ingest] Upsert 완료: {saved}행.")
    finally:
        db.close()

    # 2) embedding NULL인 행만 chunk 단위로 가져와 임베딩 후 bulk_update (3시간대, 안정적)
    print("[ingest] FlagEmbedding BGE-m3 로드 중 ...")
    embeddings = get_embedding_model(use_fp16=True, batch_size=128)
    db2 = SessionLocal()
    try:
        filled = fill_embeddings_for_anchors(
            db2,
            embeddings,
            batch_size=128,
            fetch_chunk=2000,
        )
        print(f"[ingest] embedding 채우기 완료: {filled}행.")
        return filled
    finally:
        db2.close()


def run_fill_only() -> int:
    """embedding이 NULL인 행만 채움. 중단 후 재실행 시 사용."""
    from domain.hub.repositories.competency_anchor_repository import fill_embeddings_for_anchors  # type: ignore
    from core.database import SessionLocal  # type: ignore
    from domain.shared.embedding import get_embedding_model  # type: ignore

    print("[fill-only] FlagEmbedding BGE-m3 로드 중 ...")
    embeddings = get_embedding_model(use_fp16=True, batch_size=128)
    db = SessionLocal()
    try:
        n = fill_embeddings_for_anchors(db, embeddings, batch_size=128, fetch_chunk=2000)
        print(f"[fill-only] embedding 채우기 완료: {n}행.")
        return n
    finally:
        db.close()


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="competency_anchors xlsx 적재 또는 embedding만 채우기")
    parser.add_argument("--fill-only", action="store_true", help="추출/Upsert 생략, embedding NULL인 행만 채우기")
    args = parser.parse_args()

    try:
        if args.fill_only:
            n = run_fill_only()
        else:
            n = run_ingest()
        print(f"정상 종료. embedding 채워진 행 수: {n}")
    except Exception as e:
        print(f"오류: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
