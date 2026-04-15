"""
채팅 첨부 파일 임시 저장소 (BP: 업로드 API → file_id → 채팅에서 참조).

저장 후 file_id 반환, 채팅 처리 시 로드·삭제(1회 사용).
"""

import logging
import tempfile
import uuid
from pathlib import Path
from typing import List

from core.config import get_settings  # type: ignore

logger = logging.getLogger(__name__)


def _safe_file_id(file_id: str) -> bool:
    """file_id는 uuid4.hex(32자 영숫자)만 허용 (경로 이탈 방지)."""
    return bool(file_id and len(file_id) == 32 and file_id.isalnum())


def _get_upload_dir() -> Path:
    settings = get_settings()
    if settings.upload_dir and settings.upload_dir.strip():
        p = Path(settings.upload_dir.strip())
    else:
        p = Path(tempfile.gettempdir()) / "rag_upload"
    p.mkdir(parents=True, exist_ok=True)
    return p


def save_upload_file(data: bytes) -> str:
    """바이트를 저장하고 file_id 반환."""
    upload_dir = _get_upload_dir()
    file_id = uuid.uuid4().hex
    path = upload_dir / file_id
    path.write_bytes(data)
    return file_id


def load_upload_file(file_id: str) -> bytes | None:
    """file_id로 파일 바이트 로드. 없으면 None."""
    if not _safe_file_id(file_id):
        return None
    upload_dir = _get_upload_dir()
    path = upload_dir / file_id
    if not path.is_file():
        return None
    try:
        return path.read_bytes()
    except OSError as e:
        logger.warning("업로드 파일 로드 실패 %s: %s", file_id, e)
        return None


def delete_upload_file(file_id: str) -> None:
    """file_id 파일 삭제."""
    if not _safe_file_id(file_id):
        return
    upload_dir = _get_upload_dir()
    path = upload_dir / file_id
    try:
        if path.is_file():
            path.unlink()
    except OSError as e:
        logger.warning("업로드 파일 삭제 실패 %s: %s", file_id, e)


def load_upload_files_as_base64(file_ids: List[str], delete_after: bool = True) -> List[str]:
    """file_id 목록으로 파일 로드 후 base64 리스트 반환. delete_after=True면 로드 후 삭제."""
    import base64

    result: List[str] = []
    for fid in (f for f in file_ids if _safe_file_id(str(f))):
        data = load_upload_file(fid)
        if data:
            result.append(base64.b64encode(data).decode("utf-8"))
        if delete_after:
            delete_upload_file(fid)
    return result
