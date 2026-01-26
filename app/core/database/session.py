"""
데이터베이스 세션 관리

V1과 V10을 위한 세션 팩토리를 제공합니다.
"""

from typing import Generator

from sqlalchemy.orm import Session, sessionmaker  # type: ignore[import-untyped]

from core.database.engine import get_engine, get_v10_engine  # type: ignore

# V1 세션 (필요시 사용)
V1SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=get_engine(),
)

# V10 세션
V10SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=get_v10_engine(),
)


def get_db() -> Generator[Session, None, None]:
    """V1 데이터베이스 세션 의존성."""
    db = V1SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_v10_db() -> Generator[Session, None, None]:
    """V10 데이터베이스 세션 의존성."""
    db = V10SessionLocal()
    try:
        yield db
    finally:
        db.close()
