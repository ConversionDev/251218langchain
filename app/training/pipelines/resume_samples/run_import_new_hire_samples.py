"""
생성된 신입 샘플 JSONL 검증 및 employees 테이블 적재.

검증: 줄 수, 필수 필드(id, name, jobTitle, department, successDna, resume 등) 확인.
적재: 각 줄을 POST에 대응하는 형태로 DB에 insert (repository 사용).

실행 (app 디렉터리에서):
  # 검증만 (DB 변경 없음)
  python -m training.pipelines.resume_samples.run_import_new_hire_samples --file data/resume/samples/new_hire_samples_YYYYMMDD_HHMM.jsonl --dry-run

  # 검증 후 DB 적재
  python -m training.pipelines.resume_samples.run_import_new_hire_samples --file data/resume/samples/new_hire_samples_YYYYMMDD_HHMM.jsonl

  # samples 폴더에서 가장 최신 파일 자동 선택
  python -m training.pipelines.resume_samples.run_import_new_hire_samples
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

app_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

from core.database import SessionLocal  # type: ignore
from core.paths import get_resume_samples_dir  # type: ignore
from domain.hub.repositories.employee_repository import create as repo_create  # type: ignore

_REQUIRED_KEYS = {"id", "name", "jobTitle", "department"}
_OPTIONAL_BUT_EXPECTED = {"successDna", "resume", "employmentType", "applicationDate", "joinedAt", "gender", "age", "trainingHours", "status"}


def load_and_validate_jsonl(path: Path) -> tuple[list[dict], list[str]]:
    """JSONL 파일을 읽고, 각 줄을 파싱·검증. 반환: (유효한 행 리스트, 에러 메시지 리스트)."""
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


def import_to_db(rows: list[dict], skip_existing: bool = True) -> tuple[int, int]:
    """rows를 employees 테이블에 삽입. 반환: (성공 수, 스킵/실패 수)."""
    db = SessionLocal()
    ok, skip = 0, 0
    try:
        for r in rows:
            try:
                repo_create(db, r)
                ok += 1
            except ValueError as e:
                if "already exists" in str(e).lower() or "ALREADY_EXISTS" in str(e):
                    if skip_existing:
                        skip += 1
                        continue
                raise
        return ok, skip
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="신입 샘플 JSONL 검증 및 DB 적재")
    parser.add_argument("--file", type=Path, default=None, help="JSONL 파일 경로 (미지정 시 samples 폴더 최신 파일)")
    parser.add_argument("--dry-run", action="store_true", help="검증만 하고 DB에 넣지 않음")
    parser.add_argument("--no-skip", action="store_true", help="id 중복 시 스킵하지 않고 에러")
    args = parser.parse_args()

    path = args.file
    if path is None:
        samples_dir = get_resume_samples_dir()
        files = sorted(samples_dir.glob("new_hire_samples_*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not files:
            print("[ERROR] data/resume/samples/ 에 new_hire_samples_*.jsonl 파일이 없습니다. 먼저 run_generate_new_hire_samples 를 실행하세요.")
            sys.exit(1)
        path = files[0]
        print(f"[INFO] 최신 파일 사용: {path}")

    path = Path(path)
    if not path.is_absolute():
        path = app_dir / path
    if not path.exists():
        print(f"[ERROR] 파일 없음: {path}")
        sys.exit(1)

    rows, errors = load_and_validate_jsonl(path)
    if errors:
        for e in errors[:20]:
            print(f"[WARN] {e}")
        if len(errors) > 20:
            print(f"[WARN] ... 외 {len(errors) - 20}건")
    if not rows:
        print("[ERROR] 유효한 행이 없습니다.")
        sys.exit(1)

    print(f"[INFO] 검증 완료: 총 {len(rows)}건 (에러 {len(errors)}건)")
    if rows:
        sample = rows[0]
        keys = set(sample.keys())
        print(f"[INFO] 샘플 키: {sorted(keys)}")
        if _OPTIONAL_BUT_EXPECTED - keys:
            print(f"[INFO] 선택 키 미존재: {_OPTIONAL_BUT_EXPECTED - keys}")

    if args.dry_run:
        print("[INFO] --dry-run: DB 적재 생략")
        return

    started = datetime.now()
    print(f"[INFO] DB 적재 시작: {started.strftime('%Y-%m-%d %H:%M:%S')}")
    ok, skip = import_to_db(rows, skip_existing=not args.no_skip)
    finished = datetime.now()
    elapsed = finished - started
    print(f"[INFO] DB 적재 종료: {finished.strftime('%Y-%m-%d %H:%M:%S')} (소요 {elapsed.total_seconds():.1f}초)")
    print(f"[INFO] 적재 완료: 성공 {ok}건, 스킵(이미 존재) {skip}건")


if __name__ == "__main__":
    main()
