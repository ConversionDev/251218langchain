"""
FastAPI 백엔드 서버 - FastAPI와 LangChain 연동.

이 서버는 FastAPI를 통해 LangChain RAG 체인을 제공하는 API 서버입니다.
PGVector 벡터 스토어를 직접 초기화하여 챗봇 API를 제공합니다.

역할:
- FastAPI 서버 제공 (REST API)
- LangChain RAG 체인 실행
- PGVector 벡터 스토어 초기화 및 관리
- LangGraph 기반 스팸 감지 API
"""

import warnings
from pathlib import Path
from typing import Any, Optional

# 공통 모듈 (환경 변수 로딩 포함)
from core.config import get_settings  # type: ignore
from core.database import wait_for_postgres  # type: ignore

# LangChain 관련 import (warnings 필터링 전에 import)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# LangChain 1.x 호환: langchain_classic 또는 langchain에서 import 시도
try:
    from langchain.chains import (
        create_history_aware_retriever,
        create_retrieval_chain,
    )
    from langchain.chains.combine_documents import create_stuff_documents_chain
except ImportError:
    # 하위 호환성: langchain-classic 패키지 사용
    try:
        from langchain_classic.chains import (
            create_history_aware_retriever,
            create_retrieval_chain,
        )
        from langchain_classic.chains.combine_documents import create_stuff_documents_chain
    except ImportError:
        # 최신 LangChain 1.x: langchain 패키지에서 직접 import
        from langchain.chains.history_aware_retriever import create_history_aware_retriever
        from langchain.chains.retrieval import create_retrieval_chain
        from langchain.chains.combine_documents import create_stuff_documents_chain

from langchain_community.vectorstores import PGVector
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable

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

# 설정 로드
settings = get_settings()
CONNECTION_STRING = settings.connection_string
COLLECTION_NAME = settings.collection_name

# FastAPI 앱 생성
app = FastAPI(
    title="LangChain Chatbot API",
    description="PGVector와 연동된 LangChain 챗봇 API",
    version="1.0.0",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 변수
vector_store: Optional[PGVector] = None
local_embeddings = None
local_llm = None
local_rag_chain: Optional[Runnable] = None
# ChatService 인스턴스 (타입 힌트는 함수 내부에서 import)
chat_service: Optional[Any] = None


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


def initialize_llm():
    """LLM 모델 초기화 - EXAONE은 LangGraph에서 사용되므로 여기서는 로딩하지 않음."""
    global local_llm

    # EXAONE은 LangGraph에서 사용되므로 local_llm은 None으로 설정
    local_llm = None


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


def create_rag_chain(llm_model, embeddings_model):
    """RAG 체인 생성 - LangChain 체인 기능 활용."""
    try:
        # 1. Retriever 생성 (현재 Embedding 모델 사용)
        current_vector_store = PGVector(
            embedding_function=embeddings_model,
            collection_name=COLLECTION_NAME,
            connection_string=CONNECTION_STRING,
        )
        retriever = current_vector_store.as_retriever(search_kwargs={"k": 3})

        # 2. 대화 기록을 고려한 검색 쿼리 생성 프롬프트
        contextualize_q_system_prompt = (
            "대화 기록과 최신 사용자 질문이 주어졌을 때, "
            "대화 기록의 맥락을 참고하여 독립적으로 이해할 수 있는 질문으로 재구성하세요. "
            "질문에 답하지 말고, 필요시 재구성하고 그렇지 않으면 그대로 반환하세요."
        )
        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", contextualize_q_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )

        # 3. 대화 기록을 고려한 Retriever 생성
        history_aware_retriever = create_history_aware_retriever(
            llm_model, retriever, contextualize_q_prompt
        )

        # 4. 질문 답변 프롬프트
        qa_system_prompt = (
            "당신은 LangChain과 PGVector를 사용하는 도움이 되는 AI 어시스턴트입니다. "
            "다음 검색된 컨텍스트 정보를 참고하여 사용자의 질문에 답변해주세요. "
            "컨텍스트에 답변할 수 없는 질문이면, 정중하게 그렇게 말씀해주세요. "
            "답변은 최대 3문장으로 간결하게 작성해주세요.\n\n"
            "컨텍스트:\n{context}"
        )
        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", qa_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )

        # 5. 문서 결합 체인 생성
        question_answer_chain = create_stuff_documents_chain(llm_model, qa_prompt)

        # 6. 최종 RAG 체인 생성
        rag_chain = create_retrieval_chain(
            history_aware_retriever, question_answer_chain
        )

        return rag_chain
    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] RAG 체인 생성 실패: {error_msg[:200]}...")
        raise


def initialize_rag_chain():
    """RAG 체인 초기화 - 로컬 모델용 체인 생성."""
    global local_rag_chain

    # 로컬 모델용 RAG 체인 생성
    if local_llm and local_embeddings:
        try:
            local_rag_chain = create_rag_chain(local_llm, local_embeddings)
            print("[OK] 로컬 RAG 체인 초기화 완료")
        except Exception as e:
            print(f"[WARNING] 로컬 RAG 체인 초기화 실패: {str(e)[:100]}...")
            local_rag_chain = None

    if not local_rag_chain:
        print("[WARNING] 로컬 RAG 체인 초기화에 실패했습니다.")
        if not local_llm:
            print("  - 로컬 LLM이 초기화되지 않았습니다.")
        if not local_embeddings:
            print("  - 로컬 Embeddings가 초기화되지 않았습니다.")
        print("[WARNING] RAG 기능이 비활성화됩니다. 채팅 기능을 사용할 수 없습니다.")


@app.on_event("startup")  # FastAPI 0.104+ 호환 (lifespan도 지원하지만 하위 호환성 유지)
async def startup_event():
    """서버 시작 시 초기화."""
    global chat_service, local_embeddings, local_llm, local_rag_chain, vector_store

    print("=" * 50)
    print("LangChain FastAPI 서버 시작 중...")
    print("=" * 50)

    # 환경 변수 확인
    llm_provider = settings.llm_provider
    exaone_model_dir = settings.exaone_model_dir or "기본값 사용"
    print(f"\n[INFO] LLM_PROVIDER: {llm_provider}")
    print(f"[INFO] EXAONE_MODEL_DIR: {exaone_model_dir}")

    # Neon PostgreSQL 연결 대기
    print("\n1. Neon PostgreSQL 연결 확인 중...")
    wait_for_postgres()

    # ChatService 초기화
    print("\n2. ChatService 초기화 중...")
    from domain.chat.services.chat_service import ChatService  # type: ignore

    chat_service = ChatService(
        connection_string=CONNECTION_STRING,
        collection_name=COLLECTION_NAME,
        model_name_or_path=exaone_model_dir
        if exaone_model_dir != "기본값 사용"
        else None,
    )

    # Embedding 모델 초기화
    print("\n3. Embedding 모델 초기화 중...")
    chat_service.initialize_embeddings()

    # LLM 모델 초기화
    print("\n4. LLM 모델 초기화 중...")
    chat_service.initialize_llm()

    # EXAONE 베이스 모델 미리 로드 (서버 시작 시 - 전략 3: 하이브리드)
    if llm_provider == "exaone":
        print("\n4-1. EXAONE 베이스 모델 미리 로드 중...")
        from core.resource_manager.exaone_manager import ExaoneManager  # type: ignore

        ExaoneManager().get_base_model()  # 베이스 모델만 사전 로드 (어댑터는 필요 시 로드)
        print("[OK] EXAONE 베이스 모델 미리 로드 완료!")

    # PGVector 스토어 초기화 (기존 함수 사용)
    print("\n5. PGVector 스토어 초기화 중...")
    # ChatService의 embeddings를 전역 변수에 할당 (기존 코드 호환성)
    local_embeddings = chat_service.local_embeddings
    local_llm = chat_service.local_llm
    initialize_vector_store()

    # RAG 체인 초기화
    print("\n6. RAG 체인 초기화 중...")
    chat_service.initialize_rag_chain()
    # ChatService의 RAG 체인을 전역 변수에 할당 (기존 코드 호환성)
    local_rag_chain = chat_service.local_rag_chain

    # 스팸 감지 모델은 Lazy Loading (첫 요청 시 로드)
    print("\n7. 스팸 감지 모델: Lazy Loading 설정 (첫 요청 시 LLaMA 로드)")
    print("[INFO] VRAM 절약을 위해 스팸 테스트 요청 시 LLaMA 모델이 로드됩니다.")

    print("\n" + "=" * 50)
    print("[OK] 서버 초기화 완료!")
    print("=" * 50)


# 라우터 등록 (순환 import 방지를 위해 여기서 import)
from api.v1.chat.chat_router import router as chat_router  # type: ignore  # noqa: E402
from api.v1.spam.email_router import email_router  # type: ignore  # noqa: E402
from api.v1.agent.graph_router import router as graph_router  # type: ignore  # noqa: E402
from api.v1.spam.mcp_router import router as mcp_router  # type: ignore  # noqa: E402

app.include_router(chat_router)
app.include_router(graph_router)
app.include_router(mcp_router)
app.include_router(email_router)


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
        "vector_store": "initialized" if vector_store else "not initialized",
        "local_embeddings": "initialized" if local_embeddings else "not initialized",
        "local_llm": "initialized" if local_llm else "not initialized",
        "local_rag_chain": "initialized" if local_rag_chain else "not initialized",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
