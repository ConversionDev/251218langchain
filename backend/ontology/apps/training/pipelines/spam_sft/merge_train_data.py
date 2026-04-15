"""
스팸 SFT 학습 데이터 병합

train.jsonl + exaone_synthetic.jsonl 을 합쳐 train_full.jsonl 로 저장합니다.
셔플(seed 고정) 후 저장하므로 두 소스가 골고루 섞입니다.
검증은 기존 val.jsonl 을 그대로 사용하면 됩니다.

실행 (프로젝트 루트에서 app 이 패키지로 잡히는 경우):
  python -m app.training.pipelines.spam_sft.merge_train_data

또는 app 디렉터리에서:
  python -m training.pipelines.spam_sft.merge_train_data
"""

import json
import random
import sys
from pathlib import Path

# app 루트를 path에 추가
app_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

from core.paths import get_spam_sft_dir  # noqa: E402

SEED = 42
TRAIN_FULL_FILENAME = "train_full.jsonl"


def _load_jsonl(file_path: Path) -> list:
    data = []
    with file_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return data


def _save_jsonl(data: list, file_path: Path) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def main() -> None:
    sft_dir = get_spam_sft_dir()
    train_path = sft_dir / "train.jsonl"
    exaone_path = sft_dir / "exaone_synthetic.jsonl"
    out_path = sft_dir / TRAIN_FULL_FILENAME

    if not train_path.exists():
        print(f"[ERROR] 없음: {train_path}")
        sys.exit(1)
    if not exaone_path.exists():
        print(f"[ERROR] 없음: {exaone_path}")
        sys.exit(1)

    train = _load_jsonl(train_path)
    exaone = _load_jsonl(exaone_path)
    merged = train + exaone
    random.seed(SEED)
    random.shuffle(merged)

    _save_jsonl(merged, out_path)
    print(f"[OK] 병합 완료: {len(train)} + {len(exaone)} = {len(merged)} 건")
    print(f"     저장: {out_path}")
    print()
    print("다음으로 학습 실행:")
    print(f"  python -m app.training.models.llama.spam_classifier.finetune \\")
    print(f"    --train_path {out_path} \\")
    print(f"    --val_path {sft_dir / 'val.jsonl'}")


if __name__ == "__main__":
    main()
