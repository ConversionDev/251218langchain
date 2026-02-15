"""
도메인 공통 임베딩 — FlagEmbedding + BGE-m3.

Soccer·Disclosure 등에서 공통 사용. 설정은 core.config에서 읽음.
LangChain Embeddings 인터페이스(embed_documents, embed_query) 제공.
"""

import warnings
from typing import Dict, List, Optional, Tuple

# BGE-m3 Dense 출력 차원 (1024)
BGE_M3_DENSE_DIM = 1024

# FlagEmbedding 내부에서 XLMRobertaTokenizerFast 사용 시 나오는 경고 억제 (라이브러리 내부 호출 방식)
for _cat in (UserWarning, FutureWarning):
    warnings.filterwarnings("ignore", message=".*fast tokenizer.*__call__.*", category=_cat)


def _default_device() -> Optional[str]:
    """CUDA 사용 가능 시 cuda:0, 아니면 None(라이브러리 기본)."""
    try:
        import torch  # type: ignore[import-untyped]
        if torch.cuda.is_available():
            return "cuda:0"
    except Exception:
        pass
    return None


class FlagEmbeddingWrapper:
    """FlagEmbedding BGEM3FlagModel → LangChain Embeddings 인터페이스 래퍼."""

    def __init__(
        self,
        model_name: str = "BAAI/bge-m3",
        use_fp16: bool = True,
        devices: Optional[str] = None,
        batch_size: int = 512,
    ):
        from FlagEmbedding import BGEM3FlagModel  # type: ignore[import-untyped]

        if devices is None:
            devices = _default_device()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            warnings.simplefilter("ignore", FutureWarning)
            kwargs: Dict[str, Any] = {"use_fp16": use_fp16}
            if devices is not None:
                kwargs["devices"] = devices
            try:
                self._model = BGEM3FlagModel(model_name, **kwargs)
            except TypeError:
                kwargs.pop("devices", None)
                self._model = BGEM3FlagModel(model_name, **kwargs)
        self._batch_size = batch_size

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """문서 리스트를 Dense 1024차원 벡터로 임베딩. 내부 배치로 처리."""
        if not texts:
            return []
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            warnings.simplefilter("ignore", FutureWarning)
            result = self._model.encode_corpus(
                texts,
                return_dense=True,
                return_sparse=False,
                batch_size=getattr(self, "_batch_size", 512),
            )
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
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            warnings.simplefilter("ignore", FutureWarning)
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

# disclosure 쿼리용 BGE 싱글톤 (fp16 한 번만 로드, GPU 통일)
_disclosure_bge_model: Optional["FlagEmbeddingWrapper"] = None


def get_embedding_model(
    model_name: Optional[str] = None,
    use_fp16: bool = True,
    devices: Optional[str] = None,
    batch_size: int = 512,
) -> FlagEmbeddingWrapper:
    """
    Soccer·Disclosure 공통 임베딩 모델 (FlagEmbedding BGE-m3).
    동일 인자로 호출 시 캐시된 인스턴스 반환(재로딩 없음).
    devices: None이면 CUDA 사용 가능 시 cuda:0, 아니면 라이브러리 기본.
    batch_size: encode_corpus 내부 배치 크기(기본 512, GPU 메모리 부족 시 줄이기).
    """
    if model_name is None:
        from core.config import get_settings  # type: ignore

        model_name = get_settings().default_embedding_model
    key = (model_name, use_fp16, devices)
    if key not in _embedding_model_cache:
        _embedding_model_cache[key] = FlagEmbeddingWrapper(
            model_name=model_name,
            use_fp16=use_fp16,
            devices=devices,
            batch_size=batch_size,
        )
    return _embedding_model_cache[key]


def get_disclosure_embedding_model() -> Optional["FlagEmbeddingWrapper"]:
    """
    disclosure 테이블 쿼리 임베딩용 BGE-m3.
    get_embedding_model과 동일한 devices 사용 → 서버당 단일 인스턴스(중복 로드 방지).
    """
    global _disclosure_bge_model
    if _disclosure_bge_model is not None:
        return _disclosure_bge_model
    try:
        from core.config import get_settings  # type: ignore
        devices = getattr(get_settings(), "embedding_device", None) or None
        _disclosure_bge_model = get_embedding_model(use_fp16=True, devices=devices)
        _disclosure_bge_model.embed_query("test")
        return _disclosure_bge_model
    except Exception:
        _disclosure_bge_model = None
        return None


def preload_disclosure_embedding_model() -> bool:
    """서버 기동 시 disclosure용 BGE를 미리 로드. 성공 여부 반환."""
    model = get_disclosure_embedding_model()
    return model is not None
