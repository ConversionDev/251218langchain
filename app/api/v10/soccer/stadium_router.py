"""
스타디움 데이터 업로드 및 미리보기 API

JSONL 파일을 받아서 첫 5개 행을 미리보기하고, 전체 데이터를 DB에 저장합니다.
"""

import json
import logging
import tempfile
import os
from pathlib import Path
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session

from core.database import get_v10_db, get_v10_vector_store  # type: ignore
from core.config import get_settings  # type: ignore
from domain.v10.shared.data_loader import load_stadiums_hybrid  # type: ignore

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/soccer/stadium/upload")
async def upload_stadium_jsonl(
    file: UploadFile = File(...),
    db: Session = Depends(get_v10_db)
):
    """
    스타디움 JSONL 파일을 업로드하고 첫 5개 행을 미리보기한 후, 전체 데이터를 DB에 저장합니다.

    Args:
        file: 업로드할 JSONL 파일

    Returns:
        미리보기 데이터 및 저장 결과
    """
    try:
        # 파일 확장자 검증
        if not file.filename or not file.filename.endswith('.jsonl'):
            raise HTTPException(
                status_code=400,
                detail="JSONL 파일만 업로드 가능합니다."
            )

        # 파일 내용 읽기 (미리보기용)
        content = await file.read()
        content_str = content.decode('utf-8')

        # JSONL 파싱 (첫 5개 행만 - 미리보기)
        lines = content_str.strip().split('\n')
        preview_data: List[Dict[str, Any]] = []

        for i, line in enumerate(lines[:5], 1):  # 첫 5개 행만
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
                preview_data.append({
                    "row": i,
                    "data": data
                })
            except json.JSONDecodeError as e:
                logger.warning(f"행 {i} 파싱 실패: {str(e)}")
                preview_data.append({
                    "row": i,
                    "error": f"JSON 파싱 오류: {str(e)}",
                    "raw": line[:100]  # 처음 100자만
                })

        # 임베딩 모델 가져오기 (서버에서 초기화된 것 사용)
        try:
            from server import local_embeddings  # type: ignore
            if local_embeddings is None:
                raise HTTPException(
                    status_code=503,
                    detail="임베딩 모델이 초기화되지 않았습니다. 서버를 재시작하세요."
                )
            embeddings_model = local_embeddings
        except ImportError:
            raise HTTPException(
                status_code=503,
                detail="임베딩 모델을 가져올 수 없습니다. 서버를 재시작하세요."
            )

        # 벡터 스토어 생성
        settings = get_settings()
        vector_store = get_v10_vector_store(embeddings_model, settings.v10_collection_name)

        # 임시 파일로 저장 (DB 저장용)
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.jsonl') as tmp_file:
            tmp_file.write(content)  # 이미 읽은 content 사용
            tmp_path = Path(tmp_file.name)

        try:
            logger.info(f"[업로드 시작] stadiums 파일: {file.filename}")

            # 하이브리드 방식으로 데이터 로드 (전체 데이터 저장)
            results = load_stadiums_hybrid(
                jsonl_path=tmp_path,
                db=db,
                vector_store=vector_store
            )

            # DB 커밋 확인
            db.commit()

            logger.info(
                f"[업로드 완료] stadiums: "
                f"관계형 DB {results.get('db', 0)}개, "
                f"벡터 스토어 {results.get('vector', 0)}개 저장됨"
            )

            return {
                "success": True,
                "message": "스타디움 데이터 업로드 및 로드 완료",
                "data_type": "stadiums",
                "filename": file.filename,
                "total_rows": len(lines),
                "preview_rows": len(preview_data),
                "preview": preview_data,
                "results": results,
            }

        except Exception as load_error:
            # 에러 발생 시 DB 롤백
            db.rollback()
            logger.error(f"[업로드 실패] stadiums 파일 처리 중 오류: {str(load_error)}")
            raise HTTPException(
                status_code=500,
                detail=f"데이터 로드 중 오류 발생: {str(load_error)}"
            )
        finally:
            # 임시 파일 삭제
            if tmp_path.exists():
                try:
                    os.unlink(tmp_path)
                except Exception as cleanup_error:
                    logger.warning(f"임시 파일 삭제 실패: {str(cleanup_error)}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"파일 업로드 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"파일 업로드 중 오류 발생: {str(e)}"
        )
