"""
기존 성과 샘플 JSONL을 목표 형식으로 수정 (재생성 없이).

- successDna 제거 (AI가 나중에 텍스트 기반으로 채움)
- employeeId별 300명 고유 name·email 부여 (generator와 동일 규칙)

실행 (app 디렉터리):
  python -m training.pipelines.performance_samples.normalize_performance_jsonl
  python -m training.pipelines.performance_samples.normalize_performance_jsonl --file data/performance/samples/performance_samples_20260221_1141.jsonl --in-place
"""

import argparse
import json
import sys
from pathlib import Path

app_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

# generator와 동일 규칙 (300명 고유 이름·이메일)
_SURNAMES = ["김", "이", "박", "최", "정", "강", "조", "윤", "장", "임", "한", "오", "서", "신", "권"]
_GIVEN_NAMES = [
    "민준", "서연", "지우", "예은", "도윤", "하준", "시우", "준혁", "지훈", "수아",
    "유나", "재윤", "현우", "소율", "다은", "보라", "지현", "하율", "태민", "승우",
]
NAMES_POOL = [s + g for s in _SURNAMES for g in _GIVEN_NAMES]
RECENT_GRADES = ["사원", "대리", "과장", "차장", "팀장"]
CANONICAL_DEPARTMENTS = ["인사", "재무", "영업", "마케팅", "개발·IT", "경영지원", "전략·기획"]


def build_employee_profile() -> dict:
    """HP001~HP150, NP001~NP150 → name, jobTitle, email (300명 고유)."""
    profile = {}
    num_depts = len(CANONICAL_DEPARTMENTS)
    num_grades = len(RECENT_GRADES)
    num_names = len(NAMES_POOL)
    for prefix in ("HP", "NP"):
        for i in range(1, 151):
            eid = f"{prefix}{str(i).zfill(3)}"
            idx = (0 if prefix == "HP" else 150) + (i - 1)
            profile[eid] = {
                "name": NAMES_POOL[idx % num_names],
                "jobTitle": RECENT_GRADES[idx % num_grades],
                "department": CANONICAL_DEPARTMENTS[(i - 1) % num_depts],
                "email": f"{eid.lower()}@company.local",
            }
    return profile


def normalize_row(row: dict, profile: dict) -> dict:
    """successDna 제거, name/jobTitle/department/email 프로필로 덮기."""
    out = dict(row)
    out.pop("successDna", None)
    eid = out.get("employeeId") or ""
    if eid in profile:
        out["name"] = profile[eid]["name"]
        out["jobTitle"] = profile[eid]["jobTitle"]
        out["department"] = profile[eid]["department"]
        out["email"] = profile[eid]["email"]
    else:
        out.setdefault("email", f"{eid.lower()}@company.local" if eid else "")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="성과 샘플 JSONL 목표 형식 정규화 (successDna 제거, 300명 이름/이메일)")
    parser.add_argument("--file", type=Path, default=None, help="입력 JSONL 경로")
    parser.add_argument("--in-place", action="store_true", help="원본 파일 덮어쓰기 (미지정 시 _normalized.jsonl 로 저장)")
    parser.add_argument("-o", "--output", type=Path, default=None, help="출력 경로 (--in-place 미사용 시)")
    args = parser.parse_args()

    from core.paths import get_performance_samples_dir  # type: ignore

    samples_dir = get_performance_samples_dir()
    if args.file is not None:
        path = Path(args.file)
    else:
        files = sorted(samples_dir.glob("performance_samples_*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not files:
            print("[ERROR] data/performance/samples/ 에 performance_samples_*.jsonl 이 없습니다.", file=sys.stderr)
            sys.exit(1)
        path = files[0]
        print(f"[INFO] 최신 파일 사용: {path}")

    if not path.exists():
        print(f"[ERROR] 파일 없음: {path}", file=sys.stderr)
        sys.exit(1)

    profile = build_employee_profile()
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
                rows.append(normalize_row(row, profile))
            except json.JSONDecodeError as e:
                print(f"[WARN] JSON 파싱 스킵: {e}", file=sys.stderr)

    if args.in_place:
        out_path = path
    elif args.output is not None:
        out_path = args.output
    else:
        out_path = path.parent / f"{path.stem}_normalized.jsonl"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"[OK] {len(rows)}건 정규화 → {out_path}")
    if args.in_place and path != out_path:
        pass
    elif args.in_place:
        print("[INFO] 원본 파일이 목표 형식으로 덮어씌워졌습니다.")


if __name__ == "__main__":
    main()
