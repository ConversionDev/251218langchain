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


# 경로는 core.paths에서 직접 import (이중 경유 제거)

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
    """SFT 형식 데이터에서 이메일 메타데이터 추출 (LLaMA 스팸 학습·추론 공통)."""
    input_data = sft_item.get("input", {})
    return {
        "subject": input_data.get("subject", ""),
        "sender": input_data.get("sender", ""),
        "body": input_data.get("body", ""),
        "attachments": input_data.get("attachments", []),
        "received_at": input_data.get("received_at", ""),
    }


def format_email_text(email_metadata: Dict[str, Any]) -> str:
    """이메일 메타데이터를 텍스트로 변환 (제목·발신자·본문·첨부·수신일시)."""
    subject = email_metadata.get("subject", "")
    sender = email_metadata.get("sender", "")
    body = email_metadata.get("body", "")
    attachments = email_metadata.get("attachments", [])
    received_at = email_metadata.get("received_at", "")
    attachments_str = ", ".join(attachments) if attachments else "없음"
    parts = [f"제목: {subject}", f"발신자: {sender}"]
    if body:
        parts.append(f"본문: {body}")
    parts.extend([f"첨부파일: {attachments_str}", f"수신일시: {received_at}"])
    return "\n".join(parts)


def format_sft_prompt(instruction: str, input_data: Dict[str, Any]) -> str:
    """SFT 형식을 프롬프트 문자열로 변환."""
    subject = input_data.get("subject", "")
    attachments = input_data.get("attachments", [])
    received_at = input_data.get("received_at", "")
    attachments_str = ", ".join(attachments) if attachments else "없음"
    return f"{instruction}\n\n제목: {subject}\n첨부파일: {attachments_str}\n수신일시: {received_at}"
