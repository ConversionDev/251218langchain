"""
Spam Orchestrator — 스팸 감지 워크플로우 통합 관리

실행 흐름:
  1. Gateway (진입·분류) — LLaMA로 텍스트 정제, 규칙 vs 정책 라우팅 결정
  2. [분기] 규칙 → Final decision / 정책 → Policy (EXAONE) → Final decision
  3. Final decision — LLaMA 또는 EXAONE 결과를 action으로 최종 결정

구성:
  - SpamGatewayService: 진입 처리 (hub HTTP, rule vs policy 판단)
  - 유틸 함수: exaone 결과 변환, 에러 처리
  - 그래프 노드: gateway_node, policy_node, final_decision_node
  - 그래프 빌드/실행 API: build_spam_detection_graph, run_spam_detection
"""

import logging
import uuid
from typing import Any, Dict, Optional

from langgraph.graph import END, StateGraph

from domain.hub.mcp.http_client import llama_classify, llama_classify_spam  # type: ignore
from domain.hub.orchestrators.graph_orchestrator import get_checkpointer  # type: ignore
from domain.models import SpamDetectionState  # type: ignore
from domain.spokes.spam.services.rule_service import RuleService  # type: ignore

logger = logging.getLogger(__name__)


# =============================================================================
# 1) SpamGatewayService — 진입 처리 (hub HTTP, rule vs policy 판단)
# =============================================================================


class SpamGatewayService:
    """스팸 플로우 진입 처리.

    - 스팸 분류 (spam_prob) — hub HTTP
    - 규칙 기반 vs 정책 기반 판단 — hub HTTP (classify)
    """

    def __init__(self, rule_service: Optional[RuleService] = None):
        self._rule_service = rule_service or RuleService()

    def read(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """이메일 메타데이터를 읽고 분류·라우팅 전략 반환."""
        result_dict = self._classify_spam(data)
        routing_strategy = self._decide_routing_strategy(data)
        return {
            "email_metadata": data,
            "llama_result": result_dict,
            "routing_strategy": routing_strategy,
        }

    def _classify_spam(self, email_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """hub HTTP로 스팸 분류."""
        try:
            return llama_classify_spam(email_metadata)
        except Exception as e:
            logger.warning("LLaMA 스팸 분류 실패: %s", e)
        return {"spam_prob": 0.5, "confidence": "low", "label": "UNCERTAIN"}

    def _decide_routing_strategy(self, email_metadata: Dict[str, Any]) -> str:
        """hub HTTP(classify)로 규칙/정책 판단."""
        try:
            text = (
                f"제목: {email_metadata.get('subject', '')} "
                f"발신자: {email_metadata.get('sender', '')} "
                f"본문: {str(email_metadata.get('body', ''))[:200]}"
            )
            result = llama_classify(text)
            return "rule" if result == "RULE_BASED" else "policy"
        except Exception as e:
            logger.warning("hub classify 실패, RuleService 사용: %s", e)

        is_rule_based = self._rule_service.is_rule_based(email_metadata)
        return "rule" if is_rule_based else "policy"


# =============================================================================
# 2) 유틸 — exaone 결과 변환, 에러 처리
# =============================================================================


def _create_exaone_result_from_service_result(
    service_result: Dict[str, Any],
    analysis_text: Optional[str] = None,
    rule_based: bool = False,
    additional_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """서비스 결과를 exaone_result 형식으로 변환."""
    if analysis_text is None:
        analysis_text = service_result.get("analysis", "")
    exaone_result: Dict[str, Any] = {
        "raw_output": analysis_text,
        "parsed": {
            "is_spam": service_result.get("is_spam"),
            "action": service_result.get("action"),
            "confidence": service_result.get("confidence", "medium"),
            "analysis": analysis_text,
        },
        "risk_codes": service_result.get("reason_codes", []),
        "is_spam": service_result.get("is_spam"),
        "confidence": service_result.get("confidence", "medium"),
        "analysis": analysis_text,
        "rule_based": rule_based,
    }
    if additional_metadata:
        exaone_result.update(additional_metadata)
    return exaone_result


def _create_error_exaone_result(
    error: Exception,
    error_message: str,
    error_code: str,
    rule_based: bool = False,
) -> Dict[str, Any]:
    """에러 발생 시 exaone_result 형식으로 변환."""
    return {
        "raw_output": error_message,
        "parsed": {
            "is_spam": None,
            "action": "ask_user_confirm",
            "confidence": "low",
            "analysis": error_message,
        },
        "risk_codes": [error_code],
        "is_spam": None,
        "confidence": "low",
        "analysis": error_message,
        "error": str(error),
        "rule_based": rule_based,
    }


def _handle_node_error(
    error: Exception,
    node_name: str,
    routing_path: str,
    error_code: str,
    rule_based: bool = False,
) -> Dict[str, Any]:
    """노드 에러 처리 공통 로직."""
    logger.exception("%s 노드 오류: %s", node_name, error)
    error_message = f"{node_name} 기반 처리 중 오류 발생: {str(error)}"
    exaone_result = _create_error_exaone_result(
        error=error,
        error_message=error_message,
        error_code=error_code,
        rule_based=rule_based,
    )
    return {
        "exaone_result": exaone_result,
        "routing_path": routing_path + f" -> {node_name}Service(ERROR)",
    }


# =============================================================================
# 3) Gateway 노드 — 진입·분류 (LLaMA, 규칙/정책 라우팅 결정)
# =============================================================================

_gateway_service: Optional[SpamGatewayService] = None


def _get_gateway_service() -> SpamGatewayService:
    global _gateway_service
    if _gateway_service is None:
        _gateway_service = SpamGatewayService()
    return _gateway_service


def gateway_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """진입 노드: 게이트웨이 서비스로 텍스트 정제/추출 후 규칙 vs 정책 라우팅 결정."""
    email_metadata = state.get("email_metadata", {})
    routing_path = state.get("routing_path", "Start")
    try:
        gateway = _get_gateway_service()
        result = gateway.read(email_metadata)
        return {
            "email_metadata": result["email_metadata"],
            "llama_result": result["llama_result"],
            "routing_strategy": result.get("routing_strategy"),
            "routing_path": routing_path + " -> Gateway(LLaMA)",
        }
    except Exception as e:
        logger.exception("Gateway 노드 오류: %s", e)
        return {
            "llama_result": {
                "spam_prob": 0.5,
                "confidence": "low",
                "label": "UNCERTAIN",
            },
            "routing_path": routing_path + " -> Gateway(ERROR)",
        }


# =============================================================================
# 4) Policy 노드 — 정책 기반 처리 (EXAONE)
# =============================================================================


def policy_node(state: SpamDetectionState) -> Dict[str, Any]:
    """정책 노드: Policy Service(EXAONE)로 분석 후 exaone_result 반환."""
    from domain.spokes.spam.services.policy_service import PolicyService  # type: ignore

    email_metadata = state.get("email_metadata", {})
    routing_path = state.get("routing_path", "Start")
    try:
        policy_service = PolicyService()
        policy_result = policy_service.process(email_metadata, use_existing_policy=True)
        analysis_text = policy_result.get("analysis", "")
        exaone_result = _create_exaone_result_from_service_result(
            service_result=policy_result,
            analysis_text=analysis_text,
            rule_based=False,
            additional_metadata={"policy_id": policy_result.get("policy_id")},
        )
        return {
            "exaone_result": exaone_result,
            "routing_path": routing_path + " -> PolicyService(EXAONE)",
        }
    except Exception as e:
        return _handle_node_error(
            error=e,
            node_name="Policy",
            routing_path=routing_path,
            error_code="POLICY_SERVICE_ERROR",
            rule_based=False,
        )


# =============================================================================
# 5) Final decision 노드 — spam_agents(정책 에이전트) 호출
# =============================================================================


def final_decision_node(state: SpamDetectionState) -> Dict[str, Any]:
    """최종 결정 노드: spam.agents.spam_agents의 정책 기반 결정 호출."""
    from domain.spokes.spam.agents.spam_agents import decide_final_action  # type: ignore

    return decide_final_action(
        routing_strategy=state.get("routing_strategy"),
        llama_result=state.get("llama_result"),
        exaone_result=state.get("exaone_result"),
        routing_path=state.get("routing_path", ""),
    )


# =============================================================================
# 6) 라우팅 결정 — Gateway 이후 규칙 vs 정책 분기
# =============================================================================


def routing_decision(state: SpamDetectionState) -> str:
    """Gateway 이후: 규칙이면 final_decision, 정책이면 policy_service."""
    routing_strategy = state.get("routing_strategy")
    if routing_strategy == "rule":
        return "final_decision"
    if routing_strategy == "policy":
        return "policy_service"
    logger.warning(
        "routing_strategy 없음 또는 알 수 없는 값: %s. 정책 기반으로 진행.",
        routing_strategy,
    )
    return "policy_service"


# =============================================================================
# 7) 그래프 빌드 및 실행 API
# =============================================================================


def build_spam_detection_graph():
    """스팸 감지 그래프 빌드: Gateway → [규칙/정책 분기] → Final decision."""
    checkpointer = get_checkpointer()
    g = StateGraph(SpamDetectionState)
    g.add_node("gateway", gateway_node)
    g.add_node("policy_service", policy_node)
    g.add_node("final_decision", final_decision_node)
    g.set_entry_point("gateway")
    g.add_conditional_edges(
        "gateway",
        routing_decision,
        {"final_decision": "final_decision", "policy_service": "policy_service"},
    )
    g.add_edge("policy_service", "final_decision")
    g.add_edge("final_decision", END)
    return g.compile(checkpointer=checkpointer)


_spam_detection_graph: Any = None


def get_spam_detection_graph():
    """스팸 감지 그래프 인스턴스 반환 (lazy loading)."""
    global _spam_detection_graph
    if _spam_detection_graph is None:
        _spam_detection_graph = build_spam_detection_graph()
    return _spam_detection_graph


def run_spam_detection(email_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """스팸 감지 실행 — API 진입점.

    Args:
        email_metadata: 이메일 메타데이터

    Returns:
        스팸 감지 결과 (action, reason_codes, confidence, spam_prob 등)
    """
    initial_state: SpamDetectionState = {
        "email_metadata": email_metadata,
        "llama_result": None,
        "exaone_result": None,
        "routing_strategy": None,
        "routing_path": "",
        "messages": [],
    }
    config = {"configurable": {"thread_id": f"spam_{uuid.uuid4().hex[:8]}"}}
    try:
        graph = get_spam_detection_graph()
        result = graph.invoke(initial_state, config=config)
        fd = result.get("final_decision", {})
        logger.debug(
            "스팸 감지 완료: action=%s, routing_strategy=%s",
            fd.get("action"),
            result.get("routing_strategy"),
        )
        return {
            "action": fd.get("action", "deliver"),
            "reason_codes": fd.get("reason_codes", []),
            "user_message": fd.get("user_message", ""),
            "confidence": fd.get("confidence", "low"),
            "spam_prob": fd.get("spam_prob", 0.0),
            "llama_result": result.get("llama_result", {}),
            "exaone_result": result.get("exaone_result"),
            "routing_strategy": result.get("routing_strategy"),
            "routing_path": result.get("routing_path", ""),
        }
    except Exception as e:
        logger.error("스팸 감지 그래프 실행 실패: %s", e, exc_info=True)
        return {
            "action": "deliver",
            "reason_codes": ["GRAPH_ERROR"],
            "user_message": f"스팸 감지 처리 중 오류가 발생했습니다: {str(e)}",
            "confidence": "low",
            "spam_prob": 0.0,
            "llama_result": {},
            "exaone_result": None,
            "routing_strategy": None,
            "routing_path": "Error",
        }
