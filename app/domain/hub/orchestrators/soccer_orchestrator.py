"""
Soccer Orchestrator — 축구 데이터 처리 워크플로우 통합 관리

LangGraph를 사용하여 Policy 기반과 Rule 기반을 자동 판단하여 처리합니다.

포함된 오케스트레이터:
  - PlayerOrchestrator: 선수 데이터 (Policy/Rule 자동 판단)
  - StadiumOrchestrator: 경기장 데이터 (Rule 기반)
  - TeamOrchestrator: 팀 데이터 (Rule 기반)
  - ScheduleOrchestrator: 경기 일정 데이터 (Rule 기반)

워크플로우:
  Validate → [에러 있음] → ErrorHandler → DetermineStrategy
  Validate → [에러 없음] → DetermineStrategy
  DetermineStrategy → [Policy/Rule] → Process → Save → Finalize
"""

import json
import logging
import uuid
from typing import Any, Dict, List, Optional

from langgraph.graph import END, StateGraph

from domain.models.states.soccer_state import EmbeddingSyncState, SoccerDataState  # type: ignore
from domain.spokes.soccer.agents.soccer_agent import PlayerAgent  # type: ignore
from domain.hub.service import (  # type: ignore
    PlayerService,
    ScheduleService,
    StadiumService,
    TeamService,
)

logger = logging.getLogger(__name__)


# =============================================================================
# 공통 그래프 노드 (Validate → ErrorHandler → Save → Retry/Finalize)
# =============================================================================


def validate_node(state: SoccerDataState) -> SoccerDataState:
    """입력 데이터 검증 — validated_data 설정 또는 errors 설정."""
    data = state.get("data", [])
    path = state.get("processing_path", "Start")
    if not isinstance(data, list):
        return {"errors": [{"error": "data는 리스트여야 합니다"}], "processing_path": path + " -> Validate"}
    if not data:
        return {"errors": [{"error": "data가 비어 있습니다"}], "processing_path": path + " -> Validate"}
    return {"validated_data": data, "processing_path": path + " -> Validate"}


def error_handler_node(state: SoccerDataState) -> SoccerDataState:
    """검증 오류 로깅 후 다음 단계로 진행."""
    errors = state.get("errors", [])
    path = state.get("processing_path", "Start")
    for e in errors:
        logger.warning("[ErrorHandler] %s", e.get("error", e))
    return {"processing_path": path + " -> ErrorHandler"}


def save_node(state: SoccerDataState) -> SoccerDataState:
    """transformed_data를 data_type에 맞는 Service로 저장."""
    transformed = state.get("transformed_data") or state.get("validated_data") or []
    db = state.get("db")
    data_type = (state.get("data_type") or "").rstrip("s")  # "players" -> "player"
    path = state.get("processing_path", "Start")
    auto_commit = state.get("auto_commit", True)
    if not db or not transformed:
        return {"saved_count": 0, "save_failed": False, "processing_path": path + " -> Save"}
    services = {
        "player": PlayerService(),
        "schedule": ScheduleService(),
        "stadium": StadiumService(),
        "team": TeamService(),
    }
    svc = services.get(data_type)
    if not svc:
        return {
            "save_failed": True,
            "processing_path": path + " -> Save",
            "errors": (state.get("errors") or []) + [{"error": f"알 수 없는 data_type: {state.get('data_type')}"}],
        }
    try:
        result = svc.process(data=transformed, db=db, vector_store=None, auto_commit=auto_commit)
        saved = result.get("db", 0)
        return {"saved_count": saved, "save_failed": False, "processing_path": path + " -> Save"}
    except Exception as e:
        logger.exception("Save 실패: %s", e)
        return {
            "save_failed": True,
            "processing_path": path + " -> Save",
            "errors": (state.get("errors") or []) + [{"error": str(e)}],
        }


def retry_save_node(state: SoccerDataState) -> SoccerDataState:
    """재시도 횟수만 증가시키고 다시 Save로 보냄."""
    count = state.get("save_retry_count", 0) + 1
    return {"save_retry_count": count}


def finalize_node(state: SoccerDataState) -> SoccerDataState:
    """최종 result 구성 (호출 측에서 db commit 등에 사용)."""
    saved = state.get("saved_count") or 0
    path = state.get("processing_path", "Start")
    strategy = state.get("decided_strategy", "rule")
    return {
        "result": {"db": saved, "vector": 0, "processed": saved, "total": len(state.get("data") or [])},
        "processing_path": path + " -> Finalize",
        "decided_strategy": strategy,
        "db": state.get("db"),
    }


# =============================================================================
# 공통 유틸리티
# =============================================================================


def _log_preview_data(orchestrator_name: str, preview_data: List[Dict[str, Any]]) -> None:
    """미리보기 데이터(상위 5개)를 로그로 출력합니다."""
    logger.info("=" * 80)
    logger.info(f"[{orchestrator_name}] 상위 5개 데이터 미리보기")
    logger.info("=" * 80)

    for idx, item in enumerate(preview_data, 1):
        row_num = item.get("row", idx)
        logger.info(f"\n[데이터 {idx}/{len(preview_data)}] (행 {row_num})")
        try:
            if "data" in item:
                formatted_json = json.dumps(item["data"], ensure_ascii=False, indent=2)
                logger.info(formatted_json)
            elif "error" in item:
                logger.warning(f"에러: {item.get('error')}")
            else:
                formatted_json = json.dumps(item, ensure_ascii=False, indent=2)
                logger.info(formatted_json)
        except Exception as e:
            logger.warning(f"데이터 {idx} 출력 중 오류: {str(e)}")
            logger.info(f"원본 데이터: {str(item)[:200]}...")

    logger.info("=" * 80)


def _handle_graph_result(
    orchestrator_name: str,
    result: SoccerDataState,
    data_len: int,
) -> Dict[str, Any]:
    """그래프 실행 결과를 처리하고 트랜잭션을 커밋합니다."""
    db_session = result.get("db")
    if db_session is not None:
        try:
            db_session.commit()
        except Exception as commit_err:
            db_session.rollback()
            logger.error(f"[{orchestrator_name}] commit 실패: %s", commit_err)
            return {
                "success": False,
                "result": result.get("result", {}),
                "processing_path": result.get("processing_path", ""),
                "decided_strategy": result.get("decided_strategy", "rule"),
                "error": str(commit_err),
            }

    final_result = result.get("result", {})
    processing_path = result.get("processing_path", "")
    decided_strategy = result.get("decided_strategy", "rule")

    logger.info(f"[{orchestrator_name}] 처리 완료: {final_result}")

    return {
        "success": True,
        "result": final_result,
        "processing_path": processing_path,
        "decided_strategy": decided_strategy,
    }


def _handle_graph_error(
    orchestrator_name: str,
    error: Exception,
    data_len: int,
) -> Dict[str, Any]:
    """그래프 실행 오류를 처리합니다."""
    logger.error(f"[{orchestrator_name}] 처리 실패: {str(error)}")
    import traceback
    traceback.print_exc()

    return {
        "success": False,
        "result": {
            "processed": 0,
            "db": 0,
            "vector": 0,
            "total": data_len,
            "errors": [{"error": f"그래프 실행 오류: {str(error)}"}],
        },
        "processing_path": "Error",
        "decided_strategy": "rule",
        "error": str(error),
    }


# =============================================================================
# 1) Player Orchestrator — Policy/Rule 자동 판단
# =============================================================================


def _player_determine_strategy_node(state: SoccerDataState) -> SoccerDataState:
    """Player 전략 판단 노드 — 데이터 복잡도에 따라 Policy/Rule 결정."""
    validated_data = state.get("validated_data", [])
    processing_path = state.get("processing_path", "Start")

    logger.info(f"[Player:DetermineStrategy] 전략 판단 시작: {len(validated_data)}개 데이터")

    # 기본적으로 Rule 기반 사용 (휴리스틱 처리)
    # 향후 LLM 기반 판단으로 확장 가능
    decided_strategy = "rule"

    logger.info(f"[Player:DetermineStrategy] 결정된 전략: {decided_strategy}")

    return {
        "decided_strategy": decided_strategy,
        "processing_path": processing_path + " -> DetermineStrategy",
    }


def _player_policy_process_node(state: SoccerDataState) -> SoccerDataState:
    """Player Policy 기반 처리 노드 — PlayerAgent(LLM) 사용."""
    validated_data = state.get("validated_data", [])
    vector_store = state.get("vector_store")
    processing_path = state.get("processing_path", "Start")

    logger.info(f"[Player:PolicyProcess] Policy 기반 처리 시작: {len(validated_data)}개 데이터")

    try:
        agent = PlayerAgent()
        result = agent.process(
            data=validated_data,
            db=None,
            vector_store=vector_store,
        )

        logger.info(f"[Player:PolicyProcess] Policy 기반 처리 완료: {result}")

        return {
            "transformed_data": validated_data,
            "saved_count": result.get("vector", 0),
            "processing_path": processing_path + " -> PolicyProcess",
        }
    except Exception as e:
        logger.error(f"[Player:PolicyProcess] 처리 중 오류: {str(e)}")
        errors = state.get("errors", [])
        errors.append({"error": f"Policy 기반 처리 실패: {str(e)}"})
        return {
            "errors": errors,
            "processing_path": processing_path + " -> PolicyProcess(Error)",
        }


def _player_rule_process_node(state: SoccerDataState) -> SoccerDataState:
    """Player Rule 기반 처리 노드 — PlayerService 사용."""
    validated_data = state.get("validated_data", [])
    db = state.get("db")
    processing_path = state.get("processing_path", "Start")

    logger.info(f"[Player:RuleProcess] Rule 기반 처리 시작: {len(validated_data)}개 데이터")

    try:
        service = PlayerService()
        result = service.process(
            data=validated_data,
            db=db,
            vector_store=None,
            auto_commit=state.get("auto_commit", True),
        )

        logger.info(f"[Player:RuleProcess] Rule 기반 처리 완료: {result}")

        return {
            "transformed_data": validated_data,
            "saved_count": result.get("db", 0),
            "processing_path": processing_path + " -> RuleProcess",
        }
    except Exception as e:
        logger.error(f"[Player:RuleProcess] 처리 중 오류: {str(e)}")
        errors = state.get("errors", [])
        errors.append({"error": f"Rule 기반 처리 실패: {str(e)}"})
        return {
            "errors": errors,
            "processing_path": processing_path + " -> RuleProcess(Error)",
        }


def _player_route_strategy(state: SoccerDataState) -> str:
    """Player 전략 라우팅 — Policy 또는 Rule."""
    decided_strategy = state.get("decided_strategy", "rule")
    return "policy_process" if decided_strategy == "policy" else "rule_process"


def build_player_graph():
    """Player 데이터 처리 Graph 빌드."""
    g = StateGraph(SoccerDataState)

    g.add_node("validate", validate_node)
    g.add_node("error_handler", error_handler_node)
    g.add_node("determine_strategy", _player_determine_strategy_node)
    g.add_node("policy_process", _player_policy_process_node)
    g.add_node("rule_process", _player_rule_process_node)
    g.add_node("save", save_node)
    g.add_node("retry_save", retry_save_node)
    g.add_node("finalize", finalize_node)

    g.set_entry_point("validate")

    def route_after_validate(state: SoccerDataState) -> str:
        errors = state.get("errors", [])
        return "error_handler" if errors else "determine_strategy"

    g.add_conditional_edges(
        "validate",
        route_after_validate,
        {"error_handler": "error_handler", "determine_strategy": "determine_strategy"},
    )
    g.add_edge("error_handler", "determine_strategy")
    g.add_conditional_edges(
        "determine_strategy",
        _player_route_strategy,
        {"policy_process": "policy_process", "rule_process": "rule_process"},
    )
    g.add_edge("policy_process", "save")
    g.add_edge("rule_process", "save")

    def route_after_save(state: SoccerDataState) -> str:
        save_failed = state.get("save_failed", False)
        save_retry_count = state.get("save_retry_count", 0)
        return "retry_save" if save_failed and save_retry_count < 3 else "finalize"

    g.add_conditional_edges(
        "save",
        route_after_save,
        {"retry_save": "retry_save", "finalize": "finalize"},
    )
    g.add_edge("retry_save", "save")
    g.add_edge("finalize", END)

    return g.compile()


_player_graph: Any = None


def get_player_graph():
    """Player 그래프 인스턴스 반환 (lazy loading)."""
    global _player_graph
    if _player_graph is None:
        _player_graph = build_player_graph()
    return _player_graph


class PlayerOrchestrator:
    """선수 데이터 처리 오케스트레이터 — Policy/Rule 자동 판단."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def process(
        self,
        data: List[Dict[str, Any]],
        preview_data: List[Dict[str, Any]],
        db=None,
        vector_store=None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Player 데이터를 LangGraph로 처리합니다."""
        self.logger.info(
            f"[PlayerOrchestrator] LangGraph 처리 시작: 전체 {len(data)}개, 미리보기 {len(preview_data)}개"
        )

        _log_preview_data("PlayerOrchestrator", preview_data)

        initial_state: SoccerDataState = {
            "data": data,
            "preview_data": preview_data,
            "data_type": "players",
            "validated_data": None,
            "transformed_data": None,
            "saved_count": None,
            "result": None,
            "errors": None,
            "processing_path": "Start",
            "decided_strategy": None,
            "db": db,
            "vector_store": vector_store,
            "save_retry_count": 0,
            "save_failed": False,
            "auto_commit": False,
        }

        config = {"configurable": {"thread_id": f"player_{uuid.uuid4().hex[:8]}"}}

        try:
            graph = get_player_graph()
            result: SoccerDataState = graph.invoke(initial_state, config=config)
            return _handle_graph_result("PlayerOrchestrator", result, len(data))
        except Exception as e:
            return _handle_graph_error("PlayerOrchestrator", e, len(data))


# =============================================================================
# 2) Stadium Orchestrator — Rule 기반 전용
# =============================================================================


def _stadium_determine_strategy_node(state: SoccerDataState) -> SoccerDataState:
    """Stadium 전략 판단 노드 — 항상 Rule 기반."""
    processing_path = state.get("processing_path", "Start")
    logger.info("[Stadium:DetermineStrategy] Stadium은 항상 Rule 기반 사용")
    return {
        "decided_strategy": "rule",
        "processing_path": processing_path + " -> DetermineStrategy",
    }


def _stadium_rule_process_node(state: SoccerDataState) -> SoccerDataState:
    """Stadium Rule 기반 처리 노드 — StadiumService 사용."""
    validated_data = state.get("validated_data", [])
    db = state.get("db")
    processing_path = state.get("processing_path", "Start")

    logger.info(f"[Stadium:RuleProcess] Rule 기반 처리 시작: {len(validated_data)}개 데이터")

    try:
        service = StadiumService()
        result = service.process(
            data=validated_data,
            db=db,
            vector_store=None,
            auto_commit=state.get("auto_commit", True),
        )

        logger.info(f"[Stadium:RuleProcess] Rule 기반 처리 완료: {result}")

        return {
            "transformed_data": validated_data,
            "saved_count": result.get("db", 0),
            "processing_path": processing_path + " -> RuleProcess",
        }
    except Exception as e:
        logger.error(f"[Stadium:RuleProcess] 처리 중 오류: {str(e)}")
        errors = state.get("errors", [])
        errors.append({"error": f"Rule 기반 처리 실패: {str(e)}"})
        return {
            "errors": errors,
            "processing_path": processing_path + " -> RuleProcess(Error)",
        }


def _stadium_route_strategy(state: SoccerDataState) -> str:
    """Stadium 전략 라우팅 — 항상 Rule."""
    return "rule_process"


def build_stadium_graph():
    """Stadium 데이터 처리 Graph 빌드."""
    g = StateGraph(SoccerDataState)

    g.add_node("validate", validate_node)
    g.add_node("error_handler", error_handler_node)
    g.add_node("determine_strategy", _stadium_determine_strategy_node)
    g.add_node("rule_process", _stadium_rule_process_node)
    g.add_node("save", save_node)
    g.add_node("retry_save", retry_save_node)
    g.add_node("finalize", finalize_node)

    g.set_entry_point("validate")

    def route_after_validate(state: SoccerDataState) -> str:
        errors = state.get("errors", [])
        return "error_handler" if errors else "determine_strategy"

    g.add_conditional_edges(
        "validate",
        route_after_validate,
        {"error_handler": "error_handler", "determine_strategy": "determine_strategy"},
    )
    g.add_edge("error_handler", "determine_strategy")
    g.add_conditional_edges(
        "determine_strategy",
        _stadium_route_strategy,
        {"rule_process": "rule_process"},
    )
    g.add_edge("rule_process", "save")

    def route_after_save(state: SoccerDataState) -> str:
        save_failed = state.get("save_failed", False)
        save_retry_count = state.get("save_retry_count", 0)
        return "retry_save" if save_failed and save_retry_count < 3 else "finalize"

    g.add_conditional_edges(
        "save",
        route_after_save,
        {"retry_save": "retry_save", "finalize": "finalize"},
    )
    g.add_edge("retry_save", "save")
    g.add_edge("finalize", END)

    return g.compile()


_stadium_graph: Any = None


def get_stadium_graph():
    """Stadium 그래프 인스턴스 반환 (lazy loading)."""
    global _stadium_graph
    if _stadium_graph is None:
        _stadium_graph = build_stadium_graph()
    return _stadium_graph


class StadiumOrchestrator:
    """경기장 데이터 처리 오케스트레이터 — Rule 기반 전용."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def process(
        self,
        data: List[Dict[str, Any]],
        preview_data: List[Dict[str, Any]],
        db=None,
        vector_store=None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Stadium 데이터를 LangGraph로 처리합니다."""
        self.logger.info(
            f"[StadiumOrchestrator] LangGraph 처리 시작: 전체 {len(data)}개, 미리보기 {len(preview_data)}개"
        )

        _log_preview_data("StadiumOrchestrator", preview_data)

        initial_state: SoccerDataState = {
            "data": data,
            "preview_data": preview_data,
            "data_type": "stadiums",
            "validated_data": None,
            "transformed_data": None,
            "saved_count": None,
            "result": None,
            "errors": None,
            "processing_path": "Start",
            "decided_strategy": None,
            "db": db,
            "vector_store": vector_store,
            "save_retry_count": 0,
            "save_failed": False,
            "auto_commit": False,
        }

        config = {"configurable": {"thread_id": f"stadium_{uuid.uuid4().hex[:8]}"}}

        try:
            graph = get_stadium_graph()
            result: SoccerDataState = graph.invoke(initial_state, config=config)
            return _handle_graph_result("StadiumOrchestrator", result, len(data))
        except Exception as e:
            return _handle_graph_error("StadiumOrchestrator", e, len(data))


# =============================================================================
# 3) Team Orchestrator — Rule 기반 전용
# =============================================================================


def _team_determine_strategy_node(state: SoccerDataState) -> SoccerDataState:
    """Team 전략 판단 노드 — 항상 Rule 기반."""
    processing_path = state.get("processing_path", "Start")
    logger.info("[Team:DetermineStrategy] Team은 항상 Rule 기반 사용")
    return {
        "decided_strategy": "rule",
        "processing_path": processing_path + " -> DetermineStrategy",
    }


def _team_rule_process_node(state: SoccerDataState) -> SoccerDataState:
    """Team Rule 기반 처리 노드 — TeamService 사용."""
    validated_data = state.get("validated_data", [])
    db = state.get("db")
    processing_path = state.get("processing_path", "Start")

    logger.info(f"[Team:RuleProcess] Rule 기반 처리 시작: {len(validated_data)}개 데이터")

    try:
        service = TeamService()
        result = service.process(
            data=validated_data,
            db=db,
            vector_store=None,
            auto_commit=state.get("auto_commit", True),
        )

        logger.info(f"[Team:RuleProcess] Rule 기반 처리 완료: {result}")

        return {
            "transformed_data": validated_data,
            "saved_count": result.get("db", 0),
            "processing_path": processing_path + " -> RuleProcess",
        }
    except Exception as e:
        logger.error(f"[Team:RuleProcess] 처리 중 오류: {str(e)}")
        errors = state.get("errors", [])
        errors.append({"error": f"Rule 기반 처리 실패: {str(e)}"})
        return {
            "errors": errors,
            "processing_path": processing_path + " -> RuleProcess(Error)",
        }


def _team_route_strategy(state: SoccerDataState) -> str:
    """Team 전략 라우팅 — 항상 Rule."""
    return "rule_process"


def build_team_graph():
    """Team 데이터 처리 Graph 빌드."""
    g = StateGraph(SoccerDataState)

    g.add_node("validate", validate_node)
    g.add_node("error_handler", error_handler_node)
    g.add_node("determine_strategy", _team_determine_strategy_node)
    g.add_node("rule_process", _team_rule_process_node)
    g.add_node("save", save_node)
    g.add_node("retry_save", retry_save_node)
    g.add_node("finalize", finalize_node)

    g.set_entry_point("validate")

    def route_after_validate(state: SoccerDataState) -> str:
        errors = state.get("errors", [])
        return "error_handler" if errors else "determine_strategy"

    g.add_conditional_edges(
        "validate",
        route_after_validate,
        {"error_handler": "error_handler", "determine_strategy": "determine_strategy"},
    )
    g.add_edge("error_handler", "determine_strategy")
    g.add_conditional_edges(
        "determine_strategy",
        _team_route_strategy,
        {"rule_process": "rule_process"},
    )
    g.add_edge("rule_process", "save")

    def route_after_save(state: SoccerDataState) -> str:
        save_failed = state.get("save_failed", False)
        save_retry_count = state.get("save_retry_count", 0)
        return "retry_save" if save_failed and save_retry_count < 3 else "finalize"

    g.add_conditional_edges(
        "save",
        route_after_save,
        {"retry_save": "retry_save", "finalize": "finalize"},
    )
    g.add_edge("retry_save", "save")
    g.add_edge("finalize", END)

    return g.compile()


_team_graph: Any = None


def get_team_graph():
    """Team 그래프 인스턴스 반환 (lazy loading)."""
    global _team_graph
    if _team_graph is None:
        _team_graph = build_team_graph()
    return _team_graph


class TeamOrchestrator:
    """팀 데이터 처리 오케스트레이터 — Rule 기반 전용."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def process(
        self,
        data: List[Dict[str, Any]],
        preview_data: List[Dict[str, Any]],
        db=None,
        vector_store=None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Team 데이터를 LangGraph로 처리합니다."""
        self.logger.info(
            f"[TeamOrchestrator] LangGraph 처리 시작: 전체 {len(data)}개, 미리보기 {len(preview_data)}개"
        )

        _log_preview_data("TeamOrchestrator", preview_data)

        initial_state: SoccerDataState = {
            "data": data,
            "preview_data": preview_data,
            "data_type": "teams",
            "validated_data": None,
            "transformed_data": None,
            "saved_count": None,
            "result": None,
            "errors": None,
            "processing_path": "Start",
            "decided_strategy": None,
            "db": db,
            "vector_store": vector_store,
            "save_retry_count": 0,
            "save_failed": False,
            "auto_commit": False,
        }

        config = {"configurable": {"thread_id": f"team_{uuid.uuid4().hex[:8]}"}}

        try:
            graph = get_team_graph()
            result: SoccerDataState = graph.invoke(initial_state, config=config)
            return _handle_graph_result("TeamOrchestrator", result, len(data))
        except Exception as e:
            return _handle_graph_error("TeamOrchestrator", e, len(data))


# =============================================================================
# 4) Schedule Orchestrator — Rule 기반 전용
# =============================================================================


def _schedule_determine_strategy_node(state: SoccerDataState) -> SoccerDataState:
    """Schedule 전략 판단 노드 — 항상 Rule 기반."""
    processing_path = state.get("processing_path", "Start")
    logger.info("[Schedule:DetermineStrategy] Schedule은 항상 Rule 기반 사용")
    return {
        "decided_strategy": "rule",
        "processing_path": processing_path + " -> DetermineStrategy",
    }


def _schedule_rule_process_node(state: SoccerDataState) -> SoccerDataState:
    """Schedule Rule 기반 처리 노드 — ScheduleService 사용."""
    validated_data = state.get("validated_data", [])
    db = state.get("db")
    processing_path = state.get("processing_path", "Start")

    logger.info(f"[Schedule:RuleProcess] Rule 기반 처리 시작: {len(validated_data)}개 데이터")

    try:
        service = ScheduleService()
        result = service.process(
            data=validated_data,
            db=db,
            vector_store=None,
            auto_commit=state.get("auto_commit", True),
        )

        logger.info(f"[Schedule:RuleProcess] Rule 기반 처리 완료: {result}")

        return {
            "transformed_data": validated_data,
            "saved_count": result.get("db", 0),
            "processing_path": processing_path + " -> RuleProcess",
        }
    except Exception as e:
        logger.error(f"[Schedule:RuleProcess] 처리 중 오류: {str(e)}")
        errors = state.get("errors", [])
        errors.append({"error": f"Rule 기반 처리 실패: {str(e)}"})
        return {
            "errors": errors,
            "processing_path": processing_path + " -> RuleProcess(Error)",
        }


def _schedule_route_strategy(state: SoccerDataState) -> str:
    """Schedule 전략 라우팅 — 항상 Rule."""
    return "rule_process"


def build_schedule_graph():
    """Schedule 데이터 처리 Graph 빌드."""
    g = StateGraph(SoccerDataState)

    g.add_node("validate", validate_node)
    g.add_node("error_handler", error_handler_node)
    g.add_node("determine_strategy", _schedule_determine_strategy_node)
    g.add_node("rule_process", _schedule_rule_process_node)
    g.add_node("save", save_node)
    g.add_node("retry_save", retry_save_node)
    g.add_node("finalize", finalize_node)

    g.set_entry_point("validate")

    def route_after_validate(state: SoccerDataState) -> str:
        errors = state.get("errors", [])
        return "error_handler" if errors else "determine_strategy"

    g.add_conditional_edges(
        "validate",
        route_after_validate,
        {"error_handler": "error_handler", "determine_strategy": "determine_strategy"},
    )
    g.add_edge("error_handler", "determine_strategy")
    g.add_conditional_edges(
        "determine_strategy",
        _schedule_route_strategy,
        {"rule_process": "rule_process"},
    )
    g.add_edge("rule_process", "save")

    def route_after_save(state: SoccerDataState) -> str:
        save_failed = state.get("save_failed", False)
        save_retry_count = state.get("save_retry_count", 0)
        return "retry_save" if save_failed and save_retry_count < 3 else "finalize"

    g.add_conditional_edges(
        "save",
        route_after_save,
        {"retry_save": "retry_save", "finalize": "finalize"},
    )
    g.add_edge("retry_save", "save")
    g.add_edge("finalize", END)

    return g.compile()


_schedule_graph: Any = None


def get_schedule_graph():
    """Schedule 그래프 인스턴스 반환 (lazy loading)."""
    global _schedule_graph
    if _schedule_graph is None:
        _schedule_graph = build_schedule_graph()
    return _schedule_graph


class ScheduleOrchestrator:
    """경기 일정 데이터 처리 오케스트레이터 — Rule 기반 전용."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def process(
        self,
        data: List[Dict[str, Any]],
        preview_data: List[Dict[str, Any]],
        db=None,
        vector_store=None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Schedule 데이터를 LangGraph로 처리합니다."""
        self.logger.info(
            f"[ScheduleOrchestrator] LangGraph 처리 시작: 전체 {len(data)}개, 미리보기 {len(preview_data)}개"
        )

        _log_preview_data("ScheduleOrchestrator", preview_data)

        initial_state: SoccerDataState = {
            "data": data,
            "preview_data": preview_data,
            "data_type": "schedules",
            "validated_data": None,
            "transformed_data": None,
            "saved_count": None,
            "result": None,
            "errors": None,
            "processing_path": "Start",
            "decided_strategy": None,
            "db": db,
            "vector_store": vector_store,
            "save_retry_count": 0,
            "save_failed": False,
            "auto_commit": False,
        }

        config = {"configurable": {"thread_id": f"schedule_{uuid.uuid4().hex[:8]}"}}

        try:
            graph = get_schedule_graph()
            result: SoccerDataState = graph.invoke(initial_state, config=config)
            return _handle_graph_result("ScheduleOrchestrator", result, len(data))
        except Exception as e:
            return _handle_graph_error("ScheduleOrchestrator", e, len(data))


# =============================================================================
# 5) Embedding Sync — LangGraph (Validate → ProcessEntity 반복 → Finalize)
# =============================================================================

EMBEDDING_SYNC_ENTITY_TYPES = ["players", "teams", "schedules", "stadiums"]


def _embedding_sync_validate_node(state: EmbeddingSyncState) -> EmbeddingSyncState:
    entities = state.get("entities") or list(EMBEDDING_SYNC_ENTITY_TYPES)
    valid = [e for e in entities if e in EMBEDDING_SYNC_ENTITY_TYPES]
    if not valid:
        valid = list(EMBEDDING_SYNC_ENTITY_TYPES)
    path = state.get("processing_path", "Start")
    logger.info("[EmbeddingSync] Validate entities=%s", valid)
    return {
        "entities": valid,
        "results": state.get("results") or {},
        "current_entity_index": 0,
        "processing_path": path + " -> Validate",
    }


def _embedding_sync_process_entity_node(state: EmbeddingSyncState) -> EmbeddingSyncState:
    from domain.spokes.soccer.services.embedding_service import (  # type: ignore
        run_embedding_sync_single_entity,
    )

    entities = state.get("entities") or []
    idx = state.get("current_entity_index", 0)
    results = dict(state.get("results") or {})
    path = state.get("processing_path", "Start")
    db = state.get("db")
    embeddings_model = state.get("embeddings_model")
    batch_size = state.get("batch_size", 32)

    if idx >= len(entities) or not db or not embeddings_model:
        return {"processing_path": path + " -> ProcessEntity(skip)", "results": results}

    table_key = entities[idx]
    logger.info("[EmbeddingSync] ProcessEntity table_key=%s index=%s", table_key, idx)
    one_result = run_embedding_sync_single_entity(db, embeddings_model, table_key, batch_size=batch_size)
    results[table_key] = one_result
    return {
        "results": results,
        "current_entity_index": idx + 1,
        "processing_path": path + f" -> ProcessEntity({table_key})",
    }


def _embedding_sync_finalize_node(state: EmbeddingSyncState) -> EmbeddingSyncState:
    path = state.get("processing_path", "Start")
    results = state.get("results") or {}
    logger.info("[EmbeddingSync] Finalize results=%s", results)
    return {"processing_path": path + " -> Finalize"}


def _embedding_sync_route_after_process(state: EmbeddingSyncState) -> str:
    entities = state.get("entities") or []
    idx = state.get("current_entity_index", 0)
    return "process_entity" if idx < len(entities) else "finalize"


def build_embedding_sync_graph():
    g = StateGraph(EmbeddingSyncState)
    g.add_node("validate", _embedding_sync_validate_node)
    g.add_node("process_entity", _embedding_sync_process_entity_node)
    g.add_node("finalize", _embedding_sync_finalize_node)
    g.set_entry_point("validate")
    g.add_edge("validate", "process_entity")
    g.add_conditional_edges(
        "process_entity",
        _embedding_sync_route_after_process,
        {"process_entity": "process_entity", "finalize": "finalize"},
    )
    g.add_edge("finalize", END)
    return g.compile()


_embedding_sync_graph: Any = None


def get_embedding_sync_graph():
    global _embedding_sync_graph
    if _embedding_sync_graph is None:
        _embedding_sync_graph = build_embedding_sync_graph()
    return _embedding_sync_graph


def run_embedding_sync_orchestrate(
    db,
    embeddings_model: Any,
    entities: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    임베딩 동기화를 LangGraph로 실행.
    그래프: Validate → ProcessEntity(반복) → Finalize.
    """
    logger.info("[EmbeddingSyncOrchestrate] 임베딩 동기화 시작 entities=%s", entities)
    try:
        initial_state: EmbeddingSyncState = {
            "entities": entities or list(EMBEDDING_SYNC_ENTITY_TYPES),
            "db": db,
            "embeddings_model": embeddings_model,
            "batch_size": 32,
            "results": {},
            "current_entity_index": 0,
            "processing_path": "Start",
            "errors": None,
        }
        config = {"configurable": {"thread_id": f"embed_sync_{uuid.uuid4().hex[:8]}"}}
        graph = get_embedding_sync_graph()
        result_state: EmbeddingSyncState = graph.invoke(initial_state, config=config)
        results = result_state.get("results") or {}
        out = {"success": True, "results": results}
        logger.info("[EmbeddingSyncOrchestrate] 완료 results=%s", results)
        return out
    except Exception as e:
        logger.exception("[EmbeddingSyncOrchestrate] 실패: %s", e)
        raise
