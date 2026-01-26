"""
데이터베이스 Engine 관리

V1과 V10을 위한 Engine을 생성하고 관리합니다.
"""

from sqlalchemy import create_engine  # type: ignore[import-untyped]

from core.config import get_settings  # type: ignore

settings = get_settings()

# V1 Engine (필요시 사용)
_v1_engine = create_engine(
    settings.connection_string,
    echo=False,
)

# V10 Engine
_v10_engine = create_engine(
    settings.connection_string,
    echo=False,
)


def get_engine():
    """V1 Engine 반환."""
    return _v1_engine


def get_v10_engine():
    """V10 Engine 반환."""
    return _v10_engine
