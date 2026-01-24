"""
정책 기반 처리 노드

정책 기반 판단을 수행하는 LangGraph 노드.
Policy Service를 통해 EXAONE을 사용하여 분석합니다.
"""

from typing import Any, Dict

from domain.spam.models.state_model import (  # type: ignore
    SpamDetectionState,
)
from domain.spam.services.policy_service import PolicyService  # type: ignore
from .utils import (  # type: ignore
    create_exaone_result_from_service_result,
    handle_node_error,
)


# Policy Service 싱글톤
_policy_service: PolicyService | None = None


def _get_policy_service() -> PolicyService:
    """Policy Service 싱글톤 인스턴스 반환."""
    global _policy_service
    if _policy_service is None:
        _policy_service = PolicyService()
    return _policy_service


def policy_node(state: SpamDetectionState) -> Dict[str, Any]:
    """정책 기반 처리 노드.

    LangGraph 노드 역할:
    - SpamDetectionState 입력 → State 업데이트 반환
    - graph.py에서 "policy_service" 노드로 등록됨

    처리 흐름:
    1. Policy Service로 정책 기반 처리 (EXAONE 사용)
    2. 결과를 exaone_result 형식으로 변환
    3. final_decision으로 전달
    """
    email_metadata = state.get("email_metadata", {})
    routing_path = state.get("routing_path", "Start")

    try:
        # Policy Service로 정책 기반 처리
        policy_service = _get_policy_service()
        policy_result = policy_service.process(email_metadata, use_existing_policy=True)

        # exaone_result 형식으로 변환 (ExaoneResult 모델 형식에 맞춤)
        analysis_text = policy_result.get("analysis", "")
        exaone_result = create_exaone_result_from_service_result(
            service_result=policy_result,
            analysis_text=analysis_text,
            rule_based=False,
            additional_metadata={"policy_id": policy_result.get("policy_id")},
        )

        new_routing_path = routing_path + " -> PolicyService(EXAONE)"

        return {
            "exaone_result": exaone_result,
            "routing_path": new_routing_path,
        }
    except Exception as e:
        return handle_node_error(
            error=e,
            node_name="Policy",
            routing_path=routing_path,
            error_code="POLICY_SERVICE_ERROR",
            rule_based=False,
        )
