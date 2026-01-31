"""팀 데이터 처리 Orchestrator

LangGraph를 사용하여 Rule 기반 처리만 수행합니다.
"""

import json
import logging
import uuid
from typing import Any, Dict, List

from langgraph.graph import END, StateGraph

from domain.v10.soccer.hub.processing import (  # type: ignore
    error_handler_node,
    finalize_node,
    retry_save_node,
    validate_node,
)
from domain.v10.soccer.models.states.team_state import TeamProcessingState  # type: ignore
from domain.v10.soccer.spokes.services.team_service import TeamService  # type: ignore

logger = logging.getLogger(__name__)


def _determine_strategy_node(state: TeamProcessingState) -> Dict[str, Any]:
    """
    전략 판단 노드.

    Team은 Agent가 없으므로 항상 Rule 기반을 사용합니다.

    Args:
        state: Team 처리 상태

    Returns:
        업데이트된 상태 (decided_strategy 포함)
    """
    processing_path = state.get("processing_path", "Start")

    logger.info("[DetermineStrategyNode] Team은 항상 Rule 기반 사용")

    decided_strategy = "rule"

    new_path = processing_path + " -> DetermineStrategy"

    return {
        "decided_strategy": decided_strategy,
        "processing_path": new_path,
    }


def _rule_process_node(state: TeamProcessingState) -> Dict[str, Any]:
    """
    Rule 기반 처리 노드.

    TeamService를 사용하여 명확한 규칙에 따라 데이터를 처리합니다.

    Args:
        state: Team 처리 상태

    Returns:
        업데이트된 상태 (transformed_data, saved_count 포함)
    """
    validated_data = state.get("validated_data", [])
    db = state.get("db")
    processing_path = state.get("processing_path", "Start")

    logger.info(f"[RuleProcessNode] Rule 기반 처리 시작: {len(validated_data)}개 데이터")

    try:
        service = TeamService()
        result = service.process(
            data=validated_data,
            db=db,
            vector_store=None,
            auto_commit=state.get("auto_commit", True),
        )

        logger.info(f"[RuleProcessNode] Rule 기반 처리 완료: {result}")

        new_path = processing_path + " -> RuleProcess"

        return {
            "transformed_data": validated_data,
            "saved_count": result.get("db", 0),
            "processing_path": new_path,
        }
    except Exception as e:
        logger.error(f"[RuleProcessNode] 처리 중 오류: {str(e)}")
        errors = state.get("errors", [])
        errors.append({
            "error": f"Rule 기반 처리 실패: {str(e)}"
        })
        return {
            "errors": errors,
            "processing_path": processing_path + " -> RuleProcess(Error)",
        }


def _route_strategy(state: TeamProcessingState) -> str:
    """
    전략 라우팅 함수.

    Team은 항상 Rule 기반만 사용합니다.

    Args:
        state: Team 처리 상태

    Returns:
        다음 노드 이름 ("rule_process")
    """
    return "rule_process"


def build_team_graph():
    """
    Team 데이터 처리 Graph 빌드.

    워크플로우:
    - Validate → [에러 있음] → ErrorHandler → DetermineStrategy → RuleProcess → Save → Finalize
    - Validate → [에러 없음] → DetermineStrategy → RuleProcess → Save → Finalize

    Returns:
        컴파일된 StateGraph
    """
    from domain.v10.soccer.hub.processing import save_node  # type: ignore

    g = StateGraph(TeamProcessingState)

    # 노드 추가
    g.add_node("validate", validate_node)
    g.add_node("error_handler", error_handler_node)
    g.add_node("determine_strategy", _determine_strategy_node)
    g.add_node("rule_process", _rule_process_node)
    g.add_node("save", save_node)
    g.add_node("retry_save", retry_save_node)
    g.add_node("finalize", finalize_node)

    # 엔트리 포인트 설정
    g.set_entry_point("validate")

    # 조건부 라우팅: Validate → ErrorHandler 또는 DetermineStrategy
    def route_after_validate(state: TeamProcessingState) -> str:
        """Validate 후 라우팅 결정"""
        errors = state.get("errors", [])
        if errors:
            return "error_handler"
        return "determine_strategy"

    g.add_conditional_edges(
        "validate",
        route_after_validate,
        {
            "error_handler": "error_handler",
            "determine_strategy": "determine_strategy",
        }
    )

    # ErrorHandler → DetermineStrategy
    g.add_edge("error_handler", "determine_strategy")

    # DetermineStrategy → RuleProcess
    g.add_conditional_edges(
        "determine_strategy",
        _route_strategy,
        {
            "rule_process": "rule_process",
        }
    )

    # RuleProcess → Save
    g.add_edge("rule_process", "save")

    # 조건부 라우팅: Save → RetrySave 또는 Finalize
    def route_after_save(state: TeamProcessingState) -> str:
        """Save 후 라우팅 결정"""
        save_failed = state.get("save_failed", False)
        save_retry_count = state.get("save_retry_count", 0)

        if save_failed and save_retry_count < 3:
            return "retry_save"
        return "finalize"

    g.add_conditional_edges(
        "save",
        route_after_save,
        {
            "retry_save": "retry_save",
            "finalize": "finalize",
        }
    )

    # RetrySave → Save
    g.add_edge("retry_save", "save")

    # Finalize → END
    g.add_edge("finalize", END)

    # 컴파일
    return g.compile()


# 그래프 인스턴스 캐시
_team_graph: Any = None


def get_team_graph():
    """
    Team 데이터 처리 그래프 인스턴스 반환 (lazy loading).

    Returns:
        컴파일된 StateGraph
    """
    global _team_graph
    if _team_graph is None:
        _team_graph = build_team_graph()
    return _team_graph


class TeamOrchestrator:
    """팀 데이터 처리 오케스트레이터

    LangGraph를 사용하여 Rule 기반 처리만 수행합니다.
    """

    def __init__(self):
        """TeamOrchestrator 초기화"""
        self.logger = logging.getLogger(__name__)

    def _log_preview_data(self, preview_data: List[Dict[str, Any]]) -> None:
        """
        미리보기 데이터(상위 5개)를 로그로 출력합니다.

        Args:
            preview_data: 미리보기 데이터 리스트
        """
        self.logger.info("=" * 80)
        self.logger.info("[TeamOrchestrator] 상위 5개 데이터 미리보기")
        self.logger.info("=" * 80)

        for idx, item in enumerate(preview_data, 1):
            row_num = item.get("row", idx)
            self.logger.info(f"\n[데이터 {idx}/{len(preview_data)}] (행 {row_num})")
            try:
                if "data" in item:
                    formatted_json = json.dumps(item["data"], ensure_ascii=False, indent=2)
                    self.logger.info(formatted_json)
                elif "error" in item:
                    self.logger.warning(f"에러: {item.get('error')}")
                else:
                    formatted_json = json.dumps(item, ensure_ascii=False, indent=2)
                    self.logger.info(formatted_json)
            except Exception as e:
                self.logger.warning(f"데이터 {idx} 출력 중 오류: {str(e)}")
                self.logger.info(f"원본 데이터: {str(item)[:200]}...")

        self.logger.info("=" * 80)

    def process(
        self,
        data: List[Dict[str, Any]],
        preview_data: List[Dict[str, Any]],
        db=None,
        vector_store=None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        데이터를 처리합니다.
        LangGraph를 사용하여 Rule 기반 처리만 수행합니다.

        Args:
            data: 처리할 전체 데이터 리스트
            preview_data: 미리보기 데이터 (로깅용)
            db: 데이터베이스 세션 (Rule 기반 저장용)
            vector_store: 벡터 스토어 (사용하지 않음)
            **kwargs: 추가 파라미터

        Returns:
            처리 결과 딕셔너리
        """
        self.logger.info(f"[TeamOrchestrator] LangGraph 처리 시작: 전체 {len(data)}개, 미리보기 {len(preview_data)}개")

        # 상위 5개 데이터 출력 (테스트용)
        self._log_preview_data(preview_data)

        # 그래프 가져오기
        graph = get_team_graph()

        # 초기 상태 구성
        initial_state: TeamProcessingState = {
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

        # 그래프 실행
        config = {"configurable": {"thread_id": f"team_{uuid.uuid4().hex[:8]}"}}

        try:
            result = graph.invoke(initial_state, config=config)

            # 트랜잭션: 그래프 내부는 auto_commit=False이므로 여기서 한 번만 commit
            db_session = result.get("db")
            if db_session is not None:
                try:
                    db_session.commit()
                except Exception as commit_err:
                    db_session.rollback()
                    self.logger.error("[TeamOrchestrator] commit 실패: %s", commit_err)
                    return {
                        "success": False,
                        "result": result.get("result", {}),
                        "processing_path": result.get("processing_path", ""),
                        "decided_strategy": result.get("decided_strategy", "rule"),
                        "error": str(commit_err),
                    }

            # 결과 추출
            final_result = result.get("result", {})
            processing_path = result.get("processing_path", "")
            decided_strategy = result.get("decided_strategy", "rule")

            self.logger.info(f"[TeamOrchestrator] 처리 완료: {final_result}")

            return {
                "success": True,
                "result": final_result,
                "processing_path": processing_path,
                "decided_strategy": decided_strategy,
            }
        except Exception as e:
            self.logger.error(f"[TeamOrchestrator] 처리 실패: {str(e)}")
            import traceback
            traceback.print_exc()

            return {
                "success": False,
                "result": {
                    "processed": 0,
                    "db": 0,
                    "vector": 0,
                    "total": len(data),
                    "errors": [{"error": f"그래프 실행 오류: {str(e)}"}],
                },
                "processing_path": "Error",
                "decided_strategy": "rule",
                "error": str(e),
            }
