"""
Competency anchors 파이프라인: raw(xlsx+pdf) → prepared JSONL → 검증 → competency_anchors 적재.

한 번 실행 시:
  1. raw/*.xlsx, *.pdf → prepared/competency_rows.jsonl (전략 분기, 2000건 제한)
  2. 검증: 행 수·필수 필드
  3. JSONL → save_batch_upsert → fill_embeddings_for_anchors

사용:
  cd app && python -m training.pipelines.ingest.run_competency_ingest
"""

import json
import sys
from pathlib import Path

# app 루트를 경로에 추가
app_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

from core.database import SessionLocal  # type: ignore
from domain.hub.repositories.competency_anchor_repository import (  # type: ignore
    fill_embeddings_for_anchors,
    save_batch_upsert,
)
from domain.shared.embedding import get_embedding_model  # type: ignore
from training.shared.competency_extract import (  # type: ignore
    extract_raw_to_prepared,
    get_competency_prepared_dir,
    get_competency_raw_dir,
)
from training.shared.competency_verify import verify_competency_prepared  # type: ignore


def main() -> None:
    raw_dir = get_competency_raw_dir()
    prepared_dir = get_competency_prepared_dir()

    # 1. raw → prepared (2000건 제한)
    if raw_dir.exists():
        xlsx = list(raw_dir.glob("*.xlsx"))
        pdfs = list(raw_dir.glob("*.pdf"))
        if xlsx or pdfs:
            print(f"[INFO] raw (xlsx {len(xlsx)}, pdf {len(pdfs)}) → prepared JSONL 변환 중 (최대 2000건)...")
            try:
                extracted = extract_raw_to_prepared(raw_dir, prepared_dir, limit=2000)
                print(f"[INFO] 추출 완료: {len(extracted)}건")
            except RuntimeError as e:
                print(f"[ERROR] {e}")
                sys.exit(1)
    else:
        print(f"[INFO] raw 디렉터리 없음: {raw_dir}")

    # 2. 검증
    ok, err = verify_competency_prepared(prepared_dir)
    if not ok:
        print(f"[ERROR] 검증 실패: {err}")
        sys.exit(1)
    print("[INFO] 검증 통과")

    # 3. prepared JSONL → DB 적재
    path = prepared_dir / "competency_rows.jsonl"
    if not path.exists():
        print(f"[WARNING] prepared 파일 없음: {path}")
        sys.exit(0)

    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))

    if not rows:
        print("[WARNING] 적재할 행이 없습니다.")
        sys.exit(0)

    print(f"[INFO] 적재 입력: {len(rows)}건")
    db = SessionLocal()
    try:
        inserted = save_batch_upsert(db, rows)
        print(f"[INFO] Upsert 완료: {inserted}건")
        embeddings_model = get_embedding_model(use_fp16=True)
        filled = fill_embeddings_for_anchors(db, embeddings_model)
        print(f"[OK] 임베딩 채움: {filled}건")
    finally:
        db.close()


if __name__ == "__main__":
    main()
