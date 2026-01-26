"""
Alembic 환경 설정 - V10 전용

V10 도메인의 데이터베이스 마이그레이션을 관리합니다.
V1과 완전히 분리된 독립적인 마이그레이션 시스템입니다.
"""

from logging.config import fileConfig
from pathlib import Path
import sys

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# 프로젝트 루트를 Python 경로에 추가
current_dir = Path(__file__).parent.parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# V10 모델들 import (Alembic이 메타데이터를 수집)
from core.database import Base  # type: ignore
from domain.v10.member.bases.player import Player  # noqa: F401
from domain.v10.member.bases.team import Team  # noqa: F401
from domain.v10.member.bases.schedule import Schedule  # noqa: F401
from domain.v10.member.bases.stadium import Stadium  # noqa: F401

# V10 전용 데이터베이스 설정
from core.config import get_settings  # type: ignore
from core.database import get_v10_engine  # type: ignore

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# V10 전용 데이터베이스 연결 문자열 설정
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.connection_string)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def include_object(object, name, type_, reflected, compare_to):
    """
    Alembic autogenerate에서 특정 객체를 제외합니다.
    
    langchain_pg_* 테이블은 LangChain PGVector에서 자동으로 생성되는 테이블이므로
    Alembic 마이그레이션에서 제외합니다.
    """
    if type_ == "table" and name.startswith("langchain_pg_"):
        return False
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # V10 전용 Engine 사용
    connectable = get_v10_engine()

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
