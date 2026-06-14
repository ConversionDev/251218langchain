"""이력서 분석 API.

POST /api/resume/analyze: 이력서 파일 업로드 → 텍스트 추출 → RAG+LLM 분석 → Success DNA + 기본 정보 반환.
Core 직원 등록 시 이력서 업로드로 연동.
지원 확장자: domain/shared/document_extract.SUPPORTED_TEXT_EXTENSIONS (PDF, TXT, Word .docx)
"""

import asyncio
import logging
from typing import Any, Dict

from fastapi import APIRouter, File, HTTPException, UploadFile

from api.services.resume_analyzer import analyze_resume_file  # type: ignore
from core.config import settings  # type: ignore
from domain.shared.document_extract import (  # type: ignore
    SUPPORTED_IMAGE_EXTENSIONS,
    SUPPORTED_TEXT_EXTENSIONS,
)

# 이력서 업로드 허용 = 텍스트 문서 + 이미지(스캔본, Gemini OCR 처리)
RESUME_UPLOAD_EXTENSIONS = (*SUPPORTED_TEXT_EXTENSIONS, *SUPPORTED_IMAGE_EXTENSIONS)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resume", tags=["Resume"])


@router.post("/analyze")
async def resume_analyze(file: UploadFile = File(..., description="이력서 파일 (PDF, TXT, Word .docx, 이미지 png/jpg — 스캔본은 OCR)")):
    """이력서 파일을 분석하여 기본 정보와 Success DNA를 반환합니다.

    Returns:
        name, jobTitle, department, email, joinedAt, resume, successDna
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="파일명이 없습니다.")

    ext = (file.filename or "").lower()
    if not any(ext.endswith(e) for e in RESUME_UPLOAD_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail=f"지원 형식: {', '.join(RESUME_UPLOAD_EXTENSIONS)}",
        )

    try:
        data = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"파일 읽기 실패: {e}")

    if not data or len(data) < 10:
        raise HTTPException(status_code=400, detail="파일 내용이 비어있거나 너무 짧습니다.")

    max_bytes = int(settings.resume_max_file_size_mb * 1024 * 1024)
    if len(data) > max_bytes:
        raise HTTPException(status_code=400, detail=f"파일 크기는 {settings.resume_max_file_size_mb:.0f}MB를 초과할 수 없습니다.")

    try:
        result: Dict[str, Any] = await asyncio.to_thread(
            analyze_resume_file,
            data,
            file.filename or "resume.pdf",
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception("이력서 분석 실패: %s", e)
        raise HTTPException(status_code=500, detail=f"이력서 분석 중 오류가 발생했습니다: {e}")
