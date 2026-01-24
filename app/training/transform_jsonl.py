"""
ETL Transform: Split Train/Validation Dataset

학습 전 최종 준비 통합 스크립트 (BP).

역할: Transform (변환 - 최종 단계)
1. 데이터 품질 검증 및 정제
2. 토크나이징 준비 및 시퀀스 길이 관리
3. Train/Validation 분할 (Stratified)

입력: transform_raw_to_sft.py가 생성한 sft_train.jsonl 파일
출력: train.jsonl, val.jsonl (학습 준비 완료)
"""

import json
import random
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# app/ 디렉토리를 Python 경로에 추가
app_dir = Path(__file__).parent.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

try:
    from transformers import AutoTokenizer

    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    print("[WARNING] transformers가 설치되지 않았습니다. 토크나이징 기능을 건너뜁니다.")

# transform_validation.py에서 DataQualityValidator import
from training.transform_validation import DataQualityValidator  # type: ignore


class TokenizerManager:
    """토크나이저 관리 클래스."""

    def __init__(self, model_path: Optional[Path] = None):
        """초기화.

        Args:
            model_path: EXAONE 모델 경로 (None이면 자동 탐지)
        """
        self.tokenizer = None
        self.model_path = model_path or self._find_exaone_model()

    def _find_exaone_model(self) -> Optional[Path]:
        """EXAONE 모델 경로 자동 탐지."""
        current_dir = Path(
            __file__
        ).parent.parent.parent  # spam_agent -> service -> api
        exaone_dir = current_dir / "model" / "exaone"

        if exaone_dir.exists() and (exaone_dir / "tokenizer.json").exists():
            return exaone_dir

        return None

    def load_tokenizer(self) -> bool:
        """토크나이저 로드.

        Returns:
            로드 성공 여부
        """
        if not HAS_TRANSFORMERS:
            return False

        if self.model_path is None:
            print(
                "[WARNING] EXAONE 모델 경로를 찾을 수 없습니다. 토크나이징을 건너뜁니다."
            )
            return False

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                str(self.model_path), trust_remote_code=True
            )
            print(f"[OK] 토크나이저 로드 완료: {self.model_path}")
            return True
        except Exception as e:
            print(f"[WARNING] 토크나이저 로드 실패: {e}")
            return False

    def tokenize_sample(
        self, item: Dict[str, Any], max_length: int = 2048
    ) -> Tuple[Optional[int], bool]:
        """샘플 토크나이징 및 길이 확인.

        Args:
            item: SFT 형식 샘플
            max_length: 최대 토큰 길이

        Returns:
            (토큰 길이, 제한 내 여부)
        """
        if self.tokenizer is None:
            return None, True  # 토크나이저 없으면 통과

        try:
            # 프롬프트 구성
            instruction = item.get("instruction", "")
            input_data = item.get("input", {})
            subject = input_data.get("subject", "")
            attachments = input_data.get("attachments", [])
            received_at = input_data.get("received_at", "")

            prompt = f"{instruction}\n제목: {subject}\n첨부파일: {', '.join(attachments) if attachments else '없음'}\n수신일시: {received_at}"

            # 토크나이징
            tokens = self.tokenizer.encode(prompt, add_special_tokens=True)
            token_length = len(tokens)

            return token_length, token_length <= max_length
        except Exception as e:
            print(f"[WARNING] 토크나이징 실패: {e}")
            return None, True  # 오류 시 통과


def load_jsonl(file_path: Path) -> List[Dict[str, Any]]:
    """JSONL 파일 로드.

    Args:
        file_path: JSONL 파일 경로

    Returns:
        데이터 리스트
    """
    data = []
    with file_path.open("r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            try:
                item = json.loads(line)
                data.append(item)
            except json.JSONDecodeError:
                continue

    return data


def save_jsonl(data: List[Dict[str, Any]], output_path: Path) -> None:
    """JSONL 파일 저장.

    Args:
        data: 저장할 데이터 리스트
        output_path: 출력 파일 경로
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def split_train_val(
    data: List[Dict[str, Any]],
    train_ratio: float = 0.9,
    seed: int = 42,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Stratified Train/Validation 분할.

    Args:
        data: 전체 데이터
        train_ratio: 학습 데이터 비율
        seed: 랜덤 시드

    Returns:
        (train_data, val_data)
    """
    random.seed(seed)

    # 클래스별로 분류
    block_samples = [
        item for item in data if item.get("output", {}).get("action") == "BLOCK"
    ]
    allow_samples = [
        item for item in data if item.get("output", {}).get("action") == "ALLOW"
    ]

    # 각 클래스별로 분할
    random.shuffle(block_samples)
    random.shuffle(allow_samples)

    block_split = int(len(block_samples) * train_ratio)
    allow_split = int(len(allow_samples) * train_ratio)

    train_data = block_samples[:block_split] + allow_samples[:allow_split]
    val_data = block_samples[block_split:] + allow_samples[allow_split:]

    # 최종 셔플
    random.shuffle(train_data)
    random.shuffle(val_data)

    return train_data, val_data


def process_sft_dataset(
    input_path: Path,
    output_dir: Path,
    train_ratio: float = 0.9,
    max_token_length: int = 2048,
    seed: int = 42,
) -> Dict[str, Any]:
    """SFT 데이터셋 처리 (검증 + 토크나이징 + 분할).

    Args:
        input_path: 입력 SFT JSONL 파일 경로
        output_dir: 출력 디렉토리
        train_ratio: 학습 데이터 비율
        max_token_length: 최대 토큰 길이
        seed: 랜덤 시드

    Returns:
        통계 딕셔너리
    """
    print(f"[INFO] 데이터셋 처리 시작: {input_path}")
    print()

    # 1. 데이터 로드
    print("[Step 1] 데이터 로드 중...")
    all_data = load_jsonl(input_path)
    print(f"[INFO] 총 {len(all_data)}개 샘플 로드됨")
    print()

    # 2. 데이터 품질 검증
    print("[Step 2] 데이터 품질 검증 중...")
    validator = DataQualityValidator()
    valid_data: List[Dict[str, Any]] = []
    invalid_count = 0
    warnings_count: Dict[str, int] = defaultdict(int)

    for item in all_data:
        is_valid, error, warnings = validator.validate_item(item)
        if is_valid:
            valid_data.append(item)
            for warning in warnings:
                warnings_count[warning] += 1
        else:
            invalid_count += 1

    print(f"[INFO] 유효 샘플: {len(valid_data)}개")
    print(f"[INFO] 무효 샘플: {invalid_count}개")
    if warnings_count:
        print(f"[INFO] 경고: {sum(warnings_count.values())}개")
    print()

    # 3. 토크나이징 준비 및 시퀀스 길이 관리
    print("[Step 3] 토크나이징 준비 및 시퀀스 길이 관리 중...")
    tokenizer_mgr = TokenizerManager()
    tokenized_data = []
    token_lengths = []
    removed_by_token = 0

    if tokenizer_mgr.load_tokenizer():
        for item in valid_data:
            token_length, is_valid = tokenizer_mgr.tokenize_sample(
                item, max_token_length
            )
            if token_length is not None:
                token_lengths.append(token_length)

            if is_valid:
                tokenized_data.append(item)
            else:
                removed_by_token += 1

        if token_lengths:
            print("[INFO] 토큰 길이 통계:")
            print(f"  - 최소: {min(token_lengths)} 토큰")
            print(f"  - 최대: {max(token_lengths)} 토큰")
            print(f"  - 평균: {sum(token_lengths) / len(token_lengths):.2f} 토큰")
            print(f"[INFO] 제한 초과로 제거된 샘플: {removed_by_token}개")
    else:
        print("[INFO] 토크나이저를 사용할 수 없어 토크나이징 단계를 건너뜁니다.")
        tokenized_data = valid_data

    print(f"[INFO] 토크나이징 후 샘플: {len(tokenized_data)}개")
    print()

    # 4. Train/Validation 분할
    print(
        f"[Step 4] Train/Validation 분할 중... (비율: {train_ratio:.0%}/{1 - train_ratio:.0%})"
    )
    train_data, val_data = split_train_val(tokenized_data, train_ratio, seed)

    # 클래스 분포 확인
    train_block = sum(
        1 for item in train_data if item.get("output", {}).get("action") == "BLOCK"
    )
    train_allow = len(train_data) - train_block
    val_block = sum(
        1 for item in val_data if item.get("output", {}).get("action") == "BLOCK"
    )
    val_allow = len(val_data) - val_block

    print(
        f"[INFO] Train: {len(train_data)}개 (BLOCK: {train_block}, ALLOW: {train_allow})"
    )
    print(
        f"[INFO] Validation: {len(val_data)}개 (BLOCK: {val_block}, ALLOW: {val_allow})"
    )
    print()

    # 5. 파일 저장
    print("[Step 5] 파일 저장 중...")
    output_dir.mkdir(parents=True, exist_ok=True)

    train_path = output_dir / "train.jsonl"
    val_path = output_dir / "val.jsonl"

    save_jsonl(train_data, train_path)
    save_jsonl(val_data, val_path)

    print(f"[OK] Train 데이터 저장: {train_path}")
    print(f"[OK] Validation 데이터 저장: {val_path}")
    print()

    # 통계 반환
    stats = {
        "total": len(all_data),
        "valid": len(valid_data),
        "invalid": invalid_count,
        "tokenized": len(tokenized_data),
        "removed_by_token": removed_by_token,
        "train": len(train_data),
        "validation": len(val_data),
        "train_ratio": train_ratio,
        "warnings": dict(warnings_count),
    }

    return stats


def main():
    """메인 실행 함수."""
    # 경로 설정 (app/training -> app -> app/data/sft_dataset)
    app_dir = Path(__file__).parent.parent  # training -> app
    data_dir = app_dir / "data" / "sft_dataset"

    # 입력 파일 찾기 (우선순위: cleaned > train)
    # transform_raw_to_sft.py가 생성한 sft_train.jsonl 파일 사용
    input_file = data_dir / "sft_train_cleaned.jsonl"
    if not input_file.exists():
        input_file = data_dir / "sft_train.jsonl"

    if not input_file.exists():
        print("[ERROR] 입력 파일을 찾을 수 없습니다.")
        print("[INFO] 다음 파일 중 하나가 필요합니다:")
        print(f"  - {data_dir / 'sft_train_cleaned.jsonl'}")
        print(f"  - {data_dir / 'sft_train.jsonl'}")
        print(
            "[INFO] 먼저 transform_raw_to_sft.py를 실행하여 SFT 형식 파일을 생성하세요."
        )
        return

    # 출력 디렉토리
    output_dir = data_dir / "processed"

    print(f"[INFO] 입력 파일: {input_file}")
    print(f"[INFO] 출력 디렉토리: {output_dir}")
    print()

    # 처리 실행
    stats = process_sft_dataset(
        input_path=input_file,
        output_dir=output_dir,
        train_ratio=0.9,
        max_token_length=2048,
        seed=42,
    )

    # 최종 통계 출력
    print("=" * 60)
    print("[OK] 데이터셋 처리 완료!")
    print("=" * 60)
    print("[INFO] 최종 통계:")
    print(f"  - 총 샘플: {stats['total']}개")
    print(
        f"  - 유효 샘플: {stats['valid']}개 ({stats['valid'] / stats['total'] * 100:.2f}%)"
    )
    print(f"  - 무효 샘플: {stats['invalid']}개")
    print(f"  - 토크나이징 후: {stats['tokenized']}개")
    print(f"  - 토큰 제한 초과 제거: {stats['removed_by_token']}개")
    print(
        f"  - Train: {stats['train']}개 ({stats['train'] / stats['tokenized'] * 100:.2f}%)"
    )
    print(
        f"  - Validation: {stats['validation']}개 ({stats['validation'] / stats['tokenized'] * 100:.2f}%)"
    )
    print()
    print("[INFO] 출력 파일:")
    print(f"  - {output_dir / 'train.jsonl'}")
    print(f"  - {output_dir / 'val.jsonl'}")


if __name__ == "__main__":
    main()
