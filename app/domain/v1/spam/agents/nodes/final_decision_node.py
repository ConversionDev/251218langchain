"""
최종 결정 노드

최종 결정을 수행하는 LangGraph 노드.
"""

from typing import Any, Dict

from domain.v1.spam.models.state_model import (  # type: ignore
    SpamDetectionState,
)


def final_decision_node(state: SpamDetectionState) -> Dict[str, Any]:
    """최종 결정 노드 - 라우팅 전략에 따라 LLaMA 또는 EXAONE 결과 사용.

    LangGraph 노드 역할:
    - SpamDetectionState 입력 → State 업데이트 반환
    - graph.py에서 "final_decision" 노드로 등록됨

    아키텍처 원칙:
    - 규칙 기반: LLaMA 결과를 최종 결정으로 직접 사용
    - 정책 기반: EXAONE 결과를 최종 결정으로 사용

    LangChain 컴포넌트 사용:
    - 없음 (순수 비즈니스 로직)
    """
    routing_strategy = state.get("routing_strategy")
    llama_result = state.get("llama_result")
    exaone_result = state.get("exaone_result")
    routing_path = state.get("routing_path", "")

    # 규칙 기반: LLaMA 결과를 최종 결정으로 사용
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

        # LLaMA 결과에서 정보 추출
        spam_prob = llama_result.get("spam_prob", 0.5)
        confidence = llama_result.get("confidence", "low")
        label = llama_result.get("label", "UNCERTAIN")

        # LLaMA 결과 기반으로 action 결정
        if spam_prob >= 0.8 or label == "SPAM":
            action = "reject"
            reason_codes = ["LLAMA_SPAM_DETECTED"]
        elif spam_prob >= 0.6 or label == "SUSPICIOUS":
            action = "quarantine"
            reason_codes = ["SUSPICIOUS_CONTENT"]
        elif spam_prob <= 0.3 or label == "HAM":
            action = "deliver"
            reason_codes = []
        else:
            # 애매한 경우
            action = "deliver_with_warning"
            reason_codes = ["LOW_CONFIDENCE"]

    # 정책 기반: EXAONE 결과를 최종 결정으로 사용
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

        # EXAONE 결과에서 정보 추출
        is_spam = exaone_result.get("is_spam")
        risk_codes = exaone_result.get("risk_codes", [])
        confidence = exaone_result.get("confidence", "medium")

        # is_spam을 기반으로 spam_prob 계산
        if is_spam is True:
            spam_prob = 1.0 if confidence == "high" else 0.8
        elif is_spam is False:
            spam_prob = 0.0 if confidence == "high" else 0.2
        else:
            spam_prob = 0.5

        # 정책 규칙 적용 (EXAONE 결과 기반)
        if is_spam is True or "CRITICAL_PHISHING" in risk_codes:
            action = "reject"
            reason_codes = risk_codes if risk_codes else ["EXAONE_SPAM_DETECTED"]
        elif len(risk_codes) >= 2 or (is_spam is True and confidence == "medium"):
            action = "quarantine"
            reason_codes = risk_codes if risk_codes else ["SUSPICIOUS_CONTENT"]
        elif is_spam is False:
            if confidence == "high" or confidence == "medium":
                action = "deliver"
                reason_codes = []
            else:
                action = "deliver_with_warning"
                reason_codes = risk_codes if risk_codes else ["LOW_CONFIDENCE"]
        elif len(risk_codes) >= 1:
            action = "deliver_with_warning"
            reason_codes = risk_codes
        else:
            action = "ask_user_confirm"
            reason_codes = risk_codes if risk_codes else ["UNCERTAIN"]
    else:
        # routing_strategy가 없는 경우 (에러 처리)
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

    # 사용자 메시지 생성
    messages = {
        "reject": "스팸 메일로 차단되었습니다.",
        "quarantine": "의심스러운 메일입니다.",
        "deliver_with_warning": "주의가 필요한 메일입니다.",
        "deliver": "정상 메일입니다.",
        "ask_user_confirm": "확인이 필요한 메일입니다.",
    }

    base_message = messages.get(action, "확인이 필요한 메일입니다.")

    reason_descriptions = {
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

    if reason_codes:
        reasons = "\n".join(
            [f"- {reason_descriptions.get(code, code)}" for code in reason_codes]
        )
        user_message = f"{base_message}\n\n{reasons}\n\n발신자를 확인하세요."
    else:
        user_message = f"{base_message}\n\n발신자를 확인하세요."

    # 최종 결정 생성 (라우팅 전략에 따라 confidence와 spam_prob 설정)
    if routing_strategy == "rule":
        final_decision = {
            "action": action,
            "reason_codes": reason_codes,
            "user_message": user_message,
            "confidence": confidence,  # LLaMA의 confidence 사용
            "spam_prob": spam_prob,  # LLaMA 결과 사용
        }
    else:  # policy
        final_decision = {
            "action": action,
            "reason_codes": reason_codes,
            "user_message": user_message,
            "confidence": confidence,  # EXAONE의 confidence 사용
            "spam_prob": spam_prob,  # EXAONE 결과 기반 계산
        }

    new_routing_path = routing_path + " -> FinalDecision"

    return {
        "final_decision": final_decision,
        "routing_path": new_routing_path,
    }
