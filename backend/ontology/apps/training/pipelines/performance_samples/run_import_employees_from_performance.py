"""
성과 샘플 JSONL에서 직원(employeeId, name, jobTitle, department, email)을 추출해
employees 테이블에 기존 직원(employmentType=regular)으로 적재.

성과 데이터에 등장하는 사람들을 기존 직원 목록에 먼저 넣은 뒤,
run_import_performance_samples 로 성과 기록을 넣으면 됩니다.

실행 (app 디렉터리):
  python -m training.pipelines.performance_samples.run_import_employees_from_performance
  python -m training.pipelines.performance_samples.run_import_employees_from_performance --file data/performance/samples/performance_samples_20260221_1141.jsonl
  python -m training.pipelines.performance_samples.run_import_employees_from_performance --dry-run
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
from infrastructure.persistence.repositories.employee_repository import create as repo_create  # type: ignore


def load_and_extract_employees(path: Path) -> tuple[list[dict], list[str]]:
    """JSONL을 읽어 직원별 첫 등장 행에서 (id, name, jobTitle, department, email) 추출. 중복 제거."""
    seen: set[str] = set()
    employees: list[dict] = []
    errors = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if not isinstance(obj, dict):
                    continue
                eid = obj.get("employeeId") or obj.get("employee_id")
                if not eid or eid in seen:
                    continue
                seen.add(eid)
                employees.append({
                    "id": eid,
                    "name": (obj.get("name") or "").strip() or eid,
                    "jobTitle": (obj.get("jobTitle") or "").strip() or "",
                    "department": (obj.get("department") or "").strip() or "",
                    "email": (obj.get("email") or "").strip() or None,
                })
            except json.JSONDecodeError:
                errors.append(f"줄 {i}: JSON 파싱 실패")
    return employees, errors


def main() -> None:
    parser = argparse.ArgumentParser(
        description="성과 JSONL에서 직원 추출 후 employees 테이블에 기존 직원으로 적재"
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=None,
        help="성과 샘플 JSONL 경로 (미지정 시 samples 최신 performance_samples_*.jsonl)",
    )
    parser.add_argument("--dry-run", action="store_true", help="추출만 하고 DB 적재 안 함")
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
                "[ERROR] data/performance/samples/ 에 performance_samples_*.jsonl 이 없습니다.",
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

    employees, errors = load_and_extract_employees(path)
    if errors:
        for e in errors[:10]:
            print(f"[WARN] {e}")
        if len(errors) > 10:
            print(f"[WARN] ... 외 {len(errors) - 10}건")

    if not employees:
        print("[ERROR] 추출된 직원이 없습니다.", file=sys.stderr)
        sys.exit(1)

    print(f"[INFO] 추출된 직원: {len(employees)}명 (employeeId 기준 중복 제거)")
    if args.dry_run:
        for e in employees[:5]:
            print(f"  - {e['id']}: {e['name']} / {e['department']}")
        if len(employees) > 5:
            print(f"  ... 외 {len(employees) - 5}명")
        print("[INFO] --dry-run: DB 적재 생략")
        return

    db = SessionLocal()
    ok, skip = 0, 0
    try:
        for e in employees:
            row_data = {
                **e,
                "employmentType": "regular",
                "status": None,
            }
            try:
                repo_create(db, row_data)
                ok += 1
            except ValueError as err:
                if "already exists" in str(err).lower() or "ALREADY_EXISTS" in str(err):
                    if not args.no_skip:
                        skip += 1
                        continue
                raise
    finally:
        db.close()

    print(f"[OK] employees 적재: 성공 {ok}건, 스킵(이미 존재) {skip}건")
    print("[INFO] 이제 run_import_performance_samples 로 성과 기록을 넣으면 됩니다.")


if __name__ == "__main__":
    main()
