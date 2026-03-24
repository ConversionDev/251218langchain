"""
labeled_slots.csv → 엑사원 SFT용 messages 형식 JSONL (esg_error_chat.jsonl).

실행 (app 디렉터리에서):
  cd C:\\dev\\RAG\\app
  python -m training.pipelines.esg_dummy.run_esg_to_chat_format
  python -m training.pipelines.esg_dummy.run_esg_to_chat_format --max-rows 30000
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

_app_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_app_root) not in sys.path:
    sys.path.insert(0, str(_app_root))

from core.paths import get_esg_dummy_dir  # type: ignore  # app 하위 실행 시 core = app/core


def row_to_user_content(row: dict[str, str]) -> str:
    """한 슬롯 행을 모델 입력용 문장으로 변환."""
    parts = [
        f"날짜 {row.get('noticedate', '')}",
        f"시간 {row.get('hour', '')}시",
        f"공정 {row.get('process', '')}",
        f"라인 {row.get('line', '')}",
        f"전력사용량 {row.get('usage', '')}",
        f"생산량 {row.get('production', '')}",
        f"설비수 {row.get('equipment_ct', '')}",
        f"교대 {row.get('shift', '')}",
        f"스크랩 {row.get('scrap', '')}",
        f"폐기물 {row.get('waste', '')}",
    ]
    return " | ".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(description="labeled_slots.csv → esg_error_chat.jsonl")
    parser.add_argument("--max-rows", type=int, default=0, help="최대 행 수 (0=전체). SFT용 샘플 제한 시 사용")
    parser.add_argument("--seed", type=int, default=42, help="샘플링 시드")
    args = parser.parse_args()

    data_dir = get_esg_dummy_dir()
    csv_path = data_dir / "labeled_slots.csv"
    out_path = data_dir / "esg_error_chat.jsonl"

    if not csv_path.exists():
        print(f"[ERROR] 파일 없음: {csv_path}")
        sys.exit(1)

    t0 = time.perf_counter()
    rows: list[dict[str, str]] = []
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            label = (r.get("label") or "").strip()
            if not label:
                continue
            rows.append(r)

    if args.max_rows and len(rows) > args.max_rows:
        import random
        random.seed(args.seed)
        rows = random.sample(rows, args.max_rows)
        print(f"[INFO] {args.max_rows}건 샘플링 (seed={args.seed})")

    count = 0
    with out_path.open("w", encoding="utf-8") as f:
        for r in rows:
            user_text = row_to_user_content(r)
            label = (r.get("label") or "normal").strip()
            msg = {
                "label": label,
                "messages": [
                    {"role": "user", "content": f"다음 시계열 슬롯의 이상 유형을 한 단어로만 답하세요.\n\n{user_text}"},
                    {"role": "assistant", "content": label},
                ],
            }
            f.write(json.dumps(msg, ensure_ascii=False) + "\n")
            count += 1

    elapsed = time.perf_counter() - t0
    print(f"[OK] {out_path.name} 생성: {count}건  |  소요: {elapsed:.1f}초  속도: {count / elapsed:.0f} rows/s")
    print(f"     경로: {out_path}")


if __name__ == "__main__":
    main()
