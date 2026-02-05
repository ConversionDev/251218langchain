"""축구 API: 공개 업로드(/api/soccer/*) + 내부 MCP 프록시(/internal/soccer/*). 업로드는 in-process만 사용."""

import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from domain.hub.mcp.utils import get_soccer_mcp_url, result_to_str  # type: ignore
from domain.models.enums import SpamPolicy  # type: ignore

logger = logging.getLogger(__name__)

_UPLOAD_MAP: Dict[str, tuple] = {
    "players": ("player", "process_player"),
    "teams": ("team", "process_team"),
    "schedules": ("schedule", "process_schedule"),
    "stadiums": ("stadium", "process_stadium"),
}


def _inprocess_process(
    data_type: str,
    all_data: List[Dict[str, Any]],
    preview_data: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """같은 프로세스에서 오케스트레이터 직접 호출."""
    from domain.spokes.soccer.mcp.soccer_server import (  # type: ignore
        _process_player_impl,
        _process_schedule_impl,
        _process_stadium_impl,
        _process_team_impl,
    )
    impl_map: Dict[str, Any] = {
        "players": _process_player_impl,
        "teams": _process_team_impl,
        "schedules": _process_schedule_impl,
        "stadiums": _process_stadium_impl,
    }
    impl = impl_map.get(data_type)
    if not impl:
        raise ValueError(f"지원하지 않는 data_type: {data_type}")
    return impl(data=all_data, preview_data=preview_data, db=None, vector_store=None)

# 공개 API: /api/soccer/* (register_router에서 prefix="/api" 적용)
router = APIRouter(tags=["soccer"])

# 내부 API: /internal/soccer/* (spokes가 Hub HTTP로 호출)
_internal = APIRouter(prefix="/internal/soccer", tags=["Soccer Proxy"])


async def _process_jsonl_upload(
    file: UploadFile,
    data_type: str,
    message_ok: str,
) -> Dict[str, Any]:
    """JSONL 파싱 + 미리보기 + in-process 오케스트레이터 호출."""
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

    if data_type not in _UPLOAD_MAP:
        raise HTTPException(status_code=400, detail=f"지원하지 않는 data_type: {data_type}")

    try:
        logger.info("[업로드 시작] %s 파일: %s", data_type, file.filename)
        raw = _inprocess_process(data_type, all_data, preview_data)
        result = raw if isinstance(raw, dict) else json.loads(str(raw))
        strategy_result = result.get("result", {})
        decided_strategy = result.get("decided_strategy", SpamPolicy.RULE.value)
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
    except HTTPException:
        raise
    except Exception as load_error:
        logger.error("[업로드 실패] %s 파일 처리 중 오류: %s", data_type, str(load_error))
        raise HTTPException(status_code=500, detail=f"데이터 로드 중 오류 발생: {str(load_error)}") from load_error


@router.post("/soccer/player/upload")
async def upload_player_jsonl(file: UploadFile = File(...)):
    """선수 JSONL 업로드 및 미리보기 (BP: Hub → soccer_call → Spoke)."""
    try:
        return await _process_jsonl_upload(file, "players", "선수 데이터 업로드 및 로드 완료")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("파일 업로드 중 오류 발생: %s", str(e))
        raise HTTPException(status_code=500, detail=f"파일 업로드 중 오류 발생: {str(e)}") from e


@router.post("/soccer/team/upload")
async def upload_team_jsonl(file: UploadFile = File(...)):
    """팀 JSONL 업로드 및 미리보기 (BP: Hub → soccer_call → Spoke)."""
    try:
        return await _process_jsonl_upload(file, "teams", "팀 데이터 업로드 및 로드 완료")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("파일 업로드 중 오류 발생: %s", str(e))
        raise HTTPException(status_code=500, detail=f"파일 업로드 중 오류 발생: {str(e)}") from e


@router.post("/soccer/schedule/upload")
async def upload_schedule_jsonl(file: UploadFile = File(...)):
    """스케줄 JSONL 업로드 및 미리보기 (BP: Hub → soccer_call → Spoke)."""
    try:
        return await _process_jsonl_upload(file, "schedules", "스케줄 데이터 업로드 및 로드 완료")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("파일 업로드 중 오류 발생: %s", str(e))
        raise HTTPException(status_code=500, detail=f"파일 업로드 중 오류 발생: {str(e)}") from e


@router.post("/soccer/stadium/upload")
async def upload_stadium_jsonl(file: UploadFile = File(...)):
    """스타디움 JSONL 업로드 및 미리보기 (BP: Hub → soccer_call → Spoke)."""
    try:
        return await _process_jsonl_upload(file, "stadiums", "스타디움 데이터 업로드 및 로드 완료")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("파일 업로드 중 오류 발생: %s", str(e))
        raise HTTPException(status_code=500, detail=f"파일 업로드 중 오류 발생: {str(e)}") from e


# ---------------------------------------------------------------------------
# 임베딩 동기화 (BullMQ 스타일): 큐에 job 추가 → 워커 → 오케스트레이터 → 서비스
# ---------------------------------------------------------------------------

class EmbeddingJobRequest(BaseModel):
    entities: Optional[List[str]] = Field(default=None, description="players, teams, schedules, stadiums. 없으면 전체.")


def _run_embedding_sync_background(job_id: str, entities: Optional[List[str]]) -> None:
    """백그라운드에서 임베딩 동기화 실행. 완료 시 Redis 상태를 completed/failed로 갱신."""
    from api.shared.embedding_sync import run_embedding_sync_task  # type: ignore

    run_embedding_sync_task(job_id, entities)


@router.post("/soccer/embedding")
async def embedding_job_add(
    request: EmbeddingJobRequest,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """버튼 클릭 시 즉시 백그라운드에서 임베딩 동기화 실행. job_id 반환 후 폴링으로 상태 확인."""
    from api.shared.redis import create_embedding_job_inline, is_redis_token_valid  # type: ignore

    if not is_redis_token_valid():
        raise HTTPException(status_code=503, detail="Redis 연결 불가(UPSTASH_REDIS_REST_URL/TOKEN 확인)")
    entities = request.entities or ["players", "teams", "schedules", "stadiums"]
    job_id = create_embedding_job_inline(entities)
    if job_id is None:
        raise HTTPException(status_code=500, detail="job 등록 실패")
    background_tasks.add_task(_run_embedding_sync_background, job_id, entities)
    return {"job_id": job_id, "status": "processing"}


@router.get("/soccer/embedding/status/{job_id}")
async def embedding_job_status(job_id: str) -> Dict[str, Any]:
    """job 상태 조회. waiting | processing | completed | failed."""
    from api.shared.redis import get_embedding_job_status  # type: ignore

    data = get_embedding_job_status(job_id)
    if data is None:
        raise HTTPException(status_code=404, detail="job을 찾을 수 없음")
    return data


# ---------------------------------------------------------------------------
# 내부 /internal/soccer/* (Hub MCP Soccer HTTP 프록시)
# ---------------------------------------------------------------------------


class SoccerRouteRequest(BaseModel):
    question: str = Field(..., description="라우팅할 질문")


class SoccerRouteResponse(BaseModel):
    result: str = Field(..., description="선택된 오케스트레이터 등")


class SoccerCallRequest(BaseModel):
    orchestrator: str = Field(..., description="오케스트레이터 이름")
    tool: str = Field(..., description="도구 이름")
    arguments: Optional[Dict[str, Any]] = Field(default_factory=lambda: {}, description="인자")


class SoccerRouteAndCallRequest(BaseModel):
    question: str = Field(..., description="질문")
    tool: str = Field(..., description="도구 이름")
    arguments: Optional[Dict[str, Any]] = Field(default_factory=lambda: {}, description="인자")


@_internal.post("/route", response_model=SoccerRouteResponse)
async def soccer_route_endpoint(request: SoccerRouteRequest) -> SoccerRouteResponse:
    """Soccer 라우팅만. Soccer MCP call_tool 위임."""
    try:
        from fastmcp.client import Client  # type: ignore
        url = get_soccer_mcp_url()
        async with Client(url) as client:
            result = await client.call_tool("soccer_route", {"question": request.question})
            return SoccerRouteResponse(result=result_to_str(result))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@_internal.post("/call")
async def soccer_call_endpoint(request: SoccerCallRequest) -> Dict[str, Any]:
    """Soccer MCP → Spoke call_tool 프록시."""
    try:
        from fastmcp.client import Client  # type: ignore
        url = get_soccer_mcp_url()
        async with Client(url) as client:
            result = await client.call_tool(
                "soccer_call",
                {
                    "orchestrator": request.orchestrator,
                    "tool": request.tool,
                    "arguments": request.arguments or {},
                },
            )
            if hasattr(result, "data") and result.data is not None:
                return {"result": result.data}
            return {"result": result_to_str(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@_internal.post("/route_and_call")
async def soccer_route_and_call_endpoint(request: SoccerRouteAndCallRequest) -> Dict[str, Any]:
    """라우팅 후 Soccer MCP → Spoke call_tool까지 한 번에."""
    try:
        from fastmcp.client import Client  # type: ignore
        url = get_soccer_mcp_url()
        async with Client(url) as client:
            result = await client.call_tool(
                "soccer_route_and_call",
                {
                    "question": request.question,
                    "tool": request.tool,
                    "arguments": request.arguments or {},
                },
            )
            if hasattr(result, "data") and result.data is not None:
                return {"result": result.data}
            return {"result": result_to_str(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@_internal.get("/health")
async def soccer_internal_health() -> Dict[str, str]:
    return {"status": "ok", "service": "Soccer Proxy"}


# 내부 라우터는 register_router에서 prefix 없이 등록
internal_soccer_router = _internal
