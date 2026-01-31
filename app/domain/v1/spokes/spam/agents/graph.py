"""
스팸 감지 LangGraph 워크플로우

실행 흐름:
  1. Gateway (진입·분류) — LLaMA 리더로 텍스트 정제/추출, 규칙 vs 정책 라우팅 결정
  2. [분기] 규칙 → Final decision / 정책 → Policy (EXAONE) → Final decision
  3. Final decision — LLaMA 또는 EXAONE 결과를 action으로 최종 결정

역할별 구성: 유틸 → Gateway → Policy → Final decision → 그래프 빌드/실행 API
"""

import logging
import uuid
from typing import Any, Dict, Optional

from domain.v1.hub.orchestrators.graph_orchestrator import (  # type: ignore
    get_checkpointer,
)
from domain.v1.models.state_model import SpamDetectionState  # type: ignore
from langgraph.graph import END, StateGraph

from .reader.llma_reader import LLaMAReader  # type: ignore

logger = logging.getLogger(__name__)


# =============================================================================
# 1) 유틸 — 정책 노드에서 사용 (exaone 결과 변환, 에러 처리)
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
# 2) Gateway — 진입·분류 (LLaMA 리더, 규칙/정책 라우팅 결정)
# =============================================================================

_llama_reader: Optional[LLaMAReader] = None


def _get_llama_reader() -> LLaMAReader:
    global _llama_reader
    if _llama_reader is None:
        _llama_reader = LLaMAReader()
    return _llama_reader


def gateway_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """진입 노드: LLaMA 리더로 텍스트 정제/추출 후 규칙 vs 정책 라우팅 결정."""
    email_metadata = state.get("email_metadata", {})
    routing_path = state.get("routing_path", "Start")
    try:
        reader = _get_llama_reader()
        result = reader.read(email_metadata)
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
# 3) Policy — 정책 기반 처리 (EXAONE)
# =============================================================================

def policy_node(state: SpamDetectionState) -> Dict[str, Any]:
    """정책 노드: Policy Service(EXAONE)로 분석 후 exaone_result 반환."""
    from domain.v1.spokes.spam.services.policy_service import PolicyService  # type: ignore

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
# 4) Final decision — LLaMA/EXAONE 결과를 action으로 최종 결정
# =============================================================================

_ACTION_MESSAGES = {
    "reject": "스팸 메일로 차단되었습니다.",
    "quarantine": "의심스러운 메일입니다.",
    "deliver_with_warning": "주의가 필요한 메일입니다.",
    "deliver": "정상 메일입니다.",
    "ask_user_confirm": "확인이 필요한 메일입니다.",
}

_REASON_DESCRIPTIONS = {
    "LLAMA_SPAM_DETECTED": "LLaMA가 스팸으로 판별",
    "EXAONE_SPAM_DETECTED": "EXAONE이 스팸으로 판별",
    "SUSPICIOUS_CONTENT": "의심스러운 내용",
    "LOW_CONFIDENCE": "신뢰도가 낮음",
    "UNCERTAIN": "불확실한 케이스",
    "URGENT_MONEY": "긴급 금전 요청 패턴",
    "URL_MISMATCH": "URL 도메인 불일치",
    "SENDER_MISMATCH": "발신자 정보 불일치",
    "CRITICAL_PHISHING": "심각한 피싱 시도",
}


def final_decision_node(state: SpamDetectionState) -> Dict[str, Any]:
    """최종 결정 노드: 라우팅 전략에 따라 LLaMA 또는 EXAONE 결과로 action 결정."""
    routing_strategy = state.get("routing_strategy")
    llama_result = state.get("llama_result")
    exaone_result = state.get("exaone_result")
    routing_path = state.get("routing_path", "")

    # 규칙 기반: LLaMA 결과 사용
    if routing_strategy == "rule":
        if not llama_result:
            return {
                "final_decision": {
                    "action": "ask_user_confirm",
                    "reason_codes": ["SYSTEM_ERROR"],
                    "user_message": "LLaMA 분석 결과를 받을 수 없습니다. 시스템 오류가 발생했습니다.",
                    "confidence": "low",
                    "spam_prob": 0.5,
                },
                "routing_path": routing_path + " -> FinalDecision(ERROR)",
            }
        spam_prob = llama_result.get("spam_prob", 0.5)
        confidence = llama_result.get("confidence", "low")
        label = llama_result.get("label", "UNCERTAIN")
        if spam_prob >= 0.8 or label == "SPAM":
            action, reason_codes = "reject", ["LLAMA_SPAM_DETECTED"]
        elif spam_prob >= 0.6 or label == "SUSPICIOUS":
            action, reason_codes = "quarantine", ["SUSPICIOUS_CONTENT"]
        elif spam_prob <= 0.3 or label == "HAM":
            action, reason_codes = "deliver", []
        else:
            action, reason_codes = "deliver_with_warning", ["LOW_CONFIDENCE"]

    # 정책 기반: EXAONE 결과 사용
    elif routing_strategy == "policy":
        if not exaone_result:
            return {
                "final_decision": {
                    "action": "ask_user_confirm",
                    "reason_codes": ["SYSTEM_ERROR"],
                    "user_message": "EXAONE 분석 결과를 받을 수 없습니다. 시스템 오류가 발생했습니다.",
                    "confidence": "low",
                    "spam_prob": 0.5,
                },
                "routing_path": routing_path + " -> FinalDecision(ERROR)",
            }
        is_spam = exaone_result.get("is_spam")
        risk_codes = exaone_result.get("risk_codes", [])
        confidence = exaone_result.get("confidence", "medium")
        if is_spam is True:
            spam_prob = 1.0 if confidence == "high" else 0.8
        elif is_spam is False:
            spam_prob = 0.0 if confidence == "high" else 0.2
        else:
            spam_prob = 0.5
        if is_spam is True or "CRITICAL_PHISHING" in risk_codes:
            action, reason_codes = "reject", risk_codes or ["EXAONE_SPAM_DETECTED"]
        elif len(risk_codes) >= 2 or (is_spam is True and confidence == "medium"):
            action, reason_codes = "quarantine", risk_codes or ["SUSPICIOUS_CONTENT"]
        elif is_spam is False:
            if confidence in ("high", "medium"):
                action, reason_codes = "deliver", []
            else:
                action, reason_codes = "deliver_with_warning", risk_codes or ["LOW_CONFIDENCE"]
        elif len(risk_codes) >= 1:
            action, reason_codes = "deliver_with_warning", risk_codes
        else:
            action, reason_codes = "ask_user_confirm", risk_codes or ["UNCERTAIN"]

    else:
        return {
            "final_decision": {
                "action": "ask_user_confirm",
                "reason_codes": ["SYSTEM_ERROR"],
                "user_message": "라우팅 전략을 결정할 수 없습니다. 시스템 오류가 발생했습니다.",
                "confidence": "low",
                "spam_prob": 0.5,
            },
            "routing_path": routing_path + " -> FinalDecision(ERROR)",
        }

    base_message = _ACTION_MESSAGES.get(action, "확인이 필요한 메일입니다.")
    reasons = "\n".join(
        [f"- {_REASON_DESCRIPTIONS.get(c, c)}" for c in reason_codes]
    ) if reason_codes else ""
    user_message = f"{base_message}\n\n{reasons}\n\n발신자를 확인하세요." if reasons else f"{base_message}\n\n발신자를 확인하세요."

    final_decision = {
        "action": action,
        "reason_codes": reason_codes,
        "user_message": user_message,
        "confidence": confidence,
        "spam_prob": spam_prob,
    }
    return {
        "final_decision": final_decision,
        "routing_path": routing_path + " -> FinalDecision",
    }


# =============================================================================
# 5) 라우팅 결정 — Gateway 이후 규칙 vs 정책 분기
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
# 6) 그래프 빌드 및 실행 API
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


def run_spam_detection_graph(email_metadata: dict) -> dict:
    """스팸 감지 그래프 실행. API 진입점."""
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
            "user_message": f"스팸 감지 처리 중 오류 발생: {str(e)}",
            "confidence": "low",
            "spam_prob": 0.0,
            "llama_result": {},
            "exaone_result": None,
            "routing_strategy": None,
            "routing_path": "Error",
        }
