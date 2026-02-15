"""
Competency prepared JSONL 검증: 행 수(1~2000), 필수 필드(content, source) 존재.
"""

import json
from pathlib import Path
from typing import Optional, Tuple

from training.shared.competency_extract import get_competency_prepared_dir  # type: ignore


def verify_competency_prepared(
    prepared_dir: Optional[Path] = None,
    max_rows: int = 2000,
) -> Tuple[bool, str]:
    """
    prepared/competency_rows.jsonl 검증.

    Returns:
        (성공 여부, 실패 시 메시지)
    """
    prepared = prepared_dir or get_competency_prepared_dir()
    path = prepared / "competency_rows.jsonl"
    if not path.exists():
        return True, ""  # 파일 없으면 검증 스킵(추출 결과 없음)
    count = 0
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            count += 1
            if count > max_rows:
                return False, f"행 수 초과: {max_rows} 초과"
            try:
                row = json.loads(line)
            except json.JSONDecodeError as e:
                return False, f"JSON 파싱 실패 (행 {count}): {e}"
            if not row.get("content") or not str(row.get("content", "")).strip():
                return False, f"행 {count}: content 없음"
            if not row.get("source"):
                return False, f"행 {count}: source 없음"
    if count == 0:
        return False, "행이 0건입니다"
    return True, ""
