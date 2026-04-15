"""
스팸 정책 기반 에이전트

LLaMA/EXAONE 결과를 정책·규칙 기반으로 action으로 변환.
모델 호출 없이 결과 해석만 수행.
"""

from typing import Any, Dict, Optional, Tuple

# action → 사용자 메시지
ACTION_MESSAGES = {
    "reject": "스팸 메일로 차단되었습니다.",
    "quarantine": "의심스러운 메일입니다.",
    "deliver_with_warning": "주의가 필요한 메일입니다.",
    "deliver": "정상 메일입니다.",
    "ask_user_confirm": "확인이 필요한 메일입니다.",
}

# reason_code → 설명
REASON_DESCRIPTIONS = {
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


def decide_final_action(
    routing_strategy: Optional[str],
    llama_result: Optional[Dict[str, Any]],
    exaone_result: Optional[Dict[str, Any]],
    routing_path: str = "",
) -> Dict[str, Any]:
    """LLaMA/EXAONE 결과를 정책 기반으로 action 결정.

    Args:
        routing_strategy: "rule" | "policy"
        llama_result: LLaMA 분류 결과 (spam_prob, label, confidence)
        exaone_result: EXAONE 분석 결과 (is_spam, risk_codes, confidence)
        routing_path: 라우팅 경로 문자열

    Returns:
        {"final_decision": {...}, "routing_path": str}
    """
    # 규칙 기반: LLaMA 결과 사용
    if routing_strategy == "rule":
        if not llama_result:
            return _error_final_decision(
                "LLaMA 분석 결과를 받을 수 없습니다. 시스템 오류가 발생했습니다.",
                routing_path,
            )
        action, reason_codes, confidence, spam_prob = _rule_based_decision(llama_result)
        return _build_result(action, reason_codes, confidence, spam_prob, routing_path)

    # 정책 기반: EXAONE 결과 사용
    if routing_strategy == "policy":
        if not exaone_result:
            return _error_final_decision(
                "EXAONE 분석 결과를 받을 수 없습니다. 시스템 오류가 발생했습니다.",
                routing_path,
            )
        action, reason_codes, confidence, spam_prob = _policy_based_decision(exaone_result)
        return _build_result(action, reason_codes, confidence, spam_prob, routing_path)

    # 라우팅 전략 없음
    return _error_final_decision(
        "라우팅 전략을 결정할 수 없습니다. 시스템 오류가 발생했습니다.",
        routing_path,
    )


def _rule_based_decision(llama_result: Dict[str, Any]) -> Tuple[str, list, str, float]:
    """규칙 기반(LLaMA) 결과 → action 결정."""
    spam_prob = llama_result.get("spam_prob", 0.5)
    confidence = llama_result.get("confidence", "low")
    label = llama_result.get("label", "UNCERTAIN")

    if spam_prob >= 0.8 or label == "SPAM":
        return "reject", ["LLAMA_SPAM_DETECTED"], confidence, spam_prob
    if spam_prob >= 0.6 or label == "SUSPICIOUS":
        return "quarantine", ["SUSPICIOUS_CONTENT"], confidence, spam_prob
    if spam_prob <= 0.3 or label == "HAM":
        return "deliver", [], confidence, spam_prob
    return "deliver_with_warning", ["LOW_CONFIDENCE"], confidence, spam_prob


def _policy_based_decision(exaone_result: Dict[str, Any]) -> Tuple[str, list, str, float]:
    """정책 기반(EXAONE) 결과 → action 결정."""
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
        return "reject", risk_codes or ["EXAONE_SPAM_DETECTED"], confidence, spam_prob
    if len(risk_codes) >= 2 or (is_spam is True and confidence == "medium"):
        return "quarantine", risk_codes or ["SUSPICIOUS_CONTENT"], confidence, spam_prob
    if is_spam is False:
        if confidence in ("high", "medium"):
            return "deliver", [], confidence, spam_prob
        return "deliver_with_warning", risk_codes or ["LOW_CONFIDENCE"], confidence, spam_prob
    if len(risk_codes) >= 1:
        return "deliver_with_warning", risk_codes, confidence, spam_prob
    return "ask_user_confirm", risk_codes or ["UNCERTAIN"], confidence, spam_prob


def _error_final_decision(
    user_message: str,
    routing_path: str,
) -> Dict[str, Any]:
    """에러 시 final_decision 반환."""
    return {
        "final_decision": {
            "action": "ask_user_confirm",
            "reason_codes": ["SYSTEM_ERROR"],
            "user_message": user_message,
            "confidence": "low",
            "spam_prob": 0.5,
        },
        "routing_path": routing_path + " -> FinalDecision(ERROR)",
    }


def _build_result(
    action: str,
    reason_codes: list,
    confidence: str,
    spam_prob: float,
    routing_path: str,
) -> Dict[str, Any]:
    """final_decision 및 user_message 조립."""
    base_message = ACTION_MESSAGES.get(action, "확인이 필요한 메일입니다.")
    reasons = (
        "\n".join([f"- {REASON_DESCRIPTIONS.get(c, c)}" for c in reason_codes])
        if reason_codes
        else ""
    )
    user_message = (
        f"{base_message}\n\n{reasons}\n\n발신자를 확인하세요."
        if reasons
        else f"{base_message}\n\n발신자를 확인하세요."
    )

    return {
        "final_decision": {
            "action": action,
            "reason_codes": reason_codes,
            "user_message": user_message,
            "confidence": confidence,
            "spam_prob": spam_prob,
        },
        "routing_path": routing_path + " -> FinalDecision",
    }
