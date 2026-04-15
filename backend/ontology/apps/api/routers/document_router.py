"""문서 확장자·지원 정보 API.

PDF/TXT/Word/Excel 지원 확장자는 domain/shared/document_extract 단일 소스.
프론트는 이 API로 accept 문자열 등과 동기화.
"""

from fastapi import APIRouter

from domain.shared.document_extract import (  # type: ignore
    SUPPORTED_EXCEL_EXTENSIONS,
    SUPPORTED_EXTENSIONS,
    SUPPORTED_TEXT_EXTENSIONS,
)

router = APIRouter(prefix="/document", tags=["Document"])


@router.get("/supported-extensions")
def get_supported_extensions():
    """지원 문서 확장자 (domain/shared/document_extract와 동기화)."""
    return {
        "text": list(SUPPORTED_TEXT_EXTENSIONS),
        "excel": list(SUPPORTED_EXCEL_EXTENSIONS),
        "all": list(SUPPORTED_EXTENSIONS),
    }
