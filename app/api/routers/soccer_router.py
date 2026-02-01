"""축구 데이터 업로드 API (선수, 팀, 스케줄, 스타디움)."""

import json
import logging
from typing import Any, Dict, List, Type

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from core.database import get_v10_db  # type: ignore

logger = logging.getLogger(__name__)

router = APIRouter(tags=["soccer"])


async def _process_jsonl_upload(
    file: UploadFile,
    db: Session,
    data_type: str,
    message_ok: str,
    OrchestratorClass: Type[Any],
) -> Dict[str, Any]:
    """JSONL 파싱 + 미리보기 + 오케스트레이터 처리 공통 로직."""
    if not file.filename or not file.filename.endswith(".jsonl"):
        raise HTTPException(status_code=400, detail="JSONL 파일만 업로드 가능합니다.")

    content = await file.read()
    lines = content.decode("utf-8").strip().split("\n")
    preview_data: List[Dict[str, Any]] = []
    all_data: List[Dict[str, Any]] = []

    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            all_data.append(data)
            if i <= 5:
                preview_data.append({"row": i, "data": data})
        except json.JSONDecodeError as e:
            logger.warning("행 %d 파싱 실패: %s", i, str(e))
            if i <= 5:
                preview_data.append({"row": i, "error": f"JSON 파싱 오류: {str(e)}", "raw": line[:100]})

    try:
        logger.info("[업로드 시작] %s 파일: %s", data_type, file.filename)
        orchestrator = OrchestratorClass()
        result = orchestrator.process(data=all_data, preview_data=preview_data, db=db)
        db.commit()
        strategy_result = result.get("result", {})
        decided_strategy = result.get("decided_strategy", "rule")
        logger.info(
            "[업로드 완료] %s: 전략=%s, 처리됨=%s/%s개",
            data_type,
            decided_strategy,
            strategy_result.get("processed", 0),
            strategy_result.get("total", 0),
        )
        return {
            "success": result.get("success", False),
            "message": message_ok,
            "data_type": data_type,
            "filename": file.filename,
            "total_rows": len(all_data),
            "preview_rows": len(preview_data),
            "preview": preview_data,
            "strategy": decided_strategy,
            "results": strategy_result,
        }
    except Exception as load_error:
        db.rollback()
        logger.error("[업로드 실패] %s 파일 처리 중 오류: %s", data_type, str(load_error))
        raise HTTPException(status_code=500, detail=f"데이터 로드 중 오류 발생: {str(load_error)}") from load_error


@router.post("/soccer/player/upload")
async def upload_player_jsonl(
    file: UploadFile = File(...),
    db: Session = Depends(get_v10_db),
):
    """선수 JSONL 업로드 및 미리보기."""
    from domain.hub.orchestrators import PlayerOrchestrator  # type: ignore

    try:
        return await _process_jsonl_upload(
            file, db, "players", "선수 데이터 업로드 및 로드 완료", PlayerOrchestrator
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("파일 업로드 중 오류 발생: %s", str(e))
        raise HTTPException(status_code=500, detail=f"파일 업로드 중 오류 발생: {str(e)}") from e


@router.post("/soccer/team/upload")
async def upload_team_jsonl(
    file: UploadFile = File(...),
    db: Session = Depends(get_v10_db),
):
    """팀 JSONL 업로드 및 미리보기."""
    from domain.hub.orchestrators import TeamOrchestrator  # type: ignore

    try:
        return await _process_jsonl_upload(
            file, db, "teams", "팀 데이터 업로드 및 로드 완료", TeamOrchestrator
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("파일 업로드 중 오류 발생: %s", str(e))
        raise HTTPException(status_code=500, detail=f"파일 업로드 중 오류 발생: {str(e)}") from e


@router.post("/soccer/schedule/upload")
async def upload_schedule_jsonl(
    file: UploadFile = File(...),
    db: Session = Depends(get_v10_db),
):
    """스케줄 JSONL 업로드 및 미리보기."""
    from domain.hub.orchestrators import ScheduleOrchestrator  # type: ignore

    try:
        return await _process_jsonl_upload(
            file, db, "schedules", "스케줄 데이터 업로드 및 로드 완료", ScheduleOrchestrator
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("파일 업로드 중 오류 발생: %s", str(e))
        raise HTTPException(status_code=500, detail=f"파일 업로드 중 오류 발생: {str(e)}") from e


@router.post("/soccer/stadium/upload")
async def upload_stadium_jsonl(
    file: UploadFile = File(...),
    db: Session = Depends(get_v10_db),
):
    """스타디움 JSONL 업로드 및 미리보기."""
    from domain.hub.orchestrators import StadiumOrchestrator  # type: ignore

    try:
        return await _process_jsonl_upload(
            file, db, "stadiums", "스타디움 데이터 업로드 및 로드 완료", StadiumOrchestrator
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("파일 업로드 중 오류 발생: %s", str(e))
        raise HTTPException(status_code=500, detail=f"파일 업로드 중 오류 발생: {str(e)}") from e
