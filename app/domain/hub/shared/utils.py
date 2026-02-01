"""
공통 유틸리티 함수

중복 코드를 제거하기 위한 공통 유틸리티 모듈.
경로 유틸은 core.paths를 재사용합니다.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List

# 환경 변수 설정 (한 곳에서 관리)
os.environ.setdefault("TRANSFORMERS_TRUST_REMOTE_CODE", "true")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")


def get_app_root() -> Path:
    """App 루트 디렉토리 경로 반환."""
    from core.paths import get_app_root as _get  # type: ignore

    return _get()


def get_api_root() -> Path:
    """API 루트 디렉토리 경로 반환 (get_app_root 별칭)."""
    return get_app_root()


def get_artifacts_dir() -> Path:
    """Artifacts 디렉토리 경로 반환."""
    from core.paths import get_artifacts_dir as _get  # type: ignore

    return _get()


def get_base_models_dir() -> Path:
    """Base 모델 디렉토리 경로 반환."""
    from core.paths import get_base_models_dir as _get  # type: ignore

    return _get()


def get_fine_tuned_dir() -> Path:
    """Fine-tuning된 모델 디렉토리 경로 반환."""
    from core.paths import get_fine_tuned_dir as _get  # type: ignore

    return _get()


def get_model_dir() -> Path:
    """모델 디렉토리 경로 반환 (하위 호환성)."""
    return get_base_models_dir()


def get_data_dir() -> Path:
    """데이터 디렉토리 경로 반환."""
    from core.paths import get_data_dir as _get  # type: ignore

    return _get()


def get_output_dir() -> Path:
    """출력 디렉토리 경로 반환 (하위 호환성)."""
    from core.paths import get_output_dir as _get  # type: ignore

    return _get()


def load_jsonl(file_path: Path) -> List[Dict[str, Any]]:
    """JSONL 파일 로드."""
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


def save_jsonl(data: List[Dict[str, Any]], file_path: Path) -> None:
    """JSONL 파일 저장."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def extract_email_metadata(sft_item: Dict[str, Any]) -> Dict[str, Any]:
    """SFT 형식 데이터에서 이메일 메타데이터 추출."""
    input_data = sft_item.get("input", {})
    return {
        "subject": input_data.get("subject", ""),
        "sender": input_data.get("sender", ""),
        "attachments": input_data.get("attachments", []),
        "received_at": input_data.get("received_at", ""),
    }


def format_email_text(email_metadata: Dict[str, Any]) -> str:
    """이메일 메타데이터를 텍스트로 변환."""
    subject = email_metadata.get("subject", "")
    sender = email_metadata.get("sender", "")
    attachments = email_metadata.get("attachments", [])
    received_at = email_metadata.get("received_at", "")
    attachments_str = ", ".join(attachments) if attachments else "없음"
    return f"제목: {subject}\n발신자: {sender}\n첨부파일: {attachments_str}\n수신일시: {received_at}"


def format_sft_prompt(instruction: str, input_data: Dict[str, Any]) -> str:
    """SFT 형식을 프롬프트 문자열로 변환."""
    subject = input_data.get("subject", "")
    attachments = input_data.get("attachments", [])
    received_at = input_data.get("received_at", "")
    attachments_str = ", ".join(attachments) if attachments else "없음"
    return f"{instruction}\n\n제목: {subject}\n첨부파일: {attachments_str}\n수신일시: {received_at}"
