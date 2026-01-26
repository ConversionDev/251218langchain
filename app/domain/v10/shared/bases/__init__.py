"""
레거시 호환을 위한 래퍼

기존 import 호환성을 유지하기 위한 래퍼 모듈입니다.
새로운 코드는 core.database를 직접 사용하세요.
"""

# 새로운 구조로 리다이렉트
from core.database import Base  # type: ignore

# 기존 import 호환성 유지
__all__ = ["Base"]
