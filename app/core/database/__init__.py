"""
데이터베이스 모듈 - 통합 관리

모든 데이터베이스 관련 기능을 제공합니다.
"""

# Base 클래스
from core.database.base import Base  # type: ignore

# Session 관리
from core.database.session import (  # type: ignore
    get_db,
    SessionLocal,
)

# Engine 관리
from core.database.engine import get_engine  # type: ignore

# 믹스인
from core.database.mixin import (  # type: ignore
    TimestampMixin,
    SoftDeleteMixin,
    StatusMixin,
)

# 유틸리티
from core.database.connection import (  # type: ignore
    wait_for_postgres,
    get_vector_count,
    check_collection_exists,
)

__all__ = [
    # Base
    "Base",
    # Session
    "get_db",
    "SessionLocal",
    # Engine
    "get_engine",
    # Mixin
    "TimestampMixin",
    "SoftDeleteMixin",
    "StatusMixin",
    # Utils
    "wait_for_postgres",
    "get_vector_count",
    "check_collection_exists",
]
