"""
사내 주소록 샘플 JSONL → internal_addresses 테이블 적재.

실행 (app 디렉터리):
  python -m training.pipelines.address_book.run_import_internal_addresses
  python -m training.pipelines.address_book.run_import_internal_addresses --file data/address_book/samples/internal_addresses.jsonl
"""

import argparse
import json
import sys
from pathlib import Path

app_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

from core.database import SessionLocal  # type: ignore
from infrastructure.persistence.repositories.internal_address_repository import upsert_from_dict  # type: ignore

_REQUIRED_KEYS = {"id", "type", "display_name", "email"}


def load_jsonl(path: Path) -> tuple[list[dict], list[str]]:
    """JSONL 로드 및 필수 키 검증. 반환: (행 리스트, 에러 메시지)."""
    errors = []
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if not isinstance(obj, dict):
                    errors.append(f"줄 {i}: 객체가 아님")
                    continue
                missing = _REQUIRED_KEYS - set(obj.keys())
                if missing:
                    errors.append(f"줄 {i} (id={obj.get('id')}): 필수 키 누락 {missing}")
                    continue
                rows.append(obj)
            except json.JSONDecodeError as e:
                errors.append(f"줄 {i}: JSON 파싱 실패 - {e}")
    return rows, errors


def main() -> None:
    parser = argparse.ArgumentParser(description="사내 주소록 JSONL → internal_addresses 적재")
    parser.add_argument("--file", type=Path, default=None, help="JSONL 경로 (미지정 시 data/address_book/samples/internal_addresses.jsonl)")
    args = parser.parse_args()

    if args.file is not None:
        path = Path(args.file)
    else:
        path = app_dir / "data" / "address_book" / "samples" / "internal_addresses.jsonl"
        print(f"[INFO] 기본 파일 사용: {path}")

    if not path.is_absolute():
        path = app_dir / path
    if not path.exists():
        print(f"[ERROR] 파일 없음: {path}", file=sys.stderr)
        sys.exit(1)

    rows, errors = load_jsonl(path)
    if errors:
        for e in errors[:15]:
            print(f"[WARN] {e}")
        if len(errors) > 15:
            print(f"[WARN] ... 외 {len(errors) - 15}건")
    if not rows:
        print("[ERROR] 유효한 행이 없습니다.", file=sys.stderr)
        sys.exit(1)

    print(f"[INFO] 로드: {len(rows)}건 (에러 {len(errors)}건)")
    db = SessionLocal()
    try:
        for r in rows:
            upsert_from_dict(db, r)
        print(f"[OK] 적재: {len(rows)}건")
    finally:
        db.close()


if __name__ == "__main__":
    main()
