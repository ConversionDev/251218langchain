"""선수 데이터 처리 Orchestrator

LangGraph를 사용하여 Policy 기반과 Rule 기반을 자동 판단하여 처리합니다.
"""

import json
import logging
import uuid
from typing import Any, Dict, List

from langgraph.graph import END, StateGraph

from domain.v10.soccer.hub.nodes import (  # type: ignore
    error_handler_node,
    finalize_node,
    retry_save_node,
    validate_node,
)
from domain.v10.soccer.models.states.player_state import PlayerProcessingState  # type: ignore
from domain.v10.soccer.spokes.agents.player_agent import PlayerAgent  # type: ignore
from domain.v10.soccer.spokes.services.player_service import PlayerService  # type: ignore

logger = logging.getLogger(__name__)


def _determine_strategy_node(state: PlayerProcessingState) -> Dict[str, Any]:
    """
    전략 판단 노드.

    데이터의 복잡도나 특성에 따라 Policy 기반 또는 Rule 기반을 결정합니다.
    현재는 간단한 휴리스틱으로 판단하지만, 향후 LLM 기반 판단으로 확장 가능합니다.

    Args:
        state: Player 처리 상태

    Returns:
        업데이트된 상태 (decided_strategy 포함)
    """
    validated_data = state.get("validated_data", [])
    processing_path = state.get("processing_path", "Start")

    logger.info(f"[DetermineStrategyNode] 전략 판단 시작: {len(validated_data)}개 데이터")

    # 간단한 휴리스틱: 데이터 복잡도나 에러율에 따라 판단
    # 향후 LLM 기반 판단으로 확장 가능
    # 현재는 기본적으로 Rule 기반 사용 (휴리스틱 처리)
    decided_strategy = "rule"

    # Policy 기반 판단 조건 (예시)
    # - 데이터에 불확실한 필드가 많을 때
    # - 복잡한 비즈니스 로직이 필요할 때
    # - 예외 케이스가 많을 때

    # Rule 기반 판단 조건 (기본)
    # - 명확한 규칙으로 처리 가능할 때
    # - 단순한 검증/변환이 필요할 때

    logger.info(f"[DetermineStrategyNode] 결정된 전략: {decided_strategy}")

    new_path = processing_path + " -> DetermineStrategy"

    return {
        "decided_strategy": decided_strategy,
        "processing_path": new_path,
    }


def _policy_process_node(state: PlayerProcessingState) -> Dict[str, Any]:
    """
    Policy 기반 처리 노드.

    PlayerAgent를 사용하여 LLM 기반 복잡한 비즈니스 로직을 처리합니다.

    Args:
        state: Player 처리 상태

    Returns:
        업데이트된 상태 (transformed_data, saved_count 포함)
    """
    validated_data = state.get("validated_data", [])
    vector_store = state.get("vector_store")
    processing_path = state.get("processing_path", "Start")

    logger.info(f"[PolicyProcessNode] Policy 기반 처리 시작: {len(validated_data)}개 데이터")

    try:
        agent = PlayerAgent()
        result = agent.process(
            data=validated_data,
            db=None,  # Policy 기반은 벡터 스토어만 사용
            vector_store=vector_store,
        )

        logger.info(f"[PolicyProcessNode] Policy 기반 처리 완료: {result}")

        new_path = processing_path + " -> PolicyProcess"

        return {
            "transformed_data": validated_data,  # Agent가 처리한 데이터
            "saved_count": result.get("vector", 0),  # 벡터 스토어 저장 개수
            "processing_path": new_path,
        }
    except Exception as e:
        logger.error(f"[PolicyProcessNode] 처리 중 오류: {str(e)}")
        errors = state.get("errors", [])
        errors.append({
            "error": f"Policy 기반 처리 실패: {str(e)}"
        })
        return {
            "errors": errors,
            "processing_path": processing_path + " -> PolicyProcess(Error)",
        }


def _rule_process_node(state: PlayerProcessingState) -> Dict[str, Any]:
    """
    Rule 기반 처리 노드.

    PlayerService를 사용하여 명확한 규칙에 따라 데이터를 처리합니다.

    Args:
        state: Player 처리 상태

    Returns:
        업데이트된 상태 (transformed_data, saved_count 포함)
    """
    validated_data = state.get("validated_data", [])
    db = state.get("db")
    processing_path = state.get("processing_path", "Start")

    logger.info(f"[RuleProcessNode] Rule 기반 처리 시작: {len(validated_data)}개 데이터")

    try:
        service = PlayerService()
        result = service.process(
            data=validated_data,
            db=db,
            vector_store=None,  # Rule 기반은 관계형 DB만 사용
        )

        logger.info(f"[RuleProcessNode] Rule 기반 처리 완료: {result}")

        new_path = processing_path + " -> RuleProcess"

        return {
            "transformed_data": validated_data,  # Service가 처리한 데이터
            "saved_count": result.get("db", 0),  # 관계형 DB 저장 개수
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


def _route_strategy(state: PlayerProcessingState) -> str:
    """
    전략 라우팅 함수.

    결정된 전략에 따라 Policy 또는 Rule 처리 노드로 라우팅합니다.

    Args:
        state: Player 처리 상태

    Returns:
        다음 노드 이름 ("policy_process" 또는 "rule_process")
    """
    decided_strategy = state.get("decided_strategy", "rule")

    if decided_strategy == "policy":
        return "policy_process"
    else:
        return "rule_process"


def build_player_graph():
    """
    Player 데이터 처리 Graph 빌드.

    워크플로우:
    - Validate → [에러 있음] → ErrorHandler → DetermineStrategy
    - Validate → [에러 없음] → DetermineStrategy
    - DetermineStrategy → [Policy/Rule] → Process → Finalize

    Returns:
        컴파일된 StateGraph
    """
    from domain.v10.soccer.hub.nodes.save_node import save_node  # type: ignore

    g = StateGraph(PlayerProcessingState)

    # 노드 추가
    g.add_node("validate", validate_node)
    g.add_node("error_handler", error_handler_node)
    g.add_node("determine_strategy", _determine_strategy_node)
    g.add_node("policy_process", _policy_process_node)
    g.add_node("rule_process", _rule_process_node)
    g.add_node("save", save_node)
    g.add_node("retry_save", retry_save_node)
    g.add_node("finalize", finalize_node)

    # 엔트리 포인트 설정
    g.set_entry_point("validate")

    # 조건부 라우팅: Validate → ErrorHandler 또는 DetermineStrategy
    def route_after_validate(state: PlayerProcessingState) -> str:
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

    # 조건부 라우팅: DetermineStrategy → Policy 또는 Rule 처리
    g.add_conditional_edges(
        "determine_strategy",
        _route_strategy,
        {
            "policy_process": "policy_process",
            "rule_process": "rule_process",
        }
    )

    # Policy/Rule 처리 → Save
    g.add_edge("policy_process", "save")
    g.add_edge("rule_process", "save")

    # 조건부 라우팅: Save → RetrySave 또는 Finalize
    def route_after_save(state: PlayerProcessingState) -> str:
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
_player_graph: Any = None


def get_player_graph():
    """
    Player 데이터 처리 그래프 인스턴스 반환 (lazy loading).

    Returns:
        컴파일된 StateGraph
    """
    global _player_graph
    if _player_graph is None:
        _player_graph = build_player_graph()
    return _player_graph


class PlayerOrchestrator:
    """선수 데이터 처리 오케스트레이터

    LangGraph를 사용하여 Policy 기반과 Rule 기반을 자동 판단하여 처리합니다.
    """

    def __init__(self):
        """PlayerOrchestrator 초기화"""
        self.logger = logging.getLogger(__name__)

    def _log_preview_data(self, preview_data: List[Dict[str, Any]]) -> None:
        """
        미리보기 데이터(상위 5개)를 로그로 출력합니다.

        Args:
            preview_data: 미리보기 데이터 리스트
        """
        self.logger.info("=" * 80)
        self.logger.info("[Orchestrator] 상위 5개 데이터 미리보기")
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
        LangGraph를 사용하여 Policy 기반과 Rule 기반을 자동 판단하여 처리합니다.

        Args:
            data: 처리할 전체 데이터 리스트
            preview_data: 미리보기 데이터 (로깅용)
            db: 데이터베이스 세션 (Rule 기반 저장용)
            vector_store: 벡터 스토어 (Policy 기반 저장용)
            **kwargs: 추가 파라미터

        Returns:
            처리 결과 딕셔너리
        """
        self.logger.info(f"[PlayerOrchestrator] LangGraph 처리 시작: 전체 {len(data)}개, 미리보기 {len(preview_data)}개")

        # 상위 5개 데이터 출력 (테스트용)
        self._log_preview_data(preview_data)

        # 그래프 가져오기
        graph = get_player_graph()

        # 초기 상태 구성
        initial_state: PlayerProcessingState = {
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
        }

        # 그래프 실행
        config = {"configurable": {"thread_id": f"player_{uuid.uuid4().hex[:8]}"}}

        try:
            result = graph.invoke(initial_state, config=config)

            # 결과 추출
            final_result = result.get("result", {})
            processing_path = result.get("processing_path", "")
            decided_strategy = result.get("decided_strategy", "rule")

            self.logger.info(f"[PlayerOrchestrator] 처리 완료: {final_result}")

            return {
                "success": True,
                "result": final_result,
                "processing_path": processing_path,
                "decided_strategy": decided_strategy,
            }
        except Exception as e:
            self.logger.error(f"[PlayerOrchestrator] 처리 실패: {str(e)}")
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
