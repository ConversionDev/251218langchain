"""
LLaMA 리더기

텍스트 정제/추출 및 규칙/정책 판단을 담당하는 리더기.
LLaMA 모델을 사용합니다.
"""

from typing import Any, Dict, Optional

# LLaMA Gate 임포트
from core.llm.providers.llama import LLaMAGate  # type: ignore
from domain.v1.spam.services.rule_service import RuleService  # type: ignore

from .base_reader import BaseReader  # type: ignore


class LLaMAReader(BaseReader):
    """LLaMA 리더기.

    텍스트 정제/추출 및 규칙/정책 판단을 수행합니다.
    - 스팸 분류 (spam_prob) - LLaMA 사용
    - 규칙 기반 vs 정책 기반 판단 - LLaMA 사용

    Lazy Loading: LLaMA 모델은 첫 요청 시 로드됩니다.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,  # 하위 호환성 유지 (사용 안함)
        device: Optional[str] = None,  # 하위 호환성 유지 (사용 안함)
        use_finetuned: bool = True,  # 하위 호환성 유지 (사용 안함)
        rule_service: Optional[RuleService] = None,
    ):
        """초기화.

        Args:
            model_path: (미사용) 하위 호환성용
            device: (미사용) 하위 호환성용
            use_finetuned: (미사용) 하위 호환성용
            rule_service: 규칙 서비스 (None이면 새로 생성)
        """
        # LLaMA Gate는 Lazy Loading (첫 요청 시 로드)
        self._llama_gate: Optional[LLaMAGate] = None
        self._llama_loaded = False

        # 규칙 서비스 초기화 (fallback용)
        self._rule_service = rule_service or RuleService()

    def _ensure_llama_loaded(self) -> None:
        """LLaMA 모델이 로드되어 있는지 확인하고, 없으면 로드."""
        if not self._llama_loaded:
            try:
                print("[INFO] LLaMA Gate 초기화 중 (Lazy Loading)...")
                self._llama_gate = LLaMAGate(
                    model_id="unsloth/Llama-3.2-3B-Instruct",
                    load_in_4bit=True,
                )
                self._llama_loaded = True
                print("[OK] LLaMA Gate 초기화 완료")
            except Exception as e:
                print(f"[ERROR] LLaMA Gate 초기화 실패: {e}")
                self._llama_gate = None

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
        # LLaMA 모델 Lazy Loading
        print("[DEBUG] LLaMAReader.read() 시작: LLaMA 모델 로드 확인")
        self._ensure_llama_loaded()
        print(f"[DEBUG] LLaMAReader.read() 모델 로드 완료: loaded={self._llama_loaded}")

        # 1. LLaMA로 스팸 분류 수행
        result_dict = self._classify_spam(data)

        # 2. 규칙/정책 판단
        routing_strategy = self._decide_routing_strategy(data)

        # 정제된 메타데이터 및 라우팅 전략 반환
        return {
            "email_metadata": data,
            "llama_result": result_dict,
            "routing_strategy": routing_strategy,
        }

    def _classify_spam(self, email_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """LLaMA로 스팸 분류.

        Args:
            email_metadata: 이메일 메타데이터

        Returns:
            스팸 분류 결과
        """
        if self._llama_gate is not None:
            try:
                return self._llama_gate.classify_spam(email_metadata)
            except Exception as e:
                print(f"[WARNING] LLaMA 스팸 분류 실패: {e}")

        # fallback
        return {
            "spam_prob": 0.5,
            "confidence": "low",
            "label": "UNCERTAIN",
        }

    def _decide_routing_strategy(self, email_metadata: Dict[str, Any]) -> str:
        """규칙 기반인지 정책 기반인지 판단.

        Args:
            email_metadata: 이메일 메타데이터

        Returns:
            라우팅 전략 ("rule" 또는 "policy")
        """
        # LLaMA Gate 사용 시
        if self._llama_gate is not None:
            try:
                # 이메일 텍스트 생성
                text = (
                    f"제목: {email_metadata.get('subject', '')} "
                    f"발신자: {email_metadata.get('sender', '')} "
                    f"본문: {email_metadata.get('body', '')[:200]}"
                )
                # LLaMA Gate로 분류
                result = self._llama_gate.classify(text)
                # "rule_based" -> "rule", "policy_based" -> "policy"
                return "rule" if result == "rule_based" else "policy"
            except Exception as e:
                print(f"[WARNING] LLaMA Gate 분류 실패, RuleService 사용: {e}")

        # Rule Service를 사용하여 규칙 기반 처리 가능 여부 확인 (fallback)
        is_rule_based = self._rule_service.is_rule_based(email_metadata)

        if is_rule_based:
            return "rule"
        else:
            return "policy"

    def cleanup(self) -> None:
        """리소스 정리 (선택적)."""
        pass
