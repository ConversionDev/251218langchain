"""
신입 샘플 JSONL의 department를 일반 기업 대표 부서 7개로 통일.

대표 부서: 인사, 재무, 영업, 마케팅, 개발·IT, 경영지원, 전략·기획

실행 (app 디렉터리에서):
  python -m training.pipelines.resume_samples.normalize_departments --file data/resume/samples/new_hire_samples_20260219_0256.jsonl
  python -m training.pipelines.resume_samples.normalize_departments  # 최신 샘플 파일 자동 선택
"""

import argparse
import json
import sys
from pathlib import Path

app_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

from core.paths import get_resume_samples_dir  # type: ignore

# 일반 기업 공통 대표 부서 7개
CANONICAL_DEPARTMENTS = [
    "인사",
    "재무",
    "영업",
    "마케팅",
    "개발·IT",
    "경영지원",
    "전략·기획",
]

# 기존 부서명 -> 대표 부서 매핑
DEPARTMENT_MAP = {
    "마케팅": "마케팅",
    "마케팅 전략": "마케팅",
    "개발": "개발·IT",
    "제품 개발": "개발·IT",
    "협업 개발": "개발·IT",
    "영업": "영업",
    "영업 관리": "영업",
    "영업 전략": "영업",
    "프로젝트 관리": "전략·기획",
    "팀 리더십": "인사",
    "리더십 개발": "인사",
    "팀 리더십 개발": "인사",
    "팀 리더십 프로그램": "인사",
}
DEFAULT_DEPARTMENT = "경영지원"


def map_department(raw: str) -> str:
    return DEPARTMENT_MAP.get(raw.strip(), DEFAULT_DEPARTMENT)


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize departments to 7 canonical ones")
    parser.add_argument(
        "--file",
        type=Path,
        default=None,
        help="JSONL file path (default: latest in data/resume/samples)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print mapping stats only, do not write")
    args = parser.parse_args()

    if args.file is not None:
        path = Path(args.file)
        if not path.is_absolute():
            path = app_dir / path
    else:
        samples_dir = get_resume_samples_dir()
        files = sorted(samples_dir.glob("new_hire_samples_*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not files:
            print("No new_hire_samples_*.jsonl found in", samples_dir)
            sys.exit(1)
        path = files[0]
        print("Using latest file:", path.name)

    if not path.exists():
        print("File not found:", path)
        sys.exit(1)

    rows: list[dict] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if not isinstance(obj, dict) or "department" not in obj:
                    rows.append(obj)
                    continue
                old_dept = obj.get("department", "")
                new_dept = map_department(old_dept)
                obj["department"] = new_dept
                rows.append(obj)
            except json.JSONDecodeError:
                continue

    # 7개 부서가 모두 나오도록 부족한 부서에 재할당
    from collections import Counter
    counts = Counter(r.get("department", "") for r in rows)
    missing = [d for d in CANONICAL_DEPARTMENTS if counts[d] == 0]
    if missing:
        # 부서별 행 인덱스 (많은 순으로 기부할 후보)
        indices_by_dept: dict[str, list[int]] = {}
        for i, r in enumerate(rows):
            d = r.get("department", "")
            indices_by_dept.setdefault(d, []).append(i)
        donor_order = sorted(
            [d for d in indices_by_dept if d in CANONICAL_DEPARTMENTS],
            key=lambda d: -len(indices_by_dept[d]),
        )
        for need_dept in missing:
            n_need = max(1, len(rows) // 7)
            assigned = 0
            for donor in donor_order:
                if assigned >= n_need:
                    break
                donor_indices = indices_by_dept[donor]
                n_take = min(n_need - assigned, max(1, len(donor_indices) // 2))
                for idx in donor_indices[:n_take]:
                    rows[idx]["department"] = need_dept
                    assigned += 1
                indices_by_dept[donor] = donor_indices[n_take:]
                if assigned >= n_need:
                    break

    if args.dry_run:
        counts_after = Counter(r.get("department", "") for r in rows)
        print("Canonical departments:", CANONICAL_DEPARTMENTS)
        print("Counts after mapping:")
        for d in CANONICAL_DEPARTMENTS:
            print(f"  {d}: {counts_after[d]}")
        return

    with open(path, "w", encoding="utf-8") as f:
        for obj in rows:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

    counts_after = Counter(r.get("department", "") for r in rows)
    print("Wrote", path)
    print("Counts:", dict(counts_after))


if __name__ == "__main__":
    main()
