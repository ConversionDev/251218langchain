"""
도메인 공통 임베딩 — FlagEmbedding + BGE-m3.

Soccer·Disclosure 등에서 공통 사용. 설정은 core.config에서 읽음.
LangChain Embeddings 인터페이스(embed_documents, embed_query) 제공.
"""

from typing import Dict, List, Optional, Tuple

# BGE-m3 Dense 출력 차원 (1024)
BGE_M3_DENSE_DIM = 1024


class FlagEmbeddingWrapper:
    """FlagEmbedding BGEM3FlagModel → LangChain Embeddings 인터페이스 래퍼."""

    def __init__(self, model_name: str = "BAAI/bge-m3", use_fp16: bool = True):
        from FlagEmbedding import BGEM3FlagModel  # type: ignore[import-untyped]

        self._model = BGEM3FlagModel(model_name, use_fp16=use_fp16)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """문서 리스트를 Dense 1024차원 벡터로 임베딩."""
        if not texts:
            return []
        result = self._model.encode_corpus(texts, return_dense=True, return_sparse=False)
        dense = result.get("dense_vecs")
        if dense is None:
            return []
        import numpy as np

        if isinstance(dense, np.ndarray):
            if dense.ndim == 1:
                return [dense.tolist()]
            return [row.tolist() for row in dense]
        return [list(row) for row in dense]

    def embed_query(self, text: str) -> List[float]:
        """단일 쿼리를 Dense 1024차원 벡터로 임베딩."""
        result = self._model.encode_queries([text], return_dense=True, return_sparse=False)
        dense = result.get("dense_vecs")
        if dense is None:
            return []
        import numpy as np

        if isinstance(dense, np.ndarray):
            if dense.ndim == 2:
                return dense[0].tolist()
            return dense.tolist()
        return list(dense[0]) if dense else []


# (model_name, use_fp16) → 인스턴스 캐시 (재로딩 방지)
_embedding_model_cache: Dict[Tuple[str, bool], "FlagEmbeddingWrapper"] = {}


def get_embedding_model(
    model_name: Optional[str] = None,
    use_fp16: bool = True,
) -> FlagEmbeddingWrapper:
    """
    Soccer·Disclosure 공통 임베딩 모델 (FlagEmbedding BGE-m3).
    동일 인자로 호출 시 캐시된 인스턴스 반환(재로딩 없음).
    """
    if model_name is None:
        from core.config import get_settings  # type: ignore

        model_name = get_settings().default_embedding_model
    key = (model_name, use_fp16)
    if key not in _embedding_model_cache:
        _embedding_model_cache[key] = FlagEmbeddingWrapper(model_name=model_name, use_fp16=use_fp16)
    return _embedding_model_cache[key]
