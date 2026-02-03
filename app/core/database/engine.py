"""
데이터베이스 Engine 관리

단일 연결 문자열로 Engine을 생성합니다.
"""

from sqlalchemy import create_engine  # type: ignore[import-untyped]

from core.config import get_settings  # type: ignore

settings = get_settings()

_engine = create_engine(
    settings.connection_string,
    echo=False,
)


def get_engine():
    """DB Engine 반환."""
    return _engine
