"""
팀 데이터 업로드 및 미리보기 API

JSONL 파일을 받아서 첫 5개 행을 미리보기하고, 전체 데이터를 DB에 저장합니다.
"""

import json
import logging
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session

from core.database import get_v10_db  # type: ignore
from domain.v10.soccer.hub.orchestrators.team_orchestrator import TeamOrchestrator  # type: ignore

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/soccer/team/upload")
async def upload_team_jsonl(
    file: UploadFile = File(...),
    db: Session = Depends(get_v10_db)
):
    """
    팀 JSONL 파일을 업로드하고 첫 5개 행을 미리보기한 후, 전체 데이터를 DB에 저장합니다.

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

        # 파일 내용 읽기
        content = await file.read()
        content_str = content.decode('utf-8')

        # JSONL 파싱
        lines = content_str.strip().split('\n')

        # 미리보기 데이터 (첫 5개 행)
        preview_data: List[Dict[str, Any]] = []
        # 전체 데이터
        all_data: List[Dict[str, Any]] = []

        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
                all_data.append(data)

                # 미리보기용 (첫 5개 행만) - 프론트 형식에 맞게 변환
                if i <= 5:
                    preview_data.append({
                        "row": i,
                        "data": data
                    })

            except json.JSONDecodeError as e:
                logger.warning(f"행 {i} 파싱 실패: {str(e)}")
                if i <= 5:
                    preview_data.append({
                        "row": i,
                        "error": f"JSON 파싱 오류: {str(e)}",
                        "raw": line[:100]  # 처음 100자만
                    })

        try:
            logger.info(f"[업로드 시작] teams 파일: {file.filename}")

            # Orchestrator 초기화
            orchestrator = TeamOrchestrator()

            # Orchestrator를 통해 데이터 처리 (LangGraph 휴리스틱 처리 + 규칙 기반 DB 저장)
            orchestrator_result = orchestrator.process(
                data=all_data,
                preview_data=preview_data,
                db=db  # DB 세션 전달 (규칙 기반 저장용)
            )

            # DB 커밋 (규칙 기반 저장 후)
            db.commit()

            # 결과 정리
            strategy_result = orchestrator_result.get("result", {})
            decided_strategy = orchestrator_result.get("decided_strategy", "rule")

            logger.info(
                f"[업로드 완료] teams: "
                f"전략={decided_strategy}, "
                f"처리됨={strategy_result.get('processed', 0)}/{strategy_result.get('total', 0)}개"
            )

            return {
                "success": orchestrator_result.get("success", False),
                "message": "팀 데이터 업로드 및 로드 완료",
                "data_type": "teams",
                "filename": file.filename,
                "total_rows": len(all_data),
                "preview_rows": len(preview_data),
                "preview": preview_data,
                "strategy": decided_strategy,
                "results": strategy_result,
            }

        except Exception as load_error:
            # 에러 발생 시 DB 롤백
            db.rollback()
            logger.error(f"[업로드 실패] teams 파일 처리 중 오류: {str(load_error)}")
            raise HTTPException(
                status_code=500,
                detail=f"데이터 로드 중 오류 발생: {str(load_error)}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"파일 업로드 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"파일 업로드 중 오류 발생: {str(e)}"
        )
