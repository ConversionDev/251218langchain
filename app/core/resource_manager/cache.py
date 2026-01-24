"""
LRU 캐시

어댑터 캐싱을 위한 LRU 캐시 구현.
"""

from collections import OrderedDict
from typing import Any, Optional


class LRUCache:
    """LRU 캐시 구현."""

    def __init__(self, max_size: int = 3):
        """초기화.

        Args:
            max_size: 최대 캐시 크기
        """
        self._max_size = max_size
        self._cache: OrderedDict[str, Any] = OrderedDict()

    def get(self, key: str) -> Optional[Any]:
        """캐시에서 항목 조회.

        Args:
            key: 키

        Returns:
            캐시된 값 또는 None
        """
        if key in self._cache:
            # 최근 사용된 항목을 끝으로 이동
            self._cache.move_to_end(key)
            return self._cache[key]
        return None

    def put(self, key: str, value: Any) -> None:
        """캐시에 항목 추가.

        Args:
            key: 키
            value: 값
        """
        if key in self._cache:
            # 기존 항목 업데이트
            self._cache.move_to_end(key)
        else:
            # 새 항목 추가
            if len(self._cache) >= self._max_size:
                # 가장 오래된 항목 제거
                self._cache.popitem(last=False)
            self._cache[key] = value
        self._cache[key] = value

    def clear(self) -> None:
        """캐시 비우기."""
        self._cache.clear()
