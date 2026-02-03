"""
Soccer MCP Server (역할 통합).

- MCP: Central이 call_tool로 호출. 라우팅만 담당. Spoke로 call_tool 위임.
- Spoke: Soccer MCP가 call_tool로 호출. Player/Stadium/Team/Schedule 오케스트레이터 실행.
"""

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Literal

from fastmcp import FastMCP

from domain.hub.mcp.utils import get_soccer_spoke_mcp_url, result_to_str  # type: ignore

OrchestratorName = Literal["player", "schedule", "stadium", "team"]


# ---------------------------------------------------------------------------
# MCP (라우팅 + Spoke call_tool)
# ---------------------------------------------------------------------------

mcp_proxy = FastMCP("Soccer MCP Server (Routing + Spoke Proxy)")


@dataclass(frozen=True)
class RouteResult:
    orchestrator: OrchestratorName
    routed_by: str = "keywords"

    def to_dict(self) -> Dict[str, Any]:
        return {"orchestrator": self.orchestrator, "routed_by": self.routed_by}


def _route(question: str) -> RouteResult:
    q = (question or "").lower()
    player_keywords = [
        "선수", "player", "이름", "나이", "국적", "포지션", "키", "몸무게", "출생", "생년", "생일",
    ]
    schedule_keywords = ["일정", "schedule", "경기", "매치", "vs", "대전", "날짜", "시간"]
    stadium_keywords = ["경기장", "stadium", "구장", "아레나", "장소"]
    team_keywords = ["팀", "team", "클럽", "구단", "코드"]
    scores = {
        "player": sum(1 for k in player_keywords if k in q),
        "schedule": sum(1 for k in schedule_keywords if k in q),
        "stadium": sum(1 for k in stadium_keywords if k in q),
        "team": sum(1 for k in team_keywords if k in q),
    }
    max_score = max(scores.values()) if scores else 0
    selected: OrchestratorName = "player" if max_score == 0 else max(scores.keys(), key=lambda k: scores[k])  # type: ignore
    return RouteResult(orchestrator=selected, routed_by="keywords")


@mcp_proxy.tool
def soccer_route(question: str) -> str:
    """질문을 어느 오케스트레이터로 보낼지 결정(라우팅만)."""
    return json.dumps(_route(question).to_dict(), ensure_ascii=False)


@mcp_proxy.tool
async def soccer_call(
    orchestrator: OrchestratorName,
    tool: str,
    arguments: Dict[str, Any] | None = None,
) -> Any:
    """중앙 → Soccer Spoke call_tool 프록시."""
    from fastmcp.client import Client  # type: ignore
    async with Client(get_soccer_spoke_mcp_url()) as client:
        result = await client.call_tool(tool, arguments or {})
        if hasattr(result, "data") and result.data is not None:
            return result.data
        return {"content": result_to_str(result)}


@mcp_proxy.tool
async def soccer_route_and_call(
    question: str,
    tool: str,
    arguments: Dict[str, Any] | None = None,
) -> Any:
    """라우팅 후 Soccer Spoke call_tool까지 한 번에 수행."""
    return await soccer_call(_route(question).orchestrator, tool, arguments)


@mcp_proxy.tool
def server_health() -> str:
    """Soccer MCP 서버 헬스체크."""
    return json.dumps(
        {"status": "ok", "role": "routing_and_spoke_proxy", "spoke_url": get_soccer_spoke_mcp_url()},
        ensure_ascii=False,
    )


# ---------------------------------------------------------------------------
# Spoke (오케스트레이터 실행, BP: db=None이면 자체 세션 사용)
# ---------------------------------------------------------------------------

mcp_spoke = FastMCP("Soccer Spoke MCP (Orchestrator Execution)")


def _get_session_if_needed(db: Any) -> Any:
    """db가 None일 때 통합 DB 세션 생성 (BP: Spoke가 자체 세션으로 저장)."""
    if db is not None:
        return db
    try:
        from core.database import SessionLocal  # type: ignore
        return SessionLocal()
    except Exception:
        return None


def _process_player_impl(
    data: List[Dict[str, Any]],
    preview_data: List[Dict[str, Any]],
    db: Any = None,
    vector_store: Any = None,
) -> Dict[str, Any]:
    from domain.hub.orchestrators.soccer_orchestrator import PlayerOrchestrator  # type: ignore
    session = _get_session_if_needed(db)
    try:
        out = PlayerOrchestrator().process(data=data, preview_data=preview_data, db=session, vector_store=vector_store)
        if session is not None and session != db:
            session.commit()
        return out
    except Exception:
        if session is not None and session != db:
            session.rollback()
        raise
    finally:
        if session is not None and session != db:
            session.close()


def _process_stadium_impl(
    data: List[Dict[str, Any]],
    preview_data: List[Dict[str, Any]],
    db: Any = None,
    vector_store: Any = None,
) -> Dict[str, Any]:
    from domain.hub.orchestrators.soccer_orchestrator import StadiumOrchestrator  # type: ignore
    session = _get_session_if_needed(db)
    try:
        out = StadiumOrchestrator().process(data=data, preview_data=preview_data, db=session, vector_store=vector_store)
        if session is not None and session != db:
            session.commit()
        return out
    except Exception:
        if session is not None and session != db:
            session.rollback()
        raise
    finally:
        if session is not None and session != db:
            session.close()


def _process_team_impl(
    data: List[Dict[str, Any]],
    preview_data: List[Dict[str, Any]],
    db: Any = None,
    vector_store: Any = None,
) -> Dict[str, Any]:
    from domain.hub.orchestrators.soccer_orchestrator import TeamOrchestrator  # type: ignore
    session = _get_session_if_needed(db)
    try:
        out = TeamOrchestrator().process(data=data, preview_data=preview_data, db=session, vector_store=vector_store)
        if session is not None and session != db:
            session.commit()
        return out
    except Exception:
        if session is not None and session != db:
            session.rollback()
        raise
    finally:
        if session is not None and session != db:
            session.close()


def _process_schedule_impl(
    data: List[Dict[str, Any]],
    preview_data: List[Dict[str, Any]],
    db: Any = None,
    vector_store: Any = None,
) -> Dict[str, Any]:
    from domain.hub.orchestrators.soccer_orchestrator import ScheduleOrchestrator  # type: ignore
    session = _get_session_if_needed(db)
    try:
        out = ScheduleOrchestrator().process(data=data, preview_data=preview_data, db=session, vector_store=vector_store)
        if session is not None and session != db:
            session.commit()
        return out
    except Exception:
        if session is not None and session != db:
            session.rollback()
        raise
    finally:
        if session is not None and session != db:
            session.close()


@mcp_spoke.tool
def process_player(
    data: List[Dict[str, Any]],
    preview_data: List[Dict[str, Any]] | None = None,
) -> str:
    """선수 데이터 처리. Player 오케스트레이터 실행."""
    preview = preview_data or data[:5]
    result = _process_player_impl(data=data, preview_data=preview, db=None, vector_store=None)
    return json.dumps(result, ensure_ascii=False, default=str)


@mcp_spoke.tool
def process_stadium(
    data: List[Dict[str, Any]],
    preview_data: List[Dict[str, Any]] | None = None,
) -> str:
    """경기장 데이터 처리. Stadium 오케스트레이터 실행."""
    preview = preview_data or data[:5]
    result = _process_stadium_impl(data=data, preview_data=preview, db=None, vector_store=None)
    return json.dumps(result, ensure_ascii=False, default=str)


@mcp_spoke.tool
def process_team(
    data: List[Dict[str, Any]],
    preview_data: List[Dict[str, Any]] | None = None,
) -> str:
    """팀 데이터 처리. Team 오케스트레이터 실행."""
    preview = preview_data or data[:5]
    result = _process_team_impl(data=data, preview_data=preview, db=None, vector_store=None)
    return json.dumps(result, ensure_ascii=False, default=str)


@mcp_spoke.tool
def process_schedule(
    data: List[Dict[str, Any]],
    preview_data: List[Dict[str, Any]] | None = None,
) -> str:
    """경기 일정 데이터 처리. Schedule 오케스트레이터 실행."""
    preview = preview_data or data[:5]
    result = _process_schedule_impl(data=data, preview_data=preview, db=None, vector_store=None)
    return json.dumps(result, ensure_ascii=False, default=str)


# ---------------------------------------------------------------------------
# 진입점
# ---------------------------------------------------------------------------


def get_soccer_mcp() -> FastMCP:
    """Soccer MCP 앱 반환 (Central이 call_tool로 호출하는 대상)."""
    return mcp_proxy


def get_soccer_spoke_mcp() -> FastMCP:
    """Soccer Spoke MCP 앱 반환 (Soccer MCP가 call_tool로 호출하는 대상)."""
    return mcp_spoke
