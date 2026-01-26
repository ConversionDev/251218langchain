"""
EXAONE Service 레이어

모든 판별/판독을 담당하는 EXAONE 중심 서비스.
EXAONE은 이제 툴 방식으로 사용됩니다 (tools.py의 analyze_with_exaone).
"""

from .models import ExaoneConfig, ExaoneResult

__all__ = ["ExaoneResult", "ExaoneConfig"]
