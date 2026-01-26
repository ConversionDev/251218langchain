"""
노드 유틸리티 함수

스팸 감지 노드들에서 공통으로 사용하는 유틸리티 함수들.
"""

import traceback
from typing import Any, Dict, Optional


def create_exaone_result_from_service_result(
    service_result: Dict[str, Any],
    analysis_text: Optional[str] = None,
    rule_based: bool = False,
    additional_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """서비스 결과를 exaone_result 형식으로 변환.

    Args:
        service_result: 서비스 처리 결과 (RuleService 또는 PolicyService)
        analysis_text: 분석 텍스트 (None이면 service_result에서 추출)
        rule_based: 규칙 기반 여부
        additional_metadata: 추가 메타데이터 (예: matched_rule_id, policy_id)

    Returns:
        exaone_result 형식의 딕셔너리
    """
    if analysis_text is None:
        analysis_text = service_result.get("analysis", "")

    exaone_result = {
        "raw_output": analysis_text,  # ExaoneResult 필수 필드
        "parsed": {
            "is_spam": service_result.get("is_spam"),
            "action": service_result.get("action"),
            "confidence": service_result.get("confidence", "medium"),
            "analysis": analysis_text,
        },
        "risk_codes": service_result.get("reason_codes", []),  # reason_codes를 risk_codes로 매핑
        "is_spam": service_result.get("is_spam"),
        "confidence": service_result.get("confidence", "medium"),
        "analysis": analysis_text,
        "rule_based": rule_based,
    }

    # 추가 메타데이터 병합
    if additional_metadata:
        exaone_result.update(additional_metadata)

    return exaone_result


def create_error_exaone_result(
    error: Exception,
    error_message: str,
    error_code: str,
    rule_based: bool = False,
) -> Dict[str, Any]:
    """에러 발생 시 exaone_result 형식으로 변환.

    Args:
        error: 발생한 예외
        error_message: 에러 메시지
        error_code: 에러 코드 (예: "RULE_SERVICE_ERROR", "POLICY_SERVICE_ERROR")
        rule_based: 규칙 기반 여부

    Returns:
        에러 형식의 exaone_result 딕셔너리
    """
    return {
        "raw_output": error_message,  # ExaoneResult 필수 필드
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


def handle_node_error(
    error: Exception,
    node_name: str,
    routing_path: str,
    error_code: str,
    rule_based: bool = False,
) -> Dict[str, Any]:
    """노드 에러 처리 공통 로직.

    Args:
        error: 발생한 예외
        node_name: 노드 이름 (예: "Rule", "Policy")
        routing_path: 현재 라우팅 경로
        error_code: 에러 코드
        rule_based: 규칙 기반 여부

    Returns:
        에러 상태를 포함한 노드 반환값
    """
    # 에러 로깅
    print(f"[ERROR] {node_name} 노드 오류: {str(error)}")
    traceback.print_exc()

    # 에러 메시지 생성
    error_message = f"{node_name} 기반 처리 중 오류 발생: {str(error)}"

    # exaone_result 에러 형식으로 변환
    exaone_result = create_error_exaone_result(
        error=error,
        error_message=error_message,
        error_code=error_code,
        rule_based=rule_based,
    )

    return {
        "exaone_result": exaone_result,
        "routing_path": routing_path + f" -> {node_name}Service(ERROR)",
    }
