"""
성과 샘플 JSONL → performance_records 테이블 적재.

정규화된 JSONL(normalize_performance_jsonl 실행 후 또는 목표 형식)을 읽어
통합 테이블 performance_records에 넣습니다.

실행 (app 디렉터리):
  python -m training.pipelines.performance_samples.run_import_performance_samples
  python -m training.pipelines.performance_samples.run_import_performance_samples --file data/performance/samples/performance_samples_20260221_1141.jsonl
  python -m training.pipelines.performance_samples.run_import_performance_samples --no-skip
"""

import argparse
import json
import sys
from pathlib import Path

app_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

from core.database import SessionLocal  # type: ignore
from core.paths import get_performance_samples_dir  # type: ignore
from domain.hub.repositories.performance_record_repository import bulk_insert  # type: ignore

_REQUIRED_KEYS = {"id", "employeeId", "period", "textType", "text"}


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
    parser = argparse.ArgumentParser(description="성과 샘플 JSONL → performance_records 적재")
    parser.add_argument("--file", type=Path, default=None, help="JSONL 경로 (미지정 시 samples 최신 파일)")
    parser.add_argument("--no-skip", action="store_true", help="id 중복 시 스킵하지 않고 에러")
    args = parser.parse_args()

    if args.file is not None:
        path = Path(args.file)
    else:
        samples_dir = get_performance_samples_dir()
        files = sorted(
            samples_dir.glob("performance_samples_*.jsonl"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if not files:
            print(
                "[ERROR] data/performance/samples/ 에 performance_samples_*.jsonl 이 없습니다. "
                "먼저 normalize_performance_jsonl 을 실행하세요.",
                file=sys.stderr,
            )
            sys.exit(1)
        path = files[0]
        print(f"[INFO] 최신 파일 사용: {path}")

    path = Path(path)
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
        ok, skip = bulk_insert(db, rows, skip_existing=not args.no_skip)
        print(f"[OK] 적재: 성공 {ok}건, 스킵(이미 존재) {skip}건")
    finally:
        db.close()


if __name__ == "__main__":
    main()
