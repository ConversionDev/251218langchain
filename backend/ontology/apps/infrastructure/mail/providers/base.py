"""
수신 공급자 추상화.

verify/parse 분리 없이 parse_and_verify 단일 진입점만 사용 (호출부에서 verify 누락 방지).
"""

from abc import ABC, abstractmethod
from typing import Any

from infrastructure.mail.schemas import NormalizedInboundMail  # type: ignore


class InboundMailProvider(ABC):
    """수신 메일 공급자. 검증 + 파싱을 한 번에 수행."""

    @abstractmethod
    def parse_and_verify(self, request_or_payload: Any) -> NormalizedInboundMail:
        """
        요청(또는 이미 파싱된 payload)을 검증하고 NormalizedInboundMail로 반환.

        검증 실패 시 예외 발생. 호출부는 try/except로 처리.
        """
        ...
