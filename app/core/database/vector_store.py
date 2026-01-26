"""
벡터 스토어 관리

V1과 V10을 위한 PGVector 스토어를 생성하고 관리합니다.
"""

from typing import Optional

from langchain_community.vectorstores import PGVector  # type: ignore[import-untyped]

from core.config import get_settings  # type: ignore


def get_v10_vector_store(embeddings_model, collection_name: Optional[str] = None):
    """
    V10 전용 벡터 스토어를 생성합니다.

    Args:
        embeddings_model: 임베딩 모델 (예: HuggingFaceEmbeddings)
        collection_name: 컬렉션 이름 (None이면 설정에서 가져옴)

    Returns:
        PGVector 인스턴스
    """
    settings = get_settings()
    connection_string = settings.connection_string
    
    # V10 전용 컬렉션 이름 (기본값: v10_soccer_collection)
    if collection_name is None:
        collection_name = getattr(settings, "v10_collection_name", "v10_soccer_collection")
    
    return PGVector(
        embedding_function=embeddings_model,
        collection_name=collection_name,
        connection_string=connection_string,
    )


def get_v1_vector_store(embeddings_model, collection_name: Optional[str] = None):
    """
    V1 전용 벡터 스토어를 생성합니다.

    Args:
        embeddings_model: 임베딩 모델 (예: HuggingFaceEmbeddings)
        collection_name: 컬렉션 이름 (None이면 설정에서 가져옴)

    Returns:
        PGVector 인스턴스
    """
    settings = get_settings()
    connection_string = settings.connection_string
    
    if collection_name is None:
        collection_name = settings.collection_name
    
    return PGVector(
        embedding_function=embeddings_model,
        collection_name=collection_name,
        connection_string=connection_string,
    )
