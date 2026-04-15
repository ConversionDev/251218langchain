"""
데이터베이스 세션 관리

단일 세션 팩토리와 의존성을 제공합니다.
"""

from typing import Generator

from sqlalchemy.orm import Session, sessionmaker  # type: ignore[import-untyped]

from core.database.engine import get_engine  # type: ignore

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=get_engine(),
)


def get_db() -> Generator[Session, None, None]:
    """DB 세션 의존성."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
