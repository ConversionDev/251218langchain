"""
Competency anchors 파이프라인: raw(xlsx+pdf) → prepared JSONL → 검증 → FAISS+Neon 적재.

한 번 실행 시:
  1. raw → prepared/competency_rows.jsonl (2000건 제한)
  2. 검증
  3. 임베딩 생성 → FAISS 인덱스+id_map 저장 → Neon에는 텍스트만 save_batch_upsert (embedding 없음)

사용:
  cd app && python -m training.pipelines.ingest.run_competency_ingest
"""

import json
import sys
from pathlib import Path

import numpy as np  # type: ignore

# app 루트를 경로에 추가
app_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

from core.database import SessionLocal  # type: ignore
from core.faiss_store import build_and_save_index  # type: ignore
from domain.hub.repositories.competency_anchor_repository import (  # type: ignore
    _build_embedding_content,
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
    embeddings_model = get_embedding_model(use_fp16=True)
    texts = [_build_embedding_content(r) for r in rows]
    vectors = embeddings_model.embed_documents(texts)
    if len(vectors) != len(rows):
        print(f"[ERROR] 임베딩 개수 불일치: {len(vectors)} vs {len(rows)}")
        sys.exit(1)
    arr = np.array(vectors, dtype=np.float32)
    unique_ids = [str(r.get("unique_id", "")) for r in rows]
    build_and_save_index(arr, unique_ids, "competency_anchors")
    print("[INFO] FAISS 인덱스·id_map 저장 완료")
    db = SessionLocal()
    try:
        inserted = save_batch_upsert(db, rows)
        print(f"[OK] Neon 텍스트 적재 완료: {inserted}건")
    finally:
        db.close()


if __name__ == "__main__":
    main()
