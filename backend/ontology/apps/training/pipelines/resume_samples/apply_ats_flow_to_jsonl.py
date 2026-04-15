"""
샘플 JSONL을 실제 ATS 플로우에 맞게 수정합니다.

- successDna: null — AI 분석 전 상태. [AI 분석] 클릭 시 엑사원이 resume 기반으로 생성.
- applicationDate: null — 일괄 적재 샘플은 제출 시각 없음. /apply 제출분만 서버 시각 기록.
- status: "pending", joinedAt: null 유지.

실행 (app 디렉터리에서):
  python -m training.pipelines.resume_samples.apply_ats_flow_to_jsonl --file data/resume/samples/new_hire_samples_20260219_0256.jsonl
"""

import argparse
import json
import sys
from pathlib import Path

app_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

from core.paths import get_resume_samples_dir  # type: ignore


def apply_ats(obj: dict) -> dict:
    """한 레코드를 ATS 플로우용으로 변경."""
    out = dict(obj)
    out["successDna"] = None
    out["applicationDate"] = None
    out["status"] = "pending"
    out["joinedAt"] = None
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="샘플 JSONL을 ATS 플로우용으로 수정 (successDna=null, applicationDate=null)")
    parser.add_argument("--file", type=Path, default=None, help="JSONL 파일 경로")
    parser.add_argument("--dry-run", action="store_true", help="저장하지 않고 결과만 출력")
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
                    rows.append(apply_ats(obj))
                else:
                    print(f"[WARN] 줄 {i}: 객체가 아님, 건너뜀")
            except json.JSONDecodeError as e:
                print(f"[WARN] 줄 {i}: JSON 파싱 실패 - {e}")

    if not rows:
        print("[ERROR] 유효한 행이 없습니다.")
        sys.exit(1)

    print(f"[INFO] ATS 플로우 적용: {len(rows)}건 (successDna=null, applicationDate=null, status=pending)")
    sample = rows[0]
    print(f"[INFO] 샘플 successDna={sample.get('successDna')}, applicationDate={sample.get('applicationDate')}")

    if args.dry_run:
        print("[INFO] --dry-run: 파일 저장 생략")
        return

    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    tmp_path.replace(path)
    print(f"[INFO] 저장 완료: {path}")


if __name__ == "__main__":
    main()
