"""
FastAPI 백엔드 서버.

역할:
- FastAPI 서버 제공 (REST API)
- LangGraph 에이전트 채팅 (단일 진입)
- RAG: disclosures·competency_anchors 테이블 검색 (LangChain PGVector 테이블 미사용)
- 스팸 감지 등 기타 API
"""

import asyncio
import logging
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, Optional

# 공통 모듈 (환경 변수 로딩 포함)
from core.config import get_settings  # type: ignore
from core.database import wait_for_postgres  # type: ignore

from fastapi import FastAPI

settings = get_settings()

# Llama + ExaOne Fast MCP 통일 (health + MCP 프로토콜 한 앱)
from domain.hub.mcp.central_control_server import get_http_app  # type: ignore  # noqa: E402

mcp_app = get_http_app()


@asynccontextmanager
async def _app_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    FastAPI 애플리케이션 라이프사이클 관리.

    Windows/uvicorn: lifespan에서 초기화를 기다리면 yield 직후 서버가 종료되는 현상이 있어,
    먼저 yield로 서버를 띄운 뒤 에이전트·DB 초기화를 백그라운드 태스크로 실행합니다.
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
            print("DB·마이그레이션 초기화 중...")
            print("=" * 50)
            await asyncio.to_thread(init_db)
            print("\n" + "=" * 50)
            print("[OK] 백엔드 초기화 완료!")
            print("=" * 50)
        except Exception as e:
            init_error = e
            logging.exception("백엔드 초기화 실패: %s", e)

    init_task = asyncio.create_task(run_inits())
    # 서버를 먼저 띄우기 위해 yield를 즉시 수행 (초기화는 백그라운드에서 진행)
    yield

    init_task.cancel()
    try:
        await init_task
    except asyncio.CancelledError:
        pass
    if init_error:
        logging.warning("백엔드 초기화 중 오류가 있었습니다: %s", init_error)
    print("\n[INFO] 서버 종료 중...")
    try:
        from domain.hub.llm.gemini_adapter import _close_genai_client
        _close_genai_client()
    except Exception:
        pass


app = FastAPI(
    title="LangChain Chatbot API",
    description="LangGraph 에이전트 채팅·RAG(disclosures·competency 테이블 검색)",
    version="1.0.0",
    lifespan=_app_lifespan,
)

# 게이트웨이: CORS (진입부)
from gateway import add_cors_middleware  # type: ignore

add_cors_middleware(app)

# 전역 변수 (에이전트 RAG: disclosures·competency 검색용 임베딩)
local_embeddings = None
local_llm = None
_rag_init_lock = threading.Lock()
_rag_initialized = False


def init_db() -> None:
    """DB 초기화: Alembic 마이그레이션으로 Soccer 등 관계형 테이블 자동 생성·업데이트."""
    try:
        # 설정 가져오기
        current_settings = get_settings()

        # 관계형 테이블 자동 생성 (Alembic + 자동 생성 방식)
        logging.info("관계형 테이블 생성 중 (Alembic 자동 생성)...")
        wait_for_postgres()

        try:
            # 모델들을 명시적으로 import하여 Base.metadata에 등록
            from alembic import command  # type: ignore

            # Alembic 설정
            from alembic.config import Config  # type: ignore
            from core.database import get_engine  # type: ignore
            from domain.models.bases.soccer import (  # noqa: F401
                Player,
                Schedule,
                Stadium,
                Team,
            )
            from sqlalchemy import inspect  # type: ignore[import-untyped]

            app_dir = Path(__file__).parent
            alembic_ini_path = app_dir / "alembic.ini"
            alembic_cfg = Config(str(alembic_ini_path))
            # CWD와 무관하게 app/alembic 사용 (관계형 + 임베딩 테이블 모두 여기서 관리)
            script_location = app_dir / "alembic"
            alembic_cfg.set_main_option("script_location", str(script_location))
            logging.info("Alembic script_location: %s", script_location.resolve())

            # Alembic 마이그레이션 파일 디렉토리 확인
            alembic_versions_path = app_dir / "alembic" / "versions"
            if not alembic_versions_path.exists():
                alembic_versions_path.mkdir(parents=True, exist_ok=True)

            if current_settings.auto_migrate:
                # 기동 시에는 upgrade만 실행 (마이그레이션 생성은 수동: alembic revision --autogenerate -m "설명")
                try:
                    command.upgrade(alembic_cfg, current_settings.migration_revision)
                    logging.info("✓ DB 마이그레이션 완료")
                except Exception as upgrade_error:
                    # 마이그레이션 실패 시에만 테이블 확인
                    logging.error(f"마이그레이션 실행 실패: {upgrade_error}")
                    try:
                        engine = get_engine()
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
                logging.warning("자동 마이그레이션이 비활성화되어 있습니다. (AUTO_MIGRATE=false)")
                logging.warning("테이블을 생성하려면 마이그레이션을 수동으로 실행하거나 AUTO_MIGRATE=true로 설정하세요.")

        except Exception as e:
            logging.error(f"관계형 테이블 생성 중 오류: {e}")
            import traceback
            logging.error(traceback.format_exc())
            raise  # 테이블 생성 실패는 치명적 오류이므로 재발생

        # Soccer 등 데이터는 JSONL 업로드를 통해 LangGraph 휴리스틱 처리로 로드됩니다.
        logging.info("✓ DB 초기화 완료")
    except Exception as e:
        logging.error(f"DB 초기화 실패: {e}")
        raise


def init_v1() -> None:
    """에이전트·RAG 초기화: LangGraph, ExaOne, Embedding(disclosures·competency 검색용)."""
    global local_embeddings, local_llm

    print("=" * 50)
    print("에이전트·RAG 초기화 (LangGraph, ExaOne, Embedding)...")
    print("=" * 50)

    llm_provider = settings.llm_provider
    print(f"\n[INFO] LLM_PROVIDER: {llm_provider}")
    print("[INFO] EXAONE: HuggingFace 캐시에서 로드 (EXAONE_MODEL_DIR 미사용)")

    print("\n1. Neon PostgreSQL 연결 확인 중...")
    wait_for_postgres()

    if llm_provider == "exaone":
        print("\n2. EXAONE: Lazy Loading (첫 채팅 요청 시 로드)")

    print("\n3. Embedding 서버 기동 시 초기화 중... (RAG: disclosures·competency 테이블 검색용)")
    ensure_rag_initialized()
    print("[OK] Embedding·RAG 초기화 완료!")
    print("\n4. 스팸 감지 모델: Lazy Loading (첫 요청 시 LLaMA 로드)")
    print("[INFO] VRAM 절약을 위해 스팸 테스트 요청 시 LLaMA 모델이 로드됩니다.")

    print("\n" + "=" * 50)
    print("[OK] 에이전트·RAG 초기화 완료!")
    print("=" * 50)


def initialize_embeddings():
    """Embedding 모델 초기화 — FlagEmbedding BGE-m3 (disclosures·competency RAG 검색용)."""
    global local_embeddings

    try:
        from domain.shared.embedding import get_embedding_model  # type: ignore

        device = getattr(settings, "embedding_device", None) or None
        local_embeddings = get_embedding_model(
            model_name=getattr(settings, "default_embedding_model", None),
            use_fp16=True,
            devices=device,
        )
        local_embeddings.embed_query("test")
        print("[OK] 로컬 Embedding 초기화 완료 (FlagEmbedding BGE-m3, RAG: disclosures·competency)")
    except Exception as local_error:
        print(f"[WARNING] 로컬 Embedding 모델 초기화 실패: {str(local_error)[:100]}...")
        local_embeddings = None

    if not local_embeddings:
        print(
            "[WARNING] 로컬 Embedding 모델 초기화에 실패했습니다. "
            "RAG(disclosures·competency 검색)가 비활성화됩니다."
        )


def ensure_rag_initialized() -> None:
    """RAG용 Embedding + FAISS 인덱스 한 번만 초기화."""
    global _rag_initialized
    if _rag_initialized:
        return
    with _rag_init_lock:
        if _rag_initialized:
            return
        if local_embeddings is None:
            initialize_embeddings()
        try:
            from domain.shared.embedding import preload_disclosure_embedding_model  # type: ignore
            if preload_disclosure_embedding_model():
                print("[OK] RAG 임베딩 준비 완료 (FlagEmbedding BGE-m3, disclosures·competency)")
            else:
                print("[WARNING] RAG 임베딩 준비 실패")
        except Exception as e:
            print(f"[WARNING] RAG 임베딩 준비 예외: {e}")
        try:
            from core.faiss_store import load_faiss_indices  # type: ignore
            if load_faiss_indices():
                print("[OK] FAISS 인덱스 로드 완료 (disclosures·competency_anchors)")
            else:
                print("[INFO] FAISS 인덱스 없음 또는 로드 스킵 (pgvector fallback)")
        except Exception as e:
            print(f"[WARNING] FAISS 로드 예외: {e}")
        _rag_initialized = True


# 게이트웨이: 라우터/MCP 등록 (통합: api/routers + MCP)
from api.routers import (  # type: ignore  # noqa: E402
    chat_router,
    disclosure_router,
    document_router,
    email_router,
    employee_router,
    resume_router,
    soccer_router,
)
from gateway import register_routes  # type: ignore  # noqa: E402

register_routes(
    app,
    mcp_app,
    chat_router=chat_router,
    disclosure_router=disclosure_router,
    document_router=document_router,
    email_router=email_router,
    employee_router=employee_router,
    resume_router=resume_router,
    soccer_router=soccer_router,
)


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
        "local_embeddings": "initialized" if local_embeddings else "lazy (not loaded yet)",
    }
