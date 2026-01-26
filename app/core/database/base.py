"""
SQLAlchemy Base 클래스

Alembic 마이그레이션과 SQLAlchemy ORM을 위한 기본 클래스입니다.
모든 도메인 모델이 이 Base를 상속받아 사용합니다.

사용 예:
    from core.database import Base

    class MyModel(Base):
        __tablename__ = "my_table"
        id = Column(Integer, primary_key=True)
"""

from sqlalchemy.orm import DeclarativeBase  # type: ignore[import-untyped]


class Base(DeclarativeBase):
    """
    모든 모델의 기본 클래스

    특징:
    - 도메인 간 직접 의존 없음 (루즈한 결합도)
    - 공통 기능은 믹스인으로 제공
    - 각 도메인은 독립적으로 진화 가능
    - Alembic이 자동으로 메타데이터를 수집하여 마이그레이션 생성

    메타데이터:
    - Base.metadata: Alembic이 사용하는 메타데이터 객체
    - 모든 모델의 스키마 정보를 포함
    """

    pass
