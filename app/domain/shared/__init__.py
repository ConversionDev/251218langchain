"""
도메인 공통 인프라 (Soccer·Disclosure 등 여러 spoke에서 사용).

- embedding: FlagEmbedding BGE-m3 래퍼 및 get_embedding_model
"""

from .embedding import (
    BGE_M3_DENSE_DIM,
    FlagEmbeddingWrapper,
    get_embedding_model,
)

__all__ = [
    "BGE_M3_DENSE_DIM",
    "FlagEmbeddingWrapper",
    "get_embedding_model",
]
