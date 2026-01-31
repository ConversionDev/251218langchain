"""
LLaMA 리더기

텍스트 정제/추출 및 규칙/정책 판단을 담당하는 리더기.
Hub Llama Adapter를 통해 Llama에 접근합니다.
"""

from typing import Any, Dict, Optional

from domain.v1.spokes.spam.services.rule_service import RuleService  # type: ignore

from .base_reader import BaseReader  # type: ignore


class LLaMAReader(BaseReader):
    """LLaMA 리더기.

    텍스트 정제/추출 및 규칙/정책 판단을 수행합니다.
    - 스팸 분류 (spam_prob) - Hub Llama Adapter
    - 규칙 기반 vs 정책 기반 판단 - Hub Llama Adapter (classify)
    """

    def __init__(self, rule_service: Optional[RuleService] = None):
        """초기화.

        Args:
            rule_service: 규칙 서비스 (None이면 새로 생성)
        """
        self._rule_service = rule_service or RuleService()

    def read(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """데이터를 읽고 정제/추출된 메타데이터 및 라우팅 전략을 반환.

        Args:
            data: 이메일 메타데이터

        Returns:
            정제/추출된 메타데이터, 분류 결과, 라우팅 전략
            {
                "email_metadata": Dict,
                "llama_result": Dict,
                "routing_strategy": "rule" | "policy",
            }
        """
        result_dict = self._classify_spam(data)
        routing_strategy = self._decide_routing_strategy(data)
        return {
            "email_metadata": data,
            "llama_result": result_dict,
            "routing_strategy": routing_strategy,
        }

    def _classify_spam(self, email_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Hub Llama Adapter로 스팸 분류."""
        try:
            from domain.v1.hub.llm import classify_spam  # type: ignore

            return classify_spam(email_metadata)
        except Exception as e:
            print(f"[WARNING] LLaMA 스팸 분류 실패: {e}")
        return {
            "spam_prob": 0.5,
            "confidence": "low",
            "label": "UNCERTAIN",
        }

    def _decide_routing_strategy(self, email_metadata: Dict[str, Any]) -> str:
        """Hub Llama Adapter(classify)로 규칙/정책 판단. RULE_BASED -> rule, 그 외 -> policy."""
        try:
            from domain.v1.hub.llm import classify  # type: ignore

            text = (
                f"제목: {email_metadata.get('subject', '')} "
                f"발신자: {email_metadata.get('sender', '')} "
                f"본문: {email_metadata.get('body', '')[:200]}"
            )
            result = classify(text)
            return "rule" if result == "RULE_BASED" else "policy"
        except Exception as e:
            print(f"[WARNING] Hub classify 실패, RuleService 사용: {e}")

        is_rule_based = self._rule_service.is_rule_based(email_metadata)
        return "rule" if is_rule_based else "policy"

    def cleanup(self) -> None:
        """리소스 정리 (선택적)."""
        pass
