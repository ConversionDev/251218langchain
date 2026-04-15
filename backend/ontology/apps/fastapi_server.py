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
    """DB 초기화: Alembic 마이그레이션으로 관계형 테이블 자동 생성·업데이트."""
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
                    logging.error(f"마이그레이션 실행 실패: {upgrade_error}")
                    raise
            else:
                logging.warning("자동 마이그레이션이 비활성화되어 있습니다. (AUTO_MIGRATE=false)")
                logging.warning("테이블을 생성하려면 마이그레이션을 수동으로 실행하거나 AUTO_MIGRATE=true로 설정하세요.")

        except Exception as e:
            logging.error(f"관계형 테이블 생성 중 오류: {e}")
            import traceback
            logging.error(traceback.format_exc())
            raise  # 테이블 생성 실패는 치명적 오류이므로 재발생

        # Disclosure 등 데이터는 JSONL 업로드를 통해 LangGraph 휴리스틱 처리로 로드됩니다.
        logging.info("✓ DB 초기화 완료")
    except Exception as e:
        logging.error(f"DB 초기화 실패: {e}")
        raise


def init_v1() -> None:
    """에이전트·RAG 초기화. t3.small 등 메모리 절약을 위해 스타트업에서는 DB만 확인하고, 모델·인덱스는 Lazy."""
    global local_embeddings, local_llm

    print("=" * 50)
    print("에이전트·RAG 초기화 (Lazy: Embedding·FAISS 스킵)...")
    print("=" * 50)

    llm_provider = settings.llm_provider
    print(f"\n[INFO] LLM_PROVIDER: {llm_provider}")

    print("\n1. Neon PostgreSQL 연결 확인 중...")
    wait_for_postgres()

    print("\n2. EXAONE: Lazy Loading (첫 채팅 요청 시 adapter 로드)")
    print("\n3. Embedding·RAG: Lazy (첫 RAG 요청 시 Embedding만 로드, FAISS 인덱스는 미로드 → pgvector 사용)")
    print("\n4. 스팸 LLaMA: Lazy Loading (첫 스팸 요청 시 adapter 로드)")

    print("\n" + "=" * 50)
    print("[OK] 에이전트·RAG 초기화 완료 (주소록/메일 즉시 사용, 채팅·RAG·스팸은 첫 요청 시 로드)")
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
            logging.info("[RAG] 초기화 시작 — Embedding(BGE-m3) 로드 중 (메모리 사용량 증가, OOM 시 프로세스 종료 가능)")
            initialize_embeddings()
        try:
            from domain.shared.embedding import preload_disclosure_embedding_model  # type: ignore
            logging.info("[RAG] disclosure 임베딩 모델 preload 시작")
            if preload_disclosure_embedding_model():
                print("[OK] RAG 임베딩 준비 완료 (FlagEmbedding BGE-m3, pgvector 사용)")
            else:
                print("[WARNING] RAG 임베딩 준비 실패")
        except Exception as e:
            print(f"[WARNING] RAG 임베딩 준비 예외: {e}")
        # FAISS 인덱스는 스타트업에서 로드하지 않음 (메모리 절약). RAG는 pgvector fallback으로 동작.
        _rag_initialized = True


# 게이트웨이: 라우터/MCP 등록 (통합: api/routers + MCP)
from api.routers import (  # type: ignore  # noqa: E402
    activity_router,
    address_book_router,
    audit_router,
    chat_router,
    disclosure_router,
    document_router,
    email_router,
    employee_router,
    resume_router,
)
from gateway import register_routes  # type: ignore  # noqa: E402

register_routes(
    app,
    mcp_app,
    activity_router=activity_router,
    address_book_router=address_book_router,
    audit_router=audit_router,
    chat_router=chat_router,
    disclosure_router=disclosure_router,
    document_router=document_router,
    email_router=email_router,
    employee_router=employee_router,
    resume_router=resume_router,
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
