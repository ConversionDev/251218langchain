"""
리더기 인터페이스

모든 리더기는 이 인터페이스를 구현해야 합니다.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseReader(ABC):
    """리더기 기본 인터페이스.

    텍스트 정제/추출을 담당하는 리더기의 공통 인터페이스.
    """

    @abstractmethod
    def read(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """데이터를 읽고 정제/추출된 메타데이터를 반환.

        Args:
            data: 입력 데이터 (이메일 메타데이터 등)

        Returns:
            정제/추출된 메타데이터 딕셔너리
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """리소스 정리 (선택적)."""
        pass
