"""
공통 유틸리티 함수

중복 코드를 제거하기 위한 공통 유틸리티 모듈
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List

# 환경 변수 설정 (한 곳에서 관리)
os.environ.setdefault("TRANSFORMERS_TRUST_REMOTE_CODE", "true")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")


def get_api_root() -> Path:
    """API 루트 디렉토리 경로 반환.

    Returns:
        app/api 디렉토리 경로
    """
    current_dir = Path(__file__).parent  # services
    return current_dir.parent.parent  # services -> spam -> domains -> api


def get_app_root() -> Path:
    """App 루트 디렉토리 경로 반환.

    Returns:
        app 디렉토리 경로
    """
    current_dir = Path(__file__).parent  # services
    return current_dir.parent.parent.parent  # services -> spam -> domains -> app


def get_artifacts_dir() -> Path:
    """Artifacts 디렉토리 경로 반환.

    Returns:
        app/artifacts 디렉토리 경로
    """
    return get_app_root() / "artifacts"


def get_base_models_dir() -> Path:
    """Base 모델 디렉토리 경로 반환.

    Returns:
        app/artifacts/base_models 디렉토리 경로
    """
    return get_artifacts_dir() / "base_models"


def get_fine_tuned_dir() -> Path:
    """Fine-tuning된 모델 디렉토리 경로 반환.

    Returns:
        app/artifacts/fine_tuned 디렉토리 경로
    """
    return get_artifacts_dir() / "fine_tuned"


def get_model_dir() -> Path:
    """모델 디렉토리 경로 반환 (하위 호환성).

    Returns:
        app/artifacts/base_models 디렉토리 경로
    """
    return get_base_models_dir()


def get_data_dir() -> Path:
    """데이터 디렉토리 경로 반환.

    Returns:
        app/data 디렉토리 경로
    """
    return get_app_root() / "data"


def get_output_dir() -> Path:
    """출력 디렉토리 경로 반환 (하위 호환성).

    Returns:
        app/artifacts/fine_tuned 디렉토리 경로
    """
    return get_fine_tuned_dir()


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
                # JSON 파싱 오류는 무시하고 계속 진행
                continue

    return data


def save_jsonl(data: List[Dict[str, Any]], file_path: Path) -> None:
    """JSONL 파일 저장.

    Args:
        data: 데이터 리스트
        file_path: 저장할 파일 경로
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def extract_email_metadata(sft_item: Dict[str, Any]) -> Dict[str, Any]:
    """SFT 형식 데이터에서 이메일 메타데이터 추출.

    Args:
        sft_item: SFT 형식 데이터 (instruction, input, output 포함)

    Returns:
        이메일 메타데이터
    """
    input_data = sft_item.get("input", {})
    return {
        "subject": input_data.get("subject", ""),
        "sender": input_data.get("sender", ""),
        "attachments": input_data.get("attachments", []),
        "received_at": input_data.get("received_at", ""),
    }


def format_email_text(email_metadata: Dict[str, Any]) -> str:
    """이메일 메타데이터를 텍스트로 변환.

    Args:
        email_metadata: 이메일 메타데이터
            - subject: 제목
            - sender: 발신자
            - attachments: 첨부파일 목록
            - received_at: 수신 일시

    Returns:
        포맷팅된 텍스트
    """
    subject = email_metadata.get("subject", "")
    sender = email_metadata.get("sender", "")
    attachments = email_metadata.get("attachments", [])
    received_at = email_metadata.get("received_at", "")

    attachments_str = ", ".join(attachments) if attachments else "없음"

    text = f"제목: {subject}\n발신자: {sender}\n첨부파일: {attachments_str}\n수신일시: {received_at}"

    return text


def format_sft_prompt(instruction: str, input_data: Dict[str, Any]) -> str:
    """SFT 형식을 프롬프트 문자열로 변환.

    Args:
        instruction: 지시문
        input_data: 입력 데이터 (subject, attachments, received_at 등)

    Returns:
        포맷팅된 프롬프트
    """
    subject = input_data.get("subject", "")
    attachments = input_data.get("attachments", [])
    received_at = input_data.get("received_at", "")

    attachments_str = ", ".join(attachments) if attachments else "없음"

    prompt = f"{instruction}\n\n제목: {subject}\n첨부파일: {attachments_str}\n수신일시: {received_at}"

    return prompt
