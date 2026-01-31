"""
FastAPI 백엔드 서버.

역할:
- FastAPI 서버 제공 (REST API)
- LangGraph 에이전트 채팅 (단일 진입)
- PGVector 벡터 스토어 초기화 (에이전트 RAG 노드용)
- 스팸 감지 등 기타 API
"""

import asyncio
import logging
import threading
import warnings
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, Optional

# 공통 모듈 (환경 변수 로딩 포함)
from core.config import get_settings  # type: ignore
from core.database import wait_for_postgres  # type: ignore

# LangChain 관련 import (warnings 필터링 전에 import)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from langchain_community.vectorstores import PGVector

# PGVector의 JSONB deprecation 경고 무시 (import 후 경고 필터링)
try:
    from langchain_core._api.deprecation import LangChainPendingDeprecationWarning

    warnings.filterwarnings(
        "ignore",
        category=LangChainPendingDeprecationWarning,
        module="langchain_community.vectorstores.pgvector",
    )
except ImportError:
    warnings.filterwarnings(
        "ignore",
        category=DeprecationWarning,
        module="langchain_community.vectorstores.pgvector",
    )

warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    module="langchain_community.vectorstores.pgvector",
)

settings = get_settings()
CONNECTION_STRING = settings.connection_string
COLLECTION_NAME = settings.collection_name

# Llama + ExaOne Fast MCP 통일 (health + MCP 프로토콜 한 앱)
from domain.v1.hub.mcp.app import get_http_app  # type: ignore  # noqa: E402

mcp_app = get_http_app()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    FastAPI 애플리케이션 라이프사이클 관리.

    Windows/uvicorn: lifespan에서 초기화를 기다리면 yield 직후 서버가 종료되는 현상이 있어,
    먼저 yield로 서버를 띄운 뒤 V1/V10 초기화를 백그라운드 태스크로 실행합니다.
    """
    print("\n" + "=" * 50)
    print("FastAPI 서버 시작 중...")
    print("=" * 50)

    init_error: Optional[Exception] = None

    async def run_inits() -> None:
        nonlocal init_error
        try:
            await asyncio.to_thread(init_v1)
            print("\n" + "=" * 50)
            print("V10 도메인 초기화 중...")
            print("=" * 50)
            await asyncio.to_thread(init_v10)
            print("\n" + "=" * 50)
            print("[OK] 모든 도메인 초기화 완료!")
            print("=" * 50)
        except Exception as e:
            init_error = e
            logging.exception("도메인 초기화 실패: %s", e)

    init_task = asyncio.create_task(run_inits())
    # 서버를 먼저 띄우기 위해 yield를 즉시 수행 (초기화는 백그라운드에서 진행)
    yield

    init_task.cancel()
    try:
        await init_task
    except asyncio.CancelledError:
        pass
    if init_error:
        logging.warning("초기화 중 오류가 있었습니다: %s", init_error)
    print("\n[INFO] 서버 종료 중...")


app = FastAPI(
    title="LangChain Chatbot API",
    description="PGVector와 연동된 LangChain 챗봇 API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 변수 (에이전트 RAG 노드·벡터스토어용)
vector_store: Optional[PGVector] = None
local_embeddings = None
local_llm = None
_rag_init_lock = threading.Lock()
_rag_initialized = False


def init_v10() -> None:
    """V10 도메인 초기화: Alembic 마이그레이션으로 테이블 자동 생성 및 업데이트."""
    try:
        # 설정 가져오기
        current_settings = get_settings()

        # 관계형 테이블 자동 생성 (Alembic + 자동 생성 방식)
        logging.info("V10 관계형 테이블 생성 중 (Alembic 자동 생성)...")
        wait_for_postgres()

        try:
            # 모델들을 명시적으로 import하여 Base.metadata에 등록
            from alembic import command  # type: ignore

            # Alembic 설정
            from alembic.config import Config  # type: ignore
            from core.database import get_v10_engine  # type: ignore
            from domain.v10.soccer.models.bases.player import Player  # noqa: F401
            from domain.v10.soccer.models.bases.schedule import Schedule  # noqa: F401
            from domain.v10.soccer.models.bases.stadium import Stadium  # noqa: F401
            from domain.v10.soccer.models.bases.team import Team  # noqa: F401
            from sqlalchemy import inspect  # type: ignore[import-untyped]

            alembic_ini_path = Path(__file__).parent / "alembic.ini"
            alembic_cfg = Config(str(alembic_ini_path))
            # CWD와 무관하게 app/alembic을 사용 (main.py를 루트에서 실행해도 versions를 찾도록)
            app_dir = Path(__file__).parent
            alembic_cfg.set_main_option("script_location", str(app_dir / "alembic"))

            # Alembic 마이그레이션 파일 디렉토리 확인
            alembic_versions_path = Path(__file__).parent / "alembic" / "versions"
            if not alembic_versions_path.exists():
                alembic_versions_path.mkdir(parents=True, exist_ok=True)

            if current_settings.v10_auto_migrate:
                # autogenerate 실행 (변경사항이 있으면 새 마이그레이션 파일 생성)
                try:
                    command.revision(
                        alembic_cfg,
                        autogenerate=True,
                        message="Auto-generated migration for V10 domain"
                    )
                except Exception as autogen_error:
                    # autogenerate 실패는 무시 (변경사항이 없을 수도 있음)
                    error_msg = str(autogen_error)
                    if "Target database is not up to date" in error_msg:
                        logging.debug("기존 마이그레이션을 먼저 적용해야 합니다.")
                    elif "Can't locate revision identified by" in error_msg:
                        logging.debug("마이그레이션 체인 문제가 있을 수 있습니다.")
                    # 기타 오류는 무시 (변경사항 없음으로 간주)

                # Alembic 마이그레이션 실행 (기존 + 새로 생성된 마이그레이션 모두 적용)
                try:
                    command.upgrade(alembic_cfg, current_settings.v10_migration_revision)
                    logging.info("✓ V10 도메인 마이그레이션 완료")
                except Exception as upgrade_error:
                    # 마이그레이션 실패 시에만 테이블 확인
                    logging.error(f"마이그레이션 실행 실패: {upgrade_error}")
                    try:
                        engine = get_v10_engine()
                        inspector = inspect(engine)
                        existing_tables = inspector.get_table_names()
                        expected_tables = ["players", "teams", "schedules", "stadiums"]
                        created_tables = [name for name in expected_tables if name in existing_tables]

                        if len(created_tables) != len(expected_tables):
                            missing_tables = [name for name in expected_tables if name not in existing_tables]
                            logging.warning(f"일부 테이블이 생성되지 않았습니다: {missing_tables}")
                    except Exception:
                        pass  # 테이블 확인 실패는 무시
                    raise  # 마이그레이션 실패는 재발생
            else:
                logging.warning("V10 자동 마이그레이션이 비활성화되어 있습니다. (V10_AUTO_MIGRATE=false)")
                logging.warning("테이블을 생성하려면 마이그레이션을 수동으로 실행하거나 V10_AUTO_MIGRATE=true로 설정하세요.")

        except Exception as e:
            logging.error(f"관계형 테이블 생성 중 오류: {e}")
            import traceback
            logging.error(traceback.format_exc())
            raise  # 테이블 생성 실패는 치명적 오류이므로 재발생

        # V10 데이터는 JSONL 업로드를 통해 LangGraph 휴리스틱 처리로 로드됩니다.
        logging.info("✓ V10 도메인 초기화 완료")
    except Exception as e:
        logging.error(f"V10 도메인 초기화 실패: {e}")
        raise


def init_v1() -> None:
    """V1 도메인 초기화: 에이전트용 벡터스토어·Embedding·Exaone 사전 로드."""
    global local_embeddings, local_llm, vector_store

    print("=" * 50)
    print("V1 도메인 초기화 (LangGraph 에이전트)...")
    print("=" * 50)

    llm_provider = settings.llm_provider
    exaone_model_dir = settings.exaone_model_dir or "기본값 사용"
    print(f"\n[INFO] LLM_PROVIDER: {llm_provider}")
    print(f"[INFO] EXAONE_MODEL_DIR: {exaone_model_dir}")

    # Neon PostgreSQL 연결 대기 (에이전트 RAG·벡터스토어용)
    print("\n1. Neon PostgreSQL 연결 확인 중...")
    wait_for_postgres()

    # EXAONE 베이스 모델 미리 로드
    if llm_provider == "exaone":
        print("\n2. EXAONE 베이스 모델 미리 로드 중...")
        from core.resource_manager.exaone_manager import ExaoneManager  # type: ignore

        ExaoneManager().get_base_model()
        print("[OK] EXAONE 베이스 모델 미리 로드 완료!")

    # Embedding·벡터스토어는 Lazy Loading (첫 RAG 요청 시 로드 → 서버 기동 속도 개선)
    print("\n3. Embedding·PGVector: Lazy Loading (첫 RAG 요청 시 로드)")
    print("[INFO] 채팅에서 RAG 사용 시 첫 요청에만 Embedding 모델이 로드됩니다.")
    # 스팸 감지 모델은 Lazy Loading (첫 요청 시 로드)
    print("\n4. 스팸 감지 모델: Lazy Loading (첫 요청 시 LLaMA 로드)")
    print("[INFO] VRAM 절약을 위해 스팸 테스트 요청 시 LLaMA 모델이 로드됩니다.")

    print("\n" + "=" * 50)
    print("[OK] V1 도메인 초기화 완료!")
    print("=" * 50)


def initialize_embeddings():
    """Embedding 모델 초기화 - 로컬 모델 초기화."""
    import torch

    global local_embeddings

    # 로컬 Embedding 초기화 (GPU 사용 가능 시 자동 감지)
    try:
        # langchain-huggingface 사용 (deprecation 경고 해결)
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
        except ImportError:
            # fallback to langchain_community
            from langchain_community.embeddings import HuggingFaceEmbeddings

        # GPU 필수 확인
        if not torch.cuda.is_available():
            raise RuntimeError(
                "CUDA가 사용 불가능합니다. GPU가 필요합니다.\n"
                "torch.cuda.is_available()이 False입니다."
            )

        # EMBEDDING_DEVICE 환경 변수 또는 CUDA 사용
        embedding_device = settings.embedding_device
        if embedding_device is None:
            embedding_device = "cuda"  # GPU 전용

        local_embeddings = HuggingFaceEmbeddings(
            model_name=settings.default_embedding_model,
            model_kwargs={"device": embedding_device},
        )
        # 간단한 테스트
        local_embeddings.embed_query("test")
        print(
            f"[OK] 로컬 Embedding 모델 초기화 완료 (sentence-transformers, device={embedding_device})"
        )
    except Exception as local_error:
        print(f"[WARNING] 로컬 Embedding 모델 초기화 실패: {str(local_error)[:100]}...")
        local_embeddings = None

    if not local_embeddings:
        print(
            "[WARNING] 로컬 Embedding 모델 초기화에 실패했습니다. "
            "Embedding 기능이 비활성화됩니다. 벡터 스토어와 RAG 기능을 사용할 수 없습니다."
        )


def initialize_vector_store():
    """PGVector 스토어 초기화."""
    global vector_store, local_embeddings

    # 사용할 embedding 모델 선택 (로컬 모델 사용)
    if local_embeddings:
        current_embeddings = local_embeddings
        print("[INFO] 로컬 Embedding 모델 사용 (fallback)")
    else:
        print(
            "[WARNING] 사용 가능한 Embedding 모델이 없습니다. "
            "벡터 스토어를 초기화할 수 없습니다."
        )
        vector_store = None
        return

    try:
        print("[INFO] ===== PGVector 연결 확인 시작 =====")
        print(f"[INFO] 컬렉션 이름: {COLLECTION_NAME}")
        print(f"[INFO] 연결 문자열: {CONNECTION_STRING[:60]}...")

        # 기존 컬렉션이 있고 벡터 데이터가 있는지 확인
        try:
            print("[INFO] PGVector 객체 생성 중...")
            vector_store = PGVector(
                embedding_function=current_embeddings,
                collection_name=COLLECTION_NAME,
                connection_string=CONNECTION_STRING,
            )
            print("[OK] PGVector 객체 생성 완료")

            # 벡터 데이터가 있는지 확인
            import psycopg2  # type: ignore[import-untyped]

            print("[INFO] 데이터베이스에서 벡터 데이터 확인 중...")
            conn = psycopg2.connect(CONNECTION_STRING)
            cur = conn.cursor()

            # 컬렉션 UUID 확인
            cur.execute(
                f"""
                SELECT uuid FROM langchain_pg_collection WHERE name = '{COLLECTION_NAME}'
            """
            )
            collection_result = cur.fetchone()

            if collection_result:
                collection_uuid = collection_result[0]
                print(f"[INFO] 컬렉션 UUID: {collection_uuid}")

                # 벡터 개수 확인
                cur.execute(
                    f"""
                    SELECT COUNT(*)
                    FROM langchain_pg_embedding
                    WHERE collection_id = '{collection_uuid}'
                """
                )
                result = cur.fetchone()
                vector_count = result[0] if result else 0

                # 벡터 차원 확인
                cur.execute(
                    f"""
                    SELECT array_length(embedding::vector, 1) as vector_dim
                    FROM langchain_pg_embedding
                    WHERE collection_id = '{collection_uuid}'
                    LIMIT 1
                """
                )
                dim_result = cur.fetchone()
                vector_dim = dim_result[0] if dim_result and dim_result[0] else None

                conn.close()

                if vector_count > 0:
                    print("[OK] 기존 PGVector 스토어 로드 완료")
                    print(f"[INFO] 벡터 데이터 개수: {vector_count}개")
                    if vector_dim:
                        print(f"[INFO] 벡터 차원: {vector_dim}차원")
                    print("[OK] ===== PGVector 연결 확인 완료 =====")
                else:
                    # 컬렉션은 있지만 벡터 데이터가 없음 (정상 - 사용자가 나중에 추가할 수 있음)
                    print("[INFO] 컬렉션은 존재하지만 벡터 데이터가 없습니다.")
                    print("[INFO] RAG 기능 사용 시 벡터 데이터를 추가해야 합니다.")
                    print("[OK] ===== PGVector 연결 확인 완료 =====")
            else:
                conn.close()
                print("[WARNING] 컬렉션이 데이터베이스에 존재하지 않습니다.")

        except Exception as e:
            # 컬렉션이 없으면 빈 컬렉션으로 생성
            error_msg = str(e)
            print("[INFO] 컬렉션 로드 실패, 새로 생성합니다...")
            print(f"[INFO] 오류 내용: {error_msg[:150]}")
            print("[INFO] 빈 PGVector 컬렉션 생성 중...")

            # 빈 컬렉션으로 PGVector 스토어 생성 (초기 문서 없음)
            vector_store = PGVector(
                embedding_function=current_embeddings,
                collection_name=COLLECTION_NAME,
                connection_string=CONNECTION_STRING,
            )
            print("[OK] 빈 PGVector 컬렉션 생성 완료")
            print("[INFO] RAG 기능 사용 시 벡터 데이터를 추가해야 합니다.")
            print("[OK] ===== PGVector 연결 확인 완료 =====")
    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] PGVector 스토어 초기화 실패: {error_msg[:200]}...")
        raise


def ensure_rag_initialized() -> None:
    """RAG용 Embedding·벡터스토어를 첫 사용 시 한 번만 초기화 (Lazy Loading)."""
    global _rag_initialized
    if _rag_initialized:
        return
    with _rag_init_lock:
        if _rag_initialized:
            return
        if local_embeddings is None:
            initialize_embeddings()
        if local_embeddings and vector_store is None:
            initialize_vector_store()
        _rag_initialized = True


# 라우터 등록 (순환 import 방지를 위해 여기서 import)
from api.v1.agent.graph_router import (
    router as graph_router,  # type: ignore  # noqa: E402
)
from api.v1.agent.email_router import email_router  # type: ignore  # noqa: E402

# v10 라우터 등록 (soccer 라우터 통합)
from api.v10.soccer.player_router import (
    router as player_router,  # type: ignore  # noqa: E402
)
from api.v10.soccer.schedule_router import (
    router as schedule_router,  # type: ignore  # noqa: E402
)
from api.v10.soccer.stadium_router import (
    router as stadium_router,  # type: ignore  # noqa: E402
)
from api.v10.soccer.team_router import (
    router as team_router,  # type: ignore  # noqa: E402
)

app.include_router(graph_router)
app.include_router(email_router)

# Fast MCP 통일: /mcp/health + /mcp/server 한 앱으로 마운트
app.mount("/mcp", mcp_app)

# v10 API 라우터 등록 (prefix: /api/v10)
# 모든 타입이 /soccer/{type}/upload 패턴으로 통일
app.include_router(player_router, prefix="/api/v10")  # /soccer/player/upload
app.include_router(team_router, prefix="/api/v10")  # /soccer/team/upload
app.include_router(stadium_router, prefix="/api/v10")  # /soccer/stadium/upload
app.include_router(schedule_router, prefix="/api/v10")  # /soccer/schedule/upload


@app.get("/")
async def root():
    """루트 엔드포인트."""
    return {
        "message": "LangChain Chatbot API",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트."""
    return {
        "status": "healthy",
        "vector_store": "initialized" if vector_store else "lazy (not loaded yet)",
        "local_embeddings": "initialized" if local_embeddings else "lazy (not loaded yet)",
    }
