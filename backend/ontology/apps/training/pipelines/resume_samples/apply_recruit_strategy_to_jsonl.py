"""
채용 전략에 맞춰 신입 샘플 JSONL 필드를 수정합니다.

- status: "pending" (미검토)
- applicationDate: 지원일 (기존 joinedAt 기준 2개월 전, 없으면 2023-06-01)
- joinedAt: null (지원자는 아직 입사 전)
- successDna: 유지 (AI 분석 시 덮어쓰기 가능)

실행 (app 디렉터리에서):
  python -m training.pipelines.resume_samples.apply_recruit_strategy_to_jsonl
  python -m training.pipelines.resume_samples.apply_recruit_strategy_to_jsonl --file app/data/resume/samples/new_hire_samples_20260219_0256.jsonl
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

app_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

from core.paths import get_resume_samples_dir  # type: ignore


def application_date_from_joined(joined_at: str | None) -> str:
    """joinedAt 문자열에서 약 2개월 전 날짜를 지원일로 사용."""
    if not joined_at or not joined_at.strip():
        return "2023-06-01"
    try:
        dt = datetime.strptime(joined_at.strip()[:10], "%Y-%m-%d")
        app_dt = dt - timedelta(days=60)
        return app_dt.strftime("%Y-%m-%d")
    except ValueError:
        return "2023-06-01"


def apply_strategy(obj: dict) -> dict:
    """한 레코드에 채용 전략 필드 적용."""
    out = dict(obj)
    out["status"] = "pending"
    out["applicationDate"] = application_date_from_joined(out.get("joinedAt"))
    out["joinedAt"] = None
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="신입 샘플 JSONL에 채용 전략 필드(status, applicationDate, joinedAt=null) 적용")
    parser.add_argument("--file", type=Path, default=None, help="JSONL 파일 경로 (미지정 시 samples 폴더 최신 파일)")
    parser.add_argument("--dry-run", action="store_true", help="적용 결과만 출력, 파일 미저장")
    args = parser.parse_args()

    path = args.file
    if path is None:
        samples_dir = get_resume_samples_dir()
        files = sorted(samples_dir.glob("new_hire_samples_*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not files:
            print("[ERROR] data/resume/samples/ 에 new_hire_samples_*.jsonl 파일이 없습니다.")
            sys.exit(1)
        path = files[0]
        print(f"[INFO] 최신 파일 사용: {path}")

    path = Path(path)
    if not path.is_absolute():
        path = app_dir / path
    if not path.exists():
        print(f"[ERROR] 파일 없음: {path}")
        sys.exit(1)

    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    rows.append(apply_strategy(obj))
                else:
                    print(f"[WARN] 줄 {i}: 객체가 아님, 건너뜀")
            except json.JSONDecodeError as e:
                print(f"[WARN] 줄 {i}: JSON 파싱 실패 - {e}")

    if not rows:
        print("[ERROR] 유효한 행이 없습니다.")
        sys.exit(1)

    print(f"[INFO] 적용 완료: {len(rows)}건 (status=pending, applicationDate 설정, joinedAt=null)")
    sample = rows[0]
    print(f"[INFO] 샘플 키: {sorted(sample.keys())}")
    print(f"[INFO] 샘플 status={sample.get('status')}, applicationDate={sample.get('applicationDate')}, joinedAt={sample.get('joinedAt')}")

    if args.dry_run:
        print("[INFO] --dry-run: 파일 저장 생략")
        return

    # 같은 경로에 덮어쓰기 (안전하게 임시 파일 후 교체)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    tmp_path.replace(path)
    print(f"[INFO] 저장 완료: {path}")


if __name__ == "__main__":
    main()
